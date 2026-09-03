"""
stochastic.py — Seeded randomness for environmental noise and perturbations.

This is Way-Forward Part 1, Step 6 ("Replicability"): the simulation gains
two sources of environmental variability —

    1. Wind noise:            a multiplicative perturbation applied to every
                               movement/thread-laying distance cost.
    2. Anchor availability:   some anchor points may be randomly unavailable
                               in a given run, modelling reduced anchor
                               availability / a harsher environment.

Both are OFF by default (config.yaml -> stochastic.enabled: false), so the
existing deterministic baseline plan (70 actions, 600.1 cm — the regression
target in tests/test_planner.py) is completely unaffected unless a config
explicitly turns stochastic behaviour on.

Everything here draws from a single seeded `random.Random` instance stored
on the state (`state.rng`). Given the same seed and the same config, a run
is fully reproducible: this is the "random seed parameter" the Way-Forward
document asks for so reviewers can reproduce exact figures.
"""

import random

from .config_loader import CONFIG


def make_rng(seed=None):
    """
    Build a seeded RNG for one simulation run.

    Precedence: explicit `seed` argument > config.stochastic.seed > None
    (falls back to OS entropy — non-reproducible, only used if the caller
    deliberately opts out of a fixed seed).
    """
    if seed is None:
        seed = CONFIG.get("stochastic", {}).get("seed")
    return random.Random(seed)


def wind_noise_factor(rng):
    """
    Sample a multiplicative noise factor to apply to a single movement or
    thread-laying cost, modelling wind disturbance during construction.

    Returns 1.0 (no perturbation) whenever stochastic behaviour, or wind
    noise specifically, is disabled in config — so this is always safe to
    call unconditionally from operators.
    """
    stoch_cfg = CONFIG.get("stochastic", {})
    wind_cfg = stoch_cfg.get("wind", {})

    if not stoch_cfg.get("enabled", False) or not wind_cfg.get("enabled", False):
        return 1.0

    std = wind_cfg.get("noise_std", 0.0)
    factor = 1.0 + rng.gauss(0.0, std)
    # A gust should never fully cancel or reverse a cost; floor it well
    # above zero so distances stay physically meaningful.
    return max(factor, 0.1)


def select_available_anchors(all_nodes, rng):
    """
    Simulate reduced anchor-point availability for one run.

    Only nodes listed in config.stochastic.anchor_availability.removable_nodes
    are ever candidates for removal (the supporting-structure sticks and
    crossbars are never touched, since without them the spider has nowhere
    to start). Each candidate is independently dropped with probability
    `removal_prob`.

    Parameters
    ----------
    all_nodes : iterable of str
        The full set of structure nodes that would exist with no
        perturbation (typically `rigid.structure_nodes`).
    rng : random.Random

    Returns
    -------
    set of str
        A NEW set — `all_nodes` is never mutated.
    """
    stoch_cfg = CONFIG.get("stochastic", {})
    anchor_cfg = stoch_cfg.get("anchor_availability", {})

    available = set(all_nodes)

    if not stoch_cfg.get("enabled", False) or not anchor_cfg.get("enabled", False):
        return available

    removal_prob = anchor_cfg.get("removal_prob", 0.0)
    candidates = set(anchor_cfg.get("removable_nodes", [])) & available

    for node in sorted(candidates):  # sorted: draw order must be seed-stable
        if rng.random() < removal_prob:
            available.discard(node)

    return available
