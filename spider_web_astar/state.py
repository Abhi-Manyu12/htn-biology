"""
state.py — State representation for the A* planner.

Mirrors spider_web_htn.state but adds hashing for the A* closed set. The state
is copied on every successor so A* can explore branches independently.
"""

from spider_web_htn.state import create_initial_state, rigid  # noqa: F401
from spider_web_htn.utils import NODE_COORDS  # noqa: F401


def state_key(state):
    """
    Hashable key for WebState.

    The environment is fixed during an experiment, so the key contains the
    spider location, complete thread network (including thread type), and all
    progress flags/counters that can affect future successors.
    """
    return (
        state.spider_pos,
        frozenset(state.threads),
        frozenset(state.nodes),  # important if a future experiment changes nodes
        state.proto_hub_exists,
        state.proto_hub_pos,
        state.proto_radii_count,
        state.radii_count,
        state.frame_count,
        state.top_frame_done,
        state.hub_spiral_done,
        state.auxiliary_spiral_done,
        state.capture_spiral_done,
        state.web_complete,
        state.bridge_established,
        state.high_thread_established,
    )


_copy_counter = [0]


def copy_state(state):
    """Deep-copy a WebState without sharing mutable containers."""
    _copy_counter[0] += 1
    s = type(state)("web_state_copy_" + str(_copy_counter[0]))
    s.spider_pos = state.spider_pos
    s.nodes = set(state.nodes)
    s.threads = list(state.threads)
    s.proto_hub_exists = state.proto_hub_exists
    s.proto_hub_pos = state.proto_hub_pos
    s.proto_radii_count = state.proto_radii_count
    s.radii_count = state.radii_count
    s.frame_count = state.frame_count
    s.top_frame_done = state.top_frame_done
    s.hub_spiral_done = state.hub_spiral_done
    s.auxiliary_spiral_done = state.auxiliary_spiral_done
    s.capture_spiral_done = state.capture_spiral_done
    s.web_complete = state.web_complete
    s.bridge_established = state.bridge_established
    s.high_thread_established = state.high_thread_established
    s.energy_expended = state.energy_expended
    return s


# Experimental goal thresholds. Keep these identical for HTN and A*.
GOAL_THRESHOLDS = {
    "min_proto_radii": 3,
    "min_frame": 2,
    "min_radii": 4,
    "min_capture_spiral": 4,
}
