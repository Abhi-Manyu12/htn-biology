"""Export a GTPyhop web-construction plan (actions, macro phase, per-step energy, node coords) as JSON.

Run INSIDE a private checkout of the repo (never the read-only copy), e.g.

    cd "$W/work/core/repo_39b89f3"          # git worktree at commit 39b89f3 (Checkpoint-2 era)
    "$W/.venv/bin/python" "$W/report/scripts/core/export_plan.py" spider_web_htn_updated \
        "$W/work/core/derived/plan_checkpoint2_39b89f3.json" --deterministic

`--deterministic` writes a copy of the package's config.yaml with stochastic.enabled=false to a temp file and
points SPIDER_WEB_CONFIG at it *before* the package is imported (the shipped config at 39b89f3 had
stochastic.enabled: true, anchor removal p=0.2, seed 7107).

The macro-phase tagging is the same rule set as spider_web_htn_updated/visualize_updated.py
(determine_macro_phase), and energy is the Euclidean distance of each movement operator (Eq. 1 of the
Checkpoint 2 report), computed with the package's own _movement_cost / calculate_distance.
"""
import argparse
import contextlib
import io
import json
import os
import sys
import tempfile

import yaml

MOVE = ("walk", "lay_thread", "lay_frame_thread", "lay_radius", "drop_down", "swing_tarzan",
        "reel_up", "build_spiral_segment")


def phase_of(name, args, prev):
    mapping = {
        'attach_dragline': 'exploration', 'mark_high_thread_done': 'exploration',
        'anchor': 'proto_hub', 'insert_radius': 'proto_hub', 'mark_proto_hub': 'proto_hub',
        'lay_frame_thread': 'frame', 'lay_radius': 'radii',
        'mark_auxiliary_spiral_done': 'auxiliary_spiral', 'mark_capture_spiral_done': 'capture_spiral',
        'mark_web_complete': 'complete',
    }
    if name in mapping:
        return mapping[name]
    if name == 'build_spiral_segment' and len(args) > 2:
        return 'auxiliary_spiral' if args[2] == 'auxiliary_spiral' else 'capture_spiral'
    if name == 'lay_thread' and len(args) > 2 and args[2] == 'dragline':
        return 'proto_hub'
    if name in ('drop_down', 'swing_tarzan'):
        return 'proto_hub'
    return prev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("out")
    ap.add_argument("--deterministic", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, os.getcwd())
    if a.deterministic:
        cfg_path = os.path.join(os.getcwd(), a.package, "config.yaml")
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
        cfg.setdefault("stochastic", {})["enabled"] = False
        tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        yaml.safe_dump(cfg, tmp)
        tmp.close()
        os.environ["SPIDER_WEB_CONFIG"] = tmp.name
    import importlib
    import gtpyhop
    main_mod = importlib.import_module(a.package + ".main")
    state_mod = importlib.import_module(a.package + ".state")
    utils_mod = importlib.import_module(a.package + ".utils")
    with contextlib.redirect_stdout(io.StringIO()):
        main_mod.setup_domain()
        st = state_mod.create_initial_state()
        gtpyhop.set_verbose_level(0)
        plan = gtpyhop.find_plan(st, [("build_web",)])
    dist = utils_mod.calculate_distance
    get_coord = getattr(utils_mod, "get_node_coord", None)
    coords = {k: list(v) for k, v in utils_mod.NODE_COORDS.items()}
    steps, prev, cum = [], 'exploration', 0.0
    for act in plan:
        name, args = act[0], list(act[1:])
        ph = phase_of(name, args, prev)
        e = dist(str(args[0]), str(args[1])) if (name in MOVE and len(args) >= 2) else 0.0
        cum += e
        for x in args[:2]:
            if isinstance(x, str) and x not in coords and get_coord is not None and "@" in x:
                coords[x] = list(get_coord(x))
        steps.append({"name": name, "args": args, "phase": ph, "energy": e, "cumulative_energy": cum})
        prev = ph
    out = {"package": a.package, "cwd": os.getcwd(), "deterministic": a.deterministic,
           "node_coords": coords, "steps": steps, "total_steps": len(steps), "total_energy": cum,
           "initial_nodes": sorted(st.nodes)}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"{a.package} @ {os.getcwd()}: {len(steps)} actions, {cum:.2f} cm -> {a.out}")


if __name__ == "__main__":
    main()
