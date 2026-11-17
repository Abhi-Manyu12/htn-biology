"""common.py -- shared loaders and the web-drawing helper for the astar_fap figures."""
import contextlib
import io
import json
import os
import sys
from collections import Counter

W = "<WORKSPACE>"
sys.path.insert(0, os.path.join(W, "tools"))
from plotstyle import C, THREAD_COLORS  # noqa: E402

REPO = os.path.join(W, "repo/htn-biology")          # read-only, for committed data files
CLONE = os.path.join(W, "work/astar_fap/repo")      # private clone (imports only)
RUNS = os.path.join(W, "work/astar_fap/data/runs.jsonl")
FIGDIR = os.path.join(W, "report/figures/astar_fap")

# repo thread-type name -> THREAD_COLORS key
TYPE_KEY = {"bridge": "bridge", "dragline": "dragline", "proto_radius": "proto_radius",
            "frame": "frame", "radius": "radius", "auxiliary_spiral": "aux_spiral",
            "capture_spiral": "capture_spiral", "y_frame": "frame", "loose_spoke": "radius",
            "stabilimentum": "stabilimentum"}
COLORS = dict(THREAD_COLORS, stabilimentum=C["green"])
LABELS = {"bridge": "bridge", "dragline": "dragline", "proto_radius": "proto-radius",
          "frame": "frame", "radius": "radius", "aux_spiral": "auxiliary spiral",
          "capture_spiral": "capture spiral", "stabilimentum": "stabilimentum"}
WIDTH = {"frame": 1.6, "radius": 1.3, "proto_radius": 1.3, "aux_spiral": 1.0,
         "capture_spiral": 1.0, "dragline": 0.9, "bridge": 1.2, "stabilimentum": 1.6}
ORDER = ["dragline", "bridge", "proto_radius", "frame", "radius", "aux_spiral",
         "capture_spiral", "stabilimentum"]


def load_js(path):
    t = open(path).read()
    return json.loads(t[t.index("{"):t.rindex("}") + 1])


def load_runs():
    recs = [json.loads(l) for l in open(RUNS)]
    return recs


def by_tag(recs, tag):
    return [r for r in recs if r.get("tag") == tag]


def rig_edges(which="htn"):
    sys.path.insert(0, CLONE)
    with contextlib.redirect_stdout(io.StringIO()):
        if which == "htn":
            from spider_web_htn.state import rigid
            from spider_web_htn.utils import NODE_COORDS as NC
        else:
            from spider_web_fap.state import rigid
            from spider_web_fap.utils import FAP_NODE_COORDS as NC
    return [(NC[a], NC[b]) for a, b in rigid.walkable_edges]


def draw_web(ax, threads, coords, rig="htn", annotate_mult=True, removed=(), lim=True,
             fontsize=6.5, off=0.4):
    """threads: list of (n1, n2, type). coords: name -> (x, y). Returns set of type keys drawn."""
    for (x1, y1), (x2, y2) in rig_edges(rig):
        ax.plot([x1, x2], [y1, y2], color="#BBBBBB", lw=0.7, ls=(0, (3, 2)), zorder=0)
    for n1, n2, *_ in removed:
        (x1, y1), (x2, y2) = coords[n1], coords[n2]
        ax.plot([x1, x2], [y1, y2], color=COLORS["aux_spiral"], lw=0.8, ls=(0, (2, 2)), zorder=1)
    mult = Counter()
    for t in threads:
        n1, n2, ty = t[0], t[1], TYPE_KEY.get(t[2], t[2])
        mult[(frozenset((n1, n2)), ty)] += 1
    drawn = set()
    pairs_seen = Counter()
    for ty in ORDER:
        for (pair, tty), m in mult.items():
            if tty != ty:
                continue
            ends = sorted(pair)
            n1, n2 = (ends[0], ends[0]) if len(ends) == 1 else ends
            (x1, y1), (x2, y2) = coords[n1], coords[n2]
            # offset parallel copies of the same edge with different types slightly
            k = pairs_seen[pair]
            pairs_seen[pair] += 1
            dx, dy = x2 - x1, y2 - y1
            L = max((dx * dx + dy * dy) ** 0.5, 1e-9)
            ox, oy = (-dy / L * off * k, dx / L * off * k)
            ax.plot([x1 + ox, x2 + ox], [y1 + oy, y2 + oy], color=COLORS[ty], lw=WIDTH[ty],
                    solid_capstyle="round", zorder=2 + ORDER.index(ty) * 0.1)
            drawn.add(ty)
            if annotate_mult and m > 1:
                ax.text(min(x1, x2) + ox - 0.12 * L, max(y1, y2) - (0.2 + 0.3 * k) * L, f"×{m}", fontsize=fontsize,
                        color=COLORS[ty], ha="right", va="center", zorder=5,
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))
    ax.set_aspect("equal")
    if lim:
        ax.set_xlim(-1.5, 17.5)
        ax.set_ylim(-1.5, 19.5)
    ax.grid(False)
    ax.set_xticks([0, 8, 16])
    ax.set_yticks([0, 6, 12, 18])
    return drawn


def legend_handles(types):
    from matplotlib.lines import Line2D
    return [Line2D([], [], color=COLORS[t], lw=WIDTH[t] + 0.4, label=LABELS[t])
            for t in ORDER if t in types]
