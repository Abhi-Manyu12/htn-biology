#!/usr/bin/env python3
"""
visualize_updated.py — Generate plan data and open the web visualization for
the config-driven Zschokke 1996 HTN model (spider_web_htn_updated).

Mirrors spider_web_htn's visualize.py / spider_web_astar's visualize_astar.py,
but pulls node coordinates, domain setup and initial state from
spider_web_htn_updated instead — including the multi-turn logarithmic
(auxiliary) / Archimedean (capture) spiral waypoints from spiral_geometry.py,
so the visualization renders the real spiral curves rather than a single
straight pass between the 7 boundary anchors.

Usage:
    python3 -m spider_web_htn_updated.visualize_updated
"""

import json
import os
import webbrowser
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gtpyhop
from spider_web_htn_updated.main import setup_domain
from spider_web_htn_updated.state import create_initial_state
from spider_web_htn_updated.operators import _movement_cost
from spider_web_htn_updated.utils import NODE_COORDS


def determine_macro_phase(action_name, args, prev_phase):
    """Determine the macro construction phase for an action."""
    mapping = {
        'attach_dragline': 'exploration',
        'mark_high_thread_done': 'exploration',
        'anchor': 'proto_hub',
        'insert_radius': 'proto_hub',
        'mark_proto_hub': 'proto_hub',
        'lay_frame_thread': 'frame',
        'lay_radius': 'radii',
        'mark_auxiliary_spiral_done': 'auxiliary_spiral',
        'mark_capture_spiral_done': 'capture_spiral',
        'mark_web_complete': 'complete',
    }
    if action_name in mapping:
        return mapping[action_name]
    if action_name == 'build_spiral_segment' and len(args) > 2:
        return 'auxiliary_spiral' if args[2] == 'auxiliary_spiral' else 'capture_spiral'
    if action_name == 'lay_thread' and len(args) > 2 and args[2] == 'dragline':
        return 'proto_hub'
    # Pure movement actions don't define a phase on their own — keep whatever
    # phase we were already in.
    return prev_phase


def export_plan_data(seed=None):
    """Run the planner and export plan data in the shape index_updated.html expects."""
    domain = setup_domain()
    state = create_initial_state(seed=seed)
    gtpyhop.set_verbose_level(0)

    plan = gtpyhop.find_plan(state, [("build_web",)])

    if not plan:
        print("✗ No plan found!")
        return None

    print(f"✓ Plan found — {len(plan)} actions")

    # Energy is re-derived from the static cost model (calculate_distance +
    # optional wind multiplier), the same approach main.py::_estimate_energy
    # uses, rather than replayed through the operators. This is exact when
    # config.stochastic.wind.enabled is false (the default); with wind
    # enabled, a fresh replay RNG stream will diverge slightly from the one
    # actually consumed during planning.
    energy_state = create_initial_state(seed=seed)

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
                step_energy = _movement_cost(energy_state, str(args[0]), str(args[1]))

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

    # This file lives in spider_web_htn_updated/, so visualization/ is one
    # level up (shared with spider_web_htn's and spider_web_astar's viz).
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    viz_dir = os.path.join(project_root, "visualization")
    os.makedirs(viz_dir, exist_ok=True)

    data_path = os.path.join(viz_dir, "plan_data_updated.js")
    with open(data_path, "w") as f:
        f.write(f"const PLAN_DATA = {json.dumps(data, indent=2)};\n")
    print(f"  Data written to: {data_path}")

    html_path = os.path.join(viz_dir, "index_updated.html")
    if os.path.exists(html_path):
        url = f"file://{html_path}"
        print(f"  Opening: {url}")
        webbrowser.open(url)
    else:
        print(f"  ⚠ HTML not found: {html_path}")


if __name__ == "__main__":
    main()
