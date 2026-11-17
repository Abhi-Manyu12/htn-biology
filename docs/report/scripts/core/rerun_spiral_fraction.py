"""Sweep domain.spiral.start_radius_fraction in the updated package (private clone at 61d18d8) and record plan
length, total energy and spiral-phase energies. Each value runs in a fresh subprocess with SPIDER_WEB_CONFIG
pointing at a modified copy of config.yaml (stochastic disabled, as shipped).

    "$PY" rerun_spiral_fraction.py "$W/work/core/repo" "$W/work/core/derived/spiral_fraction_sweep_61d18d8.json"
"""
import json, os, subprocess, sys, tempfile
import yaml

repo, out = sys.argv[1], sys.argv[2]
cfg0 = yaml.safe_load(open(os.path.join(repo, "spider_web_htn_updated", "config.yaml")))
code = r'''
import sys, json, contextlib, io
sys.path.insert(0, %r)
import gtpyhop
from spider_web_htn_updated.main import setup_domain
from spider_web_htn_updated.state import create_initial_state
from spider_web_htn_updated.utils import calculate_distance
with contextlib.redirect_stdout(io.StringIO()):
    setup_domain(); gtpyhop.set_verbose_level(0)
    plan = gtpyhop.find_plan(create_initial_state(), [("build_web",)])
E = {"auxiliary_spiral": 0.0, "capture_spiral": 0.0, "total": 0.0}
mode = None
for a in plan:
    if a[0] == "build_spiral_segment": mode = a[3]
    if a[0] in ("mark_auxiliary_spiral_done", "mark_capture_spiral_done"): mode = None
    if a[0] in ("walk","lay_thread","lay_frame_thread","lay_radius","drop_down","swing_tarzan","reel_up","build_spiral_segment"):
        d = calculate_distance(a[1], a[2]); E["total"] += d
        if mode: E[mode] += d
print("RESULT" + json.dumps({"n": len(plan), **E}))
''' % repo
rows = []
for f in (0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60):
    cfg = json.loads(json.dumps(cfg0))
    cfg["domain"]["spiral"]["start_radius_fraction"] = f
    tmp = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    yaml.safe_dump(cfg, tmp); tmp.close()
    env = dict(os.environ, SPIDER_WEB_CONFIG=tmp.name)
    o = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, cwd=repo)
    line = [l for l in o.stdout.splitlines() if l.startswith("RESULT")][0]
    r = json.loads(line[6:]); r["start_radius_fraction"] = f; rows.append(r); print(r)
json.dump(rows, open(out, "w"), indent=1)
