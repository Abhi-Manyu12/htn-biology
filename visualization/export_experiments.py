"""Build browser replay assets from saved ledgers; never execute new trials.

Run from the repository root: python3 -m visualization.export_experiments
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from spider_web_recovery.domain import Config, World

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "visualization" / "experiments"
STUDIES = {
    "moving": "mulder_reentrant_v4",
    "recovery": "recovery_v1",
    "e1": "e1_v1_20261112",
    "expanded": "e1_expanded_v1_20261113",
}
METRICS = ("elapsed_s", "travel_cm", "silk_cm", "planning_s")


def demo_case(study_id, row):
    """Curated coverage keeps static bundles small; all-seed means remain intact."""
    if study_id == "recovery":
        return row["config"]["sectors"] == 4 and row["config"]["depth"] == 0
    if study_id != "expanded":
        return True
    config = row["config"]
    if row["suite"] == "scaling":
        return config["amplitude_cm"] == 10 and (
            row["scenario"] == "damage_multi" or
            row["scenario"] == "intact" and config["sectors"] == 8 or
            row["scenario"] == "transfer_partial" and config["sectors"] == 32)
    if row["suite"] == "resource":
        return config["sectors"] == 8 and row["scenario"] in ("damage_single", "damage_multi")
    return (config["amplitude_cm"] == 30 and config["frequency_hz"] == 0.1
            and row["scenario"] == "damage_single")


def script_json(value):
    """Keep data inert even if a future label contains HTML/script syntax."""
    return json.dumps(value, separators=(",", ":"), allow_nan=False).replace(
        "<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def outcome(row, moving=False):
    return {
        "success": row["success"],
        "reason": row.get("failure_reason"),
        "elapsed_s": row["elapsed_s"],
        "travel_cm": row["travel_cm"],
        "silk_cm": row["silk_chord_length_cm"] if moving else row["silk_used_cm"],
        "planning_s": row.get("policy_wall_s", row.get("planning_wall_s")),
        "method_calls": row.get("method_calls"),
        "event_fired": row.get("event_fired"),
        "donor_silk_cm": row.get("donor_web_silk_cm", 0),
    }


def aggregate(rows, moving=False):
    values = [outcome(row, moving) for row in rows]
    successful = [value for value in values if value["success"]]
    means = {}
    for metric in METRICS:
        eligible = values if metric == "planning_s" else successful
        measured = [v[metric] for v in eligible if v[metric] is not None]
        means[metric] = statistics.mean(measured) if measured else None
    return {"n": len(values), "successes": len(successful), "means": means}


def state_view(state):
    edges = [["hub", anchor, "radius"] for anchor in state["radii"].values()
             if anchor not in state["unavailable"]]
    edges += [[a, b, "capture"] for a, b in state["captures"].values()
              if a not in state["unavailable"] and b not in state["unavailable"]]
    return {"edges": edges, "unavailable": state["unavailable"],
            "blocked": state["blocked"], "silk": state["silk_used"],
            "remaining": state["silk_remaining"]}


def sector_replay(row, trace):
    """Retain every observed state change, including zero-duration damage."""
    world = World(Config(**row["config"]))
    initial = next((event["before"] for event in trace if "before" in event), row["final_state"])
    frames = []
    states = []
    state_ids = {}

    def intern(state):
        view = state_view(state)
        key = script_json(view)
        if key not in state_ids:
            state_ids[key] = len(states)
            states.append(view)
        return state_ids[key]

    previous = initial
    intern(initial)
    travel = 0.0
    for event in trace:
        after = event.get("after", event.get("observed", event.get("observed_state")))
        if after is None:
            continue
        before = event.get("before", previous)
        travel += event.get("travel_cm", 0)
        action = event.get("action", [])
        frames.append({"t0": before["clock_s"], "t1": after["clock_s"],
                       "from": before["position_material"], "to": after["position_material"],
                       "before": intern(before), "state": intern(after),
                       "kind": event["event"], "label": " ".join(map(str, action[:3])) or event.get("scenario", event["event"]),
                       "accepted": event.get("accepted", True),
                       "travel": travel,
                       "disturbance": bool(event.get("injected")) or event["event"] == "intervention"})
        previous = after
    final = row["final_state"]
    if previous != final or not math.isclose(previous["clock_s"], row["elapsed_s"], abs_tol=1e-6):
        raise ValueError("Trace endpoint disagrees with saved sector outcome")
    if not math.isclose(travel, row["travel_cm"], abs_tol=1e-6):
        raise ValueError("Trace travel disagrees with saved sector outcome")
    return {"nodes": world.coords, "scaffold": sorted(world.scaffold),
            "initial": initial["position_material"], "states": states, "frames": frames}


def moving_replay(row, trace):
    frames = []
    travel = 0.0
    for event in trace:
        if event["event"] != "action":
            continue
        travel += event["travel_cm"]
        frames.append({"t0": event["start_time_s"], "t1": event["end_time_s"],
                       "from": event["start_material_cm"], "to": event["end_material_cm"],
                       "kind": event["phase"], "label": event["task"],
                       "accepted": event["accepted"], "thread": event["silk"] and event["accepted"],
                       "travel": travel, "disturbance": event.get("injected_miss", False)})
    if not frames or not math.isclose(frames[-1]["t1"], row["elapsed_s"], abs_tol=1e-6):
        raise ValueError("Trace endpoint disagrees with saved moving-support outcome")
    if not math.isclose(travel, row["travel_cm"], abs_tol=1e-6):
        raise ValueError("Trace travel disagrees with saved moving-support outcome")
    return {"nodes": {}, "scaffold": [], "initial": frames[0]["from"], "states": [], "frames": frames}


def build_study(study_id, source, root=ROOT):
    """Match traces through the original runner's case/config indices."""
    sources = {}

    def read(path):
        raw = path.read_bytes()
        sources[path.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    moving = study_id == "moving"
    manifest = read(source / ("metadata.json" if moving else "provenance.json"))
    if not moving:
        geometry_path = root / "spider_web_recovery" / "domain.py"
        geometry_hash = hashlib.sha256(geometry_path.read_bytes()).hexdigest()
        expected_hash = manifest["source_sha256"]["domain.py" if study_id == "recovery" else "spider_web_recovery/domain.py"]
        if geometry_hash != expected_hash:
            raise ValueError("Domain geometry source differs from the historical manifest")
        sources[geometry_path.relative_to(root).as_posix()] = geometry_hash
    if moving:
        csv_path = source / "trials.csv"
        sources[csv_path.relative_to(root).as_posix()] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        with csv_path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            for key in ("elapsed_s", "travel_cm", "silk_chord_length_cm", "planning_wall_s", "method_calls", "initial_phase_rad"):
                row[key] = float(row[key]) if row[key] else None
            row["success"] = row["success"] == "True"
            row["seed"] = int(row["seed"])
        groups = [(profile, controller) for profile in ("moving_005", "transient_miss")
                  for controller in ("local_repair", "full")]
        configs = []
    else:
        rows = read(source / "trials.json")
        configs = manifest["configs"]
        scenarios = list(dict.fromkeys(row["scenario"] for row in rows))
        groups = [(index, scenario) for index in range(len(configs)) for scenario in scenarios]
    seed = manifest["seeds"][0]
    cases = []
    for case_index, scenario in groups:
        if moving:
            candidates = [r for r in rows if r["profile"] == case_index and r["controller"] == scenario
                          and r["complexity"] == "configured"]
            config = {**manifest["base_settings"], **manifest["complexities"]["configured"],
                      **manifest["profiles"][case_index]}
        else:
            config = configs[case_index]
            candidates = [r for r in rows if r["config"] == config and r["scenario"] == scenario
                          and (study_id != "expanded" or r["config_id"] == case_index)]
        representatives = [r for r in candidates if r["seed"] == seed]
        if not representatives:
            continue
        if not demo_case(study_id, representatives[0]):
            continue
        runs = []
        for row in representatives:
            controller = row.get("planner_backend", row.get("controller", row.get("backend")))
            if moving:
                filename = source / f"trace_{case_index}_{scenario}_{controller}.json"
            elif study_id == "recovery":
                filename = source / "traces" / f"case{case_index}_{scenario}_{controller}" / "events.json"
            else:
                filename = source / "traces" / f"case{case_index}_{scenario}_{controller}.json"
            if not filename.exists():
                raise FileNotFoundError(f"Saved trace missing: {filename}")
            trace = read(filename)
            replay = moving_replay(row, trace) if moving else sector_replay(row, trace)
            matched = [r for r in candidates if r.get("planner_backend", r.get("controller", r.get("backend"))) == controller]
            runs.append({"id": controller, "outcome": outcome(row, moving), "aggregate": aggregate(matched, moving),
                         "source": filename.relative_to(root).as_posix(), "sha256": sources[filename.relative_to(root).as_posix()],
                         **replay})
        phase = representatives[0].get("forcing_phase", representatives[0].get("initial_phase_rad"))
        if phase is None:
            phase = random.Random(seed).uniform(0, 2 * math.pi)
        cases.append({"id": f"{case_index}_{scenario}", "scenario": case_index if moving else scenario,
                      "policy": scenario if moving else None, "suite": representatives[0].get("suite"),
                      "config": config, "seed": seed, "phase": phase, "runs": runs})
    if not cases:
        raise ValueError(f"No measured replay cases for {study_id}")
    return {"id": study_id, "total_trials": len(rows), "cases": cases,
            "provenance": (source / ("metadata.json" if moving else "provenance.json")).relative_to(root).as_posix(),
            "source_sha256": sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for study_id, directory in STUDIES.items():
        study = build_study(study_id, ROOT / "mulder_results" / directory)
        payload = f"window.EXPERIMENT_STUDIES[{script_json(study_id)}]={script_json(study)};\n"
        target = args.output / f"{study_id}.js"
        target.write_text(payload)
        manifest[study_id] = {"cases": len(study["cases"]), "runs": sum(len(c["runs"]) for c in study["cases"]),
                              "bundle_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                              "source_sha256": study["source_sha256"]}
        print(f"{study_id}: {manifest[study_id]['cases']} cases, {manifest[study_id]['runs']} runs, {len(payload):,} bytes")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
