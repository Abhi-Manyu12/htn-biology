"""Figures for the Mulder model-version-3 paper-facing study (2,280 trials).

Source: mulder_results/paper_validation_v3/trials.csv and comparisons.csv
(byte-identical to mulder_results/paper_validation_v3_report/, which is the re-analysis used by
docs/research/evidence/mulder_v3_summary.json).
Run: python fig_v3.py   (writes into W/report/figures/mulder/)
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _common import (RES, ORDER, POLICY_COLORS, C, apply, save, out, wilson, TOTAL_ACTIONS,
                     FIG_WIDE, FIG_2PANEL, FIG_GRID, FIG_1COL, R)

apply()


def E(v, lo, hi):
    """Asymmetric error-bar lengths, clipped at 0 against floating-point rounding."""
    return [[max(0.0, v - lo)], [max(0.0, hi - v)]]


V3 = RES / "paper_validation_v3"
df = pd.read_csv(V3 / "trials.csv")
cmp = pd.read_csv(V3 / "comparisons.csv")
for col in ("ci95", "percent_ci95", "success_ci95"):
    cmp[col] = cmp[col].apply(lambda s: json.loads(s) if isinstance(s, str) and s.startswith("[") else None)

MOVING = [(5, 0.049), (5, 0.05), (10, 0.049), (10, 0.05)]
COND_LABEL = {(0, 0.0): "stationary", (5, 0.049): "5 cm\n0.049 Hz", (5, 0.05): "5 cm\n0.05 Hz",
              (10, 0.049): "10 cm\n0.049 Hz", (10, 0.05): "10 cm\n0.05 Hz"}
COND_MARK = {(5, 0.049): "o", (5, 0.05): "s", (10, 0.049): "^", (10, 0.05): "D"}


def cell(profile, ctrl, a, f):
    sub = df[(df.profile == profile) & (df.controller == ctrl) & (df.amplitude_cm == a)]
    if a:
        sub = sub[np.isclose(sub.frequency_hz, f)]
    return int(sub.success.sum()), len(sub)


def crow(profile, ctrl, a, f, metric):
    s = cmp[(cmp.profile == profile) & (cmp.controller == ctrl) & (cmp.amplitude_cm == a) &
            np.isclose(cmp.frequency_hz, f) & (cmp.metric == metric)]
    assert len(s) == 1, (profile, ctrl, a, f, metric)
    return s.iloc[0]


# ---------------------------------------------------------------- 1. completion heatmap
def fig_completion():
    conds = [(0, 0.0)] + MOVING
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    for ax, prof in zip(axes, ("endpoint", "tracking")):
        data = np.zeros((len(ORDER), len(conds)))
        for i, c in enumerate(ORDER):
            for j, (a, f) in enumerate(conds):
                k, n = cell(prof, c, a, f)
                data[i, j] = k / n
                ax.text(j, i, f"{k}/{n}", ha="center", va="center", fontsize=7.5,
                        color="white" if k / n > 0.55 else "black")
        ax.imshow(data, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(conds)), [COND_LABEL[c] for c in conds], fontsize=7)
        ax.set_yticks(range(len(ORDER)), ORDER)
        ax.grid(False)
        ax.set_xlabel(f"{prof} executor")
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(length=0)
    fig.tight_layout()
    save(fig, out("v3_completion"))


# ---------------------------------------------------------------- 2. Wilson dot plot
def fig_completion_wilson():
    fig, axes = plt.subplots(1, 2, figsize=FIG_2PANEL, sharey=True)
    for ax, prof in zip(axes, ("endpoint", "tracking")):
        for i, c in enumerate(ORDER):
            for j, cond in enumerate(MOVING):
                k, n = cell(prof, c, *cond)
                lo, hi = wilson(k, n)
                x = j + (i - 2.5) * 0.13
                ax.errorbar(x, k / n, yerr=E(k / n, lo, hi), fmt=COND_MARK[cond],
                            color=POLICY_COLORS[c], ms=3.5, lw=0.9, capsize=1.5)
        ax.set_xticks(range(4), [COND_LABEL[c] for c in MOVING], fontsize=7)
        ax.set_ylim(-0.03, 1.05)
        ax.set_xlabel(f"{prof} executor, moving conditions")
    axes[0].set_ylabel("completion rate (n = 30 per point)")
    handles = [Line2D([], [], color=POLICY_COLORS[c], marker="o", lw=0, label=c) for c in ORDER]
    axes[1].legend(handles=handles, loc="center right", fontsize=7, handletextpad=0.2)
    fig.tight_layout()
    save(fig, out("v3_completion_wilson"))


# ---------------------------------------------------------------- 3. partial progress under endpoint execution
def fig_endpoint_progress():
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 2.8), sharey=True)
    rng = np.random.default_rng(0)
    for ax, cond in zip(axes, MOVING):
        a, f = cond
        for i, c in enumerate(ORDER):
            sub = df[(df.profile == "endpoint") & (df.controller == c) & (df.amplitude_cm == a) &
                     np.isclose(df.frequency_hz, f)]
            y = sub.completed_actions.values
            x = i + rng.uniform(-0.25, 0.25, len(y))
            ax.scatter(x, y, s=6, color=POLICY_COLORS[c], alpha=0.75, lw=0)
            ax.plot([i - 0.3, i + 0.3], [np.median(y)] * 2, color="black", lw=0.8)
        ax.set_yscale("log")
        ax.set_xticks(range(6), ORDER, rotation=60, ha="right", fontsize=7)
        ax.set_xlabel(COND_LABEL[cond].replace("\n", ", "), fontsize=8)
        ax.axhline(TOTAL_ACTIONS, color=C["grey"], ls="--", lw=0.6)
    axes[0].set_ylabel("accepted actions (of 218, log scale)")
    axes[0].set_yticks([2, 5, 10, 20, 50, 100, 218], ["2", "5", "10", "20", "50", "100", "218"])
    fig.tight_layout()
    save(fig, out("v3_endpoint_progress"))


# ---------------------------------------------------------------- 4. paired effects (regenerated + extended)
def fig_paired_effects():
    ctrls = ["local", "local_repair", "filtered", "predictive", "full"]
    metrics = [("elapsed_s", "construction duration"), ("sampled_travel_10s_cm", "travel, 10 s camera cadence")]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True)
    for ax, (m, lab) in zip(axes, metrics):
        for i, c in enumerate(ctrls):
            for j, cond in enumerate(MOVING):
                r = crow("tracking", c, cond[0], cond[1], m)
                y = i + (j - 1.5) * 0.17
                lo, hi = r.percent_ci95
                ax.errorbar(r.percent_difference, y, xerr=E(r.percent_difference, lo, hi),
                            fmt=COND_MARK[cond], color=POLICY_COLORS[c], ms=3.6, lw=0.9, capsize=1.5)
        ax.axvline(0, color=C["grey"], lw=0.7)
        ax.set_xlabel(f"moving $-$ stationary, % ({lab})")
    axes[0].set_yticks(range(len(ctrls)), ctrls)
    axes[0].invert_yaxis()
    handles = [Line2D([], [], color=C["grey"], marker=COND_MARK[c], lw=0, label=COND_LABEL[c].replace("\n", ", "))
               for c in MOVING]
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=7, handletextpad=0.2,
               bbox_to_anchor=(0.55, 1.03))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, out("v3_paired_effects"))


def fig_paired_effects_primary():
    """Like-for-like regeneration of docs/manuscript/figures/mulder_v3_paired_effects (10 cm, 0.05 Hz)."""
    ctrls = ["local", "full", "predictive"]
    fig, axes = plt.subplots(1, 2, figsize=FIG_2PANEL)
    for ax, m, lab in zip(axes, ("elapsed_s", "sampled_travel_10s_cm"),
                          ("construction duration", "travel at 10 s camera cadence")):
        for i, c in enumerate(ctrls):
            r = crow("tracking", c, 10, 0.05, m)
            lo, hi = r.percent_ci95
            ax.errorbar(i, r.percent_difference, yerr=E(r.percent_difference, lo, hi),
                        fmt="o", color=POLICY_COLORS[c], capsize=3)
            ax.annotate(f"{r.percent_difference:.2f}%", (i, r.percent_difference), xytext=(7, 0),
                        textcoords="offset points", va="center", fontsize=7)
        ax.axhline(0, color=C["grey"], lw=0.7)
        ax.set_xticks(range(3), ctrls)
        ax.set_xlim(-0.5, 2.7)
        ax.set_ylabel(f"moving $-$ stationary (%)\n{lab}")
    fig.tight_layout()
    save(fig, out("v3_paired_effects_primary"))


# ---------------------------------------------------------------- 5. phase-time allocation shifts
def fig_phase_allocation():
    ctrls = ["local", "filtered", "full"]
    metrics = [("radials_time_pct", "radii"), ("auxiliary_time_pct", "auxiliary spiral"),
               ("capture_time_pct", "capture spiral")]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.6), sharey=True)
    for ax, (m, lab) in zip(axes, metrics):
        for i, c in enumerate(ctrls):
            for j, cond in enumerate(MOVING):
                r = crow("tracking", c, cond[0], cond[1], m)
                lo, hi = r.ci95
                y = i + (j - 1.5) * 0.17
                ax.errorbar(r.mean_difference, y, xerr=E(r.mean_difference, lo, hi),
                            fmt=COND_MARK[cond], color=POLICY_COLORS[c], ms=3.4, lw=0.9, capsize=1.5)
        ax.axvline(0, color=C["grey"], lw=0.7)
        ax.set_xlabel(f"$\\Delta$ share of time, {lab}\n(percentage points)")
    axes[0].set_yticks(range(3), ctrls)
    axes[0].invert_yaxis()
    handles = [Line2D([], [], color=C["grey"], marker=COND_MARK[c], lw=0, label=COND_LABEL[c].replace("\n", ", "))
               for c in MOVING]
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=7, handletextpad=0.2,
               bbox_to_anchor=(0.55, 1.04))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, out("v3_phase_allocation"))


# ---------------------------------------------------------------- 6. distributions of costs by policy
def fig_cost_distributions():
    panels = [("elapsed_s", "construction time (s)", False), ("sampled_travel_10s_cm", "travel, 10 s cadence (cm)", False),
              ("repairs", "repairs per trial", False), ("planning_calls", "planning calls per trial", True),
              ("method_calls", "HTN method calls per trial", True), ("planning_wall_s", "planning wall time (s)", True)]
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.6))
    rng = np.random.default_rng(1)
    for ax, (m, lab, logy) in zip(axes.flat, panels):
        for i, c in enumerate(ORDER):
            st = df[(df.profile == "tracking") & (df.controller == c) & (df.amplitude_cm == 0)]
            mv = df[(df.profile == "tracking") & (df.controller == c) & (df.amplitude_cm == 10) &
                    np.isclose(df.frequency_hz, 0.05) & df.success]
            for off, sub, filled in ((-0.18, st, False), (0.18, mv, True)):
                if not len(sub):
                    ax.text(i + off, 0.5, "none\ncompleted", transform=ax.get_xaxis_transform(), ha="center",
                            va="center", fontsize=5.5, color=C["grey"], rotation=90)
                    continue
                y = sub[m].values
                x = i + off + rng.uniform(-0.08, 0.08, len(y))
                ax.scatter(x, y, s=7, lw=0.6, alpha=0.8,
                           facecolor=POLICY_COLORS[c] if filled else "white", edgecolor=POLICY_COLORS[c])
        ax.set_xticks(range(6), ORDER, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel(lab, fontsize=8)
        if logy:
            ax.set_yscale("log")
    handles = [Line2D([], [], marker="o", lw=0, mfc="white", mec="black", label="stationary (all 30 complete)"),
               Line2D([], [], marker="o", lw=0, mfc="black", mec="black", label="10 cm, 0.05 Hz (completed runs)")]
    fig.legend(handles=handles, loc="upper center", ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, out("v3_cost_distributions"))


# ---------------------------------------------------------------- 7. sensitivity profiles + sensory lag (C10)
SENS = ["tracking", "tracking_dt_half", "tracking_slow", "tracking_fast", "tracking_tight", "repair_delay_1s",
        "flat_tracking", "flat_slow", "phase_wait", "sensor_lag_1s", "sensor_lag_5s"]


def fig_sensitivity():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.6), sharey=True, gridspec_kw={"width_ratios": [1, 1.25]})
    for i, prof in enumerate(SENS):
        for j, c in enumerate(("local", "predictive")):
            k, n = cell(prof, c, 10, 0.05)
            lo, hi = wilson(k, n)
            y = i + (j - 0.5) * 0.3
            axes[0].errorbar(k / n, y, xerr=E(k / n, lo, hi), fmt="o", color=POLICY_COLORS[c],
                             ms=3.5, capsize=1.5, lw=0.9)
            axes[0].text(1.13, y, f"{k}/{n}", va="center", fontsize=6.5)
            r = crow(prof, c, 10, 0.05, "elapsed_s")
            if r.paired_n:
                lo2, hi2 = r.percent_ci95
                axes[1].errorbar(r.percent_difference, y, xerr=E(r.percent_difference, lo2, hi2),
                                 fmt="o", color=POLICY_COLORS[c], ms=3.5, capsize=1.5, lw=0.9)
            else:
                axes[1].text(0.05, y, "no completed pairs", va="center", fontsize=6.5, color=C["vermillion"])
    axes[0].set_xlim(-0.05, 1.3)
    axes[0].set_xticks([0, 0.5, 1])
    axes[0].set_xlabel("completion at 10 cm, 0.05 Hz\n(Wilson 95% interval)")
    axes[1].set_xlabel("duration change vs own stationary control, %\n(paired bootstrap 95% interval)")
    axes[1].set_xlim(0, 2.1)
    axes[0].set_yticks(range(len(SENS)), SENS, fontsize=7.5)
    axes[0].invert_yaxis()
    handles = [Line2D([], [], color=POLICY_COLORS[c], marker="o", lw=0, label=c) for c in ("local", "predictive")]
    axes[1].legend(handles=handles, loc="lower right", fontsize=7)
    fig.tight_layout()
    save(fig, out("v3_sensitivity"))


def fig_sensor_lag():
    profs = [("tracking", "lag 0 s (tracking,\nseeds 0-11)"), ("sensor_lag_1s", "lag 1 s"), ("sensor_lag_5s", "lag 5 s")]
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    rng = np.random.default_rng(2)
    for i, (prof, lab) in enumerate(profs):
        for j, c in enumerate(("local", "predictive")):
            sub = df[(df.profile == prof) & (df.controller == c) & (df.amplitude_cm == 10) &
                     np.isclose(df.frequency_hz, 0.05) & (df.seed < 12)]
            x0 = i + (j - 0.5) * 0.36
            for _, r in sub.iterrows():
                mk = "o" if r.success else ("x" if r.failure_reason == "attachment_miss" else "^")
                ax.scatter(x0 + rng.uniform(-0.09, 0.09), r.completed_actions, marker=mk, s=14,
                           color=POLICY_COLORS[c], lw=0.9, facecolor=POLICY_COLORS[c] if mk != "x" else None)
            ax.text(x0, 300, f"{int(sub.success.sum())}/{len(sub)}", ha="center", fontsize=7)
    ax.set_yscale("log")
    ax.set_yticks([2, 5, 10, 20, 50, 100, 218], ["2", "5", "10", "20", "50", "100", "218"])
    ax.set_ylim(1.5, 420)
    ax.set_xticks(range(3), [p[1] for p in profs])
    ax.set_ylabel("accepted actions (of 218, log scale)")
    handles = [Line2D([], [], color=POLICY_COLORS[c], marker="o", lw=0, label=c) for c in ("local", "predictive")]
    handles += [Line2D([], [], color="black", marker="o", lw=0, label="completed"),
                Line2D([], [], color="black", marker="x", lw=0, label="attachment miss"),
                Line2D([], [], color="black", marker="^", lw=0, label="action time limit")]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=7)
    fig.tight_layout()
    save(fig, out("v3_sensor_lag"))


# ---------------------------------------------------------------- 8. phase_wait (C11) and flat vs HTN (C06)
def matched(prof_a, prof_b, ctrl, metric="elapsed_s"):
    a = df[(df.profile == prof_a) & (df.controller == ctrl) & (df.amplitude_cm == 10) & np.isclose(df.frequency_hz, 0.05)]
    b = df[(df.profile == prof_b) & (df.controller == ctrl) & (df.amplitude_cm == 10) & np.isclose(df.frequency_hz, 0.05)]
    m = a.merge(b, on="seed", suffixes=("_a", "_b"))
    m = m[m.success_a & m.success_b]
    return m


def fig_phase_wait():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.7), gridspec_kw={"width_ratios": [1.3, 1, 1]})
    m = matched("phase_wait", "tracking_slow", "local")
    d = (m.elapsed_s_a - m.elapsed_s_b).values
    w = m.method_wait_s_a.values
    axes[0].bar(m.seed, d, color=POLICY_COLORS["local"], width=0.7, label="total extra time")
    axes[0].scatter(m.seed, w, color="black", s=10, zorder=3, label="time spent in method waits")
    axes[0].axhline(d.mean(), color=C["vermillion"], lw=0.8, ls="--")
    axes[0].text(11.6, d.mean() + 0.6, f"mean {d.mean():.2f} s", ha="right", fontsize=7, color=C["vermillion"])
    axes[0].set_xlabel("forcing-phase seed")
    axes[0].set_ylabel("phase_wait $-$ tracking_slow (s)")
    axes[0].legend(fontsize=6.5, loc="upper left", ncol=1)
    axes[0].set_ylim(0, max(d.max(), w.max()) * 1.55)
    axes[0].set_xticks(range(0, 12, 2))
    # moving-minus-stationary for the three slow-speed profiles
    for i, prof in enumerate(("tracking_slow", "flat_slow", "phase_wait")):
        r = crow(prof, "local", 10, 0.05, "elapsed_s")
        lo, hi = r.ci95
        axes[1].errorbar(i, r.mean_difference, yerr=E(r.mean_difference, lo, hi), fmt="o",
                         color=POLICY_COLORS["local"], capsize=3)
    axes[1].set_xticks(range(3), ["tracking\n_slow", "flat\n_slow", "phase\n_wait"], fontsize=7)
    axes[1].set_ylabel("moving $-$ stationary (s)")
    axes[1].set_ylim(0, 60)
    sub = df[(df.profile == "phase_wait") & (df.controller == "local") & (df.amplitude_cm == 10)]
    vals, counts = np.unique(sub.method_waits, return_counts=True)
    axes[2].bar(vals, counts, color=POLICY_COLORS["local"], width=0.6)
    axes[2].set_xticks(vals)
    axes[2].set_xlabel("waits chosen per moving trial")
    axes[2].set_ylabel("trials (n = 12)")
    fig.tight_layout()
    save(fig, out("v3_phase_wait"))
    return d.mean(), w.mean(), len(d)


def fig_flat_vs_htn():
    fig, axes = plt.subplots(1, 2, figsize=FIG_2PANEL)
    for j, c in enumerate(("local", "predictive")):
        m = matched("flat_tracking", "tracking", c)
        d = (m.elapsed_s_a - m.elapsed_s_b).values
        axes[0].scatter(m.seed + (j - 0.5) * 0.25, d, color=POLICY_COLORS[c], s=12, label=c)
    axes[0].set_ylim(-1, 1)
    axes[0].set_xlabel("forcing-phase seed (10 cm, 0.05 Hz)")
    axes[0].set_ylabel("flat $-$ HTN construction time (s)")
    axes[0].legend(fontsize=7)
    for i, prof in enumerate(("tracking", "flat_tracking")):
        for j, c in enumerate(("local", "predictive")):
            r = crow(prof, c, 10, 0.05, "elapsed_s")
            lo, hi = r.percent_ci95
            axes[1].errorbar(i + (j - 0.5) * 0.25, r.percent_difference,
                             yerr=E(r.percent_difference, lo, hi), fmt="o",
                             color=POLICY_COLORS[c], capsize=3)
    axes[1].set_xticks([0, 1], ["HTN (tracking, n = 30)", "flat (flat_tracking, n = 12)"], fontsize=7.5)
    axes[1].set_xlim(-0.5, 1.5)
    axes[1].set_ylabel("moving $-$ stationary duration (%)")
    axes[1].set_ylim(0.9, 1.05)
    fig.tight_layout()
    save(fig, out("v3_flat_vs_htn"))


# ---------------------------------------------------------------- 9. measured quantities vs paper reference (C09/C12)
def fig_geometry_vs_paper():
    ref = json.load(open(R / "spider_web_mulder" / "paper_reference.json"))
    pv = ref["published_p_values"]
    # model metric, paper key, label, status
    rows = [("elapsed_s", "elapsed_s", "construction time", "predicted (uncalibrated)"),
            ("sampled_travel_10s_cm", "travel_cm", "travel (10 s cadence)", "predicted (uncalibrated)"),
            ("radials_time_pct", "radials_time_pct", "radii time share", "predicted (uncalibrated)"),
            ("auxiliary_time_pct", "auxiliary_time_pct", "auxiliary time share", "predicted (uncalibrated)"),
            ("capture_time_pct", "capture_time_pct", "capture time share", "predicted (uncalibrated)"),
            ("web_area_cm2", "web_area_cm2", "web area", "imposed / estimated"),
            ("capture_spiral_area_cm2", "capture_spiral_area_cm2", "capture-spiral area", "imposed / estimated"),
            ("eccentricity", "eccentricity", "eccentricity", "imposed"),
            ("mean_mesh_space_cm", "mean_mesh_space_cm", "mean mesh space", "imposed"),
            ("mean_capture_spiral_count", "mean_capture_spiral_count", "capture-spiral count", "imposed"),
            ("radial_count_measured", "radial_count_measured", "radial count", "imposed")]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    for i, (m, pk, lab, status) in enumerate(rows):
        r = crow("tracking", "local", 10, 0.05, m)
        if m.endswith("_pct"):
            val, (lo, hi), unit = r.mean_difference, r.ci95, "pp"
        elif m == "eccentricity":
            val, (lo, hi), unit = r.mean_difference, r.ci95, "abs"
        else:
            val, (lo, hi), unit = r.percent_difference, r.percent_ci95, "%"
        col = C["blue"] if status.startswith("predicted") else C["grey"]
        ax.errorbar(val, i, xerr=E(val, lo, hi), fmt="o", color=col, ms=4, capsize=2)
        txt = f"{val:+.3f} {unit}" if abs(val) > 1e-6 else f"$\\approx$0 (|$\\Delta$| < 1e-12)"
        ax.text(2.3, i, txt, va="center", fontsize=8.2)
        ax.text(3.95, i, f"p = {pv[pk]}", va="center", fontsize=8.2)
        ax.text(5.15, i, status, va="center", fontsize=8.2, color=col)
    ax.axvline(0, color=C["grey"], lw=0.7)
    ax.set_yticks(range(len(rows)), [r[2] for r in rows], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(-0.6, 6.75)
    ax.set_xticks([-0.5, 0, 0.5, 1, 1.5, 2])
    ax.set_xlabel("model moving $-$ stationary: % (pp for time shares)")
    ax.text(2.3, -1.1, "model difference", fontsize=8.5, weight="bold")
    ax.text(3.95, -1.1, "paper p (M vs R)", fontsize=8.5, weight="bold")
    ax.text(5.15, -1.1, "model status", fontsize=8.5, weight="bold")
    ax.spines["bottom"].set_bounds(-0.6, 2.1)
    fig.tight_layout()
    save(fig, out("v3_geometry_vs_paper"))


if __name__ == "__main__":
    assert len(df) == 2280
    fig_completion()
    fig_completion_wilson()
    fig_endpoint_progress()
    fig_paired_effects()
    fig_paired_effects_primary()
    fig_phase_allocation()
    fig_cost_distributions()
    fig_sensitivity()
    fig_sensor_lag()
    print("phase_wait (mean extra s, mean wait s, n):", fig_phase_wait())
    fig_flat_vs_htn()
    fig_geometry_vs_paper()
