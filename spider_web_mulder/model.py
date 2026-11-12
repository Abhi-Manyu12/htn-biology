"""Geometry, a resumable GTPyhop domain, and explicit benchmark assumptions.

The shear is an affine kinematic approximation, not a silk mechanics solver.
Construction starts with an established hub and accessible radial supports.
"""

from dataclasses import dataclass, fields
from pathlib import Path
import math

import gtpyhop
import yaml


class _Immutable:
    def __deepcopy__(self, memo):
        # These records contain only numbers, strings, immutable records and
        # coordinate tuples. Share them across GTPyhop search-state copies.
        return self


class _Segments(tuple):
    def __deepcopy__(self, memo):
        return self


@dataclass(frozen=True)
class Settings(_Immutable):
    execution_mode: str = "endpoint"
    method_policy: str = "direct"
    width_cm: float = 30.0
    height_cm: float = 30.0
    amplitude_cm: float = 10.0
    frequency_hz: float = 0.05
    radial_count: int = 16
    auxiliary_turns: int = 3
    capture_turns: int = 8
    inner_radius_fraction: float = 0.15
    outer_radius_fraction: float = 0.85
    speed_cm_s: float = 1.0
    attachment_time_s: float = 0.5
    integration_step_s: float = 0.25
    attachment_tolerance_cm: float = 0.5
    correction_limit_cm: float = 4.0
    correction_speed_cm_s: float = 2.0
    repair_delay_s: float = 0.2
    max_repairs_per_action: int = 3
    max_elapsed_s: float = 20000.0
    event_threshold_cm: float = 2.0
    filter_tau_s: float = 10.0
    prediction_samples: int = 17
    prediction_horizon_s: float = 20.0
    sensor_tau_s: float = 0.0
    max_action_time_s: float = 120.0
    max_method_wait_s: float = 5.0
    web_width_fraction: float = 1.0
    web_height_fraction: float = 1.0

    def __post_init__(self):
        for f in fields(self):
            if f.name in ("execution_mode", "method_policy"):
                continue
            value = getattr(self, f.name)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                raise ValueError(f"{f.name} must be a finite number")
        for name in ("width_cm", "height_cm", "speed_cm_s", "integration_step_s",
                     "correction_speed_cm_s", "filter_tau_s", "max_elapsed_s",
                     "prediction_horizon_s"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        for name in ("amplitude_cm", "frequency_hz", "attachment_time_s",
                     "attachment_tolerance_cm", "correction_limit_cm", "repair_delay_s",
                     "event_threshold_cm", "sensor_tau_s", "max_method_wait_s"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be nonnegative")
        if self.max_action_time_s <= self.attachment_time_s:
            raise ValueError("max_action_time_s must exceed attachment_time_s")
        if self.execution_mode not in ("endpoint", "tracking"):
            raise ValueError("execution_mode must be endpoint or tracking")
        if self.method_policy not in ("direct", "phase_wait"):
            raise ValueError("method_policy must be direct or phase_wait")
        if self.method_policy == "phase_wait" and self.execution_mode != "tracking":
            raise ValueError("phase_wait requires tracking execution")
        if not (0 < self.web_width_fraction <= 1 and 0 < self.web_height_fraction <= 1):
            raise ValueError("Web width and height fractions must be in (0, 1]")
        for name, minimum in (("radial_count", 4), ("auxiliary_turns", 1),
                              ("capture_turns", 1), ("prediction_samples", 2),
                              ("max_repairs_per_action", 0)):
            value = getattr(self, name)
            if not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if not 0 < self.inner_radius_fraction < self.outer_radius_fraction < 1:
            raise ValueError("Require 0 < inner_radius_fraction < outer_radius_fraction < 1")


def load_settings(path=None):
    path = Path(path) if path else Path(__file__).with_name("config.yaml")
    with path.open() as stream:
        raw = yaml.safe_load(stream)
    if not isinstance(raw, dict):
        raise ValueError("Config must be a mapping")
    values = {}
    allowed = {f.name for f in fields(Settings)}
    for section in ("environment", "construction", "execution", "control"):
        group = raw.get(section, {})
        if not isinstance(group, dict):
            raise ValueError(f"{section} must be a mapping")
        unknown = set(group) - allowed
        if unknown:
            raise ValueError(f"Unknown settings: {sorted(unknown)}")
        if set(group) & set(values):
            raise ValueError("Duplicate settings across sections")
        values.update(group)
    return Settings(**values), raw.get("experiment", {})


@dataclass(frozen=True)
class Shear(_Immutable):
    settings: Settings
    phase: float = 0.0

    def displacement(self, time):
        s = self.settings
        return s.amplitude_cm * math.sin(2 * math.pi * s.frequency_hz * time + self.phase)

    def changed_between(self, start, end):
        """Detect motion even when an interval ends at the same displacement."""
        if end <= start or self.settings.amplitude_cm == 0 or self.settings.frequency_hz == 0:
            return False
        omega = 2 * math.pi * self.settings.frequency_hz
        values = [self.displacement(start), self.displacement(end)]
        first = math.ceil((omega * start + self.phase - math.pi / 2) / math.pi)
        last = math.floor((omega * end + self.phase - math.pi / 2) / math.pi)
        # Consecutive extrema alternate; two capture the complete range.
        for k in range(first, min(last, first + 1) + 1):
            values.append(self.displacement((math.pi / 2 + k * math.pi - self.phase) / omega))
        return max(values) - min(values) > 1e-9

    def world(self, point, time):
        x, y = point
        return (x + (1 - y / self.settings.height_cm) * self.displacement(time), y)

    def material(self, point, time):
        x, y = point
        return (x - (1 - y / self.settings.height_cm) * self.displacement(time), y)


@dataclass(frozen=True)
class Segment(_Immutable):
    index: int
    task: str
    phase: str
    start: tuple
    end: tuple
    silk: bool = True


def construction(settings):
    """Ordered compound tasks: frame edges, radii, and individual spiral turns.

    Counts and ideal waypoints are imposed. Actual attachment error and lengths
    are measured; prescribed counts must not be treated as emergent biology.
    Auxiliary threads remain as scaffolding in this first kinematic model.
    """
    s = settings
    hub = (s.width_cm / 2, s.height_cm / 2)
    segments = []
    position = hub

    def add(task, phase, end, silk=True):
        nonlocal position
        segments.append(Segment(len(segments), task, phase, position, end, silk))
        position = end

    half_width = s.width_cm*s.web_width_fraction/2
    half_height = s.height_cm*s.web_height_fraction/2
    left, right = hub[0]-half_width, hub[0]+half_width
    bottom, top = hub[1]-half_height, hub[1]+half_height
    corners = [(left, top), (right, top), (right, bottom), (left, bottom)]
    add("frame_0", "frame", corners[0], False)
    for i in range(4):
        add(f"frame_{i}", "frame", corners[(i + 1) % 4])
    add("frame_3", "frame", hub, False)

    anchors = []
    for i in range(s.radial_count):
        theta = math.pi / 2 + 2 * math.pi * i / s.radial_count
        dx, dy = math.cos(theta), math.sin(theta)
        radius = min(half_width / max(abs(dx), 1e-12), half_height / max(abs(dy), 1e-12))
        anchor = (hub[0] + radius * dx, hub[1] + radius * dy)
        anchors.append(anchor)
        add(f"radius_{i}", "radials", anchor)
        add(f"radius_{i}", "radials", hub, False)

    for phase, turns in (("auxiliary", s.auxiliary_turns), ("capture", s.capture_turns)):
        steps = turns * s.radial_count
        for j in range(steps + 1):
            u = j / steps
            if phase == "auxiliary":
                fraction = s.inner_radius_fraction * (s.outer_radius_fraction / s.inner_radius_fraction) ** u
            else:
                fraction = s.outer_radius_fraction - u * (s.outer_radius_fraction - s.inner_radius_fraction)
            anchor = anchors[j % s.radial_count]
            point = tuple(h + fraction * (a - h) for h, a in zip(hub, anchor))
            add(f"{phase}_{min(j // s.radial_count, turns - 1)}", phase, point, j > 0)
        add(f"{phase}_{turns - 1}", phase, hub, False)
    return tuple(segments)


def make_state(segments, motion):
    state = gtpyhop.State("mulder")
    state.segments = _Segments(segments)
    state.motion = motion
    state.done = set()
    state.snapshot_time = 0.0
    return state


def place_segment(state, index, target):
    """Symbolic planning action; physical execution is handled by the runner."""
    if index in state.done or any(i not in state.done for i in range(index)):
        return False
    state.done.add(index)
    if state.motion.settings.method_policy == "phase_wait":
        seg = state.segments[index]
        state.snapshot_time += component_duration([seg], state.motion, state.snapshot_time)
    return state


def component_duration(segments, motion, stamp):
    s = motion.settings
    shear = motion.displacement(stamp)/s.height_cm
    return sum(math.hypot(seg.end[0]-seg.start[0]-shear*(seg.end[1]-seg.start[1]),
                          seg.end[1]-seg.start[1])/s.speed_cm_s+s.attachment_time_s for seg in segments)


def recommended_wait(state, task):
    """Choose a small phase wait only if a nominal geometric cost decreases.

    The cost approximation freezes shear while evaluating a component. Actual
    execution remains continuous, so experiments must verify any advantage.
    """
    s = state.motion.settings
    if s.method_policy != "phase_wait" or s.frequency_hz == 0 or s.amplitude_cm == 0:
        return 0.0
    segments = [seg for seg in state.segments if seg.task == task and seg.index not in state.done]
    if not segments:
        return 0.0
    current = component_duration(segments, state.motion, state.snapshot_time)
    step = max(s.integration_step_s, 0.25)
    candidates = [min(s.max_method_wait_s, k*step) for k in range(1, math.ceil(s.max_method_wait_s/step)+1)]
    best = min(candidates, key=lambda delay: delay+component_duration(segments, state.motion, state.snapshot_time+delay), default=0)
    benefit = current-best-component_duration(segments, state.motion, state.snapshot_time+best)
    return best if benefit > 0.05 else 0.0


def wait_for_support(state, index, duration):
    if duration <= 0 or index in state.done:
        return False
    state.snapshot_time += duration
    return state


def build_web(state):
    tasks = dict.fromkeys(seg.task for seg in state.segments if seg.index not in state.done)
    return [("build_component", task) for task in tasks]


def build_component(state, task):
    if recommended_wait(state, task) > 0:
        return False
    return [("place_segment", seg.index, state.motion.world(seg.end, state.snapshot_time))
            for seg in state.segments if seg.task == task and seg.index not in state.done]


def build_component_with_wait(state, task):
    delay = recommended_wait(state, task)
    if delay <= 0:
        return False
    remaining = [seg for seg in state.segments if seg.task == task and seg.index not in state.done]
    return [("wait_for_support", remaining[0].index, delay)] + [
        ("place_segment", seg.index, state.motion.world(seg.end, state.snapshot_time+delay)) for seg in remaining]


def setup_domain(counter=None):
    """Return a domain; counter records actual method invocations, not depth."""
    domain = gtpyhop.Domain("mulder_moving_supports")
    gtpyhop.declare_actions(place_segment, wait_for_support)

    def counted(fn):
        def wrapped(*args):
            if counter is not None:
                counter[0] += 1
            return fn(*args)
        wrapped.__name__ = fn.__name__
        return wrapped

    gtpyhop.declare_task_methods("build_web", counted(build_web))
    gtpyhop.declare_task_methods("build_component", counted(build_component), counted(build_component_with_wait))
    return domain
