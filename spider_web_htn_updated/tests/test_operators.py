"""
test_operators.py — Verifies that each primitive operator enforces its
preconditions and refuses illegal state transitions (returns False rather
than mutating state), per the roadmap's "unit testing" requirement:

    "Implement a test suite ... to verify that the agent never attempts an
    illegal state transition (e.g., laying a spiral before the bridge)."
"""

from spider_web_htn_updated import operators as ops
from spider_web_htn_updated.config_loader import CONFIG

HUB = CONFIG["domain"]["default_hub_name"]


# ---------------------------------------------------------------------------
# walk()
# ---------------------------------------------------------------------------

def test_walk_fails_if_spider_not_at_start(fresh_state):
    # Spider starts at right_stick_top, not left_stick_top
    result = ops.walk(fresh_state, "left_stick_top", "left_stick_mid")
    assert result is False


def test_walk_fails_to_unreachable_node(fresh_state):
    # proto_hub doesn't exist as a node yet (only created via `anchor`),
    # so it should not be reachable — this is exactly the "illegal
    # transition" case: walking to a node that doesn't exist in the graph.
    result = ops.walk(fresh_state, fresh_state.spider_pos, HUB)
    assert result is False


def test_walk_succeeds_along_structural_edge(fresh_state):
    start = fresh_state.spider_pos  # right_stick_top
    result = ops.walk(fresh_state, start, "right_stick_mid")
    assert result is not False
    assert result.spider_pos == "right_stick_mid"
    assert result.energy_expended > 0


# ---------------------------------------------------------------------------
# lay_thread()
# ---------------------------------------------------------------------------

def test_lay_thread_fails_if_spider_not_at_n1(fresh_state):
    result = ops.lay_thread(fresh_state, "left_stick_top", "right_stick_top", "bridge")
    assert result is False


def test_lay_thread_succeeds_from_current_position(fresh_state):
    start = fresh_state.spider_pos
    result = ops.lay_thread(fresh_state, start, "right_stick_bottom", "bridge")
    assert result is not False
    assert (start, "right_stick_bottom", "bridge") in result.threads
    assert result.spider_pos == "right_stick_bottom"


# ---------------------------------------------------------------------------
# attach_dragline()
# ---------------------------------------------------------------------------

def test_attach_dragline_fails_if_not_at_node(fresh_state):
    result = ops.attach_dragline(fresh_state, "left_stick_top")
    assert result is False


def test_attach_dragline_succeeds_at_current_position(fresh_state):
    result = ops.attach_dragline(fresh_state, fresh_state.spider_pos)
    assert result is not False


# ---------------------------------------------------------------------------
# remove_thread()
# ---------------------------------------------------------------------------

def test_remove_thread_fails_if_thread_does_not_exist(fresh_state):
    result = ops.remove_thread(fresh_state, "left_stick_top", "right_stick_top")
    assert result is False


def test_remove_thread_succeeds_if_thread_exists(fresh_state):
    fresh_state.threads.append(("left_stick_top", "right_stick_top", "bridge"))
    result = ops.remove_thread(fresh_state, "left_stick_top", "right_stick_top")
    assert result is not False
    assert ("left_stick_top", "right_stick_top", "bridge") not in result.threads


# ---------------------------------------------------------------------------
# drop_down() / swing_tarzan()
# ---------------------------------------------------------------------------

def test_drop_down_fails_if_spider_not_at_from_node(fresh_state):
    result = ops.drop_down(fresh_state, HUB, "anchor_bottom_left")
    assert result is False


def test_swing_tarzan_fails_if_spider_not_at_from_node(fresh_state):
    result = ops.swing_tarzan(fresh_state, HUB, "anchor_left_upper")
    assert result is False


# ---------------------------------------------------------------------------
# reel_up() — requires an existing (provisional) thread
# ---------------------------------------------------------------------------

def test_reel_up_fails_without_existing_thread(state_at_hub_with_radii):
    state = state_at_hub_with_radii
    result = ops.reel_up(state, HUB, "anchor_left_upper")
    assert result is False


def test_reel_up_succeeds_with_existing_thread(state_at_hub_with_radii):
    state = state_at_hub_with_radii
    state.threads.append((HUB, "anchor_left_upper", "dragline"))
    result = ops.reel_up(state, HUB, "anchor_left_upper")
    assert result is not False
    assert result.spider_pos == "anchor_left_upper"


# ---------------------------------------------------------------------------
# insert_radius() — requires spider at hub
# ---------------------------------------------------------------------------

def test_insert_radius_fails_if_spider_not_at_hub(fresh_state):
    result = ops.insert_radius(fresh_state, "anchor_left_upper", HUB)
    assert result is False


# ---------------------------------------------------------------------------
# mark_proto_hub() — the key "illegal transition" example from the roadmap:
# a proto-hub (and therefore everything built on top of it, including
# spirals) must not be establishable before enough proto-radii converge.
# ---------------------------------------------------------------------------

def test_mark_proto_hub_fails_with_insufficient_radii(state_at_hub_with_radii):
    # Fixture sets proto_radii_count = min_proto_radii - 1 → still short.
    result = ops.mark_proto_hub(state_at_hub_with_radii, HUB)
    assert result is False


def test_mark_proto_hub_succeeds_at_threshold(state_at_hub_with_radii, min_proto_radii):
    state = state_at_hub_with_radii
    state.proto_radii_count = min_proto_radii  # now meets the threshold
    result = ops.mark_proto_hub(state, HUB)
    assert result is not False
    assert result.proto_hub_exists is True
    assert result.proto_hub_pos == HUB


# ---------------------------------------------------------------------------
# build_spiral_segment() — "laying a spiral before the bridge" style checks.
# The operator itself only checks spider position, so we verify that a
# spiral segment cannot be laid from a hub node that was never actually
# established (never added to state.nodes / never visited).
# ---------------------------------------------------------------------------

def test_build_spiral_segment_fails_if_spider_not_at_n1(fresh_state):
    # Spider is at right_stick_top, not at the (nonexistent) hub.
    result = ops.build_spiral_segment(fresh_state, HUB, "anchor_top_center", "capture_spiral")
    assert result is False


def test_lay_frame_thread_fails_if_spider_not_at_n1(fresh_state):
    result = ops.lay_frame_thread(fresh_state, "left_stick_top", "right_stick_top")
    assert result is False


def test_lay_radius_fails_if_spider_not_at_hub(fresh_state):
    result = ops.lay_radius(fresh_state, HUB, "anchor_top_center")
    assert result is False


def test_mark_web_complete_sets_flag(fresh_state):
    result = ops.mark_web_complete(fresh_state)
    assert result.web_complete is True
