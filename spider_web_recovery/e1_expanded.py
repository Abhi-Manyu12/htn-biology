"""E1 expanded scaling/resource/movement study; see E1_EXPANDED_PROTOCOL.md."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import statistics
import sys

import numpy as np

from spider_web_mulder.validation import interval, save_csv, wilson
from . import e1_benchmark as original
from .domain import Config
from .e1 import CONTROLLERS, SCENARIOS, run_trial

SEEDS = tuple(range(20, 30))
ANALYSIS_SEED = 20261113
REPLICATES = 2000
SUITES = ("scaling", "resource", "movement")
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT/"docs/research/E1_EXPANDED_PROTOCOL.md"


def designs(suites=SUITES):
    """Explicit configurations avoid accidentally grouping different stock/frequency."""
    cases = []
    def add(suite, cfg, scenarios, margin=None):
        cases.append(dict(suite=suite, config=cfg, scenarios=tuple(scenarios), margin=margin))
    if "scaling" in suites:
        for n, a in itertools.product((4, 8, 16, 24, 32), (0, 10)):
            add("scaling", Config(sectors=n, depth=0, silk_cm=1000, amplitude_cm=a), SCENARIOS)
    if "resource" in suites:
        for n, margin in itertools.product((8, 16, 32), (-1, 0, 20, 60)):
            add("resource", Config(sectors=n, depth=0, silk_cm=19*n+margin, amplitude_cm=10),
                ("intact", "damage_single", "damage_multi", "transfer_partial"), margin)
    if "movement" in suites:
        for n, a, freq in itertools.product((8, 24), (20, 30), (.05, .10)):
            add("movement", Config(sectors=n, depth=0, silk_cm=1000, amplitude_cm=a, frequency_hz=freq),
                ("intact", "damage_single", "transfer_partial"))
    return cases


def group_key(row):
    return row["config_id"], row["scenario"], row["seed"]


def check_exposure(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[group_key(row)].append(row)
    result = dict(matched_cases=len(groups), identical_exposed_cases=0, all_unexposed_cases=0)
    for key, group in groups.items():
        if len(group) != 4 or {r["controller"] for r in group} != set(CONTROLLERS):
            raise ValueError(f"Incomplete or duplicated controller case: {key}")
        if len({str(r["config"]) for r in group}) != 1:
            raise ValueError(f"Mismatched configurations: {key}")
        if len({r["event_fired"] for r in group}) != 1:
            raise ValueError(f"Unequal exposure: {key}")
        if group[0]["event_fired"]:
            if len({(r["pre_state_sha256"], r["post_state_sha256"]) for r in group}) != 1:
                raise ValueError(f"Mismatched checkpoint state: {key}")
            result["identical_exposed_cases"] += 1
        else:
            result["all_unexposed_cases"] += 1
    return result


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["config_id"], r["scenario"], r["controller"])].append(r)
    out = []
    for (_, scenario, controller), group in sorted(groups.items()):
        first = group[0]
        item = dict(suite=first["suite"], config_id=first["config_id"],
                    scenario=scenario, controller=controller, margin_cm=first["margin_cm"],
                    **first["config"], trials=len(group),
                    successes=sum(r["success"] for r in group),
                    events_fired=sum(r["event_fired"] for r in group))
        item["success_ci95"] = wilson(item["successes"], item["trials"])
        for metric in ("policy_wall_s", "recovery_policy_wall_s", "method_calls", "restorations",
                       "stale_preconditions", "unnecessary_repeats", "elapsed_s", "travel_cm", "silk_used_cm"):
            candidates = [r for r in group if metric not in ("elapsed_s", "travel_cm", "silk_used_cm") or r["success"]]
            values = [r[metric] for r in candidates if r[metric] is not None]
            item["mean_"+metric] = statistics.mean(values) if values else None
            item["n_"+metric] = len(values)
        out.append(item)
    return out


def paired(rows):
    check_exposure(rows)
    groups = defaultdict(dict)
    for r in rows:
        groups[(r["config_id"], r["scenario"])][(r["seed"], r["controller"])] = r
    rng = np.random.default_rng(ANALYSIS_SEED)
    out = []
    physical = ("elapsed_s", "travel_cm", "silk_used_cm")
    for (_, scenario), group in sorted(groups.items()):
        seeds = sorted({k[0] for k in group})
        for first, second in original.CONTRASTS:
            pairs = [(group[s, first], group[s, second]) for s in seeds]
            metrics = ("success", "policy_wall_s", "recovery_policy_wall_s", *physical)
            if second == "fresh_htn":
                metrics += ("method_calls",)
            for metric in metrics:
                eligible = [(a, b) for a, b in pairs
                            if (metric not in physical or (a["success"] and b["success"]))
                            and a[metric] is not None and b[metric] is not None]
                values = [float(a[metric])-float(b[metric]) for a, b in eligible]
                r = pairs[0][0]
                out.append(dict(suite=r["suite"], config_id=r["config_id"], scenario=scenario,
                                margin_cm=r["margin_cm"], **r["config"],
                                contrast=f"{first}_minus_{second}", metric=metric,
                                attempted_pairs=len(pairs), paired_n=len(values),
                                conditioning=("both succeed" if metric in physical else
                                              "both exposed" if metric == "recovery_policy_wall_s" else "all pairs"),
                                mean_difference=statistics.mean(values) if values else None,
                                ci95=interval(values, rng, REPLICATES)))
    return out


def plots(rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"history":"#777777", "state_rules":"#0072B2", "fresh_htn":"#D55E00", "retained_htn":"#009E73"}
    markers = {"history":"x", "state_rules":"o", "fresh_htn":"s", "retained_htn":"^"}
    def subset(**filters):
        return [r for r in rows if all((r["config"].get(k) if k in r["config"] else r.get(k)) == v
                                        for k, v in filters.items())]
    def save(fig, name):
        for ext in ("png", "svg"):
            fig.savefig(output/f"{name}.{ext}", dpi=200)
        plt.close(fig)
    if any(r["suite"] == "scaling" for r in rows):
        sizes = (4, 8, 16, 24, 32)
        fig, ax = plt.subplots(figsize=(7.2, 4.4), layout="constrained")
        for controller in CONTROLLERS:
            means = [statistics.mean(r["policy_wall_s"] for r in subset(suite="scaling", scenario="damage_multi",
                     controller=controller, sectors=n, amplitude_cm=10))*1000 for n in sizes]
            ax.plot(sizes, means, marker=markers[controller], color=colors[controller], label=controller.replace("_", " "))
        ax.set(xlabel="Web sectors", ylabel="Mean decision wall time (ms)", xticks=sizes)
        ax.legend(frameon=False, ncol=2)
        save(fig, "scaling_decision_time")

        fig, axes = plt.subplots(1, 2, figsize=(9, 4), layout="constrained")
        for ax, metric, ylabel in zip(axes, ("elapsed_s", "silk_used_cm"),
                                      ("Additional simulated time (s)", "Additional actor silk (cm)")):
            for scenario, marker in (("damage_single", "o"), ("damage_multi", "s"), ("transfer_partial", "^")):
                values = []
                for n in sizes:
                    changed = {r["seed"]:r for r in subset(suite="scaling", scenario=scenario,
                               controller="state_rules", sectors=n, amplitude_cm=10)}
                    intact = {r["seed"]:r for r in subset(suite="scaling", scenario="intact",
                              controller="state_rules", sectors=n, amplitude_cm=10)}
                    differences = [changed[s][metric]-intact[s][metric] for s in changed
                                   if changed[s]["success"] and intact[s]["success"]]
                    values.append(statistics.mean(differences) if differences else float("nan"))
                ax.plot(sizes, values, marker=marker, label=scenario.replace("damage_", "").replace("_", " "))
            ax.set(xlabel="Web sectors", ylabel=ylabel, xticks=sizes)
        axes[0].legend(frameon=False)
        save(fig, "scaling_repair_cost")
    if any(r["suite"] == "resource" for r in rows):
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), sharey=True, layout="constrained")
        margins = (-1, 0, 20, 60)
        for ax, n in zip(axes, (8, 16, 32)):
            for controller in CONTROLLERS:
                fractions = []
                for m in margins:
                    group = subset(suite="resource", scenario="damage_multi", controller=controller, sectors=n, margin_cm=m)
                    fractions.append(sum(r["success"] for r in group)/len(group))
                ax.plot(margins, fractions, marker=markers[controller], color=colors[controller],
                        label=controller.replace("_", " "), alpha=.8)
            ax.set(title=f"{n} sectors", xlabel="Stock above intact requirement (cm)", xticks=margins, ylim=(-.05, 1.1))
        axes[0].set_ylabel("Valid completion fraction")
        axes[1].legend(frameon=False, fontsize=8, loc="lower right")
        save(fig, "resource_completion")
    if any(r["suite"] == "movement" for r in rows):
        fig, axes = plt.subplots(1, 2, figsize=(9, 4), layout="constrained")
        for n, color in ((8, "#0072B2"), (24, "#D55E00")):
            for freq, style in ((.05, "-"), (.1, "--")):
                amplitudes = (0, 10, 20, 30) if freq == .05 and any(r["suite"] == "scaling" for r in rows) else (20, 30)
                times, fractions = [], []
                for amp in amplitudes:
                    suite = "scaling" if amp in (0, 10) else "movement"
                    group = subset(suite=suite, scenario="damage_single", controller="state_rules", sectors=n,
                                   amplitude_cm=amp, frequency_hz=freq)
                    successful = [r["elapsed_s"] for r in group if r["success"]]
                    times.append(statistics.mean(successful) if successful else float("nan"))
                    fractions.append(len(successful)/len(group))
                label = f"{n} sectors, {freq:g} Hz"
                axes[0].plot(amplitudes, times, marker="o", linestyle=style, color=color, label=label)
                axes[1].plot(amplitudes, fractions, marker="o", linestyle=style, color=color, label=label)
        axes[0].set(xlabel="Support amplitude (cm)", ylabel="Mean simulated time (s)\n(successful trials only)")
        axes[1].set(xlabel="Support amplitude (cm)", ylabel="Valid completion fraction", ylim=(-.05, 1.1))
        axes[0].legend(frameon=False, fontsize=8)
        save(fig, "movement_stress")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suite", nargs="+", choices=SUITES, default=list(SUITES))
    parser.add_argument("--seeds", type=int, default=len(SEEDS), help="first N of fixed seeds 20–29")
    args = parser.parse_args(argv)
    if not 1 <= args.seeds <= len(SEEDS) or len(set(args.suite)) != len(args.suite):
        parser.error("Use 1–10 seeds and unique suite names")
    if args.output.exists():
        parser.error("Choose a new output directory")
    cases = designs(args.suite)
    seeds = SEEDS[:args.seeds]
    command = [sys.executable, "-m", "spider_web_recovery.e1_expanded",
               *(sys.argv[1:] if argv is None else list(map(str, argv)))]
    manifest = original.provenance([case["config"] for case in cases], args.seeds, list(SCENARIOS), command)
    manifest.update(expanded_protocol_sha256=original.digest(PROTOCOL),
                    seeds=list(seeds), analysis_seed=ANALYSIS_SEED, bootstrap_replicates=REPLICATES,
                    suites=args.suite, design=[dict(suite=c["suite"], config=asdict(c["config"]),
                                                    margin=c["margin"], scenarios=c["scenarios"]) for c in cases])
    args.output.mkdir(parents=True, exist_ok=False)
    original.dump(args.output/"provenance.json", manifest)
    traces = args.output/"traces"
    traces.mkdir()
    rows = []
    with (args.output/"trials.jsonl").open("x") as journal:
        for case_id, case in enumerate(cases):
            for scenario in case["scenarios"]:
                for seed in seeds:
                    offset = seed % len(CONTROLLERS)
                    for controller in CONTROLLERS[offset:]+CONTROLLERS[:offset]:
                        row, trace, _ = run_trial(case["config"], controller, scenario, seed)
                        row.update(suite=case["suite"], config_id=case_id, margin_cm=case["margin"])
                        rows.append(row)
                        journal.write(json.dumps(row, allow_nan=False)+"\n")
                        journal.flush()
                        if seed == seeds[0]:
                            original.dump(traces/f"case{case_id}_{scenario}_{controller}.json", trace)
                print(f"{case['suite']} config {case_id+1}/{len(cases)} {scenario} complete", flush=True)
    exposure = check_exposure(rows)
    original.dump(args.output/"exposure.json", exposure)
    for name, data in (("trials", rows), ("summary", summarize(rows)), ("paired", paired(rows))):
        original.dump(args.output/f"{name}.json", data)
        save_csv(args.output/f"{name}.csv", data)
    plots(rows, args.output)
    for name, sha in manifest["source_sha256"].items():
        if original.digest(ROOT/name) != sha:
            raise RuntimeError(f"Source changed during sweep: {name}")
    if original.digest(PROTOCOL) != manifest["expanded_protocol_sha256"]:
        raise RuntimeError("Expanded protocol changed during sweep")
    original.dump(args.output/"artifact_sha256.json", {
        p.relative_to(args.output).as_posix(): original.digest(p)
        for p in sorted(args.output.rglob("*")) if p.is_file()})
    print(f"Completed {len(rows)} trials: {args.output.resolve()}", flush=True)


if __name__ == "__main__":
    main()
