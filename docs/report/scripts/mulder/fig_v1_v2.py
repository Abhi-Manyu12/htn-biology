"""Figures for the Mulder model-version-1 pilot / frequency study and the version-2 verified sweep.

Sources (all trials.csv):
  mulder_results/pilot                         (v1, 270 trials)
  mulder_results/frequency_0049_vs_005         (v1, 180 trials)
  mulder_results/controller_audit_v2/verified_sweep   (v2, 180 trials; identical outcomes to
                                                        controller_audit_v2/frequency_comparison)
  mulder_results/paper_validation_v3 (endpoint profile only, for the v3 0.049/0.05 Hz panel)
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _common import RES, ORDER, POLICY_COLORS, C, apply, save, out, TOTAL_ACTIONS

apply()
pilot = pd.read_csv(RES / "pilot" / "trials.csv")
f1 = pd.read_csv(RES / "frequency_0049_vs_005" / "trials.csv")
f2 = pd.read_csv(RES / "controller_audit_v2" / "verified_sweep" / "trials.csv")
v3 = pd.read_csv(RES / "paper_validation_v3" / "trials.csv")
v3e = v3[v3.profile == "endpoint"]
LOGTICKS = ([2, 5, 10, 20, 50, 100, 218], ["2", "5", "10", "20", "50", "100", "218"])


def fig_pilot_grid():
    amps, freqs = [0.0, 5.0, 10.0], [0.01, 0.05, 0.1]
    fig, axes = plt.subplots(2, 3, figsize=(6.2, 4.3))
    for ax, c in zip(axes.flat, ORDER):
        data = np.zeros((3, 3))
        for i, a in enumerate(amps):
            for j, f in enumerate(freqs):
                s = pilot[(pilot.controller == c) & (pilot.amplitude_cm == a) & np.isclose(pilot.frequency_hz, f)]
                k, n = int(s.success.sum()), len(s)
                data[i, j] = k / n
                ax.text(j, i, f"{k}/{n}", ha="center", va="center", fontsize=10,
                        color="white" if k / n > 0.55 else "black")
        ax.imshow(data, vmin=0, vmax=1, cmap="Blues", origin="lower")
        ax.set_xticks(range(3), ["0.01", "0.05", "0.1"], fontsize=9.5)
        ax.set_yticks(range(3), ["0", "5", "10"], fontsize=9.5)
        ax.grid(False)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_edgecolor(POLICY_COLORS[c])
            s.set_linewidth(2)
            s.set_visible(True)
        ax.set_title(c, fontsize=11, color="black")
        ax.set_xlabel("frequency (Hz)", fontsize=9.5)
        ax.set_ylabel("amplitude (cm)", fontsize=9.5)
    fig.tight_layout()
    save(fig, out("v1_pilot_completion"))


def fig_pilot_progress():
    conds = [(a, f) for a in (5.0, 10.0) for f in (0.01, 0.05, 0.1)]
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.4), sharey=True)
    rng = np.random.default_rng(3)
    for ax, (a, f) in zip(axes.flat, conds):
        for i, c in enumerate(ORDER):
            s = pilot[(pilot.controller == c) & (pilot.amplitude_cm == a) & np.isclose(pilot.frequency_hz, f)]
            y = s.completed_actions.values
            ax.scatter(i + rng.uniform(-0.2, 0.2, len(y)), y, s=11, color=POLICY_COLORS[c], lw=0, alpha=0.85)
        ax.axhline(TOTAL_ACTIONS, color=C["grey"], ls="--", lw=0.6)
        ax.set_yscale("log")
        ax.set_yticks(*LOGTICKS)
        ax.set_xticks(range(6), ORDER, rotation=45, ha="right", fontsize=7)
        ax.text(0.02, 0.97, f"{a:g} cm, {f:g} Hz", transform=ax.transAxes, fontsize=8, va="top",
                bbox=dict(fc="white", ec="none", pad=1))
    for ax in axes[:, 0]:
        ax.set_ylabel("accepted actions (of 218)")
    fig.tight_layout()
    save(fig, out("v1_pilot_progress"))


def fig_pilot_costs():
    """Completed v1 trials only; stationary rows pooled over the three frequencies (identical runs)."""
    panels = [("elapsed_s", "construction time (s)", False), ("normalized_travel", "travel / ideal static path", False),
              ("repairs", "repairs per trial", True), ("planning_calls", "planning calls", True),
              ("attachment_error_mean_cm", "mean accepted error (cm)", False), ("planning_wall_s", "planning wall time (s)", True)]
    groups = [(0.0, None, "stationary", "white"), (5.0, 0.01, "5 cm, 0.01 Hz", None), (10.0, 0.01, "10 cm, 0.01 Hz", None)]
    marks = {"stationary": "o", "5 cm, 0.01 Hz": "s", "10 cm, 0.01 Hz": "D"}
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.6))
    rng = np.random.default_rng(4)
    for ax, (m, lab, logy) in zip(axes.flat, panels):
        for i, c in enumerate(ORDER):
            for j, (a, f, glab, _) in enumerate(groups):
                s = pilot[(pilot.controller == c) & (pilot.amplitude_cm == a) & pilot.success]
                if f is not None:
                    s = s[np.isclose(s.frequency_hz, f)]
                if not len(s):
                    continue
                y = s[m].values.astype(float)
                if logy:
                    y = np.where(y <= 0, np.nan, y)
                x = i + (j - 1) * 0.25 + rng.uniform(-0.05, 0.05, len(y))
                ax.scatter(x, y, s=9, marker=marks[glab], lw=0.6, edgecolor=POLICY_COLORS[c],
                           facecolor="white" if a == 0 else POLICY_COLORS[c])
        ax.set_xticks(range(6), ORDER, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel(lab, fontsize=8)
        if logy:
            ax.set_yscale("log")
    handles = [Line2D([], [], marker=marks[g[2]], lw=0, mec="black", mfc="white" if g[0] == 0 else "black", label=g[2])
               for g in groups]
    fig.legend(handles=handles, loc="upper center", ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, out("v1_pilot_costs"))


def fig_frequency():
    sets = [(f1, "v1 (frequency_0049_vs_005)"), (f2, "v2 (controller_audit_v2/verified_sweep)"),
            (v3e, "v3 endpoint profile (paper_validation_v3)")]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.3), sharey=True)
    rng = np.random.default_rng(5)
    for ax, (d, title) in zip(axes, sets):
        for i, c in enumerate(ORDER):
            a = d[(d.controller == c) & (d.amplitude_cm == 5) & np.isclose(d.frequency_hz, 0.049)].sort_values("seed")
            b = d[(d.controller == c) & (d.amplitude_cm == 5) & np.isclose(d.frequency_hz, 0.05)].sort_values("seed")
            assert list(a.seed) == list(b.seed)
            xa, xb = i - 0.17, i + 0.17
            jit = rng.uniform(-0.04, 0.04, len(a))
            for ya, yb, jj in zip(a.completed_actions, b.completed_actions, jit):
                ax.plot([xa + jj, xb + jj], [ya, yb], color=POLICY_COLORS[c], lw=0.4, alpha=0.5)
            ax.scatter(xa + jit, a.completed_actions, s=8, marker="o", facecolor="white", edgecolor=POLICY_COLORS[c], lw=0.7, zorder=3)
            ax.scatter(xb + jit, b.completed_actions, s=8, marker="o", color=POLICY_COLORS[c], zorder=3)
            ax.text(i, 330, f"{int(a.success.sum())}|{int(b.success.sum())}", ha="center", fontsize=6.5)
        ax.set_yscale("log")
        ax.set_yticks(*LOGTICKS)
        ax.set_ylim(1.6, 420)
        ax.set_xticks(range(6), ORDER, rotation=45, ha="right", fontsize=7)
        ax.set_xlabel(title, fontsize=7.5)
    axes[0].set_ylabel("accepted actions at 5 cm (of 218)")
    handles = [Line2D([], [], marker="o", lw=0, mfc="white", mec="black", label="0.049 Hz"),
               Line2D([], [], marker="o", lw=0, mfc="black", mec="black", label="0.05 Hz")]
    fig.legend(handles=handles, loc="upper center", ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, out("freq_0049_vs_005"))


def fig_v1_vs_v2():
    key = ["controller", "seed", "amplitude_cm", "frequency_hz"]
    m = f1.merge(f2, on=key, suffixes=("_v1", "_v2"))
    m = m[m.amplitude_cm > 0]
    fig, axes = plt.subplots(1, 2, figsize=FIG2)
    for ax, a in zip(axes, (5.0, 10.0)):
        s = m[m.amplitude_cm == a]
        for c in ORDER:
            t = s[s.controller == c]
            ax.scatter(t.completed_actions_v1, t.completed_actions_v2, s=14, color=POLICY_COLORS[c], alpha=0.85,
                       lw=0, label=c)
        ax.plot([1.8, 240], [1.8, 240], color=C["grey"], lw=0.6, ls="--")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(*LOGTICKS)
        ax.set_yticks(*LOGTICKS)
        ax.set_xlim(1.8, 240)
        ax.set_ylim(1.8, 240)
        ax.set_aspect("equal")
        ax.set_xlabel(f"v1 accepted actions ({a:g} cm)")
        ax.set_ylabel(f"v2 accepted actions ({a:g} cm)")
    axes[1].legend(fontsize=6.5, loc="upper left", handletextpad=0.1)
    fig.tight_layout()
    save(fig, out("v1_vs_v2_progress"))


FIG2 = (7.0, 3.4)

if __name__ == "__main__":
    assert len(pilot) == 270 and len(f1) == 180 and len(f2) == 180
    fig_pilot_grid()
    fig_pilot_progress()
    fig_pilot_costs()
    fig_frequency()
    fig_v1_vs_v2()
