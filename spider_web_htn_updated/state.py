"""
state.py — State representation for the Zschokke 1996 orb web construction model.

The state tracks the spider's position, the thread network (as a graph),
construction progress flags, and cumulative energy expenditure.

Rigid relations (the fixed supporting-structure topology) and the spider's
starting position are now sourced from config.yaml, so a different
environment (e.g. a wider frame, extra crossbars) only requires editing the
config — no changes here.
"""

import gtpyhop

from .config_loader import CONFIG
from .stochastic import make_rng, select_available_anchors

# ---------------------------------------------------------------------------
# Rigid relations — environmental constants that do not change during planning
# ---------------------------------------------------------------------------

rigid = gtpyhop.State("rigid")

# The nodes that form the supporting structure (always available), from config.
rigid.structure_nodes = set(CONFIG["environment"]["structure_nodes"])

# Physical connections along the supporting structure (spider can walk these
# without needing a silk thread), from config.
rigid.walkable_edges = list(CONFIG["environment"]["walkable_edges"])


def _is_walkable(n1, n2):
    """Check if (n1, n2) is a walkable structural edge."""
    for a, b in rigid.walkable_edges:
        if (a == n1 and b == n2) or (a == n2 and b == n1):
            return True
    return False


# ---------------------------------------------------------------------------
# Initial state factory
# ---------------------------------------------------------------------------

def create_initial_state(name="web_state_0", seed=None):
    """
    Create a fresh initial state matching the configured lab setup.

    The spider starts at ``environment.spider_start_pos`` (config.yaml). The
    only known nodes are the supporting-structure nodes; web-nodes are added
    dynamically during construction. No threads exist yet.

    Parameters
    ----------
    name : str
        Name for the resulting gtpyhop.State.
    seed : int, optional
        RNG seed for this run (see stochastic.py). Precedence: this argument
        > config.stochastic.seed > OS entropy. Irrelevant when
        config.stochastic.enabled is false (the default) — the state is then
        fully deterministic regardless of seed.

    Returns
    -------
    gtpyhop.State
    """
    s = gtpyhop.State(name)

    # Seeded RNG for this run — every stochastic draw (wind noise, anchor
    # availability, and any future perturbation) comes from this single
    # generator so the whole run is reproducible from one seed.
    s.rng = make_rng(seed)
    # Record which seed produced this run, for logging/reproducibility.
    s.seed_used = seed if seed is not None else CONFIG.get("stochastic", {}).get("seed")

    # Spider position (from config)
    s.spider_pos = CONFIG["environment"]["spider_start_pos"]

    # Known nodes (starts with just the structure; web-nodes are added during
    # construction). Some anchor points may be unavailable this run if
    # stochastic.anchor_availability is enabled in config.
    s.nodes = select_available_anchors(rigid.structure_nodes, s.rng)

    # Thread network: list of (node1, node2, thread_type)
    # thread_type ∈ {"bridge", "dragline", "proto_radius", "radius",
    #                "frame", "auxiliary_spiral", "capture_spiral"}
    s.threads = []

    # Proto-hub state
    s.proto_hub_exists = False
    s.proto_hub_pos = None
    s.proto_radii_count = 0

    # Later-stage progress
    s.radii_count = 0
    s.frame_count = 0
    s.top_frame_done = False
    s.hub_spiral_done = False
    s.auxiliary_spiral_done = False
    s.capture_spiral_done = False

    # Overall completion
    s.web_complete = False

    # Bridging
    s.bridge_established = False
    s.high_thread_established = False

    # Energy tracking (Zschokke's distance-as-cost metric, in cm)
    s.energy_expended = 0.0

    return s
