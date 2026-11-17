"""Replay fidelity checks, not new scientific trials or biological validation."""
import csv
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from visualization.export_experiments import aggregate, script_json, sector_replay

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "visualization" / "experiments"


def bundle(study_id):
    payload = (ASSETS / f"{study_id}.js").read_text()
    prefix = f'window.EXPERIMENT_STUDIES["{study_id}"]='
    assert payload.startswith(prefix) and payload.endswith(';\n')
    return json.loads(payload[len(prefix):-2])


@pytest.mark.parametrize("study_id", ("moving", "recovery", "e1", "expanded"))
def test_bundled_ledgers_have_valid_endpoints_and_matched_groups(study_id):
    study = bundle(study_id)
    assert study["cases"]
    manifest = json.loads((ASSETS / "manifest.json").read_text())[study_id]
    assert hashlib.sha256((ASSETS / f"{study_id}.js").read_bytes()).hexdigest() == manifest["bundle_sha256"]
    assert study["source_sha256"] == manifest["source_sha256"]
    for case in study["cases"]:
        assert case["seed"] == (20 if study_id == "expanded" else 0)
        assert len({run["id"] for run in case["runs"]}) == len(case["runs"])
        for run in case["runs"]:
            assert run["frames"] or run["outcome"]["elapsed_s"] == 0
            assert all(frame["t0"] <= frame["t1"] for frame in run["frames"])
            stamps = [frame["t1"] for frame in run["frames"]]
            assert stamps == sorted(stamps)
            if run["frames"]:
                assert run["frames"][-1]["t1"] == pytest.approx(run["outcome"]["elapsed_s"])
                assert run["frames"][-1]["travel"] == pytest.approx(run["outcome"]["travel_cm"])
            assert run["aggregate"]["n"] == (20 if study_id == "e1" else 10)
            assert run["sha256"] == study["source_sha256"][run["source"]]


def saved_transfer():
    evidence = ROOT / "docs" / "research" / "evidence" / "e1_v1"
    with (evidence / "trials.csv").open(newline="") as stream:
        record = next(row for row in csv.DictReader(stream) if row["controller"] == "retained_htn"
                      and row["scenario"] == "transfer_partial" and row["seed"] == "0"
                      and json.loads(row["config"])["sectors"] == 8
                      and json.loads(row["config"])["amplitude_cm"] == 10)
    row = {**record, "config": json.loads(record["config"]), "final_state": json.loads(record["final_state"]),
           "elapsed_s": float(record["elapsed_s"]), "travel_cm": float(record["travel_cm"])}
    trace = json.loads((evidence / "traces" / "case3_transfer_partial_retained_htn.json").read_text())
    return row, trace


def test_curated_transfer_preserves_external_web_replacement_and_actor_stock():
    row, trace = saved_transfer()
    result = sector_replay(row, trace)
    transfer = next(frame for frame in result["frames"] if frame["kind"] == "intervention")
    before, after = (result["states"][transfer[name]] for name in ("before", "state"))
    assert transfer["t1"] - transfer["t0"] == 5
    assert before["edges"] != after["edges"]
    assert before["silk"] == after["silk"]
    assert before["remaining"] == after["remaining"]
    assert any(anchor.startswith("B") for edge in after["edges"] for anchor in edge[:2])


def test_export_rejects_source_outcome_disagreement():
    row, trace = saved_transfer()
    incorrect = deepcopy(row)
    incorrect["travel_cm"] += 1
    with pytest.raises(ValueError, match="travel disagrees"):
        sector_replay(incorrect, trace)


def test_failed_strata_are_not_reported_as_zero_physical_cost():
    row = {"success": False, "elapsed_s": 10, "travel_cm": 5, "silk_used_cm": 2, "planning_wall_s": .03}
    stats = aggregate([row])
    assert stats["n"] == 1 and stats["successes"] == 0
    assert stats["means"]["elapsed_s"] is None
    assert stats["means"]["silk_cm"] is None
    assert stats["means"]["planning_s"] == .03


def test_script_data_cannot_close_script_or_inject_markup():
    value = {"label": '</script><img src=x onerror="alert(1)">\u2028\u2029'}
    encoded = script_json(value)
    assert "<" not in encoded and "\u2028" not in encoded and "\u2029" not in encoded
    assert json.loads(encoded) == value


def test_expanded_coverage_contains_size_resource_and_motion_cases():
    cases = bundle("expanded")["cases"]
    assert {case["suite"] for case in cases} == {"scaling", "resource", "movement"}
    assert {case["config"]["sectors"] for case in cases} == {4, 8, 16, 24, 32}
    assert any(all(run["outcome"]["event_fired"] is False for run in case["runs"]) for case in cases)
    assert any(case["scenario"] == "transfer_partial" for case in cases)
