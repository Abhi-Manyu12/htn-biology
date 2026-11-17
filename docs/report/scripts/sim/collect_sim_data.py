"""Run the evaluation scripts in evals/ inside the simulation page (headless Chrome via tools/shot.mjs)
and store each result as JSON in W/work/sim/data/<name>.json. Every number in the sim figures comes from here.
Usage: .venv/bin/python report/scripts/sim/collect_sim_data.py [name ...]"""
import json, os, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PAGE = os.path.join(W, "simulation", "orb_web_sim.html")
OUT = os.path.join(W, "work", "sim", "data")
os.makedirs(OUT, exist_ok=True)
names = sys.argv[1:] or ["web_states", "phases", "validation", "sweeps", "supports", "anchors"]
common = open(os.path.join(HERE, "evals", "common.js")).read()
for nm in names:
    js = common + "\n" + open(os.path.join(HERE, "evals", nm + ".js")).read()
    with tempfile.TemporaryDirectory() as td:
        ef = os.path.join(td, "e.js"); open(ef, "w").write(js)
        t0 = time.time()
        p = subprocess.run(["node", os.path.join(W, "tools", "shot.mjs"), PAGE + "?run=0&ui=0", os.path.join(td, "x.png"),
                            "--eval-file", ef, "--width", "900", "--height", "900", "--scale", "1", "--wait", "50"],
                           capture_output=True, text=True)
    line = [l for l in p.stdout.splitlines() if l.startswith("eval result: ")]
    errs = [l for l in p.stdout.splitlines() if "page errors" in l or l.startswith("  ")]
    if not line:
        print(p.stdout[-2000:], p.stderr[-2000:]); raise SystemExit("eval failed: " + nm)
    data = json.loads(line[0][len("eval result: "):])
    json.dump(data, open(os.path.join(OUT, nm + ".json"), "w"))
    print(f"{nm}: {time.time() - t0:.1f} s, {len(line[0]) / 1e6:.2f} MB", "| page errors:" if errs else "", " ".join(errs))
