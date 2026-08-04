"""
state.py — World state representation for the FAP model.

Tracks:
- Spider position & node set
- Thread network (with silk chemistry tags)
- Silk type ("dry_structural" vs "sticky_capture")
- FAP macro-stage completion flags
- Energy expenditure
"""

import gtpyhop
from .utils import FAP_NODE_COORDS

# Supporting structure rigid relations
rigid = gtpyhop.State("fap_rigid")
rigid.structure_nodes = set(FAP_NODE_COORDS.keys())
rigid.walkable_edges = [
    ("anchor_top_left", "bridge_midpoint"),
    ("bridge_midpoint", "anchor_top_right"),
    ("anchor_top_right", "frame_right_mid"),
    ("frame_right_mid", "anchor_bottom_right"),
    ("anchor_bottom_right", "anchor_bottom_stem"),
    ("anchor_bottom_stem", "anchor_bottom_left"),
    ("anchor_bottom_left", "frame_left_mid"),
    ("frame_left_mid", "anchor_top_left"),
]


def create_fap_initial_state(name="fap_state_0"):
    """Create initial state for FAP web construction."""
    s = gtpyhop.State(name)

    # Spider position (starts at top left anchor)
    s.spider_pos = "anchor_top_left"

    # Known nodes & thread graph
    s.nodes = set(rigid.structure_nodes)
    s.threads = []  # list of (n1, n2, thread_type, silk_chemistry)

    # Internal physiology (FAP Step 1: Silk Chemistry)
    s.silk_chemistry = "dry_structural"  # switches to "sticky_capture" in Stage 4

    # FAP Macro-Stage Progress Flags
    s.bridge_established = False
    s.slack_line_attached = False
    s.y_frame_established = False

    s.spokes_count = 0
    s.last_spoke_side = "left"

    s.auxiliary_spiral_done = False
    s.capture_spiral_done = False
    s.stabilimentum_done = False
    s.web_complete = False

    s.recycled_threads_count = 0
    s.energy_expended = 0.0

    return s
