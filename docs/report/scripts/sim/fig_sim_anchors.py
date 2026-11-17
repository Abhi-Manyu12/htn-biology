"""Figure 6: anchor availability. (top) seeded removal exactly as stochastic.select_available_anchors draws it, at
increasing removal probability, for the config seed 7107 and seed 4; threads on removed anchors are not built (no
replanning). Figure 6b: structural failure after construction (an anchor detaches, perturbations.py).
Data: work/sim/data/anchors.json (collect_sim_data.py)."""
from simplot import *
apply()
d = load("anchors")
_src = open(os.path.join(W, "repo", "htn-biology", "visualization", "plan_data_updated.js")).read()
R = {"nodes": json.loads(_src[_src.index("{"):_src.rindex("}") + 1])["node_coords"]}
fig, axs = plt.subplots(2, 4, figsize=(7.0, 5.0), sharex=True, sharey=True)
for ax, r in zip(axs.flat, d["drops"]):
    draw_web(ax, r["th"], d["rig"], lw_scale=0.8, removed_pts=[R["nodes"][n] for n in r["removed"]], spider=r["m"]["spider_xy_cm"])
    web_axes(ax, ylim=(-6.0, 19)); ax.set_yticks([0, 6, 12, 18]); ax.set_xticks([0, 8, 16])
    panel(ax, "", f"seed {r['seed']}, $p$ = {r['p']}")
    short = ", ".join(n.replace("anchor_", "").replace("_", " ") for n in r["removed"])
    import textwrap
    ax.text(8, -3.2, "\n".join(textwrap.wrap("removed: " + short, 28)), ha="center", va="center", fontsize=6.6)
for ax in axs[1]: ax.set_xlabel("$x$ (cm)")
for ax in axs[:, 0]: ax.set_ylabel("$y$ (cm)")
type_legend(fig, [t for t in TYPES if t != "dragline"], y=0.0, ncol=9, extra=[Line2D([], [], ls="none", marker="s", ms=4.5, mfc="white", mec="k", label="removed anchor")])
fig.subplots_adjust(bottom=0.15, top=0.95, left=0.07, right=0.99, wspace=0.06, hspace=0.16)
save(fig, os.path.join(FIG, "sim_anchor_removal"))

fig, axs = plt.subplots(1, 2, figsize=(5.4, 3.2), sharey=True)
dl, dr = d["detach"]
for ax, src, txt, tag in [(axs[0], dl, "bottom-left anchor lets go", "a"), (axs[1], dr, "right-lower anchor lets go", "b")]:
    for t in src["before"]["th"]:
        ax.plot([p[0] for p in t["pts"]], [p[1] for p in t["pts"]], color="#D9D9D9", lw=0.5, zorder=2)
    draw_web(ax, src["after"]["th"], d["rig"], lw_scale=0.85, spider=src["after"]["m"]["spider_xy_cm"])
    ax.plot(*R["nodes"][src["anchor"]], ls="none", marker="s", ms=4.5, mfc="white", mec="k", mew=0.7, zorder=5)
    web_axes(ax); ax.set_xlabel("$x$ (cm)"); panel(ax, tag, txt)
axs[0].set_ylabel("$y$ (cm)")
fig.subplots_adjust(bottom=0.15, top=0.92, left=0.09, right=0.99, wspace=0.07)
save(fig, os.path.join(FIG, "sim_detach"))
for x in d["detach"]:
    print(x["anchor"], "hub before", x["before"]["m"]["hub_xy_cm"], "after", x["after"]["m"]["hub_xy_cm"], "Tmax before %.3f after %.3f" % (x["before"]["m"]["max_tension"]["mN"], x["after"]["m"]["max_tension"]["mN"]), x["after"]["settle"])
for r in d["drops"]:
    print(r["seed"], r["p"], len(r["th"]), "threads", r["removed"], "hub", [round(v, 2) for v in r["m"]["hub_xy_cm"]], "sag %.2f" % r["m"]["max_sag"]["cm"])
