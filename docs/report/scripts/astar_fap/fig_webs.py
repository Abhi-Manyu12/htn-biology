#!/usr/bin/env python3
"""fig_webs.py -- FAP web (single panel) and the four planners' final webs side by side.

Data: W/work/astar_fap/data/runs.jsonl (tags htn, htn_updated, fap; produced by run_measurements.py,
re-run at commit 61d18d8) and the committed A* plan visualization/plan_data_astar.js.
Also prints the per-type thread counts used in the comparison table.
"""
import contextlib
import io
import os
import sys
from collections import Counter

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CLONE, FIGDIR, REPO, TYPE_KEY, by_tag, draw_web, legend_handles,  # noqa: E402
                    load_js, load_runs)
from plotstyle import FIG_SQUARE, apply, save  # noqa: E402

sys.path.insert(0, CLONE)
with contextlib.redirect_stdout(io.StringIO()):
    from spider_web_htn import operators as ops
    from spider_web_htn.state import create_initial_state

apply()
recs = load_runs()
htn, upd, fap = by_tag(recs, "htn")[0], by_tag(recs, "htn_updated")[0], by_tag(recs, "fap")[0]

ast = load_js(os.path.join(REPO, "visualization/plan_data_astar.js"))
s = create_initial_state()
for st in ast["steps"]:
    s = getattr(ops, st["action"][0])(s, *st["action"][1:])
ast_threads = [list(t) for t in s.threads]
ast_coords = {k: tuple(v) for k, v in ast["node_coords"].items()}

# ---------------------------------------------------------------- FAP single panel
fc = {k: tuple(v) for k, v in fap["coords"].items()}
fig, ax = plt.subplots(figsize=FIG_SQUARE)
types = draw_web(ax, fap["threads"], fc, rig="fap", removed=fap["recycled"])
ax.plot(*fc["hub_center"], marker="o", ms=6, mfc="none", mec="k", mew=0.9, zorder=6)
ax.annotate("hub_center", fc["hub_center"], xytext=(11.5, 11.0), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.6))
from matplotlib.lines import Line2D  # noqa: E402
h = legend_handles(types)
for hh in h:
    if hh.get_label() == "frame":
        hh.set_label("Y-frame")
h.append(Line2D([], [], color="#8E6BBF", lw=0.8, ls=(0, (2, 2)), label="aux. spiral (recycled)"))
ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
ax.set_xlabel("x (cm)")
ax.set_ylabel("y (cm)")
save(fig, os.path.join(FIGDIR, "fap_web_final"))

# ---------------------------------------------------------------- 4-panel grid
panels = [
    ("(a) original HTN", htn["threads"], {k: tuple(v) for k, v in htn["coords"].items()}, "htn",
     f"{htn['plan_length']} actions, {htn['energy_state']:.1f} cm"),
    ("(b) updated HTN", upd["threads"], {k: tuple(v) for k, v in upd["coords"].items()}, "htn",
     f"{upd['plan_length']} actions, {upd['energy_state']:.1f} cm"),
    ("(c) A* (committed plan)", ast_threads, ast_coords, "htn",
     f"{ast['total_steps']} actions, {ast['total_energy']:.1f} cm"),
    ("(d) FAP", fap["threads"], fc, "fap",
     f"{fap['plan_length']} actions, {fap['energy_state']:.1f} cm"),
]
fig, axs = plt.subplots(2, 2, figsize=(6.2, 7.0))
axs = axs.ravel()
alltypes = set()
for ax, (name, th, co, rig, sub) in zip(axs, panels):
    alltypes |= draw_web(ax, th, co, rig=rig, fontsize=6.5, off=0.25,
                         removed=fap["recycled"] if rig == "fap" else ())
    ax.text(0.5, 1.02, name + ": " + sub, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=8.5)
    ax.set_xlabel("x (cm)", fontsize=8)
    ax.set_ylabel("y (cm)", fontsize=8)
hl = legend_handles(alltypes)
for hh in hl:
    if hh.get_label() == "frame":
        hh.set_label("frame / Y-frame")
fig.legend(handles=hl, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, 0.0),
           handlelength=1.6, columnspacing=1.0)
fig.subplots_adjust(wspace=0.25, hspace=0.25, bottom=0.11, top=0.96)
save(fig, os.path.join(FIGDIR, "webs_four_planners"))

# ---------------------------------------------------------------- table numbers
for name, th, *_ in panels:
    c = Counter(TYPE_KEY.get(t[2], t[2]) for t in th)
    distinct_r = len({frozenset(t[:2]) for t in th if t[2] == "radius"})
    print(name, dict(c), "distinct radius edges:", distinct_r, "total threads:", len(th))
