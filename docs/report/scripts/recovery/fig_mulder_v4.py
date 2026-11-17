"""Mulder v4 (IPyHOP integrated into the Mulder construction HTN) figures.

Sources: mulder_results/mulder_reentrant_v4/{trials.csv,paired.json} (2,160 trials) and
docs/research/evidence/mulder_suffix_control.json (10 diagnostic GTPyhop whole-suffix trials).
Outputs: v4_completion, v4_pair_differences, v4_calls_vs_time, v4_lag_control
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _common import (EVID, OUT, POLICIES, PROFILES, PROFILE_LABEL, V4, V4_BACK, V4_BACK_COLOR, plotstyle,
                     wilson)

PC = plotstyle.POLICY_COLORS
BLAB = {"legacy": "legacy GTPyhop", "ipyhop_fresh": "fresh IPyHOP", "ipyhop_retained": "retained IPyHOP",
        "control": "GTPyhop whole-suffix\ncontrol"}
CTRL_COLOR = plotstyle.C["purple"]


def completion(t):
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 5.0), gridspec_kw=dict(hspace=0.55))
    for ax, size in zip(axes, ["small", "configured"]):
        M = np.zeros((len(PROFILES), 18))
        for i, pr in enumerate(PROFILES):
            for j, pol in enumerate(POLICIES):
                for k, b in enumerate(V4_BACK):
                    g = t[(t.complexity == size) & (t.profile == pr) & (t.controller == pol) & (t.planner_backend == b)]
                    assert len(g) == 10
                    M[i, 3 * j + k] = g.success.sum()
        ax.imshow(M, cmap="Blues", vmin=0, vmax=13, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, f"{int(M[i, j])}", ha="center", va="center", fontsize=6.5,
                        color="white" if M[i, j] > 7 else "black")
        for j in range(1, 6):
            ax.axvline(3 * j - 0.5, color="white", lw=2.5)
        ax.set_yticks(range(len(PROFILES)), [PROFILE_LABEL[p] for p in PROFILES], fontsize=7.5)
        ax.set_xticks(range(18), ["L", "F", "R"] * 6, fontsize=6.5)
        for j, pol in enumerate(POLICIES):
            ax.text(3 * j + 1, -0.85, pol, ha="center", va="bottom", fontsize=7.5, color="black")
        ax.grid(False)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        desc = "small (4 radii / 1 aux. / 1 capture turn)" if size == "small" else \
            "configured (16 radii / 3 aux. / 8 capture turns)"
        ax.set_title(f"{desc}: completed runs out of 10", fontsize=8.5, pad=20)
    fig.text(0.5, 0.005, "L = legacy GTPyhop component/root repair,  F = fresh IPyHOP,  R = retained IPyHOP",
             ha="center", fontsize=7.5)
    plotstyle.save(fig, str(OUT / "v4_completion"))


def pair_differences(t):
    k = ["controller", "seed", "complexity", "profile"]
    r = t[t.planner_backend == "ipyhop_retained"].set_index(k).sort_index()
    f = t[t.planner_backend == "ipyhop_fresh"].set_index(k).sort_index()
    assert len(r) == len(f) == 720 and (r.index == f.index).all()
    pol = r.index.get_level_values("controller")
    rng = np.random.default_rng(1)
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.0), gridspec_kw=dict(width_ratios=[1.5, 1, 1], wspace=0.45))
    ax = axes[0]
    phys = [("success", "comple-\ntion"), ("completed_actions", "completed\nactions"), ("repairs", "repairs"),
            ("elapsed_s", "elapsed\ntime (s)"), ("travel_cm", "travel\n(cm)")]
    for i, (c, lab) in enumerate(phys):
        d = (r[c].astype(float) - f[c].astype(float)).to_numpy()
        x = i + rng.uniform(-0.3, 0.3, len(d))
        ax.scatter(x, d, s=3, c=[PC[p] for p in pol], alpha=0.6, lw=0)
        ax.text(i, 0.55, f"{int((d == 0).sum())}/{len(d)}\n= 0", ha="center", fontsize=7.2)
    ax.set_xticks(range(len(phys)), [p[1] for p in phys], fontsize=6.5, rotation=35, ha="right")
    ax.set_ylim(-1, 1)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_ylabel("retained $-$ fresh IPyHOP (per pair)")
    ax.set_title("physical outcomes (n = 720 pairs)", fontsize=8.5)
    for ax, c, sc, lab in ((axes[1], "method_calls", 1, "method calls"),
                           (axes[2], "planning_wall_s", 1, "planning wall time (s)")):
        d = (r[c] - f[c]).to_numpy() * sc
        x = np.array([POLICIES.index(p) for p in pol]) + rng.uniform(-0.3, 0.3, len(d))
        ax.scatter(x, d, s=3, c=[PC[p] for p in pol], alpha=0.7, lw=0)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xticks(range(6), POLICIES, rotation=50, ha="right", fontsize=6.5)
        ax.set_title(lab, fontsize=8.5)
        if c == "method_calls":
            ax.set_yscale("symlog", linthresh=10)
            ax.text(0.03, 0.97, f"{int((d < 0).sum())} pairs < 0\n{int((d == 0).sum())} pairs = 0\n{int((d > 0).sum())} pairs > 0",
                    transform=ax.transAxes, va="top", fontsize=7.2)
        else:
            ax.text(0.03, 0.97, f"{int((d > 0).sum())} of 720 pairs > 0", transform=ax.transAxes, va="top", fontsize=7.2)
    plotstyle.save(fig, str(OUT / "v4_pair_differences"))


def calls_vs_time(t):
    p = pd.read_json(V4 / "paired.json")
    p = p[p.contrast == "ipyhop_retained minus ipyhop_fresh"]
    fresh = t[t.planner_backend == "ipyhop_fresh"].groupby(["complexity", "profile", "controller"])[
        ["method_calls", "planning_wall_s"]].mean()
    rows = []
    for (cx, pr, ct), g in p.groupby(["complexity", "profile", "controller"]):
        mc = g[g.metric == "method_calls"].iloc[0]
        wt = g[g.metric == "planning_wall_s"].iloc[0]
        if mc.mean_difference == 0:
            continue
        fm, fw = fresh.loc[(cx, pr, ct)]
        rows.append(dict(cx=cx, pr=pr, ct=ct, x=100 * mc.mean_difference / fm,
                         xl=100 * mc.ci95[0] / fm, xh=100 * mc.ci95[1] / fm,
                         y=100 * wt.mean_difference / fw, yl=100 * wt.ci95[0] / fw, yh=100 * wt.ci95[1] / fw,
                         dc=mc.mean_difference, dw=wt.mean_difference))
    d = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    YMAX = 120
    for _, r in d.iterrows():
        if r.y > YMAX:   # one off-scale cell, labelled instead of plotted
            ax.annotate(f"{r.cx}, {r.pr}, {r.ct}:\n{r.x:+.2f}% calls, {r.y:+.0f}% time\n(95% CI {r.yl:+.0f} to {r.yh:+.0f}%)",
                        xy=(r.x, YMAX), xytext=(r.x - 0.3, YMAX - 8), ha="right", va="top", fontsize=7,
                        arrowprops=dict(arrowstyle="->", lw=0.6, color=PC[r.ct]))
            continue
        col = PC[r.ct]
        mk = "o" if r.cx == "configured" else "s"
        ax.plot([r.xl, r.xh], [r.y, r.y], color=col, lw=0.7)
        ax.plot([r.x, r.x], [r.yl, r.yh], color=col, lw=0.7)
        ax.plot(r.x, r.y, mk, color=col, ms=4.5, mfc=col if r.cx == "configured" else "white")
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_ylim(-60, YMAX)
    ax.set_xlabel("retained $-$ fresh method calls (% of fresh mean)")
    ax.set_ylabel("retained $-$ fresh planning wall time\n(% of fresh mean)")
    up = int((d.yl > 0).sum())
    ax.text(0.02, 0.97, f"{len(d)} cells with fewer retained method calls;\n"
            f"in {up} of them the wall-time CI lies wholly above 0", transform=ax.transAxes, va="top", fontsize=7.5)
    hs = [Line2D([], [], color=PC[c], marker="o", ls="", ms=4.5, label=c) for c in POLICIES if c in set(d.ct)]
    hs += [Line2D([], [], color="k", marker="o", ls="", ms=4.5, label="configured size"),
           Line2D([], [], color="k", marker="s", mfc="white", ls="", ms=4.5, label="small size")]
    ax.legend(handles=hs, fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    plotstyle.save(fig, str(OUT / "v4_calls_vs_time"))
    d.to_csv(OUT.parent.parent.parent / "work" / "recovery" / "v4_calls_vs_time_cells.csv", index=False)
    return d


def lag_control(t):
    ctl = pd.DataFrame(json.loads((EVID / "mulder_suffix_control.json").read_text())["trials"])
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), gridspec_kw=dict(width_ratios=[1.25, 1.2, 1], wspace=0.5))
    ax = axes[0]
    groups = []
    for size in ("small", "configured"):
        lag = t[(t.complexity == size) & (t.profile == "lag_1s") & (t.controller == "filtered")]
        for b in V4_BACK:
            g = lag[lag.planner_backend == b]
            groups.append((size, b, int(g.success.sum()), len(g)))
        if size == "configured":
            groups.append((size, "control", int(ctl.success.sum()), len(ctl)))
    x = 0
    ticks = []
    for size, b, k, n in groups:
        lo, hi = wilson(k, n)
        col = CTRL_COLOR if b == "control" else V4_BACK_COLOR[b]
        ax.bar(x, k / n, 0.8, color=col)
        ax.plot([x, x], [lo, hi], color="#333", lw=0.8)
        ax.text(x, hi + 0.03, f"{k}", ha="center", fontsize=7.2)
        ticks.append(x)
        x += 1
        if size == "small" and b == V4_BACK[-1]:
            x += 0.7
    ax.set_xticks(ticks, ["L", "F", "R", "L", "F", "R", "C"], fontsize=7)
    ax.text(1, -0.13, "small", ha="center", transform=ax.get_xaxis_transform(), fontsize=7.5)
    ax.text(5.2, -0.13, "configured", ha="center", transform=ax.get_xaxis_transform(), fontsize=7.5)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("completion fraction (Wilson 95% CI)\nlabel = completed of 10")
    ax.set_title("1 s lag, filtered policy", fontsize=8.5)

    bx = axes[1]
    lag = t[(t.complexity == "configured") & (t.profile == "lag_1s") & (t.controller == "filtered")]
    cols = ["legacy", "ipyhop_fresh", "ipyhop_retained", "control"]
    for j, b in enumerate(cols):
        g = (ctl if b == "control" else lag[lag.planner_backend == b]).set_index("seed").sort_index()
        col = CTRL_COLOR if b == "control" else V4_BACK_COLOR[b]
        for s, row in g.iterrows():
            bx.plot(j, s, "o", ms=6.5, color=col, mfc=col if row.success else "white", mew=1.0)
            bx.text(j + 0.22, s, f"{int(row.completed_actions)}", va="center", fontsize=6.6, color="#444")
    bx.set_xticks(range(4), ["L", "F", "R", "C"], fontsize=7)
    bx.set_yticks(range(10))
    bx.set_ylim(9.6, -0.6)
    bx.set_xlim(-0.5, 3.8)
    bx.set_ylabel("seed (initial phase)")
    bx.grid(False)
    bx.set_title("per seed (configured);\nfilled = completed, number = actions done", fontsize=7.5)

    cx = axes[2]
    for j, b in enumerate(cols):
        g = ctl if b == "control" else lag[lag.planner_backend == b]
        col = CTRL_COLOR if b == "control" else V4_BACK_COLOR[b]
        v = g.planning_wall_s.to_numpy()
        cx.bar(j, v.mean(), 0.75, color=col, yerr=v.std(ddof=1), error_kw=dict(lw=0.7, capsize=2))
    cx.set_xticks(range(4), ["L", "F", "R", "C"], fontsize=7)
    cx.set_ylabel("planning wall time per run (s)")
    cx.set_title("planning cost (configured)", fontsize=8.5)
    hs = [Line2D([], [], color=V4_BACK_COLOR[b], marker="s", ls="", ms=6, label=f"{l} = {BLAB[b]}")
          for b, l in zip(V4_BACK, "LFR")]
    hs.append(Line2D([], [], color=CTRL_COLOR, marker="s", ls="", ms=6, label="C = GTPyhop whole-suffix control"))
    fig.legend(handles=hs, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.16), fontsize=7)
    plotstyle.save(fig, str(OUT / "v4_lag_control"))


if __name__ == "__main__":
    plotstyle.apply()
    t = pd.read_csv(V4 / "trials.csv")
    assert len(t) == 2160
    completion(t)
    pair_differences(t)
    d = calls_vs_time(t)
    print(d.round(3).to_string())
    lag_control(t)
