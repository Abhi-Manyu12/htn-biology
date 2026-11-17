#!/usr/bin/env python3
"""fig_compare.py -- descriptive side-by-side of the four planners (NOT a joint conclusion, C17).

compare_cumcost : cumulative locomotory cost vs action index
                  (HTN: visualization/plan_data.js; updated HTN: visualization/plan_data_updated.js;
                   A*: visualization/plan_data_astar.js; FAP: our run, replayed through its operators).
compare_bars    : plan length, cost and planning wall time (runs.jsonl; HTN/updated/FAP: 20 timed
                  repetitions in one process, A*: 10 processes with PYTHONHASHSEED 0-9).
"""
import contextlib
import io
import os
import statistics
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CLONE, FIGDIR, REPO, by_tag, load_js, load_runs  # noqa: E402
from plotstyle import AGENT_COLORS, C, FIG_1COL, apply, save  # noqa: E402

sys.path.insert(0, CLONE)
with contextlib.redirect_stdout(io.StringIO()):
    from spider_web_fap import operators as fops
    from spider_web_fap import methods as fmtd
    from spider_web_fap.state import create_fap_initial_state

apply()
recs = load_runs()
COL = {"HTN (original)": AGENT_COLORS["HTN"], "HTN (updated)": C["sky"],
       "A*": AGENT_COLORS["A*"], "FAP": AGENT_COLORS["FAP"]}

# ------------------------------------------------------------ cumulative cost
series = {}
for name, f in [("HTN (original)", "plan_data.js"), ("HTN (updated)", "plan_data_updated.js"),
                ("A*", "plan_data_astar.js")]:
    d = load_js(os.path.join(REPO, "visualization", f))
    series[name] = [0.0] + [s["cumulative_energy"] for s in d["steps"]]
fap = by_tag(recs, "fap")[0]
s = create_fap_initial_state()
cum = [0.0]
for a in fap["plan"]:
    fn = getattr(fops, a[0], None) or getattr(fmtd, a[0])
    s = fn(s, *a[1:])
    cum.append(s.energy_expended)
series["FAP"] = cum
assert abs(cum[-1] - fap["energy_state"]) < 1e-9

fig, ax = plt.subplots(figsize=FIG_1COL)
for name, y in series.items():
    ax.plot(np.arange(len(y)), y, color=COL[name], drawstyle="steps-post")
    dy = {"HTN (original)": 30, "HTN (updated)": -45}.get(name, 0)
    ax.text(len(y) - 1 + 1.5, y[-1] + dy, f"{name}\n{len(y) - 1} actions, {y[-1]:.1f} cm",
            color=COL[name], fontsize=8, va="center")
ax.set_xlim(0, 165)
ax.set_ylim(0, 820)
ax.set_xlabel("action index")
ax.set_ylabel("cumulative locomotory cost (cm)")
save(fig, os.path.join(FIGDIR, "compare_cumcost"))

# ------------------------------------------------------------ bars
htn, upd = by_tag(recs, "htn")[0], by_tag(recs, "htn_updated")[0]
seeds = by_tag(recs, "astar_old_seed")
head = by_tag(recs, "astar_head_default")[0]
ast_t = [r["wall_time_raw"] for r in seeds]
ast_cost = [r["energy_raw"] for r in seeds]
ast_len = [r["plan_length"] for r in seeds]
rows = [
    ("HTN\n(original)", htn["plan_length"], htn["energy_state"], htn["timing"]["all_s"], COL["HTN (original)"]),
    ("HTN\n(updated)", upd["plan_length"], upd["energy_state"], upd["timing"]["all_s"], COL["HTN (updated)"]),
    ("A*\n1e1bd44", statistics.median(ast_len), statistics.median(ast_cost), ast_t, COL["A*"]),
    ("FAP", fap["plan_length"], fap["energy_state"], fap["timing"]["all_s"], COL["FAP"]),
]
fig, axs = plt.subplots(1, 3, figsize=(7.0, 3.0))
x = np.arange(len(rows) + 1)
labels = ["HTN\norig.", "HTN\nupd.", "A*\n1e1bd44", "FAP", "A*\n61d18d8"]
for j, r in enumerate(rows):
    axs[0].bar(j, r[1], color=r[4], width=0.65)
    axs[0].text(j, r[1] + 2, f"{r[1]:g}", ha="center", fontsize=8)
    axs[1].bar(j, r[2], color=r[4], width=0.65)
    axs[1].text(j, r[2] + 12, f"{r[2]:.1f}", ha="center", fontsize=8)
    t = np.array(r[3]) * 1e3
    med = np.median(t)
    axs[2].bar(j, med, color=r[4], width=0.65)
    axs[2].errorbar(j, med, yerr=[[med - t.min()], [t.max() - med]], color="k", lw=0.8, capsize=2)
    axs[2].text(j, t.max() * 1.35, f"{med:.3g}", ha="center", fontsize=8)
# A* at HEAD: no plan -> hatched marker in the time panel only
jh = len(rows)
for a in axs[:2]:
    a.text(jh, 0.03, "no plan", transform=a.get_xaxis_transform(), ha="center", fontsize=7.5,
           color=C["vermillion"], rotation=90, va="bottom")
axs[2].bar(jh, head["wall_time_raw"] * 1e3, color="white", edgecolor=C["vermillion"], hatch="///", width=0.65)
axs[2].text(jh, head["wall_time_raw"] * 1e3 * 1.35, "$\\geq$120 s\n(budget)", ha="center", fontsize=7.5,
            color=C["vermillion"])
axs[0].set_ylabel("plan length (actions)")
axs[1].set_ylabel("locomotory cost (cm)")
axs[2].set_ylabel("planning wall time (ms)")
axs[2].set_yscale("log")
axs[2].set_ylim(1, 2e6)
axs[0].set_ylim(0, 150)
axs[1].set_ylim(0, 860)
for a in axs:
    a.set_xticks(x)
    a.set_xticklabels(labels, fontsize=7.5)
    a.grid(axis="x", visible=False)
fig.tight_layout()
save(fig, os.path.join(FIGDIR, "compare_bars"))

print({r[0].replace("\n", " "): (r[1], round(r[2], 2), round(np.median(r[3]) * 1e3, 3),
                                 round(min(r[3]) * 1e3, 3), round(max(r[3]) * 1e3, 3)) for r in rows})
print("astar seeds cost", sorted(ast_cost), "len", sorted(ast_len))
