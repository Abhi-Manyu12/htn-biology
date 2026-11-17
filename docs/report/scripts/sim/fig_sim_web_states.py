"""Figure 1: finished web -- straight-line plan vs gravity vs gravity + wind (same scale).
Data: work/sim/data/web_states.json (collect_sim_data.py, page simulation/orb_web_sim.html)."""
from simplot import *
apply()
d = load("web_states")
fig, axs = plt.subplots(1, 3, figsize=(7.0, 3.35), sharey=True)
cases = [("plan", "a", "straight-line plan, $g$ = 0"), ("gravity", "b", "gravity, $X$ = 2000"), ("wind4", "c", "gravity + wind 4 m/s in $+x$")]
for ax, (k, tag, txt) in zip(axs, cases):
    s = d[k]
    draw_web(ax, s["th"], d["rig"], spider=s["m"]["spider_xy_cm"] if k != "plan" else None)
    web_axes(ax); panel(ax, tag, txt)
    ax.set_xlabel("$x$ (cm)")
    m = s["m"]
    ax.text(0.5, -0.30, f"max thread sag {m['max_sag']['cm']:.2f} cm, hub at ({m['hub_xy_cm'][0]:.2f}, {m['hub_xy_cm'][1]:.2f})", transform=ax.transAxes, ha="center", va="top", fontsize=7)
axs[0].set_ylabel("$y$ (cm)")
type_legend(fig, [t for t in TYPES if t != "dragline"], y=-0.04, ncol=8, extra=[Line2D([], [], ls="none", marker="D", ms=3.4, color="k", label="spider (30 mg)")])
fig.subplots_adjust(bottom=0.27, wspace=0.08, top=0.93, left=0.07, right=0.99)
save(fig, os.path.join(FIG, "sim_web_states"))
