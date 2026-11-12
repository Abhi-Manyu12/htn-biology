"""Regression checks for the expanded protocol's matching and denominators."""
from dataclasses import asdict
import csv
import json

import pytest

from spider_web_recovery.domain import Config
from spider_web_recovery.e1 import CONTROLLERS, run_trial
from spider_web_recovery.e1_expanded import SEEDS, check_exposure, designs, paired, summarize
from spider_web_recovery.e1_expanded_figures import load_trials


def test_frozen_design_has_expected_trials_and_new_seeds():
    cases = designs()
    assert sum(len(c["scenarios"])*len(CONTROLLERS)*len(SEEDS) for c in cases) == 5280
    assert set(SEEDS).isdisjoint(range(20))
    assert {c["config"].sectors for c in cases if c["suite"] == "scaling"} == {4, 8, 16, 24, 32}
    assert {c["margin"] for c in cases if c["suite"] == "resource"} == {-1, 0, 20, 60}


def case_rows(config, config_id, scenario="damage_single"):
    rows = []
    for controller in CONTROLLERS:
        row, _, _ = run_trial(config, controller, scenario, 20)
        row.update(suite="resource", config_id=config_id, margin_cm=config.silk_cm-19*config.sectors)
        rows.append(row)
    return rows


def test_resource_exhaustion_before_event_is_counted_and_never_paired_as_zero_cost():
    rows = case_rows(Config(sectors=4, depth=0, silk_cm=75), 0)
    assert check_exposure(rows) == dict(matched_cases=1, identical_exposed_cases=0, all_unexposed_cases=1)
    assert all(not r["success"] and not r["event_fired"] for r in rows)
    for result in paired(rows):
        if result["metric"] in ("elapsed_s", "travel_cm", "silk_used_cm", "recovery_policy_wall_s"):
            assert result["paired_n"] == 0 and result["mean_difference"] is None
        elif result["metric"] == "success":
            assert result["paired_n"] == 1


def test_distinct_resource_configurations_are_not_silently_combined():
    rows = case_rows(Config(sectors=4, depth=0, silk_cm=75), 0)
    rows += case_rows(Config(sectors=4, depth=0, silk_cm=150), 1)
    assert check_exposure(rows)["matched_cases"] == 2
    summary = summarize(rows)
    assert len(summary) == 8
    comparisons = paired(rows)
    success = [r for r in comparisons if r["metric"] == "success"]
    assert len(success) == 6 and all(r["attempted_pairs"] == 1 for r in success)
    assert {r["silk_cm"] for r in success} == {75, 150}
    rows[0]["config"] = asdict(Config(sectors=4, depth=0, silk_cm=76))
    with pytest.raises(ValueError, match="configurations"):
        check_exposure(rows)


def test_exposure_audit_rejects_unequal_states():
    rows = case_rows(Config(sectors=4, depth=0, silk_cm=150), 0)
    assert all(r["event_fired"] for r in rows)
    rows[0]["post_state_sha256"] = "changed"
    with pytest.raises(ValueError, match="checkpoint"):
        check_exposure(rows)


def test_curated_csv_reader_preserves_failure_and_configuration(tmp_path):
    path = tmp_path/"trials.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("seed", "config", "margin_cm", "success"))
        writer.writeheader()
        writer.writerow(dict(seed=20, config=json.dumps({"sectors": 8}), margin_cm=-1, success=False))
    assert load_trials(path) == [dict(seed=20, config={"sectors": 8}, margin_cm=-1, success=False)]
    path.write_text('seed,config,margin_cm,success\n20,"{}",0,unknown\n')
    with pytest.raises(ValueError, match="success"):
        load_trials(path)
