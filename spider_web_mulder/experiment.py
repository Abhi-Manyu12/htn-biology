"""Paired moving-support experiments. Run with python -m spider_web_mulder."""

import argparse
import contextlib
import csv
from dataclasses import asdict, replace
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics
import platform
import time

import gtpyhop

from .model import Shear, construction, load_settings, make_state, setup_domain
from .measurements import measure_web
from .tracking import SampledTrack, execute_tracking

MODEL_VERSION = 3


# feedback, retry after a miss, proactive trigger
POLICIES = {
    "fixed": (False, False, None),
    "local": (True, False, None),
    "filtered": (True, True, "filtered"),
    "local_repair": (True, True, None),
    "full": (True, True, "full"),
    "predictive": (True, True, "predictive"),
}
CONTROLLERS = tuple(POLICIES)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def nominal_duration(segment, settings):
    return distance(segment.start, segment.end) / settings.speed_cm_s + settings.attachment_time_s


def feasibility_margin(actions, segments, motion, now, settings):
    """Sampled endpoint drift margin for the active compound task.

    This is a forecast under known sinusoidal forcing, not a robust guarantee
    over unknown disturbances. A negative estimate requests task-level repair.
    """
    task = segments[actions[0][1]].task
    if settings.execution_mode == "tracking":
        # Conservative bound on relative path length under any shear within
        # the configured amplitude. Sensor lag contributes a separate error
        # estimate. This does not predict silk tension or guarantee contact.
        margins = []
        for _, index, _ in actions:
            seg = segments[index]
            if seg.task != task:
                break
            dx, dy = seg.end[0]-seg.start[0], seg.end[1]-seg.start[1]
            shear = settings.amplitude_cm/settings.height_cm
            upper_length = max(math.hypot(dx-sign*shear*dy, dy) for sign in (-1,1))
            slack_cm = settings.speed_cm_s*(settings.max_action_time_s-settings.attachment_time_s)-upper_length
            lag_cm = (1-seg.end[1]/settings.height_cm)*settings.amplitude_cm*2*math.pi*settings.frequency_hz*settings.sensor_tau_s
            margins.append(min(slack_cm, settings.attachment_tolerance_cm-lag_cm))
        return min(margins)
    elapsed = 0.0
    margin = math.inf
    for _, index, target in actions:
        seg = segments[index]
        if seg.task != task:
            break
        duration = nominal_duration(seg, settings)
        end = min(elapsed + duration, settings.prediction_horizon_s)
        if elapsed > settings.prediction_horizon_s:
            break
        for k in range(settings.prediction_samples):
            offset = elapsed + (end - elapsed) * k / (settings.prediction_samples - 1)
            drift = distance(target, motion.world(seg.end, now + offset))
            margin = min(margin, settings.correction_limit_cm + settings.attachment_tolerance_cm - drift)
        elapsed += duration
    return margin


def arrival_correction(target, endpoint, now, motion, settings):
    """Diagnostic oracle: choose a bounded horizontal correction using future motion.

    Search all sign changes on a dense grid and refine roots. This is not a
    general physical reachability proof or a production controller.
    """
    limit = settings.correction_limit_cm
    speed = settings.correction_speed_cm_s
    def residual(delta):
        return target[0] + delta - motion.world(endpoint, now + abs(delta) / speed)[0]
    candidates = [0.0]
    grid = [-limit + 2 * limit * k / 2000 for k in range(2001)]
    candidates.extend(grid)
    for left, right in zip(grid, grid[1:]):
        if residual(left) * residual(right) < 0:
            for _ in range(40):
                middle = (left + right) / 2
                if residual(left) * residual(middle) <= 0:
                    right = middle
                else:
                    left = middle
            candidates.append((left + right) / 2)
    feasible = [d for d in candidates if abs(residual(d)) <= settings.attachment_tolerance_cm]
    delta = min(feasible, key=abs) if feasible else min(candidates, key=lambda d: (abs(residual(d)), abs(d)))
    return (target[0] + delta, target[1])


def execute(segment, target, position, now, motion, settings, feedback,
            *, details=None, correction_mode="endpoint", observe=None):
    """Execute a world-space command then optionally correct its endpoint.

    Travel is integrated in material (frame-relative) coordinates to exclude
    passive support advection. A finite endpoint correction takes real time;
    the support keeps moving during that correction. Failed attempts consume
    travel/time but do not commit a finished thread to the web.
    """
    if settings.execution_mode == "tracking" and correction_mode == "endpoint":
        return execute_tracking(segment, target, position, now, motion, settings, feedback,
                                details=details, observe=observe)
    start_time = now
    if observe:
        observe(now, position)
    start_world = motion.world(position, now)
    duration = distance(position, motion.material(target, now)) / settings.speed_cm_s
    duration += settings.attachment_time_s
    duration = max(duration, 1e-9)
    previous = position
    travel = 0.0
    steps = max(1, math.ceil(duration / settings.integration_step_s))
    for k in range(1, steps + 1):
        fraction = k / steps
        stamp = start_time + fraction * duration
        point = tuple(a + fraction * (b - a) for a, b in zip(start_world, target))
        current = motion.material(point, stamp)
        travel += distance(previous, current)
        previous = current
        if observe:
            observe(stamp, current)
    now += duration
    arrival_time = now
    target_at_arrival = motion.world(segment.end, now)
    error_before = distance(motion.material(target, now), segment.end)
    actual_world = target
    correction = 0.0
    drift = distance(target, target_at_arrival)
    if feedback:
        desired = motion.world(segment.end, now)
        drift = distance(actual_world, desired)
        correction = min(drift, settings.correction_limit_cm)
        if correction_mode == "arrival_oracle":
            corrected = arrival_correction(target, segment.end, now, motion, settings)
            correction = distance(target, corrected)
        elif correction_mode == "endpoint":
            corrected = tuple(a + correction / drift * (b - a)
                              for a, b in zip(actual_world, desired)) if drift > 1e-12 else target
        else:
            raise ValueError(f"Unknown correction mode: {correction_mode}")
        if correction > 1e-12:
            correction_duration = correction / settings.correction_speed_cm_s
            steps = max(1, math.ceil(correction_duration / settings.integration_step_s))
            for k in range(1, steps + 1):
                fraction = k / steps
                stamp = now + fraction * correction_duration
                point = tuple(a + fraction * (b - a) for a, b in zip(actual_world, corrected))
                current = motion.material(point, stamp)
                travel += distance(previous, current)
                previous = current
                if observe:
                    observe(stamp, current)
            now += correction_duration
            actual_world = corrected
    actual = motion.material(actual_world, now)
    error = distance(actual, segment.end)
    if details is not None:
        details.update(start_time_s=start_time, arrival_time_s=arrival_time,
                       end_time_s=now, duration_s=now - start_time,
                       target_world_cm=target, target_at_departure_cm=motion.world(segment.end, start_time),
                       target_at_arrival_cm=target_at_arrival,
                       target_at_finish_cm=motion.world(segment.end, now),
                       target_motion_during_correction_cm=distance(target_at_arrival, motion.world(segment.end, now)),
                       error_before_correction_cm=error_before,
                       requested_correction_cm=drift if feedback else 0.0,
                       correction_limit_cm=settings.correction_limit_cm if feedback else 0.0,
                       correction_saturated=feedback and drift > settings.correction_limit_cm,
                       feedback=feedback, intended_material_cm=segment.end,
                       tolerance_cm=settings.attachment_tolerance_cm, execution_mode="endpoint")
    return actual, now, travel, error, correction


def polygon_area(points):
    if len(points) < 3:
        return None
    return abs(sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(points, points[1:] + points[:1]))) / 2


def run_trial(settings, controller, seed=0, *, record_path=False, hierarchy="htn",
              planner_backend="legacy", forced_miss_index=None, record_planner_tree=False):
    if controller not in CONTROLLERS:
        raise ValueError(f"Unknown controller: {controller}")
    feedback, can_retry, trigger = POLICIES[controller]
    if hierarchy not in ("htn", "flat"):
        raise ValueError("hierarchy must be htn or flat")
    if planner_backend not in ("legacy", "ipyhop_fresh", "ipyhop_retained"):
        raise ValueError("Unknown planner_backend")
    if planner_backend != "legacy" and hierarchy != "htn":
        raise ValueError("IPyHOP requires hierarchy=htn")
    if forced_miss_index is not None and (isinstance(forced_miss_index, bool) or
            not isinstance(forced_miss_index, int) or forced_miss_index < 0):
        raise ValueError("forced_miss_index must be a nonnegative integer")
    # Every controller gets the identical continuous trajectory for this seed.
    phase = random.Random(seed).uniform(0, 2 * math.pi)
    motion = Shear(settings, phase)
    segments = construction(settings)
    state = make_state(segments, motion)
    counter = [0]
    setup_domain(counter)
    backend = None
    if planner_backend != "legacy":
        from .reentrant import MulderPlanner
        backend = MulderPlanner(planner_backend, counter, record_planner_tree)
    if forced_miss_index is not None and forced_miss_index >= len(segments):
        raise ValueError("forced_miss_index outside construction")
    forced_miss_used = False
    now = 0.0
    position = segments[0].start
    planning_seconds = 0.0
    planning_calls = 0
    repairs = 0
    trace = []
    travel = 0.0
    silk_length = 0.0
    phase_time = dict.fromkeys(("frame", "radials", "auxiliary", "capture"), 0.0)
    phase_travel = dict.fromkeys(phase_time, 0.0)
    endpoints = {}
    filtered = 0.0
    previous_check = 0.0
    filtered_task = None
    target_times = {}
    target_plans = {}
    camera = SampledTrack() if record_path else None
    if camera:
        camera.observe(0, position)

    def plan(task=None):
        nonlocal planning_calls, planning_seconds
        state.snapshot_time = now
        started = time.perf_counter()
        if backend is not None:
            # Both IPyHOP modes return the entire unexecuted suffix. Re-entry
            # selects scope through the actual tree rather than cached splicing.
            result = backend.plan(state)
        else:
            result = legacy_plan(task)
        planning_seconds += time.perf_counter() - started
        planning_calls += 1
        if result is False or result is None:
            raise RuntimeError("Symbolic construction plan is infeasible")
        for _, index, _ in result:
            target_times[index] = now
            target_plans[index] = planning_calls
        return result

    def legacy_plan(task):
        with contextlib.redirect_stdout(io.StringIO()):
            # GTPyhop uses process-global current-domain and verbosity settings.
            old_verbose = gtpyhop.get_verbose_level()
            try:
                gtpyhop.set_verbose_level(0)
                if hierarchy == "flat":
                    todo = [("place_segment", seg.index, motion.world(seg.end, now))
                            for seg in segments if seg.index not in state.done and (task is None or seg.task == task)]
                else:
                    todo = [("build_component", task)] if task else [("build_web",)]
                result = gtpyhop.find_plan(state, todo)
            finally:
                gtpyhop.set_verbose_level(old_verbose)
        return result

    actions = plan()
    attempts = {}
    failure = None
    monitoring_seconds = 0.0
    prediction_checks = 0
    just_repaired = False
    method_waits = 0
    method_wait_seconds = 0.0
    while actions:
        if now >= settings.max_elapsed_s:
            failure = "time_limit"
            break
        if actions[0][0] == "wait_for_support":
            _, index, delay = actions.pop(0)
            seg = segments[index]
            before = now
            now = min(settings.max_elapsed_s, now+delay)
            phase_time[seg.phase] += now-before
            if backend is not None:
                backend.completed()
            method_waits += 1
            method_wait_seconds += now-before
            if camera:
                camera.phase = seg.phase
                camera.observe(now, position)
            trace.append(dict(event="method_wait", index=index, task=seg.task, time_s=now,
                              start_time_s=before, end_time_s=now, wait_s=now-before,
                              reason="phase_wait_method"))
            continue
        index = actions[0][1]
        seg = segments[index]
        drift = distance(actions[0][2], motion.world(seg.end, now))
        interval = now - previous_check
        alpha = -math.expm1(-interval / settings.filter_tau_s)
        filter_reset = seg.task != filtered_task
        if filter_reset:
            # Do not average errors for unrelated component endpoints.
            filtered = drift
            filtered_task = seg.task
        else:
            filtered += alpha * (drift - filtered)
        changed = motion.changed_between(previous_check, now)
        previous_check = now
        margin = None
        scope = None
        reason = None
        if not just_repaired and trigger == "full" and changed:
            scope, reason = "web", "support_change"
        elif not just_repaired and trigger == "filtered" and filtered > settings.event_threshold_cm:
            scope, reason = "component", "filtered_drift"
        elif not just_repaired and trigger == "predictive":
            started = time.perf_counter()
            margin = feasibility_margin(actions, segments, motion, now, settings)
            monitoring_seconds += time.perf_counter() - started
            prediction_checks += 1
            if margin < 0:
                scope, reason = "component", "predicted_drift"
        trace.append(dict(event="decision", time_s=now, index=index, task=seg.task,
                          controller=controller, drift_cm=drift, filtered_drift_cm=filtered,
                          filter_reset=filter_reset, event_threshold_cm=settings.event_threshold_cm,
                          support_changed=changed, margin_cm=margin, scope=scope, reason=reason,
                          skipped_proactive_after_retry=just_repaired,
                          target_age_s=now - target_times[index], plan_id=target_plans[index]))
        just_repaired = False
        if scope:
            before = now
            # During a repair delay the spider passively follows its material point.
            now += settings.repair_delay_s
            phase_time[seg.phase] += now - before
            replacement = plan(None if scope == "web" else seg.task)
            actions = replacement if scope == "web" or backend is not None else replacement + [
                a for a in actions if segments[a[1]].task != seg.task]
            repairs += 1
            trace.append(dict(event="repair", time_s=now, index=index, task=seg.task,
                              scope=scope, reason=reason, margin_cm=margin,
                              start_time_s=before, end_time_s=now, plan_id=planning_calls,
                              updated_indices=[a[1] for a in replacement]))
            filtered = 0.0
            if actions[0][0] == "wait_for_support":
                just_repaired = True
                continue

        _, index, target = actions[0]
        seg = segments[index]
        before = now
        start = position
        execution_details = {}
        if camera:
            camera.phase = seg.phase
        position, now, walked, error, correction = execute(
            seg, target, position, now, motion, settings, feedback, details=execution_details,
            observe=camera.observe if camera else None)
        travel += walked
        phase_time[seg.phase] += now - before
        phase_travel[seg.phase] += walked
        accepted = error <= settings.attachment_tolerance_cm + 1e-9
        injected_miss = accepted and index == forced_miss_index and not forced_miss_used
        if injected_miss:
            accepted = False
            forced_miss_used = True
        if execution_details.get("action_timed_out"):
            accepted = False
            failure = "action_time_limit"
        if now >= settings.max_elapsed_s and not (accepted and len(state.done)+1 == len(segments)):
            accepted = False
            failure = "time_limit"
        trace.append(dict(event="action", time_s=now, index=index, task=seg.task,
                          phase=seg.phase, accepted=accepted, injected_miss=injected_miss, error_cm=error,
                          correction_cm=correction, travel_cm=walked,
                          silk=seg.silk, start_material_cm=start, end_material_cm=position,
                          attempt=attempts.get(index, 0) + 1,
                          target_created_s=target_times[index], plan_id=target_plans[index],
                          target_age_s=before - target_times[index], **execution_details))
        if accepted:
            endpoints[index] = (start, position)
            if seg.silk:
                silk_length += distance(start, position)
            state.done.add(index)
            actions.pop(0)
            if backend is not None:
                backend.completed()
        else:
            attempts[index] = attempts.get(index, 0) + 1
            if failure or not can_retry or attempts[index] > settings.max_repairs_per_action:
                failure = failure or "attachment_miss"
                break
            repair_started = now
            now += settings.repair_delay_s
            phase_time[seg.phase] += settings.repair_delay_s
            # Retry the smallest affected compound task, preserving completed work.
            replacement = plan(seg.task)
            actions = replacement if backend is not None else replacement + [a for a in actions if segments[a[1]].task != seg.task]
            repairs += 1
            trace.append(dict(event="repair", time_s=now, index=index, task=seg.task,
                              scope="component", reason="attachment_miss", margin_cm=None,
                              start_time_s=repair_started, end_time_s=now, plan_id=planning_calls,
                              updated_indices=[a[1] for a in replacement]))
            just_repaired = True
            filtered = 0.0

    reference = sum(distance(seg.start, seg.end) for seg in segments)
    frame_indices = [seg.index for seg in segments if seg.phase == "frame" and seg.silk]
    frame_points = [endpoints[i][1] for i in frame_indices if i in endpoints]
    errors = [row["error_cm"] for row in trace if row["event"] == "action" and row["accepted"]]
    capture = [endpoints[seg.index][1] for seg in segments
               if seg.phase == "capture" and seg.silk and seg.index in endpoints]
    mesh = [distance(a, b) for a, b in zip(capture, capture[settings.radial_count:])]
    task_counts = {phase_name: sum(seg.index in state.done and seg.silk and seg.phase == phase_name
                                  for seg in segments) for phase_name in phase_time}
    trajectory = dict(amplitude_cm=settings.amplitude_cm, frequency_hz=settings.frequency_hz, phase=phase)
    trajectory_id = hashlib.sha256(json.dumps(trajectory, sort_keys=True).encode()).hexdigest()[:16]
    result = dict(controller=controller, seed=seed, trajectory_id=trajectory_id,
                  execution_mode=settings.execution_mode, hierarchy=hierarchy, model_version=MODEL_VERSION,
                  method_policy=settings.method_policy, method_waits=method_waits,
                  method_wait_s=method_wait_seconds,
                  amplitude_cm=settings.amplitude_cm, frequency_hz=settings.frequency_hz,
                  initial_phase_rad=phase, success=len(state.done) == len(segments),
                  failure_reason=failure, completed_actions=len(state.done), total_actions=len(segments),
                  elapsed_s=now, travel_cm=travel, normalized_travel=travel / reference,
                  silk_chord_length_cm=silk_length, planning_calls=planning_calls,
                  repairs=repairs, method_calls=counter[0], planning_wall_s=planning_seconds,
                  prediction_checks=prediction_checks, prediction_wall_s=monitoring_seconds,
                  repairs_per_attempt=repairs / max(1, sum(t["event"] == "action" for t in trace)),
                  attachment_error_mean_cm=statistics.mean(errors) if errors else None,
                  capture_mesh_proxy_cm=statistics.mean(mesh) if mesh else None,
                  frame_area_cm2=polygon_area(frame_points) if len(frame_points) == 4 else None)
    for phase_name in phase_time:
        result[f"{phase_name}_time_s"] = phase_time[phase_name]
        result[f"{phase_name}_travel_cm"] = phase_travel[phase_name]
        result[f"{phase_name}_segments"] = task_counts[phase_name]
        result[f"{phase_name}_time_pct"] = 100*phase_time[phase_name]/now if now else 0
        result[f"{phase_name}_travel_pct"] = 100*phase_travel[phase_name]/travel if travel else 0
    result.update(measure_web(segments, endpoints, settings, result["success"]))
    if camera:
        result["sampled_travel_10s_cm"] = camera.finish(now, position)
        sampled_by_phase = dict.fromkeys(phase_time, 0.0)
        for a,b in zip(camera.samples,camera.samples[1:]):
            sampled_by_phase[b["phase"]] += distance(a["material_cm"],b["material_cm"])
        for phase_name,value in sampled_by_phase.items():
            result[f"sampled_{phase_name}_travel_pct"] = 100*value/result["sampled_travel_10s_cm"] if result["sampled_travel_10s_cm"] else 0
        trace.append(dict(event="camera_track", samples=camera.samples))
    if backend is not None:
        result.update(planner_backend=planner_backend, reentries=backend.reentries, model_version=4)
        trace.extend(backend.snapshots)
    return result, trace


def web_svg(trace, settings):
    """Accepted threads in frame-relative coordinates; failed attempts omitted."""
    colors = {"frame": "#555555", "radials": "#2a6fbb", "auxiliary": "#bbbbbb", "capture": "#d17626"}
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 {settings.width_cm + 4} {settings.height_cm + 4}">',
             '<rect x="-2" y="-2" width="100%" height="100%" fill="white"/>']
    for event in trace:
        if event["event"] != "action" or not event["accepted"] or not event["silk"]:
            continue
        a, b = event["start_material_cm"], event["end_material_cm"]
        lines.append(f'<line x1="{a[0]}" y1="{settings.height_cm - a[1]}" '
                     f'x2="{b[0]}" y2="{settings.height_cm - b[1]}" '
                     f'stroke="{colors[event["phase"]]}" stroke-width="0.06"/>')
    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def summarize(rows):
    """Wilson success intervals and paired success differences against local."""
    groups = {}
    for row in rows:
        key = (row["amplitude_cm"], row["frequency_hz"], row["controller"])
        groups.setdefault(key, []).append(row)
    summaries = []
    for (amplitude, frequency, controller), group in groups.items():
        n = len(group)
        p = sum(r["success"] for r in group) / n
        z = 1.959963984540054
        denominator = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denominator
        radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
        local = {r["seed"]: r for r in groups.get((amplitude, frequency, "local"), [])}
        paired = [int(r["success"]) - int(local[r["seed"]]["success"])
                  for r in group if r["seed"] in local]
        successful = [r for r in group if r["success"]]
        summaries.append(dict(amplitude_cm=amplitude, frequency_hz=frequency, controller=controller,
                              trials=n, success_rate=p, success_ci95=[center - radius, center + radius],
                              paired_success_difference_vs_local=statistics.mean(paired) if paired else None,
                              mean_repairs=statistics.mean(r["repairs"] for r in group),
                              successful_trials=len(successful),
                              successful_mean_travel_cm=statistics.mean(r["travel_cm"] for r in successful) if successful else None))
    return summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--controllers", nargs="+", choices=CONTROLLERS, default=list(CONTROLLERS))
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--amplitudes", nargs="+", type=float)
    parser.add_argument("--frequencies", nargs="+", type=float)
    parser.add_argument("--output", type=Path, default=Path("mulder_results"))
    parser.add_argument("--trace", action="store_true", help="Write per-trial action/repair traces")
    args = parser.parse_args(argv)
    settings, experiment = load_settings(args.config)
    seeds = args.seeds if args.seeds is not None else experiment.get("seeds", [0])
    amplitudes = args.amplitudes if args.amplitudes is not None else experiment.get("amplitudes_cm", [settings.amplitude_cm])
    frequencies = args.frequencies if args.frequencies is not None else experiment.get("frequencies_hz", [settings.frequency_hz])
    if not seeds or len(set(seeds)) != len(seeds):
        parser.error("Seeds must be nonempty and unique")
    if len(set(args.controllers)) != len(args.controllers):
        parser.error("Controllers must be unique")
    # Validate the whole sweep before writing any output.
    cases = [replace(settings, amplitude_cm=a, frequency_hz=f) for a in amplitudes for f in frequencies]
    if not cases:
        parser.error("Sweep must contain at least one condition")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Output directory is not empty; choose a new directory")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_index, case in enumerate(cases):
        for seed in seeds:
            for controller in args.controllers:
                row, trace = run_trial(case, controller, seed)
                rows.append(row)
                if args.trace:
                    path = args.output / f"trace_{case_index}_{seed}_{controller}.json"
                    path.write_text(json.dumps(trace, indent=2, allow_nan=False) + "\n")
                    path.with_suffix(".svg").write_text(web_svg(trace, case))
        print(f"A={case.amplitude_cm:g} cm, f={case.frequency_hz:g} Hz: completed {len(seeds) * len(args.controllers)} trials", flush=True)
    with (args.output / "trials.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "summary.json").write_text(json.dumps(summarize(rows), indent=2, allow_nan=False) + "\n")
    metadata = dict(settings=asdict(settings), seeds=seeds, controllers=args.controllers,
                    amplitudes_cm=amplitudes, frequencies_hz=frequencies,
                    paper_doi="10.1007/s00114-021-01725-1", model_version=MODEL_VERSION,
                    assumptions=["affine shear", "known sinusoidal forecast", "pre-established hub and supports",
                                 "prescribed counts and spiral waypoints", "no silk mechanics or abandonment policy"])
    metadata["python_version"] = platform.python_version()
    metadata["source_sha256"] = {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("model.py", "experiment.py", "tracking.py", "measurements.py")}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()
