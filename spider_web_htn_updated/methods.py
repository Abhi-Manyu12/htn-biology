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

All anchor orderings, construction thresholds (e.g. how many radii/frames
make a "complete" web), and node cycles used by the alternative proto-hub
methods are sourced from config.yaml (domain section) rather than hardcoded
here, so a different environment/domain parameterisation can be tried by
editing the config alone.

Convention
----------
- Each method takes ``state`` as its first argument (plus task-specific params).
- On success it returns a list of subtasks (tuples).
- On failure / inapplicability it returns ``False``.
"""

from .config_loader import CONFIG

_DOMAIN = CONFIG["domain"]

_MIN_PROTO_RADII = _DOMAIN["min_proto_radii"]
_TARGET_RADII_COUNT = _DOMAIN["target_radii_count"]
_TARGET_FRAME_COUNT = _DOMAIN["target_frame_count"]
_FRAME_PAIRS = _DOMAIN["frame_pairs"]
_RADII_ANCHOR_ORDER = _DOMAIN["radii_anchor_order"]
_PROTO_HUB_ANCHORS = _DOMAIN["proto_hub_anchors"]
_SPIRAL_NODES = _DOMAIN["spiral_nodes"]
_DEFAULT_HUB_NAME = _DOMAIN["default_hub_name"]


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
    """Base case: proto-hub already exists with >= min_proto_radii proto-radii."""
    if state.proto_hub_exists:
        return []
    return False


def establish_proto_hub_via_walk(state):
    """
    Build one proto-radius by walking along existing threads to the
    supporting structure, then return to hub.

    Zschokke (1996, Fig. 2D): "it either walks along existing threads."
    This is variant 1 of 3 ways to reach the supporting structure.

    Anchor cycle order comes from config (domain.proto_hub_anchors.via_walk).
    """
    if state.proto_hub_exists:
        return []

    hub = _DEFAULT_HUB_NAME
    anchors = _PROTO_HUB_ANCHORS["via_walk"]
    idx = state.proto_radii_count % len(anchors)
    target_anchor = anchors[idx]

    subtasks = []

    if state.proto_radii_count == 0:
        subtasks.append(("anchor", hub))

    subtasks.extend([
        ("lay_thread", hub, target_anchor, "dragline"),
        ("reel_up", target_anchor, hub),
        ("insert_radius", target_anchor, hub),
    ])

    # After building enough proto-radii, mark the hub
    if state.proto_radii_count >= _MIN_PROTO_RADII - 1:  # will reach threshold after insert_radius
        subtasks.append(("mark_proto_hub", hub))
    else:
        subtasks.append(("establish_proto_hub",))

    return subtasks


def establish_proto_hub_via_drop(state):
    """
    Build one proto-radius by dropping down vertically on dragline.

    Zschokke (1996, Fig. 2E): "or it drops down vertically using the dragline."
    Variant 2 of 3.

    Anchor cycle order comes from config (domain.proto_hub_anchors.via_drop).
    """
    if state.proto_hub_exists:
        return []

    hub = _DEFAULT_HUB_NAME
    anchors = _PROTO_HUB_ANCHORS["via_drop"]
    idx = state.proto_radii_count % len(anchors)
    target_anchor = anchors[idx]

    subtasks = [
        ("anchor", hub),
        ("drop_down", hub, target_anchor),
        ("reel_up", target_anchor, hub),
        ("insert_radius", target_anchor, hub),
    ]

    if state.proto_radii_count >= _MIN_PROTO_RADII - 1:
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

    Anchor cycle order comes from config (domain.proto_hub_anchors.via_tarzan).
    """
    if state.proto_hub_exists:
        return []

    hub = _DEFAULT_HUB_NAME
    anchors = _PROTO_HUB_ANCHORS["via_tarzan"]
    idx = state.proto_radii_count % len(anchors)
    target_anchor = anchors[idx]

    subtasks = [
        ("anchor", hub),
        ("swing_tarzan", hub, target_anchor),
        ("reel_up", target_anchor, hub),
        ("insert_radius", target_anchor, hub),
    ]

    if state.proto_radii_count >= _MIN_PROTO_RADII - 1:
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

    Frame pair ordering and the target frame count come from config
    (domain.frame_pairs, domain.target_frame_count).
    """
    if state.frame_count >= _TARGET_FRAME_COUNT:
        return []  # all frames done

    hub = state.proto_hub_pos or _DEFAULT_HUB_NAME

    subtasks = []
    start_idx = state.frame_count
    for n1, n2 in _FRAME_PAIRS[start_idx:]:
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

    Anchor ordering and target radii count come from config
    (domain.radii_anchor_order, domain.target_radii_count).
    """
    if state.radii_count >= _TARGET_RADII_COUNT:
        return []  # enough radii

    hub = state.proto_hub_pos or _DEFAULT_HUB_NAME

    subtasks = []
    start_idx = state.radii_count
    for anchor_node in _RADII_ANCHOR_ORDER[start_idx:]:
        subtasks.extend([
            ("lay_radius", hub, anchor_node),
            ("walk", anchor_node, hub), # return to hub
        ])

    return subtasks if subtasks else []


# ---------------------------------------------------------------------------
# ④c Auxiliary spiral
# ---------------------------------------------------------------------------

def build_auxiliary_spiral_method(state):
    """
    Build the auxiliary (temporary) spiral working outward from the hub.

    Zschokke (Fig. 2J): "Circling of the hub changes suddenly without
    interruption into the construction of the auxiliary spiral."

    Node traversal order comes from config (domain.spiral_nodes.auxiliary).
    """
    if state.auxiliary_spiral_done:
        return []

    hub = state.proto_hub_pos or _DEFAULT_HUB_NAME
    spiral_nodes = _SPIRAL_NODES["auxiliary"]

    subtasks = []  # start circling from hub
    prev = hub
    for node in spiral_nodes:
        subtasks.append(
            ("build_spiral_segment", prev, node, "auxiliary_spiral")
        )
        prev = node

    subtasks.append(("walk", prev, hub))
    subtasks.append(("mark_auxiliary_spiral_done",))
    return subtasks


# ---------------------------------------------------------------------------
# ④d Capture spiral
# ---------------------------------------------------------------------------

def build_capture_spiral_method(state):
    """
    Build the capture (sticky) spiral working inward toward the hub.

    Zschokke (Fig. 2K): "The spider finally completes the web by building the
    capture spiral."

    Node traversal order comes from config (domain.spiral_nodes.capture).
    """
    if state.capture_spiral_done:
        return []

    hub = state.proto_hub_pos or _DEFAULT_HUB_NAME
    spiral_nodes = _SPIRAL_NODES["capture"]

    subtasks = []
    prev = hub
    for node in spiral_nodes:
        subtasks.append(
            ("build_spiral_segment", prev, node, "capture_spiral")
        )
        prev = node

    subtasks.append(("walk", prev, hub))
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
