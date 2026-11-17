#!/usr/bin/env python3
"""fig_astar_web.py -- the committed A* plan (visualization/plan_data_astar.js) drawn as a web.

Outputs: astar_web_final (single panel) and astar_web_buildup (4 panels, state after each phase).
The plan is replayed through the repo's own primitive operators (spider_web_htn.operators, private
clone) to obtain the thread list; nothing is re-planned here.
"""
import contextlib
import io
import os
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CLONE, FIGDIR, REPO, draw_web, legend_handles, load_js  # noqa: E402
from plotstyle import FIG_SQUARE, FIG_WIDE, apply, save  # noqa: E402

sys.path.insert(0, CLONE)
with contextlib.redirect_stdout(io.StringIO()):
    from spider_web_htn import operators as ops
    from spider_web_htn.state import create_initial_state

apply()
data = load_js(os.path.join(REPO, "visualization/plan_data_astar.js"))
coords = {k: tuple(v) for k, v in data["node_coords"].items()}
s = create_initial_state()
states = [list(s.threads)]
for st in data["steps"]:
    a = st["action"]
    r = getattr(ops, a[0])(s, *a[1:])
    assert r is not False, a
    s = r
    states.append(list(s.threads))
print("final threads", len(s.threads), "steps", len(data["steps"]), "energy", data["total_energy"])

# single panel
fig, ax = plt.subplots(figsize=FIG_SQUARE)
types = draw_web(ax, states[-1], coords)
hub = coords["right_stick_top"]
ax.plot(*hub, marker="o", ms=7, mfc="none", mec="k", mew=1.0, zorder=6)
ax.annotate("proto-hub = right_stick_top", hub, xytext=(12.0, 19.2), fontsize=8,
            arrowprops=dict(arrowstyle="->", lw=0.6), ha="center", va="center")
ins = ax.inset_axes([0.47, 0.50, 0.30, 0.30])
draw_web(ins, states[-1], coords, lim=False, fontsize=6, off=0.12)
ins.set_xlim(14.4, 16.9)
ins.set_ylim(14.4, 18.6)
ins.set_xticks([15, 16])
ins.set_yticks([15, 18])
ins.tick_params(labelsize=6)
ax.indicate_inset_zoom(ins, edgecolor="#555555", lw=0.6)
ax.set_xlabel("x (cm)")
ax.set_ylabel("y (cm)")
ax.legend(handles=legend_handles(types), loc="center", bbox_to_anchor=(0.5, 0.27), fontsize=8)
save(fig, os.path.join(FIGDIR, "astar_web_final"))

# build-up strip
cuts = [(9, "after step 9: proto-hub"), (17, "after step 17: radii + frame"),
        (21, "after step 21: auxiliary spiral"), (26, "after step 26: complete")]
fig, axs = plt.subplots(1, 4, figsize=(7.0, 2.75), sharey=True)
alltypes = set()
for ax, (k, lab) in zip(axs, cuts):
    alltypes |= draw_web(ax, states[k], coords, fontsize=6.5)
    ax.set_xlabel("x (cm)", fontsize=8)
    ax.tick_params(labelsize=7.5)
    ax.text(0.5, 1.02, f"{lab}\n{data['steps'][k - 1]['cumulative_energy']:.1f} cm",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=7.8)
axs[0].set_ylabel("y (cm)", fontsize=8)
fig.legend(handles=legend_handles(alltypes), loc="lower center", ncol=5, fontsize=8,
           bbox_to_anchor=(0.5, 0.02))
fig.subplots_adjust(wspace=0.08, bottom=0.27)
save(fig, os.path.join(FIGDIR, "astar_web_buildup"))
