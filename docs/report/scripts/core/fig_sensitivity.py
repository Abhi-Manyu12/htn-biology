"""Anchor-removal sensitivity (sensitivity_comparison.csv) and our audit of what an HTN 'success' contains.

Sources: sensitivity_comparison.csv (repo root, committed 39b89f3, n=1000 per group per p);
work/core/derived/htn_success_audit_39b89f3.json (rerun_htn_success_audit.py, our re-run at 39b89f3, same seeds).
"""
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DERIVED, FIG, REPO, wilson
import plotstyle
from plotstyle import AGENT_COLORS as AC

plotstyle.apply()
df = pd.read_csv(os.path.join(REPO, "sensitivity_comparison.csv"))
audit = json.load(open(os.path.join(DERIVED, "htn_success_audit_39b89f3.json")))["rows"]
G = {"htn": ("HTN (Group A)", AC["HTN"], "o"), "baseline": ("Baseline (Group B)", AC["Baseline"], "s")}

# --- success rate ------------------------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
for g, (lab, col, m) in G.items():
    d = df[df.group == g]
    lo, hi = zip(*[wilson(k, n) for k, n in zip(d.successes, d.n_runs)])
    y = d.success_rate.values
    a1.errorbar(d.removal_prob, y, yerr=[np.maximum(0, y - np.array(lo)), np.maximum(0, np.array(hi) - y)], marker=m, color=col, label=lab,
                ms=4, lw=1.2)
pp = np.linspace(0, 0.8, 200)
a1.plot(pp, 1 - pp ** 8, color=AC["HTN"], ls=":", lw=1.0, label=r"$1-p^{8}$ (all 8 anchors lost)")
a1.axvspan(0.5, 0.82, color="#EEEEEE", zorder=0, lw=0)
a1.text(0.65, 0.835, "beyond the\nCheckpoint 2\nTable 6 range", ha="center", fontsize=6.5, color="#555555")
a1.set_xlabel("Anchor-removal probability $p$")
a1.set_ylabel("Success rate (95% Wilson CI)")
a1.set_ylim(0.8, 1.012)
a1.set_xlim(-0.02, 0.82)
a1.legend(fontsize=6.6, loc="lower left")

ps = [r["p"] for r in audit]
n = np.array([r["n"] for r in audit])
succ = np.array([r["greedy_success"] for r in audit])
struct = np.array([r["struct_complete"] for r in audit])
mean_radii = [sum(int(k) * v for k, v in r["radii_hist"].items()) / max(1, sum(r["radii_hist"].values())) for r in audit]
a2.plot(ps, succ / n, "o-", color=AC["HTN"], ms=4, label="HTN: plan returned (counted as success)")
lo, hi = zip(*[wilson(k, nn) for k, nn in zip(struct, n)])
a2.errorbar(ps, struct / n, yerr=[np.maximum(0, struct / n - np.array(lo)), np.maximum(0, np.array(hi) - struct / n)], fmt="o--", mfc="white",
            color=AC["HTN"], ms=4, label="HTN: plan builds all 8 radii\n(passes baseline's is_web_complete)")
a2.set_xlabel("Anchor-removal probability $p$")
a2.set_ylabel("Fraction of $n=1000$ trials")
a2.set_ylim(-0.03, 1.05)
ax3 = a2.twinx()
ax3.plot(ps, mean_radii, "^-", color=plotstyle.C["grey"], ms=3.5, lw=1.0)
ax3.set_ylabel("Mean radii laid (successful HTN plans)", color=plotstyle.C["grey"], fontsize=7.5)
ax3.set_ylim(0, 8.4)
ax3.spines["right"].set_visible(True)
ax3.grid(False)
ax3.tick_params(axis="y", colors=plotstyle.C["grey"])
a2.legend(fontsize=6.4, loc="upper right", bbox_to_anchor=(1.0, 0.925))
fig.tight_layout(w_pad=1.0)
plotstyle.save(fig, f"{FIG}/sens_anchor_success")

# --- energy ---------------------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.6), gridspec_kw={"width_ratios": [1, 1, 0.8]})
for ax, g in zip(axs[:2], ("htn", "baseline")):
    lab, col, m = G[g]
    d = df[df.group == g]
    ax.fill_between(d.removal_prob, d.energy_mean - d.energy_stdev, d.energy_mean + d.energy_stdev, color=col,
                    alpha=0.18, lw=0, label="mean $\\pm$ SD")
    ax.plot(d.removal_prob, d.energy_mean, marker=m, color=col, ms=3.8, label="mean")
    ax.plot(d.removal_prob, d.energy_median, ls="--", color=col, lw=1.0, label="median")
    ax.set_title(lab, fontsize=8.5)
    ax.set_xlabel("Anchor-removal probability $p$")
    ax.set_ylim(bottom=0)
axs[0].set_ylabel("Energy of successful runs (cm)")
axs[0].legend(fontsize=6.5, loc="lower left")
h = df[df.group == "htn"].set_index("removal_prob")
b = df[df.group == "baseline"].set_index("removal_prob")
axs[2].plot(h.index, b.energy_mean / h.energy_mean, "o-", color="black", ms=3.5, label="ratio of means")
axs[2].plot(h.index, b.energy_median / h.energy_median, "o--", mfc="white", color="black", ms=3.5,
            label="ratio of medians")
axs[2].set_ylim(0, 16)
axs[2].set_xlabel("Anchor-removal probability $p$")
axs[2].set_ylabel("Baseline / HTN energy")
axs[2].legend(fontsize=6.5, loc="lower right")
fig.tight_layout(w_pad=0.8)
plotstyle.save(fig, f"{FIG}/sens_anchor_energy")
print((b.energy_mean / h.energy_mean).round(2).to_dict())
print((b.energy_median / h.energy_median).round(2).to_dict())
print(list(zip(ps, succ, struct, [round(x, 2) for x in mean_radii])))
