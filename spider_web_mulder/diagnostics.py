"""Explain matched controller trials: python3 -m spider_web_mulder.diagnostics."""

import argparse
import csv
from dataclasses import asdict, dataclass, replace
import hashlib
import html
import json
import math
from pathlib import Path

from .experiment import CONTROLLERS, MODEL_VERSION, execute, run_trial, web_svg
from .model import Shear, construction, load_settings


@dataclass(frozen=True)
class FrozenMotion:
    """Hold the frame at the failed action's departure pose, not at zero shear."""
    original: Shear
    frozen_at: float

    def world(self, point, time):
        return self.original.world(point, self.frozen_at)

    def material(self, point, time):
        return self.original.material(point, self.frozen_at)


def replay_failure(settings, result, trace):
    """Isolated replays of the FIRST miss, sharing start position and time.

    These do not continue or replace the original trial. No repair delay is
    charged: each replay asks a question about the exact pre-action state.
    """
    failed = next((e for e in trace if e["event"] == "action" and not e["accepted"]), None)
    if failed is None:
        return []
    motion = Shear(settings, result["initial_phase_rad"])
    segment = construction(settings)[failed["index"]]
    now = failed["start_time_s"]
    saved = tuple(failed["target_world_cm"])
    refreshed = motion.world(segment.end, now)
    frozen = FrozenMotion(motion, now)
    cases = [
        ("original", saved, motion, failed["feedback"], "endpoint"),
        ("refreshed_target", refreshed, motion, failed["feedback"], "endpoint"),
        ("frozen_saved_target", saved, frozen, failed["feedback"], "endpoint"),
        ("frozen_refreshed_target", refreshed, frozen, failed["feedback"], "endpoint"),
        ("arrival_oracle", saved, motion, True, "arrival_oracle"),
        ("refreshed_arrival_oracle", refreshed, motion, True, "arrival_oracle"),
    ]
    rows = []
    for name, target, forcing, feedback, mode in cases:
        details = {}
        position, end, travel, error, correction = execute(
            segment, target, tuple(failed["start_material_cm"]), now,
            forcing, settings, feedback, details=details, correction_mode=mode)
        rows.append(dict(controller=result["controller"], replay=name, index=segment.index,
                         task=segment.task, start_time_s=now, end_time_s=end,
                         start_material_cm=failed["start_material_cm"], end_material_cm=position,
                         accepted=error <= settings.attachment_tolerance_cm + 1e-9 and not details.get("action_timed_out",False),
                         error_cm=error, correction_cm=correction, travel_cm=travel,
                         feedback=feedback,
                         intervention_note="Changes executor to endpoint plus future-aware correction" if
                         settings.execution_mode=="tracking" and mode=="arrival_oracle" else "Same executor as original",
                         **{k: v for k, v in details.items()
                                             if k not in ("start_time_s", "end_time_s", "feedback")}))
    return rows


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, tuple, dict)) else v
                             for k, v in row.items()})


def action_map(settings, traces):
    rows = []
    for seg in construction(settings):
        row = dict(index=seg.index, task=seg.task, phase=seg.phase,
                   start_material_cm=seg.start, intended_material_cm=seg.end, silk=seg.silk)
        for controller in CONTROLLERS:
            attempts = [e for e in traces[controller] if e["event"] == "action" and e["index"] == seg.index]
            row[controller] = "; ".join(f'{e["attempt"]}: {"accepted" if e["accepted"] else "missed"}'
                                        for e in attempts) or "not reached"
        rows.append(row)
    return rows


def timeline_svg(results, traces, settings):
    width, height = 1150, 290
    left, plot_width = 130, 970
    maximum = max(r["elapsed_s"] for r in results) or 1
    x = lambda t: left + t / maximum * plot_width
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Controller timelines and frame displacement">',
             '<rect width="100%" height="100%" fill="white"/>']
    for i, row in enumerate(results):
        y = 28 + i * 27
        lines.append(f'<text x="5" y="{y+4}" font-size="12">{row["controller"]}</text>')
        for event in traces[row["controller"]]:
            if event["event"] == "action":
                color = "#287d55" if event["accepted"] else "#c53030"
                lines.append(f'<rect x="{x(event["start_time_s"]):.3f}" y="{y-6}" '
                             f'width="{max(.8, x(event["time_s"])-x(event["start_time_s"])):.3f}" '
                             f'height="12" fill="{color}"><title>Action {event["index"]}, attempt {event["attempt"]}, '
                             f'error {event["error_cm"]:.4f} cm</title></rect>')
            elif event["event"] == "repair":
                lines.append(f'<path d="M{x(event["time_s"]):.3f},{y-10}v20" stroke="#7b3caa">'
                             f'<title>{event["reason"]}: {event["scope"]}</title></path>')
    motion = Shear(settings, results[0]["initial_phase_rad"])
    # Resolve the sinusoid even in long trials, capped to keep artifacts small.
    count = min(20000, max(400, math.ceil(maximum * settings.frequency_hz * 40)))
    scale = max(settings.amplitude_cm, 1)
    points = " ".join(f'{x(t):.3f},{220 - 22 * motion.displacement(t) / scale:.3f}'
                      for t in (maximum * k / count for k in range(count + 1)))
    lines += [f'<polyline points="{points}" fill="none" stroke="#2864b4" stroke-width="1"/>',
              '<text x="5" y="220" font-size="11">Frame motion</text>',
              f'<text x="{left}" y="260" font-size="12">0 s</text>',
              f'<text x="{width-150}" y="260" font-size="12">{maximum:.1f} s</text>',
              '<text x="130" y="282" font-size="11">Green: accepted · Red: missed · Purple: repair · Hover for details</text>', '</svg>']
    return "\n".join(lines)


def error_svg(trace, tolerance):
    events = [e for e in trace if e["event"] == "action"]
    high = max([tolerance * 1.2, .01] + [e["error_before_correction_cm"] for e in events] +
               [e["error_cm"] for e in events])
    x = lambda i: 60 + 840 * i / max(len(events) - 1, 1)
    y = lambda value: 170 - 140 * value / high
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 205" role="img" aria-label="Attachment error by attempt">',
             f'<path d="M60,{y(tolerance)}H900" stroke="#333" stroke-dasharray="5 3"/>',
             f'<text x="62" y="{y(tolerance)-4}" font-size="11">Tolerance {tolerance:g} cm</text>']
    for key, color in (("error_before_correction_cm", "#c97618"), ("error_cm", "#2864b4")):
        points = " ".join(f'{x(i):.2f},{y(e[key]):.2f}' for i, e in enumerate(events))
        lines.append(f'<polyline points="{points}" stroke="{color}" fill="none"/>')
        for i, event in enumerate(events):
            lines.append(f'<circle cx="{x(i):.2f}" cy="{y(event[key]):.2f}" r="2" fill="{color}">'
                         f'<title>Action {event["index"]}, attempt {event["attempt"]}: {event[key]:.5f} cm</title></circle>')
    lines.extend([f'<text x="5" y="25" font-size="11">{high:.2f} cm</text>',
                  '<text x="60" y="198" font-size="12">Attempt order → · Orange: before correction · Blue: after correction</text>', '</svg>'])
    return "\n".join(lines)


def report_html(results, traces, replays, settings):
    esc = lambda value: html.escape(str(value))
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Mulder controller diagnostics</title>',
             '<style>body{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 20px;color:#182333}svg{width:100%;height:auto}table{border-collapse:collapse;font-size:12px;width:100%}td,th{border:1px solid #ddd;padding:5px;text-align:left}th{position:sticky;top:0;background:#eee}.scroll{max-height:500px;overflow:auto}section{margin:30px 0}select,input{padding:8px}code{background:#eee}</style>',
             '<h1>Matched controller diagnostic report</h1>',
             f'<p>Amplitude {settings.amplitude_cm:g} cm; frequency {settings.frequency_hz:g} Hz; '
             f'executor {settings.execution_mode}; identical initial phase across controllers. Execution times diverge after interventions.</p>',
             '<p>This explains this simulation; it does not establish spider behaviour or physical unreachability.</p>',
             timeline_svg(results, traces, settings),
             '<h2>Complete event ledger</h2><label>Controller <select id="controller"><option value="">All</option>']
    parts += [f'<option>{c}</option>' for c in CONTROLLERS]
    parts += ['</select></label> <label>Event <select id="event"><option value="">All</option><option>decision</option><option>action</option><option>repair</option></select></label> ',
              '<label>Task or action <input id="search" placeholder="frame_1 or 2"></label>',
              '<p id="count"></p><div class="scroll"><table><thead><tr><th>Controller</th><th>Event</th><th>Time s</th><th>Action/task</th><th>Attempt</th><th>Target age s</th><th>Drift / before cm</th><th>After cm</th><th>Correction cm</th><th>Decision / reason</th></tr></thead><tbody id="ledger">']
    for result in results:
        controller = result["controller"]
        for event in traces[controller]:
            why = event.get("reason") or ("accepted" if event.get("accepted") else
                                          "missed" if event["event"] == "action" else "continue")
            values = [controller, event["event"], round(event["time_s"], 4),
                      f'{event["index"]} / {event["task"]}', event.get("attempt", ""),
                      round(event["target_age_s"], 4) if "target_age_s" in event else "",
                      round(event.get("error_before_correction_cm", event.get("drift_cm", 0)), 4),
                      round(event["error_cm"], 4) if "error_cm" in event else "",
                      round(event["correction_cm"], 4) if "correction_cm" in event else "", why]
            parts.append(f'<tr data-controller="{controller}" data-event="{event["event"]}" '
                         f'data-search="{event["index"]} {event["task"]}">' +
                         ''.join(f'<td>{esc(v)}</td>' for v in values) + '</tr>')
    parts += ['</tbody></table></div><h2>First-miss controlled replays</h2>',
              '<p>Every replay starts at exactly the original failed action’s position and time. '
              'Refreshed targets add no repair delay. Frozen frames keep the departure pose. '
              'Arrival oracles use perfect future motion and enable correction even for fixed; '
              'on tracking trials they additionally switch to the endpoint executor, as recorded in replay intervention notes. '
              'they are diagnostic interventions, not extra production controllers. '
              'The oracle searches bounded horizontal corrections; failure is not a proof of unreachability.</p>',
              '<table><tr><th>Controller</th><th>Action</th><th>Replay</th><th>Accepted</th><th>Error cm</th></tr>']
    for row in replays:
        parts.append('<tr>' + ''.join(f'<td>{esc(v)}</td>' for v in
                     (row["controller"], row["index"], row["replay"], row["accepted"], f'{row["error_cm"]:.6f}')) + '</tr>')
    parts.append('</table>')
    parts += ['<h2>Intended construction versus attempted actions</h2>',
              '<p>Every planned segment is listed. “Not reached” means construction stopped earlier, not that this segment itself failed.</p>',
              '<details><summary>Expand the complete six-controller action map</summary><div class="scroll"><table><tr><th>Action / component</th>']
    parts.extend(f'<th>{c}</th>' for c in CONTROLLERS)
    parts.append('</tr>')
    for row in action_map(settings, traces):
        parts.append(f'<tr><td>{row["index"]} / {row["task"]}</td>' +
                     ''.join(f'<td>{esc(row[c])}</td>' for c in CONTROLLERS) + '</tr>')
    parts.append('</table></div></details>')
    for row in results:
        c = row["controller"]
        parts += [f'<section><h2>{c}</h2><p>Completed {row["completed_actions"]}/{row["total_actions"]}; '
                  f'repairs {row["repairs"]}; final outcome {esc(row["failure_reason"] or "success")}.</p>',
                  error_svg(traces[c], settings.attachment_tolerance_cm), '</section>']
    parts += ['<script>function filter(){let n=0;for(const r of document.querySelectorAll("#ledger tr")){const show=(!controller.value||r.dataset.controller===controller.value)&&(!eventFilter.value||r.dataset.event===eventFilter.value)&&r.dataset.search.includes(search.value);r.hidden=!show;if(show)n++;}document.getElementById("count").textContent=n+" events shown";}const controller=document.getElementById("controller"),eventFilter=document.getElementById("event"),search=document.getElementById("search");for(const el of [controller,eventFilter,search])el.addEventListener("input",filter);filter();</script>', '</html>']
    return "\n".join(parts)


def report_markdown(results, traces, replays, settings, seed):
    lines = ["# Matched controller diagnostics", "",
             f"Amplitude **{settings.amplitude_cm:g} cm**, frequency **{settings.frequency_hz:g} Hz**, seed **{seed}**, executor **{settings.execution_mode}**.", "",
             "Open [report.html](report.html) for the filterable complete ledger, controller timelines and error plots.",
             "CSV/JSON ledgers retain every decision, attempt and repair, including repeated attempts of the same action.", "",
             "| Controller | Completed actions | Repairs | First missed action | Error at first miss (cm) |",
             "|---|---:|---:|---:|---:|"]
    for row in results:
        first = next((e for e in traces[row["controller"]] if e["event"] == "action" and not e["accepted"]), None)
        lines.append(f'| {row["controller"]} | {row["completed_actions"]}/{row["total_actions"]} | '
                     f'{row["repairs"]} | {first["index"] if first else "none"} | '
                     f'{format(first["error_cm"], ".6f") if first else "—"} |')
    lines.extend(["", "## Isolated first-failure replays", "",
                  "Each controller's replays share its original start position and time. Different controllers may have different start times.",
                  "No repair delay is introduced. All correction limits and speeds remain unchanged.", "",
                  "| Controller | Replay | Accepted | Final error (cm) |",
                  "|---|---|---|---:|"])
    for row in replays:
        lines.append(f'| {row["controller"]} | {row["replay"]} | {row["accepted"]} | {row["error_cm"]:.6f} |')
    lines.extend(["", "## Reading the evidence", "",
                  "- `original` must reproduce the recorded action exactly; automated tests check this.",
                  "- `refreshed_target` isolates stale commands by updating the target at departure with no added delay.",
                  "- `frozen_saved_target` removes subsequent frame movement while retaining stale-command error.",
                  "- `frozen_refreshed_target` removes both staleness and subsequent frame movement.",
                  "- The arrival oracles use perfect future motion to search for a bounded horizontal correction. They enable feedback even for `fixed`.",
                  "- A successful intervention identifies an execution strategy that works for this isolated action. It does not guarantee completion of a whole web.",
                  "- A failed oracle search is not proof that the target is physically unreachable. Continuous tracking, path alternatives and silk mechanics are not tested.",
                  "- The current predictive margin is a sampled drift estimate over nominal timings, not a forecast of the actual finite correction dynamics.",
                  f"- This report uses model version {MODEL_VERSION}; compare versions and executor modes explicitly.",
                  "- On tracking trials, arrival-oracle replays also change to endpoint execution; consult intervention_note in replays.json rather than treating that as an isolated correction change.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--amplitude", type=float, default=5.0)
    parser.add_argument("--frequency", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--execution-mode",choices=("endpoint","tracking"),default="endpoint")
    parser.add_argument("--output", type=Path, default=Path("mulder_results/diagnostics"))
    args = parser.parse_args(argv)
    settings, _ = load_settings(args.config)
    settings = replace(settings, amplitude_cm=args.amplitude, frequency_hz=args.frequency,
                       execution_mode=args.execution_mode,method_policy="direct")
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error("Choose an empty output directory")
    args.output.mkdir(parents=True, exist_ok=True)
    results, traces, ledger, replays = [], {}, [], []
    for controller in CONTROLLERS:
        row, trace = run_trial(settings, controller, args.seed)
        results.append(row)
        traces[controller] = trace
        ledger.extend(dict(controller=controller, sequence=i, **event) if "controller" not in event
                      else dict(sequence=i, **event) for i, event in enumerate(trace))
        replays.extend(replay_failure(settings, row, trace))
        (args.output / f"web_{controller}.svg").write_text(web_svg(trace, settings))
    for name, rows in (("trials", results), ("ledger", ledger), ("replays", replays),
                       ("action_map", action_map(settings, traces))):
        write_csv(args.output / f"{name}.csv", rows)
        (args.output / f"{name}.json").write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n")
    (args.output / "report.html").write_text(report_html(results, traces, replays, settings))
    (args.output / "report.md").write_text(report_markdown(results, traces, replays, settings, args.seed))
    (args.output / "timeline.svg").write_text(timeline_svg(results, traces, settings))
    for controller in CONTROLLERS:
        (args.output / f"errors_{controller}.svg").write_text(error_svg(traces[controller], settings.attachment_tolerance_cm))
    metadata = dict(settings=asdict(settings), seed=args.seed, controllers=list(CONTROLLERS),
                    model_version=MODEL_VERSION, source_sha256={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                                   for name in ("model.py", "experiment.py", "diagnostics.py", "tracking.py", "measurements.py")})
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Diagnostic report: {(args.output / 'report.html').resolve()}")


if __name__ == "__main__":
    main()
