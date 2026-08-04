"""
state.py — State representation for the Zschokke 1996 orb web construction model.

The state tracks the spider's position, the thread network (as a graph),
construction progress flags, and cumulative energy expenditure.
"""

import gtpyhop

# ---------------------------------------------------------------------------
# Rigid relations — environmental constants that do not change during planning
# ---------------------------------------------------------------------------

rigid = gtpyhop.State("rigid")

# The nodes that form the supporting structure (always available)
rigid.structure_nodes = {
    "right_stick_top", "right_stick_mid", "right_stick_bottom",
    "left_stick_top", "left_stick_mid", "left_stick_bottom",
    "crossbar_right", "crossbar_left",
    "bottom_path",
    # Anchor points along the sticks and bottom path
    "anchor_left_upper", "anchor_left_lower",
    "anchor_right_upper", "anchor_right_lower",
    "anchor_top_center",
    "anchor_bottom_left", "anchor_bottom_center", "anchor_bottom_right",
}

# Physical connections along the supporting structure (spider can walk these
# without needing a silk thread).
rigid.walkable_edges = [
    ("right_stick_top", "right_stick_mid"),
    ("right_stick_mid", "crossbar_right"),
    ("crossbar_right", "right_stick_bottom"),
    ("right_stick_bottom", "bottom_path"),
    ("bottom_path", "left_stick_bottom"),
    ("left_stick_bottom", "crossbar_left"),
    ("crossbar_left", "left_stick_mid"),
    ("left_stick_mid", "left_stick_top"),
    # Direct vertical traversals along sticks
    ("right_stick_top", "crossbar_right"),
    ("right_stick_top", "right_stick_bottom"),
    ("left_stick_top", "crossbar_left"),
    ("left_stick_top", "left_stick_bottom"),
    ("right_stick_mid", "right_stick_bottom"),
    ("left_stick_mid", "left_stick_bottom"),
    # Anchor points on the LEFT stick (y-axis: 0 → 18)
    ("left_stick_top", "anchor_left_upper"),       # (0,18)→(0,15)
    ("anchor_left_upper", "left_stick_mid"),        # (0,15)→(0,12)
    ("left_stick_mid", "anchor_left_lower"),        # (0,12)→(0,6)
    ("anchor_left_lower", "crossbar_left"),         # (0,6)→(0,9)
    ("anchor_left_lower", "left_stick_bottom"),     # (0,6)→(0,0)
    # Anchor points on the RIGHT stick
    ("right_stick_top", "anchor_right_upper"),      # (16,18)→(16,15)
    ("anchor_right_upper", "right_stick_mid"),      # (16,15)→(16,12)
    ("right_stick_mid", "anchor_right_lower"),      # (16,12)→(16,6)
    ("anchor_right_lower", "crossbar_right"),       # (16,6)→(16,9)
    ("anchor_right_lower", "right_stick_bottom"),   # (16,6)→(16,0)
    # Anchor points along the bottom path
    ("left_stick_bottom", "anchor_bottom_left"),    # (0,0)→(3,0)
    ("anchor_bottom_left", "anchor_bottom_center"), # (3,0)→(8,0)
    ("anchor_bottom_center", "bottom_path"),        # (8,0)→(8,0) same point
    ("anchor_bottom_center", "anchor_bottom_right"),# (8,0)→(13,0)
    ("anchor_bottom_right", "right_stick_bottom"),  # (13,0)→(16,0)
    # Top bridging anchors (on the top horizontal thread between stick tops)
    ("left_stick_top", "anchor_top_center"),        # (0,18)→(8,18)
    ("anchor_top_center", "right_stick_top"),       # (8,18)→(16,18)
]


def _is_walkable(n1, n2):
    """Check if (n1, n2) is a walkable structural edge."""
    for a, b in rigid.walkable_edges:
        if (a == n1 and b == n2) or (a == n2 and b == n1):
            return True
    return False


# ---------------------------------------------------------------------------
# Initial state factory
# ---------------------------------------------------------------------------

def create_initial_state(name="web_state_0"):
    """
    Create a fresh initial state matching Zschokke's lab setup.

    The spider starts on the top of the right-hand stick.  The only known
    nodes are the supporting-structure nodes.  No threads exist yet.

    Returns
    -------
    gtpyhop.State
    """
    s = gtpyhop.State(name)

    # Spider position
    s.spider_pos = "right_stick_top"

    # Known nodes (starts with just the structure; web-nodes are added during
    # construction)
    s.nodes = set(rigid.structure_nodes)

    # Thread network: list of (node1, node2, thread_type)
    # thread_type ∈ {"bridge", "dragline", "proto_radius", "radius",
    #                "frame", "auxiliary_spiral", "capture_spiral"}
    s.threads = []

    # Proto-hub state
    s.proto_hub_exists = False
    s.proto_hub_pos = None
    s.proto_radii_count = 0

    # Later-stage progress
    s.radii_count = 0
    s.frame_count = 0
    s.top_frame_done = False
    s.hub_spiral_done = False
    s.auxiliary_spiral_done = False
    s.capture_spiral_done = False

    # Overall completion
    s.web_complete = False

    # Bridging
    s.bridge_established = False
    s.high_thread_established = False

    # Energy tracking (Zschokke's distance-as-cost metric, in cm)
    s.energy_expended = 0.0

    return s
