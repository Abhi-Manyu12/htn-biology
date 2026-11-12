"""
main.py — Entry point for the Zschokke 1996 orb web HTN planner.

Creates the GTPyhop domain, registers all operators and methods, builds the
initial state, and runs the planner to produce a web-construction plan.
"""

import gtpyhop
from .state import create_initial_state
from . import operators as ops
from . import methods as mtd
from .operators import _movement_cost
from .instrumentation import (
    count_calls_all,
    get_decomposition_counter,
    reset_decomposition_counter,
)

# Set by run_planner() after each find_plan() call — "tree nodes visited
# during planning" (Way-Forward Part 1, Formal Evaluation Protocol,
# Decomposition Depth (D)), read via get_last_decomposition_depth().
_last_decomposition_depth = None


def get_last_decomposition_depth():
    """Decomposition-node count from the most recent run_planner() call."""
    return _last_decomposition_depth


# ---------------------------------------------------------------------------
# Domain setup
# ---------------------------------------------------------------------------

def setup_domain():
    """
    Create the GTPyhop planning domain, register operators and methods.

    Returns
    -------
    gtpyhop.Domain
    """
    domain = gtpyhop.Domain("zschokke1996_orb_web")

    # ── Register primitive operators (actions) ──────────────────────────
    gtpyhop.declare_actions(
        ops.walk,
        ops.anchor,
        ops.lay_thread,
        ops.attach_dragline,
        ops.remove_thread,
        ops.drop_down,
        ops.swing_tarzan,
        ops.reel_up,
        ops.insert_radius,
        ops.mark_proto_hub,
        ops.lay_frame_thread,
        ops.lay_radius,
        ops.build_spiral_segment,
        ops.mark_web_complete,
        ops.flee_from_predator,
        # Marker pseudo-operators from methods.py
        mtd.mark_high_thread_done,
        mtd.mark_auxiliary_spiral_done,
        mtd.mark_capture_spiral_done,
    )

    # ── Register HTN methods ────────────────────────────────────────────
    # Each method function is wrapped with count_calls() so every attempted
    # decomposition (successful or backtracked-away-from) increments the
    # shared decomposition-node counter — see instrumentation.py and
    # get_last_decomposition_depth().

    # Top-level task
    gtpyhop.declare_task_methods(
        "build_web",
        *count_calls_all(mtd.build_web),
    )

    # Early stages — exploration & bridging
    gtpyhop.declare_task_methods(
        "explore_and_bridge",
        *count_calls_all(mtd.explore_bridge_walk_detour),
    )

    # Establish highest thread (two alternatives for variability)
    gtpyhop.declare_task_methods(
        "establish_high_thread",
        *count_calls_all(mtd.establish_high_thread_direct, mtd.establish_high_thread_via_climb),
    )

    # Proto-hub — THREE alternatives modelling Zschokke's observed variability
    # GTPyhop will backtrack among these if one fails
    gtpyhop.declare_task_methods(
        "establish_proto_hub",
        *count_calls_all(
            mtd.establish_proto_hub_done,
            mtd.establish_proto_hub_via_walk,
            mtd.establish_proto_hub_via_drop,
            mtd.establish_proto_hub_via_tarzan,
        ),
    )

    # Later stages — stereotyped
    gtpyhop.declare_task_methods(
        "build_remaining_web",
        *count_calls_all(mtd.build_remaining_web),
    )

    gtpyhop.declare_task_methods(
        "build_frame",
        *count_calls_all(mtd.build_frame_method),
    )

    gtpyhop.declare_task_methods(
        "build_radii",
        *count_calls_all(mtd.build_radii_method),
    )

    gtpyhop.declare_task_methods(
        "build_auxiliary_spiral",
        *count_calls_all(mtd.build_auxiliary_spiral_method),
    )

    gtpyhop.declare_task_methods(
        "build_capture_spiral",
        *count_calls_all(mtd.build_capture_spiral_method),
    )

    # Finalisation
    gtpyhop.declare_task_methods(
        "finalise_web",
        *count_calls_all(mtd.finalise_web),
    )

    return domain


# ---------------------------------------------------------------------------
# Plan execution
# ---------------------------------------------------------------------------

def run_planner(verbose_level=1, seed=None):
    """
    Set up domain, create initial state, and find a plan.

    Parameters
    ----------
    verbose_level : int
        0 = silent, 1 = results only, 2 = recursive calls, 3 = full detail.
    seed : int, optional
        RNG seed for this run — forwarded to create_initial_state(). See
        state.create_initial_state / stochastic.make_rng for precedence
        (this argument > config.stochastic.seed > OS entropy). Irrelevant
        when config.stochastic.enabled is false (the default).

    Returns
    -------
    list or False
        The plan (list of action tuples), or False if planning fails.
    """
    domain = setup_domain()

    state = create_initial_state(seed=seed)

    gtpyhop.set_verbose_level(verbose_level)

    print("=" * 70)
    print("  Zschokke 1996 — Orb Web Construction HTN Planner")
    print("  Species: Araneus diadematus (European garden spider)")
    print("=" * 70)
    print()

    state.display("Initial state")
    if state.seed_used is not None:
        print(f"RNG seed: {state.seed_used}")
        print()

    print("Finding plan for task: ('build_web',)")
    print("-" * 70)

    reset_decomposition_counter()
    plan = gtpyhop.find_plan(state, [("build_web",)])
    global _last_decomposition_depth
    _last_decomposition_depth = get_decomposition_counter()

    print()
    if plan is False or plan is None:
        print("✗  No plan found.")
        return False

    print("=" * 70)
    print(f"    Plan found — {len(plan)} actions")
    print("=" * 70)
    print()

    # Categorise and display the plan
    _print_plan_summary(plan, state)

    return plan


# Dispatch table from action name to the real operator/pseudo-operator
# function that implements it — used by replay_plan() below.
_ACTION_FUNCS = {
    "walk": ops.walk,
    "anchor": ops.anchor,
    "lay_thread": ops.lay_thread,
    "attach_dragline": ops.attach_dragline,
    "remove_thread": ops.remove_thread,
    "drop_down": ops.drop_down,
    "swing_tarzan": ops.swing_tarzan,
    "reel_up": ops.reel_up,
    "insert_radius": ops.insert_radius,
    "mark_proto_hub": ops.mark_proto_hub,
    "lay_frame_thread": ops.lay_frame_thread,
    "lay_radius": ops.lay_radius,
    "build_spiral_segment": ops.build_spiral_segment,
    "mark_web_complete": ops.mark_web_complete,
    "flee_from_predator": ops.flee_from_predator,
    "mark_high_thread_done": mtd.mark_high_thread_done,
    "mark_auxiliary_spiral_done": mtd.mark_auxiliary_spiral_done,
    "mark_capture_spiral_done": mtd.mark_capture_spiral_done,
}


def replay_plan(plan, seed=None):
    """
    Execute a found plan for real against a fresh initial state, applying
    each action's actual operator function (unlike _estimate_energy, which
    only sums distances without touching state) — so state.threads and
    state.energy_expended end up genuinely populated afterward. Needed for
    anything that reads the final web structure, e.g. utils.efficiency_ratio.

    Raises
    ------
    RuntimeError
        If an action fails to apply — would mean the plan GTPyhop just
        found doesn't actually execute against its own initial state,
        which should never happen for a valid plan.
    """
    state = create_initial_state(seed=seed)
    for action in plan:
        name, args = action[0], action[1:]
        func = _ACTION_FUNCS[name]
        result = func(state, *args)
        if result is False:
            raise RuntimeError(
                f"replay_plan: action {name}{tuple(args)} failed to apply "
                f"— plan diverged from its own initial state."
            )
        state = result
    return state


def _print_plan_summary(plan, initial_state):
    """Pretty-print the plan grouped by construction phase."""
    phase_labels = {
        "walk":                  "Movement",
        "anchor":                "Anchor",
        "lay_thread":            "Thread",
        "attach_dragline":       "Dragline",
        "remove_thread":         "Remove",
        "drop_down":             "Drop",
        "swing_tarzan":          "Tarzan",
        "reel_up":               "Reel-up",
        "insert_radius":         "Proto-radius",
        "mark_proto_hub":        "Proto-hub ✓",
        "lay_frame_thread":      "Frame",
        "lay_radius":            "Radius",
        "build_spiral_segment":  "Spiral",
        "mark_web_complete":     "Complete ✓",
        "mark_high_thread_done":       "Bridge ✓",
        "mark_auxiliary_spiral_done":   "Aux. spiral ✓",
        "mark_capture_spiral_done":    "Cap. spiral ✓",
    }

    print("Step  Phase            Action")
    print("─" * 70)
    for i, action in enumerate(plan, 1):
        action_name = action[0]
        label = phase_labels.get(action_name, action_name)
        args = ", ".join(str(a) for a in action[1:]) if len(action) > 1 else ""
        print(f" {i:3d}  {label:<16s} {action_name}({args})")

    # Estimate energy by replaying on a fresh state
    print()
    print("─" * 70)
    energy = _estimate_energy(plan, initial_state)
    if energy is not None:
        print(f"  Estimated energy expended: {energy:.1f} cm walked")
        print(f"  (Zschokke median exploration: 5.61 cm on simple structure)")
    print()


def _estimate_energy(plan, initial_state):
    """
    Replay the plan on a fresh state copy to compute total energy.
    Returns the total distance or None on failure.
    """
    total = 0.0
    pos = initial_state.spider_pos
    for action in plan:
        name = action[0]
        if name in ("walk", "lay_thread", "lay_frame_thread", "lay_radius",
                     "drop_down", "swing_tarzan", "reel_up",
                     "build_spiral_segment"):
            if len(action) >= 3:
                n1, n2 = action[1], action[2]
                total += _movement_cost(initial_state, n1, n2)
                pos = n2

    return total


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Command-line entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Zschokke 1996 orb web HTN planner")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="RNG seed for this run (overrides config.stochastic.seed). "
             "Only affects the plan if config.stochastic.enabled is true.",
    )
    parser.add_argument(
        "--verbose", type=int, default=1, choices=[0, 1, 2, 3],
        help="0 = silent, 1 = results only, 2 = recursive calls, 3 = full detail.",
    )
    args = parser.parse_args()

    run_planner(verbose_level=args.verbose, seed=args.seed)


if __name__ == "__main__":
    main()
