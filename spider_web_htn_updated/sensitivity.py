"""
sensitivity.py — Sensitivity analysis: does the HTN planner degrade
gracefully as environmental noise increases, and how does that compare to
the flat-state random-walker baseline (Group B, baseline.py) under the
exact same noise?

From the Way-Forward roadmap:
    "Run the model 1,000 times under varying conditions. How does the
    'success rate' of the web construction change when you introduce
    environmental noise (e.g., wind, reduced anchor availability)?"

And per the team's own framing (chat, 2026-09-09): the bar is that the
planner should degrade gracefully, not crash, as the environment worsens —
"agar surroundings mai slightly change aajaaye, toh code blow up nhi karna
chahiye."

This module sweeps anchor_availability.removal_prob (and optionally wind
noise_std) over a grid, running N_RUNS seeded trials per condition for BOTH
groups, and reports per group:
    - success rate: fraction of runs that reached completion (HTN: gtpyhop
      find_plan didn't return False; baseline: is_web_complete(state) within
      its step budget) — "did the code blow up / give up"
    - energy stats for the successful runs (mean/median/stdev), so we can
      also see *how much worse* successful webs get, not just whether they
      complete at all.

Both groups use the SAME seed per trial index, so they see the exact same
anchor-removal draw and wind stream for a given (condition, trial) pair —
a paired comparison, not just two independently-averaged curves. Every HTN
run uses a fresh gtpyhop.Domain, so the whole sweep is reproducible end to
end from base_seed alone.

Usage:
    python -m spider_web_htn_updated.sensitivity
    python -m spider_web_htn_updated.sensitivity --n-runs 1000 --out results.csv
"""

import argparse
import contextlib
import csv
import io
import random
import statistics
import sys

import gtpyhop

from .config_loader import CONFIG
from .state import create_initial_state
from . import operators as ops
from . import methods as mtd
from .baseline import run_baseline

_BASELINE_MAX_STEPS = 3000


# ---------------------------------------------------------------------------
# Domain setup (mirrors main.py's setup_domain — duplicated rather than
# imported so repeated calls across the sweep don't re-register actions on
# a domain object that's being swapped out from under gtpyhop's global
# registry each time; each trial gets a completely fresh Domain).
# ---------------------------------------------------------------------------

def _setup_domain():
    domain = gtpyhop.Domain("sensitivity_zschokke1996_orb_web")

    gtpyhop.declare_actions(
        ops.walk, ops.anchor, ops.lay_thread, ops.attach_dragline,
        ops.remove_thread, ops.drop_down, ops.swing_tarzan, ops.reel_up,
        ops.insert_radius, ops.mark_proto_hub, ops.lay_frame_thread,
        ops.lay_radius, ops.build_spiral_segment, ops.mark_web_complete,
        mtd.mark_high_thread_done, mtd.mark_auxiliary_spiral_done,
        mtd.mark_capture_spiral_done,
    )

    gtpyhop.declare_task_methods("build_web", mtd.build_web)
    gtpyhop.declare_task_methods("explore_and_bridge", mtd.explore_bridge_walk_detour)
    gtpyhop.declare_task_methods(
        "establish_high_thread",
        mtd.establish_high_thread_direct, mtd.establish_high_thread_via_climb,
    )
    gtpyhop.declare_task_methods(
        "establish_proto_hub",
        mtd.establish_proto_hub_done, mtd.establish_proto_hub_via_walk,
        mtd.establish_proto_hub_via_drop, mtd.establish_proto_hub_via_tarzan,
    )
    gtpyhop.declare_task_methods("build_remaining_web", mtd.build_remaining_web)
    gtpyhop.declare_task_methods("build_frame", mtd.build_frame_method)
    gtpyhop.declare_task_methods("build_radii", mtd.build_radii_method)
    gtpyhop.declare_task_methods("build_auxiliary_spiral", mtd.build_auxiliary_spiral_method)
    gtpyhop.declare_task_methods("build_capture_spiral", mtd.build_capture_spiral_method)
    gtpyhop.declare_task_methods("finalise_web", mtd.finalise_web)

    return domain


def _run_once_htn(seed):
    """Run the HTN planner (Group A) once with the given seed. Returns (success, energy).

    IMPORTANT: gtpyhop.find_plan never mutates the state object passed to it —
    internally it deep-copies state on every action application (see
    gtpyhop.main.State.copy / _apply_action_and_continue_iterative), backtracks
    across many discarded branches, and returns only the plan (list of action
    tuples), never the final state. So `state.energy_expended` after find_plan
    returns is always 0.0 — it was never touched.

    Under stochastic wind, this means we cannot recover "the energy the search
    actually experienced" — that information lived only on deep copies that
    were thrown away. What we CAN do honestly is execute the found plan for
    real, exactly once, on a fresh copy of the same initial state (same
    anchor availability, since that's fixed once per seed) — consuming wind
    draws from a SEPARATE, dedicated execution RNG rather than continuing to
    draw from `state.rng`, whose position is meaningless after a discarded
    search (it's advanced by however many branches the search tried, not by
    the accepted plan). This is deterministic and reproducible per seed, and
    it's an honest "cost of actually walking this plan once," not a
    re-randomized number pretending to be the search-time cost.
    """
    _setup_domain()
    state = create_initial_state(seed=seed)
    with contextlib.redirect_stdout(io.StringIO()):
        gtpyhop.set_verbose_level(0)
        plan = gtpyhop.find_plan(state, [("build_web",)])

    if plan is False or plan is None:
        return False, None

    exec_state = create_initial_state(seed=seed)
    exec_state.rng = random.Random(f"htn-exec-{seed}")

    energy = 0.0
    for action in plan:
        name = action[0]
        if name in ("walk", "lay_thread", "lay_frame_thread", "lay_radius",
                     "drop_down", "swing_tarzan", "reel_up", "build_spiral_segment"):
            if len(action) >= 3:
                energy += ops._movement_cost(exec_state, action[1], action[2])
    return True, energy


def _run_once_baseline(seed):
    """Run the flat-state random walker (Group B) once with the given seed.

    Returns (success, energy). Uses the SAME seed as the paired HTN trial so
    both groups see identical anchor-removal/wind draws for a given trial —
    the walker's own action-selection randomness is separately (but still
    deterministically) derived from the same seed inside run_baseline.
    """
    result = run_baseline(seed=seed, max_steps=_BASELINE_MAX_STEPS)
    if not result["success"]:
        return False, None
    return True, result["energy_expended"]


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

def run_sensitivity_sweep(
    removal_probs=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5),
    wind_stds=(0.0,),
    n_runs=1000,
    base_seed=1000,
    verbose=True,
):
    """
    Run BOTH groups (HTN and the flat-state baseline) n_runs times for every
    (removal_prob, wind_std) combination in the grid, restoring config
    afterward. Each trial index uses the same seed for both groups, so the
    comparison is paired (identical anchor-removal/wind draw per trial).

    Returns
    -------
    list of dict, one row per (group, removal_prob, wind_std) condition:
        {group, removal_prob, wind_std, n_runs, successes, success_rate,
         energy_mean, energy_median, energy_stdev}
    """
    stoch_cfg = CONFIG["stochastic"]
    anchor_cfg = stoch_cfg["anchor_availability"]
    wind_cfg = stoch_cfg["wind"]

    # Save originals so the sweep leaves CONFIG exactly as it found it.
    orig_enabled = stoch_cfg["enabled"]
    orig_anchor_enabled = anchor_cfg["enabled"]
    orig_removal_prob = anchor_cfg["removal_prob"]
    orig_wind_enabled = wind_cfg["enabled"]
    orig_wind_std = wind_cfg["noise_std"]

    results = []
    runners = {"htn": _run_once_htn, "baseline": _run_once_baseline}

    try:
        stoch_cfg["enabled"] = True
        anchor_cfg["enabled"] = True

        for wind_std in wind_stds:
            wind_cfg["enabled"] = wind_std > 0.0
            wind_cfg["noise_std"] = wind_std

            for removal_prob in removal_probs:
                anchor_cfg["removal_prob"] = removal_prob

                # Each group runs as its own complete block (all n_runs
                # trials back to back), rather than alternating HTN/baseline
                # calls trial-by-trial. Seeds still match across groups for
                # the same trial index, so the comparison stays paired.
                per_group = {}
                for group, runner in runners.items():
                    successes = 0
                    energies = []
                    for trial in range(n_runs):
                        seed = base_seed + trial
                        ok, energy = runner(seed)
                        if ok:
                            successes += 1
                            energies.append(energy)
                    per_group[group] = {"successes": successes, "energies": energies}

                for group, data in per_group.items():
                    successes = data["successes"]
                    energies = data["energies"]
                    success_rate = successes / n_runs
                    row = {
                        "group": group,
                        "removal_prob": removal_prob,
                        "wind_std": wind_std,
                        "n_runs": n_runs,
                        "successes": successes,
                        "success_rate": success_rate,
                        "energy_mean": statistics.mean(energies) if energies else None,
                        "energy_median": statistics.median(energies) if energies else None,
                        "energy_stdev": statistics.stdev(energies) if len(energies) > 1 else 0.0,
                    }
                    results.append(row)

                    if verbose:
                        print(
                            f"  [{group:8s}] removal_prob={removal_prob:.2f}  wind_std={wind_std:.2f}  "
                            f"success_rate={success_rate:.3f} ({successes}/{n_runs})  "
                            f"energy_mean={row['energy_mean'] if row['energy_mean'] is None else round(row['energy_mean'], 1)}"
                        )
    finally:
        stoch_cfg["enabled"] = orig_enabled
        anchor_cfg["enabled"] = orig_anchor_enabled
        anchor_cfg["removal_prob"] = orig_removal_prob
        wind_cfg["enabled"] = orig_wind_enabled
        wind_cfg["noise_std"] = orig_wind_std

    return results


def _write_csv(results, path):
    fieldnames = [
        "group", "removal_prob", "wind_std", "n_runs", "successes", "success_rate",
        "energy_mean", "energy_median", "energy_stdev",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    parser = argparse.ArgumentParser(
        description="Sensitivity analysis: HTN planner success rate under "
                     "environmental noise (anchor removal, wind)."
    )
    parser.add_argument("--n-runs", type=int, default=1000,
                         help="Trials per condition (default: 1000, per Way-Forward spec).")
    parser.add_argument("--removal-probs", type=float, nargs="+",
                         default=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
                         help="Anchor-removal probabilities to sweep.")
    parser.add_argument("--wind-stds", type=float, nargs="+", default=[0.0],
                         help="Wind noise_std values to sweep (0.0 = wind disabled).")
    parser.add_argument("--seed", type=int, default=1000,
                         help="Base seed; each trial gets base_seed + running index.")
    parser.add_argument("--out", type=str, default=None,
                         help="Optional CSV output path.")
    args = parser.parse_args()

    print("=" * 70)
    print("  Sensitivity Analysis — HTN (Group A) vs. Baseline (Group B)")
    print("  Success Rate Under Environmental Noise")
    print("=" * 70)
    print(f"  n_runs per condition (per group): {args.n_runs}")
    print(f"  removal_probs: {args.removal_probs}")
    print(f"  wind_stds: {args.wind_stds}")
    print("-" * 70)

    results = run_sensitivity_sweep(
        removal_probs=args.removal_probs,
        wind_stds=args.wind_stds,
        n_runs=args.n_runs,
        base_seed=args.seed,
    )

    print("-" * 70)
    for group in ("htn", "baseline"):
        zero_noise = next(
            (r for r in results
             if r["group"] == group and r["removal_prob"] == 0.0 and r["wind_std"] == 0.0),
            None,
        )
        if zero_noise:
            print(f"  [{group}] baseline (no noise) success rate: {zero_noise['success_rate']:.3f}")

        group_rows = [r for r in results if r["group"] == group]
        worst = min(group_rows, key=lambda r: r["success_rate"])
        print(
            f"  [{group}] worst condition: removal_prob={worst['removal_prob']:.2f}, "
            f"wind_std={worst['wind_std']:.2f} -> success_rate={worst['success_rate']:.3f}"
        )

    if args.out:
        _write_csv(results, args.out)
        print(f"  Results written to: {args.out}")

    return results


if __name__ == "__main__":
    main()
