from dataclasses import replace
import json

import gtpyhop
import pytest

from spider_web_mulder.experiment import (
    CONTROLLERS, execute, feasibility_margin, main, run_trial, summarize,
)
from spider_web_mulder.model import (
    Settings, Shear, construction, load_settings, make_state, setup_domain,
)


@pytest.fixture
def small():
    return Settings(radial_count=4, auxiliary_turns=1, capture_turns=1,
                    integration_step_s=0.5)


def deterministic(row):
    return {k: v for k, v in row.items() if not k.endswith("wall_s")}


def test_shear_fixed_top_moving_bottom_and_inverse(small):
    motion = Shear(small, phase=0)
    quarter_period = 1 / (4 * small.frequency_hz)
    assert motion.world((0, 30), quarter_period) == pytest.approx((0, 30))
    assert motion.world((0, 0), quarter_period) == pytest.approx((10, 0))
    for t in (0, 1, 5, 18):
        assert motion.material(motion.world((12, 7), t), t) == pytest.approx((12, 7))


def test_stationary_controllers_agree(small):
    settings = replace(small, amplitude_cm=0)
    results = [run_trial(settings, c, 10)[0] for c in CONTROLLERS]
    for row in results:
        assert row["success"]
        assert row["repairs"] == 0
        assert row["planning_calls"] == 1
        assert row["normalized_travel"] == pytest.approx(1)
        assert row["frame_area_cm2"] == pytest.approx(900)
        assert row["elapsed_s"] == pytest.approx(results[0]["elapsed_s"])
        assert row["elapsed_s"] == pytest.approx(sum(row[f"{p}_time_s"] for p in ("frame", "radials", "auxiliary", "capture")))
        assert row["travel_cm"] == pytest.approx(results[0]["travel_cm"])


def test_matched_trajectory_and_reproducibility(small):
    a, trace_a = run_trial(small, "predictive", 7)
    b, trace_b = run_trial(small, "predictive", 7)
    c, _ = run_trial(small, "local", 7)
    d, _ = run_trial(small, "local", 8)
    assert deterministic(a) == deterministic(b)
    assert trace_a == trace_b
    assert a["trajectory_id"] == c["trajectory_id"]
    assert a["trajectory_id"] != d["trajectory_id"]


def test_mild_motion_can_complete_without_replanning(small):
    row, _ = run_trial(replace(small, amplitude_cm=0.01), "local", 3)
    assert row["success"]
    assert row["repairs"] == 0


def test_predictive_repair_can_precede_failure(small):
    settings = replace(small, correction_limit_cm=0.1)
    _, trace = run_trial(settings, "predictive", 0)
    repair = next(e for e in trace if e["event"] == "repair")
    assert repair["reason"] == "predicted_drift"
    assert repair["margin_cm"] < 0


def test_zero_frequency_is_stationary_even_with_nonzero_amplitude(small):
    row, _ = run_trial(replace(small, frequency_hz=0), "full", 2)
    assert row["success"]
    assert row["repairs"] == 0
    assert row["normalized_travel"] == pytest.approx(1)


def test_resumable_domain_preserves_completed_work(small):
    segments = construction(small)
    state = make_state(segments, Shear(small))
    state.done.update(range(3))
    setup_domain()
    plan = gtpyhop.find_plan(state, [("build_web",)])
    assert [a[1] for a in plan] == list(range(3, len(segments)))
    assert state.done == {0, 1, 2}  # search must not mutate the live state
    component = gtpyhop.find_plan(state, [("build_component", segments[3].task)])
    assert all(segments[a[1]].task == segments[3].task for a in component)


def test_prediction_detects_future_change_not_just_current_error(small):
    settings = replace(small, correction_limit_cm=0, attachment_tolerance_cm=0.1)
    motion = Shear(settings, phase=0)
    segments = construction(settings)
    # The lower frame endpoint has zero drift now, but moves in the horizon.
    seg = next(s for s in segments if s.end[1] == 0)
    target = motion.world(seg.end, 0)
    assert target == seg.end
    assert feasibility_margin([("place_segment", seg.index, target)], segments, motion, 0, settings) < 0


def test_finite_correction_is_not_instantaneous(small):
    settings = replace(small, amplitude_cm=1, frequency_hz=0.01)
    motion = Shear(settings, 0)
    segment = next(s for s in construction(settings) if s.end[1] == 0)
    target = motion.world(segment.end, 0)
    raw = execute(segment, target, segment.start, 0, motion, settings, False)
    corrected = execute(segment, target, segment.start, 0, motion, settings, True)
    assert corrected[1] > raw[1]
    assert corrected[4] > 0
    assert corrected[3] < raw[3]


def test_retry_budget_and_no_reexecution_of_completed_segments(small):
    settings = replace(small, correction_limit_cm=0, attachment_tolerance_cm=1e-8,
                       max_repairs_per_action=2)
    row, trace = run_trial(settings, "local_repair", 0)
    accepted = [e["index"] for e in trace if e["event"] == "action" and e["accepted"]]
    assert len(accepted) == len(set(accepted))
    assert not row["success"]
    assert row["failure_reason"] == "attachment_miss"
    failed = [e for e in trace if e["event"] == "action" and not e["accepted"]]
    assert len(failed) == 3
    assert row["repairs"] == 2


def test_time_limit_is_reported(small):
    row, _ = run_trial(replace(small, max_elapsed_s=0.01), "local_repair")
    assert not row["success"]
    assert row["failure_reason"] == "time_limit"


def test_integration_converges(small):
    coarse, _ = run_trial(replace(small, integration_step_s=0.05), "local", 0)
    fine, _ = run_trial(replace(small, integration_step_s=0.025), "local", 0)
    assert coarse["success"] == fine["success"]
    assert coarse["travel_cm"] == pytest.approx(fine["travel_cm"], rel=0.002)


@pytest.mark.parametrize("change", [
    {"frequency_hz": -1}, {"amplitude_cm": float("nan")}, {"radial_count": 3},
    {"prediction_samples": 1}, {"integration_step_s": 0}, {"capture_turns": 1.5},
    {"inner_radius_fraction": 0.99}, {"max_repairs_per_action": -1},
])
def test_invalid_settings(change):
    with pytest.raises(ValueError):
        Settings(**change)


def test_cli_artifacts_and_no_overwrite(tmp_path):
    output = tmp_path / "results"
    args = ["--seeds", "1", "--amplitudes", "0", "--frequencies", "0.05",
            "--controllers", "local", "--output", str(output), "--trace"]
    main(args)
    summary = json.loads((output / "summary.json").read_text())
    assert summary[0]["success_rate"] == 1
    assert summary[0]["success_ci95"][0] < 1
    assert (output / "trials.csv").exists()
    assert list(output.glob("*.svg"))
    assert json.loads((output / "metadata.json").read_text())["seeds"] == [1]
    with pytest.raises(SystemExit):
        main(args)


def test_config_and_summary(small):
    settings, experiment = load_settings()
    assert settings.width_cm == 30
    assert experiment["seeds"]
    rows = [run_trial(replace(small, amplitude_cm=0), c, seed)[0]
            for c in ("local", "predictive") for seed in (1, 2)]
    assert all(s["paired_success_difference_vs_local"] == 0 for s in summarize(rows))
