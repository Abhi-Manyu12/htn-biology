"""
conftest.py — shared pytest fixtures for the spider_web_htn test suite.
"""

import os
import sys

# Make the spider_web_htn package (living one level up from tests/) importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from spider_web_htn_updated.state import create_initial_state
from spider_web_htn_updated.config_loader import CONFIG


@pytest.fixture
def fresh_state():
    """A brand-new initial state: spider at start position, no threads, no hub."""
    return create_initial_state()


@pytest.fixture
def state_at_hub_with_radii():
    """
    A state positioned as if the spider has already built (min_proto_radii - 1)
    proto-radii and is standing at the hub — one insert_radius / mark_proto_hub
    call away from completing the proto-hub stage.
    """
    state = create_initial_state()
    hub = CONFIG["domain"]["default_hub_name"]
    state.nodes.add(hub)
    state.spider_pos = hub
    state.proto_radii_count = CONFIG["domain"]["min_proto_radii"] - 1
    return state


@pytest.fixture
def min_proto_radii():
    return CONFIG["domain"]["min_proto_radii"]
