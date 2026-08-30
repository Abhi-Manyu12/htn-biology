#!/usr/bin/env python3
"""
visualize_astar.py — Generate A* plan data and open the web visualization.

Mirrors spider_web_htn's visualize.py so both planners can feed the same
visualization frontend and be compared side-by-side.

Usage:
    python3 visualize_astar.py
"""

import json
import os
import webbrowser
import sys

sys.path.insert(0, os.path.dirname(__file__))

from spider_web_htn.state import create_initial_state
from spider_web_htn.utils import NODE_COORDS

from spider_web_astar.astar import find_plan
from spider_web_astar.operators import _successor
from spider_web_astar.state import copy_state


def determine_macro_phase(action_name, args, prev_phase):
    """
    Determine the macro construction phase for an A* action.

    A*'s flat action set differs from the HTN's (no separate
    mark_top_frame_done / mark_auxiliary_spiral_done / relocate_hub /
    construct_frame_with_radius — those are HTN methods; A* folds the same
    effects into plain primitives + wrapper-set flags, see operators.py).
    """
    mapping = {
        'anchor': 'proto_hub',
        'insert_radius': 'proto_hub',
        'mark_proto_hub': 'proto_hub',
        'lay_frame_thread': 'frame',
        'lay_radius': 'radii',
        'mark_web_complete': 'complete',
    }
    if action_name in mapping:
        return mapping[action_name]
    if action_name == 'build_spiral_segment' and len(args) > 2:
        return 'auxiliary_spiral' if args[2] == 'auxiliary_spiral' else 'capture_spiral'
    # Pure movement / setup actions don't define a phase on their own —
    # keep whatever phase we were already in.
    if action_name in ('walk', 'lay_thread', 'drop_down', 'swing_tarzan',
                       'attach_dragline', 'remove_thread', 'reel_up'):
        return prev_phase
    return prev_phase


def export_plan_data(weight=3.0, time_limit_s=120.0, energy_limit=None):
    """Run the A* planner and export plan data in the same shape as the HTN exporter."""
    initial = create_initial_state()

    result = find_plan(
        initial,
        time_limit_s=time_limit_s,
        weight=weight,
        energy_limit=energy_limit,
    )

    if not result.success:
        print("✗ No plan found!")
        return None

    print(f"✓ Plan found — {len(result.plan)} actions, weight={weight}")

    steps = []
    prev_phase = 'exploration'
    cumulative_energy = 0.0

    # Replay the plan through the real operators to get EXACT per-step cost
    # (rather than re-deriving it from straight-line distance, as the HTN
    # exporter does) — we have the true cost model available here, so use it.
    state = copy_state(initial)

    for action in result.plan:
        action_list = list(action)
        action_name = action_list[0]
        args = action_list[1:]

        macro_phase = determine_macro_phase(action_name, args, prev_phase)

        applied = _successor(state, action_name, args)
        if applied is None:
            # Should not happen — the plan was just found by the same
            # operator model — but fail loudly rather than silently if it
            # ever does, since it would mean plan replay diverged from
            # what A* actually searched.
            raise RuntimeError(
                f"Replay diverged at step {len(steps) + 1}: "
                f"{action_name}{tuple(args)} failed to apply."
            )
        cost, new_state = applied
        step_energy = cost
        state = new_state

        cumulative_energy += step_energy

        steps.append({
            "action": action_list,
            "name": action_name,
            "args": args,
            "phase": macro_phase,
            "energy": round(step_energy, 1),
            "cumulative_energy": round(cumulative_energy, 1),
        })
        prev_phase = macro_phase

    coords = {name: list(xy) for name, xy in NODE_COORDS.items()}

    return {
        "node_coords": coords,
        "steps": steps,
        "total_steps": len(steps),
        "total_energy": round(cumulative_energy, 1),
    }


def main():
    data = export_plan_data()
    if data is None:
        return

    # Layout: htn-biology/{spider_web_htn, spider_web_astar, visualization}/
    # This file lives in spider_web_astar/, so visualization/ is one level up.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    viz_dir = os.path.join(project_root, "visualization")
    os.makedirs(viz_dir, exist_ok=True)

    data_path = os.path.join(viz_dir, "plan_data_astar.js")
    with open(data_path, "w") as f:
        f.write(f"const PLAN_DATA = {json.dumps(data, indent=2)};\n")
    print(f"  Data written to: {data_path}")

    html_path = os.path.join(viz_dir, "index_astar.html")
    if os.path.exists(html_path):
        url = f"file://{html_path}"
        print(f"  Opening: {url}")
        webbrowser.open(url)
    else:
        print(f"  ⚠ HTML not found: {html_path}")
        print("  Run make_index_astar.py once to create it from index.html.")


if __name__ == "__main__":
    main()