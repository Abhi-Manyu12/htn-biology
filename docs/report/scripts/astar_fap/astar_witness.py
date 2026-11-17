#!/usr/bin/env python3
"""astar_witness.py -- hand-built action sequences checked against the A* successor generator.

Two checks, both run in a private repo copy (--repo):
  (1) a complete plan that is CHEAPER than the 75.54 cm plan weighted A* returns, which shows that
      plan is not cost-optimal;
  (2) a reachable state S at which the heuristic exceeds the true cost-to-go (h(S) > h*(S)), i.e. the
      heuristic is not admissible, and an edge where it is not consistent.
Every action is looked up in get_successors(state) -- if the generator does not offer it, we abort.

    python astar_witness.py --repo <clone> [--hfix]
"""
import argparse
import contextlib
import io
import json
import math
import sys

p = argparse.ArgumentParser()
p.add_argument("--repo", required=True)
p.add_argument("--hfix", action="store_true")
args = p.parse_args()
sys.path.insert(0, args.repo)

with contextlib.redirect_stdout(io.StringIO()):
    import spider_web_astar.heuristic as H
    from spider_web_astar.operators import get_successors, is_goal
    from spider_web_astar.astar import find_plan
    from spider_web_htn.state import create_initial_state
if args.hfix:
    H.calculate_distance = lambda a, b: math.dist(a, b)

PREFIX = [  # hub on the zero-length pair bottom_path / anchor_bottom_center (both at (8, 0))
    ("lay_thread", "right_stick_top", "bottom_path", "dragline"),
]
for _ in range(4):
    PREFIX += [("swing_tarzan", "bottom_path", "anchor_bottom_center"),
               ("walk", "anchor_bottom_center", "bottom_path"),
               ("insert_radius", "anchor_bottom_center", "bottom_path")]
PREFIX += [("mark_proto_hub", "bottom_path")]
RADII = []
for _ in range(4):
    RADII += [("lay_radius", "bottom_path", "anchor_bottom_center"),
              ("walk", "anchor_bottom_center", "bottom_path")]
FRAME = [("lay_frame_thread", "bottom_path", "anchor_bottom_center"),
         ("lay_frame_thread", "anchor_bottom_center", "anchor_top_center")]
SPIRAL = [("build_spiral_segment", "anchor_top_center", "left_stick_top", "auxiliary_spiral"),
          ("build_spiral_segment", "left_stick_top", "anchor_left_upper", "auxiliary_spiral"),
          ("build_spiral_segment", "anchor_left_upper", "left_stick_mid", "auxiliary_spiral"),
          ("build_spiral_segment", "left_stick_mid", "crossbar_left", "auxiliary_spiral"),
          ("build_spiral_segment", "crossbar_left", "anchor_left_lower", "capture_spiral"),
          ("build_spiral_segment", "anchor_left_lower", "left_stick_bottom", "capture_spiral"),
          ("build_spiral_segment", "left_stick_bottom", "anchor_bottom_left", "capture_spiral"),
          ("build_spiral_segment", "anchor_bottom_left", "anchor_bottom_center", "capture_spiral")]
DONE = [("mark_web_complete",)]


def apply(seq, s):
    g, rows = 0.0, []
    for a in seq:
        succ = {act: (c, ns) for act, c, ns in get_successors(s)}
        if a not in succ:
            raise SystemExit(f"generator does not offer {a}")
        c, ns = succ[a]
        rows.append((a, c, H.heuristic(s), H.heuristic(ns)))
        g += c
        s = ns
    return s, g, rows


out = {"repo": args.repo, "hfix": args.hfix}
# (1) a full plan, radii before frame
s, g, rows = apply(PREFIX + RADII + FRAME + SPIRAL + DONE, create_initial_state())
out["cheap_plan"] = {"length": len(rows), "cost": g, "goal": bool(is_goal(s))}
# consistency: an edge with h(s) > c + h(s')
viol = [(list(a), c, hs, hn) for a, c, hs, hn in rows if hs > c + hn + 1e-9]
out["consistency_violations"] = viol[:3]
out["n_consistency_violations"] = len(viol)
# (2) state S: hub, frames, spirals done, no radii yet, spider at hub -> h(S) vs h*(S)
S, gS, _ = apply(PREFIX + FRAME + SPIRAL + [("walk", "anchor_bottom_center", "bottom_path")],
                 create_initial_state())
with contextlib.redirect_stdout(io.StringIO()):
    r = find_plan(S, time_limit_s=60, weight=1.0)
out["state_S"] = {"g": gS, "radii": S.radii_count, "frames": S.frame_count,
                  "capture_done": S.capture_spiral_done, "spider": S.spider_pos,
                  "h": H.heuristic(S), "h_star_found": (r.energy - gS) if r.success else None,
                  "astar_from_S": {k: v for k, v in r.to_dict().items()},
                  "plan_from_S": [list(a) for a in r.plan]}
print(json.dumps(out, indent=1))
