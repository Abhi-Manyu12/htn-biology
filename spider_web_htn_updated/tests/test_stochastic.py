"""
test_stochastic.py — Unit tests for stochastic.py (Way-Forward Step 6).

These deliberately build config dicts in-process rather than relying on the
module-level CONFIG singleton, so they can exercise enabled/disabled
combinations without needing a subprocess (contrast with test_planner.py's
config-swap tests, which do need a subprocess because of end-to-end
module-level binding).
"""

import random

import pytest

from spider_web_htn_updated import stochastic as stoch


# ---------------------------------------------------------------------------
# make_rng
# ---------------------------------------------------------------------------

def test_make_rng_with_explicit_seed_is_reproducible():
    rng1 = stoch.make_rng(seed=7)
    rng2 = stoch.make_rng(seed=7)
    assert [rng1.random() for _ in range(5)] == [rng2.random() for _ in range(5)]


def test_make_rng_different_seeds_diverge():
    rng1 = stoch.make_rng(seed=1)
    rng2 = stoch.make_rng(seed=2)
    assert [rng1.random() for _ in range(5)] != [rng2.random() for _ in range(5)]


def test_make_rng_returns_random_instance():
    rng = stoch.make_rng(seed=42)
    assert isinstance(rng, random.Random)


# ---------------------------------------------------------------------------
# wind_noise_factor
# ---------------------------------------------------------------------------

def test_wind_noise_factor_is_noop_when_stochastic_disabled(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": False,
        "wind": {"enabled": True, "noise_std": 0.5},
    })
    rng = stoch.make_rng(seed=1)
    assert stoch.wind_noise_factor(rng) == 1.0


def test_wind_noise_factor_is_noop_when_wind_disabled(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": True,
        "wind": {"enabled": False, "noise_std": 0.5},
    })
    rng = stoch.make_rng(seed=1)
    assert stoch.wind_noise_factor(rng) == 1.0


def test_wind_noise_factor_perturbs_when_fully_enabled(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": True,
        "wind": {"enabled": True, "noise_std": 0.2},
    })
    rng = stoch.make_rng(seed=1)
    factors = [stoch.wind_noise_factor(rng) for _ in range(50)]
    assert any(f != 1.0 for f in factors)


def test_wind_noise_factor_never_drops_below_floor(monkeypatch):
    # Large noise_std should still be clamped well above zero.
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": True,
        "wind": {"enabled": True, "noise_std": 5.0},
    })
    rng = stoch.make_rng(seed=3)
    factors = [stoch.wind_noise_factor(rng) for _ in range(200)]
    assert all(f >= 0.1 for f in factors)


def test_wind_noise_factor_reproducible_given_same_seed():
    def run(seed):
        rng = stoch.make_rng(seed=seed)
        # Temporarily point stoch.CONFIG at an enabled config for this run.
        return [stoch.wind_noise_factor(rng) for _ in range(10)]

    stoch.CONFIG["stochastic"] = {
        "enabled": True,
        "wind": {"enabled": True, "noise_std": 0.1},
    }
    try:
        assert run(99) == run(99)
    finally:
        stoch.CONFIG.pop("stochastic", None)


# ---------------------------------------------------------------------------
# select_available_anchors
# ---------------------------------------------------------------------------

ALL_NODES = {"a", "b", "c", "d", "sticks_are_never_removable"}


def test_select_available_anchors_noop_when_disabled(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": False,
        "anchor_availability": {
            "enabled": True, "removal_prob": 1.0,
            "removable_nodes": list(ALL_NODES),
        },
    })
    rng = stoch.make_rng(seed=1)
    result = stoch.select_available_anchors(ALL_NODES, rng)
    assert result == ALL_NODES


def test_select_available_anchors_never_touches_non_removable_nodes(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": True,
        "anchor_availability": {
            "enabled": True, "removal_prob": 1.0,
            "removable_nodes": ["a", "b"],  # only these are candidates
        },
    })
    rng = stoch.make_rng(seed=1)
    result = stoch.select_available_anchors(ALL_NODES, rng)
    # c, d, and the "structure" node must always survive.
    assert {"c", "d", "sticks_are_never_removable"} <= result


def test_select_available_anchors_does_not_mutate_input(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": True,
        "anchor_availability": {
            "enabled": True, "removal_prob": 1.0,
            "removable_nodes": ["a"],
        },
    })
    original = set(ALL_NODES)
    rng = stoch.make_rng(seed=1)
    stoch.select_available_anchors(ALL_NODES, rng)
    assert ALL_NODES == original


def test_select_available_anchors_reproducible_given_same_seed(monkeypatch):
    monkeypatch.setitem(stoch.CONFIG, "stochastic", {
        "enabled": True,
        "anchor_availability": {
            "enabled": True, "removal_prob": 0.5,
            "removable_nodes": list(ALL_NODES),
        },
    })
    r1 = stoch.select_available_anchors(ALL_NODES, stoch.make_rng(seed=123))
    r2 = stoch.select_available_anchors(ALL_NODES, stoch.make_rng(seed=123))
    assert r1 == r2
