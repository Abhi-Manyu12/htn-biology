"""Recovery v1 (sector-construction benchmark) result figures.

Source: mulder_results/recovery_v1_verified/{trials.csv,paired.json} (2,240 trials; the same data are
curated in docs/research/evidence/recovery_v1_summary.json). recovery_v1/ is an earlier execution of the same
study; all its non-timing fields are identical (checked in check_recovery_runs.py).

Outputs: rec_outcome_matrix, rec_planning_effort, rec_paired_effort, rec_execution_outcomes
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _common import BACKENDS, OUT, REC, SCENARIOS, SCEN_LABEL, plotstyle, wilson

BC = plotstyle.BACKEND_COLORS
SHORT = {"fresh_root": "fresh_root", "component": "component", "ipyhop_fresh": "ipyhop_fresh",
         "ipyhop": "ipyhop\n(retained)"}


def load():
    t = pd.read_csv(REC / "trials.csv")
    cfg = t["config"].apply(json.loads)
    t["sectors"], t["depth"], t["amp"] = cfg.str["sectors"], cfg.str["depth"], cfg.str["amplitude_cm"]
    return t


def outcome_matrix(t):
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.3), gridspec_kw=dict(wspace=0.06, width_ratios=[1.55, 1, 1]))
    g = t.groupby(["scenario", "backend"])
    panels = [("success", "completed / trials\n(Wilson 95% CI)"), ("repairs", "mean re-planning calls"),
              ("stale_preconditions", "mean stale-precondition\ndetections")]
    for ax, (col, title) in zip(axes, panels):
        M = np.array([[g.get_group((s, b))[col].mean() for b in BACKENDS] for s in SCENARIOS], float)
        cmap = "Blues" if col == "success" else "Oranges"
        vmax = 1 if col == "success" else max(4, M.max())
        ax.imshow(M, cmap=cmap, vmin=0, vmax=vmax * 1.35, aspect="auto")
        for i, s in enumerate(SCENARIOS):
            for j, b in enumerate(BACKENDS):
                grp = g.get_group((s, b))
                if col == "success":
                    k, n = int(grp.success.sum()), len(grp)
                    lo, hi = wilson(k, n)
                    txt = f"{k}/{n}\n{lo:.2f}\u2013{hi:.2f}"
                else:
                    sd = grp[col].std()
                    txt = f"{grp[col].mean():.0f}" if sd == 0 else f"{grp[col].mean():.2f}"
                white = col == "success" and grp.success.mean() > 0.5
                ax.text(j, i, txt, ha="center", va="center", fontsize=7.2 if col == "success" else 8,
                        color="white" if white else "black")
        ax.set_xticks(range(4), [SHORT[b] for b in BACKENDS], rotation=40, ha="right", fontsize=6.8)
        ax.set_yticks(range(len(SCENARIOS)), [SCEN_LABEL[s] for s in SCENARIOS] if ax is axes[0] else [])
        ax.set_title(title, fontsize=8)
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    plotstyle.save(fig, str(OUT / "rec_outcome_matrix"))


def grouped(ax, t, col, scale=1.0, ylabel="", scen=SCENARIOS, legend=False):
    width = 0.2
    x = np.arange(len(scen))
    for j, b in enumerate(BACKENDS):
        means, sds = [], []
        for s in scen:
            v = t[(t.scenario == s) & (t.backend == b)][col] * scale
            means.append(v.mean())
            sd = v.std(ddof=1)
            sds.append(sd if sd > 1e-12 else np.nan)   # no bar for zero spread
        ax.bar(x + (j - 1.5) * width, means, width, yerr=sds, color=BC[b], label=SHORT[b].replace("\n", " "),
               error_kw=dict(lw=0.6, capsize=1.2, ecolor="#444"), edgecolor="white", lw=0.3)
    ax.set_xticks(x, [SCEN_LABEL[s] for s in scen], rotation=30, ha="right", fontsize=7)
    ax.set_ylabel(ylabel)
    if legend:
        ax.legend(ncol=4, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0), handlelength=1.2)


def planning_effort(p):
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw=dict(wspace=0.28))
    grouped(axes[0], p, "method_calls", ylabel="method calls per trial")
    grouped(axes[1], p, "planning_wall_s", 1000, ylabel="planning wall time per trial (ms)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 0.96), fontsize=7.5)
    plotstyle.save(fig, str(OUT / "rec_planning_effort"))


def paired_effort():
    p = pd.read_json(REC / "paired.json")
    strata = [(4, 0), (4, 2), (8, 0), (8, 2)]
    scol = {(4, 0): plotstyle.C["sky"], (4, 2): plotstyle.C["blue"], (8, 0): plotstyle.C["orange"],
            (8, 2): plotstyle.C["vermillion"]}
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.3), gridspec_kw=dict(wspace=0.12))
    metrics = [("method_calls", 1, "method calls"), ("ipyhop_iterations", 1, "IPyHOP iterations"),
               ("planning_wall_s", 1000, "planning wall time (ms)")]
    for ax, (m, sc, lab) in zip(axes, metrics):
        q = p[p.metric == m]
        for i, s in enumerate(SCENARIOS):
            k = 0
            for (n, d) in strata:
                for amp, mk in ((0, "o"), (10, "^")):
                    r = q[(q.scenario == s) & (q.sectors == n) & (q.depth == d) & (q.amplitude_cm == amp)].iloc[0]
                    y = i + (k - 3.5) * 0.085
                    lo, hi = r.ci95
                    ax.plot([lo * sc, hi * sc], [y, y], color=scol[(n, d)], lw=0.9)
                    ax.plot(r.mean_difference * sc, y, mk, color=scol[(n, d)], ms=3.2,
                            mfc=scol[(n, d)] if amp else "white")
                    k += 1
        ax.axvline(0, color="black", lw=0.7)
        ax.set_yticks(range(len(SCENARIOS)), [SCEN_LABEL[s] for s in SCENARIOS] if ax is axes[0] else [])
        ax.invert_yaxis()
        ax.set_xlabel(f"retained $-$ fresh IPyHOP\n{lab}")
        ax.grid(axis="y", visible=False)
        if m == "planning_wall_s":
            ax.set_xlim(-10, 6)
            ax.text(0.02, 0.005, "CIs clipped at axis limits", transform=ax.transAxes, fontsize=6, color="#555")
        ax.text(0.02, 1.01, "retained cheaper", transform=ax.transAxes, fontsize=6.5, color="#555", ha="left")
        ax.text(0.98, 1.01, "retained costlier", transform=ax.transAxes, fontsize=6.5, color="#555", ha="right")
    from matplotlib.lines import Line2D
    hs = [Line2D([], [], color=scol[k], marker="s", ls="", ms=5, label=f"{k[0]} sectors, depth {k[1]}")
          for k in strata]
    hs += [Line2D([], [], color="k", marker="o", mfc="white", ls="", ms=4, label="stationary (0 cm)"),
           Line2D([], [], color="k", marker="^", ls="", ms=4, label="moving (10 cm)")]
    fig.legend(handles=hs, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.17), fontsize=6.6,
               handletextpad=0.2, columnspacing=0.8)
    plotstyle.save(fig, str(OUT / "rec_paired_effort"))


def execution_outcomes(p):
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.7), gridspec_kw=dict(wspace=0.38, hspace=0.62))
    panels = [("travel_cm", 1, "physical travel (cm)"), ("silk_used_cm", 1, "silk used (cm)"),
              ("elapsed_s", 1, "simulated elapsed time (s)"), ("repairs", 1, "re-planning calls"),
              ("stale_preconditions", 1, "stale-precondition\ndetections"),
              ("recovery_retraced_cm", 1, "retraced during\nrecovery (cm)")]
    for ax, (c, s, lab) in zip(axes.flat, panels):
        grouped(ax, p, c, s, lab)
        ax.tick_params(axis="x", labelsize=6.3)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 0.97), fontsize=7.5)
    plotstyle.save(fig, str(OUT / "rec_execution_outcomes"))


if __name__ == "__main__":
    plotstyle.apply()
    t = load()
    outcome_matrix(t)
    primary = t[(t.sectors == 8) & (t.depth == 2) & (t.amp == 10)]
    assert primary.groupby(["scenario", "backend"]).size().eq(10).all()
    planning_effort(primary)
    paired_effort()
    execution_outcomes(primary)
