"""Build W/simulation/orb_web_sim.html from the template in W/work/sim/ by embedding
(a) the HTN plan in visualization/plan_data_updated.js and (b) the parts of
spider_web_htn_updated/config.yaml and spider_web_mulder/config.yaml the page mirrors.
Run: .venv/bin/python report/scripts/sim/build_sim_page.py"""
import json, os, re, yaml
W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
R = os.path.join(W, "repo", "htn-biology")
src = open(os.path.join(R, "visualization", "plan_data_updated.js")).read()
plan = json.loads(src[src.index("{"): src.rindex("}") + 1])
cfg = yaml.safe_load(open(os.path.join(R, "spider_web_htn_updated", "config.yaml")))
mul = yaml.safe_load(open(os.path.join(R, "spider_web_mulder", "config.yaml")))
data = {
    "nodes": plan["node_coords"],
    "steps": [[s["name"], s["args"], s["phase"], s["energy"], s["cumulative_energy"]] for s in plan["steps"]],
    "total_energy": plan["total_energy"],
    "frame": [cfg["environment"]["frame_width"], cfg["environment"]["frame_height"]],
    "walkable": cfg["environment"]["walkable_edges"],
    "spider_start": cfg["environment"]["spider_start_pos"],
    "removable": cfg["stochastic"]["anchor_availability"]["removable_nodes"],
    "seed": cfg["stochastic"]["seed"],
    "noise_std": cfg["stochastic"]["wind"]["noise_std"],
    "removal_prob": cfg["stochastic"]["anchor_availability"]["removal_prob"],
    "empirical": cfg["empirical"],
    "mulder": {"amplitude_cm": mul["environment"]["amplitude_cm"], "frequency_hz": mul["environment"]["frequency_hz"],
               "speed_cm_s": mul["execution"]["speed_cm_s"], "attachment_time_s": mul["execution"]["attachment_time_s"],
               "amplitudes_cm": mul["experiment"]["amplitudes_cm"], "frequencies_hz": mul["experiment"]["frequencies_hz"]},
    "silk_capacity_default": float(re.search(r"DEFAULT_SILK_CAPACITY\s*=\s*([0-9.]+)", open(os.path.join(R, "spider_web_htn_updated", "perturbations.py")).read()).group(1)),
}
txt = json.dumps(data, separators=(",", ":"))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page_src")
tpl = open(os.path.join(SRC, "template.html")).read()
core = open(os.path.join(SRC, "core.js")).read()
ui = open(os.path.join(SRC, "ui.js")).read()
out = tpl.replace("/*__REPO_DATA__*/null", txt).replace("/*__CORE_JS__*/", core).replace("/*__UI_JS__*/", ui)
assert "__CORE_JS__" not in out and "__UI_JS__" not in out and "__REPO_DATA__" not in out
os.makedirs(os.path.join(W, "simulation"), exist_ok=True)
open(os.path.join(W, "simulation", "orb_web_sim.html"), "w").write(out)
print("wrote simulation/orb_web_sim.html", len(out), "bytes; data", len(txt))
