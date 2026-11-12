"""E1 protocol contracts; independently replay accepted effects and check exposure."""
from dataclasses import replace
import json

import pytest

from spider_web_mulder.model import Settings, Shear
from spider_web_recovery.domain import Config, World, links, edge, valid_capture, valid_radius
from spider_web_recovery.e1 import CONTROLLERS, SCENARIOS, intervene, perform, run_trial
from spider_web_recovery.e1_benchmark import audit_exposure, main, paired
from spider_web_recovery.experiment import OPS, observation


def observed_world(config, observed):
    state = World(config)
    for name in ("position", "position_material", "clock_s", "silk_remaining", "silk_used", "silk_lost"):
        setattr(state, name, observed[name])
    state.radii = observed["radii"].copy()
    state.captures = observed["captures"].copy()
    state.restore_captures = set(observed["restore_captures"])
    state.blocked = set(map(tuple, observed["blocked"]))
    for anchor in observed["unavailable"]:
        state.available[anchor] = False
    return state


@pytest.mark.parametrize("sectors", [4, 8])
@pytest.mark.parametrize("amplitude", [0, 10])
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_matched_case_contract(sectors, amplitude, scenario):
    config = Config(sectors=sectors, depth=0, amplitude_cm=amplitude)
    rows = []
    for controller in CONTROLLERS:
        row, trace, _ = run_trial(config, controller, scenario, 3)
        rows.append(row)
        feasible = scenario in ("intact", "damage_single", "damage_multi", "transfer_partial")
        expected = feasible and (controller != "history" or scenario == "intact")
        assert row["success"] is expected
        assert row["event_fired"]
        assert row["silk_used_cm"]+row["silk_remaining_cm"]+row["silk_lost_cm"] == pytest.approx(config.silk_cm)
        assert row["unnecessary_repeats"] == 0
        assert row["attempts"] <= config.max_attempts
        assert row["replans"] <= config.max_repairs
        if row["success"]:
            assert row["valid_radii"] == row["valid_captures"] == sectors
            assert row["restorations"] > 0 if scenario != "intact" else row["restorations"] == 0
        for event in trace:
            if event["event"] != "action":
                continue
            before, after = event["before"], event["after"]
            assert after["clock_s"] >= before["clock_s"]
            state = observed_world(config, before)
            action = event["action"]
            candidate = OPS[action[0]](state.copy(), *action[1:])
            assert (candidate is not None) == event["accepted"]
            if event["accepted"]:
                assert after["radii"] == candidate.radii
                assert after["captures"] == candidate.captures
                assert after["silk_used"] == pytest.approx(candidate.silk_used)
                if action[0] == "move":
                    assert edge(*action[1:3]) in links(state)
                    assert before["position"] == action[1]
                    assert after["position"] == action[2]
                if action[0] in ("attach", "capture"):
                    valid = valid_radius(state, action[1]) if action[0] == "attach" else valid_capture(state, action[1])
                    assert not valid  # Independent redundant-work check.
    assert audit_exposure(rows) == dict(matched_cases=1, identical_exposed_cases=1,
                                        all_controllers_unexposed_cases=0, mismatches=0)


def test_transfer_keeps_actor_costs_and_accounts_for_donor_separately():
    row, trace, _ = run_trial(Config(depth=0), "state_rules", "transfer_partial", 0)
    event = next(e for e in trace if e["event"] == "intervention")
    before, after = event["before"], event["after"]
    for key in ("position", "position_material", "silk_remaining", "silk_used", "silk_lost"):
        assert before[key] == after[key]
    assert after["clock_s"]-before["clock_s"] == pytest.approx(5.)
    assert event["external_displacement_cm"] == 0
    assert event["displaced_web_silk_cm"] == pytest.approx(4*14+2*5)
    assert event["donor_web_silk_cm"] == pytest.approx(3*14+5)
    assert row["silk_used_cm"] == pytest.approx(5*14+5*5)
    assert all(a.startswith("B") for a in after["radii"].values())


@pytest.mark.parametrize("scenario", ["damage_single", "damage_multi", "transfer_partial"])
def test_retained_reentry_uses_real_unexecuted_leaf_and_retains_prefix(scenario):
    row, trace, trees = run_trial(Config(depth=0), "retained_htn", scenario, 0, record_trees=True)
    assert row["success"] and len(trees) == 2
    replan = next(e for e in trace if e["event"] == "replan")
    executed = {e["node_id"] for e in trace[:trace.index(replan)] if e["event"] == "action"}
    leaf = next(n for n in trees[0]["nodes"] if n["id"] == replan["failed_node"])
    assert leaf["kind"] == "A" and leaf["id"] not in executed
    assert trees[1]["failed_node"] == leaf["id"]
    assert trees[1]["label"] == "replan"
    assert any(n["tag"] == "old" and n["kind"] == "A" for n in trees[1]["nodes"])
    assert any(n["tag"] == "new" and n["kind"] == "A" for n in trees[1]["nodes"])
    _, fresh_trace, fresh_trees = run_trial(Config(depth=0), "fresh_htn", scenario, 0, record_trees=True)
    assert all(t["label"] == "fresh_plan" and t["failed_node"] is None for t in fresh_trees)
    assert next(e for e in fresh_trace if e["event"] == "replan")["failed_node"] is None


@pytest.mark.parametrize("controller", CONTROLLERS)
@pytest.mark.parametrize("change", [dict(silk_cm=0), dict(max_elapsed_s=.1), dict(max_attempts=1)])
def test_early_failure_is_not_success_or_event_exposure(controller, change):
    config = replace(Config(depth=0), **change)
    row, _, _ = run_trial(config, controller)
    assert not row["success"] and not row["event_fired"]
    assert row["attempts"] <= config.max_attempts
    assert row["recovery_policy_wall_s"] is None


@pytest.mark.parametrize("controller", ["fresh_htn", "retained_htn"])
def test_repair_budget_stops_before_replanning(controller):
    row, _, _ = run_trial(Config(depth=0, max_repairs=0), controller)
    assert row["event_fired"] and not row["success"]
    assert row["failure_reason"] == "repair_budget" and row["replans"] == 0


def test_precondition_rejection_and_deadline_do_not_commit_effects():
    config = Config(max_elapsed_s=.1)
    settings = Settings(execution_mode="tracking", max_elapsed_s=.1)
    state = World(config)
    initial = observation(state)
    after, accepted, _, _ = perform(state, ("capture", 0, "A0", "A3", ("capture", 0)), Shear(settings, 0), settings)
    assert not accepted and after.captures == {} and after.silk_used == 0
    state = World(config)
    state.position = "A0"
    after, accepted, _, terminal = perform(state, ("attach", 0, "A0", ("radius", 0)), Shear(settings, 0), settings)
    assert not accepted and terminal == "execution_budget"
    assert after.radii == {} and after.silk_remaining == initial["silk_remaining"]


@pytest.mark.parametrize("seed", [-1, True, 1.5])
def test_invalid_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        run_trial(seed=seed)


def test_transfer_rejects_unaligned_position():
    state = World(Config())
    state.position = "left"
    with pytest.raises(ValueError, match="hub"):
        intervene(state, "transfer_partial", 0)


def test_analysis_rejects_mismatch_and_reports_conditional_denominators():
    rows = [run_trial(Config(depth=0), c, "damage_resource", 0)[0] for c in CONTROLLERS]
    contrasts = paired(rows)
    assert all(r["paired_n"] == 0 and r["mean_difference"] is None and r["ci95"] is None
               for r in contrasts if r["metric"] == "travel_cm")
    assert all(r["paired_n"] == 1 for r in contrasts if r["metric"] == "success")
    with pytest.raises(ValueError, match="duplicate"):
        audit_exposure(rows+rows[:1])
    rows[0]["post_state_sha256"] = "tampered"
    with pytest.raises(ValueError, match="Mismatched"):
        paired(rows)


def test_runner_saves_provenance_and_refuses_overwrite(tmp_path):
    output = tmp_path/"e1"
    args = ["--output", str(output), "--seeds", "1", "--sectors", "4", "--amplitudes", "0", "--scenarios", "intact"]
    main(args)
    manifest = json.loads((output/"provenance.json").read_text())
    assert manifest["seeds"] == [0]
    assert manifest["tree_snapshots_in_primary"] is False
    assert "docs/research/E1_PROTOCOL.md" in manifest["source_sha256"]
    assert manifest["physical_settings"][0]["execution_mode"] == "tracking"
    hashes = json.loads((output/"artifact_sha256.json").read_text())
    assert "trials.csv" in hashes and "completion.svg" in hashes
    original = (output/"trials.csv").read_bytes()
    with pytest.raises(SystemExit):
        main(args)
    assert (output/"trials.csv").read_bytes() == original
