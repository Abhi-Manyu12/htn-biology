#!/usr/bin/env python3
"""
visualize.py — Generate plan data and open the web visualization.

Usage:
    python3 visualize.py
"""

import json
import os
import webbrowser
import sys

sys.path.insert(0, os.path.dirname(__file__))

from spider_web_htn.main import setup_domain
from spider_web_htn.state import create_initial_state
from spider_web_htn.utils import NODE_COORDS, calculate_distance
import gtpyhop


def determine_macro_phase(action_name, args, prev_phase):
    """Determine the macro construction phase for an action."""
    mapping = {
        'attach_dragline': 'exploration',
        'mark_high_thread_done': 'exploration',
        'anchor': 'proto_hub',
        'insert_radius': 'proto_hub',
        'mark_proto_hub': 'proto_hub',
        'relocate_hub': 'hub_relocate',
        'mark_top_frame_done': 'hub_relocate',
        'construct_frame_with_radius': 'frame',
        'lay_radius': 'radii',
        'construct_secondary_radius': 'radii',
        'remove_auxiliary_spiral_segment': 'capture_spiral',
        'mark_auxiliary_spiral_done': 'auxiliary_spiral',
        'mark_capture_spiral_done': 'capture_spiral',
        'mark_web_complete': 'complete',
    }
    if action_name in mapping:
        return mapping[action_name]
    if action_name == 'build_spiral_segment' and len(args) > 2:
        return 'auxiliary_spiral' if args[2] == 'auxiliary_spiral' else 'capture_spiral'
    if action_name == 'lay_frame_thread':
        return prev_phase if prev_phase in ('hub_relocate', 'exploration') else 'frame'
    if action_name == 'lay_thread' and len(args) > 2 and args[2] == 'dragline':
        return 'proto_hub'
    if action_name in ('drop_down', 'swing_tarzan'):
        return 'proto_hub'
    return prev_phase


def export_plan_data():
    """Run the planner and export plan data."""
    domain = setup_domain()
    state = create_initial_state()
    gtpyhop.set_verbose_level(0)

    plan = gtpyhop.find_plan(state, [("build_web",)])

    if not plan:
        print("✗ No plan found!")
        return None

    print(f"✓ Plan found — {len(plan)} actions")

    steps = []
    prev_phase = 'exploration'
    cumulative_energy = 0.0

    for action in plan:
        action_list = list(action)
        action_name = action_list[0]
        args = action_list[1:]

        macro_phase = determine_macro_phase(action_name, args, prev_phase)

        step_energy = 0.0
        if action_name in ('walk', 'lay_thread', 'lay_frame_thread', 'lay_radius',
                           'drop_down', 'swing_tarzan', 'reel_up',
                           'build_spiral_segment'):
            if len(args) >= 2 and args[0] and args[1]:
                step_energy = calculate_distance(str(args[0]), str(args[1]))
        elif action_name == 'construct_frame_with_radius':
            if len(args) >= 3:
                step_energy = (calculate_distance(str(args[0]), str(args[1])) +
                             calculate_distance(str(args[1]), str(args[2])) +
                             calculate_distance(str(args[2]), str(args[0])))
        elif action_name == 'relocate_hub' and len(args) >= 2:
            step_energy = calculate_distance(str(args[1]), 'anchor_top_center')

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

    viz_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visualization")
    os.makedirs(viz_dir, exist_ok=True)

    data_path = os.path.join(viz_dir, "plan_data.js")
    with open(data_path, "w") as f:
        f.write(f"const PLAN_DATA = {json.dumps(data, indent=2)};\n")
    print(f"  Data written to: {data_path}")

    html_path = os.path.join(viz_dir, "index.html")
    if os.path.exists(html_path):
        url = f"file://{html_path}"
        print(f"  Opening: {url}")
        webbrowser.open(url)
    else:
        print(f"  ⚠ HTML not found: {html_path}")


if __name__ == "__main__":
    main()
