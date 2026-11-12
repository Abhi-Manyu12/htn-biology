"""Geometry measured from accepted chords, following Mulder Table 1 formulas.

Areas use polygonal envelopes of simulated thread geometry, not image pixels.
Cardinal capture counts/widths use ray intersections, with vertex deduplication.
"""
import math


FEATURES = ("web_area_cm2", "capture_spiral_area_cm2", "eccentricity",
            "mean_capture_spiral_count", "mean_mesh_space_cm", "radial_count_measured")


def cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def hull(points):
    points = sorted(set(tuple(p) for p in points))
    if len(points) <= 1:
        return points
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and cross((out[-1][0]-out[-2][0], out[-1][1]-out[-2][1]),
                                         (p[0]-out[-1][0], p[1]-out[-1][1])) <= 0:
                out.pop()
            out.append(p)
        return out
    return half(points)[:-1] + half(list(reversed(points)))[:-1]


def area(points):
    if len(points) < 3:
        return 0.0
    return abs(sum(cross(a, b) for a,b in zip(points, points[1:]+points[:1]))) / 2


def crossings(chords, origin, direction):
    values = []
    for a,b in chords:
        delta = (b[0]-a[0], b[1]-a[1])
        offset = (a[0]-origin[0], a[1]-origin[1])
        determinant = cross(direction, delta)
        if abs(determinant) < 1e-10:
            continue  # collinear boundary does not count as a transversal crossing
        r = cross(offset, delta) / determinant
        u = cross(offset, direction) / determinant
        if r > 1e-8 and -1e-8 <= u <= 1+1e-8:
            values.append(r)
    unique = []
    for value in sorted(values):
        if not unique or value-unique[-1] > 1e-6:
            unique.append(value)
    return unique


def measure_web(segments, endpoints, settings, complete):
    if not complete:
        return dict.fromkeys(FEATURES)
    hub = (settings.width_cm/2, settings.height_cm/2)
    structural = [endpoints[s.index] for s in segments if s.phase in ("frame", "radials") and s.silk]
    capture = [endpoints[s.index] for s in segments if s.phase == "capture" and s.silk]
    boundary = hull([p for edge in structural for p in edge])
    outer = hull([p for edge in capture for p in edge])
    directions = [(math.cos(2*math.pi*i/settings.radial_count), math.sin(2*math.pi*i/settings.radial_count))
                  for i in range(settings.radial_count)]
    inner = []
    for direction in directions:
        hits = crossings(capture, hub, direction)
        if hits:
            inner.append((hub[0]+hits[0]*direction[0], hub[1]+hits[0]*direction[1]))
    north, south = crossings(capture, hub, (0,1)), crossings(capture, hub, (0,-1))
    n, s = len(north), len(south)
    widths = (north[-1]-north[0] if n >= 2 else 0) + (south[-1]-south[0] if s >= 2 else 0)
    polygon_chords = list(zip(boundary, boundary[1:]+boundary[:1]))
    extents = [crossings(polygon_chords, hub, d) for d in ((1,0),(-1,0),(0,1),(0,-1))]
    width = sum(max(values) for values in extents[:2]) if all(extents[:2]) else None
    height = sum(max(values) for values in extents[2:]) if all(extents[2:]) else None
    return dict(web_area_cm2=area(boundary),
                capture_spiral_area_cm2=max(0,area(outer)-area(hull(inner))),
                eccentricity=abs(1-width/height) if width is not None and height else None,
                mean_capture_spiral_count=(n+s)/2,
                mean_mesh_space_cm=widths/(n+s-2) if n >= 2 and s >= 2 else None,
                radial_count_measured=sum(s.phase == "radials" and s.silk for s in segments))
