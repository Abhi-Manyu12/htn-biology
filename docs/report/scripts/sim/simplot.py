"""Shared helpers for the sim figures: load collected page data, draw a simulated web with the shared style."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(W, "tools"))
from plotstyle import apply, save, C, THREAD_COLORS, PHASE_COLORS, FIG_1COL, FIG_WIDE, FIG_SQUARE, FIG_2PANEL, FIG_GRID  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

DATA = os.path.join(W, "work", "sim", "data")
FIG = os.path.join(W, "report", "figures", "sim")
TYPES = ["bridge", "dragline", "proto_radius", "frame", "radius", "auxiliary_spiral", "capture_spiral"]
LABEL = {"bridge": "bridge", "dragline": "dragline", "proto_radius": "proto-radius", "frame": "frame", "radius": "radius",
         "auxiliary_spiral": "auxiliary spiral", "capture_spiral": "capture spiral"}
KEY = {"auxiliary_spiral": "aux_spiral"}
LW = {"frame": 1.0, "radius": 0.85, "proto_radius": 0.85, "bridge": 0.7, "dragline": 0.7, "auxiliary_spiral": 0.6, "capture_spiral": 0.6}
ORDER = ["dragline", "bridge", "proto_radius", "auxiliary_spiral", "capture_spiral", "radius", "frame"]
RIGC = "#C4C4C4"


def color(ty):
    return THREAD_COLORS[KEY.get(ty, ty)]


def load(name):
    return json.load(open(os.path.join(DATA, name + ".json")))


def shear(x, y, amp, freq, t, H=18.0):
    import math
    return x + (1 - y / H) * amp * math.sin(2 * math.pi * freq * t)


def draw_rig(ax, rig, amp=0.0, freq=0.0, t=0.0):
    for (a, b) in rig["walkable"]:
        ax.plot([shear(a[0], a[1], amp, freq, t), shear(b[0], b[1], amp, freq, t)], [a[1], b[1]], color=RIGC, lw=2.2, solid_capstyle="butt", zorder=1)
    (a, b) = rig["crossbar"]
    ax.plot([shear(a[0], a[1], amp, freq, t), shear(b[0], b[1], amp, freq, t)], [a[1], b[1]], color="#9A9A9A", lw=0.6, ls=(0, (3, 3)), zorder=1)


def draw_web(ax, th, rig=None, amp=0.0, freq=0.0, t=0.0, lw_scale=1.0, removed_pts=(), spider=None, plan=False, anchors=True):
    if rig:
        draw_rig(ax, rig, amp, freq, t)
    for ty in ORDER:
        for tr in th:
            if tr["type"] != ty:
                continue
            xs = [p[0] for p in tr["pts"]]; ys = [p[1] for p in tr["pts"]]
            if plan:
                xs, ys = [xs[0], xs[-1]], [ys[0], ys[-1]]
            ax.plot(xs, ys, color=color(ty), lw=LW[ty] * lw_scale, solid_joinstyle="round", zorder=3)
    if anchors:
        ends = {}
        for tr in th:
            for p in (tr["pts"][0], tr["pts"][-1]):
                ends[(round(p[0], 6), round(p[1], 6))] = p
        rect = [p for p in ends.values() if on_rig(p, amp, freq, t)]
        if rect:
            ax.plot([p[0] for p in rect], [p[1] for p in rect], ls="none", marker="s", ms=2.2, color="k", zorder=4)
    for p in removed_pts:
        ax.plot([shear(p[0], p[1], amp, freq, t)], [p[1]], ls="none", marker="s", ms=4.5, mfc="white", mec="k", mew=0.7, zorder=5)
    if spider is not None:
        ax.plot([spider[0]], [spider[1]], ls="none", marker="D", ms=3.4, color="k", zorder=6)


def on_rig(p, amp, freq, t, eps=1e-4):
    x0 = p[0] - (shear(0, p[1], amp, freq, t))  # undo the shear
    return abs(p[1]) < eps or abs(p[1] - 18) < eps or abs(x0) < eps or abs(x0 - 16) < eps


def web_axes(ax, xlim=(-1, 17), ylim=(-1, 19), ticks=True):
    ax.set_aspect("equal")
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.grid(False)
    if ticks:
        ax.set_xticks(range(0, 17, 4)); ax.set_yticks(range(0, 19, 6))
    for s in ("top", "right"):
        ax.spines[s].set_visible(True)


def panel(ax, tag, text, y=1.015):
    ax.text(0.0, y, f"({tag}) {text}" if tag else text, transform=ax.transAxes, ha="left", va="bottom", fontsize=8)


def type_legend(fig, types=TYPES, y=0.0, ncol=7, extra=()):
    hs = [Line2D([], [], color=color(t), lw=1.4 if t != "frame" else 1.8, label=LABEL[t]) for t in types]
    hs += [Line2D([], [], color=RIGC, lw=2.2, label="rig")] + list(extra)
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.5, y), ncol=ncol, fontsize=7.5, handlelength=1.8, columnspacing=1.1)


def removed_coords(names, nodes):
    return [nodes[n] for n in names]
