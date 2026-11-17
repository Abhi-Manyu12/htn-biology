"""Controller audit, model version 2: matched diagnostic trial (5 cm, 0.05 Hz, seed 0, endpoint executor).

Sources: mulder_results/controller_audit_v2/report/{ledger.csv, replays.csv, trials.csv}
(the same trial-level and replay outcomes are recorded in controller_audit_v2/a5_f005_seed0,
controller_audit_v2/matched_trial and diagnostics_a5_f005_seed0).
"""
import json
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _common import RES, ORDER, POLICY_COLORS, C, apply, save, out

apply()
D = RES / "controller_audit_v2" / "report"
ledger = pd.read_csv(D / "ledger.csv")
replays = pd.read_csv(D / "replays.csv")
trials = pd.read_csv(D / "trials.csv")
REPLAYS = ["original", "refreshed_target", "frozen_saved_target", "frozen_refreshed_target",
           "arrival_oracle", "refreshed_arrival_oracle"]
REASON_COL = {"attachment_miss": C["vermillion"], "filtered_drift": C["green"], "predicted_drift": C["orange"],
              "support_change": C["purple"]}


def fig_replays():
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    data = np.zeros((len(ORDER), len(REPLAYS)))
    for i, c in enumerate(ORDER):
        for j, r in enumerate(REPLAYS):
            row = replays[(replays.controller == c) & (replays.replay == r)].iloc[0]
            acc = str(row.accepted) == "True"
            data[i, j] = 1 if acc else 0
            ax.text(j, i, f"{'accepted' if acc else 'missed'}\n{row.error_cm:.3f} cm", ha="center", va="center",
                    fontsize=6.5, color="white" if acc else "black")
    ax.imshow(data, cmap=plt.matplotlib.colors.ListedColormap(["#F2F2F2", C["blue"]]), aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(REPLAYS)), [r.replace("_", "\n") for r in REPLAYS], fontsize=7)
    ax.set_yticks(range(len(ORDER)), ORDER)
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("isolated replay of each controller's first missed action (tolerance 0.5 cm)")
    fig.tight_layout()
    save(fig, out("audit_v2_replays"))


def fig_attempts():
    acts = ledger[ledger.event == "action"]
    reps = ledger[ledger.event == "repair"]
    tmax = trials.elapsed_s.max()
    phase = trials.initial_phase_rad.iloc[0]
    fig, axes = plt.subplots(7, 1, figsize=(7.0, 6.6), sharex=True,
                             gridspec_kw={"height_ratios": [0.8] + [1] * 6})
    t = np.linspace(0, tmax, 2000)
    axes[0].plot(t, 5 * np.sin(2 * math.pi * 0.05 * t + phase), color="black", lw=0.8)
    axes[0].set_ylabel("bottom\nshift (cm)", fontsize=7)
    for ax, c in zip(axes[1:], ORDER):
        a = acts[acts.controller == c]
        for _, r in a.iterrows():
            ok = str(r.accepted) == "True"
            ax.plot([r.start_time_s, r.time_s], [r.error_cm] * 2, color=C["green"] if ok else C["vermillion"], lw=2.2,
                    solid_capstyle="butt", alpha=0.85)
            if r.error_before_correction_cm > r.error_cm + 1e-9:
                ax.annotate("", xy=(r.time_s, r.error_cm), xytext=(r.arrival_time_s, r.error_before_correction_cm),
                            arrowprops=dict(arrowstyle="-|>", color=C["grey"], lw=0.6, mutation_scale=6))
                ax.plot(r.arrival_time_s, r.error_before_correction_cm, "o", ms=2.5, mfc="white", mec=C["grey"], mew=0.6)
        for _, r in reps[reps.controller == c].iterrows():
            ax.axvline(r.time_s, color=REASON_COL[r.reason], lw=0.9, ls=(0, (2, 1)))
        ax.axhline(0.5, color=C["grey"], lw=0.5, ls="--")
        ax.set_ylim(-0.4, 10.5)
        ax.set_yticks([0, 5, 10])
        tr = trials[trials.controller == c].iloc[0]
        ax.set_ylabel(c, fontsize=7.5, rotation=0, ha="right", va="center")
        ax.text(tmax * 1.005, 5, f"{int(tr.completed_actions)}/218\n{int(tr.repairs)} rep.", fontsize=6.3, va="center")
    axes[-1].set_xlabel("simulated time (s); bars: attempts at their final error (cm, 0-10 scale)")
    handles = [Line2D([], [], color=C["green"], lw=2, label="accepted attempt"),
               Line2D([], [], color=C["vermillion"], lw=2, label="missed attempt"),
               Line2D([], [], color=C["grey"], marker="o", mfc="white", lw=0.6, label="error before correction")]
    handles += [Line2D([], [], color=v, lw=0.9, ls=(0, (2, 1)), label=f"repair: {k}") for k, v in REASON_COL.items()]
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=6.5, bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout(rect=(0, 0, 0.95, 0.94))
    save(fig, out("audit_v2_attempts"))


if __name__ == "__main__":
    fig_replays()
    fig_attempts()
