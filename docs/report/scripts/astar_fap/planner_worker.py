#!/usr/bin/env python3
"""planner_worker.py -- run ONE planner from a private repo copy and print a JSON record.

Used by run_measurements.py (which spawns one subprocess per configuration so that the
A* package can be imported from two different commits).  Never run against the read-only
repo: --repo must point to a private clone/worktree under W/work/astar_fap/.

    python planner_worker.py --repo <clone> htn            [--reps N]
    python planner_worker.py --repo <clone> htn_updated    [--reps N]
    python planner_worker.py --repo <clone> fap            [--reps N] [--perturb NAME] [--strategy S]
    python planner_worker.py --repo <clone> astar --weight 3 --time 60 [--k K] [--hfix] [--trace]
"""
import argparse
import contextlib
import io
import json
import math
import statistics
import sys
import time


def _quiet_import(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn()


def _timeit(fn, reps):
    out, times = None, []
    for _ in range(reps):
        buf = io.StringIO()
        t0 = time.perf_counter()
        with contextlib.redirect_stdout(buf):
            out = fn()
        times.append(time.perf_counter() - t0)
    return out, times


def _tsum(times):
    return {"reps": len(times), "median_s": statistics.median(times), "min_s": min(times),
            "max_s": max(times), "all_s": times}


# --------------------------------------------------------------------------- HTN (original)
def run_htn(args):
    import gtpyhop
    from spider_web_htn.main import setup_domain
    from spider_web_htn.state import create_initial_state
    from spider_web_htn.utils import get_node_coord
    gtpyhop.set_verbose_level(0)
    dom = _quiet_import(setup_domain)
    plan, times = _timeit(lambda: gtpyhop.find_plan(create_initial_state(), [("build_web",)]), args.reps)
    s = create_initial_state()
    for a in plan:
        r = dom._action_dict[a[0]](s, *a[1:])
        assert r is not False, a
        s = r
    return {"planner": "htn", "success": bool(plan), "plan": [list(a) for a in plan],
            "plan_length": len(plan), "energy_state": s.energy_expended, "timing": _tsum(times),
            "threads": [[a, b, t] for a, b, t in s.threads],
            "coords": {n: list(get_node_coord(n)) for t in s.threads for n in t[:2]},
            "spider_start": create_initial_state().spider_pos}


# --------------------------------------------------------------------------- HTN (updated)
def run_htn_updated(args):
    import gtpyhop
    from spider_web_htn_updated.main import setup_domain, replay_plan
    from spider_web_htn_updated.state import create_initial_state
    from spider_web_htn_updated.utils import NODE_COORDS as UC

    def get_node_coord(n):
        return UC.get(n, (float("nan"), float("nan")))
    gtpyhop.set_verbose_level(0)
    _quiet_import(setup_domain)
    plan, times = _timeit(lambda: gtpyhop.find_plan(create_initial_state(), [("build_web",)]), args.reps)
    s = _quiet_import(lambda: replay_plan(plan))
    return {"planner": "htn_updated", "success": bool(plan), "plan": [list(a) for a in plan],
            "plan_length": len(plan), "energy_state": s.energy_expended, "timing": _tsum(times),
            "threads": [[a, b, t] for a, b, t in s.threads],
            "coords": {n: list(get_node_coord(n)) for t in s.threads for n in t[:2]}}


# --------------------------------------------------------------------------- FAP
def run_fap(args):
    import gtpyhop
    from spider_web_fap.main import setup_fap_domain, _estimate_fap_energy
    from spider_web_fap.state import create_fap_initial_state
    from spider_web_fap.utils import FAP_NODE_COORDS
    gtpyhop.set_verbose_level(0)
    dom = _quiet_import(setup_fap_domain)
    if args.strategy:
        _quiet_import(lambda: gtpyhop.set_recursive_planning(args.strategy))

    def init():
        s = create_fap_initial_state()
        if args.perturb == "start_top_right":      # spider released on the other top anchor
            s.spider_pos = "anchor_top_right"
        elif args.perturb == "start_hub":
            s.spider_pos = "hub_center"
        elif args.perturb == "y_frame_prebuilt":    # stage-1 flag already true
            s.y_frame_established = True
        return s

    plan, times = _timeit(lambda: gtpyhop.find_plan(init(), [("build_fap_web",)]), args.reps)
    rec = {"planner": "fap", "perturb": args.perturb, "strategy": args.strategy,
           "success": bool(plan), "plan_returned": repr(plan)[:200] if not plan else None,
           "timing": _tsum(times)}
    if not plan:
        return rec
    s = init()
    removed = []
    for a in plan:
        before = list(s.threads)
        r = dom._action_dict[a[0]](s, *a[1:])
        assert r is not False, a
        s = r
        for t in before:
            if t not in s.threads and t[2] == "auxiliary_spiral":
                removed.append(list(t))
    rec.update({"plan": [list(a) for a in plan], "plan_length": len(plan),
                "energy_state": s.energy_expended, "energy_estimator": _estimate_fap_energy(plan),
                "threads": [list(t) for t in s.threads], "recycled": removed,
                "recycled_count": s.recycled_threads_count,
                "coords": {k: list(v) for k, v in FAP_NODE_COORDS.items()}})
    return rec


# --------------------------------------------------------------------------- A*
def run_astar(args):
    import heapq as _hq
    import spider_web_astar.astar as A
    import spider_web_astar.heuristic as H
    from spider_web_astar.state import GOAL_THRESHOLDS
    from spider_web_astar.operators import get_successors, is_goal
    from spider_web_htn.state import create_initial_state
    from spider_web_htn.utils import NODE_COORDS

    if args.k is not None:            # problem-size scaling: radii and capture-spiral targets
        GOAL_THRESHOLDS["min_radii"] = args.k
        GOAL_THRESHOLDS["min_capture_spiral"] = args.k

    if args.hfix:
        # Our patch (NOT in the repo): heuristic.py passes coordinate tuples to
        # spider_web_htn.utils.calculate_distance, which expects node NAMES.  Replace it with a
        # Euclidean distance on tuples, i.e. the bound the heuristic docstring describes.
        H.calculate_distance = lambda a, b: math.dist(a, b)

    trace = []
    if args.trace:
        t0 = [None]
        pops = [0]

        class _HQ:
            heappush = staticmethod(_hq.heappush)

            @staticmethod
            def heappop(h):
                item = _hq.heappop(h)
                pops[0] += 1
                if t0[0] is None:
                    t0[0] = time.perf_counter()
                if pops[0] % args.trace_every == 1 or args.trace_every == 1:
                    trace.append([time.perf_counter() - t0[0], pops[0], len(h) + 1, item[0], item[2]])
                return item
        A.heapq = _HQ

    s0 = create_initial_state()
    r = A.find_plan(s0, time_limit_s=args.time, max_nodes=args.max_nodes, weight=args.weight)
    rec = {"planner": "astar", "weight": args.weight, "k": args.k, "hfix": args.hfix,
           "time_limit_s": args.time, "max_nodes": args.max_nodes, "h0": H.heuristic(s0),
           **r.to_dict(), "energy_raw": r.energy, "wall_time_raw": r.wall_time,
           "plan": [list(a) for a in r.plan], "trace": trace}
    if r.success:
        # replay the plan through the generator to get exact per-step g and h
        s, g, path = s0, 0.0, []
        for a in r.plan:
            succ = {act: (c, ns) for act, c, ns in get_successors(s)}
            c, ns = succ[tuple(a)]
            path.append({"action": list(a), "g": g, "h": H.heuristic(s),
                         "progress": H.progress_score(s), "cost": c})
            g += c
            s = ns
        path.append({"action": None, "g": g, "h": H.heuristic(s), "progress": H.progress_score(s), "cost": 0})
        rec["path"] = path
        rec["goal_ok"] = bool(is_goal(s))
        rec["threads"] = [[a, b, t] for a, b, t in s.threads]
        rec["coords"] = {k: list(v) for k, v in NODE_COORDS.items()}
    else:
        fs = r.final_state
        rec["best_state"] = None if fs is None else {
            "proto_hub_exists": fs.proto_hub_exists, "proto_hub_pos": fs.proto_hub_pos,
            "proto_radii": fs.proto_radii_count, "frames": fs.frame_count,
            "top_frame_done": fs.top_frame_done, "radii": fs.radii_count,
            "spider_pos": fs.spider_pos, "energy": fs.energy_expended}
    return rec


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("which", choices=["htn", "htn_updated", "fap", "astar"])
    p.add_argument("--reps", type=int, default=10)
    p.add_argument("--weight", type=float, default=3.0)
    p.add_argument("--time", type=float, default=60.0)
    p.add_argument("--max-nodes", dest="max_nodes", type=int, default=None)
    p.add_argument("--k", type=int, default=None)
    p.add_argument("--hfix", action="store_true")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--trace-every", dest="trace_every", type=int, default=50)
    p.add_argument("--perturb", default=None)
    p.add_argument("--strategy", default=None)
    args = p.parse_args()
    sys.path.insert(0, args.repo)
    import os
    os.chdir(args.repo)
    fn = {"htn": run_htn, "htn_updated": run_htn_updated, "fap": run_fap, "astar": run_astar}[args.which]
    rec = _quiet_import(lambda: fn(args))
    print("@@JSON@@" + json.dumps(rec))


if __name__ == "__main__":
    main()
