"""
operators.py — Primitive operators (actions) for the Zschokke 1996 model.

Each operator corresponds to an atomic movement documented by Zschokke:
walking, anchoring, laying threads, dropping, swinging ("Tarzan method"),
reeling up, and inserting radii.

Convention
----------
- Every operator takes ``state`` as its first argument, plus action-specific
  parameters.
- On success it mutates and returns ``state``.
- On precondition failure it returns ``False`` (GTPyhop will backtrack).
- All movement operators add to ``state.energy_expended`` using the
  distance-as-cost metric from Zschokke (1996).
"""

import gtpyhop

from .utils import calculate_distance, thread_exists
from .state import rigid


# ── helper ──────────────────────────────────────────────────────────────────

def _can_reach(state, target):
    """
    True if *target* is reachable from the spider's current position via
    any combination of structural walkable edges and existing threads (BFS).
    """
    if target not in state.nodes:
        return False
    if state.spider_pos == target:
        return True

    # Build adjacency from structural edges + threads
    visited = set()
    queue = [state.spider_pos]
    visited.add(state.spider_pos)

    while queue:
        current = queue.pop(0)
        # Structural edges
        for a, b in rigid.walkable_edges:
            neighbour = None
            if a == current:
                neighbour = b
            elif b == current:
                neighbour = a
            if neighbour and neighbour not in visited and neighbour in state.nodes:
                if neighbour == target:
                    return True
                visited.add(neighbour)
                queue.append(neighbour)
        # Thread edges
        for n1, n2, _ in state.threads:
            neighbour = None
            if n1 == current:
                neighbour = n2
            elif n2 == current:
                neighbour = n1
            if neighbour and neighbour not in visited and neighbour in state.nodes:
                if neighbour == target:
                    return True
                visited.add(neighbour)
                queue.append(neighbour)

    return False


# ── primitive operators ─────────────────────────────────────────────────────

def walk(state, start, end):
    """
    Spider walks from *start* to *end* along the structure or existing threads.

    Zschokke (1996): the spider always leaves a dragline; the distance covered
    is roughly proportional to the locomotory energy used.
    """
    if state.spider_pos != start:
        return False
    if not _can_reach(state, end):
        return False

    dist = calculate_distance(start, end)
    state.energy_expended += dist
    state.spider_pos = end
    return state


def anchor(state, node):
    """
    Designate the spider's current position as the named anchor *node*.

    This creates a new named point in the web graph.  The spider does not
    need to travel — it is defining where it already is (or very close by)
    as a new node.
    """
    state.nodes.add(node)
    state.spider_pos = node
    return state


def lay_thread(state, n1, n2, thread_type):
    """
    Lay a thread of *thread_type* between *n1* and *n2*.

    The spider must be at *n1*.  The new thread is recorded and the spider
    moves to *n2*, expending energy proportional to the distance.
    """
    if state.spider_pos != n1:
        return False

    state.nodes.add(n1)
    state.nodes.add(n2)
    state.threads.append((n1, n2, thread_type))
    dist = calculate_distance(n1, n2)
    state.energy_expended += dist
    state.spider_pos = n2
    return state


def attach_dragline(state, node):
    """Tighten and attach the trailing dragline at *node*."""
    if state.spider_pos != node:
        return False

    state.nodes.add(node)
    return state


def remove_thread(state, n1, n2):
    """
    Remove an existing thread between *n1* and *n2* (any type).

    Zschokke observed that the spider sometimes moves or removes older threads
    during proto-hub establishment.
    """
    for i, (t1, t2, _) in enumerate(state.threads):
        if (t1 == n1 and t2 == n2) or (t1 == n2 and t2 == n1):
            state.threads.pop(i)
            return state
    return False


def drop_down(state, from_node, to_node):
    """
    Spider drops down vertically using its dragline.

    Zschokke (1996, Fig. 2E): one of three ways the spider reaches the
    supporting structure when constructing a proto-radius.
    """
    if state.spider_pos != from_node:
        return False

    state.nodes.add(to_node)
    state.threads.append((from_node, to_node, "dragline"))
    dist = calculate_distance(from_node, to_node)
    state.energy_expended += dist
    state.spider_pos = to_node
    return state


def swing_tarzan(state, from_node, to_node):
    """
    "Tarzan method" — the spider walks a few cm, drops, and swings on the
    dragline to reach another thread or part of the supporting structure.

    Zschokke (1996): "the spider — after having attached the thread — walks a
    few centimetres and then drops down, swinging around the place where the
    dragline is attached."
    """
    if state.spider_pos != from_node:
        return False

    state.nodes.add(to_node)
    state.threads.append((from_node, to_node, "dragline"))
    dist = calculate_distance(from_node, to_node)
    state.energy_expended += dist
    state.spider_pos = to_node
    return state


def reel_up(state, from_node, to_node):
    """
    Spider reels up dragline while returning along a provisional thread,
    replacing it with a definitive thread.

    Zschokke: "the spider will then return along the provisional proto-radius
    (reeling it up along the way) back to the hub."
    """
    if state.spider_pos != from_node:
        return False
    if not thread_exists(state.threads, from_node, to_node):
        return False

    dist = calculate_distance(from_node, to_node)
    state.energy_expended += dist
    state.spider_pos = to_node
    return state


def insert_radius(state, anchor_node, hub_node):
    """
    Insert a definitive radius (or proto-radius) between *anchor_node* and
    *hub_node*.  The spider must be at the hub after reeling up.
    """
    if state.spider_pos != hub_node:
        return False

    # Remove any provisional thread and add the definitive one
    for i, (t1, t2, ttype) in enumerate(state.threads):
        if ttype == "dragline" and \
           ((t1 == anchor_node and t2 == hub_node) or
            (t1 == hub_node and t2 == anchor_node)):
            state.threads.pop(i)
            break

    state.threads.append((hub_node, anchor_node, "proto_radius"))
    state.proto_radii_count += 1
    return state


def mark_proto_hub(state, hub_node):
    """
    Mark *hub_node* as the proto-hub once several proto-radii converge there.

    Zschokke: "Gradually one point emerges where several proto-radii meet."
    """
    if state.proto_radii_count < 4:
        return False

    state.proto_hub_exists = True
    state.proto_hub_pos = hub_node
    state.nodes.add(hub_node)
    return state


def lay_frame_thread(state, n1, n2):
    """Lay a frame thread between *n1* and *n2*."""
    if state.spider_pos != n1:
        return False

    state.nodes.add(n2)
    state.threads.append((n1, n2, "frame"))
    dist = calculate_distance(n1, n2)
    state.energy_expended += dist
    state.spider_pos = n2
    state.frame_count += 1
    return state


def lay_radius(state, hub, anchor_node):
    """Lay a definitive radius from hub to anchor_node."""
    if state.spider_pos != hub:
        return False

    state.threads.append((hub, anchor_node, "radius"))
    dist = calculate_distance(hub, anchor_node)
    state.energy_expended += dist
    state.spider_pos = anchor_node
    state.radii_count += 1
    return state


def build_spiral_segment(state, n1, n2, spiral_type):
    """
    Lay one segment of a spiral (auxiliary or capture).

    Zschokke: circling the hub transitions seamlessly from hub structure →
    auxiliary spiral → capture spiral (Figs. 2I–K).
    """
    if state.spider_pos != n1:
        return False

    state.threads.append((n1, n2, spiral_type))
    dist = calculate_distance(n1, n2)
    state.energy_expended += dist
    state.spider_pos = n2
    return state


def mark_web_complete(state):
    """Mark the web as complete."""
    state.web_complete = True
    return state
