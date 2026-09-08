"""
baseline.py — Group B: Flat-State (non-hierarchical) baseline agent.

Way-Forward Part 1, Step 5 ("Comparison"). The roadmap calls for benchmarking
the HTN-based model (Group A) against a non-hierarchical baseline, "like a
random walker or a simple reactive agent", to show the hierarchical approach
is more energy-efficient and/or more resilient to disruption.

Design choice: a RANDOM WALKER, not true A*/BFS over the raw state space.
A literal shortest-path search here is intractable — the action space is
effectively unbounded (walk/lay_thread/etc. accept arbitrary node pairs, and
nothing stops the agent revisiting a node), so "search for the shortest path"
would need the exact same domain knowledge (which anchors matter, what order
things go in) that the HTN encodes — defeating the point of a *non*-
hierarchical baseline. The roadmap explicitly allows "a simple reactive
agent" as an alternative to A*/BFS; a seeded random walker is the simplest
faithful instance of that: at each step it enumerates the actions that are
*structurally plausible* (not necessarily legal — legality is still checked
by the real operator preconditions in operators.py) and picks uniformly at
random among them, with no notion of task decomposition, subgoals, or
ordering.

Fairness with Group A (the HTN model):
  - Uses the exact same operator functions from operators.py, so both
    agents are bound by identical preconditions and identical energy
    accounting (including wind noise, when enabled).
  - Uses the exact same create_initial_state(seed=...), so both agents see
    the same environment, the same anchor-availability perturbation, and
    the same wind noise stream for a given seed.
  - Success is judged by `is_web_complete`, a STRUCTURAL criterion (frame
    count, radii count, both spirals done) shared by both agents — the
    baseline never calls `mark_web_complete` for "free"; that operator
    unconditionally sets a flag and would let a lucky agent claim success
    without actually building anything, which is a real gap.

This module intentionally does not touch operators.py / methods.py: it is a
pure consumer of the same primitives, run through a different (flat)
control loop, so a diff between HTN behaviour and baseline behaviour can
never be attributed to the two models secretly using different physics.
"""

import random

from .config_loader import CONFIG
from .state import create_initial_state, rigid
from . import operators as ops
from . import methods as mtd

_DOMAIN = CONFIG["domain"]
_TARGET_FRAME_COUNT = _DOMAIN["target_frame_count"]
_TARGET_RADII_COUNT = _DOMAIN["target_radii_count"]
_DEFAULT_HUB_NAME = _DOMAIN["default_hub_name"]


# ---------------------------------------------------------------------------
# Shared structural completion criterion (Group A and Group B both use this
# to judge success — neither gets to declare victory via mark_web_complete
# alone).
# ---------------------------------------------------------------------------

def is_web_complete(state):
    """
    True once the web has all structurally required parts built:
    a proto-hub, enough frame threads, enough radii, and both spirals.

    This mirrors what the HTN's `build_remaining_web` / `finalise_web`
    methods require before they would ever call `mark_web_complete`, made
    explicit here so the flat-state baseline has the same bar to clear.
    """
    return (
        state.proto_hub_exists
        and state.frame_count >= _TARGET_FRAME_COUNT
        and state.radii_count >= _TARGET_RADII_COUNT
        and state.auxiliary_spiral_done
        and state.capture_spiral_done
    )


# ---------------------------------------------------------------------------
# Candidate action enumeration.
#
# Each candidate is (operator_function, args_tuple). "Structurally
# plausible" means: the argument types/shape make sense (e.g. walk needs a
# reachable neighbour, lay_radius needs the agent to plausibly be at a hub),
# not that the operator is guaranteed to succeed — operators.py's own
# precondition checks are the real legality gate, exactly as for Group A.
# ---------------------------------------------------------------------------

def _neighbours(state, node):
    """Nodes directly reachable from *node* by one structural or thread edge."""
    neighbours = set()
    for a, b in rigid.walkable_edges:
        if a == node and b in state.nodes:
            neighbours.add(b)
        elif b == node and a in state.nodes:
            neighbours.add(a)
    for n1, n2, _ in state.threads:
        if n1 == node and n2 in state.nodes:
            neighbours.add(n2)
        elif n2 == node and n1 in state.nodes:
            neighbours.add(n1)
    return neighbours


def enumerate_candidate_actions(state, rng):
    """
    Return a list of (operator_function, args) candidates given the current
    state. The random walker samples uniformly from this list each step.
    """
    pos = state.spider_pos
    hub = state.proto_hub_pos or _DEFAULT_HUB_NAME
    known_nodes = list(state.nodes)
    candidates = []

    # walk: to any direct neighbour of current position
    for n in _neighbours(state, pos):
        candidates.append((ops.walk, (pos, n)))

    # attach_dragline: always plausible at current position
    candidates.append((ops.attach_dragline, (pos,)))

    # lay_thread: current position to some other known node (generic bridge/dragline)
    for n in known_nodes:
        if n != pos:
            candidates.append((ops.lay_thread, (pos, n, "dragline")))

    # anchor: establish the hub at the current position, if not already established
    if not state.proto_hub_exists:
        candidates.append((ops.anchor, (hub,)))

    # reel_up / insert_radius: only meaningful once a dragline thread exists
    # from the current position to somewhere else
    for n1, n2, ttype in state.threads:
        if ttype == "dragline":
            if n1 == pos:
                candidates.append((ops.reel_up, (n1, n2)))
                candidates.append((ops.insert_radius, (n2, n1)))
            elif n2 == pos:
                candidates.append((ops.reel_up, (n2, n1)))
                candidates.append((ops.insert_radius, (n1, n2)))

    # mark_proto_hub: plausible once standing at the (candidate) hub
    if not state.proto_hub_exists and pos == hub:
        candidates.append((ops.mark_proto_hub, (hub,)))

    # lay_frame_thread / lay_radius / build_spiral_segment: current position
    # to some other known node — only meaningful once the proto-hub exists,
    # mirroring the fact that Zschokke's later stages only begin afterward
    if state.proto_hub_exists:
        for n in known_nodes:
            if n != pos:
                candidates.append((ops.lay_frame_thread, (pos, n)))
                candidates.append((ops.lay_radius, (pos, n)))
                candidates.append((ops.build_spiral_segment, (pos, n, "auxiliary_spiral")))
                candidates.append((ops.build_spiral_segment, (pos, n, "capture_spiral")))

        # mark_auxiliary_spiral_done / mark_capture_spiral_done: these are
        # the pseudo-operators that actually flip the completion flags
        # is_web_complete() checks. Like mark_web_complete, they carry no
        # precondition in operators.py/methods.py beyond "not already done"
        # (the HTN itself calls them unconditionally right after its
        # scripted spiral sequence, with no check that the spiral is
        # structurally sufficient) — so the flat agent gets the same
        # (weak) bar to clear, not a stricter one.
        if not state.auxiliary_spiral_done:
            candidates.append((mtd.mark_auxiliary_spiral_done, ()))
        if not state.capture_spiral_done:
            candidates.append((mtd.mark_capture_spiral_done, ()))

    return candidates


# ---------------------------------------------------------------------------
# The random walker itself
# ---------------------------------------------------------------------------

def run_baseline(seed=None, max_steps=2000, config_overrides=None):
    """
    Run the Group B flat-state random-walker agent once.

    Parameters
    ----------
    seed : int, optional
        RNG seed — forwarded to create_initial_state so Group B experiences
        the same environment/perturbation stream as Group A would for the
        same seed. A second, independent seeded RNG drives the walker's
        own action-selection randomness (see Notes).
    max_steps : int
        Action-selection attempts before giving up and reporting failure.
        Each "step" is one candidate action drawn and attempted — it may
        fail its precondition and be wasted (this is expected and is part
        of what makes the flat baseline less efficient than the HTN).
    config_overrides : dict, optional
        Currently unused hook for future experiments (e.g. overriding
        max_steps or targets per-run without touching config.yaml).

    Returns
    -------
    dict with keys:
        success            bool  — whether is_web_complete(state) was reached
        steps_taken        int   — total action-selection attempts used
        successful_actions int   — how many of those attempts actually succeeded
        energy_expended    float — cm, from state.energy_expended
        decomposition_depth int  — always 0 (no task hierarchy; reported for
                                    direct comparison with Group A's metric)
        seed_used          int or None
        final_state        gtpyhop.State — for inspection/debugging

    Notes
    -----
    Two independent RNGs are used deliberately: `state.rng` (seeded via
    create_initial_state) drives environmental stochasticity (wind noise,
    anchor availability) so it stays comparable to Group A given the same
    seed. A second RNG, seeded deterministically from the same `seed`
    argument, drives the walker's own random action choices — this is a
    property of the *agent*, not the *environment*, so keeping it separate
    means enabling/disabling environmental stochasticity does not change
    the walker's decision sequence.
    """
    state = create_initial_state(name="baseline_state", seed=seed)
    walker_rng = random.Random(seed)

    steps_taken = 0
    successful_actions = 0

    while steps_taken < max_steps and not is_web_complete(state):
        candidates = enumerate_candidate_actions(state, walker_rng)
        if not candidates:
            break  # no plausible action at all — stuck

        op_func, args = walker_rng.choice(candidates)
        steps_taken += 1

        result = op_func(state, *args)
        if result is not False:
            successful_actions += 1
            state = result

    return {
        "success": is_web_complete(state),
        "steps_taken": steps_taken,
        "successful_actions": successful_actions,
        "energy_expended": state.energy_expended,
        "decomposition_depth": 0,
        "seed_used": state.seed_used,
        "final_state": state,
    }


# ---------------------------------------------------------------------------
# CLI-style summary printer (mirrors main.py's run_planner output format)
# ---------------------------------------------------------------------------

def run_baseline_cli(seed=None, max_steps=2000, verbose=True):
    """Run once and print a human-readable summary, returning the result dict."""
    result = run_baseline(seed=seed, max_steps=max_steps)

    if verbose:
        print("=" * 70)
        print("  Group B — Flat-State Random Walker (no task hierarchy)")
        print("=" * 70)
        print()
        print(f"  Seed used:            {result['seed_used']}")
        print(f"  Success:              {result['success']}")
        print(f"  Steps attempted:      {result['steps_taken']}")
        print(f"  Successful actions:   {result['successful_actions']}")
        print(f"  Energy expended:      {result['energy_expended']:.1f} cm")
        print(f"  Decomposition depth:  {result['decomposition_depth']}")
        print()

    return result


if __name__ == "__main__":
    run_baseline_cli()