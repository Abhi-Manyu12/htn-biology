"""Acting with physical routes, observed effects and explicit failure context."""
from dataclasses import asdict
import math
import random

from spider_web_mulder.experiment import execute
from spider_web_mulder.model import Settings,Shear,Segment

from .backends import Backend
from .domain import ACTIONS,Config,World,achieved,edge,links,observe_anchor_loss,valid_radius,valid_capture


BACKENDS = ("fresh_root","component","ipyhop_fresh","ipyhop")
SCENARIOS = ("clean","transient_attachment","permanent_anchor","route_block","unreachable","silk_depletion","prefix_damage")
OPS = {fn.__name__:fn for fn in ACTIONS}


def observation(state):
    return dict(position=state.position,position_material=state.position_material,
                clock_s=state.clock_s,silk_remaining=state.silk_remaining,silk_used=state.silk_used,
                silk_lost=state.silk_lost,
                radii=dict(state.radii),captures=dict(state.captures),
                unavailable=sorted(a for a,available in state.available.items() if not available),
                blocked=sorted(state.blocked),restore_captures=sorted(state.restore_captures))


class Failure:
    """One explicit logical-action trigger shared by all backends in a case."""
    def __init__(self,scenario,seed,config):
        if scenario not in SCENARIOS:
            raise ValueError(scenario)
        self.scenario = scenario
        self.sector = random.Random(seed).randrange(config.sectors)
        self.route_junction = "left" if seed%2 else "right"
        self.fired = False

    def apply(self,state,action):
        if self.fired or self.scenario=="clean":
            return None
        name = action[0]
        attach_trigger = name=="attach" and action[1]==self.sector and action[2]==f"A{self.sector}"
        route_trigger = name=="move" and action[1:3]==("hub",self.route_junction)
        damage_trigger = name=="capture" and action[1]==1 and valid_capture(state,0)
        if ((self.scenario in ("transient_attachment","permanent_anchor","silk_depletion") and attach_trigger) or
            (self.scenario in ("route_block","unreachable") and route_trigger) or
            (self.scenario=="prefix_damage" and damage_trigger)):
            self.fired = True
            invalidated = []
            if self.scenario=="permanent_anchor":
                invalidated = observe_anchor_loss(state,action[2])
            elif self.scenario=="route_block":
                state.blocked.add(edge("hub",self.route_junction))
            elif self.scenario=="unreachable":
                state.blocked.update(e for e in links(state) if state.position in e)
            elif self.scenario=="silk_depletion":
                old = state.silk_remaining
                state.silk_remaining = max(0.,math.dist(state.coords["hub"],state.coords[action[2]])-1.)
                state.silk_lost += old-state.silk_remaining
            elif self.scenario=="prefix_damage":
                invalidated = observe_anchor_loss(state,state.radii[0])
            # Failed physical attachment/capture attempts consume a small silk
            # amount. Obstacle detection consumes time but no deposited thread.
            partial = min(0.2,state.silk_remaining) if name in ("attach","capture") else 0.
            state.silk_remaining -= partial
            state.silk_used += partial
            state.clock_s += 0.5 if partial else 0.1
            return dict(kind=self.scenario,transient=self.scenario=="transient_attachment",
                        silk_consumed_cm=partial,invalidated_captures=invalidated)
        return None


def run_trial(config=Config(),backend="ipyhop",scenario="permanent_anchor",seed=0):
    state = World(config)
    engine = Backend(backend)
    motion_settings = Settings(execution_mode="tracking",speed_cm_s=config.speed_cm_s,
                               amplitude_cm=config.amplitude_cm,frequency_hz=config.frequency_hz,
                               max_elapsed_s=config.max_elapsed_s)
    motion = Shear(motion_settings,random.Random(seed).uniform(0,2*math.pi))
    fault = Failure(scenario,seed,config)
    trace = []
    queue = engine.plan(state)
    repairs = 0
    attempts = 0
    transient_attempts = {}
    traveled = 0.
    stale = 0
    repeated = 0
    restored = 0
    retraced = 0.
    previous_edges = set()
    recovering_owner = None
    failure_reason = None
    while queue:
        if attempts >= config.max_attempts or state.clock_s >= config.max_elapsed_s:
            failure_reason = "execution_budget"
            break
        node_id,action = queue[0]
        owner = action[-1]
        if recovering_owner is not None and owner!=recovering_owner:
            recovering_owner = None
        before = observation(state)
        injected = fault.apply(state,action)
        if state.clock_s > config.max_elapsed_s:
            state.clock_s = config.max_elapsed_s
            failure_reason = "execution_budget"
        name = action[0]
        redundant = ((name=="attach" and valid_radius(state,action[1]) and state.radii[action[1]]==action[2]) or
                     (name=="capture" and valid_capture(state,action[1])))
        was_invalid_capture = name=="capture" and action[1] in state.restore_captures
        candidate = None if injected else OPS[name](state.copy(),*action[1:])
        reason = None
        walked = 0.
        if candidate is None:
            reason = injected["kind"] if injected else "stale_precondition"
            if not injected:
                stale += 1
                state.clock_s += 0.1
        elif name=="move":
            source,target = action[1:3]
            if edge(source,target) not in links(state):
                raise RuntimeError("Move bypassed observed route preconditions")
            segment = Segment(0,"recovery_route","frame",state.coords[source],state.coords[target],False)
            details = {}
            actual,stamp,walked,error,_ = execute(segment,motion.world(segment.end,state.clock_s),
                                                 state.position_material,state.clock_s,motion,motion_settings,True,details=details)
            state.clock_s = stamp
            state.position_material = actual
            traveled += walked
            if details.get("action_timed_out") or error > motion_settings.attachment_tolerance_cm:
                state.position = "in_transit"
                failure_reason = "movement_timeout"
                reason = failure_reason
            else:
                candidate.clock_s = stamp
                candidate.position_material = actual
                state = candidate
                if recovering_owner==owner and edge(source,target) in previous_edges:
                    retraced += walked
                previous_edges.add(edge(source,target))
        elif candidate.clock_s > config.max_elapsed_s:
            state.clock_s = config.max_elapsed_s
            failure_reason = "execution_budget"
            reason = failure_reason
        else:
            state = candidate
        attempts += 1
        accepted = reason is None
        trace.append(dict(event="action",attempt=attempts,generation=engine.planning_calls,node_id=node_id,
                          action=action,owner=owner,accepted=accepted,reason=reason,
                          injected=injected,before=before,after=observation(state),travel_cm=walked,
                          redundant=bool(redundant),legitimate_restoration=bool(was_invalid_capture and accepted)))
        if accepted:
            repeated += int(redundant)
            restored += int(was_invalid_capture)
            queue.pop(0)
            continue
        if failure_reason:
            break
        if injected and injected["transient"]:
            transient_attempts[action] = transient_attempts.get(action,0)+1
            if transient_attempts[action] <= config.transient_retries:
                trace.append(dict(event="retry",action=action,node_id=node_id,time_s=state.clock_s,
                                  reason="transient_not_blacklisted"))
                continue
        if repairs >= config.max_repairs:
            failure_reason = "repair_budget"
            break
        old_queue = list(queue)
        old_nodes = set(engine.planner.sol_tree.nodes) if engine.planner is not None else set()
        if backend=="component":
            replacement = engine.plan(state,owner=owner)
            suffix = [entry for entry in queue if entry[1][-1]!=owner]
            queue = replacement+suffix if replacement is not None else None
        elif backend=="ipyhop":
            queue = engine.plan(state,failed_node=node_id)
        else:
            queue = engine.plan(state)
        repairs += 1
        recovering_owner = owner
        new_nodes = set(engine.planner.sol_tree.nodes) if engine.planner is not None else set()
        trace.append(dict(event="replan",generation=engine.planning_calls,backend=backend,failed_node=node_id,
                          owner=owner,observed_state=observation(state),old_remaining_actions=len(old_queue),
                          new_remaining_actions=len(queue) if queue is not None else None,
                          retained_node_ids=sorted(old_nodes&new_nodes) if backend=="ipyhop" else [],
                          reason=reason))
        if queue is None:
            failure_reason = "planning_infeasible"
            break
    success = achieved(state) and failure_reason is None
    if not success and failure_reason is None:
        failure_reason = "planning_infeasible" if queue is None else "unsatisfied_goal"
    result = dict(backend=backend,scenario=scenario,seed=seed,config=asdict(config),success=success,
                  failure_reason=failure_reason,event_fired=fault.fired,attempts=attempts,repairs=repairs,
                  planning_calls=engine.planning_calls,method_calls=engine.method_calls,
                  ipyhop_iterations=engine.iterations if engine.planner is not None else None,
                  planning_wall_s=engine.planning_wall_s,elapsed_s=state.clock_s,travel_cm=traveled,
                  silk_used_cm=state.silk_used,silk_remaining_cm=state.silk_remaining,
                  silk_lost_cm=state.silk_lost,
                  stale_preconditions=stale,unnecessary_repeats=repeated,legitimate_restorations=restored,
                  recovery_retraced_cm=retraced,valid_radii=sum(valid_radius(state,i) for i in range(config.sectors)),
                  valid_captures=sum(valid_capture(state,i) for i in range(config.sectors)),final_state=observation(state))
    return result,trace,engine.tree_snapshots
