"""Event timeline of the worked recovery example (permanent_anchor; 4 sectors, depth 0, 10 cm; seed 0).

(a) retained IPyHOP: docs/research/evidence/recovery_example/events.json (identical to
    mulder_results/recovery_v1_verified/traces/case1_permanent_anchor_ipyhop/events.json).
(b) same case, last 35 s, all four back-ends: traces/case1_permanent_anchor_<backend>/events.json.
Output: rec_event_timeline
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from _common import BACKENDS, EVID, OUT, REC, load_json, plotstyle

C = plotstyle.C
ACOL = {"move": C["sky"], "attach": C["green"], "capture": C["orange"]}
BC = plotstyle.BACKEND_COLORS
LAB = {"fresh_root": "fresh_root", "component": "component", "ipyhop_fresh": "ipyhop_fresh",
       "ipyhop": "ipyhop (retained)"}


def owner_of(a):
    o = a[-1]
    return f"{'R' if o[0] == 'radius' else 'C'}{o[1]}"


def main():
    plotstyle.apply()
    ev = load_json(EVID / "recovery_example" / "events.json")
    fig, (ax, sil, bx) = plt.subplots(3, 1, figsize=(7.0, 6.0),
                                      gridspec_kw=dict(height_ratios=[1.3, 0.45, 1], hspace=0.55))
    lanes = ["R0", "R1", "R2", "R3", "C0", "C1", "C2", "C3"]
    y = {k: i for i, k in enumerate(lanes)}
    replan_t = None
    for e in ev:
        if e["event"] == "replan":
            replan_t = e["observed_state"]["clock_s"]
            rp = e
            continue
        if e["event"] != "action":
            continue
        t0, t1 = e["before"]["clock_s"], e["after"]["clock_s"]
        yy = y[owner_of(e["action"])]
        col = ACOL[e["action"][0]]
        ax.plot([t0, t1], [yy, yy], color=col, lw=6, solid_capstyle="butt")
        if e["action"][0] != "move" or not e["accepted"]:
            lab = {"attach": f"attach {e['action'][2]}", "capture": f"{e['action'][2]},{e['action'][3]}"}.get(
                e["action"][0], "")
            ha = "right" if not e["accepted"] else ("left" if e["action"][0] == "attach" else "center")
            dx = -0.8 if not e["accepted"] else (0.8 if e["action"][0] == "attach" else 0)
            if e["action"][0] == "capture":
                ha, dx = "right", -0.8
            ax.text(t1 + dx if ha != "center" else (t0 + t1) / 2, yy - 0.3, lab, ha=ha, va="bottom", fontsize=7)
        if not e["accepted"]:
            ax.plot(t1, yy, "X", color=C["vermillion"], ms=8, mec="white", mew=0.4, zorder=5)
    ax.axvline(replan_t, color="black", lw=0.8, ls="--")
    ax.text(10, 6.5, f"replan(observed state, failed node {rp['failed_node']}):\n"
            f"{rp['old_remaining_actions']} queued actions replaced by {rp['new_remaining_actions']}; "
            "R3 primary$\\to$backup,\ncapture C0 and C3 re-bound from A3 to B3",
            ha="left", va="center", fontsize=7.4, bbox=dict(fc="white", ec="#999", lw=0.5, pad=2))
    ax.annotate("", xy=(replan_t, 6.0), xytext=(76.5, 6.3), arrowprops=dict(arrowstyle="->", lw=0.6, color="#555"))
    ax.set_yticks(range(len(lanes)), lanes)
    ax.set_ylim(len(lanes) - 0.4, -1.1)
    ax.set_ylabel("task owner")
    ax.set_xlim(-3, 163)
    ax.grid(axis="y", visible=False)
    ts = [0] + [e["after"]["clock_s"] for e in ev if e["event"] == "action"]
    ss = [500.0] + [e["after"]["silk_remaining"] for e in ev if e["event"] == "action"]
    sil.step(ts, ss, where="post", color="#555", lw=0.9)
    sil.set_ylabel("silk left\n(cm)")
    sil.set_xlim(-3, 163)
    sil.set_ylim(415, 505)
    sil.axvline(replan_t, color="black", lw=0.8, ls="--")
    sil.set_xlabel("simulated clock (s)")
    ax.text(0, 1.02, "(a) retained IPyHOP, whole trial", transform=ax.transAxes, fontsize=8.5)

    # (b) all back-ends, end of the run
    for i, b in enumerate(BACKENDS):
        evb = load_json(REC / "traces" / f"case1_permanent_anchor_{b}" / "events.json")
        for e in evb:
            if e["event"] == "replan":
                t = e["observed_state"]["clock_s"]
                bx.plot([t, t], [i - 0.38, i + 0.38], color="black", lw=1.2)
            elif e["event"] == "action":
                t0, t1 = e["before"]["clock_s"], e["after"]["clock_s"]
                if t1 < 125:
                    continue
                bx.plot([t0, t1], [i, i], color=ACOL[e["action"][0]], lw=7, solid_capstyle="butt")
                if not e["accepted"]:
                    bx.plot(t1, i, "X", color=C["vermillion"], ms=7.5, mec="white", mew=0.4, zorder=5)
                    if e["reason"] == "stale_precondition":
                        bx.text(t1 + 0.15, i - 0.32, "stale", fontsize=7, color=C["vermillion"])
    bx.set_yticks(range(4), [LAB[b] for b in BACKENDS])
    for tl, b in zip(bx.get_yticklabels(), BACKENDS):
        tl.set_color(BC[b])
    bx.set_ylim(3.6, -0.6)
    bx.set_xlim(125, 160.5)
    bx.set_xlabel("simulated clock (s)")
    bx.grid(axis="y", visible=False)
    bx.text(0, 1.02, "(b) same case, all back-ends, t > 125 s", transform=bx.transAxes, fontsize=8.5)
    hs = [Patch(color=ACOL[k], label=k) for k in ("move", "attach", "capture")]
    hs += [Line2D([], [], ls="", marker="X", color=C["vermillion"], ms=7, label="failed attempt"),
           Line2D([], [], color="black", lw=1.2, label="re-planning call"),
           Line2D([], [], color="#555", lw=0.9, label="silk remaining")]
    fig.legend(handles=hs, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.02), fontsize=7.5)
    plotstyle.save(fig, str(OUT / "rec_event_timeline"))


if __name__ == "__main__":
    main()
