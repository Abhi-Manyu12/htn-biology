"""Integration checks against the actual construction geometry and actor."""
from dataclasses import replace

import pytest

from spider_web_mulder.experiment import run_trial
from spider_web_mulder.model import Settings, construction, make_state, Shear
from spider_web_mulder.reentrant import MulderPlanner


@pytest.fixture
def settings():
    return Settings(execution_mode='tracking', radial_count=4,
                    auxiliary_turns=1, capture_turns=1, integration_step_s=.5)


@pytest.mark.parametrize('controller', ['fixed','local','local_repair','filtered','full','predictive'])
def test_same_engine_clean_execution_agrees(settings, controller):
    a, _ = run_trial(settings, controller, 3, planner_backend='ipyhop_fresh')
    b, _ = run_trial(settings, controller, 3, planner_backend='ipyhop_retained')
    assert a['success'] == b['success']
    assert a['completed_actions'] == b['completed_actions']
    assert a['elapsed_s'] == pytest.approx(b['elapsed_s'])
    assert a['travel_cm'] == pytest.approx(b['travel_cm'])
    assert b['method_calls'] <= a['method_calls']


@pytest.mark.parametrize('backend', ['ipyhop_fresh', 'ipyhop_retained'])
@pytest.mark.parametrize('index', [0, 10, 25])
def test_transient_miss_preserves_prefix_and_actual_position(settings, backend, index):
    row, trace = run_trial(settings, 'local_repair', 2, planner_backend=backend,
                          forced_miss_index=index, record_planner_tree=True)
    assert row['success'] and row['repairs'] == 1
    actions = [e for e in trace if e['event'] == 'action']
    assert [e['index'] for e in actions if e['accepted']] == list(range(row['total_actions']))
    missed = next(i for i,e in enumerate(actions) if e['injected_miss'])
    assert actions[missed+1]['start_material_cm'] == actions[missed]['end_material_cm']
    assert actions[missed+1]['start_time_s'] >= actions[missed]['end_time_s']
    assert len([e for e in actions if e['injected_miss']]) == 1
    trees = [e for e in trace if e['event'] == 'planner_tree']
    assert len(trees) == 2
    assert trees[1]['done'] == list(range(index))
    assert trees[1]['reentry'] == (backend == 'ipyhop_retained')
    if backend == 'ipyhop_retained':
        assert trees[1]['failed_node'] in {n['id'] for n in trees[0]['nodes']}
        assert row['reentries'] == 1


def test_repeated_reentry_refreshes_observed_clock(settings):
    state = make_state(construction(settings), Shear(settings))
    backend = MulderPlanner('ipyhop_retained', [0], True)
    original = backend.plan(state)
    for stamp in (1., 2., 3.):
        state.snapshot_time = stamp
        result = backend.plan(state)
        assert result[0][2] == state.motion.world(state.segments[0].end, stamp)
        assert [a[1] for a in result] == [a[1] for a in original]
        assert state.done == set()
    assert backend.reentries == 3


def test_no_retry_policy_still_fails_on_injected_miss(settings):
    for mode in ('legacy','ipyhop_fresh','ipyhop_retained'):
        row, _ = run_trial(settings, 'local', planner_backend=mode, forced_miss_index=10)
        assert not row['success'] and row['repairs'] == 0


def test_recovery_cannot_remove_sensor_lag(settings):
    for mode in ('ipyhop_fresh','ipyhop_retained'):
        row, _ = run_trial(replace(settings,sensor_tau_s=1.), 'local_repair',
                           planner_backend=mode)
        assert not row['success']
        assert row['failure_reason'] == 'attachment_miss'


def test_invalid_backend_and_flat_are_rejected(settings):
    with pytest.raises(ValueError):
        run_trial(settings,'local',planner_backend='unknown')
    with pytest.raises(ValueError):
        run_trial(settings,'local',planner_backend='ipyhop_retained',hierarchy='flat')


def test_comparison_keeps_failed_planning_costs():
    from spider_web_mulder.recovery_comparison import analyze
    rows = [dict(complexity='small', profile='stress', controller='local_repair',
                 planner_backend=backend, seed=0, success=False, completed_actions=2,
                 method_calls=calls, planning_wall_s=.01, repairs=1,
                 elapsed_s=10., travel_cm=9.)
            for backend,calls in [('legacy',5),('ipyhop_fresh',10),('ipyhop_retained',7)]]
    _, contrasts = analyze(rows)
    fresh = {r['metric']:r for r in contrasts if r['contrast'].endswith('ipyhop_fresh')}
    assert fresh['method_calls']['mean_difference'] == -3
    assert fresh['method_calls']['n'] == 1
    assert fresh['elapsed_s']['n'] == 0
    assert fresh['elapsed_s']['mean_difference'] is None


def test_comparison_cli_creates_reviewable_evidence(tmp_path, monkeypatch):
    import spider_web_mulder.recovery_comparison as comparison
    monkeypatch.setattr(comparison, 'CONTROLLERS', ('local_repair',))
    monkeypatch.setattr(comparison, 'PROFILES', {'rigid':comparison.PROFILES['rigid']})
    output = tmp_path/'comparison'
    comparison.main(['--seeds','1','--output',str(output)])
    assert (output/'report.html').exists()
    assert (output/'metadata.json').exists()
    assert len((output/'trials.csv').read_text().splitlines()) == 7
    with pytest.raises(SystemExit):
        comparison.main(['--seeds','1','--output',str(output)])
