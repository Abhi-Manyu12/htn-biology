"""Audit what an HTN 'success' means in the anchor-removal sweep (sensitivity.py), at a given checkout.

Run INSIDE a private checkout (cwd = repo root), e.g. the 39b89f3 worktree that produced
sensitivity_comparison.csv:

    cd "$W/work/core/repo_39b89f3" && "$PY" "$W/report/scripts/core/rerun_htn_success_audit.py" "$D/htn_success_audit_39b89f3.json"

For removal probabilities 0.0..0.8 and the same seeds as the committed sweep (1000..1999) it records, per trial,
  * whether gtpyhop.find_plan returned a plan under the installed default strategy (GTPyhop 1.9.7: iterative
    greedy, no backtracking on downstream failure) -- this is what sensitivity.py counts as HTN success;
  * whether a plan exists under explicit full backtracking ('iterative_dfs_backtracking');
  * how many anchors survived, and how many radii / frame threads the replayed plan actually built, i.e. whether
    it would pass the baseline's structural criterion baseline.is_web_complete (8 radii, 4 frames, both spirals).
"""
import contextlib
import io
import json
import os
import sys

sys.path.insert(0, os.getcwd())
out = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

import gtpyhop  # noqa: E402
from spider_web_htn_updated import sensitivity as sens  # noqa: E402
from spider_web_htn_updated.config_loader import CONFIG  # noqa: E402
from spider_web_htn_updated.state import create_initial_state  # noqa: E402
from spider_web_htn_updated.baseline import is_web_complete  # noqa: E402
from spider_web_htn_updated import operators as _ops, methods as _mtd  # noqa: E402

# name -> operator function (main._ACTION_FUNCS does not exist yet at 39b89f3)
_ACTION_FUNCS = {f.__name__: f for f in (
    _ops.walk, _ops.anchor, _ops.lay_thread, _ops.attach_dragline, _ops.remove_thread, _ops.drop_down,
    _ops.swing_tarzan, _ops.reel_up, _ops.insert_radius, _ops.mark_proto_hub, _ops.lay_frame_thread,
    _ops.lay_radius, _ops.build_spiral_segment, _ops.mark_web_complete,
    _mtd.mark_high_thread_done, _mtd.mark_auxiliary_spiral_done, _mtd.mark_capture_spiral_done)}

REM = CONFIG["stochastic"]["anchor_availability"]["removable_nodes"]
CONFIG["stochastic"]["enabled"] = True
CONFIG["stochastic"]["anchor_availability"]["enabled"] = True
CONFIG["stochastic"]["wind"]["enabled"] = False

rows = []
for p in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    CONFIG["stochastic"]["anchor_availability"]["removal_prob"] = p
    agg = {"p": p, "n": n, "greedy_success": 0, "dfs_success": 0, "struct_complete": 0,
           "radii_hist": {}, "anchors_left_hist_fail": {}, "anchors_left_hist_succ": {}}
    for t in range(n):
        seed = 1000 + t
        s0 = create_initial_state(seed=seed)
        left = sum(1 for a in REM if a in s0.nodes)
        res = {}
        for strat in ("iterative_greedy", "iterative_dfs_backtracking"):
            sens._setup_domain()
            gtpyhop.set_recursive_planning(strat)
            with contextlib.redirect_stdout(io.StringIO()):
                gtpyhop.set_verbose_level(0)
                res[strat] = gtpyhop.find_plan(create_initial_state(seed=seed), [("build_web",)])
        g = res["iterative_greedy"]
        if g:
            agg["greedy_success"] += 1
            st = create_initial_state(seed=seed)
            for a in g:
                r = _ACTION_FUNCS[a[0]](st, *a[1:])
                if r is not False:
                    st = r
            agg["struct_complete"] += int(is_web_complete(st))
            agg["radii_hist"][st.radii_count] = agg["radii_hist"].get(st.radii_count, 0) + 1
            agg["anchors_left_hist_succ"][left] = agg["anchors_left_hist_succ"].get(left, 0) + 1
        else:
            agg["anchors_left_hist_fail"][left] = agg["anchors_left_hist_fail"].get(left, 0) + 1
        agg["dfs_success"] += int(bool(res["iterative_dfs_backtracking"]))
    rows.append(agg)
    print(p, agg["greedy_success"], agg["dfs_success"], agg["struct_complete"], dict(sorted(agg["radii_hist"].items())),
          "fail anchors-left:", dict(sorted(agg["anchors_left_hist_fail"].items())), flush=True)
gtpyhop.set_recursive_planning(False)
with open(out, "w") as f:
    json.dump({"cwd": os.getcwd(), "rows": rows}, f, indent=1)
