"""E1 actor and interventions; literature-inspired, not biological replication.

Shares the recovery-v1 domain and physical executor without changing its actor.
See docs/research/E1_PROTOCOL.md for the fixed experiment protocol.
"""
from dataclasses import asdict
import hashlib
import json
import math
import random
import time

from spider_web_mulder.experiment import execute
from spider_web_mulder.model import Settings, Shear, Segment
from .backends import Backend
from .domain import (Config, World, achieved, edge, links, observe_anchor_loss,
                     resource_lower_bound, route, valid_capture, valid_radius)
from .experiment import OPS, observation

VERSION = 1
CONTROLLERS = ("history", "state_rules", "fresh_htn", "retained_htn")
SCENARIOS = ("intact", "damage_single", "damage_multi", "transfer_partial",
             "damage_unavailable", "damage_resource")
TRANSFER_HANDLING_S = 5.0
RESOURCE_DEFICIT_CM = 1.0
RESOURCE_TOLERANCE = 1e-9
REJECTION_DELAY_S = 0.1


def state_digest(state):
    return hashlib.sha256(json.dumps(observation(state), sort_keys=True).encode()).hexdigest()


def structural_silk(state):
    """Abstract deposited amount, distinct from the actor's remaining stock."""
    return sum(math.dist(state.coords["hub"], state.coords[a])
               for a in state.radii.values()) + 5 * len(state.captures)


def intervene(state, scenario, seed):
    """Apply one checkpoint intervention. Does not rewind actor history/costs."""
    if scenario not in SCENARIOS:
        raise ValueError(scenario)
    half = state.config.sectors // 2
    sector = random.Random(seed).randrange(half)
    before = observation(state)
    old_radii, old_captures = set(state.radii), set(state.captures)
    event = dict(scenario=scenario, sector=sector, before=before,
                 displaced_web_silk_cm=0., donor_web_silk_cm=0.,
                 handling_s=0., external_displacement_cm=0.)
    if scenario == "transfer_partial":
        if state.position != "hub":
            raise ValueError("Aligned transfer requires the actor at the hub")
        event["displaced_web_silk_cm"] = structural_silk(state)
        state.radii = {i: f"B{i}" for i in range(state.config.sectors) if i != sector}
        state.captures = {
            i: (state.radii[i], state.radii[(i-1) % state.config.sectors])
            for i in range(half)
            if valid_radius(state, i) and valid_radius(state, (i-1) % state.config.sectors)
        }
        state.restore_captures = old_captures - set(state.captures)
        event["donor_web_silk_cm"] = structural_silk(state)
        state.clock_s += TRANSFER_HANDLING_S
        event["handling_s"] = TRANSFER_HANDLING_S
    elif scenario != "intact":
        targets = [sector]
        if scenario == "damage_multi":
            targets.append((sector+1) % state.config.sectors)
        for i in targets:
            observe_anchor_loss(state, f"A{i}")
        if scenario == "damage_unavailable":
            observe_anchor_loss(state, f"B{sector}")
        if scenario == "damage_resource":
            remaining = max(0., resource_lower_bound(state)-RESOURCE_DEFICIT_CM)
            remaining = min(state.silk_remaining, remaining)
            state.silk_lost += state.silk_remaining-remaining
            state.silk_remaining = remaining
    event.update(after=observation(state),
                 invalidated_radii=sorted(old_radii-set(state.radii)),
                 invalidated_captures=sorted(old_captures-set(state.captures)))
    return event


class E1Backend(Backend):
    """Same planner/adapter, with optional diagnostic tree recording."""
    def __init__(self, name, record_trees=False):
        self.record_trees = record_trees
        super().__init__(name)

    def snapshot(self, label, failed_node=None):
        if self.record_trees:
            super().snapshot(label, failed_node)


class StateRules:
    """Observed-state finite-state controller, no HTN decomposition or search.

    Shares domain predicates, primary/backup choices and shortest-path routing.
    Return-to-hub is explicit to match the authored HTN construction convention.
    """
    def __init__(self):
        self.returning_sector = None

    @staticmethod
    def travel(state, destination, owner):
        path = route(state, destination)
        if path and len(path) > 1:
            return ("move", path[0], path[1], owner)
        return None

    def select(self, state):
        if state.silk_remaining+RESOURCE_TOLERANCE < resource_lower_bound(state):
            return None
        if self.returning_sector is not None:
            if state.position != "hub":
                return self.travel(state, "hub", ("radius", self.returning_sector))
            self.returning_sector = None
        for i in range(state.config.sectors):
            if valid_radius(state, i):
                continue
            for prefix in ("A", "B"):
                anchor = f"{prefix}{i}"
                if not state.available[anchor] or route(state, anchor) is None:
                    continue
                if state.position != anchor:
                    return self.travel(state, anchor, ("radius", i))
                return ("attach", i, anchor, ("radius", i))
            return None
        ordered = sorted(state.restore_captures) + [
            i for i in range(state.config.sectors) if i not in state.restore_captures]
        for i in ordered:
            if valid_capture(state, i):
                continue
            if state.position != "hub":
                return self.travel(state, "hub", ("capture", i))
            return ("capture", i, state.radii[i],
                    state.radii[(i-1) % state.config.sectors], ("capture", i))
        return None

    def accepted(self, action):
        if action[0] == "attach":
            self.returning_sector = action[1]


def perform(state, action, motion, settings):
    """Validate with shared primitives; execute moves with shared tracking.

    Return observed state, acceptance, walked distance and terminal failure.
    No partially rejected symbolic effects are committed.
    """
    name = action[0]
    candidate = OPS[name](state.copy(), *action[1:])
    if candidate is None:
        state.clock_s = min(state.config.max_elapsed_s, state.clock_s+REJECTION_DELAY_S)
        return state, False, 0., None
    if name == "move":
        source, target = action[1:3]
        if edge(source, target) not in links(state):
            raise RuntimeError("Observed move is not graph-valid")
        segment = Segment(0, "e1_route", "frame", state.coords[source], state.coords[target], False)
        details = {}
        actual, stamp, walked, error, _ = execute(
            segment, motion.world(segment.end, state.clock_s), state.position_material,
            state.clock_s, motion, settings, True, details=details)
        if details.get("action_timed_out") or error > settings.attachment_tolerance_cm:
            state.clock_s, state.position_material = stamp, actual
            state.position = "in_transit"
            return state, False, walked, "movement_timeout"
        candidate.clock_s, candidate.position_material = stamp, actual
        return candidate, True, walked, None
    if candidate.clock_s > state.config.max_elapsed_s:
        state.clock_s = state.config.max_elapsed_s
        return state, False, 0., "execution_budget"
    return candidate, True, 0., None


def run_trial(config=Config(depth=0), controller="state_rules", scenario="damage_single",
              seed=0, record_trees=False):
    if controller not in CONTROLLERS or scenario not in SCENARIOS:
        raise ValueError("Unknown E1 controller or scenario")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    state = World(config)
    settings = Settings(execution_mode="tracking", speed_cm_s=config.speed_cm_s,
                        amplitude_cm=config.amplitude_cm, frequency_hz=config.frequency_hz,
                        max_elapsed_s=config.max_elapsed_s)
    phase = random.Random(seed).uniform(0, 2*math.pi)
    motion = Shear(settings, phase)
    rules = StateRules() if controller == "state_rules" else None
    engine = None if rules else E1Backend(
        "ipyhop" if controller == "retained_htn" else "ipyhop_fresh", record_trees)
    policy_wall = 0.
    decisions = 0
    queue = []
    if engine:
        started = time.perf_counter()
        queue = engine.plan(state)
        policy_wall += time.perf_counter()-started
        decisions += 1
    trace = []
    event = None
    attempts = replans = stale = repeated = restorations = 0
    travel = 0.
    seen_effects = set()
    event_policy_wall = None
    failure = None
    refresh = False
    while not achieved(state):
        if state.clock_s >= config.max_elapsed_s or attempts >= config.max_attempts:
            failure = "execution_budget"
            break
        if refresh:
            if replans >= config.max_repairs:
                failure = "repair_budget"
                break
            if not queue:
                failure = "unsatisfied_goal"
                break
            failed_node = queue[0][0]
            started = time.perf_counter()
            queue = engine.plan(state, failed_node=failed_node if controller == "retained_htn" else None)
            policy_wall += time.perf_counter()-started
            decisions += 1
            replans += 1
            trace.append(dict(event="replan", controller=controller,
                              failed_node=failed_node if controller == "retained_htn" else None,
                              observed=observation(state), returned_actions=None if queue is None else len(queue)))
            refresh = False
        if rules:
            started = time.perf_counter()
            action = rules.select(state)
            policy_wall += time.perf_counter()-started
            decisions += 1
            node = None
        else:
            node, action = queue[0] if queue else (None, None)
        if action is None:
            failure = "unsatisfied_goal" if queue == [] and engine else "planning_infeasible"
            break
        name = action[0]
        effect = (name, action[1]) if name in ("attach", "capture") else None
        valid = (valid_radius(state, action[1]) if name == "attach" else
                 valid_capture(state, action[1]) if name == "capture" else False)
        restoration = effect in seen_effects and not valid
        before = observation(state)
        state, accepted, walked, terminal = perform(state, action, motion, settings)
        travel += walked
        attempts += 1
        trace.append(dict(event="action", action=action, node_id=node, accepted=accepted,
                          before=before, after=observation(state), travel_cm=walked,
                          redundant=bool(effect and valid and accepted),
                          restoration=bool(restoration and accepted)))
        if accepted:
            repeated += int(bool(effect and valid))
            restorations += int(restoration)
            if effect:
                seen_effects.add(effect)
            if rules:
                rules.accepted(action)
            else:
                queue.pop(0)
        else:
            if terminal:
                failure = terminal
                break
            stale += 1
            if controller in ("history", "state_rules"):
                failure = "stale_precondition"
                break
            refresh = True
        if event is None and accepted and name == "capture" and len(state.captures) == config.sectors//2:
            pre_hash = state_digest(state)
            event = intervene(state, scenario, seed)
            event.update(event="intervention", pre_state_sha256=pre_hash,
                         post_state_sha256=state_digest(state), action_attempt=attempts)
            trace.append(event)
            event_policy_wall = policy_wall
            refresh = scenario != "intact" and controller in ("fresh_htn", "retained_htn")
    success = achieved(state) and failure is None and state.clock_s <= config.max_elapsed_s
    if not success and failure is None:
        failure = "execution_budget"
    conservation = abs(state.silk_used+state.silk_remaining+state.silk_lost-config.silk_cm)
    if conservation > RESOURCE_TOLERANCE:
        raise RuntimeError("Actor stock conservation failed")
    row = dict(e1_version=VERSION, config=asdict(config), controller=controller,
               scenario=scenario, seed=seed, forcing_phase=phase, success=success,
               failure_reason=failure, event_fired=event is not None,
               pre_state_sha256=event["pre_state_sha256"] if event else None,
               post_state_sha256=event["post_state_sha256"] if event else None,
               attempts=attempts, replans=replans, stale_preconditions=stale,
               unnecessary_repeats=repeated, restorations=restorations,
               elapsed_s=state.clock_s, travel_cm=travel, silk_used_cm=state.silk_used,
               silk_remaining_cm=state.silk_remaining, silk_lost_cm=state.silk_lost,
               donor_web_silk_cm=event["donor_web_silk_cm"] if event else 0.,
               displaced_web_silk_cm=event["displaced_web_silk_cm"] if event else 0.,
               decision_calls=decisions, policy_wall_s=policy_wall,
               recovery_policy_wall_s=None if event_policy_wall is None else policy_wall-event_policy_wall,
               method_calls=engine.method_calls if engine else None,
               planning_calls=engine.planning_calls if engine else 0,
               valid_radii=sum(valid_radius(state, i) for i in range(config.sectors)),
               valid_captures=sum(valid_capture(state, i) for i in range(config.sectors)),
               final_state=observation(state))
    return row, trace, engine.tree_snapshots if engine else []
