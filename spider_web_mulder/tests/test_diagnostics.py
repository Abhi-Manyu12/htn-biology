from dataclasses import replace
from html.parser import HTMLParser
import json

import pytest

from spider_web_mulder.diagnostics import FrozenMotion, main, replay_failure
from spider_web_mulder.experiment import CONTROLLERS, POLICIES, run_trial
from spider_web_mulder.model import Settings, Shear


@pytest.fixture
def settings():
    return Settings(amplitude_cm=5, frequency_hz=0.05, radial_count=4,
                    auxiliary_turns=1, capture_turns=1)


def test_motion_detection_does_not_alias_whole_period(settings):
    motion = Shear(settings)
    period = 1 / settings.frequency_hz
    assert motion.displacement(0) == pytest.approx(motion.displacement(period))
    assert motion.changed_between(0, period)
    assert motion.changed_between(0, period * 1000)
    assert not motion.changed_between(1, 1)
    assert not Shear(replace(settings, frequency_hz=0)).changed_between(0, 100)


@pytest.mark.parametrize("controller", CONTROLLERS)
def test_controller_contract_and_bookkeeping(settings, controller):
    row, trace = run_trial(settings, controller)
    feedback, retry, proactive = POLICIES[controller]
    actions = [e for e in trace if e["event"] == "action"]
    repairs = [e for e in trace if e["event"] == "repair"]
    decisions = [e for e in trace if e["event"] == "decision"]
    allowed = {"attachment_miss"} if retry else set()
    if proactive:
        allowed.add({"full": "support_change", "filtered": "filtered_drift",
                     "predictive": "predicted_drift"}[proactive])
    assert row["repairs"] == len(repairs)
    assert row["planning_calls"] == len(repairs) + 1
    assert len(actions) == len(decisions)
    assert row["travel_cm"] == pytest.approx(sum(e["travel_cm"] for e in actions))
    assert all(e["reason"] in allowed for e in repairs)
    assert all(e["feedback"] is feedback for e in actions)
    assert all(e["attempt"] <= settings.max_repairs_per_action + 1 for e in actions)
    accepted = [e["index"] for e in actions if e["accepted"]]
    assert accepted == list(range(row["completed_actions"]))
    for e in actions:
        assert e["target_created_s"] <= e["start_time_s"] <= e["arrival_time_s"] <= e["end_time_s"]
        assert e["target_age_s"] == pytest.approx(e["start_time_s"] - e["target_created_s"])
        assert e["accepted"] == (e["error_cm"] <= settings.attachment_tolerance_cm + 1e-9)
        assert e["correction_cm"] <= settings.correction_limit_cm + 1e-9
    for e in decisions:
        if not e["skipped_proactive_after_retry"]:
            if proactive == "full" and e["support_changed"]:
                assert e["scope"] == "web"
            if proactive == "filtered" and e["filtered_drift_cm"] > e["event_threshold_cm"]:
                assert e["scope"] == "component"
            if proactive == "predictive" and e["margin_cm"] < 0:
                assert e["scope"] == "component"
        if e["reason"] == "filtered_drift":
            assert e["filtered_drift_cm"] > e["event_threshold_cm"]
        if e["reason"] == "predicted_drift":
            assert e["margin_cm"] < 0
        if e["reason"] == "support_change":
            assert e["support_changed"]
    assert row["elapsed_s"] == pytest.approx(sum(row[f"{p}_time_s"] for p in ("frame", "radials", "auxiliary", "capture")))


@pytest.mark.parametrize("controller", ["filtered", "full", "predictive"])
def test_retry_does_not_immediately_trigger_second_refresh(settings, controller):
    _, trace = run_trial(settings, controller)
    retries = 0
    for i, event in enumerate(trace[:-2]):
        if event["event"] == "repair" and event["reason"] == "attachment_miss":
            retries += 1
            assert trace[i + 1]["event"] == "decision"
            assert trace[i + 1]["skipped_proactive_after_retry"]
            assert trace[i + 1]["scope"] is None
            assert trace[i + 2]["event"] == "action"
    assert retries


def test_component_refresh_keeps_future_targets_and_finished_work(settings):
    row, trace = run_trial(settings, "local_repair")
    # An action retains its plan timestamp until its own component is refreshed.
    actions = [e for e in trace if e["event"] == "action"]
    assert any(e["plan_id"] > 1 for e in actions)
    assert all(e["target_created_s"] == 0 for e in actions if e["plan_id"] == 1)
    assert len({e["index"] for e in actions if e["accepted"]}) == row["completed_actions"]
    assert all(e["scope"] == "component" for e in trace if e["event"] == "repair")


def test_filter_starts_fresh_for_each_component(settings):
    _, trace = run_trial(settings, "filtered")
    decisions = [e for e in trace if e["event"] == "decision"]
    previous = None
    for event in decisions:
        if event["task"] != previous:
            assert event["filter_reset"]
            assert event["filtered_drift_cm"] == pytest.approx(event["drift_cm"])
        previous = event["task"]


@pytest.mark.parametrize("controller", CONTROLLERS)
def test_counterfactual_reproduces_original_and_does_not_mutate(settings, controller):
    row, trace = run_trial(settings, controller)
    snapshot = json.dumps(trace)
    replays = replay_failure(settings, row, trace)
    assert json.dumps(trace) == snapshot
    failed = next(e for e in trace if e["event"] == "action" and not e["accepted"])
    assert len(replays) == 6
    original = replays[0]
    assert original["error_cm"] == pytest.approx(failed["error_cm"], abs=1e-12)
    assert original["end_time_s"] == pytest.approx(failed["end_time_s"])
    assert original["travel_cm"] == pytest.approx(failed["travel_cm"])
    assert all(e["start_time_s"] == failed["start_time_s"] for e in replays)
    assert next(e for e in replays if e["replay"] == "frozen_refreshed_target")["accepted"]
    assert all(e["correction_cm"] <= settings.correction_limit_cm + 1e-9 for e in replays)


def test_no_failure_means_no_counterfactual(settings):
    static = replace(settings, amplitude_cm=0)
    row, trace = run_trial(static, "local")
    assert replay_failure(static, row, trace) == []


def test_frozen_motion_keeps_departure_shear(settings):
    moving = Shear(settings)
    frozen = FrozenMotion(moving, 5)
    point = (3, 7)
    assert frozen.world(point, 100) == moving.world(point, 5)
    assert frozen.material(frozen.world(point, 100), 100) == pytest.approx(point)


def test_report_artifacts_and_html(settings, tmp_path):
    output = tmp_path / "diagnostics"
    main(["--output", str(output), "--amplitude", "5", "--frequency", "0.05", "--seed", "0"])
    text = (output / "report.html").read_text()
    HTMLParser().feed(text)
    assert "First-miss controlled replays" in text
    assert "function filter()" in text
    assert len(json.loads((output / "trials.json").read_text())) == 6
    assert len(json.loads((output / "replays.json").read_text())) == 36
    assert len(json.loads((output / "action_map.json").read_text())) == 218
    assert "not reached" in text
    assert len(list(output.glob("web_*.svg"))) == 6
    assert len(list(output.glob("errors_*.svg"))) == 6
    assert (output / "timeline.svg").exists()
    assert json.loads((output / "metadata.json").read_text())["model_version"] == 3
    with pytest.raises(SystemExit):
        main(["--output", str(output)])
