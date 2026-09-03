"""
methods.py — HTN methods for the Zschokke 1996 orb web construction model.

The methods are organised into two groups mirroring Zschokke's key finding:

1. **Early stages (variable / opportunistic):**
   Exploration, bridging, proto-hub establishment.  Multiple alternative
   methods are registered so GTPyhop's backtracking can model the "no single
   pattern" variability that Zschokke observed.

2. **Later stages (stereotyped / procedural):**
   Frame, radii, auxiliary spiral, capture spiral.  These use a rigid,
   sequential decomposition matching the fixed neural programme Zschokke
   described.

Convention
----------
- Each method takes ``state`` as its first argument (plus task-specific params).
- On success it returns a list of subtasks (tuples).
- On failure / inapplicability it returns ``False``.
"""

from .utils import get_radius_node


# ---------------------------------------------------------------------------
# ① TOP-LEVEL TASK: build_web
# ---------------------------------------------------------------------------

def build_web(state):
    """
    Top-level decomposition of the entire web construction process.

    Zschokke's sequence:
        explore & bridge → proto-hub → remaining web (frame, radii, spirals)
    """
    if state.web_complete:
        return []                       # nothing to do
    return [
        ("explore_and_bridge",),
        ("establish_proto_hub",),
        ("build_remaining_web",),
        ("finalise_web",),
    ]


# ---------------------------------------------------------------------------
# ② EARLY STAGE: explore_and_bridge
# ---------------------------------------------------------------------------

def explore_bridge_walk_detour(state):
    """
    Bridge the gap between sticks by walking the detour along the bottom.

    Zschokke (1996): "the spider bridges the open space between the two sticks.
    In the laboratory this is done by attaching the dragline at the top of one
    stick and then walking the detour along the bottom of the supporting
    structure."
    """
    if state.bridge_established:
        return []                       # already bridged

    return [
        # Attach dragline at right stick top
        ("attach_dragline", "right_stick_top"),
        # Walk down the right stick
        ("walk", "right_stick_top", "right_stick_bottom"),
        # Walk across the bottom path
        ("walk", "right_stick_bottom", "bottom_path"),
        ("walk", "bottom_path", "left_stick_bottom"),
        # Climb up the left stick partway
        ("walk", "left_stick_bottom", "left_stick_mid"),
        # Tighten & attach dragline → first thread across the gap
        ("lay_thread", "left_stick_mid", "right_stick_top", "bridge"),
        # Establish highest horizontal thread
        ("establish_high_thread",),
    ]


# ---------------------------------------------------------------------------
# ② EARLY STAGE: establish_high_thread
# ---------------------------------------------------------------------------

def establish_high_thread_direct(state):
    """
    Establish a thread as high up as possible between the stick tops.

    Zschokke: "The spider then usually tries to establish a thread as high up
    as possible; this may be achieved by replacing the original thread or by
    adding another one."

    After bridging, spider is at right_stick_top.  Walk via bridge thread
    to left_stick_mid, then up to left_stick_top.
    """
    if state.high_thread_established:
        return []

    return [
        # Cross via bridge thread to left stick midpoint
        ("walk", "right_stick_top", "left_stick_mid"),
        # Climb up to left stick top
        ("walk", "left_stick_mid", "left_stick_top"),
        # Lay the highest thread back to right stick top
        ("lay_thread", "left_stick_top", "right_stick_top", "bridge"),
        ("mark_high_thread_done",),
    ]


def establish_high_thread_via_climb(state):
    """
    Alternative: cross via bridge, climb left stick to top, then thread back.
    """
    if state.high_thread_established:
        return []

    return [
        ("walk", "right_stick_top", "left_stick_mid"),
        ("walk", "left_stick_mid", "left_stick_top"),
        ("lay_thread", "left_stick_top", "right_stick_top", "bridge"),
        ("mark_high_thread_done",),
    ]


# ---------------------------------------------------------------------------
# ③ EARLY STAGE: establish_proto_hub (VARIABLE — Zschokke's key finding)
# ---------------------------------------------------------------------------

def establish_proto_hub_done(state):
    """Base case: proto-hub already exists with ≥ 4 proto-radii."""
    if state.proto_hub_exists:
        return []
    return False


def establish_proto_hub_via_walk(state):
    """
    Build one proto-radius by walking along existing threads to the
    supporting structure, then return to hub.

    Zschokke (1996, Fig. 2D): "it either walks along existing threads."
    This is variant 1 of 3 ways to reach the supporting structure.
    """
    if state.proto_hub_exists:
        return []

    hub = "proto_hub"
    # Choose an anchor based on how many proto-radii we have
    anchors = [
        "anchor_left_upper", "anchor_right_upper",
        "anchor_left_lower", "anchor_right_lower",
        "left_stick_top", "right_stick_top",
        "crossbar_left", "crossbar_right",
    ]
    idx = state.proto_radii_count % len(anchors)
    target_anchor = anchors[idx]

    subtasks = [
        ("anchor", hub),
        ("lay_thread", hub, target_anchor, "dragline"),
        ("reel_up", target_anchor, hub),
        ("insert_radius", target_anchor, hub),
    ]

    # After building enough proto-radii, mark the hub
    if state.proto_radii_count >= 3:  # will be 4 after insert_radius
        subtasks.append(("mark_proto_hub", hub))
    else:
        subtasks.append(("establish_proto_hub",))

    return subtasks


def establish_proto_hub_via_drop(state):
    """
    Build one proto-radius by dropping down vertically on dragline.

    Zschokke (1996, Fig. 2E): "or it drops down vertically using the dragline."
    Variant 2 of 3.
    """
    if state.proto_hub_exists:
        return []

    hub = "proto_hub"
    # Use a different anchor selection for variety via backtracking
    anchors = [
        "anchor_right_lower", "anchor_left_lower",
        "crossbar_right", "crossbar_left",
        "anchor_bottom_center", "anchor_bottom_left",
    ]
    idx = state.proto_radii_count % len(anchors)
    target_anchor = anchors[idx]

    subtasks = [
        ("anchor", hub),
        ("drop_down", hub, target_anchor),
        ("reel_up", target_anchor, hub),
        ("insert_radius", target_anchor, hub),
    ]

    if state.proto_radii_count >= 3:
        subtasks.append(("mark_proto_hub", hub))
    else:
        subtasks.append(("establish_proto_hub",))

    return subtasks


def establish_proto_hub_via_tarzan(state):
    """
    Build one proto-radius using the "Tarzan method".

    Zschokke (1996): "the spider — after having attached the thread — walks a
    few centimetres and then drops down, swinging around the place where the
    dragline is attached. When the spider — in full swing — hits another thread
    or a part of the supporting structure it grabs it."
    Variant 3 of 3.
    """
    if state.proto_hub_exists:
        return []

    hub = "proto_hub"
    anchors = [
        "anchor_left_upper", "anchor_right_lower",
        "left_stick_mid", "right_stick_mid",
        "anchor_bottom_right", "anchor_top_center",
    ]
    idx = state.proto_radii_count % len(anchors)
    target_anchor = anchors[idx]

    subtasks = [
        ("anchor", hub),
        ("swing_tarzan", hub, target_anchor),
        ("reel_up", target_anchor, hub),
        ("insert_radius", target_anchor, hub),
    ]

    if state.proto_radii_count >= 3:
        subtasks.append(("mark_proto_hub", hub))
    else:
        subtasks.append(("establish_proto_hub",))

    return subtasks


# ---------------------------------------------------------------------------
# ④ LATER STAGE: build_remaining_web (STEREOTYPED)
# ---------------------------------------------------------------------------

def build_remaining_web(state):
    """
    Stereotyped later stages — rigid, predictable decomposition.

    Zschokke: "With the establishment of the proto-hub ... the spider then
    laid the foundation for the construction of the rest of the web. This
    foundation showed less variation and enabled the spider to use a more rigid
    pattern for the subsequent construction of radii, frame and the spirals."
    """
    if not state.proto_hub_exists:
        return False

    return [
        ("build_frame",),
        ("build_radii",),
        ("build_auxiliary_spiral",),
        ("build_capture_spiral",),
    ]


# ---------------------------------------------------------------------------
# ④a Frame construction
# ---------------------------------------------------------------------------

def build_frame_method(state):
    """
    Construct frame threads.

    Zschokke: "The first frame thread is always the one at the top of the
    future web, the top frame thread."  Frame construction follows "quite a
    rigid pattern".
    """
    if state.frame_count >= 4:
        return []  # all frames done

    hub = state.proto_hub_pos or "proto_hub"

    # Top frame first, then left, bottom, right
    frame_pairs = [
        ("left_stick_top", "right_stick_top"),        # top frame
        ("left_stick_top", "anchor_left_lower"),       # left frame
        ("anchor_left_lower", "anchor_right_lower"),   # bottom frame
        ("anchor_right_lower", "right_stick_top"),     # right frame
    ]

    subtasks = []
    start_idx = state.frame_count
    for n1, n2 in frame_pairs[start_idx:]:
        subtasks.extend([
            ("walk", hub, n1),
            ("lay_frame_thread", n1, n2),
            ("walk", n2, hub),
        ])

    return subtasks if subtasks else []


# ---------------------------------------------------------------------------
# ④b Radius construction
# ---------------------------------------------------------------------------

def build_radii_method(state):
    """
    Construct definitive radii by circling the hub and filling gaps.

    Zschokke: "When the spider builds the radii it keeps circling the hub to
    find a gap to place the next radius."
    """
    if state.radii_count >= 8:
        return []  # enough radii

    hub = state.proto_hub_pos or "proto_hub"

    # Radii targets — distributed around the frame
    radii_anchors = [
        "anchor_top_center",
        "anchor_left_upper",
        "anchor_left_lower",
        "anchor_bottom_left",
        "anchor_bottom_center",
        "anchor_bottom_right",
        "anchor_right_lower",
        "anchor_right_upper",
    ]

    subtasks = []
    start_idx = state.radii_count
    for anchor_node in radii_anchors[start_idx:]:
        subtasks.extend([
            ("walk", hub, hub),         # circle hub to find gap
            ("lay_radius", hub, anchor_node),
            ("walk", anchor_node, hub), # return to hub
        ])

    return subtasks if subtasks else []


# ---------------------------------------------------------------------------
# ④c Auxiliary spiral
# ---------------------------------------------------------------------------

def build_auxiliary_spiral_method(state):
    """
    Build the auxiliary (temporary) spiral working outward from the hub in a continuous Archimedean spiral.

    Zschokke (Fig. 2J): "Circling of the hub changes suddenly without
    interruption into the construction of the auxiliary spiral."
    """
    if state.auxiliary_spiral_done:
        return []

    hub = state.proto_hub_pos or "proto_hub"

    radii_anchors = [
        "anchor_top_center",
        "anchor_right_upper",
        "anchor_right_lower",
        "anchor_bottom_right",
        "anchor_bottom_center",
        "anchor_bottom_left",
        "anchor_left_lower",
        "anchor_left_upper",
    ]

    turns = 4
    total_steps = turns * len(radii_anchors)
    t_start, t_end = 0.20, 0.80

    subtasks = []
    prev_node = hub

    for step_i in range(total_steps):
        frac = t_start + step_i * (t_end - t_start) / (total_steps - 1)
        anchor = radii_anchors[step_i % len(radii_anchors)]
        curr_node = get_radius_node(anchor, frac)
        subtasks.append(("build_spiral_segment", prev_node, curr_node, "auxiliary_spiral"))
        prev_node = curr_node

    subtasks.append(("walk", prev_node, hub))
    subtasks.append(("mark_auxiliary_spiral_done",))
    return subtasks


# ---------------------------------------------------------------------------
# ④d Capture spiral
# ---------------------------------------------------------------------------

def build_capture_spiral_method(state):
    """
    Build the capture (sticky) spiral working inward toward the hub in a continuous Archimedean spiral.

    Zschokke (Fig. 2K): "The spider finally completes the web by building the
    capture spiral."
    """
    if state.capture_spiral_done:
        return []

    hub = state.proto_hub_pos or "proto_hub"

    radii_anchors = [
        "anchor_top_center",
        "anchor_right_upper",
        "anchor_right_lower",
        "anchor_bottom_right",
        "anchor_bottom_center",
        "anchor_bottom_left",
        "anchor_left_lower",
        "anchor_left_upper",
    ]

    turns = 5
    total_steps = turns * len(radii_anchors)
    t_start, t_end = 0.85, 0.20

    subtasks = []
    prev_node = hub

    for step_i in range(total_steps):
        frac = t_start - step_i * (t_start - t_end) / (total_steps - 1)
        anchor = radii_anchors[step_i % len(radii_anchors)]
        curr_node = get_radius_node(anchor, frac)
        subtasks.append(("build_spiral_segment", prev_node, curr_node, "capture_spiral"))
        prev_node = curr_node

    subtasks.append(("walk", prev_node, hub))
    subtasks.append(("mark_capture_spiral_done",))
    return subtasks


# ---------------------------------------------------------------------------
# ⑤ Finalisation
# ---------------------------------------------------------------------------

def finalise_web(state):
    """Mark the web as complete — spider waits at centre for prey."""
    if state.web_complete:
        return []
    return [("mark_web_complete",)]


# ---------------------------------------------------------------------------
# ⑥ Marker pseudo-operators (update flags without real physical action)
# ---------------------------------------------------------------------------

def mark_high_thread_done(state):
    """Operator: flag that the highest thread has been established."""
    state.high_thread_established = True
    state.bridge_established = True
    return state


def mark_auxiliary_spiral_done(state):
    """Operator: flag that the auxiliary spiral is complete."""
    state.auxiliary_spiral_done = True
    return state


def mark_capture_spiral_done(state):
    """Operator: flag that the capture spiral is complete."""
    state.capture_spiral_done = True
    return state