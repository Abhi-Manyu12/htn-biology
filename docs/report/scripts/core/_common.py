"""Shared helpers for the core-domain figure scripts."""
import json
import math
import os
import sys

W = "<WORKSPACE>"
REPO = os.path.join(W, "repo", "htn-biology")            # read-only, commit 61d18d8
DERIVED = os.path.join(W, "work", "core", "derived")       # outputs of our own re-runs (see rerun_checks.sh etc.)
FIG = os.path.join(W, "report", "figures", "core")
sys.path.insert(0, os.path.join(W, "tools"))

import plotstyle  # noqa: E402

PHASE_KEYS = ["exploration", "proto_hub", "frame", "radii", "auxiliary_spiral", "capture_spiral", "complete"]
PHASE_LABEL = {
    "exploration": "Exploration & bridging", "proto_hub": "Proto-hub establishment",
    "frame": "Frame construction", "radii": "Radii construction", "auxiliary_spiral": "Auxiliary spiral",
    "capture_spiral": "Capture spiral", "complete": "Finalisation",
}
PHASE_COLOR = {k: plotstyle.PHASE_COLORS[v] for k, v in PHASE_LABEL.items()}

THREAD_KEY = {"auxiliary_spiral": "aux_spiral"}            # model thread type -> plotstyle key
THREAD_LABEL = {"bridge": "bridge", "dragline": "dragline", "proto_radius": "proto-radius", "frame": "frame",
                "radius": "radius", "auxiliary_spiral": "auxiliary spiral", "capture_spiral": "capture spiral"}

# Supporting rig (as drawn by visualization/index*.html STRUCTURE_EDGES): two sticks, bottom bar, crossbar.
RIG = [((0, 0), (0, 18)), ((16, 0), (16, 18)), ((0, 0), (16, 0)), ((0, 9), (16, 9))]


def thread_color(t):
    return plotstyle.THREAD_COLORS[THREAD_KEY.get(t, t)]


def load_plan_js(path):
    """Parse a committed visualization/plan_data*.js file (``const PLAN_DATA = {...};``)."""
    txt = open(path).read()
    txt = txt[txt.index("{"): txt.rindex("}") + 1]
    d = json.loads(txt)
    for s in d["steps"]:
        s.setdefault("action", [s["name"]] + list(s["args"]))
    return d


def load_plan_json(path):
    d = json.load(open(path))
    for s in d["steps"]:
        s["action"] = [s["name"]] + list(s["args"])
    return d


def plans():
    """The three plans compared in the section, in display order."""
    return [
        ("Checkpoint 2 plan\n(updated pkg @ 39b89f3)", "cp2",
         load_plan_json(os.path.join(DERIVED, "plan_checkpoint2_39b89f3.json"))),
        ("Original package\n(spider_web_htn)", "orig",
         load_plan_js(os.path.join(REPO, "visualization", "plan_data.js"))),
        ("Updated package\n(spider_web_htn_updated)", "upd",
         load_plan_js(os.path.join(REPO, "visualization", "plan_data_updated.js"))),
    ]


def plans_exact():
    """Same three plans, but with unrounded per-step energies from our own export (export_plan.py) at
    39b89f3 / 61d18d8. (The committed plan_data*.js files round each step to 0.1 cm; their action
    sequences are identical to these exports -- checked in fig_energy.py.)"""
    return [
        ("Checkpoint 2 plan (updated pkg @ 39b89f3)", "cp2",
         load_plan_json(os.path.join(DERIVED, "plan_checkpoint2_39b89f3.json"))),
        ("Original package (spider_web_htn)", "orig",
         load_plan_json(os.path.join(DERIVED, "plan_original_61d18d8.json"))),
        ("Updated package (spider_web_htn_updated)", "upd",
         load_plan_json(os.path.join(DERIVED, "plan_updated_61d18d8.json"))),
    ]


PLAN_STYLE = {"cp2": dict(color=plotstyle.C["grey"], ls=":"), "orig": dict(color=plotstyle.C["orange"], ls="--"),
              "upd": dict(color=plotstyle.C["blue"], ls="-")}


def replay_threads(steps, upto=None):
    """Same thread semantics as applyAction() in visualization/index_updated.html."""
    t = []
    for s in steps[: (len(steps) if upto is None else upto)]:
        a = s["action"]
        name, args = a[0], a[1:]
        if name in ("lay_thread", "build_spiral_segment"):
            t.append((args[0], args[1], args[2]))
        elif name == "lay_frame_thread":
            t.append((args[0], args[1], "frame"))
        elif name == "lay_radius":
            t.append((args[0], args[1], "radius"))
        elif name in ("drop_down", "swing_tarzan"):
            t.append((args[0], args[1], "dragline"))
        elif name == "insert_radius":
            for i, (x, y, ty) in enumerate(t):
                if ty == "dragline" and {x, y} == {args[0], args[1]}:
                    t.pop(i)
                    break
            t.append((args[1], args[0], "proto_radius"))
        elif name == "remove_thread":
            for i, (x, y, ty) in enumerate(t):
                if {x, y} == {args[0], args[1]}:
                    t.pop(i)
                    break
    return t


ORDER = ["bridge", "dragline", "frame", "proto_radius", "radius", "auxiliary_spiral", "capture_spiral"]
WIDTH = {"bridge": 1.1, "dragline": 0.8, "proto_radius": 2.8, "frame": 1.4, "radius": 1.1,
         "auxiliary_spiral": 0.8, "capture_spiral": 1.0}
DASH = {"dragline": (0, (3, 2)), "auxiliary_spiral": (0, (2.5, 1.5))}


def draw_web(ax, plan, upto=None, legend=False, rig=True, fontsize=7):
    coords = plan["node_coords"]
    if rig:
        for (x1, y1), (x2, y2) in RIG:
            ax.plot([x1, x2], [y1, y2], color="#D0D0D0", lw=3.2, solid_capstyle="round", zorder=0)
    th = replay_threads(plan["steps"], upto)
    used = set()
    for ty in ORDER:
        for n1, n2, t in th:
            if t != ty:
                continue
            (x1, y1), (x2, y2) = coords[n1], coords[n2]
            ax.plot([x1, x2], [y1, y2], color=thread_color(t), lw=WIDTH[t], ls=DASH.get(t, "-"),
                    zorder=2 + ORDER.index(t), solid_capstyle="round")
            used.add(t)
    hub = coords.get("proto_hub")
    if hub and any("proto_hub" in (a, b) for a, b, _ in th):
        ax.plot(*hub, "o", ms=2.8, color="black", zorder=20)
    ax.set_aspect("equal")
    ax.set_xlim(-1.2, 17.2)
    ax.set_ylim(-1.2, 19.2)
    ax.set_xticks([0, 8, 16])
    ax.set_yticks([0, 9, 18])
    ax.grid(False)
    ax.tick_params(labelsize=fontsize)
    return used, th


def web_legend_handles(types):
    from matplotlib.lines import Line2D
    return [Line2D([0], [0], color=thread_color(t), lw=max(WIDTH[t], 1.2), ls=DASH.get(t, "-"),
                   label=THREAD_LABEL[t]) for t in ORDER if t in types]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def phase_table(plan):
    out = {k: [0, 0.0] for k in PHASE_KEYS}
    for s in plan["steps"]:
        out[s["phase"]][0] += 1
        out[s["phase"]][1] += s["energy"]
    return out
