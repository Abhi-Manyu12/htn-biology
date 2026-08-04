"""
main.py — GTPyhop Domain setup and runner for the 5 FAP Macro-Stages model.
"""

import gtpyhop
from .state import create_fap_initial_state
from . import operators as ops
from . import methods as mtd


def setup_fap_domain():
    """Create the GTPyhop domain for the FAP model and register all operators & methods."""
    domain = gtpyhop.Domain("fap_spider_web_model")

    # ── Register Primitive Operators ────────────────────────────────────
    gtpyhop.declare_actions(
        ops.walk,
        ops.lay_bridge_thread,
        ops.walk_to_midpoint,
        ops.attach_slack_line,
        ops.drop_down_to_anchor,
        ops.tighten_y_frame,
        ops.climb_up_and_out,
        ops.lay_loose_spoke,
        ops.pull_spoke_tight,
        ops.measure_angle_gap_check,
        ops.switch_silk_chemistry,
        ops.build_auxiliary_spiral_segment,
        ops.leg_guided_capture_dab,
        ops.bite_and_recycle_scaffolding,
        ops.construct_stabilimentum_segment,
        ops.mark_fap_complete,
        # Marker pseudo-operators
        mtd.mark_auxiliary_spiral_done,
        mtd.mark_capture_spiral_done,
        mtd.mark_stabilimentum_done,
    )

    # ── Register Task Methods for 5 FAP Macro-Stages ────────────────────
    gtpyhop.declare_task_methods("build_fap_web", mtd.build_fap_web)
    gtpyhop.declare_task_methods("fap_proto_web_y_frame", mtd.fap_proto_web_y_frame_method)
    gtpyhop.declare_task_methods("fap_radial_spokes", mtd.fap_radial_spokes_method)
    gtpyhop.declare_task_methods("fap_auxiliary_spiral", mtd.fap_auxiliary_spiral_method)
    gtpyhop.declare_task_methods("fap_capture_spiral", mtd.fap_capture_spiral_method)
    gtpyhop.declare_task_methods("fap_stabilimentum", mtd.fap_stabilimentum_method)
    gtpyhop.declare_task_methods("finalise_fap_web", mtd.finalise_fap_web)

    return domain


def run_fap_planner(verbose_level=1):
    """Run the HTN planner for the FAP model."""
    domain = setup_fap_domain()
    state = create_fap_initial_state()
    gtpyhop.set_verbose_level(verbose_level)

    print("=" * 70)
    print("  Orb Web Construction — 5 Fixed Action Patterns (FAPs) Model")
    print("  Behavioral & Ethological HTN Planner")
    print("=" * 70)
    print()

    state.display("Initial state")

    print("Finding plan for task: ('build_fap_web',)")
    print("-" * 70)

    plan = gtpyhop.find_plan(state, [("build_fap_web",)])

    print()
    if not plan:
        print("✗ No plan found.")
        return False

    print("=" * 70)
    print(f"  ✓ Plan found — {len(plan)} actions")
    print("=" * 70)
    print()

    _print_fap_summary(plan)
    return plan


def _print_fap_summary(plan):
    """Pretty print the plan grouped by FAP stage."""
    fap_labels = {
        "lay_bridge_thread":                "1. Bridge Thread",
        "walk_to_midpoint":                 "1. Walk Midpoint",
        "attach_slack_line":                "1. Attach Slack Line",
        "drop_down_to_anchor":              "1. Drop Down Anchor",
        "tighten_y_frame":                  "1. Y-Frame Tighten",
        "climb_up_and_out":                 "2. Up and Out",
        "lay_loose_spoke":                  "2. Spin Loose Line",
        "pull_spoke_tight":                 "2. Pull Spoke Tight",
        "measure_angle_gap_check":          "2. Leg Angle Measure ✓",
        "build_auxiliary_spiral_segment":   "3. Aux. Scaffolding",
        "switch_silk_chemistry":            "4. Silk Chemistry ⚗",
        "bite_and_recycle_scaffolding":     "4. Eat & Recycle ♻",
        "leg_guided_capture_dab":           "4. Leg-Guided Dab",
        "construct_stabilimentum_segment":  "5. Stabilimentum 🕸",
        "walk":                             "Movement",
        "mark_fap_complete":                "Web Complete ✓",
        "mark_auxiliary_spiral_done":       "Aux. Spiral ✓",
        "mark_capture_spiral_done":         "Capture Spiral ✓",
        "mark_stabilimentum_done":          "Stabilimentum ✓",
    }

    print("Step  FAP Stage & Action")
    print("─" * 70)
    for i, action in enumerate(plan, 1):
        name = action[0]
        label = fap_labels.get(name, name)
        args = ", ".join(str(a) for a in action[1:]) if len(action) > 1 else ""
        print(f" {i:3d}  {label:<24s} {name}({args})")
    print("─" * 70)

    energy = _estimate_fap_energy(plan)
    if energy is not None:
        print(f"  Estimated energy expended: {energy:.1f} cm walked / silk produced")
    print()


def _estimate_fap_energy(plan):
    """Replay plan actions to calculate cumulative energy expended in cm."""
    from .utils import calculate_distance

    total = 0.0
    for action in plan:
        name = action[0]
        args = action[1:]
        if name in ("walk", "lay_bridge_thread", "walk_to_midpoint",
                    "drop_down_to_anchor", "climb_up_and_out",
                    "build_auxiliary_spiral_segment", "leg_guided_capture_dab",
                    "construct_stabilimentum_segment"):
            if len(args) >= 2:
                total += calculate_distance(args[0], args[1])
        elif name == "tighten_y_frame":
            if len(args) >= 2:
                total += calculate_distance(args[0], args[1])
        elif name == "lay_loose_spoke":
            if len(args) >= 3:
                total += calculate_distance(args[0], args[1])
                total += calculate_distance(args[1], args[2])
    return total


def main():
    run_fap_planner(verbose_level=1)


if __name__ == "__main__":
    main()
