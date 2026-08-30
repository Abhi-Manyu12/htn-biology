"""
operators.py — A* wrapper around the HTN primitive operators.

A* does not have GTPyhop's automatic backtracking on operator failure. We
instead pre-check preconditions before generating a successor. Each generator
yields (action_tuple, successor_state, cost) — the cost is the energy
expenditure of that action (in cm walked, matching the HTN's metric).
"""
from spider_web_htn import operators as htn_ops
from spider_web_htn.utils import (
    NODE_COORDS,
    calculate_distance,
    thread_exists,
    count_threads_of_type,
)
from spider_web_htn.state import rigid

from .state import copy_state, GOAL_THRESHOLDS


# All anchor candidates that can be used as endpoints for radii/frame/spirals.
# These are the same anchor nodes the HTN uses.
_RADIUS_ANCHORS = [
    "anchor_left_upper", "anchor_left_lower",
    "anchor_right_upper", "anchor_right_lower",
    "anchor_top_center",
    "anchor_bottom_left", "anchor_bottom_center", "anchor_bottom_right",
]


def _can_reach(state, target):
    """Same reachability check as HTN operator helper."""
    if target not in state.nodes:
        return False
    if state.spider_pos == target:
        return True
    visited = {state.spider_pos}
    queue = [state.spider_pos]
    while queue:
        current = queue.pop(0)
        for a, b in rigid.walkable_edges:
            nbr = a if b == current else (b if a == current else None)
            if nbr and nbr not in visited and nbr in state.nodes:
                if nbr == target:
                    return True
                visited.add(nbr)
                queue.append(nbr)
        for n1, n2, _ in state.threads:
            nbr = n1 if n2 == current else (n2 if n1 == current else None)
            if nbr and nbr not in visited and nbr in state.nodes:
                if nbr == target:
                    return True
                visited.add(nbr)
                queue.append(nbr)
    return False


def _successor(state, action_name, args):
    """Apply an operator on a fresh copy; return (cost, new_state) or None."""
    new_state = copy_state(state)
    # Each operator takes the state as first arg.
    fn = getattr(htn_ops, action_name, None)
    if fn is None:
        return None
    try:
        result = fn(new_state, *args)
    except Exception:
        return None
    if result is False:
        return None
    cost = new_state.energy_expended - state.energy_expended
    return cost, new_state


# ── successor generators ────────────────────────────────────────────────────
# Each yields (action_tuple, cost, new_state). We pre-filter via preconditions
# to keep A*'s branching factor sane.

def gen_walk(state):
    """Walk along structural edges or along existing threads from current pos.

    Restricts to adjacent nodes (1 hop). This matches physical reality:
    walking requires an actual path, and laying a long dragline is a
    separate action (`lay_thread`), not walking.
    """
    pos = state.spider_pos
    seen = set()
    # Structural walkable edges (1 hop)
    for a, b in rigid.walkable_edges:
        for src, dst in ((a, b), (b, a)):
            if src == pos and dst != pos and dst in state.nodes and dst not in seen:
                seen.add(dst)
                res = _successor(state, "walk", [src, dst])
                if res is not None:
                    cost, ns = res
                    yield (("walk", src, dst), cost, ns)
    # Walk along existing threads (1 hop)
    for n1, n2, _ in state.threads:
        for src, dst in ((n1, n2), (n2, n1)):
            if src == pos and dst != pos and dst in state.nodes and dst not in seen:
                seen.add(dst)
                res = _successor(state, "walk", [src, dst])
                if res is not None:
                    cost, ns = res
                    yield (("walk", src, dst), cost, ns)


def gen_lay_thread(state):
    """Lay a dragline thread between current pos and a reachable node.

    The bridge-thread type is omitted because it produces the same edge as
    dragline from A*'s perspective — only the thread-type label differs.
    """
    pos = state.spider_pos
    candidates = [n for n in state.nodes if n != pos and not thread_exists(state.threads, pos, n)]
    for target in candidates:
        # Lay thread to nearby nodes (within 20 cm).
        dist = calculate_distance(pos, target)
        if dist > 20.0:
            continue
        res = _successor(state, "lay_thread", [pos, target, "dragline"])
        if res is not None:
            cost, ns = res
            yield (("lay_thread", pos, target, "dragline"), cost, ns)


def gen_drop_down(state):
    """Drop vertically to any directly-below node (creates dragline).

    Restricts to nodes vertically below pos (1-step drops). The HTN's
    drop is always a single hop in Zschokke's lab setup.
    """
    pos = state.spider_pos
    c1 = NODE_COORDS.get(pos)
    if c1 is None:
        return
    for target in state.nodes:
        if target == pos:
            continue
        c2 = NODE_COORDS.get(target)
        if c2 is None:
            continue
        if c2[1] >= c1[1]:
            continue
        # Restrict to physically plausible drops: target within ~15 cm below.
        dy = c1[1] - c2[1]
        if dy > 15.0:
            continue
        res = _successor(state, "drop_down", [pos, target])
        if res is not None:
            cost, ns = res
            yield (("drop_down", pos, target), cost, ns)


def gen_swing_tarzan(state):
    """Tarzan swing to any nearby node (creates dragline).

    Restricts to nodes within ~10 cm of pos. Zschokke observed Tarzan
    swings as short hops.
    """
    pos = state.spider_pos
    for target in state.nodes:
        if target == pos:
            continue
        dist = calculate_distance(pos, target)
        if dist > 10.0:
            continue
        res = _successor(state, "swing_tarzan", [pos, target])
        if res is not None:
            cost, ns = res
            yield (("swing_tarzan", pos, target), cost, ns)


def gen_anchor(state):
    """Anchor at any unused nearby name."""
    used = state.nodes
    for i in range(20):
        candidate = f"anchor_new_{i}"
        if candidate in used:
            continue
        new_state = copy_state(state)
        htn_ops.anchor(new_state, candidate)
        # anchor doesn't move spider — no energy cost.
        yield (("anchor", candidate), 0.0, new_state)
        return  # one is enough; spider doesn't gain from anchoring twice in a row


def gen_attach_dragline(state):
    """Tighten dragline at current pos."""
    new_state = copy_state(state)
    res = _successor(state, "attach_dragline", [state.spider_pos])
    if res is not None:
        cost, ns = res
        yield (("attach_dragline", state.spider_pos), cost, ns)


def gen_remove_thread(state):
    """Remove a thread the spider is currently adjacent to."""
    pos = state.spider_pos
    for n1, n2, _ in state.threads:
        if n1 == pos or n2 == pos:
            other = n2 if n1 == pos else n1
            res = _successor(state, "remove_thread", [pos, other])
            if res is not None:
                cost, ns = res
                yield (("remove_thread", pos, other), cost, ns)


def gen_reel_up(state):
    """Reel up a thread ending at current pos."""
    pos = state.spider_pos
    for n1, n2, _ in state.threads:
        if n1 != pos and n2 != pos:
            continue
        other = n2 if n1 == pos else n1
        res = _successor(state, "reel_up", [pos, other])
        if res is not None:
            cost, ns = res
            yield (("reel_up", pos, other), cost, ns)


def gen_insert_radius(state):
    """Insert a radius only when the current dragline supports that operation.

    This generator is retained because it may be the primitive that converts
    a dragline into a proto/definitive radius in the shared HTN domain.
    The previous `pass` did not enforce anything and was misleading.
    """
    pos = state.spider_pos
    for n1, n2, ttype in state.threads:
        if ttype != "dragline":
            continue
        if n1 != pos and n2 != pos:
            continue
        other = n2 if n1 == pos else n1
        # The other endpoint should be a known anchor.
        if other not in _RADIUS_ANCHORS and not other.startswith("anchor_"):
            continue
        # Insert radius from pos (hub) to other (anchor).
        res = _successor(state, "insert_radius", [other, pos])
        if res is not None:
            cost, ns = res
            yield (("insert_radius", other, pos), cost, ns)


def gen_mark_proto_hub(state):
    """Mark proto-hub if ≥4 proto-radii converge here."""
    if state.proto_hub_exists:
        return
    pos = state.spider_pos
    if state.proto_radii_count < GOAL_THRESHOLDS["min_proto_radii"]:
        return
    res = _successor(state, "mark_proto_hub", [pos])
    if res is not None:
        cost, ns = res
        yield (("mark_proto_hub", pos), cost, ns)


def gen_lay_frame_thread(state):
    """Lay a frame thread to any known anchor. Marks top_frame_done when
    the topmost frame thread is laid."""
    pos = state.spider_pos
    if not state.proto_hub_exists:
        # Frame needs hub to exist (matches HTN's method ordering).
        return
    for target in _RADIUS_ANCHORS + ["left_stick_top", "right_stick_top"]:
        if target == pos:
            continue
        if target not in state.nodes:
            continue
        res = _successor(state, "lay_frame_thread", [pos, target])
        if res is not None:
            cost, ns = res
            # If this is the top frame thread, mark it.
            if target == "anchor_top_center" and not ns.top_frame_done:
                ns.top_frame_done = True
            yield (("lay_frame_thread", pos, target), cost, ns)


def gen_lay_radius(state):
    """Lay a definitive radius from hub to any anchor."""
    pos = state.spider_pos
    if not state.proto_hub_exists:
        return
    if pos != state.proto_hub_pos and state.proto_hub_pos is not None:
        # Must be at the hub.
        return
    for target in _RADIUS_ANCHORS:
        if target == pos or target not in state.nodes:
            continue
        res = _successor(state, "lay_radius", [pos, target])
        if res is not None:
            cost, ns = res
            yield (("lay_radius", pos, target), cost, ns)


def gen_build_spiral_segment(state):
    """Lay a spiral segment between two connected nodes."""
    pos = state.spider_pos
    if not state.top_frame_done:
        # Spirals come after frame in the HTN's order.
        return
    # Candidates must be real nodes, not the current position, and must be
    # reachable through the current physical/thread network.  This fixes the
    # mismatch between the old comment and implementation (which did not
    # actually test reachability).
    candidates = [
        n for n in state.nodes
        if n != pos and _can_reach(state, n)
        and not thread_exists(state.threads, pos, n)
    ]
    aux_count = count_threads_of_type(state.threads, "auxiliary_spiral")
    cap_count = count_threads_of_type(state.threads, "capture_spiral")
    for target in candidates:
        # Aux spiral before capture spiral (matches HTN ordering).
        if aux_count < 4:
            ttype = "auxiliary_spiral"
        elif not state.capture_spiral_done:
            ttype = "capture_spiral"
        else:
            return
        res = _successor(state, "build_spiral_segment", [pos, target, ttype])
        if res is not None:
            cost, ns = res
            # Auto-mark aux/capture spiral done once we have enough segments.
            new_aux = count_threads_of_type(ns.threads, "auxiliary_spiral")
            new_cap = count_threads_of_type(ns.threads, "capture_spiral")
            if new_aux >= 4 and not ns.auxiliary_spiral_done:
                ns.auxiliary_spiral_done = True
            if new_cap >= GOAL_THRESHOLDS["min_capture_spiral"] and not ns.capture_spiral_done:
                ns.capture_spiral_done = True
            yield (("build_spiral_segment", pos, target, ttype), cost, ns)


def gen_mark_web_complete(state):
    """Mark web complete if all thresholds met."""
    if (state.frame_count >= GOAL_THRESHOLDS["min_frame"]
            and state.radii_count >= GOAL_THRESHOLDS["min_radii"]
            and state.capture_spiral_done):
        new_state = copy_state(state)
        htn_ops.mark_web_complete(new_state)
        yield (("mark_web_complete",), 0.0, new_state)


# ── successor iterator ─────────────────────────────────────────────────────

def get_successors(state):
    """Yield all valid (action, cost, new_state) from `state`."""
    # Skip "complete" if already done.
    if state.web_complete:
        return
    yield from gen_walk(state)
    yield from gen_lay_thread(state)
    yield from gen_drop_down(state)
    yield from gen_swing_tarzan(state)
    # Fixed-geometry experiment: do not create artificial anchors.
    yield from gen_attach_dragline(state)
    yield from gen_remove_thread(state)
    yield from gen_reel_up(state)
    yield from gen_insert_radius(state)
    yield from gen_mark_proto_hub(state)
    yield from gen_lay_frame_thread(state)
    yield from gen_lay_radius(state)
    yield from gen_build_spiral_segment(state)
    yield from gen_mark_web_complete(state)


def is_goal(state):
    """Check whether state satisfies the web-completion goal."""
    return (
        state.web_complete
        and state.proto_hub_exists
        and state.frame_count >= GOAL_THRESHOLDS["min_frame"]
        and state.radii_count >= GOAL_THRESHOLDS["min_radii"]
        and state.capture_spiral_done
    )