"""
methods.py — HTN Task decompositions for the 5 FAP Macro-Stages:

1. The Proto-Web & Frame FAP (Y-Shape Core)
2. Radial Spoke Construction FAP (Leg angle measurement & tension balance)
3. Auxiliary (Scaffolding) Spiral FAP
4. Capture (Sticky) Spiral FAP (Silk chemistry switch & destructive recycling)
5. Stabilimentum Construction FAP
"""

# ── Top-level FAP Task ──────────────────────────────────────────────────────

def build_fap_web(state):
    """
    Top-level task decomposing web construction into the 5 Macro-Stages
    specified in the FAP model PDF.
    """
    if state.web_complete:
        return []
    return [
        ("fap_proto_web_y_frame",),
        ("fap_radial_spokes",),
        ("fap_auxiliary_spiral",),
        ("fap_capture_spiral",),
        ("fap_stabilimentum",),
        ("finalise_fap_web",),
    ]


# ── FAP Stage 1: Proto-Web & Y-Frame FAP ─────────────────────────────────────

def fap_proto_web_y_frame_method(state):
    """
    Construct Proto-Web & Y-Frame according to the 4 explicit PDF steps:
    - Lay bridge thread across top gap.
    - Step 1: Walk to midpoint of bridge thread.
    - Step 2: Attach slack line at midpoint.
    - Step 3: Drop straight down to lower anchor point.
    - Step 4: Tighten Y-frame (pulls line downward turning horizontal bridge
              into V-shape, vertical line forms stem -> Y-shape).
    """
    if state.y_frame_established:
        return []

    return [
        # Lay initial horizontal bridge thread across top gap
        ("lay_bridge_thread", "anchor_top_left", "anchor_top_right"),
        # Step 1: Walk halfway across bridge thread
        ("walk_to_midpoint", "anchor_top_right", "bridge_midpoint"),
        # Step 2: Attach slack line at exact midpoint
        ("attach_slack_line", "bridge_midpoint"),
        # Step 3: Drop straight down toward lower anchor point
        ("drop_down_to_anchor", "bridge_midpoint", "anchor_bottom_stem"),
        # Step 4: Tighten Y-frame (forms V-arms + stem -> Y-shape at hub_center)
        ("tighten_y_frame", "anchor_bottom_stem", "hub_center"),
    ]


# ── FAP Stage 2: Radial Spoke Construction FAP ──────────────────────────────

def fap_radial_spokes_method(state):
    """
    Construct Radial Spokes using repetitive 4-step loop from PDF:
    - Step 1: Up and Out (climb up Y-frame line to outer edge).
    - Step 2: Lay Loose Line (step along outer frame, crawl back spinning loose line).
    - Step 3: Pull Tight (reach hub, pull thread tight & anchor).
    - Step 4: Angle Measurement (leg calipers measure gap, swap sides dynamically).
    """
    if state.spokes_count >= 8:
        return []

    hub = "hub_center"

    # Frame targets distributed around the 8 octants for uniform wheel
    spoke_targets = [
        ("anchor_top_left",     "frame_top_center"),
        ("anchor_top_right",    "frame_top_right"),
        ("frame_right_mid",     "frame_right_mid"),
        ("anchor_bottom_stem",  "frame_bottom_right"),
        ("anchor_bottom_stem",  "frame_bottom_center"),
        ("anchor_bottom_stem",  "frame_bottom_left"),
        ("frame_left_mid",      "frame_left_mid"),
        ("anchor_top_left",     "frame_top_left"),
    ]

    subtasks = []
    start_idx = state.spokes_count
    for climb_edge, frame_target in spoke_targets[start_idx:]:
        subtasks.extend([
            # Step 1: Up and Out
            ("climb_up_and_out", hub, climb_edge),
            # Step 2: Laying Loose Line
            ("lay_loose_spoke", climb_edge, frame_target, hub),
            # Step 3: Pulling Tight at hub
            ("pull_spoke_tight", hub, frame_target),
            # Step 4: Angle Measurement & Tension Check
            ("measure_angle_gap_check", hub, climb_edge, frame_target),
        ])

    return subtasks if subtasks else []


# ── FAP Stage 3: Auxiliary (Scaffolding) Spiral FAP ─────────────────────────

def fap_auxiliary_spiral_method(state):
    """
    Build temporary non-sticky scaffolding spiral working outward from hub.
    """
    if state.auxiliary_spiral_done:
        return []

    hub = "hub_center"
    spiral_nodes = [
        "frame_top_center", "frame_top_right",
        "frame_right_mid", "frame_bottom_right",
        "frame_bottom_center", "frame_bottom_left",
        "frame_left_mid", "frame_top_left",
    ]

    subtasks = [("walk", hub, hub)]
    prev = hub
    for node in spiral_nodes:
        subtasks.append(("build_auxiliary_spiral_segment", prev, node))
        prev = node

    subtasks.append(("walk", prev, hub))
    subtasks.append(("mark_auxiliary_spiral_done",))
    return subtasks


# ── FAP Stage 4: Capture (Sticky) Spiral FAP ────────────────────────────────

def fap_capture_spiral_method(state):
    """
    Build sticky capture spiral following 4 explicit PDF steps:
    - Step 1: Switch Silk Chemistry (dry structural -> sticky capture droplets).
    - Step 2: Outside-In Trajectory (narrowing concentric circles).
    - Step 3: Leg-Guided Placement (outer leg feels scaffolding, inner leg measures, dab).
    - Step 4: Destructive Recycling (bite, roll up, and eat old scaffolding line).
    """
    if state.capture_spiral_done:
        return []

    hub = "hub_center"
    spiral_nodes = [
        "frame_top_left", "frame_left_mid",
        "frame_bottom_left", "frame_bottom_center",
        "frame_bottom_right", "frame_right_mid",
        "frame_top_right", "frame_top_center",
    ]

    subtasks = [
        # Step 1: Switch silk chemistry to sticky capture silk
        ("switch_silk_chemistry", "sticky_capture"),
    ]

    prev = hub
    for node in spiral_nodes:
        # Step 4: Destructive Recycling (bite and eat scaffolding line as it crosses)
        subtasks.append(("bite_and_recycle_scaffolding", prev, node))
        # Step 2 & 3: Outside-In Leg-Guided Placement & Dabbing
        subtasks.append(("leg_guided_capture_dab", prev, node))
        prev = node

    subtasks.append(("walk", prev, hub))
    subtasks.append(("mark_capture_spiral_done",))
    return subtasks


# ── FAP Stage 5: Stabilimentum Construction FAP ─────────────────────────────

def fap_stabilimentum_method(state):
    """
    Construct Stabilimentum (Stage 5):
    Lay decorative zig-zag silk structure in central hub area.
    """
    if state.stabilimentum_done:
        return []

    hub = "hub_center"
    return [
        ("construct_stabilimentum_segment", hub, "stabilimentum_top"),
        ("construct_stabilimentum_segment", "stabilimentum_top", "stabilimentum_bottom"),
        ("construct_stabilimentum_segment", "stabilimentum_bottom", hub),
        ("mark_stabilimentum_done",),
    ]


# ── Finalisation ───────────────────────────────────────────────────────────

def finalise_fap_web(state):
    """Mark FAP web complete."""
    if state.web_complete:
        return []
    return [("mark_fap_complete",)]


def mark_auxiliary_spiral_done(state):
    state.auxiliary_spiral_done = True
    return state


def mark_capture_spiral_done(state):
    state.capture_spiral_done = True
    return state


def mark_stabilimentum_done(state):
    state.stabilimentum_done = True
    return state
