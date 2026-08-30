"""
main.py — Entry point for the A* planner.

Mirrors spider_web_htn.main.run_planner so the two planners can be invoked
the same way and their outputs compared.
"""
from spider_web_htn.state import create_initial_state
from .astar import find_plan


def run_astar_planner(verbose_level=1, time_limit_s=120.0,
                      max_nodes=200000, energy_limit=None, weight=3.0):
    """
    Run A* on the same initial state as the HTN planner.

    Returns
    -------
    dict with keys: success, plan, energy, nodes_expanded, wall_time,
                    plan_length, max_depth
    """
    import sys
    # Force UTF-8 on stdout to handle unicode characters on Windows.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    initial = create_initial_state()

    print("=" * 70)
    print("  Zschokke 1996 - Orb Web Construction A* Planner (flat-state)")
    print("  Species: Araneus diadematus (European garden spider)")
    print("=" * 70)
    print()

    if verbose_level >= 1:
        initial.display("Initial state")

    print("Finding plan via A* (goal: web_complete == True)")
    print("-" * 70)

    result = find_plan(initial,
                       time_limit_s=time_limit_s,
                       max_nodes=max_nodes,
                       energy_limit=energy_limit,
                       weight=weight)

    print()
    if result.success:
        print("=" * 70)
        print(f"  [OK] Plan found - {len(result.plan)} actions")
        print(f"     Energy:       {result.energy:.2f} cm walked")
        print(f"     Nodes expanded: {result.nodes_expanded}")
        print(f"     Wall time:    {result.wall_time:.3f} s")
        print("=" * 70)
        if verbose_level >= 1:
            _print_plan_summary(result.plan)
        if verbose_level >= 2:
            _print_plan_order(result.plan)
    else:
        print("=" * 70)
        print("  [FAIL] No plan found within budget")
        print(f"     Nodes expanded:  {result.nodes_expanded}")
        print(f"     Nodes generated: {result.generated_nodes}")
        print(f"     Max frontier:    {result.max_open_size}")
        print(f"     Max depth:       {result.max_depth}")
        print(f"     Wall time:       {result.wall_time:.3f} s")

        if result.lower_bound is not None:
            tag = "VALID admissible bound" if result.lower_bound_valid else \
                  "informative only, NOT a sound bound (weight > 1.0)"
            print(f"     Lower bound on optimal cost: {result.lower_bound:.2f} ({tag})")

        if result.final_state is not None:
            s = result.final_state

            print("\n  Best state reached:")
            print(f"     Proto hub exists: {s.proto_hub_exists}")
            print(f"     Proto hub position: {s.proto_hub_pos}")
            print(f"     Proto radii: {s.proto_radii_count}")
            print(f"     Frames:      {s.frame_count}")
            print(f"     Top frame done: {s.top_frame_done}")
            print(f"     Radii:       {s.radii_count}")
            from spider_web_htn.utils import count_threads_of_type
            print(f"     Aux spiral segments: {count_threads_of_type(s.threads, 'auxiliary_spiral')}")
            print(f"     Capture spiral segments: {count_threads_of_type(s.threads, 'capture_spiral')}")
            print(f"     Capture spiral done: {s.capture_spiral_done}")
            print(f"     Position:    {s.spider_pos}")
            print(f"     Energy:      {s.energy_expended:.2f}")

        print("=" * 70)


def _print_plan_summary(plan):
    """Pretty-print the plan grouped by action type."""
    from collections import Counter
    counts = Counter()
    for action in plan:
        name = action[0]
        # Strip suffixes like _dragline / _bridge to group.
        base = name.split("_")[0] if name.endswith(("_dragline", "_bridge")) else name
        counts[base] += 1
    print()
    print("Action breakdown:")
    for name, n in counts.most_common():
        print(f"  {name:<25s} {n:3d}")


def _print_plan_order(plan):
    """Print the exact, ordered action sequence (not just grouped counts)."""
    print()
    print("Exact action order:")
    for i, action in enumerate(plan, start=1):
        name = action[0]
        args = action[1:]
        args_str = ", ".join(str(a) for a in args)
        print(f"  {i:3d}. {name}({args_str})")


def main():
    run_astar_planner(verbose_level=2)


if __name__ == "__main__":
    main()