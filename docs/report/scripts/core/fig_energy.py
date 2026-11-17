"""Cumulative locomotory energy vs action index (phase-shaded) and per-phase action/energy bars.

Sources: work/core/derived/plan_{checkpoint2_39b89f3,original_61d18d8,updated_61d18d8}.json (export_plan.py),
whose action sequences are asserted identical to the committed visualization/plan_data*.js.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from _common import (FIG, PHASE_COLOR, PHASE_KEYS, PHASE_LABEL, PLAN_STYLE, REPO, load_plan_js, phase_table,
                     plans_exact)
import plotstyle

plotstyle.apply()
P = plans_exact()
by = {k: p for _, k, p in P}

# consistency with the committed UI data
for key, js in (("orig", "plan_data.js"), ("upd", "plan_data_updated.js")):
    c = load_plan_js(os.path.join(REPO, "visualization", js))
    assert [s["action"] for s in c["steps"]] == [s["action"] for s in by[key]["steps"]], key
    assert abs(c["total_energy"] - by[key]["total_energy"]) < 0.06, key

# --- cumulative energy -----------------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"width_ratios": [1.15, 1]})
upd = by["upd"]["steps"]
x = np.arange(1, len(upd) + 1)
cum = np.array([s["cumulative_energy"] for s in upd])
start = 0
for i in range(1, len(upd) + 1):
    if i == len(upd) or upd[i]["phase"] != upd[start]["phase"]:
        ph = upd[start]["phase"]
        a1.axvspan(start + 0.5, i + 0.5, color=PHASE_COLOR[ph], alpha=0.28, lw=0)
        start = i
a1.step(x, cum, where="post", color="black", lw=1.2)
a1.plot(x, cum, ".", color="black", ms=2.2)
a1.set_xlim(0.5, len(upd) + 0.5)
a1.set_ylim(0, 740)
a1.set_xlabel(r"Action index $i$ in plan $\pi$ (updated package)")
a1.set_ylabel("Cumulative energy, Eq. (1) (cm)")
a1.grid(axis="x", visible=False)
from matplotlib.patches import Patch
a1.legend(handles=[Patch(color=PHASE_COLOR[k], alpha=0.5, label=PHASE_LABEL[k]) for k in PHASE_KEYS[:-1]],
          loc="upper left", fontsize=6.6, handlelength=1.0, borderaxespad=0.2)

for label, key, p in P:
    c = [0] + [s["cumulative_energy"] for s in p["steps"]]
    a2.plot(range(len(c)), c, label=f"{label.split(' (')[0]}: {p['total_steps']} actions, {p['total_energy']:.1f} cm",
            **PLAN_STYLE[key])
    # mark the start of the spiral phases
    i0 = next(i for i, s in enumerate(p["steps"]) if s["phase"] == "auxiliary_spiral")
    a2.plot(i0, c[i0], "o", color=PLAN_STYLE[key]["color"], ms=3.5)
a2.set_xlabel(r"Action index $i$")
a2.set_ylabel("Cumulative energy (cm)")
a2.legend(loc="lower right", fontsize=6.6)
a2.set_ylim(0, 790)
a2.annotate("spirals begin (dots)", xy=(52, 474), xytext=(8, 560), fontsize=6.8,
            arrowprops=dict(arrowstyle="->", lw=0.6))
fig.tight_layout(w_pad=1.2)
plotstyle.save(fig, f"{FIG}/energy_cumulative")

# --- per-phase bars --------------------------------------------------------------------------------------
fig, (b1, b2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
keys = PHASE_KEYS[:-1]
w = 0.27
xs = np.arange(len(keys))
for j, (label, key, p) in enumerate(P):
    t = phase_table(p)
    n = [t[k][0] for k in keys]
    e = [t[k][1] for k in keys]
    col = PLAN_STYLE[key]["color"]
    b1.bar(xs + (j - 1) * w, n, w, color=col, label=label.split(" (")[0])
    b2.bar(xs + (j - 1) * w, e, w, color=col, label=label.split(" (")[0])
    for xx, v in zip(xs + (j - 1) * w, n):
        b1.text(xx, v + 0.6, f"{v}", ha="center", va="bottom", fontsize=6.4)
    for xx, v in zip(xs + (j - 1) * w, e):
        b2.text(xx, v + 2, f"{v:.0f}", ha="center", va="bottom", fontsize=6.4, rotation=90)
short = ["Explor.", "Proto-hub", "Frame", "Radii", "Aux.\nspiral", "Capture\nspiral"]
for ax in (b1, b2):
    ax.set_xticks(xs)
    ax.set_xticklabels(short, fontsize=7)
    ax.grid(axis="x", visible=False)
b1.set_ylabel("Actions per phase")
b2.set_ylabel("Energy per phase (cm)")
b1.set_ylim(0, 48)
b2.set_ylim(0, 200)
b1.legend(fontsize=6.6, loc="upper left")
fig.tight_layout(w_pad=1.5)
plotstyle.save(fig, f"{FIG}/energy_per_phase")

for label, key, p in P:
    t = phase_table(p)
    print(key, p["total_steps"], round(p["total_energy"], 2),
          {k: (v[0], round(v[1], 2), round(100 * v[1] / p["total_energy"], 1)) for k, v in t.items()})
