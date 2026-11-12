"""Paper-facing paired comparisons and mechanism/sensitivity ablations.

python3 -m spider_web_mulder.validation --output mulder_results/paper_validation
"""
import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import html
import json
from pathlib import Path
import platform
import statistics
import time

import numpy as np

from .experiment import CONTROLLERS, MODEL_VERSION, run_trial
from .measurements import FEATURES
from .model import load_settings
from .reference import REFERENCE_COLUMNS, calibrate_rigid, load_reference, reference_effects


METRICS = ("elapsed_s", "travel_cm", "sampled_travel_10s_cm",
           "radials_time_pct", "auxiliary_time_pct", "capture_time_pct",
           "radials_travel_pct", "auxiliary_travel_pct", "capture_travel_pct", *FEATURES,
           "sampled_radials_travel_pct", "sampled_auxiliary_travel_pct", "sampled_capture_travel_pct",
           "repairs", "planning_calls", "method_calls", "planning_wall_s", "prediction_wall_s")


def interval(values, rng, replicates):
    data = np.array(values, dtype=float)
    if not len(data):
        return None
    samples = rng.choice(data, size=(replicates, len(data)), replace=True).mean(axis=1)
    return [float(x) for x in np.quantile(samples, [0.025, 0.975])]


def wilson(successes, n):
    z = 1.959963984540054
    p = successes/n
    denominator = 1+z*z/n
    center = (p+z*z/(2*n))/denominator
    radius = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return [max(0., float(center-radius)), min(1., float(center+radius))]


def paired_analysis(rows, replicates=2000):
    rng = np.random.default_rng(20261020)
    controls = {(r["profile"], r["controller"], r["seed"]):r for r in rows if r["amplitude_cm"] == 0}
    groups = {}
    for r in rows:
        if r["amplitude_cm"]:
            key = (r["profile"], r["controller"], r["amplitude_cm"], r["frequency_hz"])
            groups.setdefault(key, []).append(r)
    result = []
    for (profile, controller, amplitude, frequency), group in groups.items():
        base = dict(profile=profile, controller=controller, amplitude_cm=amplitude, frequency_hz=frequency,
                    trials=len(group), successes=sum(r["success"] for r in group))
        base["success_rate"] = base["successes"]/base["trials"]
        base["success_ci95"] = wilson(base["successes"], base["trials"])
        differences = [int(r["success"])-int(controls[(profile,controller,r["seed"])]["success"]) for r in group]
        result.append(dict(base, metric="completion", paired_n=len(group), moving_mean=base["success_rate"],
                           control_mean=statistics.mean(controls[(profile,controller,r["seed"])]["success"] for r in group),
                           mean_difference=statistics.mean(differences), ci95=interval(differences,rng,replicates),
                           percent_difference=None, percent_ci95=None))
        for metric in METRICS:
            pairs = [(r, controls[(profile,controller,r["seed"])]) for r in group
                     if r["success"] and controls[(profile,controller,r["seed"])]["success"] and
                     r.get(metric) is not None and controls[(profile,controller,r["seed"])].get(metric) is not None]
            differences = [r[metric]-c[metric] for r,c in pairs]
            percentages = [100*(r[metric]-c[metric])/c[metric] for r,c in pairs if abs(c[metric]) > 1e-8]
            result.append(dict(base, metric=metric, paired_n=len(pairs),
                               moving_mean=statistics.mean(r[metric] for r,c in pairs) if pairs else None,
                               control_mean=statistics.mean(c[metric] for r,c in pairs) if pairs else None,
                               mean_difference=statistics.mean(differences) if pairs else None,
                               ci95=interval(differences,rng,replicates),
                               percent_difference=statistics.mean(percentages) if percentages else None,
                               percent_ci95=interval(percentages,rng,replicates)))
    return result


def profiles(settings, suite, n):
    # A=0 is executed once per seed/profile/controller, not duplicated by frequency.
    primary = [(0,0)] + [(a,f) for a in (5,10) for f in (0.049,0.05)]
    specs = [dict(name="endpoint", settings=replace(settings,execution_mode="endpoint",method_policy="direct",sensor_tau_s=0),
                  controllers=CONTROLLERS, conditions=primary, seeds=n, hierarchy="htn"),
             dict(name="tracking", settings=replace(settings,execution_mode="tracking",method_policy="direct",sensor_tau_s=0),
                  controllers=CONTROLLERS, conditions=primary, seeds=n, hierarchy="htn")]
    if suite == "full":
        sensitivity = [
            ("tracking_dt_half", dict(integration_step_s=settings.integration_step_s/2), "htn"),
            ("tracking_slow", dict(speed_cm_s=0.5), "htn"),
            ("tracking_fast", dict(speed_cm_s=2.0), "htn"),
            ("sensor_lag_1s", dict(sensor_tau_s=1.0), "htn"),
            ("sensor_lag_5s", dict(sensor_tau_s=5.0), "htn"),
            ("tracking_tight", dict(attachment_tolerance_cm=0.1), "htn"),
            ("repair_delay_1s", dict(repair_delay_s=1.0), "htn"),
            ("flat_tracking", {}, "flat"),
            ("phase_wait", dict(method_policy="phase_wait", speed_cm_s=0.5), "htn"),
            ("flat_slow", dict(speed_cm_s=0.5), "flat")]
        for name, overrides, hierarchy in sensitivity:
            changes = dict(execution_mode="tracking", method_policy="direct", sensor_tau_s=0)
            changes.update(overrides)
            specs.append(dict(name=name, settings=replace(settings,**changes), controllers=("local","predictive"),
                              conditions=[(0,0),(10,0.05)], seeds=min(n,12), hierarchy=hierarchy))
    return specs


def save_csv(path, rows):
    with path.open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})


def plot_results(comparisons, output, rows):
    # Standard plotting tools, standalone PNG and SVG. No browser or CDN needed.
    import os
    import tempfile
    os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"mulder-matplotlib"))
    cache = Path(tempfile.gettempdir())/"mulder-font-cache"
    cache.mkdir(exist_ok=True)
    os.environ.setdefault("XDG_CACHE_HOME",str(cache))
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    figure = Figure(figsize=(12,4),layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(1,2)
    for axis,profile in zip(axes,("endpoint","tracking")):
        data = np.zeros((len(CONTROLLERS),3))
        for i,c in enumerate(CONTROLLERS):
            stationary = [r["success"] for r in rows if r["profile"]==profile and r["controller"]==c and r["amplitude_cm"]==0]
            data[i,0] = statistics.mean(stationary)
            for j,a in enumerate((5,10),1):
                matches = [r for r in comparisons if r["profile"]==profile and r["controller"]==c and
                           r["amplitude_cm"]==a and r["frequency_hz"]==0.05 and r["metric"]=="completion"]
                data[i,j] = matches[0]["success_rate"] if matches else np.nan
        axis.imshow(data,vmin=0,vmax=1,cmap="YlGn",aspect="auto")
        axis.set_xticks(range(3),["stationary","5 cm","10 cm"])
        axis.set_yticks(range(len(CONTROLLERS)),CONTROLLERS)
        axis.set_title(f"{profile}: completion at 0.05 Hz")
        for i in range(len(CONTROLLERS)):
            for j in range(3):
                axis.text(j,i,f"{data[i,j]:.0%}",ha="center",va="center")
    for extension in ("png","svg"):
        figure.savefig(output/f"completion.{extension}",dpi=160)
    figure = Figure(figsize=(11,4),layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(1,2)
    for axis,metric,title in zip(axes,("elapsed_s","sampled_travel_10s_cm"),("Construction duration","Travel at 10 s camera cadence")):
        for i,c in enumerate(("local","full","predictive")):
            row = next(r for r in comparisons if r["profile"]=="tracking" and r["controller"]==c and
                       r["amplitude_cm"]==10 and r["frequency_hz"]==0.05 and r["metric"]==metric)
            if row["percent_difference"] is not None:
                mean = row["percent_difference"]
                lower,upper = row["percent_ci95"]
                axis.errorbar(i,mean,yerr=[[max(0,mean-lower)],[max(0,upper-mean)]],fmt="o",capsize=5)
        axis.axhline(0,color="grey",linewidth=1)
        axis.set_xticks(range(3),["local","full","predictive"])
        axis.set_ylabel("Moving minus stationary (%)")
        axis.set_title(title)
    for extension in ("png","svg"):
        figure.savefig(output/f"paired_effects.{extension}",dpi=160)


def write_report(comparisons, rows, output, provenance, calibration):
    lines = ["# Mulder paper comparison — model version 3", "",
             "This is a computational comparison with the published pattern, not independent verification of the biological experiment.",
             "Raw biological observations are not bundled with the paper. No data were fabricated or digitized approximately from bar charts.", "",
             f"**Trials run: {len(rows)}.** Paired bootstrap intervals use initial motion phases as simulation units, not biological spiders.",
             "Continuous costs below use only pairs in which both conditions complete. Failures remain in completion rates.", "",
             "![Completion](completion.png)", "", "![Paired effects](paired_effects.png)", "",
             "## Completion at the published frequency", "",
             "Stationary controls are executed once per controller/profile/seed and reused for frequency comparisons.", "",
             "| Executor | Controller | Amplitude cm | Completed | 95% Wilson interval |",
             "|---|---|---:|---:|---|"]
    for r in comparisons:
        if r["profile"] in ("endpoint","tracking") and r["frequency_hz"]==0.05 and r["metric"]=="completion":
            low,high = r["success_ci95"]
            lines.append(f'| {r["profile"]} | {r["controller"]} | {r["amplitude_cm"]:g} | {r["successes"]}/{r["trials"]} | {low:.3f}–{high:.3f} |')
    lines += ["", "## Paired moving–stationary differences", "",
              "Tracking execution, 10 cm amplitude, 0.05 Hz. Relative mean differences and paired 95% bootstrap intervals.",
              "No threshold for biological equivalence is assumed. Small or non-significant differences do not establish biological equivalence.", "",
              "| Controller | Measurement | Successful pairs | Mean change % | 95% interval % |",
              "|---|---|---:|---:|---|"]
    for r in comparisons:
        if r["profile"]=="tracking" and r["controller"] in ("local","full","predictive") and r["amplitude_cm"]==10 and r["frequency_hz"]==0.05 and r["metric"] in ("elapsed_s","travel_cm","sampled_travel_10s_cm","radials_time_pct","auxiliary_time_pct","capture_time_pct"):
            mean,ci = r["percent_difference"],r["percent_ci95"]
            lines.append(f'| {r["controller"]} | {r["metric"]} | {r["paired_n"]} | {mean:.3f} | {ci[0]:.3f}–{ci[1]:.3f} |' if mean is not None else f'| {r["controller"]} | {r["metric"]} | 0 | unavailable | unavailable |')
    lines += ["", "## Sensitivity and hierarchy results", "",
              "10 cm, 0.05 Hz. Differences are against each profile's own stationary control; speed profiles must not be compared as if they had equal absolute cost.", "",
              "| Profile | Controller | Moving completions | Duration change % |",
              "|---|---|---:|---:|"]
    for r in comparisons:
        if r["profile"] not in ("endpoint","tracking") and r["metric"]=="elapsed_s":
            percent = f'{r["percent_difference"]:.3f}' if r["percent_difference"] is not None else "no completed pairs"
            lines.append(f'| {r["profile"]} | {r["controller"]} | {r["successes"]}/{r["trials"]} | {percent} |')
    local = next(r for r in comparisons if r["profile"]=="tracking" and r["controller"]=="local" and r["amplitude_cm"]==10 and r["frequency_hz"]==0.05 and r["metric"]=="completion")
    lines += ["", f'The ideal continuous local controller completes {local["successes"]}/{local["trials"]} primary moving trials. '
              'Its performance must be read alongside lag sensitivity and prescribed-geometry assumptions.', ""]
    for ablation,base in (("flat_tracking","tracking"),("phase_wait","tracking_slow")):
        alternatives = [r for r in rows if r["profile"]==ablation and r["controller"]=="local" and r["amplitude_cm"]==10 and r["frequency_hz"]==0.05]
        baseline = {r["seed"]:r for r in rows if r["profile"]==base and r["controller"]=="local" and r["amplitude_cm"]==10 and r["frequency_hz"]==0.05}
        differences = [r["elapsed_s"]-baseline[r["seed"]]["elapsed_s"] for r in alternatives if r["success"] and r["seed"] in baseline and baseline[r["seed"]]["success"]]
        if differences:
            lines.append(f'- {ablation} versus {base}, matched local-controller seeds: mean duration difference **{statistics.mean(differences):.6f} s** across {len(differences)} completed pairs.')
    lines += ["", "## Measurement and calibration status", "",
              "- Frame dimensions, approximate forcing frequency, and the 10 s tracking cadence come from the paper. Peak amplitude is explicitly swept at 5 and 10 cm to cover the ambiguous movement wording.",
              "- Areas are polygonal-envelope estimates from accepted chords. Capture area subtracts an estimated hub envelope. These are not ImageJ pixel measurements.",
              "- Cardinal capture counts, radial count, mesh width/count formula, and eccentricity formula follow Table 1. Failed webs have missing final-geometry values.",
              "- Frame time remains a separate construction category. Phase percentages use total construction time including frame activity; do not silently equate frame work with the paper's radial phase.",
              "- Continuous frame-corrected travel and camera-sampled travel are both reported. The latter is comparable in observation cadence, not guaranteed identical to biological tracking.",
              "- Speed, contact dwell, sensor lag, action budget, geometry and route access remain model assumptions unless calibrated against supplied rigid observations.",
              f'- Calibration status: **{calibration["status"]}**. See calibration.json and provenance.json.', "",
              "## What the mechanism comparisons establish", "",
              "- The continuous executor explicitly assumes no-slip passive advection on the supporting silk and bounds locomotion relative to its instantaneous geometry. Contact dwell is separate from movement.",
              "- A local controller knows the instantaneous attachment identity and geometry; zero sensor lag is an idealization. Independent sensor-lag, speed, time-step, tolerance and delay profiles test sensitivity to that idealization.",
              "- The flat_tracking and flat_slow ablations execute the same segment sequence without compound-task decomposition. Similar outcomes mean hierarchy is not demonstrated to be necessary for tolerance in this benchmark.",
              "- phase_wait adds a genuine HTN alternative: immediate construction or a bounded pause selected using nominal deformation-dependent cost. Outcomes and delay costs are recorded; the method is not assumed to improve construction.",
              "- Under perfect material-coordinate tracking, identical prescribed endpoints make true frame-relative distance and geometry invariant by construction. This is a sanity check, not independent validation of the paper's geometric finding.",
              "- More planning is not presumed beneficial: full replanning retains its configured delay and computational cost. Tracking-aware prediction uses deadline slack and estimated sensor lag; endpoint drift margins are used only for the legacy executor.",
              "- Silk stress, viscoelasticity, graph-constrained traversal, anchor loss, behavioural willingness, and learned geometry are not identified by this experiment. The simulator's 0.1 Hz extrapolations cannot explain the biological refusal to build.", "",
              "## Files", "",
              "- trials.csv / trials.json: all successes and failures, costs, measured geometry and sampled travel.",
              "- comparisons.csv / comparisons.json: paired differences, intervals, sample counts and completion uncertainty.",
              "- profiles.json: complete settings and seeds for every mechanism and sensitivity profile.",
              "- calibration.json / provenance.json: fitted versus assumed quantities and exact source hashes.",
              "- biological_reference_template.csv: optional raw-observation import format. Use --reference-csv to fit rigid controls only and retain moving observations for comparison.", ""]
    text = "\n".join(lines)
    (output/"report.md").write_text(text)
    # Plain report remains readable without JavaScript or external services.
    body = html.escape(text)
    (output/"report.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Mulder validation</title><style>body{font:15px system-ui;max-width:1200px;margin:30px auto;padding:20px}img{max-width:100%}pre{white-space:pre-wrap;line-height:1.6}</style><h1>Mulder paper comparison</h1><img src="completion.png" alt="Completion by executor and controller"><img src="paired_effects.png" alt="Paired duration and sampled travel differences"><pre>'+body+'</pre></html>')


def compare_biological_effects(comparisons, biological):
    mapping = {"travel_cm":"sampled_travel_10s_cm", "radials_travel_pct":"sampled_radials_travel_pct",
               "auxiliary_travel_pct":"sampled_auxiliary_travel_pct", "capture_travel_pct":"sampled_capture_travel_pct"}
    result = []
    for metric,observation in biological.items():
        for row in comparisons:
            if row["profile"]=="tracking" and row["amplitude_cm"]==10 and row["frequency_hz"]==0.05 and row["metric"]==mapping.get(metric,metric):
                result.append(dict(metric=metric,controller=row["controller"],
                                   observed=observation,simulated=dict(paired_phases=row["paired_n"],
                                   mean_paired_difference=row["mean_difference"],ci95_difference=row["ci95"]),
                                   qualification="Biological individuals and simulation phases are distinct uncertainty units; no pooled significance test."))
    return result


def analyse_existing(source, output, replicates):
    """Rerender saved trials without rerunning or altering the simulation."""
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Choose an empty analysis output directory")
    rows = json.loads((source/"trials.json").read_text())
    provenance = json.loads((source/"provenance.json").read_text())
    calibration = json.loads((source/"calibration.json").read_text())
    comparisons = paired_analysis(rows,replicates)
    output.mkdir(parents=True,exist_ok=True)
    for name,data in (("trials",rows),("comparisons",comparisons)):
        save_csv(output/f"{name}.csv",data)
        (output/f"{name}.json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
    for name in ("profiles.json","calibration.json","biological_reference_template.csv","biological_effects.json"):
        if (source/name).exists():
            (output/name).write_bytes((source/name).read_bytes())
    provenance["reanalysis"] = dict(input_trials_sha256=hashlib.sha256((source/"trials.json").read_bytes()).hexdigest(),
                                   analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                   bootstrap_resamples=replicates,simulation_rerun=False)
    (output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    if (output/"biological_effects.json").exists():
        bio = json.loads((output/"biological_effects.json").read_text())
        (output/"biological_comparison.json").write_text(json.dumps(compare_biological_effects(comparisons,bio),indent=2)+"\n")
    plot_results(comparisons,output,rows)
    write_report(comparisons,rows,output,provenance,calibration)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path)
    parser.add_argument("--seeds",type=int,default=30)
    parser.add_argument("--bootstrap",type=int,default=2000)
    parser.add_argument("--suite",choices=("core","full"),default="full")
    parser.add_argument("--reference-csv",type=Path)
    parser.add_argument("--analyse-existing",type=Path)
    parser.add_argument("--output",type=Path,default=Path("mulder_results/paper_validation"))
    args = parser.parse_args(argv)
    if args.seeds < 2 or args.bootstrap < 100:
        parser.error("Use at least two seeds and 100 bootstrap resamples")
    if args.analyse_existing:
        if args.reference_csv:
            parser.error("Calibration requires a fresh simulation run")
        analyse_existing(args.analyse_existing,args.output,args.bootstrap)
        print(f'Report: {(args.output/"report.html").resolve()}')
        return
    settings,_ = load_settings(args.config)
    calibration = dict(status="not empirically calibrated: raw observations unavailable",fitted_parameters={})
    biological = None
    if args.reference_csv:
        reference = load_reference(args.reference_csv)
        settings,fit = calibrate_rigid(settings,reference)
        calibration = dict(status="fitted to supplied rigid observations; moving held out",**fit)
        biological = reference_effects(reference)
    specs = profiles(settings,args.suite,args.seeds)
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error("Choose an empty output directory")
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/"biological_reference_template.csv").open("w",newline="") as stream:
        csv.writer(stream).writerow(REFERENCE_COLUMNS)
    rows = []
    for spec in specs:
        for amplitude,frequency in spec["conditions"]:
            case = replace(spec["settings"],amplitude_cm=amplitude,frequency_hz=frequency)
            for seed in range(spec["seeds"]):
                for controller in spec["controllers"]:
                    started = time.perf_counter()
                    row,_ = run_trial(case,controller,seed,record_path=True,hierarchy=spec["hierarchy"])
                    rows.append(dict(profile=spec["name"],trial_wall_s=time.perf_counter()-started,**row))
            print(f'{spec["name"]}: A={amplitude:g}, f={frequency:g}, {spec["seeds"]*len(spec["controllers"])} trials complete',flush=True)
    comparisons = paired_analysis(rows,args.bootstrap)
    for name,data in (("trials",rows),("comparisons",comparisons)):
        save_csv(args.output/f"{name}.csv",data)
        (args.output/f"{name}.json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
    (args.output/"profiles.json").write_text(json.dumps([{**s,"settings":asdict(s["settings"])} for s in specs],indent=2)+"\n")
    (args.output/"calibration.json").write_text(json.dumps(calibration,indent=2)+"\n")
    if biological is not None:
        (args.output/"biological_effects.json").write_text(json.dumps(biological,indent=2)+"\n")
        (args.output/"biological_comparison.json").write_text(json.dumps(compare_biological_effects(comparisons,biological),indent=2)+"\n")
    reference_path = Path(__file__).with_name("paper_reference.json")
    provenance = dict(model_version=MODEL_VERSION,paper=json.loads(reference_path.read_text()),
                      bootstrap_resamples=args.bootstrap,bootstrap_seed=20261020,
                      python=platform.python_version(),numpy=np.__version__,
                      uncertainty_unit="initial motion phase; not biological individual",
                      source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))})
    if args.reference_csv:
        provenance["reference_sha256"] = hashlib.sha256(args.reference_csv.read_bytes()).hexdigest()
    (args.output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    plot_results(comparisons,args.output,rows)
    write_report(comparisons,rows,args.output,provenance,calibration)
    print(f'Report: {(args.output/"report.html").resolve()}')


if __name__ == "__main__":
    main()
