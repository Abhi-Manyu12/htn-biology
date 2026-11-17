"""Figure 5: moving supports (affine shear of spider_web_mulder/model.py applied to the 16 x 18 cm rig).
Data: work/sim/data/supports.json (collect_sim_data.py)."""
from simplot import *
import numpy as np
apply()
d = load("supports")
run = [r for r in d["runs"] if r["amp"] == 10 and r["freq"] == 0.05][0]
fig = plt.figure(figsize=(7.0, 6.6))
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.05], hspace=0.5, wspace=0.16)
labels = ["$t$ = 0 s, phase 0$^\\circ$", "$t$ = 5 s, 90$^\\circ$", "$t$ = 10 s, 180$^\\circ$", "$t$ = 15 s, 270$^\\circ$"]
for i, s in enumerate(run["snaps"]):
    ax = fig.add_subplot(gs[i // 2, i % 2])
    draw_web(ax, s["th"], d["rig"], amp=10, freq=0.05, t=s["t"], lw_scale=0.9, spider=s["m"]["spider_xy_cm"])
    web_axes(ax, xlim=(-11, 27), ylim=(-1, 19), ticks=False); ax.set_xticks([-10, -5, 0, 5, 10, 15, 20, 25]); ax.set_yticks([0, 6, 12, 18])
    if i % 2 == 0: ax.set_ylabel("$y$ (cm)")
    if i >= 2: ax.set_xlabel("$x$ (cm)")
    m = s["m"]
    panel(ax, "abcd"[i], f"{labels[i]}; $T_{{\\max}}$ {m['max_tension']['mN']:.1f} mN, strain {m['max_strain']['pct']:.0f}%")
ax = fig.add_subplot(gs[2, 0])
for r, col, ls, lab in [(run, C["blue"], "-", "$A$ = 10 cm, $f$ = 0.05 Hz"), ([x for x in d["runs"] if x["amp"] == 5][0], C["green"], "-", "$A$ = 5 cm, $f$ = 0.05 Hz"),
                        ([x for x in d["runs"] if x["freq"] == 0.1][0], C["vermillion"], (0, (3, 3)), "$A$ = 10 cm, $f$ = 0.1 Hz")]:
    t = np.array([p["t"] for p in r["series"]]) * r["freq"]
    ax.plot(t, [p["T"] for p in r["series"]], color=col, lw=1.1, ls=ls, label=lab)
ax.set_xlabel("time / period, $tf$"); ax.set_ylabel("max tension (mN)"); ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=1)
ax.set_ylim(0, 30); panel(ax, "e", "maximum tension")
ax = fig.add_subplot(gs[2, 1])
t = np.array([p["t"] for p in run["series"]]) * 0.05
ax.plot(t, [p["disp"] for p in run["series"]], color=C["grey"], lw=0.9, label="bottom-bar shift (cm)")
ax.plot(t, [p["hub"][0] - 8 for p in run["series"]], color=C["blue"], lw=1.1, label="hub $\\Delta x$ (cm)")
ax.plot(t, [p["sag"] for p in run["series"]], color=C["vermillion"], lw=1.1, label="max thread sag (cm)")
ax.plot(t, [p["strain"] / 10 for p in run["series"]], color="k", lw=0.9, ls="--", label="max strain / 10 (%)")
ax.set_xlabel("time / period, $tf$"); ax.set_ylabel("cm, or % / 10"); ax.legend(fontsize=7, loc="lower left", ncol=2); ax.set_ylim(-19, 12)
panel(ax, "f", "$A$ = 10 cm, $f$ = 0.05 Hz")
fig.subplots_adjust(top=0.96, bottom=0.07, left=0.08, right=0.99)
save(fig, os.path.join(FIG, "sim_moving_supports"))
for r in d["runs"]:
    print(r["amp"], r["freq"], "max T %.2f" % max(p["T"] for p in r["series"]), "max strain %.1f" % max(p["strain"] for p in r["series"]),
          "max KE %.2e" % max(p["KE"] for p in r["series"]), "hub dx range %.2f..%.2f" % (min(p["hub"][0] for p in r["series"]) - 8, max(p["hub"][0] for p in r["series"]) - 8),
          "max sag %.2f" % max(p["sag"] for p in r["series"]), "Ttype", {p["Ttype"] for p in r["series"]})
