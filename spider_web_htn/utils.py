"""
utils.py — Utility functions for the Zschokke 1996 orb web construction model.

Provides node coordinates matching Zschokke's simple U-shaped supporting structure
(Fig. 1A: 18cm high, 16cm wide), distance calculations, and graph helpers.
"""

import math

# ---------------------------------------------------------------------------
# Node coordinate definitions
# ---------------------------------------------------------------------------
# Zschokke's simple supporting structure (Fig. 1A):
#   - Perspex plate with two vertical drinking straws (sticks), 16 cm apart
#   - Each stick is 18 cm high
#   - One horizontal cross-bar parallel to the plate
#   - Spider released at the top of the right-hand stick
#
# Coordinate system: origin at bottom-left of frame, x right, y up (cm).

NODE_COORDS = {
    # Stick tops and bottoms
    "right_stick_top":      (16.0, 18.0),
    "right_stick_mid":      (16.0, 12.0),
    "right_stick_bottom":   (16.0,  0.0),
    "left_stick_top":       ( 0.0, 18.0),
    "left_stick_mid":       ( 0.0, 12.0),
    "left_stick_bottom":    ( 0.0,  0.0),

    # Cross-bar (simple structure — one horizontal bar connecting sticks)
    "crossbar_right":       (16.0,  9.0),
    "crossbar_left":        ( 0.0,  9.0),

    # Bottom connecting path (floor of tray — the detour route)
    "bottom_path":          ( 8.0,  0.0),

    # Proto-hub position — typically near the centre of the web
    "proto_hub":            ( 8.0, 12.0),

    # Anchor points around the frame for radii and frame threads
    "anchor_top_center":    ( 8.0, 18.0),
    "anchor_left_upper":    ( 0.0, 15.0),
    "anchor_left_lower":    ( 0.0,  6.0),
    "anchor_right_upper":   (16.0, 15.0),
    "anchor_right_lower":   (16.0,  6.0),
    "anchor_bottom_left":   ( 3.0,  0.0),
    "anchor_bottom_center": ( 8.0,  0.0),
    "anchor_bottom_right":  (13.0,  0.0),
}


def get_node_coord(node_name):
    """
    Get (x, y) coordinates for a static node or dynamic spiral node (anchor@fraction).
    """
    if node_name in NODE_COORDS:
        return NODE_COORDS[node_name]

    if "@" in node_name:
        parts = node_name.split("@")
        anchor_name = parts[0]
        try:
            fraction = float(parts[1])
            hub_c = NODE_COORDS.get("proto_hub", (8.0, 12.0))
            anchor_c = NODE_COORDS.get(anchor_name)
            if anchor_c:
                x = hub_c[0] + fraction * (anchor_c[0] - hub_c[0])
                y = hub_c[1] + fraction * (anchor_c[1] - hub_c[1])
                return (x, y)
        except ValueError:
            pass

    return (8.0, 12.0)


def get_radius_node(anchor_name, fraction):
    """
    Helper to generate a dynamic node name for a position along a radius at a fraction [0, 1].
    """
    return f"{anchor_name}@{fraction:.2f}"


def calculate_distance(node1, node2):
    """
    Euclidean distance between two nodes (in cm).

    Zschokke (1996) used the distance the spider walked as a proxy for
    metabolic energy expenditure.  Since the spider always leaves a dragline,
    the distance covered ≈ the length of silk produced ≈ the locomotory
    energy used.

    Parameters
    ----------
    node1, node2 : str
        Node names present in NODE_COORDS or dynamic spiral nodes (anchor@fraction).

    Returns
    -------
    float
        Distance in centimetres.
    """
    if node1 == node2:
        return 0.0

    c1 = get_node_coord(node1)
    c2 = get_node_coord(node2)

    return math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


def get_adjacent_nodes(node, threads):
    """
    Return the set of nodes directly reachable from *node* via existing threads.

    Parameters
    ----------
    node : str
        The source node.
    threads : list of (str, str, str)
        Each entry is ``(n1, n2, thread_type)``.

    Returns
    -------
    set of str
    """
    adjacent = set()
    for n1, n2, _ in threads:
        if n1 == node:
            adjacent.add(n2)
        elif n2 == node:
            adjacent.add(n1)
    return adjacent


def thread_exists(threads, n1, n2):
    """Check whether a thread (of any type) exists between n1 and n2."""
    for t1, t2, _ in threads:
        if (t1 == n1 and t2 == n2) or (t1 == n2 and t2 == n1):
            return True
    return False


def count_threads_of_type(threads, thread_type):
    """Count threads of a given type."""
    return sum(1 for _, _, t in threads if t == thread_type)
