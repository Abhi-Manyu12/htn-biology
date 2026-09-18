"""
compare.py — Way-Forward Part 1, Step 5 ("Comparison"): runs Group A (the
HTN model) and Group B (the flat-state random-walker baseline) and reports
summary statistics side by side.

Usage:
    python -m spider_web_htn_updated.compare
    python -m spider_web_htn_updated.compare --n-seeds 100 --max-steps 8000

Group A is deterministic (with stochastic.enabled: false, the shipped
default), so it only needs to run once — its energy/action-count don't vary
across seeds. Group B is run across many seeds and aggregated, since it is
genuinely stochastic and a single run says little about its typical
behaviour.

Metrics reported map onto the roadmap's evaluation table (Way Forward.pdf,
"3. Quantitative Metrics"):
    Success Rate (Ps)       — fraction of Group B runs that reached
                              is_web_complete within the step budget.
                              Group A's HTN plan always succeeds by
                              construction (GTPyhop wouldn't return a plan
                              otherwise), so Ps(A) = 1.0 by definition.
    Efficiency Ratio (eta)  — energy_expended, reported directly here
                              (dividing by web area requires choosing an
                              area estimate for the irregular polygon the
                              radii trace out, which is left as a follow-up
                              rather than guessed at here).
    Decomposition Depth (D) — 0 for Group B (no hierarchy) vs. Group A's
                              actual HTN tree depth (not yet instrumented —
                              see note in main.py).
"""

import argparse
import statistics

from .main import run_planner
from .baseline import run_baseline
from .operators import _movement_cost
from .state import create_initial_state


def _htn_energy(plan):
    """Replay a plan on a fresh state to compute total energy (Group A)."""
    state = create_initial_state()
    total = 0.0
    for action in plan:
        name = action[0]
        if name in ("walk", "lay_thread", "lay_frame_thread", "lay_radius",
                     "drop_down", "swing_tarzan", "reel_up", "build_spiral_segment"):
            if len(action) >= 3:
                total += _movement_cost(state, action[1], action[2])
    return total


def run_comparison(n_seeds=30, max_steps=5000, verbose=True):
    """
    Run Group A once and Group B across n_seeds seeds; return a dict with
    both sets of results and summary statistics for Group B.
    """
    # --- Group A: HTN model (deterministic given stochastic.enabled=false) ---
    plan = run_planner(verbose_level=0)
    if plan is False:
        raise RuntimeError("Group A (HTN) failed to find a plan — check config.yaml")
    group_a = {
        "success_rate": 1.0,
        "actions": len(plan),
        "energy": _htn_energy(plan),
        "decomposition_depth": None,  # not yet instrumented, see main.py note
    }

    # --- Group B: flat-state random walker, across many seeds ---
    group_b_runs = [run_baseline(seed=s, max_steps=max_steps) for s in range(n_seeds)]
    successes = [r for r in group_b_runs if r["success"]]
    success_rate = len(successes) / n_seeds

    group_b = {
        "success_rate": success_rate,
        "n_seeds": n_seeds,
        "max_steps": max_steps,
        "mean_energy_successful": (
            statistics.mean(r["energy_expended"] for r in successes) if successes else None
        ),
        "stdev_energy_successful": (
            statistics.stdev(r["energy_expended"] for r in successes) if len(successes) > 1 else None
        ),
        "mean_steps_successful": (
            statistics.mean(r["steps_taken"] for r in successes) if successes else None
        ),
        "decomposition_depth": 0,
        "raw_runs": group_b_runs,
    }

    if verbose:
        _print_comparison(group_a, group_b)

    return {"group_a": group_a, "group_b": group_b}


def _print_comparison(group_a, group_b):
    print("=" * 70)
    print("  Group A (HTN)  vs.  Group B (Flat-State Random Walker)")
    print("=" * 70)
    print()
    print(f"{'Metric':<28}{'Group A (HTN)':<22}{'Group B (baseline)'}")
    print("-" * 70)
    print(f"{'Success rate':<28}{group_a['success_rate']:<22.2f}{group_b['success_rate']:.2f}"
          f"  ({group_b['n_seeds']} seeds, {group_b['max_steps']} step budget)")

    b_energy = (f"{group_b['mean_energy_successful']:.1f} +/- "
                f"{group_b['stdev_energy_successful']:.1f}"
                if group_b["mean_energy_successful"] is not None else "n/a (no successes)")
    print(f"{'Energy (cm)':<28}{group_a['energy']:<22.1f}{b_energy}")

    b_steps = (f"{group_b['mean_steps_successful']:.0f}"
               if group_b["mean_steps_successful"] is not None else "n/a")
    print(f"{'Actions/steps':<28}{group_a['actions']:<22}{b_steps}")

    print(f"{'Decomposition depth':<28}{'n/a (not instrumented)':<22}{group_b['decomposition_depth']}")
    print()
    if group_b["mean_energy_successful"] is not None:
        ratio = group_b["mean_energy_successful"] / group_a["energy"]
        print(f"  Group B uses ~{ratio:.1f}x the energy of Group A on average (successful runs only).")
    print()
    print("  Caveat: Group B's completion criterion shares the same weak")
    print("  markers as the HTN domain (mark_proto_hub / mark_*_spiral_done")
    print("  check counts/flags, not full structural coherence), so a")
    print("  'success' for Group B does not guarantee as topologically sound")
    print("  a web as Group A's rigid, sequential construction guarantees.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Compare Group A (HTN) vs Group B (baseline)")
    parser.add_argument("--n-seeds", type=int, default=30,
                         help="Number of seeded Group B runs to aggregate")
    parser.add_argument("--max-steps", type=int, default=5000,
                         help="Step budget per Group B run")
    args = parser.parse_args()
    run_comparison(n_seeds=args.n_seeds, max_steps=args.max_steps)


if __name__ == "__main__":
    main()