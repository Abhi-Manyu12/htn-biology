"""Continuous feedback on an advecting support, with explicit contact dwell.

Passive advection is the no-slip substrate assumption. Locomotion is bounded
relative to the instantaneous sheared substrate, not relative to the room.
This models kinematics, not silk forces, compliance or a spider's cognition.
"""

import math


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def execute_tracking(segment, target, position, now, motion, settings, feedback,
                     *, details=None, observe=None):
    start = now
    departure = motion.world(segment.end, now)
    sensed = departure
    travel = 0.0
    goal_error_before = distance(position, segment.end)
    if observe:
        observe(now, position)
    # Reserve time for attachment, and clip to the experiment deadline.
    deadline = max(start, min(start + settings.max_action_time_s, settings.max_elapsed_s))
    movement_deadline = max(start, deadline - settings.attachment_time_s)
    reached = False
    while now < movement_deadline - 1e-12:
        step = min(settings.integration_step_s, movement_deadline - now)
        actual_target = motion.world(segment.end, now)
        if feedback:
            alpha = 1.0 if settings.sensor_tau_s == 0 else -math.expm1(-step / settings.sensor_tau_s)
            sensed = tuple(a + alpha * (b - a) for a, b in zip(sensed, actual_target))
            goal = motion.material(sensed, now)
        else:
            goal = motion.material(target, now)
        dx, dy = goal[0] - position[0], goal[1] - position[1]
        remaining = math.hypot(dx, dy)
        if remaining <= 1e-9:
            reached = True
            break
        ux, uy = dx / remaining, dy / remaining
        # J = [[1, -displacement/height], [0, 1]]. Use a conservative
        # within-step bound so relative locomotion never exceeds the speed cap.
        s = settings
        displacements = [motion.displacement(now), motion.displacement(now + step)] if hasattr(motion, "displacement") else [
            motion.world((0, 0), now)[0], motion.world((0, 0), now + step)[0]]
        if hasattr(motion, "settings") and s.amplitude_cm and s.frequency_hz:
            omega = 2 * math.pi * s.frequency_hz
            first = math.ceil((omega * now + motion.phase - math.pi / 2) / math.pi)
            last = math.floor((omega * (now + step) + motion.phase - math.pi / 2) / math.pi)
            for k in range(first, min(last, first + 1) + 1):
                displacements.append(s.amplitude_cm * (-1) ** k)
        stretch = max(math.hypot(ux - d / s.height_cm * uy, uy) for d in displacements)
        amount = min(remaining, s.speed_cm_s * step / max(stretch, 1e-12))
        # A fractional last step lands precisely on the measured destination.
        used = amount * stretch / s.speed_cm_s
        position = (position[0] + amount * ux, position[1] + amount * uy)
        now += used
        travel += amount
        if observe:
            observe(now, position)
        if amount >= remaining - 1e-12:
            reached = True
            break
    arrival = now
    before = distance(position, segment.end)
    # During contact the spider follows its substrate point, including on
    # fixed/open-loop trials. It has no further locomotion during this dwell.
    now = min(deadline, now + settings.attachment_time_s)
    if observe:
        observe(now, position)
    error = distance(position, segment.end)
    if details is not None:
        details.update(start_time_s=start, arrival_time_s=arrival, end_time_s=now,
                       duration_s=now-start, target_world_cm=target,
                       target_at_departure_cm=departure, target_at_arrival_cm=motion.world(segment.end, arrival),
                       target_at_finish_cm=motion.world(segment.end, now),
                       target_motion_during_correction_cm=0.0, error_before_correction_cm=before,
                       requested_correction_cm=0.0, correction_limit_cm=0.0,
                       correction_saturated=False, feedback=feedback,
                       intended_material_cm=segment.end, tolerance_cm=settings.attachment_tolerance_cm,
                       execution_mode="tracking", contact_reached=reached,
                       action_timed_out=not reached, initial_error_cm=goal_error_before,
                       contact_dwell_s=now-arrival)
    return position, now, travel, error, 0.0


class SampledTrack:
    """Sample frame-corrected trajectories at a fixed camera cadence."""
    def __init__(self, interval=10.0):
        self.interval = interval
        self.previous = None
        self.next_time = 0.0
        self.samples = []
        self.phase = "frame"

    def observe(self, stamp, point):
        if self.previous is None:
            self.previous = (stamp, point)
        old_time, old = self.previous
        while self.next_time <= stamp + 1e-10:
            fraction = (self.next_time-old_time)/(stamp-old_time) if stamp > old_time else 1.0
            fraction = min(1.0, max(0.0, fraction))
            xy = tuple(a + fraction*(b-a) for a, b in zip(old, point))
            self.samples.append(dict(time_s=self.next_time, material_cm=xy, phase=self.phase))
            self.next_time += self.interval
        self.previous = (stamp, point)

    def finish(self, stamp, point):
        self.observe(stamp, point)
        if self.samples and stamp > self.samples[-1]["time_s"] + 1e-9:
            self.samples.append(dict(time_s=stamp, material_cm=point, phase=self.phase))
        return sum(distance(a["material_cm"], b["material_cm"])
                   for a,b in zip(self.samples, self.samples[1:]))
