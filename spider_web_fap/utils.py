"""
utils.py — Geometry, node coordinates, and measurement helpers for the FAP model.

Based on the 5 Fixed Action Patterns (FAPs) model:
1. Proto-Web & Frame FAP (Y-Shape core creation)
2. Radial Spoke Construction FAP (Leg angle measurement & tension balancing)
3. Auxiliary (Scaffolding) Spiral FAP
4. Capture (Sticky) Spiral FAP (Silk chemistry switch & destructive recycling)
5. Stabilimentum Construction FAP
"""

import math

# Node coordinate system for FAP web model (16cm wide x 18cm high frame)
FAP_NODE_COORDS = {
    # Frame outer corners and anchors
    "anchor_top_left":     ( 0.0, 18.0),
    "anchor_top_right":    (16.0, 18.0),
    "anchor_bottom_left":  ( 0.0,  0.0),
    "anchor_bottom_right": (16.0,  0.0),
    "anchor_bottom_stem":  ( 8.0,  0.0),

    # Key intermediate nodes for Y-frame
    "bridge_midpoint":     ( 8.0, 18.0),
    "hub_center":          ( 8.0, 12.0),

    # Frame boundary points (Outer wheel perimeter for spokes & frame lines)
    "frame_top_center":    ( 8.0, 18.0),
    "frame_top_right":     (14.0, 16.0),
    "frame_right_mid":     (16.0, 12.0),
    "frame_bottom_right":  (14.0,  4.0),
    "frame_bottom_center": ( 8.0,  0.0),
    "frame_bottom_left":   ( 2.0,  4.0),
    "frame_left_mid":      ( 0.0, 12.0),
    "frame_top_left":      ( 2.0, 16.0),

    # Stabilimentum decorative nodes around the hub
    "stabilimentum_top":    ( 8.0, 13.5),
    "stabilimentum_bottom": ( 8.0, 10.5),
}


def calculate_distance(node1, node2):
    """Euclidean distance in cm between node1 and node2."""
    if node1 == node2:
        return 0.0
    c1 = FAP_NODE_COORDS.get(node1)
    c2 = FAP_NODE_COORDS.get(node2)
    if c1 is None or c2 is None:
        return 2.0
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)


def angle_from_center(center_node, target_node):
    """Angle in degrees (0..360) from center_node to target_node."""
    c_center = FAP_NODE_COORDS.get(center_node)
    c_target = FAP_NODE_COORDS.get(target_node)
    if not c_center or not c_target:
        return 0.0
    dx = c_target[0] - c_center[0]
    dy = c_target[1] - c_center[1]
    angle = math.degrees(math.atan2(dy, dx))
    if angle < 0:
        angle += 360.0
    return angle


def measure_angular_gap(hub, node1, node2):
    """
    Simulate the spider's leg-based angle measurement between two spokes.
    Returns gap angle in degrees.
    """
    a1 = angle_from_center(hub, node1)
    a2 = angle_from_center(hub, node2)
    diff = abs(a1 - a2) % 360.0
    if diff > 180:
        diff = 360.0 - diff
    return diff
