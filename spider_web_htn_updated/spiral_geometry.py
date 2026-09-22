"""
spiral_geometry.py — Continuous, multi-turn spiral waypoint generation for
the auxiliary and capture spiral construction phases.

Zschokke (1996) and the broader orb-weaver literature (e.g. Vollrath &
Mohren 1985) describe two geometrically distinct phases:

  - The auxiliary (scaffolding) spiral is laid working OUTWARD from the hub
    with roughly LOGARITHMIC (equiangular) radial growth — each successive
    loop is a roughly constant *multiple* further out than the loop before.
  - The capture (sticky) spiral is then laid working INWARD toward the hub,
    retracing the same rotational direction, with roughly constant
    (Archimedean) radial pitch — each successive loop is a roughly constant
    *distance* closer to the hub than the loop before — while the auxiliary
    silk is removed.

Both functions here turn that distinction into explicit polar-coordinate
waypoints around the hub, using real anchor coordinates so the resulting
geometry scales correctly if the supporting structure is rescaled.
"""

import math


def _base_angles(hub_xy, directions_xy):
    """atan2 angle (radians) from the hub to each direction's anchor."""
    hx, hy = hub_xy
    return [math.atan2(y - hy, x - hx) for x, y in directions_xy]


def _target_radii(hub_xy, directions_xy):
    """Euclidean distance from the hub to each direction's anchor."""
    hx, hy = hub_xy
    return [math.hypot(x - hx, y - hy) for x, y in directions_xy]


def generate_logarithmic_spiral(hub_xy, direction_names, directions_xy,
                                 turns, steps_per_turn, start_radius_fraction,
                                 name_prefix="aux_spiral_wp"):
    """
    Outward auxiliary spiral: exponential (logarithmic/equiangular) radial
    growth, from a small fraction of each direction's anchor radius up to
    that anchor radius, over ``turns`` full rotations around the hub.

    Returns a list of ``(waypoint_name, (x, y), source_direction_name)``
    tuples in hub-outward travel order.
    """
    hx, hy = hub_xy
    angles = _base_angles(hub_xy, directions_xy)
    targets = _target_radii(hub_xy, directions_xy)
    n_dirs = len(direction_names)
    n_steps = max(int(round(turns * steps_per_turn)), n_dirs)

    waypoints = []
    for i in range(n_steps):
        j = i % n_dirs
        t = i // n_dirs
        fraction = i / (n_steps - 1) if n_steps > 1 else 1.0

        r_target = targets[j]
        r_start = max(start_radius_fraction * r_target, 1e-6)
        # Exponential (equiangular) interpolation: r = r_start * (r_target/r_start)^fraction
        r = r_start ** (1 - fraction) * r_target ** fraction

        angle = angles[j] + t * 2 * math.pi
        x = hx + r * math.cos(angle)
        y = hy + r * math.sin(angle)
        waypoints.append((f"{name_prefix}_{i:02d}", (x, y), direction_names[j]))

    return waypoints


def generate_archimedean_spiral(hub_xy, direction_names, directions_xy,
                                 turns, steps_per_turn, end_radius_fraction,
                                 name_prefix="capture_spiral_wp"):
    """
    Inward capture spiral: linear (Archimedean, constant-pitch) radial
    decay, from each direction's anchor radius down to a small fraction of
    it, over ``turns`` full rotations around the hub.

    Returns a list of ``(waypoint_name, (x, y), source_direction_name)``
    tuples in edge-inward travel order.
    """
    hx, hy = hub_xy
    angles = _base_angles(hub_xy, directions_xy)
    targets = _target_radii(hub_xy, directions_xy)
    n_dirs = len(direction_names)
    n_steps = max(int(round(turns * steps_per_turn)), n_dirs)

    waypoints = []
    for i in range(n_steps):
        j = i % n_dirs
        t = i // n_dirs
        fraction = i / (n_steps - 1) if n_steps > 1 else 1.0

        r_start = targets[j]
        r_end = end_radius_fraction * r_start
        # Linear (Archimedean, constant pitch) interpolation.
        r = r_start + (r_end - r_start) * fraction

        angle = angles[j] + t * 2 * math.pi
        x = hx + r * math.cos(angle)
        y = hy + r * math.sin(angle)
        waypoints.append((f"{name_prefix}_{i:02d}", (x, y), direction_names[j]))

    return waypoints
