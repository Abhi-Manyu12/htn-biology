"""Own drawings from the v1 pilot per-trial traces (mulder_results/pilot/trace_<case>_<seed>_<policy>.json).

Trace naming (spider_web_mulder/experiment.py main()): case index enumerates
amplitudes x frequencies in the order of metadata.json, amplitude outer loop:
pilot amplitudes [0, 5, 10] cm x frequencies [0.01, 0.05, 0.1] Hz, so case = 3*i_amp + i_freq.
  case 4 = 5 cm, 0.05 Hz;  case 6 = 10 cm, 0.01 Hz.
Each trace is a list of events; "action" events carry start/end material coordinates (cm), the
attachment error, acceptance flag, phase and end time; "repair" events carry time and reason.
The initial forcing phase comes from trials.csv (same seed -> same phase for every policy).
"""
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from _common import (RES, ORDER, POLICY_COLORS, PHASE_THREAD, C, apply, save, out, load_trace,
                     shear_dx, TOTAL_ACTIONS)

apply()
PILOT = RES / "pilot"
trials = pd.read_csv(PILOT / "trials.csv")
H = 30.0
CASES = {4: (5.0, 0.05), 6: (10.0, 0.01)}


def trial_row(case, seed, policy):
    a, f = CASES[case]
    r = trials[(trials.controller == policy) & (trials.seed == seed) & (trials.amplitude_cm == a) &
               np.isclose(trials.frequency_hz, f)]
    assert len(r) == 1
    return r.iloc[0]


def draw_web(ax, events, t_max=None, world=None, failed=True):
    """world=(A, f, phase, t): draw at room-frame positions at time t; else material coordinates."""
    for e in events:
        if e["event"] != "action":
            continue
        if t_max is not None and e["time_s"] > t_max:
            break
        if e["accepted"] and e["silk"]:
            (x1, y1), (x2, y2) = e["start_material_cm"], e["end_material_cm"]
            if world:
                A, f, ph, t = world
                x1 += shear_dx(y1, t, A, f, ph)
                x2 += shear_dx(y2, t, A, f, ph)
            ax.plot([x1, x2], [y1, y2], color=PHASE_THREAD[e["phase"]], lw=0.45, solid_capstyle="round")
        elif not e["accepted"] and failed:
            x, y = e["end_material_cm"]
            ax.plot(x, y, marker="x", color="black", ms=2.6, mew=0.6, alpha=0.75)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


def fig_web_grid():
    fig, axes = plt.subplots(2, 6, figsize=(7.0, 2.85))
    for row, case in enumerate((6, 4)):
        a, f = CASES[case]
        for col, p in enumerate(ORDER):
            ax = axes[row, col]
            ev = load_trace(PILOT / f"trace_{case}_0_{p}.json")
            ax.add_patch(plt.Rectangle((0, 0), 30, 30, fill=False, lw=0.4, ec="#BBBBBB", ls=":"))
            draw_web(ax, ev)
            ax.set_xlim(-1.5, 31.5)
            ax.set_ylim(-1.5, 31.5)
            r = trial_row(case, 0, p)
            ax.set_title(f"{p}\n{int(r.completed_actions)}/218", fontsize=8.5, pad=2)
        axes[row, 0].text(-6, 15, f"{a:g} cm\n{f:g} Hz", rotation=90, ha="center", va="center", fontsize=9)
    handles = [Line2D([], [], color=PHASE_THREAD[k], lw=1.4, label=k) for k in ("frame", "radials", "auxiliary", "capture")]
    handles.append(Line2D([], [], color="black", marker="x", lw=0, label="missed attachment (endpoint)"))
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8, bbox_to_anchor=(0.5, -0.05))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.88, bottom=0.08, wspace=0.08, hspace=0.42)
    save(fig, out("v1_webs_six_policies"))


def fig_timeseries():
    fig, axes = plt.subplots(3, 2, figsize=(7.0, 5.4), sharex="col",
                             gridspec_kw={"height_ratios": [0.7, 1.3, 1.2]})
    for col, case in enumerate((6, 4)):
        a, f = CASES[case]
        ph = trial_row(case, 0, "local").initial_phase_rad
        tmax = max(trial_row(case, 0, p).elapsed_s for p in ORDER)
        t = np.linspace(0, tmax, 4000)
        axes[0, col].plot(t, a * np.sin(2 * math.pi * f * t + ph), color=C["black"], lw=0.7)
        axes[0, col].set_ylabel("bottom-edge\ndisplacement (cm)", fontsize=7.5)
        axes[0, col].text(0.01, 1.04, f"{a:g} cm, {f:g} Hz, seed 0", transform=axes[0, col].transAxes, fontsize=8)
        for p in ORDER:
            ev = load_trace(PILOT / f"trace_{case}_0_{p}.json")
            acts = [e for e in ev if e["event"] == "action"]
            times = [0] + [e["time_s"] for e in acts if e["accepted"]]
            axes[1, col].step(times, range(len(times)), where="post", color=POLICY_COLORS[p], lw=1.0, label=p)
            tm = [e["time_s"] for e in acts if not e["accepted"]]
            em = [e["error_cm"] for e in acts if not e["accepted"]]
            ta = [e["time_s"] for e in acts if e["accepted"]]
            ea = [max(e["error_cm"], 1e-4) for e in acts if e["accepted"]]
            axes[2, col].scatter(ta, ea, s=3, color=POLICY_COLORS[p], lw=0, alpha=0.6)
            axes[2, col].scatter(tm, em, s=14, marker="x", color=POLICY_COLORS[p], lw=0.8)
        axes[1, col].set_ylabel("accepted actions", fontsize=8)
        axes[1, col].axhline(TOTAL_ACTIONS, color=C["grey"], ls="--", lw=0.6)
        axes[2, col].axhline(0.5, color=C["grey"], ls="--", lw=0.7)
        axes[2, col].set_yscale("log")
        axes[2, col].set_ylim(5e-5, 30)
        axes[2, col].set_ylabel("attachment error (cm)\n(0 plotted at 1e-4)", fontsize=7.5)
        axes[2, col].set_xlabel("simulated time (s)")
    axes[1, 0].legend(fontsize=6.5, loc="upper left", ncol=2)
    handles = [Line2D([], [], marker="o", color="black", lw=0, ms=2.5, label="accepted attempt"),
               Line2D([], [], marker="x", color="black", lw=0, label="missed attempt")]
    axes[2, 1].legend(handles=handles, fontsize=6.5, loc="upper right")
    fig.tight_layout()
    save(fig, out("v1_trial_timeseries"))


def fig_world_snapshots():
    case, seed, p = 6, 0, "local_repair"
    a, f = CASES[case]
    r = trial_row(case, seed, p)
    assert r.success
    ph = r.initial_phase_rad
    ev = load_trace(PILOT / f"trace_{case}_{seed}_{p}.json")
    fracs = [0.1, 0.35, 0.6, 1.0]
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 1.95))
    for ax, fr in zip(axes, fracs):
        t = fr * r.elapsed_s
        d = a * math.sin(2 * math.pi * f * t + ph)
        frame = np.array([(0, 30), (30, 30), (30 + d, 0), (0 + d, 0), (0, 30)])
        ax.plot(frame[:, 0], frame[:, 1], color=C["grey"], lw=0.8, ls="--")
        ax.plot([0, 30], [30, 30], color="black", lw=2.2, solid_capstyle="butt")   # fixed top support
        ax.plot([d, 30 + d], [0, 0], color=C["vermillion"], lw=2.2, solid_capstyle="butt")  # moving bottom
        draw_web(ax, ev, t_max=t, world=(a, f, ph, t), failed=False)
        ax.set_xlim(-11.5, 41.5)
        ax.set_ylim(-1.5, 31.5)
        done = sum(1 for e in ev if e["event"] == "action" and e["accepted"] and e["time_s"] <= t)
        ax.set_title(f"t = {t:.0f} s, d = {d:+.1f} cm\n{done}/218 accepted", fontsize=7)
    handles = [Line2D([], [], color=PHASE_THREAD[k], lw=1.4, label=k) for k in ("frame", "radials", "auxiliary", "capture")]
    handles += [Line2D([], [], color="black", lw=2, label="fixed top support"),
                Line2D([], [], color=C["vermillion"], lw=2, label="moving bottom support")]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=6.5, bbox_to_anchor=(0.5, -0.02))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.8, bottom=0.12, wspace=0.05)
    save(fig, out("v1_world_snapshots"))


if __name__ == "__main__":
    fig_web_grid()
    fig_timeseries()
    fig_world_snapshots()
