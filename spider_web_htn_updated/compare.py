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

Metrics reported map onto the roadmap's evaluation table (future plan.pdf,
Part 1, "3. Quantitative Metrics"):
    Success Rate (Ps)       — fraction of Group B runs that reached
                              is_web_complete within the step budget.
                              Group A's HTN plan always succeeds by
                              construction (GTPyhop wouldn't return a plan
                              otherwise), so Ps(A) = 1.0 by definition.
    Efficiency Ratio (eta)  — S_used / Area_web (utils.efficiency_ratio),
                              where Area_web is the convex-hull area of the
                              constructed web's structural nodes
                              (utils.compute_web_area) — a geometric
                              estimate from the simulated output, not the
                              config's literature figure (different scale).
    Decomposition Depth (D) — 0 for Group B (no hierarchy) vs. Group A's
                              actual HTN decomposition-node count, from
                              main.get_last_decomposition_depth().
"""

import argparse
import statistics

from .main import run_planner, replay_plan, get_last_decomposition_depth
from .baseline import run_baseline
from .utils import efficiency_ratio, compute_web_area
from .config_loader import CONFIG


def run_comparison(n_seeds=30, max_steps=5000, verbose=True):
    """
    Run Group A once and Group B across n_seeds seeds; return a dict with
    both sets of results and summary statistics for Group B.
    """
    # --- Group A: HTN model (deterministic given stochastic.enabled=false) ---
    plan = run_planner(verbose_level=0)
    if plan is False:
        raise RuntimeError("Group A (HTN) failed to find a plan — check config.yaml")
    final_state = replay_plan(plan)
    group_a = {
        "success_rate": 1.0,
        "actions": len(plan),
        "energy": final_state.energy_expended,
        "web_area": compute_web_area(final_state),
        "eta": efficiency_ratio(final_state),
        "decomposition_depth": get_last_decomposition_depth(),
    }

    # --- Group B: flat-state random walker, across many seeds ---
    group_b_runs = [run_baseline(seed=s, max_steps=max_steps) for s in range(n_seeds)]
    successes = [r for r in group_b_runs if r["success"]]
    success_rate = len(successes) / n_seeds
    etas = [efficiency_ratio(r["final_state"]) for r in successes]
    etas = [e for e in etas if e is not None]

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
        "mean_eta": statistics.mean(etas) if etas else None,
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

    a_eta = f"{group_a['eta']:.3f}" if group_a["eta"] is not None else "n/a"
    b_eta = f"{group_b['mean_eta']:.3f}" if group_b["mean_eta"] is not None else "n/a"
    print(f"{'Efficiency eta (cm/cm^2)':<28}{a_eta:<22}{b_eta}")
    print(f"{'Web area (cm^2)':<28}{group_a['web_area']:<22.1f}")

    print(f"{'Decomposition depth':<28}{group_a['decomposition_depth']:<22}{group_b['decomposition_depth']}")
    print()
    if group_b["mean_energy_successful"] is not None:
        ratio = group_b["mean_energy_successful"] / group_a["energy"]
        print(f"  Group B uses ~{ratio:.1f}x the energy of Group A on average (successful runs only).")
    print()
    print(f"  Reference (Hesselberg & Vollrath 2004 control web, different scale —")
    print(f"  a full-size outdoor web vs. this {CONFIG['environment']['frame_width']:.0f}x"
          f"{CONFIG['environment']['frame_height']:.0f}cm lab rig, not directly comparable):")
    print(f"  area_web_cm2 = {CONFIG['empirical']['area_web_cm2']:.1f} "
          f"+/- {CONFIG['empirical'].get('area_web_se_cm2', 0):.1f}")
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