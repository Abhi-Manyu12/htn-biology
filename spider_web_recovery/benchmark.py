"""Matched failure-recovery benchmark using the pinned upstream IPyHOP."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import html
import itertools
import json
from pathlib import Path
import platform
import statistics

import gtpyhop
import networkx
import numpy as np

from spider_web_mulder.validation import save_csv,wilson,interval
from .backends import VENDOR
from .domain import Config
from .experiment import BACKENDS,SCENARIOS,run_trial


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        c = row["config"]
        groups[(row["scenario"],row["backend"],c["sectors"],c["depth"],c["amplitude_cm"])].append(row)
    result = []
    for (scenario,backend,sectors,depth,amplitude),group in groups.items():
        successes = sum(r["success"] for r in group)
        result.append(dict(scenario=scenario,backend=backend,sectors=sectors,depth=depth,amplitude_cm=amplitude,
                           trials=len(group),successes=successes,success_ci95=wilson(successes,len(group)),
                           events_fired=sum(r["event_fired"] for r in group),
                           mean_method_calls=statistics.mean(r["method_calls"] for r in group),
                           mean_repairs=statistics.mean(r["repairs"] for r in group),
                           mean_stale_preconditions=statistics.mean(r["stale_preconditions"] for r in group),
                           mean_unnecessary_repeats=statistics.mean(r["unnecessary_repeats"] for r in group),
                           mean_recovery_retraced_cm=statistics.mean(r["recovery_retraced_cm"] for r in group)))
    return result


def paired(rows):
    def key(r):
        c = r["config"]
        return (r["scenario"],r["seed"],c["sectors"],c["depth"],c["amplitude_cm"])
    fresh = {key(r):r for r in rows if r["backend"]=="ipyhop_fresh"}
    groups = defaultdict(list)
    for row in rows:
        if row["backend"]=="ipyhop" and key(row) in fresh:
            groups[(row["scenario"],row["config"]["sectors"],row["config"]["depth"],row["config"]["amplitude_cm"])].append((row,fresh[key(row)]))
    rng = np.random.default_rng(20261020)
    output = []
    for (scenario,sectors,depth,amplitude),pairs in groups.items():
        for metric in ("success","method_calls","ipyhop_iterations","planning_wall_s","elapsed_s","travel_cm","silk_used_cm"):
            computational = metric in ("success","method_calls","ipyhop_iterations","planning_wall_s")
            eligible = pairs if computational else [(a,b) for a,b in pairs if a["success"] and b["success"]]
            values = [float(a[metric])-float(b[metric]) for a,b in eligible]
            output.append(dict(scenario=scenario,sectors=sectors,depth=depth,amplitude_cm=amplitude,
                               contrast="retained_minus_fresh_IPyHOP",metric=metric,paired_n=len(values),
                               conditioning="all attempted pairs" if computational else "both constructions complete",
                               mean_difference=statistics.mean(values) if values else None,
                               ci95=interval(values,rng,2000)))
    return output


def tree_svg(snapshot):
    nodes = {n["id"]:n for n in snapshot["nodes"]}
    children = defaultdict(list)
    for parent,child in snapshot["edges"]:
        children[parent].append(child)
    levels = defaultdict(list)
    queue = [(0,0)]
    while queue:
        node,depth = queue.pop(0)
        levels[depth].append(node)
        queue.extend((child,depth+1) for child in children[node])
    width = max(1000,140*max(map(len,levels.values()),default=1))
    height = 90*(len(levels)+1)
    xy = {node:((i+.5)*width/len(layer),45+90*depth) for depth,layer in levels.items() for i,node in enumerate(layer)}
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>']
    for parent,child in snapshot["edges"]:
        a,b = xy[parent],xy[child]
        lines.append(f'<path d="M{a[0]},{a[1]}L{b[0]},{b[1]}" stroke="#bbb" fill="none"/>')
    for node,attrs in nodes.items():
        x,y = xy[node]
        color = "#3779ad" if attrs["tag"]=="old" else "#a95627"
        label = html.escape(str(attrs["info"]))
        lines.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"><title>{label}</title></circle>'
                     f'<text x="{x}" y="{y+18}" text-anchor="middle" font-size="9">{node}: {html.escape(str(attrs["info"][0]))}</text>')
    lines.append('</svg>')
    return "\n".join(lines)


def write_report(rows,summaries,contrasts,output):
    lines = ["# Retained-tree recovery benchmark", "",
             f"{len(rows)} trials. Actual upstream IPyHOP revision bdda21012b2396aed9a91980af8fbb71dbcb7075; source and BSD license are vendored.",
             "This is a dependency-changing sector-construction domain, not a rerun of the Mulder geometry/biological study.", "",
             "## Outcomes by scenario and backend", "",
             "Counts pool the declared size/depth/amplitude cases for a compact overview; summary.csv retains each stratum.", "",
             "| Scenario | Backend | Completed / trials | Events fired | Mean repairs | Mean stale preconditions |",
             "|---|---|---:|---:|---:|---:|"]
    groups = defaultdict(list)
    for row in rows:
        groups[(row["scenario"],row["backend"])].append(row)
    for (scenario,backend),group in groups.items():
        lines.append(f'| {scenario} | {backend} | {sum(r["success"] for r in group)}/{len(group)} | '
                     f'{sum(r["event_fired"] for r in group)} | {statistics.mean(r["repairs"] for r in group):.3f} | '
                     f'{statistics.mean(r["stale_preconditions"] for r in group):.3f} |')
    primary = [r for r in contrasts if r["sectors"]==8 and r["depth"]==2 and r["amplitude_cm"]==10 and r["metric"]=="method_calls"]
    if primary:
        lines += ["", "## Same-engine retained versus fresh planning effort", "",
                  "Eight sectors, depth 2, 10 cm movement. Negative differences favour retained-tree IPyHOP. Failed cases are included.", "",
                  "| Scenario | Paired seeds | Mean method-call difference | Pointwise 95% bootstrap interval |",
                  "|---|---:|---:|---|"]
        for row in primary:
            low,high = row["ci95"]
            lines.append(f'| {row["scenario"]} | {row["paired_n"]} | {row["mean_difference"]:.3f} | {low:.3f} to {high:.3f} |')
    lines += ["", "## Interpretation and scope", "",
              "- fresh_root and component use explicitly pinned GTPyhop iterative DFS backtracking. Their previous greedy default is not used here.",
              "- ipyhop_fresh and ipyhop use the same upstream engine and domain. The former discards its tree on every planning call; the latter calls replan(observed_state, failed_node_id). This isolates retained-tree recovery more closely than cross-engine comparisons.",
              "- Every attempted move is checked against current graph edges and starts from the observed position. Radius loss removes its traversable link. Scaffold links are an explicit initial condition, not invented routes after failure.",
              "- Failed attachment/capture attempts consume resource and time. Resource depletion is observed, not rolled back. History is separate from valid radii/captures; damage can require legitimate reconstruction of earlier work.",
              "- Transient misses retry the same command within a budget and are not permanently blacklisted. Unreachable/resource-infeasible cases must terminate with failure, not claim success because the planner returns an empty list.",
              "- Component repair intentionally keeps cached later actions as a diagnostic baseline. A changed anchor can invalidate their explicit preconditions; the actor rejects them and replans rather than performing an invalid construction.",
              "- This actor uses immediate observed precondition checks and actual action outcomes. It integrates upstream IPyHOP's retained-tree algorithm; it is not a verbatim reimplementation or experimental replication of the paper's full Run-Lazy-Refineahead setup.",
              "- Scenarios use declared logical-action triggers, shared across backends for a case. They are not identical absolute-time disturbances; event exposure is recorded. Initial motion phase and target sector vary with seed.",
              "- Sector capture is an abstract resource-consuming operation. Silk amounts are model units in cm, not validated deposited-silk or metabolic measurements. Physical route tracking reuses the v3 no-slip executor.",
              "- Method-call counts include shared feasibility guards. GTPyhop's eager alternative evaluation differs from IPyHOP; use the same-engine paired contrasts to assess retention. Upstream iterations are reported as supplied by IPyHOP.",
              "- planning_wall_s includes adapter setup and tree snapshot overhead. Treat it as measured implementation cost, not an isolated planner CPU theorem. Planning effort includes failed cases so infeasibility overhead is visible; construction costs compare successful pairs only. Intervals are pointwise bootstrap summaries.", "",
              "## Artifacts", "",
              "- trials.json / trials.csv: all outcomes, actual terminal state and resource accounting.",
              "- summary.json / summary.csv: stratified completion, repair and stale-plan measures.",
              "- paired.json / paired.csv: retained-minus-fresh IPyHOP differences, matched by complete case identity.",
              "- traces/: representative first-seed action ledgers, before/after observations, replan records, solution trees and tree SVGs when --trace is supplied.",
              "- provenance.json: backend strategy, upstream revision/hash manifest, runtime and source hashes.", ""]
    text = "\n".join(lines)
    (output/"report.md").write_text(text)
    examples = output/"traces"/"case1_permanent_anchor_ipyhop"
    links_html = ''
    if examples.exists():
        links_html = '<h2>Example: permanent anchor failure, retained IPyHOP</h2><ul>' + ''.join(
            f'<li><a href="{path.relative_to(output).as_posix()}">{html.escape(path.name)}</a></li>'
            for path in sorted(examples.iterdir())) + '</ul><p>In tree SVGs, blue nodes retain old refinements and orange nodes are new. Hover for task arguments.</p>'
    (output/"report.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Recovery benchmark</title>'
                                     '<style>body{font:15px system-ui;max-width:1250px;margin:30px auto;padding:20px}pre{white-space:pre-wrap;line-height:1.5}</style><pre>'+html.escape(text)+'</pre></html>')
    if links_html:
        path = output/"report.html"
        path.write_text(path.read_text().replace('</html>',links_html+'</html>'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds",type=int,default=10)
    parser.add_argument("--sectors",nargs="+",type=int,default=[4,8])
    parser.add_argument("--depths",nargs="+",type=int,default=[0,2])
    parser.add_argument("--amplitudes",nargs="+",type=float,default=[0,10])
    parser.add_argument("--backends",nargs="+",choices=BACKENDS,default=list(BACKENDS))
    parser.add_argument("--scenarios",nargs="+",choices=SCENARIOS,default=list(SCENARIOS))
    parser.add_argument("--trace",action="store_true")
    parser.add_argument("--output",type=Path,default=Path("mulder_results/recovery_v1"))
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("Use at least one seed")
    for values in (args.sectors,args.depths,args.amplitudes,args.backends,args.scenarios):
        if len(values)!=len(set(values)):
            parser.error("Duplicate sweep values are not allowed")
    configs = [Config(sectors=n,depth=d,amplitude_cm=a) for n,d,a in itertools.product(args.sectors,args.depths,args.amplitudes)]
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error("Choose an empty output directory")
    upstream = json.loads((VENDOR/"UPSTREAM.json").read_text())
    for name,digest in upstream["sha256"].items():
        if hashlib.sha256((VENDOR/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError(f"Pinned upstream source changed: {name}")
    args.output.mkdir(parents=True,exist_ok=True)
    rows = []
    for cindex,config in enumerate(configs):
        for scenario in args.scenarios:
            for seed in range(args.seeds):
                for backend in args.backends:
                    row,trace,trees = run_trial(config,backend,scenario,seed)
                    rows.append(row)
                    if args.trace and seed==0:
                        folder = args.output/"traces"/f"case{cindex}_{scenario}_{backend}"
                        folder.mkdir(parents=True,exist_ok=True)
                        (folder/"events.json").write_text(json.dumps(trace,indent=2,allow_nan=False)+"\n")
                        (folder/"trees.json").write_text(json.dumps(trees,indent=2,allow_nan=False)+"\n")
                        for i,tree in enumerate(trees):
                            (folder/f"tree_{i}.svg").write_text(tree_svg(tree))
            print(f"sectors={config.sectors}, depth={config.depth}, A={config.amplitude_cm:g}: {scenario} complete",flush=True)
    summaries = summarize(rows)
    contrasts = paired(rows)
    for name,data in (("trials",rows),("summary",summaries),("paired",contrasts)):
        (args.output/f"{name}.json").write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
        if data:
            save_csv(args.output/f"{name}.csv",data)
    source = Path(__file__).parent
    physical = source.parent/"spider_web_mulder"
    provenance = dict(recovery_model_version=1,shared_executor_version=3,python=platform.python_version(),
                      gtpyhop=gtpyhop.__version__,networkx=networkx.__version__,upstream=upstream,
                      fresh_strategy="iterative_dfs_backtracking",seeds=list(range(args.seeds)),
                      configs=[asdict(c) for c in configs],backends=args.backends,scenarios=args.scenarios,
                      event_protocol="one logical-action-triggered event per non-clean trial; no random-draw coupling",
                      source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob("*.py")},
                      shared_source_sha256={name:hashlib.sha256((physical/name).read_bytes()).hexdigest() for name in ("model.py","experiment.py","tracking.py")})
    (args.output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    write_report(rows,summaries,contrasts,args.output)
    print(f"Report: {(args.output/'report.html').resolve()}")


if __name__ == "__main__":
    main()
