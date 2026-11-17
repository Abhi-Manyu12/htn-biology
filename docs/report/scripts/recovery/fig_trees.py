"""Compact redraws of recorded upstream IPyHOP solution trees (recovery v1, verified run).

Outputs
  tree_example_before_after : worked example (case 1 = 4 sectors, depth 0, 10 cm; seed 0; permanent_anchor;
                              backend ipyhop) -- docs/research/evidence/recovery_example/{trees,events}.json
  tree_gallery              : the same case for every scenario, from
                              mulder_results/recovery_v1_verified/traces/case1_<scenario>_ipyhop/{trees,events}.json
Node structure, tags (old/new), selected methods and the failed node id are read from trees.json; which
leaves were executed before the failure is read from events.json. Nothing is inferred from a flat plan.
"""
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from _common import EVID, OUT, REC, SCENARIOS, SCEN_LABEL, load_json, plotstyle

C = plotstyle.C
OLD, NEW, GONE, DONE, FAIL = C["blue"], C["orange"], "#C8C8C8", "#333333", C["vermillion"]


def short(info, method=None):
    head = info[0]
    if head == "root":
        return "root"
    if head == "build_web":
        return "build_web"
    if head in ("radial_phase", "capture_phase"):
        return head.replace("_phase", "")
    if head == "layer":
        return "layer"
    if head == "build_radius":
        m = {"radius_primary": "primary", "radius_backup": "backup", "radius_done": "done"}.get(method, "")
        return f"R{info[1]}" + (f"\n{m}" if m else "")
    if head == "build_capture":
        m = {"capture_direct": "direct", "capture_repair": "repair", "capture_done": "done"}.get(method, "")
        return f"C{info[1]}" + (f"\n{m}" if m else "")
    if head == "restore_structure":
        return "restore"
    if head == "travel":
        return f"to {info[1]}"
    if head == "move":
        return f"{info[1]}>{info[2]}"
    if head == "attach":
        return f"attach {info[2]}"
    if head == "capture":
        return f"cap{info[1]} {info[2]},{info[3]}"
    return str(head)


def layout(snap):
    nodes = {n["id"]: n for n in snap["nodes"]}
    kids = defaultdict(list)
    for a, b in snap["edges"]:
        kids[a].append(b)
    pos, counter = {}, [0]

    def place(i, d):
        if not kids[i]:
            pos[i] = (counter[0], -d)
            counter[0] += 1
        else:
            for c in kids[i]:
                place(c, d + 1)
            xs = [pos[c][0] for c in kids[i]]
            pos[i] = ((min(xs) + max(xs)) / 2, -d)

    place(0, 0)
    return nodes, kids, pos, counter[0]


def executed_and_failed(events):
    done, failed = set(), None
    for e in events:
        if e["event"] == "replan":
            break
        if e["event"] == "action":
            if e["accepted"]:
                done.add(e["node_id"])
            else:
                failed = e["node_id"]
    return done, failed


def kept_ids(before, after):
    a = {n["id"]: n for n in after["nodes"]}
    return {n["id"] for n in before["nodes"]
            if n["id"] in a and a[n["id"]]["tag"] == "old" and a[n["id"]]["info"] == n["info"]}


def draw(ax, snap, mode, executed=(), failed=None, kept=None, switched=(), labels=True, fs=5.6, ms=4.2):
    nodes, kids, pos, nleaf = layout(snap)
    for a, b in snap["edges"]:
        (x0, y0), (x1, y1) = pos[a], pos[b]
        gone = mode == "before" and kept is not None and b not in kept
        ax.plot([x0, x1], [y0, y1], color=GONE if gone else "#9A9A9A", lw=0.6,
                ls=(0, (2, 1.5)) if gone else "-", zorder=1)
    for i, n in nodes.items():
        x, y = pos[i]
        if mode == "before":
            if i == 0:
                col = "#7F7F7F"
            elif kept is not None and i not in kept:
                col = GONE
            else:
                col = OLD
            face = DONE if i in executed else ("white" if n["kind"] == "A" else col)
            edge = DONE if i in executed else col
        else:
            col = "#7F7F7F" if i == 0 else (OLD if n["tag"] == "old" else NEW)
            face, edge = col, col
        ax.plot(x, y, "o", ms=ms, mfc=face, mec=edge, mew=0.9, zorder=3)
        if i in switched:
            ax.plot(x, y, "o", ms=ms + 4, mfc="none", mec="black", mew=1.1, zorder=4)
        if i == failed:
            ax.plot(x, y, "X", ms=ms + 3.5, color=FAIL, mec="white", mew=0.4, zorder=5)
        if labels:
            lab = short(n["info"], n.get("selected_method") or n.get("method"))
            if not kids[i]:
                ax.text(x, y - 0.22, lab, rotation=90, ha="center", va="top", fontsize=fs, zorder=6)
            elif n["info"][0] not in ("layer",):
                ax.text(x + 0.25, y + 0.12, lab, ha="left", va="bottom", fontsize=fs, zorder=6,
                        linespacing=0.9)
    ax.set_xlim(-0.8, max(nleaf, 2) - 0.2)
    ax.axis("off")
    return pos


def legend_handles():
    mk = lambda **k: Line2D([], [], ls="", marker="o", **{"ms": 5, **k})  # noqa: E731
    return [mk(mfc=DONE, mec=DONE, label="executed before failure"),
            mk(mfc="white", mec=OLD, label="pending leaf (kept)"),
            mk(mfc=GONE, mec=GONE, label="un-refined by re-entry"),
            Line2D([], [], ls="", marker="X", ms=7, color=FAIL, label="failed leaf"),
            mk(mfc=OLD, mec=OLD, label="tag old (retained)"),
            mk(mfc=NEW, mec=NEW, label="tag new (refined after re-entry)"),
            mk(mfc="none", mec="black", ms=8, label="method switched by backtracking")]


def switched_ids(before, after):
    b = {n["id"]: n for n in before["nodes"]}
    return {n["id"] for n in after["nodes"] if n["id"] in b and n["tag"] == "old"
            and n["info"] == b[n["id"]]["info"] and n["selected_method"] != b[n["id"]]["selected_method"]}


def example():
    trees = load_json(EVID / "recovery_example" / "trees.json")
    events = load_json(EVID / "recovery_example" / "events.json")
    before, after = trees
    executed, failed = executed_and_failed(events)
    assert failed == after["failed_node"]
    kept = kept_ids(before, after)
    sw = switched_ids(before, after)
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.4), gridspec_kw=dict(hspace=0.32))
    draw(axes[0], before, "before", executed, failed, kept, fs=6.6)
    draw(axes[1], after, "after", switched=sw, fs=6.6)
    axes[0].text(0.0, 1.02, "(a) initial plan, generation 1 (fresh_plan); 14 actions executed, attach A3 fails",
                 transform=axes[0].transAxes, fontsize=8.5, ha="left", va="bottom")
    axes[1].text(0.0, 1.02, f"(b) after replan(observed state, failed node {after['failed_node']}), generation 2",
                 transform=axes[1].transAxes, fontsize=8.5, ha="left", va="bottom")
    fig.legend(handles=legend_handles(), loc="lower center", ncol=4, fontsize=7.5, bbox_to_anchor=(0.5, -0.045),
               handletextpad=0.3, columnspacing=1.0)
    plotstyle.save(fig, str(OUT / "tree_example_before_after"))


def gallery():
    fig, axes = plt.subplots(len(SCENARIOS), 2, figsize=(7.0, 6.9),
                             gridspec_kw=dict(hspace=0.3, wspace=0.04))
    for r, sc in enumerate(SCENARIOS):
        d = REC / "traces" / f"case1_{sc}_ipyhop"
        trees, events = load_json(d / "trees.json"), load_json(d / "events.json")
        executed, failed = executed_and_failed(events)
        retries = [e for e in events if e["event"] == "retry"]
        before = trees[0]
        after = trees[1] if len(trees) > 1 else None
        kept = kept_ids(before, after) if after and len(after["nodes"]) > 1 else (
            {0} if after else None)
        if retries:   # transient: failed node retried, not replanned
            executed = executed | {failed}
        draw(axes[r, 0], before, "before", executed, failed, kept, labels=False, ms=3.2)
        axes[r, 0].text(-0.02, 0.5, SCEN_LABEL[sc].replace(" ", "\n"), transform=axes[r, 0].transAxes, rotation=90,
                        ha="right", va="center", fontsize=7.5, linespacing=1.0)
        ax = axes[r, 1]
        if after is None:
            msg = ("no failure, no re-entry" if sc == "clean" else
                   f"attempt failed, same command retried\n({len(retries)} retry, no re-entry, tree unchanged)")
            ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=7.5, transform=ax.transAxes, color="#555")
            ax.axis("off")
        elif len(after["nodes"]) == 1:
            ax.text(0.5, 0.5, f"replan from node {after['failed_node']} exhausted search:\n"
                    "tree reduced to root, empty plan, goal unmet\n-> planning_infeasible",
                    ha="center", va="center", fontsize=7.5, transform=ax.transAxes, color="#555")
            ax.axis("off")
        else:
            draw(ax, after, "after", switched=switched_ids(before, after), labels=False, ms=3.2)
            n_new = sum(n["tag"] == "new" for n in after["nodes"])
            ax.text(1.0, 1.0, f"{n_new} new / {len(after['nodes']) - 1} nodes", transform=ax.transAxes,
                    ha="right", va="top", fontsize=6.5, color="#555")
        if r == 0:
            axes[r, 0].set_title("initial tree (generation 1)", fontsize=8.5)
            axes[r, 1].set_title("tree after re-entry (generation 2)", fontsize=8.5)
    fig.legend(handles=legend_handles(), loc="lower center", ncol=4, fontsize=6.8, bbox_to_anchor=(0.5, 0.0),
               handletextpad=0.3, columnspacing=0.9)
    fig.subplots_adjust(bottom=0.07)
    plotstyle.save(fig, str(OUT / "tree_gallery"))


if __name__ == "__main__":
    plotstyle.apply()
    example()
    gallery()
