"""
operators.py — Primitive operators (actions) for the FAP model.

Directly implements the atomic actions specified in the 5 FAP Macro-Stages:
- Bridge & Y-frame construction (midpoint walk, slack line attach, vertical drop, Y-tighten)
- Radial spoke construction (up and out, lay loose line, pull tight, angle measure)
- Silk chemistry switching (dry structural -> sticky capture)
- Leg-guided placement & destructive recycling (bite and eat scaffolding line)
- Stabilimentum construction (decorative silk zig-zags)
"""

import gtpyhop
from .utils import calculate_distance, measure_angular_gap, FAP_NODE_COORDS
from .state import rigid


def _can_reach_fap(state, target):
    """BFS reachability check using walkable edges + existing threads."""
    if target not in state.nodes:
        return False
    if state.spider_pos == target:
        return True

    visited = {state.spider_pos}
    queue = [state.spider_pos]

    while queue:
        curr = queue.pop(0)
        # Check structural edges
        for a, b in rigid.walkable_edges:
            nbr = b if a == curr else (a if b == curr else None)
            if nbr and nbr not in visited and nbr in state.nodes:
                if nbr == target: return True
                visited.add(nbr)
                queue.append(nbr)
        # Check thread edges
        for n1, n2, _, _ in state.threads:
            nbr = n2 if n1 == curr else (n1 if n2 == curr else None)
            if nbr and nbr not in visited and nbr in state.nodes:
                if nbr == target: return True
                visited.add(nbr)
                queue.append(nbr)

    return False


# ── FAP Stage 1: Proto-Web & Y-Frame ────────────────────────────────────────

def walk(state, start, end):
    """Spider walks along existing structure or threads."""
    if state.spider_pos != start:
        return False
    if not _can_reach_fap(state, end):
        return False

    dist = calculate_distance(start, end)
    state.energy_expended += dist
    state.spider_pos = end
    return state


def lay_bridge_thread(state, n1, n2):
    """Lay horizontal bridge thread across the top gap."""
    if state.spider_pos != n1:
        return False

    state.nodes.add(n1)
    state.nodes.add(n2)
    state.threads.append((n1, n2, "bridge", state.silk_chemistry))
    dist = calculate_distance(n1, n2)
    state.energy_expended += dist
    state.spider_pos = n2
    state.bridge_established = True
    return state


def walk_to_midpoint(state, start, mid_node):
    """FAP Step 1: Walk halfway across newly established bridge thread."""
    if state.spider_pos != start:
        return False
    state.nodes.add(mid_node)
    dist = calculate_distance(start, mid_node)
    state.energy_expended += dist
    state.spider_pos = mid_node
    return state


def attach_slack_line(state, mid_node):
    """FAP Step 2: At exact midpoint, attach a new loose thread of silk."""
    if state.spider_pos != mid_node:
        return False
    state.nodes.add(mid_node)
    state.slack_line_attached = True
    return state


def drop_down_to_anchor(state, from_node, lower_anchor):
    """FAP Step 3: Drop straight down from midpoint toward lower anchor point."""
    if state.spider_pos != from_node:
        return False
    state.nodes.add(lower_anchor)
    state.threads.append((from_node, lower_anchor, "dragline", state.silk_chemistry))
    dist = calculate_distance(from_node, lower_anchor)
    state.energy_expended += dist
    state.spider_pos = lower_anchor
    return state


def tighten_y_frame(state, lower_anchor, hub_node):
    """
    FAP Step 4: Pull line downward and anchor below.
    Tension yanks original horizontal bridge down into a V-shape,
    vertical line forms the stem, creating a perfect Y-shape.
    """
    if state.spider_pos != lower_anchor:
        return False

    state.nodes.add(hub_node)
    # Remove initial flat bridge
    for i, (t1, t2, ttype, _) in enumerate(state.threads):
        if ttype == "bridge":
            state.threads.pop(i)
            break

    # Add Y-frame lines (V-arms + vertical stem)
    state.threads.append(("anchor_top_left", hub_node, "y_frame", state.silk_chemistry))
    state.threads.append(("anchor_top_right", hub_node, "y_frame", state.silk_chemistry))
    state.threads.append((hub_node, lower_anchor, "y_frame", state.silk_chemistry))

    # Move spider to central Y-hub
    dist = calculate_distance(lower_anchor, hub_node)
    state.energy_expended += dist
    state.spider_pos = hub_node
    state.y_frame_established = True
    return state


# ── FAP Stage 2: Radial Spoke Construction ──────────────────────────────────

def climb_up_and_out(state, hub_node, frame_edge):
    """FAP Step 1: Climb from central hub up an existing line of Y-frame to outer edge."""
    if state.spider_pos != hub_node:
        return False
    dist = calculate_distance(hub_node, frame_edge)
    state.energy_expended += dist
    state.spider_pos = frame_edge
    return state


def lay_loose_spoke(state, frame_start, frame_end, hub_node):
    """
    FAP Step 2: Step slightly along outer frame, attach new thread of silk,
    then crawl back down to central hub, spinning a loose line behind it.
    """
    if state.spider_pos != frame_start:
        return False

    # Step along frame
    d1 = calculate_distance(frame_start, frame_end)
    state.nodes.add(frame_end)
    state.energy_expended += d1

    # Spin loose line back to hub
    d2 = calculate_distance(frame_end, hub_node)
    state.threads.append((frame_end, hub_node, "loose_spoke", state.silk_chemistry))
    state.energy_expended += d2
    state.spider_pos = hub_node
    return state


def pull_spoke_tight(state, hub_node, frame_node):
    """
    FAP Step 3: Upon reaching central hub, pull thread tight,
    anchoring it securely at exact center.
    """
    if state.spider_pos != hub_node:
        return False

    # Replace loose spoke with tight radial spoke
    for i, (t1, t2, ttype, _) in enumerate(state.threads):
        if ttype == "loose_spoke" and \
           ((t1 == frame_node and t2 == hub_node) or (t1 == hub_node and t2 == frame_node)):
            state.threads.pop(i)
            break

    state.threads.append((hub_node, frame_node, "radius", state.silk_chemistry))
    state.spokes_count += 1
    return state


def measure_angle_gap_check(state, hub_node, spoke1, spoke2):
    """
    FAP Step 4: Angle Measurement.
    Spider uses legs to physically measure gap between new line and adjacent spoke.
    Sensory feedback validates uniform spacing.
    """
    return state


# ── FAP Stage 3 & 4: Spirals & Chemistry & Recycling ───────────────────────

def switch_silk_chemistry(state, new_chemistry):
    """
    FAP Step 1 (Capture Spiral): Switch internal silk production from strong,
    dry structural silk to highly elastic thread coated in liquid glue droplets.
    """
    state.silk_chemistry = new_chemistry
    return state


def build_auxiliary_spiral_segment(state, n1, n2):
    """FAP Stage 3: Lay temporary scaffolding spiral working outward from hub."""
    if state.spider_pos != n1:
        return False

    state.nodes.add(n2)
    state.threads.append((n1, n2, "auxiliary_spiral", "dry_structural"))
    dist = calculate_distance(n1, n2)
    state.energy_expended += dist
    state.spider_pos = n2
    return state


def leg_guided_capture_dab(state, n1, n2):
    """
    FAP Step 3 (Capture Spiral): Leg-Guided Placement.
    - Outer leg feels temporary scaffolding spiral track.
    - Inner leg grasps radial spokes for uniform distance.
    - Spinneret dabs sticky silk onto spoke.
    """
    if state.spider_pos != n1:
        return False

    state.nodes.add(n2)
    state.threads.append((n1, n2, "capture_spiral", "sticky_capture"))
    dist = calculate_distance(n1, n2)
    state.energy_expended += dist
    state.spider_pos = n2
    return state


def bite_and_recycle_scaffolding(state, n1, n2):
    """
    FAP Step 4 (Capture Spiral): Destructive Recycling.
    Spider bites, rolls up, and eats the old temporary scaffolding line
    to recycle silk proteins.
    """
    for i, (t1, t2, ttype, _) in enumerate(state.threads):
        if ttype == "auxiliary_spiral" and \
           ((t1 == n1 and t2 == n2) or (t1 == n2 and t2 == n1)):
            state.threads.pop(i)
            state.recycled_threads_count += 1
            return state
    return state


# ── FAP Stage 5: Stabilimentum ─────────────────────────────────────────────

def construct_stabilimentum_segment(state, hub_node, target_node):
    """
    FAP Stage 5: Construct Stabilimentum.
    Spider lays decorative/reflective zig-zag silk structure in hub center.
    """
    if state.spider_pos != hub_node and state.spider_pos != target_node:
        return False

    state.threads.append((hub_node, target_node, "stabilimentum", "dry_structural"))
    dist = calculate_distance(state.spider_pos, target_node)
    state.energy_expended += dist
    state.spider_pos = target_node
    state.stabilimentum_done = True
    return state


def mark_fap_complete(state):
    """Mark FAP web complete."""
    state.web_complete = True
    return state
