"""HTN vs flat random-walker baseline: committed single-run comparison, our compare.py re-runs, per-seed
distributions, and the PYTHONHASHSEED dependence of 30-seed baseline summaries.

Sources: single_run_comparison.csv (repo root, committed 39b89f3);
work/core/derived/rerun61_compare_n300_hash0.json (compare.py re-run at 61d18d8, 300 seeds, 5000-step budget,
PYTHONHASHSEED=0); work/core/derived/rerun{39,61}_compare_n30_hash{0..9}.json (30 seeds each, 10 hash seeds).
"""
import glob
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import DERIVED, FIG, REPO
import plotstyle
from plotstyle import AGENT_COLORS as AC

plotstyle.apply()
src = pd.read_csv(os.path.join(REPO, "single_run_comparison.csv"))
v = {(g, m): val for g, m, val in src.itertuples(index=False)}
big = json.load(open(os.path.join(DERIVED, "rerun61_compare_n300_hash0.json")))
runs = [r for r in big["runs"] if r["success"]]
bE = np.array([r["energy"] for r in runs])
bS = np.array([r["steps_taken"] for r in runs])

# --- summary: log bars + hash-seed fragility ------------------------------------------------------------
fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"width_ratios": [1, 1.25]})
groups = [("single_run_comparison.csv\n(39b89f3)", v[("HTN (Group A)", "energy_cm")], v[("Baseline (Group B)", "energy_cm")],
           v[("HTN (Group A)", "actions")], v[("Baseline (Group B)", "actions")], None, None),
          ("re-run, 61d18d8\n(300 seeds)", big["htn"]["energy"], bE.mean(), big["htn"]["actions"], bS.mean(),
           bE.std(ddof=1), bS.std(ddof=1))]
x = np.arange(2)
w = 0.2
for i, (lab, hE, BE, hA, BA, sdE, sdA) in enumerate(groups):
    a.bar(i - 1.5 * w, hE, w, color=AC["HTN"], label="HTN energy (cm)" if i == 0 else None)
    a.bar(i - 0.5 * w, BE, w, color=AC["Baseline"], yerr=sdE, label="Baseline energy (cm)" if i == 0 else None)
    a.bar(i + 0.5 * w, hA, w, color=AC["HTN"], hatch="///", alpha=0.55, edgecolor=AC["HTN"],
          label="HTN actions" if i == 0 else None)
    a.bar(i + 1.5 * w, BA, w, color=AC["Baseline"], hatch="///", alpha=0.55, edgecolor=AC["Baseline"], yerr=sdA,
          label="Baseline steps" if i == 0 else None)
    for xx, val in zip((i - 1.5 * w, i - 0.5 * w, i + 0.5 * w, i + 1.5 * w), (hE, BE, hA, BA)):
        a.text(xx, val * 0.55, f"{val:.0f}", ha="center", va="top", fontsize=6.6, rotation=90, color="white")
a.set_yscale("log")
a.set_ylim(10, 4e4)
a.set_xticks(x)
a.set_xticklabels([g[0] for g in groups], fontsize=6.8)
a.set_ylabel("Value (log scale)")
a.legend(fontsize=6.2, loc="upper left", ncol=2)
a.grid(axis="x", visible=False)
a.set_title("(a) HTN vs baseline", fontsize=8.5, loc="left")

for k, (tag, col, off) in enumerate((("39", plotstyle.C["grey"], -0.12), ("61", AC["Baseline"], 0.12))):
    files = sorted(glob.glob(os.path.join(DERIVED, f"rerun{tag}_compare_n30_hash*.json")),
                   key=lambda f: int(f.split("hash")[1].split(".")[0]))
    for f in files:
        d = json.load(open(f))
        hsh = int(f.split("hash")[1].split(".")[0])
        b.errorbar(hsh + off, d["baseline_energy_mean_succ"], yerr=d["baseline_energy_sd_succ"], fmt="o", color=col,
                   ms=3.8, capsize=2, label=(f"compare.py @ {'39b89f3 (shipped config: anchor removal on)' if tag == '39' else '61d18d8 (deterministic config)'}"
                                              if hsh == 0 else None))
b.axhline(7492.3, color="black", lw=1.0, ls="--", label="Checkpoint 2 Table 5 value (7492.3)")
b.axhline(v[("Baseline (Group B)", "energy_cm")], color="black", lw=0.8, ls=":",
          label="single_run_comparison.csv (7711.4)")
b.set_xticks(range(10))
b.set_xlabel("PYTHONHASHSEED of the process")
b.set_ylabel("Baseline energy, 30 seeds (mean $\\pm$ SD, cm)")
b.set_ylim(0, 35000)
b.legend(fontsize=6.2, loc="upper left")
b.grid(axis="x", visible=False)
b.set_title("(b) same 30 walker seeds, different hash seeds", fontsize=8.5, loc="left")
fig.tight_layout(w_pad=1.0)
plotstyle.save(fig, f"{FIG}/compare_summary")

# --- per-seed distributions (re-run, 61d18d8) ------------------------------------------------------------
fig, (c, d) = plt.subplots(1, 2, figsize=(7.0, 2.7))
bins = np.logspace(np.log10(min(bE.min(), 600) * 0.9), np.log10(bE.max() * 1.1), 30)
c.hist(bE, bins=bins, color=AC["Baseline"], alpha=0.8, label=f"baseline, {len(bE)} successful of {big['n_seeds']} seeds")
c.axvline(big["htn"]["energy"], color=AC["HTN"], lw=1.6, label=f"HTN ({big['htn']['energy']:.1f} cm, deterministic)")
c.axvline(np.median(bE), color="black", lw=0.9, ls="--", label=f"baseline median {np.median(bE):.0f} cm")
c.set_xscale("log")
c.set_xlabel("Locomotory energy (cm, log scale)")
c.set_ylabel("Runs")
c.set_ylim(0, c.get_ylim()[1] * 1.35)
c.legend(fontsize=6.3, loc="upper right", frameon=True, facecolor="white", edgecolor="none", framealpha=1)
bins = np.logspace(np.log10(90), np.log10(bS.max() * 1.1), 30)
d.hist(bS, bins=bins, color=AC["Baseline"], alpha=0.8, label="baseline action attempts")
d.axvline(big["htn"]["actions"], color=AC["HTN"], lw=1.6, label=f"HTN plan length ({big['htn']['actions']})")
d.axvline(np.median(bS), color="black", lw=0.9, ls="--", label=f"baseline median {np.median(bS):.0f}")
d.set_xscale("log")
d.set_xlabel("Actions / steps per run (log scale)")
d.set_ylabel("Runs")
d.set_ylim(0, d.get_ylim()[1] * 1.35)
d.legend(fontsize=6.3, loc="upper right", frameon=True, facecolor="white", edgecolor="none", framealpha=1)
fig.tight_layout(w_pad=1.2)
plotstyle.save(fig, f"{FIG}/compare_distributions")

ratio = bE / big["htn"]["energy"]
print("n succ", len(bE), "of", big["n_seeds"], "mean", bE.mean(), "sd", bE.std(ddof=1), "median", np.median(bE),
      "min", bE.min(), "max", bE.max(), "steps mean", bS.mean(), "median", np.median(bS), "min", bS.min(),
      "ratio min", ratio.min(), "frac runs with E<HTN", (bE < big["htn"]["energy"]).mean(),
      "baseline eta?", None)
print("radii laid by baseline (succ):", sorted(set(r["radii_count"] for r in runs))[:5],
      "aux segments min/median:", min(r["n_aux_segments"] for r in runs), np.median([r["n_aux_segments"] for r in runs]),
      "cap segments min/median:", min(r["n_cap_segments"] for r in runs), np.median([r["n_cap_segments"] for r in runs]),
      "runs with 0 spiral segments:", sum(1 for r in runs if r["n_aux_segments"] == 0 and r["n_cap_segments"] == 0))
