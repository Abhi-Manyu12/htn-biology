"""Wind-noise sweep: every metric in wind_sensitivity.csv vs wind sigma, both groups.

Source: wind_sensitivity.csv (repo root, committed 39b89f3; removal_prob = 0, n = 1000 per group per sigma).
The dotted curve in panel (b) is the analytic expectation of the clamped multiplier max(1 + N(0, sigma), 0.1)
(stochastic.wind_noise_factor) times the wind-free HTN energy; it is computed here, not taken from the repo.
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from _common import FIG, REPO, wilson
import plotstyle
from plotstyle import AGENT_COLORS as AC

plotstyle.apply()
df = pd.read_csv(os.path.join(REPO, "wind_sensitivity.csv"))
h = df[df.group == "htn"]
b = df[df.group == "baseline"]

fig, ax = plt.subplots(2, 2, figsize=(7.0, 4.9))
(a, bb), (c, d) = ax
for g, col, m, lab in ((h, AC["HTN"], "o", "HTN (Group A)"), (b, AC["Baseline"], "s", "Baseline (Group B)")):
    lo, hi = zip(*[wilson(k, n) for k, n in zip(g.successes, g.n_runs)])
    y = g.success_rate.values
    a.errorbar(g.wind_std, y, yerr=[np.maximum(0, y - np.array(lo)), np.maximum(0, np.array(hi) - y)], marker=m,
               color=col, ms=4, label=lab)
    c.plot(g.wind_std, g.energy_stdev, marker=m, color=col, ms=4, label=lab)
a.set_ylim(0.94, 1.005)
a.set_ylabel("Success rate (95% Wilson CI)")
a.legend(fontsize=6.8, loc="center", bbox_to_anchor=(0.5, 0.6), ncol=2)
a.set_title("(a) success rate", fontsize=8.5, loc="left")

E0 = h.energy_mean.iloc[0]
s = np.linspace(1e-4, 0.5, 200)
al = (0.1 - 1) / s
mult = 0.1 * norm.cdf(al) + (1 - norm.cdf(al)) + s * norm.pdf(al)
bb.fill_between(h.wind_std, h.energy_mean - h.energy_stdev, h.energy_mean + h.energy_stdev, color=AC["HTN"],
                alpha=0.15, lw=0, label="mean $\\pm$ SD")
bb.plot(h.wind_std, h.energy_mean, "o-", color=AC["HTN"], ms=4, label="mean")
bb.plot(h.wind_std, h.energy_median, "--", color=AC["HTN"], lw=1, label="median")
bb.plot(s, E0 * mult, ":", color="black", lw=1.1, label=r"$E_0\,\mathbb{E}[\max(1+\varepsilon,0.1)]$ (analytic)")
bb.set_ylabel("HTN energy (cm)")
bb.set_ylim(550, 660)
bb.legend(fontsize=6.5, loc="upper left")
bb.set_title("(b) HTN energy", fontsize=8.5, loc="left")

c.set_ylabel("SD of energy (cm)")
c.set_yscale("log")
c.set_title("(c) dispersion of energy (log scale)", fontsize=8.5, loc="left")
c.legend(fontsize=6.8, loc="center right")

d.plot(b.wind_std, b.energy_mean, "s-", color=AC["Baseline"], ms=4, label="mean")
d.plot(b.wind_std, b.energy_median, "s--", mfc="white", color=AC["Baseline"], ms=4, label="median")
d.set_ylabel("Baseline energy (cm)")
d.set_ylim(6000, 8600)
d.legend(fontsize=6.8, loc="center right")
d.set_title("(d) baseline energy (successful runs)", fontsize=8.5, loc="left")
for x in (a, bb, c, d):
    x.set_xlabel(r"Wind noise $\sigma$ (relative SD of each step cost)")
fig.tight_layout(h_pad=1.2, w_pad=1.2)
plotstyle.save(fig, f"{FIG}/wind_sensitivity")
print("HTN SD/sigma:", (h.energy_stdev / h.wind_std).round(2).tolist())
print("analytic at 0.5:", E0 * (0.1 * norm.cdf(-1.8) + 1 - norm.cdf(-1.8) + 0.5 * norm.pdf(-1.8)), "obs", h.energy_mean.iloc[-1])
