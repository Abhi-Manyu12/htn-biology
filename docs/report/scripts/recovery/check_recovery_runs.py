"""Consistency checks quoted in the recovery section (prints only, writes nothing).

1. recovery_v1 vs recovery_v1_verified: every trial field except planning_wall_s is identical.
2. Mulder v4: all 720 retained/fresh IPyHOP pairs have identical success, completed actions, repairs,
   elapsed time and travel; counts of pairs whose method calls differ.
3. Mulder v4 suffix control vs IPyHOP trials (configured size, lag_1s, filtered) per seed.
4. Key cell means quoted in the text.
"""
import json

import numpy as np
import pandas as pd

from _common import EVID, R, V4

a = pd.read_csv(R / "mulder_results/recovery_v1/trials.csv")
b = pd.read_csv(R / "mulder_results/recovery_v1_verified/trials.csv")
diff = [c for c in a.columns if c != "planning_wall_s" and not a[c].fillna("NA").astype(str).equals(b[c].fillna("NA").astype(str))]
print("recovery_v1 vs verified, differing non-timing columns:", diff, "rows", len(a), len(b))
print("recovery wall-time correlation between runs:", np.corrcoef(a.planning_wall_s, b.planning_wall_s)[0, 1].round(3))

t = pd.read_csv(V4 / "trials.csv")
print("v4 trials:", len(t), t.groupby("planner_backend").size().to_dict())
k = ["controller", "seed", "complexity", "profile"]
r = t[t.planner_backend == "ipyhop_retained"].set_index(k).sort_index()
f = t[t.planner_backend == "ipyhop_fresh"].set_index(k).sort_index()
for c in ["success", "completed_actions", "repairs", "elapsed_s", "travel_cm", "planning_calls"]:
    print(f"  pairs differing in {c}:", int((r[c] != f[c]).sum()), "of", len(r))
print("  pairs differing in method_calls:", int((r.method_calls != f.method_calls).sum()),
      "; retained > fresh:", int((r.method_calls > f.method_calls).sum()))
dw = r.planning_wall_s - f.planning_wall_s
print("  pairs with retained wall time > fresh:", int((dw > 0).sum()))
sel = (r.method_calls < f.method_calls)
print("  among pairs with fewer retained calls: wall time higher in", int((dw[sel] > 0).sum()), "of", int(sel.sum()))

cfg = t[(t.complexity == "configured") & (t.profile == "moving_005") & (t.controller == "full")]
print(cfg.groupby("planner_backend")[["method_calls", "planning_wall_s"]].mean().round(3))
ex0 = cfg[cfg.seed != 0].groupby("planner_backend").planning_wall_s.mean().round(3)
print("excluding seed 0:", ex0.to_dict())

ctl = pd.DataFrame(json.loads((EVID / "mulder_suffix_control.json").read_text())["trials"]).set_index("seed")
lag = t[(t.complexity == "configured") & (t.profile == "lag_1s") & (t.controller == "filtered")]
for bk in ["ipyhop_fresh", "ipyhop_retained"]:
    v = lag[lag.planner_backend == bk].set_index("seed").sort_index()
    same = all((v[c] == ctl[c]).all() for c in ["success", "completed_actions", "repairs"])
    dev = max((v[c] - ctl[c]).abs().max() for c in ["elapsed_s", "travel_cm"])
    print(f"  control matches {bk} on success/actions/repairs for all 10 seeds:", same,
          f"; max |diff| elapsed/travel (CSV vs JSON float repr): {dev:.1e}")
print("  successes: control", int(ctl.success.sum()), {bk: int(lag[lag.planner_backend == bk].success.sum()) for bk in ["legacy", "ipyhop_fresh", "ipyhop_retained"]})
print("  control mean planning wall s:", ctl.planning_wall_s.mean().round(3), "method calls:", ctl.method_calls.mean())
print(lag.groupby("planner_backend")[["method_calls", "planning_wall_s"]].mean().round(3))
