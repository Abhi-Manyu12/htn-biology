from dataclasses import replace
import hashlib
import importlib
import json

import pytest

from spider_web_recovery.backends import Backend,VENDOR
from spider_web_recovery.benchmark import main,paired
from spider_web_recovery.domain import Config,World,achieved,edge,links,observe_anchor_loss,valid_capture
from spider_web_recovery.experiment import BACKENDS,SCENARIOS,run_trial


@pytest.mark.parametrize("scenario",SCENARIOS)
@pytest.mark.parametrize("backend",BACKENDS)
def test_common_recovery_contract(backend,scenario):
    config = Config(sectors=4,depth=2)
    result,trace,_ = run_trial(config,backend,scenario,2)
    possible = scenario not in ("unreachable","silk_depletion")
    assert result["success"] is possible
    assert result["event_fired"] is (scenario!="clean")
    assert result["silk_used_cm"]+result["silk_remaining_cm"]+result["silk_lost_cm"] == pytest.approx(config.silk_cm)
    assert result["unnecessary_repeats"] == 0
    assert result["repairs"] <= config.max_repairs
    assert result["attempts"] <= config.max_attempts
    for event in trace:
        if event["event"] == "action":
            assert event["after"]["clock_s"] >= event["before"]["clock_s"]
            assert event["after"]["silk_used"] >= event["before"]["silk_used"]
            if event["accepted"] and event["action"][0]=="move":
                assert event["before"]["position"] == event["action"][1]
                assert event["after"]["position"] == event["action"][2]
                assert edge(*event["action"][1:3]) not in event["before"]["blocked"]
    if possible:
        assert result["valid_radii"] == result["valid_captures"] == config.sectors
    else:
        assert result["failure_reason"] == "planning_infeasible"


def test_actual_upstream_is_unmodified_and_pinned():
    manifest = json.loads((VENDOR/"UPSTREAM.json").read_text())
    assert manifest["revision"] == "bdda21012b2396aed9a91980af8fbb71dbcb7075"
    for name,digest in manifest["sha256"].items():
        assert hashlib.sha256((VENDOR/name).read_bytes()).hexdigest()==digest


def test_retained_tree_reuses_prefix_and_rebuilds_suffix():
    result,trace,trees = run_trial(backend="ipyhop",scenario="permanent_anchor",seed=0)
    assert result["success"] and len(trees)==2
    assert trees[1]["label"]=="replan"
    assert trees[1]["failed_node"] is not None
    assert any(n["tag"]=="old" and n["kind"]=="A" for n in trees[1]["nodes"])
    assert any(n["tag"]=="new" and n["kind"]=="A" for n in trees[1]["nodes"])
    failed = next(e for e in trace if e["event"]=="action" and not e["accepted"])
    anchor = failed["action"][2]
    later = [e for e in trace if e["event"]=="action" and e["accepted"] and e["action"][0]=="capture"]
    assert all(anchor not in e["action"][2:4] for e in later)
    assert result["stale_preconditions"]==0


def test_component_cache_exposes_dependent_suffix_problem():
    component,_,_ = run_trial(backend="component",scenario="permanent_anchor",seed=0)
    retained,_,_ = run_trial(backend="ipyhop",scenario="permanent_anchor",seed=0)
    assert component["success"] and retained["success"]
    assert component["stale_preconditions"] > retained["stale_preconditions"]
    assert component["repairs"] > retained["repairs"]


def test_transient_failure_is_retry_not_permanent_blacklist():
    result,trace,trees = run_trial(backend="ipyhop",scenario="transient_attachment")
    assert result["success"] and result["repairs"]==0 and result["planning_calls"]==1
    assert len(trees)==1
    retry = next(e for e in trace if e["event"]=="retry")
    assert retry["reason"]=="transient_not_blacklisted"
    assert result["silk_used_cm"]==pytest.approx(76.2)


def test_prefix_damage_requires_real_reconstruction():
    result,trace,_ = run_trial(backend="ipyhop",scenario="prefix_damage")
    assert result["success"] and result["legitimate_restorations"]==1
    assert result["unnecessary_repeats"]==0
    assert result["silk_used_cm"] > 76.0
    restored = [e for e in trace if e["event"]=="action" and e["legitimate_restoration"]]
    assert len(restored)==1 and restored[0]["action"][1]==0


def test_anchor_loss_invalidates_actual_effects_not_history():
    state = World(Config())
    state.radii = {i:f"A{i}" for i in range(4)}
    state.captures = {i:(f"A{i}",f"A{(i-1)%4}") for i in range(4)}
    assert achieved(state)
    invalid = observe_anchor_loss(state,"A0")
    assert set(invalid)=={0,1}
    assert 0 not in state.radii and edge("hub","A0") not in links(state)
    assert not valid_capture(state,0) and not valid_capture(state,1)
    assert not achieved(state)


def test_failed_position_is_not_reset_to_hub():
    result,trace,_ = run_trial(backend="ipyhop",scenario="permanent_anchor")
    failed_index = next(i for i,e in enumerate(trace) if e["event"]=="action" and not e["accepted"])
    failed = trace[failed_index]
    assert failed["after"]["position"].startswith("A")
    resumed = next(e for e in trace[failed_index+1:] if e["event"]=="action" and e["action"][0]=="move")
    assert resumed["action"][1]==failed["after"]["position"]
    assert resumed["before"]["silk_remaining"]==pytest.approx(failed["after"]["silk_remaining"])
    assert result["recovery_retraced_cm"] > 0


def test_blocked_route_executes_detour_and_retraces_graph():
    result,trace,_ = run_trial(backend="ipyhop",scenario="route_block",seed=0)
    assert result["success"]
    event = next(e for e in trace if e["event"]=="action" and e["injected"])
    blocked = edge(*event["action"][1:3])
    later = [e for e in trace if e["event"]=="action" and e["accepted"] and e["action"][0]=="move"]
    assert any(edge(*e["action"][1:3])==edge("left","right") for e in later)
    assert all(edge(*e["action"][1:3])!=blocked for e in later)
    assert result["recovery_retraced_cm"] >= 0


def test_fresh_and_retained_same_engine_agree_on_clean_case():
    fresh,ft,_ = run_trial(backend="ipyhop_fresh",scenario="clean",seed=3)
    retained,rt,_ = run_trial(backend="ipyhop",scenario="clean",seed=3)
    for key in ("method_calls","ipyhop_iterations","travel_cm","silk_used_cm","elapsed_s"):
        assert fresh[key]==pytest.approx(retained[key])
    assert ft==rt


def test_empty_plan_is_not_success_for_exhausted_search():
    state = World(Config(silk_cm=0))
    assert Backend("ipyhop").plan(state) is None
    result,_,_ = run_trial(Config(silk_cm=0),backend="ipyhop",scenario="clean")
    assert not result["success"] and result["failure_reason"]=="planning_infeasible"


def test_strategy_is_restored_after_fresh_search():
    engine = importlib.import_module("gtpyhop.main")
    old = engine._current_seek_plan
    result,_,_ = run_trial(backend="fresh_root",scenario="permanent_anchor")
    assert result["success"]
    assert engine._current_seek_plan is old


@pytest.mark.parametrize("change",[{"max_repairs":0},{"max_attempts":1}])
def test_execution_budgets_terminate(change):
    result,_,_ = run_trial(replace(Config(),**change),backend="ipyhop",scenario="permanent_anchor")
    assert not result["success"]
    assert result["failure_reason"] in ("repair_budget","execution_budget")


def test_last_attachment_cannot_complete_after_deadline():
    config = Config(amplitude_cm=0)
    baseline,_,_ = run_trial(config,backend="ipyhop",scenario="clean")
    limited = replace(config,max_elapsed_s=baseline["elapsed_s"]-0.25)
    result,_,_ = run_trial(limited,backend="ipyhop",scenario="clean")
    assert not result["success"] and result["failure_reason"]=="execution_budget"
    assert result["elapsed_s"] <= limited.max_elapsed_s


def test_computational_costs_include_infeasible_pairs():
    rows = [run_trial(backend=b,scenario="silk_depletion")[0] for b in ("ipyhop_fresh","ipyhop")]
    contrasts = paired(rows)
    effort = next(r for r in contrasts if r["metric"]=="method_calls")
    travel = next(r for r in contrasts if r["metric"]=="travel_cm")
    assert effort["paired_n"]==1 and effort["mean_difference"] is not None
    assert travel["paired_n"]==0


def test_cli_outputs_and_preserves_previous_results(tmp_path):
    output = tmp_path/"run"
    args = ["--seeds","1","--sectors","4","--depths","0","--amplitudes","0",
            "--scenarios","permanent_anchor","--output",str(output),"--trace"]
    main(args)
    assert len(json.loads((output/"trials.json").read_text()))==4
    assert json.loads((output/"provenance.json").read_text())["fresh_strategy"]=="iterative_dfs_backtracking"
    assert list((output/"traces").rglob("tree_1.svg"))
    with pytest.raises(SystemExit):
        main(args)
