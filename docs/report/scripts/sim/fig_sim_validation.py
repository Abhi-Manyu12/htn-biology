"""Figure 3: validation of the cable solver on one span against the analytic elastic catenary, the rigid catenary
y = a cosh(x/a) and the parabola d = wL^2/(8H). Data: work/sim/data/validation.json (collect_sim_data.py)."""
from simplot import *
import numpy as np
apply()
d = load("validation"); b = d["base"]
fig, axs = plt.subplots(2, 2, figsize=(7.0, 5.4))
# (a) shape at 3 % slack, N = 16
s = d["shape_3_16"]
ax = axs[0, 0]
el = np.array(s["curves"]["elastic"]); rg = np.array(s["curves"]["rigid"]); pa = np.array(s["curves"]["parabola"]); sim = np.array(s["sim"])
ax.plot(el[:, 0], el[:, 1], color="k", lw=1.2, label="elastic catenary (exact)")
ax.plot(rg[:, 0], rg[:, 1], color=C["blue"], lw=1.0, ls=(0, (5, 3)), label="$a\\cosh(x/a)$, $a = H/w$")
ax.plot(pa[:, 0], pa[:, 1], color=C["vermillion"], lw=1.0, ls=(0, (1, 1.5)), label="parabola, $d = wL^2/8H$")
ax.plot(sim[:, 0], sim[:, 1], ls="none", marker="s", ms=2.8, color="k", label="simulated nodes, $N$ = 16")
ax.set_xlabel("$x$ (cm)"); ax.set_ylabel("$y$ (cm)"); ax.legend(loc="upper center", fontsize=7, bbox_to_anchor=(0.5, 0.98))
ax.set_ylim(-2.2, 1.6); panel(ax, "a", f"16 cm span, slack 3%, sag {s['sag']:.3f} cm")
# (b) deviation from the exact curve, slack 3 %, N = 16 and 40
ax = axs[0, 1]
interp = lambda x: np.interp(x, el[:, 0], el[:, 1])
ax.plot(rg[:, 0], (rg[:, 1] - interp(rg[:, 0])) * 1e4, color=C["blue"], lw=1.0, ls=(0, (5, 3)), label="$a\\cosh(x/a)$ $-$ exact")
ax.plot(pa[:, 0], (pa[:, 1] - interp(pa[:, 0])) * 1e4, color=C["vermillion"], lw=1.0, ls=(0, (1, 1.5)), label="parabola $-$ exact")
for key, mk, lab in [("shape_3_16", "s", "simulation $-$ exact, $N$ = 16"), ("shape_3_40", "o", "simulation $-$ exact, $N$ = 40")]:
    r = np.array(d[key]["resid_um"])
    ax.plot(r[:, 0], r[:, 1], ls="-", lw=0.6, marker=mk, ms=2.4, mfc="white" if mk == "o" else "k", color="k", label=lab)
ax.axhline(0, color="k", lw=0.5)
ax.set_xlabel("$x$ (cm)"); ax.set_ylabel("$\\Delta y$ ($\\mu$m)"); ax.legend(fontsize=6.8, loc="upper center", bbox_to_anchor=(0.5, 0.86))
panel(ax, "b", "vertical deviation from the elastic catenary")
# (c) convergence with N
ax = axs[1, 0]
for sl, col in [(0, C["blue"]), (1, C["green"]), (5, C["vermillion"])]:
    rows = [r for r in d["conv"] if r["slack"] == sl]
    N = np.array([r["N"] for r in rows]); e = np.array([r["err_cm"] for r in rows]) * 1e4
    ax.loglog(N, e, marker="o", ms=3.2, color=col, label=f"slack {sl}%")
N = np.array([4, 256]); ax.loglog(N, 300 * (N / 4.0) ** -2, color="k", lw=0.7, ls="--", label="$\\propto N^{-2}$")
ax.set_xlabel("segments per span $N$"); ax.set_ylabel("max $|x_{sim} - x_{exact}|$ ($\\mu$m)"); ax.legend(fontsize=7)
ax.set_xticks([4, 16, 64, 256]); ax.set_xticklabels(["4", "16", "64", "256"])
panel(ax, "c", "discretisation error, 16 cm span")
# (d) model error vs slack at N = 40
ax = axs[1, 1]
rows = d["slack"]; sl = np.array([r["slack"] for r in rows])
ax.semilogy(sl, np.array([r["err_sim_cm"] for r in rows]) * 1e4, marker="s", ms=3, color="k", label="simulation, $N$ = 40")
ax.semilogy(sl, np.array([r["err_par_cm"] for r in rows]) * 1e4, marker="o", ms=3, color=C["vermillion"], label="parabola")
ax.semilogy(sl, np.array([r["err_rigid_cm"] for r in rows]) * 1e4, marker="^", ms=3, color=C["blue"], label="$a\\cosh(x/a)$")
ax2 = ax.twinx(); ax2.plot(sl, [r["sag_exact"] for r in rows], color=C["grey"], lw=0.8, ls=":"); ax2.set_ylabel("exact sag (cm), dotted", color=C["grey"]); ax2.spines["right"].set_visible(True); ax2.grid(False)
ax2.tick_params(axis="y", colors=C["grey"])
ax.set_xlabel("slack (rest length / span $-$ 1, %)"); ax.set_ylabel("max deviation from exact ($\\mu$m)"); ax.legend(fontsize=7, loc="lower right")
panel(ax, "d", "error against slack (negative = pretension)")
fig.tight_layout(h_pad=1.6, w_pad=1.2)
save(fig, os.path.join(FIG, "sim_validation"))
r40 = [r for r in d["slack"] if r["slack"] == 0][0]
print("N=40, slack 0: err", r40["err_sim_cm"] * 1e4, "um of sag", r40["sag_exact"], "cm; X=1 sag", d["x1"])
