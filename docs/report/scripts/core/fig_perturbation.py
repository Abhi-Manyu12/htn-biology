"""perturbation_trials.csv (restored historical, unaudited output; claim C28) plus our default-settings re-run.

Sources: perturbation_trials.csv (repo root, restored in 61d18d8, n=200 per group per perturbation);
work/core/derived/rerun61_perturbation_trials.csv (python -m spider_web_htn_updated.perturbations --n-runs 200,
private clone at 61d18d8; software re-run, not an audit).
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DERIVED, FIG, REPO, wilson
import plotstyle
from plotstyle import AGENT_COLORS as AC

plotstyle.apply()
hist = pd.read_csv(os.path.join(REPO, "perturbation_trials.csv"))
rer = pd.read_csv(os.path.join(DERIVED, "rerun61_perturbation_trials.csv"))
P = ["resource_depletion", "structural_failure", "predator"]
PL = ["resource\ndepletion", "structural\nfailure", "predator"]
G = {"htn": ("HTN", AC["HTN"], -0.17), "baseline": ("Baseline", AC["Baseline"], 0.17)}

fig, (a, b, c) = plt.subplots(1, 3, figsize=(7.0, 2.8))
x = np.arange(3)
for g, (lab, col, off) in G.items():
    for df, filled, tag in ((hist, True, "restored CSV"), (rer, False, "our re-run")):
        d = df[df.group == g].set_index("perturbation").loc[P]
        lo, hi = zip(*[wilson(k, n) for k, n in zip(d.successes, d.triggered)])
        y = d.success_rate.values
        dx = off + (0 if filled else 0.07)
        kw = dict(color=col, ms=4.5, mfc=col if filled else "white", ls="none", marker="o" if g == "htn" else "s")
        a.errorbar(x + dx, y, yerr=[np.maximum(0, y - np.array(lo)), np.maximum(0, np.array(hi) - y)],
                   label=f"{lab}, {tag}", **kw)
        b.plot(x + dx, d.energy_mean.values, **kw)
        sd = d.adaptation_time_stdev.values.astype(float)
        c.errorbar(x + dx, d.adaptation_time_mean.values.astype(float), yerr=sd, **kw)
for ax in (a, b, c):
    ax.set_xticks(x)
    ax.set_xticklabels(PL, fontsize=7)
    ax.grid(axis="x", visible=False)
    ax.set_xlim(-0.6, 2.6)
a.set_ylabel("Success rate (of triggered; 95% Wilson CI)")
a.set_ylim(0, 1.08)
a.legend(fontsize=5.9, loc="center", bbox_to_anchor=(0.5, 0.55))
b.set_ylabel("Mean energy of successful runs (cm)")
b.set_ylim(0, 2300)
b.axhline(2200, color="black", lw=0.8, ls="--")
b.text(2.55, 2150, "silk_capacity_initial = 2200 cm", ha="right", va="top", fontsize=6.2)
c.set_ylabel("Adaptation time $T_a$ (mean $\\pm$ SD)")
c.axhline(0, color="black", lw=0.6)
c.set_ylim(-40, 470)
for ax, yy in ((a, 0.02), (b, 0.02), (c, 0.97)):
    ax.text(0.98, yy, "historical / unaudited (C28)", transform=ax.transAxes, ha="right", va="bottom" if yy < 0.5 else "top",
            fontsize=6, color="#888888", style="italic")
fig.tight_layout(w_pad=1.0)
plotstyle.save(fig, f"{FIG}/perturbation_trials_historical")
