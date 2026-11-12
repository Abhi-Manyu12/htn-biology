"""
utils.py — Utility functions for the Zschokke 1996 orb web construction model.

Node coordinates, walkable-structure geometry, and distance calculations are
now driven entirely by config.yaml (via config_loader.CONFIG), so the same
functions here work unchanged for any environment geometry — e.g. a wider or
taller supporting structure, or different anchor spacing — configured there.
"""

import math

from .config_loader import CONFIG
from .spiral_geometry import generate_archimedean_spiral, generate_logarithmic_spiral

# ---------------------------------------------------------------------------
# Node coordinate definitions (derived from config.yaml -> environment.nodes)
# ---------------------------------------------------------------------------
# Coordinate system: origin at bottom-left of frame, x right, y up (cm).
# See config.yaml for the source values and commentary on the supporting
# structure this models (Zschokke's Fig. 1A: 18cm high, 16cm wide U-shape).

NODE_COORDS = dict(CONFIG["environment"]["nodes"])

_DEFAULT_DISTANCE = CONFIG["environment"]["default_distance"]


# ---------------------------------------------------------------------------
# Spiral waypoints (derived from config.yaml -> domain.spiral / spiral_nodes)
# ---------------------------------------------------------------------------
# Computed once at import time from the static hub/anchor coordinates above,
# then merged into NODE_COORDS so calculate_distance() gives real distances
# for spiral segments instead of falling back to the generic default.
#
# Each entry is (waypoint_name, (x, y), source_anchor_name) — source_anchor
# is the real config anchor whose direction/availability this waypoint
# belongs to, so methods.py can still skip a whole spiral spoke when that
# anchor is stochastically unavailable.

_domain_cfg = CONFIG["domain"]
_spiral_cfg = _domain_cfg.get("spiral")
_spiral_node_names = _domain_cfg.get("spiral_nodes", {})
_hub_name = _domain_cfg.get("default_hub_name", "proto_hub")

AUXILIARY_SPIRAL_WAYPOINTS = []
CAPTURE_SPIRAL_WAYPOINTS = []

if _spiral_cfg and _hub_name in NODE_COORDS:
    _hub_xy = tuple(NODE_COORDS[_hub_name])

    _aux_names = [n for n in _spiral_node_names.get("auxiliary", []) if n in NODE_COORDS]
    _cap_names = [n for n in _spiral_node_names.get("capture", []) if n in NODE_COORDS]

    if _aux_names:
        AUXILIARY_SPIRAL_WAYPOINTS = generate_logarithmic_spiral(
            _hub_xy, _aux_names, [tuple(NODE_COORDS[n]) for n in _aux_names],
            turns=_spiral_cfg["auxiliary"]["turns"],
            steps_per_turn=_spiral_cfg["auxiliary"]["steps_per_turn"],
            start_radius_fraction=_spiral_cfg["start_radius_fraction"],
        )

    if _cap_names:
        CAPTURE_SPIRAL_WAYPOINTS = generate_archimedean_spiral(
            _hub_xy, _cap_names, [tuple(NODE_COORDS[n]) for n in _cap_names],
            turns=_spiral_cfg["capture"]["turns"],
            steps_per_turn=_spiral_cfg["capture"]["steps_per_turn"],
            end_radius_fraction=_spiral_cfg["start_radius_fraction"],
        )

    for _name, _xy, _source in AUXILIARY_SPIRAL_WAYPOINTS:
        NODE_COORDS[_name] = _xy
    for _name, _xy, _source in CAPTURE_SPIRAL_WAYPOINTS:
        NODE_COORDS[_name] = _xy


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


# ---------------------------------------------------------------------------
# Web area / efficiency ratio (Way-Forward "Formal Evaluation Protocol",
# future plan.pdf Part 1 Section 3: Efficiency Ratio eta = S_used / Area_web)
# ---------------------------------------------------------------------------

def _convex_hull(points):
    """
    Convex hull of 2D points via Andrew's monotone chain, O(n log n).

    Parameters
    ----------
    points : list of (float, float)

    Returns
    -------
    list of (float, float)
        Hull vertices in counter-clockwise order. Fewer than 3 distinct
        points returns the (deduplicated) input unchanged.
    """
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def _polygon_area(vertices):
    """Shoelace-formula area of a simple polygon given ordered vertices."""
    if len(vertices) < 3:
        return 0.0
    total = 0.0
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def compute_web_area(state):
    """
    Estimate the constructed web's area (cm^2) as the convex hull area of
    every node touched by a structural thread (frame, radius, proto_radius,
    or either spiral) in the current state.

    This is a geometric estimate from the simulated output itself, not the
    literature figure in config.yaml's `empirical.area_web_cm2` — the two
    are at different physical scales (that figure is from a full-size
    outdoor web; this frame is a 16x18cm lab rig) and shouldn't be equated,
    only compared as a sanity check (see compare.py).

    Returns
    -------
    float
        Area in cm^2, or 0.0 if fewer than 3 distinct structural nodes
        exist yet (e.g. before any radii are laid).
    """
    structural_types = {"frame", "radius", "proto_radius",
                         "auxiliary_spiral", "capture_spiral"}
    nodes = set()
    for n1, n2, ttype in state.threads:
        if ttype in structural_types:
            nodes.add(n1)
            nodes.add(n2)

    coords = [NODE_COORDS[n] for n in nodes if n in NODE_COORDS]
    hull = _convex_hull(coords)
    return _polygon_area(hull)


def efficiency_ratio(state):
    """
    eta = S_used / Area_web (Way-Forward Part 1, Section 3: "Efficiency
    Ratio... Energy spent relative to web size").

    Returns
    -------
    float or None
        None if Area_web is 0 (no structural web yet — avoids a spurious
        divide-by-zero "infinitely efficient" reading).
    """
    area = compute_web_area(state)
    if area <= 0:
        return None
    return state.energy_expended / area
