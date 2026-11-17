"""Figure 4: sag and tension against the modelled factors (static equilibria of the finished web, spider load off),
plus the tension distribution by thread type and a tension-coloured web.
Data: work/sim/data/sweeps.json and web_states.json (collect_sim_data.py)."""
from simplot import *
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.collections import LineCollection
apply()
d = load("sweeps"); ws = load("web_states")


def disp_stats(th, base):
    """max and mean node displacement (cm) of a state relative to a baseline state (same threads, same node order)."""
    bt = {t["id"]: np.array(t["pts"]) for t in base}
    dmax, dx = 0.0, []
    for t in th:
        p = np.array(t["pts"]); q = bt[t["id"]]
        dd = np.hypot(*(p - q).T); dmax = max(dmax, dd.max()); dx.extend((p - q)[:, 0])
    return dmax, float(np.mean(dx))


fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.9))
# (a) wind
ax = axs[0]
for dirn, col, lab in [(0, C["blue"], "horizontal ($+x$)"), (270, C["vermillion"], "downward ($-y$)")]:
    rows = [r for r in d["wind"] if r["dir"] == dirn]; base = rows[0]["th"]
    u = [r["u"] for r in rows]
    ax.plot(u, [disp_stats(r["th"], base)[0] for r in rows], marker="o", ms=3, color=col)
    ax.plot(u, [r["m"]["max_sag"]["cm"] for r in rows], marker="s", ms=2.6, color=col, ls="--", lw=0.9)
hs = [Line2D([], [], color=C["blue"], lw=1.4, label="wind towards $+x$"), Line2D([], [], color=C["vermillion"], lw=1.4, label="wind towards $-y$"),
      Line2D([], [], color="k", marker="o", ms=3, label="max node displacement"), Line2D([], [], color="k", ls="--", marker="s", ms=2.6, lw=0.9, label="max thread sag")]
ax.set_xlabel("mean wind speed $U$ (m/s)"); ax.set_ylabel("cm"); ax.legend(handles=hs, fontsize=7, loc="upper left", ncol=1); ax.set_ylim(-0.05, 2.3)
panel(ax, "a", "wind (steady, no gusts)")
# (b) slack
ax = axs[1]
rows = d["slack"]; sl = [r["slack"] for r in rows]
ax.plot(sl, [r["m"]["max_sag"]["cm"] for r in rows], marker="o", ms=3, color="k", label="max thread sag")
def thread_sag(r, a, b, ty):
    return [t["sag_cm"] for t in r["per"] if t["type"] == ty and {t["a"], t["b"]} == {a, b}][0]
ax.plot(sl, [thread_sag(r, "anchor_left_lower", "anchor_right_lower", "frame") for r in rows], marker="s", ms=2.6, color=C["grey"], label="bottom frame (16 cm)")
ax.plot(sl, [thread_sag(r, "left_stick_mid", "right_stick_top", "bridge") for r in rows], marker="^", ms=2.6, color=C["orange"], label="diagonal bridge (17.1 cm)")
ax2 = ax.twinx(); ax2.plot(sl, [r["m"]["max_tension"]["mN"] for r in rows], color=C["blue"], lw=0.9, ls=":", marker="x", ms=3)
ax2.set_ylabel("max tension (mN), dotted", color=C["blue"]); ax2.tick_params(axis="y", colors=C["blue"]); ax2.spines["right"].set_visible(True); ax2.grid(False)
ax.set_xlabel("slack of every thread type (%)"); ax.set_ylabel("sag (cm)"); ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0.0, 1.0)); ax.set_ylim(0, 3.1)
panel(ax, "b", "slack ($<0$: pretension)")
# (c) weight: exaggeration X and gravity g collapse onto X g / 9.81
ax = axs[2]
xe = np.array([r["exag"] for r in d["exag"]]); se = np.array([r["m"]["max_sag"]["cm"] for r in d["exag"]])
gg = np.array([r["g"] for r in d["g"] if r["g"] > 0]); sg = np.array([r["m"]["max_sag"]["cm"] for r in d["g"] if r["g"] > 0])
ax.loglog(xe, se, marker="o", ms=3, color="k", label="vary $X$ ($g$ = 9.81)")
ax.loglog(2000 * gg / 9.81, sg, ls="none", marker="s", ms=4, mfc="none", color=C["vermillion"], label="vary $g$ ($X$ = 2000)")
fr = [[t["sag_cm"] for t in r["per"] if t["type"] == "frame" and {t["a"], t["b"]} == {"anchor_left_lower", "anchor_right_lower"}][0] for r in d["exag"]]
ax.loglog(xe, fr, marker="^", ms=2.6, color=C["grey"], label="bottom frame")
ref = xe[xe >= 100]; ax.loglog(ref, fr[list(xe).index(1000)] * (ref / 1000) ** (1 / 3), color="k", lw=0.6, ls="--", label="$\\propto (Xg)^{1/3}$")
ax.set_xlabel("weight factor $X g / 9.81$"); ax.set_ylabel("sag (cm)"); ax.legend(fontsize=7, loc="upper left"); ax.set_ylim(0.02, 12)
ax.axvline(2000, color=C["grey"], lw=0.5); panel(ax, "c", "silk weight")
fig.tight_layout(w_pad=0.8)
save(fig, os.path.join(FIG, "sim_sag_sweeps"))

# ---- tension: distribution by type + tension-coloured web (default, spider off) ----
st = ws["gravity_nospider"]
fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.6), gridspec_kw={"width_ratios": [1.0, 1.05]})
ax = axs[0]
types = [t for t in TYPES if any(p["type"] == t for p in st["per"])]
rng = np.random.default_rng(0)
for i, ty in enumerate(types):
    v = np.array([p["T_max_mN"] for p in st["per"] if p["type"] == ty]); x = i + rng.uniform(-0.18, 0.18, len(v))
    ax.semilogy(x, v, ls="none", marker="o", ms=3, mfc="none", color=color(ty))
    ax.plot([i - 0.28, i + 0.28], [np.median(v)] * 2, color="k", lw=1.0)
    ax.text(i, 1.5, f"$n$ = {len(v)}", ha="center", va="bottom", fontsize=6.5)
ax.set_xticks(range(len(types))); ax.set_xticklabels([LABEL[t].replace(" ", "\n") for t in types], fontsize=7)
ax.set_ylabel("per-thread maximum tension (mN)"); ax.set_ylim(1e-3, 3); ax.set_xlim(-0.6, len(types) - 0.4)
panel(ax, "a", "tension by thread type (bar = median)")
ax = axs[1]
draw_rig(ax, ws["rig"])
segs, vals = [], []
for t in st["th"]:
    p = t["pts"]
    for j, T in enumerate(t["T_mN"]):
        segs.append([p[j], p[j + 1]]); vals.append(T)
vals = np.array(vals); hi = vals.max(); lo = hi / 1000
norm = LogNorm(vmin=lo, vmax=hi); cmap = plt.get_cmap("OrRd")
cols = [cmap(0.25 + 0.75 * norm(max(v, lo))) if v > lo else (0.81, 0.81, 0.81, 1) for v in vals]
ax.add_collection(LineCollection(segs, colors=cols, linewidths=1.0, zorder=3, capstyle="round"))
web_axes(ax); ax.set_xlabel("$x$ (cm)"); ax.set_ylabel("$y$ (cm)")
from matplotlib.colors import ListedColormap
cm2 = ListedColormap(cmap(np.linspace(0.25, 1, 256)))
sm = plt.cm.ScalarMappable(norm=norm, cmap=cm2); cb = fig.colorbar(sm, ax=ax, fraction=0.05, pad=0.03); cb.set_label("segment tension (mN)")
panel(ax, "b", "tension-coloured web")
fig.tight_layout(w_pad=1.0)
save(fig, os.path.join(FIG, "sim_tension"))
print("slack-free fraction of segments below 1e-3 Tmax:", float(np.mean(vals <= lo)), "Tmax", hi)
for ty in types:
    v = np.array([p["T_max_mN"] for p in st["per"] if p["type"] == ty]); print(ty, len(v), "median", np.median(v), "max", v.max())
