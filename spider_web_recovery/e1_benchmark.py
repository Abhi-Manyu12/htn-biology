"""Reproducible E1 observed-structure sweep (defaults: frozen 1,920-trial design)."""
import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys

import gtpyhop
import networkx
import numpy as np

from spider_web_mulder.model import Settings
from spider_web_mulder.validation import interval, save_csv, wilson
from .backends import VENDOR
from .benchmark import tree_svg
from .domain import Config
from .e1 import CONTROLLERS, SCENARIOS, VERSION, run_trial

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_SEED = 20261112
BOOTSTRAP_REPLICATES = 2000
CONTRASTS = (("fresh_htn", "state_rules"), ("retained_htn", "state_rules"),
             ("retained_htn", "fresh_htn"))
PHYSICAL = ("elapsed_s", "travel_cm", "silk_used_cm")


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stratum(row):
    c = row["config"]
    return row["scenario"], c["sectors"], c["amplitude_cm"]


def audit_exposure(rows):
    """Require four unique matched controllers; compare reached checkpoint states."""
    groups = defaultdict(list)
    for row in rows:
        groups[(*stratum(row), row["seed"])].append(row)
    exposed = unexposed = 0
    for key, group in groups.items():
        if len(group) != 4 or {r["controller"] for r in group} != set(CONTROLLERS):
            raise ValueError(f"Incomplete or duplicate matched case: {key}")
        if len({r["event_fired"] for r in group}) != 1:
            raise ValueError(f"Unequal intervention exposure: {key}")
        if group[0]["event_fired"]:
            if len({(r["pre_state_sha256"], r["post_state_sha256"]) for r in group}) != 1:
                raise ValueError(f"Mismatched intervention states: {key}")
            if not group[0]["pre_state_sha256"] or not group[0]["post_state_sha256"]:
                raise ValueError(f"Missing checkpoint hashes: {key}")
            exposed += 1
        else:
            unexposed += 1
    return dict(matched_cases=len(groups), identical_exposed_cases=exposed,
                all_controllers_unexposed_cases=unexposed, mismatches=0)


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(*stratum(row), row["controller"])].append(row)
    output = []
    for (scenario, sectors, amplitude, controller), group in sorted(groups.items()):
        successes = sum(r["success"] for r in group)
        summary = dict(scenario=scenario, sectors=sectors, amplitude_cm=amplitude,
                       controller=controller, trials=len(group), successes=successes,
                       success_ci95=wilson(successes, len(group)),
                       events_fired=sum(r["event_fired"] for r in group))
        for metric in ("unnecessary_repeats", "restorations", "stale_preconditions",
                       "policy_wall_s", "recovery_policy_wall_s", "method_calls"):
            values = [r[metric] for r in group if r[metric] is not None]
            summary["mean_"+metric] = statistics.mean(values) if values else None
        output.append(summary)
    return output


def paired(rows):
    audit_exposure(rows)
    groups = defaultdict(dict)
    for row in rows:
        groups[stratum(row)][(row["seed"], row["controller"])] = row
    rng = np.random.default_rng(ANALYSIS_SEED)
    output = []
    for (scenario, sectors, amplitude), group in sorted(groups.items()):
        seeds = sorted({seed for seed, _ in group})
        for first, second in CONTRASTS:
            pairs = [(group[seed, first], group[seed, second]) for seed in seeds]
            metrics = ("success", "policy_wall_s", "recovery_policy_wall_s", *PHYSICAL)
            if second == "fresh_htn":
                metrics += ("method_calls",)
            for metric in metrics:
                eligible = [(a, b) for a, b in pairs
                            if (metric not in PHYSICAL or a["success"] and b["success"])
                            and a[metric] is not None and b[metric] is not None]
                values = [float(a[metric])-float(b[metric]) for a, b in eligible]
                condition = ("both constructions complete" if metric in PHYSICAL else
                             "both reached event" if metric == "recovery_policy_wall_s" else
                             "all attempted pairs")
                output.append(dict(scenario=scenario, sectors=sectors, amplitude_cm=amplitude,
                                   contrast=f"{first}_minus_{second}", metric=metric,
                                   attempted_pairs=len(pairs), paired_n=len(values),
                                   conditioning=condition,
                                   mean_difference=statistics.mean(values) if values else None,
                                   ci95=interval(values, rng, BOOTSTRAP_REPLICATES)))
    return output


def provenance(configs, seeds, scenarios, command):
    upstream = json.loads((VENDOR/"UPSTREAM.json").read_text())
    for name, sha in upstream["sha256"].items():
        if digest(VENDOR/name) != sha:
            raise RuntimeError(f"Pinned upstream source changed: {name}")
    sources = [ROOT/"docs/research/E1_PROTOCOL.md", ROOT/"requirements.txt"]
    for package in ("spider_web_recovery", "spider_web_mulder"):
        sources.extend(sorted((ROOT/package).glob("*.py")))
    source_hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    physical_settings = [asdict(Settings(execution_mode="tracking", speed_cm_s=c.speed_cm_s,
                                        amplitude_cm=c.amplitude_cm, frequency_hz=c.frequency_hz,
                                        max_elapsed_s=c.max_elapsed_s)) for c in configs]
    return dict(e1_version=VERSION, recovery_domain_version=1, mulder_executor_version=3,
                started_utc=datetime.now(timezone.utc).isoformat(), command=command,
                git_revision=git("rev-parse", "HEAD"), git_branch=git("branch", "--show-current"),
                git_status=git("status", "--porcelain"),
                python=sys.version, platform=platform.platform(), processor=platform.processor(),
                gtpyhop=gtpyhop.__version__, networkx=networkx.__version__, numpy=np.__version__,
                upstream=upstream, configs=[asdict(c) for c in configs],
                physical_settings=physical_settings, seeds=list(range(seeds)),
                scenarios=scenarios, controllers=CONTROLLERS,
                strategy="same-engine IPyHOP fresh root versus retained actual action leaf; state rules; cached plan",
                controller_order="rotate CONTROLLERS left by seed modulo four",
                tree_snapshots_in_primary=False, analysis_seed=ANALYSIS_SEED,
                bootstrap_replicates=BOOTSTRAP_REPLICATES, source_sha256=source_hashes)


def write_report(rows, exposure, output):
    lines = ["# E1 observed-structure recovery", "",
             f"{len(rows):,} computational trials; {exposure['identical_exposed_cases']} matched cases "
             f"with identical checkpoint states; {exposure['all_controllers_unexposed_cases']} unexposed cases.", "",
             "Counts below pool sizes, amplitudes and seeds. See summary.csv for strata and Wilson intervals.", "",
             "| Scenario | Controller | Complete / attempted | Events | Redundant effects |",
             "|---|---|---:|---:|---:|"]
    for scenario in SCENARIOS:
        for controller in CONTROLLERS:
            group = [r for r in rows if r["scenario"] == scenario and r["controller"] == controller]
            if group:
                lines.append(f"| {scenario} | {controller} | {sum(r['success'] for r in group)}/{len(group)} | "
                             f"{sum(r['event_fired'] for r in group)} | {sum(r['unnecessary_repeats'] for r in group)} |")
    lines += ["", "## Interpretation limits", "",
              "This is a prescribed sector/scaffold computational model, not empirical biological validation. "
              "The cached-plan controller is a weak diagnostic ablation. The state-rule controller shares "
              "the HTN's routing, primary/backup choices, validity and necessary resource-bound knowledge. "
              "A tie against that baseline does not establish an HTN advantage.", "",
              "Transfer uses an aligned donor frame, a common hub and five seconds of external handling. "
              "Donor silk is separate from actor expenditure. Geometry, capture cost and damage are imposed.", "",
              "Decision timings are implementation wall times on one machine, including feasibility checks "
              "and adapter work, with tree snapshots disabled. They are not CPU complexity or biological costs. "
              "Physical paired differences condition on both constructions succeeding; infeasible strata "
              "have zero eligible physical pairs, not zero physical cost. Computational contrasts include "
              "failures. Recovery-only timing conditions on event exposure. Method calls compare only the "
              "two HTN controllers. Bootstrap intervals are pointwise descriptive, with no multiplicity adjustment.", "",
              "## Reproduction and artifacts", "",
              "See provenance.json for exact settings, seeds, engine versions, source hashes and command. "
              "trials.json/csv contain every outcome; summary and paired files retain strata/denominators. "
              "traces/ holds first-seed action ledgers. diagnostics/ contains separately timed retained trees. "
              "artifact_sha256.json hashes all completed artifacts. Existing output directories are refused.", ""]
    (output/"report.md").write_text("\n".join(lines))


def plot_completion(rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    scenarios = [s for s in SCENARIOS if any(r["scenario"] == s for r in rows)]
    x = np.arange(len(scenarios))
    for index, controller in enumerate(CONTROLLERS):
        fractions = []
        for scenario in scenarios:
            group = [r for r in rows if r["scenario"] == scenario and r["controller"] == controller]
            fractions.append(sum(r["success"] for r in group)/len(group))
        ax.bar(x+(index-1.5)*.19, fractions, .19, label=controller.replace("_", " "))
    ax.set(xticks=x, xticklabels=[s.replace("_", "\n") for s in scenarios],
           ylim=(0, 1.18), ylabel="Valid completion fraction", title="E1: observed-structure recovery")
    ax.legend(ncol=4, fontsize=8, loc="upper center")
    fig.savefig(output/"completion.svg")
    fig.savefig(output/"completion.png", dpi=200)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--sectors", type=int, nargs="+", default=[4, 8])
    parser.add_argument("--amplitudes", type=float, nargs="+", default=[0, 10])
    parser.add_argument("--scenarios", choices=SCENARIOS, nargs="+", default=list(SCENARIOS))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("Use at least one seed")
    for values in (args.sectors, args.amplitudes, args.scenarios):
        if len(values) != len(set(values)):
            parser.error("Duplicate sweep values are not allowed")
    try:
        configs = [Config(sectors=n, depth=0, amplitude_cm=a)
                   for n, a in itertools.product(args.sectors, args.amplitudes)]
    except ValueError as error:
        parser.error(str(error))
    if args.output.exists():
        parser.error("Choose a new output directory; existing directories are never overwritten")
    command = [sys.executable, "-m", "spider_web_recovery.e1_benchmark",
               *(sys.argv[1:] if argv is None else [str(x) for x in argv])]
    manifest = provenance(configs, args.seeds, args.scenarios, command)
    args.output.mkdir(parents=True, exist_ok=False)
    dump(args.output/"provenance.json", manifest)
    traces = args.output/"traces"
    traces.mkdir()
    rows = []
    # Incremental JSONL survives interruption; the completion manifest is written last.
    with (args.output/"trials.jsonl").open("x") as journal:
        for index, config in enumerate(configs):
            for scenario in args.scenarios:
                for seed in range(args.seeds):
                    offset = seed % len(CONTROLLERS)
                    for controller in CONTROLLERS[offset:]+CONTROLLERS[:offset]:
                        row, trace, _ = run_trial(config, controller, scenario, seed)
                        rows.append(row)
                        journal.write(json.dumps(row, allow_nan=False)+"\n")
                        journal.flush()
                        if seed == 0:
                            dump(traces/f"case{index}_{scenario}_{controller}.json", trace)
                print(f"sectors={config.sectors}, A={config.amplitude_cm:g}: {scenario} complete", flush=True)
    exposure = audit_exposure(rows)
    dump(args.output/"exposure.json", exposure)
    for name, data in (("trials", rows), ("summary", summarize(rows)), ("paired", paired(rows))):
        dump(args.output/f"{name}.json", data)
        save_csv(args.output/f"{name}.csv", data)
    diagnostics = args.output/"diagnostics"
    diagnostics.mkdir()
    for scenario in ("damage_single", "transfer_partial"):
        row, trace, trees = run_trial(configs[0], "retained_htn", scenario, 0, record_trees=True)
        dump(diagnostics/f"{scenario}.json", dict(row=row, events=trace, trees=trees))
        for index, tree in enumerate(trees):
            (diagnostics/f"{scenario}_tree{index}.svg").write_text(tree_svg(tree))
    write_report(rows, exposure, args.output)
    plot_completion(rows, args.output)
    for name, sha in manifest["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise RuntimeError(f"Source changed during sweep: {name}")
    dump(args.output/"artifact_sha256.json", {
        p.relative_to(args.output).as_posix(): digest(p)
        for p in sorted(args.output.rglob("*")) if p.is_file()})
    print(f"Report: {(args.output/'report.md').resolve()}", flush=True)


if __name__ == "__main__":
    main()
