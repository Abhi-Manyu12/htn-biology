#!/usr/bin/env python3
"""fig_astar_search.py -- A* search behaviour, from W/work/astar_fap/data/runs.jsonl.

astar_search_path : (a) g, h, f along the returned plan and the plan's remaining cost;
                    (b) f-value of each popped heap entry vs pop index, 1e1bd44 vs 61d18d8.
astar_scaling     : (a) states expanded vs goal size k (min_radii = min_capture_spiral = k);
                    (b) states expanded and plan cost vs heuristic weight.
Code versions: '1e1bd44' = A* as committed 2026-08-30; '61d18d8' = same A* files at HEAD (h == 0);
'61d18d8 + h-fix' = HEAD with our one-line repair of the heuristic's distance call (not repo code).
"""
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FIGDIR, by_tag, load_runs  # noqa: E402
from plotstyle import C, FIG_2PANEL, apply, save  # noqa: E402

apply()
recs = load_runs()
VER = {"old": ("1e1bd44 (as committed)", C["green"], "o"),
       "head": ("61d18d8 (HEAD, $h \\equiv 0$)", C["vermillion"], "s"),
       "hfix": ("61d18d8 + h-fix (ours)", C["blue"], "^")}

# ---------------------------------------------------------------- path + trace
tr = by_tag(recs, "astar_old_trace")[0]
hd = by_tag(recs, "astar_head_default")[0]
path = tr["path"]
w = tr["weight"]
i = np.arange(len(path))
g = np.array([p["g"] for p in path])
h = np.array([p["h"] for p in path])
total = g[-1]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.5))
a1.plot(i, g, color=C["black"], label="$g$ (cost so far)")
a1.plot(i, total - g, color=C["grey"], ls="--", label="remaining plan cost")
a1.plot(i, h, color=C["blue"], label="$h$")
a1.plot(i, g + w * h, color=C["orange"], label=f"$f=g+{w:g}h$")
a1.set_xlabel("state index along returned plan")
a1.set_ylabel("cost (cm)")
a1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=8)
a1.text(-0.02, 1.02, "(a)", transform=a1.transAxes, va="bottom", fontweight="bold")

for rec, key in [(tr, "old"), (hd, "head")]:
    t = np.array(rec["trace"])
    lab, col, _ = VER[key]
    a2.plot(t[:, 1], t[:, 3], ".", ms=1.2, color=col, alpha=0.5, rasterized=True)
    a2.plot([], [], ".", ms=6, color=col,
            label=f"{lab}: {'plan, ' if rec['success'] else 'no plan, '}"
                  f"{rec['nodes_expanded']:,} exp. in {rec['wall_time_raw']:.1f} s")
a2.set_xscale("log")
a2.set_xlabel("heap pops (incl. stale entries)")
a2.set_ylabel("$f$ of popped entry (cm)")
a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1, fontsize=8)
a2.text(-0.02, 1.02, "(b)", transform=a2.transAxes, va="bottom", fontweight="bold")
fig.tight_layout()
save(fig, os.path.join(FIGDIR, "astar_search_path"))

# ---------------------------------------------------------------- scaling
fig, (b1, b2) = plt.subplots(1, 2, figsize=(7.0, 3.5))
for key, tag in [("old", "astar_old_k"), ("hfix", "astar_hfix_k"), ("head", "astar_head_k")]:
    rs = sorted(by_tag(recs, tag), key=lambda r: r["k"])
    lab, col, m = VER[key]
    k = [r["k"] for r in rs]
    n = [r["nodes_expanded"] for r in rs]
    b1.plot(k, n, color=col, lw=1.0, alpha=0.6)
    for r in rs:
        b1.plot(r["k"], r["nodes_expanded"], m, color=col, mfc=col if r["success"] else "white", mew=1.0)
    b1.plot([], [], m, color=col, label=lab)
b1.plot([], [], "o", color="k", mfc="white", label="open marker: no plan in budget")
b1.set_yscale("log")
b1.set_xticks(range(1, 9))
b1.set_xlabel("goal size $k$ (radii = capture segments = $k$)")
b1.set_ylabel("states expanded")
b1.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
b1.text(-0.02, 1.02, "(a)", transform=b1.transAxes, va="bottom", fontweight="bold")

for key, tag in [("old", "astar_old_weight"), ("hfix", "astar_hfix_weight")]:
    rs = sorted(by_tag(recs, tag), key=lambda r: r["weight"])
    lab, col, m = VER[key]
    ws = [r["weight"] for r in rs]
    b2.plot(ws, [r["nodes_expanded"] for r in rs], color=col, lw=1.0, alpha=0.6)
    for r in rs:
        b2.plot(r["weight"], r["nodes_expanded"], m, color=col, mfc=col if r["success"] else "white", mew=1.0)
        if r["success"]:
            b2.annotate(f"plan: {r['plan_length']} actions,\n{r['energy_raw']:.2f} cm, {r['wall_time_raw']:.2f} s",
                        (r["weight"], r["nodes_expanded"]), xytext=(3.4, 2500), fontsize=7.5,
                        arrowprops=dict(arrowstyle="->", lw=0.6))
    b2.plot([], [], m, color=col, label=lab)
b2.plot([], [], "o", color="k", mfc="white", label="open marker: no plan in budget")
b2.set_xscale("log")
b2.set_yscale("log")
b2.set_xticks([1, 1.5, 2, 3, 5, 10])
b2.set_xticklabels(["1", "1.5", "2", "3", "5", "10"])
b2.set_xlabel("heuristic weight $w$ in $f=g+wh$")
b2.set_ylabel("states expanded")
b2.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
b2.text(-0.02, 1.02, "(b)", transform=b2.transAxes, va="bottom", fontweight="bold")
fig.tight_layout()
save(fig, os.path.join(FIGDIR, "astar_scaling"))
