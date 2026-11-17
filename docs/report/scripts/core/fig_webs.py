"""Simulated webs drawn from plan data: final webs of the three plans, and the updated plan's build-up strip.

Sources: visualization/plan_data.js and visualization/plan_data_updated.js (committed, 61d18d8) and
work/core/derived/plan_checkpoint2_39b89f3.json (export_plan.py re-run at 39b89f3, stochastic disabled).
"""
import matplotlib.pyplot as plt

from _common import FIG, PHASE_KEYS, PHASE_LABEL, draw_web, plans, web_legend_handles
import plotstyle

plotstyle.apply()

# --- 1. final webs, three plans side by side ------------------------------------------------------------
P = plans()
fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.25))
used = set()
for ax, (label, key, plan) in zip(axes, P):
    u, th = draw_web(ax, plan)
    used |= u
    ax.set_title(f"{label}\n{plan['total_steps']} actions, {plan['total_energy']:.1f} cm", fontsize=8)
    ax.set_xlabel("x (cm)", fontsize=7.5)
axes[0].set_ylabel("y (cm)", fontsize=7.5)
fig.subplots_adjust(wspace=0.08, bottom=0.17)
fig.legend(handles=web_legend_handles(used), loc="upper center", ncol=7, fontsize=7, bbox_to_anchor=(0.5, 0.06),
           handlelength=1.8, columnspacing=1.0)
plotstyle.save(fig, f"{FIG}/web_final_three_plans")

# --- 2. build-up strip for the updated plan: web after each macro phase ----------------------------------
label, key, upd = P[2]
steps = upd["steps"]
ends = []
for ph in PHASE_KEYS[:-1]:
    idx = max(i for i, s in enumerate(steps) if s["phase"] == ph)
    ends.append((ph, idx + 1))
SHORT = {"exploration": "Exploration", "proto_hub": "Proto-hub", "frame": "Frame", "radii": "Radii",
         "auxiliary_spiral": "Auxiliary spiral", "capture_spiral": "Capture spiral"}
fig, axes = plt.subplots(1, 6, figsize=(7.0, 1.95))
cum = 0
for ax, (ph, upto) in zip(axes, ends):
    u, th = draw_web(ax, upd, upto=upto, fontsize=6)
    e = steps[upto - 1]["cumulative_energy"]
    ax.set_title(f"{SHORT[ph]}\nstep {upto}, {e:.0f} cm", fontsize=6.6)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
fig.subplots_adjust(wspace=0.06, bottom=0.12)
fig.legend(handles=web_legend_handles(set(t for _, _, t in th)),
           loc="upper center", ncol=7, fontsize=6.6, bbox_to_anchor=(0.5, 0.13), handlelength=1.6,
           columnspacing=0.9)
plotstyle.save(fig, f"{FIG}/web_buildup_updated")
