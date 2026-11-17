"""Figure 2: quasi-static sequential construction under gravity -- the web at the end of each macro phase.
Data: work/sim/data/phases.json (collect_sim_data.py)."""
from simplot import *
apply()
d = load("phases")
NAMES = {"exploration": "Exploration & bridging", "proto_hub": "Proto-hub establishment", "frame": "Frame construction",
         "radii": "Radii construction", "auxiliary_spiral": "Auxiliary spiral", "capture_spiral": "Capture spiral", "complete": "Finalisation"}
snaps = [s for s in d["snaps"] if s["phase"] != "complete"]   # 'complete' adds no thread
fig, axs = plt.subplots(2, 3, figsize=(7.0, 5.9), sharex=True, sharey=True)
for i, (ax, s) in enumerate(zip(axs.flat, snaps)):
    draw_web(ax, s["th"], d["rig"], spider=s["m"]["spider_xy_cm"])
    web_axes(ax, ylim=(-3.6, 19)); ax.set_yticks([0, 6, 12, 18])
    m = s["m"]
    panel(ax, "abcdef"[i], f"{NAMES[s['phase']]}, after step {s['k']}")
    ax.text(8, -2.1, f"{len(s['th'])} threads, max sag {m['max_sag']['cm']:.2f} cm, $T_{{\\max}}$ {m['max_tension']['mN']:.2f} mN", ha="center", va="center", fontsize=6.6)
for ax in axs[1]: ax.set_xlabel("$x$ (cm)")
for ax in axs[:, 0]: ax.set_ylabel("$y$ (cm)")
type_legend(fig, TYPES, y=0.0, ncol=9, extra=[Line2D([], [], ls="none", marker="D", ms=3.4, color="k", label="spider")])
fig.subplots_adjust(bottom=0.1, wspace=0.06, hspace=0.12, top=0.96, left=0.07, right=0.99)
save(fig, os.path.join(FIG, "sim_construction_phases"))
print("worst settle residual over all 105 steps:", d["worst_residual"], "unconverged:", d["unconverged"])
