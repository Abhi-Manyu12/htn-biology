"""
test_baseline.py — Tests for baseline.py (Way-Forward Step 5, Group B).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from spider_web_htn_updated.baseline import (
    is_web_complete,
    enumerate_candidate_actions,
    run_baseline,
)
from spider_web_htn_updated.state import create_initial_state
from spider_web_htn_updated.config_loader import CONFIG


# ---------------------------------------------------------------------------
# is_web_complete
# ---------------------------------------------------------------------------

def test_is_web_complete_false_for_fresh_state():
    state = create_initial_state()
    assert is_web_complete(state) is False


def test_is_web_complete_true_when_all_structural_requirements_met():
    state = create_initial_state()
    dom = CONFIG["domain"]
    state.proto_hub_exists = True
    state.frame_count = dom["target_frame_count"]
    state.radii_count = dom["target_radii_count"]
    state.auxiliary_spiral_done = True
    state.capture_spiral_done = True
    assert is_web_complete(state) is True


def test_is_web_complete_false_if_any_single_requirement_missing():
    dom = CONFIG["domain"]
    base_kwargs = dict(
        proto_hub_exists=True,
        frame_count=dom["target_frame_count"],
        radii_count=dom["target_radii_count"],
        auxiliary_spiral_done=True,
        capture_spiral_done=True,
    )
    for missing_key in base_kwargs:
        state = create_initial_state()
        for k, v in base_kwargs.items():
            setattr(state, k, v)
        # Knock out just this one requirement
        if isinstance(base_kwargs[missing_key], bool):
            setattr(state, missing_key, False)
        else:
            setattr(state, missing_key, 0)
        assert is_web_complete(state) is False, f"should fail with {missing_key} unmet"


# ---------------------------------------------------------------------------
# enumerate_candidate_actions
# ---------------------------------------------------------------------------

def test_enumerate_candidate_actions_nonempty_on_fresh_state():
    import random
    state = create_initial_state()
    rng = random.Random(1)
    candidates = enumerate_candidate_actions(state, rng)
    assert len(candidates) > 0
    for op_func, args in candidates:
        assert callable(op_func)
        assert isinstance(args, tuple)


def test_enumerate_candidate_actions_gates_later_stages_behind_proto_hub():
    """Frame/radius/spiral actions should not be offered before the
    proto-hub exists."""
    import random
    state = create_initial_state()
    rng = random.Random(1)
    assert state.proto_hub_exists is False

    candidates = enumerate_candidate_actions(state, rng)
    op_names = {op.__name__ for op, _ in candidates}
    assert "lay_frame_thread" not in op_names
    assert "lay_radius" not in op_names
    assert "build_spiral_segment" not in op_names


def test_enumerate_candidate_actions_offers_spiral_markers_once_hub_exists():
    import random
    state = create_initial_state()
    hub = CONFIG["domain"]["default_hub_name"]
    state.nodes.add(hub)
    state.spider_pos = hub
    state.proto_hub_exists = True
    state.proto_hub_pos = hub
    rng = random.Random(1)

    candidates = enumerate_candidate_actions(state, rng)
    op_names = {op.__name__ for op, _ in candidates}
    assert "mark_auxiliary_spiral_done" in op_names
    assert "mark_capture_spiral_done" in op_names


# ---------------------------------------------------------------------------
# run_baseline — reproducibility and structure of the result dict
# ---------------------------------------------------------------------------

def test_run_baseline_same_seed_is_reproducible():
    r1 = run_baseline(seed=7, max_steps=3000)
    r2 = run_baseline(seed=7, max_steps=3000)
    assert r1["success"] == r2["success"]
    assert r1["steps_taken"] == r2["steps_taken"]
    assert r1["energy_expended"] == pytest.approx(r2["energy_expended"], abs=1e-9)


def test_run_baseline_returns_expected_keys():
    result = run_baseline(seed=1, max_steps=500)
    for key in ("success", "steps_taken", "successful_actions",
                "energy_expended", "decomposition_depth", "seed_used", "final_state"):
        assert key in result


def test_run_baseline_decomposition_depth_is_zero():
    # Group B has no task hierarchy — this should always report 0, in
    # direct contrast to whatever depth metric Group A eventually reports.
    result = run_baseline(seed=1, max_steps=500)
    assert result["decomposition_depth"] == 0


def test_run_baseline_can_succeed_within_generous_budget():
    """
    Not a strict guarantee (it's a random walker), but with a generous
    step budget across a handful of seeds, at least one should succeed —
    this catches the earlier real bug where the spiral-completion markers
    were missing from the candidate set and success was NEVER reachable
    regardless of budget.
    """
    successes = [run_baseline(seed=s, max_steps=8000)["success"] for s in range(1, 6)]
    assert any(successes), "expected at least one of 5 seeded runs to succeed"


def test_run_baseline_respects_max_steps_budget():
    result = run_baseline(seed=1, max_steps=10)
    assert result["steps_taken"] <= 10