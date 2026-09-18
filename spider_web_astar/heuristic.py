"""
heuristic.py — admissible heuristic for the flat-state A* baseline.

The heuristic uses only lower bounds that are guaranteed by the current
operator model. It does NOT encode the HTN hierarchy.

This is the validated "Stage 4" heuristic:
  - Radius term restricted to radius anchors only (not the global-cheapest
    hop anywhere in the environment).
  - Frame-count term restricted to frame anchors only.
  - The top-frame gate (state.top_frame_done) is combined optimistically
    with the frame-count requirement via max(): we assume one action CAN
    satisfy both the count requirement and the top-frame gate if it happens
    to target anchor_top_center, and only charge extra actions beyond that
    at the generic frame-anchor cost. This keeps the bound admissible
    (never assumes fewer actions than the true minimum) while being
    tighter than treating the two requirements as fully independent.
  - Aux/capture spiral terms are left on the fully generic bound, since
    their targets aren't restricted to a fixed anchor set in the operator
    model (see gen_build_spiral_segment) — tightening those would require
    reachability-aware analysis, which wasn't pursued here.

Admissibility was checked (not proven) by replaying a known feasible plan
through this heuristic and confirming h(state) never exceeded the true
remaining cost at any step — see validate_heuristic.py. This was also
checked against an earlier "Stage 3" variant (gate costed as a separate,
always-additional term rather than combined via max()) which passed
validation too but produced a worse weighted-A* plan in practice; Stage 4
matched the untightened baseline's plan quality at weight=3.0 while giving
a strictly tighter admissible bound, so it was kept as the final version.
"""

from .state import GOAL_THRESHOLDS
from .operators import _RADIUS_ANCHORS
from spider_web_htn.utils import NODE_COORDS, calculate_distance

# Frame threads can also target the two stick-top nodes, in addition to the
# radius anchors (see operators.gen_lay_frame_thread). Kept in sync manually
# since operators.py doesn't expose this as a shared constant.
_FRAME_ANCHORS = _RADIUS_ANCHORS + ["left_stick_top", "right_stick_top"]


def _count_threads(state, thread_type):
    return sum(1 for _, _, t in state.threads if t == thread_type)


def _positive_pairwise_min(nodes):
    """Smallest strictly positive distance between distinct known nodes."""
    coords = [NODE_COORDS[n] for n in nodes if n in NODE_COORDS]
    best = float("inf")

    for i, a in enumerate(coords):
        for b in coords[i + 1:]:
            d = calculate_distance(a, b)
            if d > 0:
                best = min(best, d)

    return best if best != float("inf") else 0.0


def _min_anchor_distance(anchor_nodes):
    """
    Minimum positive distance between any two usable anchor nodes.

    This is a lower bound for any one thread-producing operation whose
    endpoints are two distinct known nodes.
    """
    nodes = [n for n in anchor_nodes if n in NODE_COORDS]
    return _positive_pairwise_min(nodes)


def _min_node_to_targets_distance(nodes, targets):
    """
    Smallest strictly positive distance from any node in `nodes` to any
    (distinct) node in `targets`.

    Tighter than `_min_anchor_distance` when the action in question is known
    to require one endpoint from a restricted anchor set (e.g. a frame
    thread must end at a frame anchor, not just "some known node").
    """
    target_names = [t for t in targets if t in NODE_COORDS]
    best = float("inf")

    for n in nodes:
        if n not in NODE_COORDS:
            continue
        for t in target_names:
            if t == n:
                continue
            d = calculate_distance(NODE_COORDS[n], NODE_COORDS[t])
            if d > 0:
                best = min(best, d)

    return best if best != float("inf") else 0.0


def remaining_work(state):
    """Number of mandatory construction operations still required."""
    remaining_proto = max(
        0,
        GOAL_THRESHOLDS["min_proto_radii"] - state.proto_radii_count,
    )

    remaining_frame = max(
        0,
        GOAL_THRESHOLDS["min_frame"] - state.frame_count,
        0 if state.top_frame_done else 1,
    )

    remaining_radii = max(
        0,
        GOAL_THRESHOLDS["min_radii"] - state.radii_count,
    )

    remaining_aux = max(
        0,
        4 - _count_threads(state, "auxiliary_spiral"),
    )

    remaining_capture = max(
        0,
        GOAL_THRESHOLDS["min_capture_spiral"]
        - _count_threads(state, "capture_spiral"),
    )

    return (
        remaining_proto
        + remaining_frame
        + remaining_radii
        + remaining_aux
        + remaining_capture
    )


def progress_score(state):
    """
    Larger is better.

    Used only as a tie-breaker in A*. It does not affect f = g + h.
    """
    return -remaining_work(state)


def heuristic(state):
    """
    Admissible lower bound on remaining energy (Stage 4 — see module
    docstring).
    """
    if state.web_complete:
        return 0.0

    known_nodes = set(state.nodes)

    remaining_radii = max(
        0,
        GOAL_THRESHOLDS["min_radii"] - state.radii_count,
    )
    remaining_aux = max(
        0,
        4 - _count_threads(state, "auxiliary_spiral"),
    )
    remaining_capture = max(
        0,
        GOAL_THRESHOLDS["min_capture_spiral"]
        - _count_threads(state, "capture_spiral"),
    )

    generic_cost = _min_anchor_distance(known_nodes)

    # ── Radius term: restricted to radius anchors ───────────────────────
    radius_cost_per_action = _min_node_to_targets_distance(known_nodes, _RADIUS_ANCHORS)
    radius_cost = remaining_radii * radius_cost_per_action

    # ── Frame term: restricted to frame anchors, gate combined via max() ─
    count_needed = max(0, GOAL_THRESHOLDS["min_frame"] - state.frame_count)
    gate_needed = 0 if state.top_frame_done else 1
    frame_cost_per_action = _min_node_to_targets_distance(known_nodes, _FRAME_ANCHORS)

    frame_actions_needed = max(count_needed, gate_needed)
    if frame_actions_needed == 0:
        frame_cost = 0.0
    elif gate_needed == 1:
        top_frame_cost = _min_node_to_targets_distance(known_nodes, ["anchor_top_center"])
        extra_actions = frame_actions_needed - 1
        frame_cost = top_frame_cost + extra_actions * frame_cost_per_action
    else:
        frame_cost = frame_actions_needed * frame_cost_per_action

    # ── Aux / capture spiral terms: generic bound (not tightened) ────────
    spiral_cost = (remaining_aux + remaining_capture) * generic_cost

    return frame_cost + radius_cost + spiral_cost