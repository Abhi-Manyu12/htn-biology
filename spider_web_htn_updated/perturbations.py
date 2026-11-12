"""
perturbations.py — Perturbation Trials and Adaptation Time (Way-Forward
Part 1, Section 4 "Perturbation Trials (Stress Testing)" and Section 3's
Adaptation Time (Ta) metric).

Three stressors, injected mid-construction for BOTH groups:
    resource_depletion — cut the spider's remaining silk budget by 30%
        (operators.py's movement operators refuse to overspend
        state.silk_capacity; see _has_capacity).
    structural_failure — destroy an anchor that already has a structural
        thread attached, removing those threads and decrementing the
        associated progress counters (frame_count / radii_count /
        proto_radii_count).
    predator — set state.predator_present, which forces both groups to
        flee (build_web's top-level method / baseline's candidate
        enumeration both check this flag before anything else) before
        resuming construction.

Trigger point: for both groups, the perturbation fires right after the
proto-hub is established (state.proto_hub_exists becomes True) — the
natural boundary in this domain between Zschokke's "variable, opportunistic"
early stage and "rigid, stereotyped" later stage, so "mid-task" means the
same thing for both architectures rather than an arbitrary fraction of
plan length (which only Group A even has).

Adaptation Time (Ta): "cycles to resume task after perturbation" (Way-
Forward Part 1, Section 3).
    Group A (HTN): GTPyhop plans are computed whole, up front, so recovery
        means replanning from the live, perturbed state via a fresh
        find_plan call (the ordinary find-a-plan process, not a special
        recovery mode — this only works because every method already
        checks its own *_done flag / progress count before deciding what
        remains, so replanning never redoes completed work). Ta is the
        EXTRA action cycles the continuation needed versus what the
        original, undisturbed plan would have needed from that same point:
            Ta = len(continuation_plan) - (len(original_plan) - trigger_index)
        A well-absorbed disruption (e.g. fleeing costs one extra action,
        nothing else changes) gives a small Ta; a disruption that forces a
        materially different, longer continuation gives a larger one.
    Group B (baseline): already a live, step-by-step loop, so Ta is simply
        the number of additional action-selection steps taken from the
        perturbation until is_web_complete (or the step budget runs out).

silk_capacity_initial default (2200 cm) is roughly 3x the deterministic,
undisturbed HTN energy requirement (~700 cm) — generous headroom so an
UNDISTURBED run never binds against it, but the resource_depletion
perturbation's 30% mid-task cut meaningfully bites. The SAME absolute
ceiling is used for both groups (matching the roadmap's framing of
S_initial as a property of "the Spider agent" generically, not something
tuned per architecture) — Group B's own inefficiency, not a smaller
budget, is what will make it fail this trial far more often, which is
itself the expected, meaningful finding.

Usage:
    python -m spider_web_htn_updated.perturbations
    python -m spider_web_htn_updated.perturbations --n-runs 200 --out pert.csv
"""

import argparse
import contextlib
import csv
import io
import random
import statistics

import gtpyhop

from .config_loader import CONFIG
from .state import create_initial_state, rigid
from . import operators as ops
from . import methods as mtd
from .main import _ACTION_FUNCS
from .baseline import enumerate_candidate_actions, is_web_complete
from .instrumentation import count_calls_all, get_decomposition_counter, reset_decomposition_counter

DEFAULT_SILK_CAPACITY = 2200.0
_BASELINE_MAX_STEPS = 4000

_REMOVABLE_ANCHORS = CONFIG["stochastic"]["anchor_availability"]["removable_nodes"]


# ---------------------------------------------------------------------------
# Domain setup (mirrors main.py / sensitivity.py — a fresh Domain per trial,
# methods wrapped for decomposition-node counting).
# ---------------------------------------------------------------------------

def _setup_domain():
    domain = gtpyhop.Domain("perturbation_zschokke1996_orb_web")

    gtpyhop.declare_actions(
        ops.walk, ops.anchor, ops.lay_thread, ops.attach_dragline,
        ops.remove_thread, ops.drop_down, ops.swing_tarzan, ops.reel_up,
        ops.insert_radius, ops.mark_proto_hub, ops.lay_frame_thread,
        ops.lay_radius, ops.build_spiral_segment, ops.mark_web_complete,
        ops.flee_from_predator,
        mtd.mark_high_thread_done, mtd.mark_auxiliary_spiral_done,
        mtd.mark_capture_spiral_done,
    )

    gtpyhop.declare_task_methods("build_web", *count_calls_all(mtd.build_web))
    gtpyhop.declare_task_methods("explore_and_bridge", *count_calls_all(mtd.explore_bridge_walk_detour))
    gtpyhop.declare_task_methods(
        "establish_high_thread",
        *count_calls_all(mtd.establish_high_thread_direct, mtd.establish_high_thread_via_climb),
    )
    gtpyhop.declare_task_methods(
        "establish_proto_hub",
        *count_calls_all(
            mtd.establish_proto_hub_done, mtd.establish_proto_hub_via_walk,
            mtd.establish_proto_hub_via_drop, mtd.establish_proto_hub_via_tarzan,
        ),
    )
    gtpyhop.declare_task_methods("build_remaining_web", *count_calls_all(mtd.build_remaining_web))
    gtpyhop.declare_task_methods("build_frame", *count_calls_all(mtd.build_frame_method))
    gtpyhop.declare_task_methods("build_radii", *count_calls_all(mtd.build_radii_method))
    gtpyhop.declare_task_methods("build_auxiliary_spiral", *count_calls_all(mtd.build_auxiliary_spiral_method))
    gtpyhop.declare_task_methods("build_capture_spiral", *count_calls_all(mtd.build_capture_spiral_method))
    gtpyhop.declare_task_methods("finalise_web", *count_calls_all(mtd.finalise_web))

    return domain


# ---------------------------------------------------------------------------
# Perturbation appliers
# ---------------------------------------------------------------------------

def apply_resource_depletion(state, factor=0.3):
    """Cut the spider's REMAINING silk budget by `factor` (default 30%)."""
    if state.silk_capacity == float("inf"):
        return
    remaining = state.silk_capacity - state.energy_expended
    state.silk_capacity = state.energy_expended + remaining * (1 - factor)


def apply_structural_failure(state, rng):
    """
    Destroy a random already-connected anchor: remove every thread
    touching it and decrement the progress counter each removed thread
    type contributes to. Returns True if an anchor was destroyed, False if
    none were connected yet (nothing to fail).
    """
    structural_types = {"frame", "radius", "proto_radius"}
    connected = set()
    for n1, n2, ttype in state.threads:
        if ttype in structural_types:
            for n in (n1, n2):
                if n in _REMOVABLE_ANCHORS:
                    connected.add(n)

    if not connected:
        return False

    victim = rng.choice(sorted(connected))
    kept = []
    for n1, n2, ttype in state.threads:
        if victim in (n1, n2):
            if ttype == "frame":
                state.frame_count = max(0, state.frame_count - 1)
            elif ttype == "radius":
                state.radii_count = max(0, state.radii_count - 1)
            elif ttype == "proto_radius":
                state.proto_radii_count = max(0, state.proto_radii_count - 1)
        else:
            kept.append((n1, n2, ttype))
    state.threads = kept
    state.nodes.discard(victim)
    return True


def apply_predator_interrupt(state):
    """Force a flee before any further construction (see module docstring)."""
    state.predator_present = True


_PERTURBATIONS = {
    "resource_depletion": lambda state, rng: apply_resource_depletion(state),
    "structural_failure": apply_structural_failure,
    "predator": lambda state, rng: apply_predator_interrupt(state),
}


# ---------------------------------------------------------------------------
# Group A (HTN): replay to the trigger point, perturb, replan, replay the
# continuation.
# ---------------------------------------------------------------------------

def run_htn_perturbation_trial(perturbation_type, seed, silk_capacity_initial=DEFAULT_SILK_CAPACITY):
    """
    Returns a dict: success, energy, adaptation_time, replan_depth,
    triggered (whether the trigger condition — proto-hub established — was
    ever reached; if not, the perturbation never fires and this trial is
    not meaningful).
    """
    _setup_domain()
    rng = random.Random(f"perturbation-{perturbation_type}-{seed}")

    state0 = create_initial_state(seed=seed)
    state0.silk_capacity = silk_capacity_initial
    with contextlib.redirect_stdout(io.StringIO()):
        gtpyhop.set_verbose_level(0)
        plan0 = gtpyhop.find_plan(state0, [("build_web",)])

    if plan0 is False or plan0 is None:
        return {"success": False, "energy": None, "adaptation_time": None,
                "replan_depth": None, "triggered": False}

    live_state = create_initial_state(seed=seed)
    live_state.silk_capacity = silk_capacity_initial

    trigger_index = None
    for i, action in enumerate(plan0):
        name, args = action[0], action[1:]
        result = _ACTION_FUNCS[name](live_state, *args)
        if result is False:
            # Should not happen — plan0 is a valid plan for this exact
            # initial state — but fail loudly rather than silently.
            raise RuntimeError(f"perturbation trial: prefix replay diverged at {action}")
        live_state = result
        if live_state.proto_hub_exists:
            trigger_index = i + 1
            break

    if trigger_index is None:
        # Proto-hub never got established within this plan (shouldn't
        # happen for a successful plan, but guard against it) — nothing
        # meaningful to perturb.
        return {"success": None, "energy": None, "adaptation_time": None,
                "replan_depth": None, "triggered": False}

    _PERTURBATIONS[perturbation_type](live_state, rng)

    with contextlib.redirect_stdout(io.StringIO()):
        gtpyhop.set_verbose_level(0)
        reset_decomposition_counter()
        continuation = gtpyhop.find_plan(live_state, [("build_web",)])
        replan_depth = get_decomposition_counter()

    if continuation is False or continuation is None:
        return {"success": False, "energy": None, "adaptation_time": None,
                "replan_depth": replan_depth, "triggered": True}

    for action in continuation:
        name, args = action[0], action[1:]
        result = _ACTION_FUNCS[name](live_state, *args)
        if result is False:
            raise RuntimeError(f"perturbation trial: continuation replay diverged at {action}")
        live_state = result

    undisturbed_remaining = len(plan0) - trigger_index
    adaptation_time = len(continuation) - undisturbed_remaining

    return {
        "success": True,
        "energy": live_state.energy_expended,
        "adaptation_time": adaptation_time,
        "replan_depth": replan_depth,
        "triggered": True,
    }


# ---------------------------------------------------------------------------
# Group B (baseline): a single continuous step loop, perturbed in place.
# ---------------------------------------------------------------------------

def run_baseline_perturbation_trial(perturbation_type, seed, silk_capacity_initial=DEFAULT_SILK_CAPACITY,
                                     max_steps=_BASELINE_MAX_STEPS):
    """Returns the same-shaped dict as run_htn_perturbation_trial."""
    rng = random.Random(f"perturbation-{perturbation_type}-{seed}")
    state = create_initial_state(name="perturbation_baseline_state", seed=seed)
    state.silk_capacity = silk_capacity_initial
    walker_rng = random.Random(seed)

    steps_taken = 0
    triggered = False
    post_trigger_steps = 0

    while steps_taken < max_steps and not is_web_complete(state):
        candidates = enumerate_candidate_actions(state, walker_rng)
        if not candidates:
            break

        op_func, args = walker_rng.choice(candidates)
        steps_taken += 1
        if triggered:
            post_trigger_steps += 1

        result = op_func(state, *args)
        if result is not False:
            state = result

        if not triggered and state.proto_hub_exists:
            triggered = True
            _PERTURBATIONS[perturbation_type](state, rng)

    if not triggered:
        return {"success": None, "energy": None, "adaptation_time": None,
                "replan_depth": None, "triggered": False}

    success = is_web_complete(state)
    return {
        "success": success,
        "energy": state.energy_expended if success else None,
        "adaptation_time": post_trigger_steps if success else None,
        "replan_depth": None,  # no task hierarchy — not applicable
        "triggered": True,
    }


# ---------------------------------------------------------------------------
# Trial sweep
# ---------------------------------------------------------------------------

def run_perturbation_trials(perturbation_types=("resource_depletion", "structural_failure", "predator"),
                             n_runs=200, base_seed=2000, silk_capacity_initial=DEFAULT_SILK_CAPACITY,
                             verbose=True):
    """
    Run both groups n_runs times (paired seeds) for each perturbation type.

    Returns
    -------
    list of dict, one row per (group, perturbation_type):
        {group, perturbation, n_runs, triggered, successes, success_rate,
         energy_mean, adaptation_time_mean, adaptation_time_stdev,
         replan_depth_mean}
    """
    results = []
    runners = {
        "htn": lambda pt, s: run_htn_perturbation_trial(pt, s, silk_capacity_initial),
        "baseline": lambda pt, s: run_baseline_perturbation_trial(pt, s, silk_capacity_initial),
    }

    for perturbation_type in perturbation_types:
        for group, runner in runners.items():
            triggered = 0
            successes = 0
            energies = []
            adaptation_times = []
            replan_depths = []

            for trial in range(n_runs):
                seed = base_seed + trial
                r = runner(perturbation_type, seed)
                if not r["triggered"]:
                    continue
                triggered += 1
                if r["success"]:
                    successes += 1
                    energies.append(r["energy"])
                    adaptation_times.append(r["adaptation_time"])
                    if r["replan_depth"] is not None:
                        replan_depths.append(r["replan_depth"])

            row = {
                "group": group,
                "perturbation": perturbation_type,
                "n_runs": n_runs,
                "triggered": triggered,
                "successes": successes,
                "success_rate": successes / triggered if triggered else None,
                "energy_mean": statistics.mean(energies) if energies else None,
                "adaptation_time_mean": statistics.mean(adaptation_times) if adaptation_times else None,
                "adaptation_time_stdev": (statistics.stdev(adaptation_times)
                                          if len(adaptation_times) > 1 else 0.0),
                "replan_depth_mean": statistics.mean(replan_depths) if replan_depths else None,
            }
            results.append(row)

            if verbose:
                sr = row["success_rate"]
                sr_str = f"{sr:.3f}" if sr is not None else "n/a"
                ta = row["adaptation_time_mean"]
                ta_str = f"{ta:.1f}" if ta is not None else "n/a"
                print(
                    f"  [{group:8s}] {perturbation_type:20s} "
                    f"success_rate={sr_str} ({row['successes']}/{row['triggered']} triggered)  "
                    f"Ta_mean={ta_str}"
                )

    return results


def _write_csv(results, path):
    fieldnames = [
        "group", "perturbation", "n_runs", "triggered", "successes", "success_rate",
        "energy_mean", "adaptation_time_mean", "adaptation_time_stdev", "replan_depth_mean",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    parser = argparse.ArgumentParser(
        description="Perturbation trials: resource depletion, structural "
                     "failure, and predator interrupts, for HTN vs baseline."
    )
    parser.add_argument("--n-runs", type=int, default=200,
                         help="Trials per (group, perturbation) pair.")
    parser.add_argument("--perturbations", type=str, nargs="+",
                         default=["resource_depletion", "structural_failure", "predator"])
    parser.add_argument("--silk-capacity", type=float, default=DEFAULT_SILK_CAPACITY)
    parser.add_argument("--seed", type=int, default=2000)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    print("=" * 70)
    print("  Perturbation Trials — HTN (Group A) vs. Baseline (Group B)")
    print("=" * 70)
    print(f"  n_runs per (group, perturbation): {args.n_runs}")
    print(f"  perturbations: {args.perturbations}")
    print(f"  silk_capacity_initial: {args.silk_capacity}")
    print("-" * 70)

    results = run_perturbation_trials(
        perturbation_types=args.perturbations,
        n_runs=args.n_runs,
        base_seed=args.seed,
        silk_capacity_initial=args.silk_capacity,
    )

    if args.out:
        _write_csv(results, args.out)
        print(f"  Results written to: {args.out}")

    return results


if __name__ == "__main__":
    main()
