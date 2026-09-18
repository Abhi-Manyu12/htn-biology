"""
utils.py — Utility functions for the Zschokke 1996 orb web construction model.

Node coordinates, walkable-structure geometry, and distance calculations are
now driven entirely by config.yaml (via config_loader.CONFIG), so the same
functions here work unchanged for any environment geometry — e.g. a wider or
taller supporting structure, or different anchor spacing — configured there.
"""

import math

from .config_loader import CONFIG

# ---------------------------------------------------------------------------
# Node coordinate definitions (derived from config.yaml -> environment.nodes)
# ---------------------------------------------------------------------------
# Coordinate system: origin at bottom-left of frame, x right, y up (cm).
# See config.yaml for the source values and commentary on the supporting
# structure this models (Zschokke's Fig. 1A: 18cm high, 16cm wide U-shape).

NODE_COORDS = dict(CONFIG["environment"]["nodes"])

_DEFAULT_DISTANCE = CONFIG["environment"]["default_distance"]


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
        Node names present in NODE_COORDS.

    Returns
    -------
    float
        Distance in centimetres.
    """
    if node1 == node2:
        return 0.0

    c1 = NODE_COORDS.get(node1)
    c2 = NODE_COORDS.get(node2)

    if c1 is None or c2 is None:
        # Fallback for dynamically created nodes — use the configured
        # default cost instead of a hardcoded literal.
        return _DEFAULT_DISTANCE

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
