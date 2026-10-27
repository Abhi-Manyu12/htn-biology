from dataclasses import replace
import csv
import json
import math

import numpy as np
import pytest

from spider_web_mulder.experiment import execute, feasibility_margin, run_trial
from spider_web_mulder.measurements import area, crossings, hull, measure_web
from spider_web_mulder.model import Settings, Shear, construction
from spider_web_mulder.reference import calibrate_rigid, individual_means, load_reference, reference_effects
from spider_web_mulder.tracking import SampledTrack
from spider_web_mulder.validation import compare_biological_effects, paired_analysis, profiles, wilson


@pytest.fixture
def tracking():
    return Settings(execution_mode="tracking",radial_count=8,auxiliary_turns=1,capture_turns=2)


def test_tracking_moving_target_and_explicit_dwell(tracking):
    segment = next(s for s in construction(tracking) if s.end[1] == 0)
    motion = Shear(tracking,0.4)
    details = {}
    result = execute(segment,motion.world(segment.end,0),segment.start,0,motion,tracking,True,details=details)
    assert result[3] < 1e-8
    assert details["contact_dwell_s"] == pytest.approx(tracking.attachment_time_s)
    assert details["end_time_s"]-details["arrival_time_s"] == pytest.approx(tracking.attachment_time_s)
    assert details["contact_reached"]


def test_relative_speed_bound_and_deadline(tracking):
    segment = next(s for s in construction(tracking) if s.end[1] == 0)
    settings = replace(tracking,max_action_time_s=1)
    motion = Shear(settings,0.3)
    points = []
    details = {}
    execute(segment,motion.world(segment.end,0),segment.start,0,motion,settings,True,
            details=details,observe=lambda t,p:points.append((t,p)))
    assert details["action_timed_out"]
    assert details["end_time_s"] <= settings.max_action_time_s
    for (a,p),(b,q) in zip(points,points[1:]):
        if b-a > 1e-12:
            dx,dy = q[0]-p[0],q[1]-p[1]
            for stamp in np.linspace(a,b,5):
                relative = math.hypot(dx-motion.displacement(stamp)/settings.height_cm*dy,dy)/(b-a)
                assert relative <= settings.speed_cm_s+1e-8


def test_no_time_reversal_when_deadline_already_passed(tracking):
    s = replace(tracking,max_elapsed_s=1)
    seg = construction(s)[0]
    result = execute(seg,seg.end,seg.start,2,Shear(s),s,True)
    assert result[1] >= 2


def test_tracking_flat_ablation_matches_actions_without_method_calls(tracking):
    htn,trace = run_trial(tracking,"local",5,hierarchy="htn",record_path=True)
    flat,_ = run_trial(tracking,"local",5,hierarchy="flat",record_path=True)
    assert htn["success"] and flat["success"]
    for metric in ("elapsed_s","travel_cm","sampled_travel_10s_cm","web_area_cm2"):
        assert htn[metric] == pytest.approx(flat[metric])
    assert htn["method_calls"] > 0 and flat["method_calls"] == 0


def test_predictive_tracking_margin_is_not_frozen_target_drift(tracking):
    s = replace(tracking,sensor_tau_s=0)
    seg = next(s for s in construction(s) if s.end[1] == 0)
    actions = [("place_segment",seg.index,(-100,0))]
    assert feasibility_margin(actions,construction(s),Shear(s),0,s) > 0
    lagged = replace(s,sensor_tau_s=5)
    assert feasibility_margin(actions,construction(lagged),Shear(lagged),0,lagged) < 0


def test_sensory_lag_can_change_outcomes(tracking):
    ideal,_ = run_trial(tracking,"local",0)
    lagged,_ = run_trial(replace(tracking,sensor_tau_s=5),"local",0)
    assert ideal["success"]
    assert not lagged["success"]


def test_tracking_step_refinement(tracking):
    coarse,_ = run_trial(replace(tracking,integration_step_s=0.1),"local",4)
    fine,_ = run_trial(replace(tracking,integration_step_s=0.05),"local",4)
    assert coarse["success"] and fine["success"]
    assert coarse["elapsed_s"] == pytest.approx(fine["elapsed_s"],rel=0.005)


def test_phase_wait_is_an_actual_htn_alternative():
    s = Settings(execution_mode="tracking",method_policy="phase_wait",speed_cm_s=0.5)
    row,trace = run_trial(s,"local",0)
    waits = [e for e in trace if e["event"] == "method_wait"]
    assert row["success"] and waits
    assert row["method_waits"] == len(waits)
    assert row["method_wait_s"] == pytest.approx(sum(e["wait_s"] for e in waits))
    assert all(0 < e["wait_s"] <= s.max_method_wait_s for e in waits)


def test_polygon_and_intersection_measurements():
    square = [(-1,-1),(1,-1),(1,1),(-1,1)]
    assert area(hull(square+[(0,0)])) == 4
    chords = list(zip(square,square[1:]+square[:1]))
    assert crossings(chords,(0,0),(1,0)) == pytest.approx([1])
    # A ray through a shared vertex must count it once.
    assert crossings(chords,(0,0),(1,1)) == pytest.approx([1])


def test_table_one_formulas_and_partial_web(tracking):
    s = replace(tracking,amplitude_cm=0,web_width_fraction=0.8,web_height_fraction=0.9)
    row,_ = run_trial(s,"local")
    assert row["web_area_cm2"] == pytest.approx(24*27)
    assert row["eccentricity"] == pytest.approx(abs(1-24/27))
    assert 0 < row["capture_spiral_area_cm2"] < row["web_area_cm2"]
    assert row["mean_capture_spiral_count"] == pytest.approx(2.5)
    assert row["radial_count_measured"] == 8
    partial,_ = run_trial(replace(s,max_action_time_s=1),"local")
    assert not partial["success"]
    assert partial["web_area_cm2"] is None


def test_camera_cadence_and_phase_allocation(tracking):
    camera = SampledTrack(10)
    camera.observe(0,(0,0))
    camera.observe(25,(25,0))
    assert camera.finish(25,(25,0)) == 25
    assert [p["time_s"] for p in camera.samples] == [0,10,20,25]
    row,trace = run_trial(tracking,"local",record_path=True)
    assert row["sampled_travel_10s_cm"] <= row["travel_cm"]+1e-6
    assert sum(row[f"sampled_{phase}_travel_pct"] for phase in ("frame","radials","auxiliary","capture")) == pytest.approx(100)
    assert trace[-1]["event"] == "camera_track"


def test_paired_intervals_exclude_failed_costs(tracking):
    rows = []
    for seed in range(3):
        for a in (0,10):
            row,_ = run_trial(replace(tracking,amplitude_cm=a),"local",seed,record_path=True)
            rows.append(dict(profile="test",**row))
    rows[-1]["success"] = False
    result = paired_analysis(rows,100)
    completion = next(r for r in result if r["metric"] == "completion")
    duration = next(r for r in result if r["metric"] == "elapsed_s")
    assert completion["trials"] == 3 and completion["successes"] == 2
    assert duration["paired_n"] == 2
    assert completion["ci95"] is not None
    assert wilson(3,3)[0] < 1


def test_rigid_calibration_does_not_use_moving_outcomes(tracking):
    truth = replace(tracking,amplitude_cm=0,web_width_fraction=0.8,web_height_fraction=0.9,speed_cm_s=0.5)
    measured,_ = run_trial(truth,"local")
    rigid = dict(measured,spider_id="one",trial_id="R1",condition="rigid")
    moving = dict(rigid,elapsed_s=999999,trial_id="M1",condition="moving")
    fit,metadata = calibrate_rigid(tracking,[rigid,moving])
    assert fit.web_width_fraction == pytest.approx(0.8)
    assert fit.web_height_fraction == pytest.approx(0.9)
    assert fit.speed_cm_s == pytest.approx(0.5)
    assert not metadata["moving_observations_used_for_fitting"]


def test_reference_import_and_equal_spider_weight(tmp_path):
    path = tmp_path/"reference.csv"
    path.write_text("spider_id,trial_id,condition,elapsed_s\na,R1,rigid,10\na,R2,rigid,20\na,M1,moving,30\nb,R1,rigid,100\nb,M1,moving,110\n")
    rows = load_reference(path)
    assert individual_means(rows,"rigid","elapsed_s") == {"a":15,"b":100}
    assert reference_effects(rows)["elapsed_s"]["mean_paired_difference"] == 12.5
    path.write_text("spider_id,trial_id,condition,elapsed_s\na,R1,rigid,nan\n")
    with pytest.raises(ValueError):
        load_reference(path)


def test_validation_profiles_preserve_explicit_ablation_controls(tracking):
    specs = profiles(tracking,"full",30)
    assert len(specs) == 12
    assert all(spec["conditions"].count((0,0)) == 1 for spec in specs)
    assert next(s for s in specs if s["name"]=="flat_tracking")["hierarchy"] == "flat"
    assert next(s for s in specs if s["name"]=="phase_wait")["settings"].method_policy == "phase_wait"


def test_biological_comparison_uses_camera_travel_units():
    comparison = dict(profile="tracking",controller="local",amplitude_cm=10,frequency_hz=0.05,
                      metric="sampled_travel_10s_cm",paired_n=30,mean_difference=2.,ci95=[1.,3.])
    result = compare_biological_effects([comparison],{"travel_cm":dict(paired_spiders=5,mean_paired_difference=1.)})
    assert result[0]["metric"] == "travel_cm"
    assert result[0]["simulated"]["mean_paired_difference"] == 2
    assert result[0]["observed"]["paired_spiders"] == 5
