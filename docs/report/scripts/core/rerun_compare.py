"""Re-run spider_web_htn_updated.compare.run_comparison and keep the per-seed Group B results.

Run INSIDE a private checkout (cwd = repo root of that checkout):

    cd "$W/work/core/repo_39b89f3" && "$PY" "$W/report/scripts/core/rerun_compare.py" 30 5000 "$D/rerun39_compare_n30.json"
    cd "$W/work/core/repo"         && "$PY" "$W/report/scripts/core/rerun_compare.py" 200 5000 "$D/rerun61_compare_n200.json"

The package's own config.yaml is used unchanged (at 39b89f3 it ships stochastic.enabled: true with anchor
removal p=0.2 and seed 7107; at 61d18d8 it ships stochastic.enabled: false). Also records which anchors the
HTN run (seed=None -> config seed) actually had available, and the number of radii it laid.
"""
import contextlib
import io
import json
import os
import statistics
import sys

sys.path.insert(0, os.getcwd())
n_seeds, max_steps, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]

from spider_web_htn_updated import compare  # noqa: E402
from spider_web_htn_updated.config_loader import CONFIG  # noqa: E402
from spider_web_htn_updated.state import create_initial_state  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()) as buf:
    res = compare.run_comparison(n_seeds=n_seeds, max_steps=max_steps, verbose=True)
printed = buf.getvalue()
a, b = res["group_a"], res["group_b"]
s0 = create_initial_state()
runs = []
for seed, r in enumerate(b["raw_runs"]):
    fs = r["final_state"]
    runs.append({"seed": seed, "success": r["success"], "steps_taken": r["steps_taken"],
                 "successful_actions": r["successful_actions"], "energy": r["energy_expended"],
                 "radii_count": fs.radii_count, "frame_count": fs.frame_count,
                 "n_aux_segments": sum(1 for t in fs.threads if t[2] == "auxiliary_spiral"),
                 "n_cap_segments": sum(1 for t in fs.threads if t[2] == "capture_spiral")})
succ = [r for r in runs if r["success"]]
summary = {
    "cwd": os.getcwd(), "n_seeds": n_seeds, "max_steps": max_steps,
    "stochastic_cfg": {k: CONFIG["stochastic"][k] for k in ("enabled", "seed")},
    "anchor_removal_cfg": CONFIG["stochastic"]["anchor_availability"],
    "htn": {k: v for k, v in a.items()},
    "htn_initial_nodes": sorted(s0.nodes),
    "baseline_success_rate": b["success_rate"],
    "baseline_energy_mean_succ": statistics.mean(r["energy"] for r in succ),
    "baseline_energy_sd_succ": statistics.stdev(r["energy"] for r in succ),
    "baseline_energy_median_succ": statistics.median(r["energy"] for r in succ),
    "baseline_steps_mean_succ": statistics.mean(r["steps_taken"] for r in succ),
    "baseline_successful_actions_mean_succ": statistics.mean(r["successful_actions"] for r in succ),
    "printed": printed,
    "runs": runs,
}
with open(out, "w") as f:
    json.dump(summary, f, indent=1, default=str)
print(printed)
print({k: summary[k] for k in ("baseline_success_rate", "baseline_energy_mean_succ", "baseline_energy_sd_succ",
                               "baseline_steps_mean_succ")}, "HTN:", a)
