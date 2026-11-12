"""Matched recovery-backend comparisons in the Mulder construction model.

python3 -m spider_web_mulder.recovery_comparison --seeds 10 --output mulder_results/mulder_reentrant_v4
"""
import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import html
import importlib.metadata
import json
from pathlib import Path
import platform
import statistics
import subprocess

import numpy as np

from .experiment import CONTROLLERS, run_trial
from .model import load_settings

BACKENDS = ('legacy', 'ipyhop_fresh', 'ipyhop_retained')
PROFILES = {
    'rigid': dict(amplitude_cm=0., frequency_hz=.05, execution_mode='tracking', sensor_tau_s=0.),
    'moving_0049': dict(amplitude_cm=10., frequency_hz=.049, execution_mode='tracking', sensor_tau_s=0.),
    'moving_005': dict(amplitude_cm=10., frequency_hz=.05, execution_mode='tracking', sensor_tau_s=0.),
    'transient_miss': dict(amplitude_cm=10., frequency_hz=.05, execution_mode='tracking', sensor_tau_s=0.),
    'lag_1s': dict(amplitude_cm=10., frequency_hz=.05, execution_mode='tracking', sensor_tau_s=1.),
    'endpoint': dict(amplitude_cm=10., frequency_hz=.05, execution_mode='endpoint', sensor_tau_s=0.),
}


def analyze(rows):
    rng = np.random.default_rng(20261020)
    groups = {}
    for row in rows:
        key = (row['complexity'], row['profile'], row['controller'], row['planner_backend'])
        groups.setdefault(key, []).append(row)
    summaries, contrasts = [], []
    for (complexity,profile,controller,backend), group in groups.items():
        result = dict(complexity=complexity,profile=profile,controller=controller,backend=backend,
                      n=len(group),successes=sum(r['success'] for r in group))
        for metric in ('method_calls','planning_wall_s','repairs','completed_actions'):
            result['mean_'+metric] = statistics.mean(r[metric] for r in group)
        completed = [r for r in group if r['success']]
        for metric in ('elapsed_s','travel_cm'):
            result['successful_mean_'+metric] = statistics.mean(r[metric] for r in completed) if completed else None
        summaries.append(result)
        if backend != 'ipyhop_retained':
            continue
        for comparator in ('ipyhop_fresh','legacy'):
            controls = {r['seed']:r for r in groups[(complexity,profile,controller,comparator)]}
            for metric in ('success','completed_actions','method_calls','planning_wall_s','repairs','elapsed_s','travel_cm'):
                pairs = [(r,controls[r['seed']]) for r in group]
                conditional = metric in ('elapsed_s','travel_cm')
                if conditional:
                    pairs = [(r,c) for r,c in pairs if r['success'] and c['success']]
                differences = np.array([float(r[metric])-float(c[metric]) for r,c in pairs])
                ci = None
                if len(differences):
                    boot = rng.choice(differences,size=(2000,len(differences)),replace=True).mean(axis=1)
                    ci = list(map(float,np.quantile(boot,[.025,.975])))
                contrasts.append(dict(complexity=complexity,profile=profile,controller=controller,
                    contrast='ipyhop_retained minus '+comparator,metric=metric,n=len(pairs),
                    conditional_on_both_success=conditional,
                    mean_difference=float(differences.mean()) if len(differences) else None,ci95=ci))
    return summaries, contrasts


def report(output, summaries, contrasts):
    columns = ('complexity','profile','controller','backend','successes','n','mean_method_calls',
               'mean_planning_wall_s','mean_repairs','successful_mean_elapsed_s','successful_mean_travel_cm')
    def table(data,keys):
        def fmt(v):
            return f'{v:.6g}' if isinstance(v,float) else str(v)
        return '<table><tr>'+''.join(f'<th>{html.escape(k)}</th>' for k in keys)+'</tr>'+''.join(
            '<tr>'+''.join('<td>'+html.escape(fmt(row[k]))+'</td>' for k in keys)+'</tr>' for row in data)+'</table>'
    page = '''<!doctype html><meta charset="utf-8"><title>Mulder HTN: IPyHOP recovery comparison</title>
<style>body{font:15px system-ui;margin:32px}table{border-collapse:collapse;margin:20px 0}td,th{border:1px solid #ccc;padding:5px}th{position:sticky;top:0;background:#eee}</style>
<h1>IPyHOP integrated into the Mulder HTN</h1>
<p>Same construction geometry, shear trajectory and physical executor. Three backends × six controllers × six profiles × two construction sizes. Seeds determine identical initial phases. Retained-minus-fresh is the same-engine comparison. Negative cost differences favor retention.</p>
<p>The synthetic transient profile rejects the first otherwise successful attachment at segment 10 once, after paying its real movement/time cost. This tests recovery software; it is not a calibrated biological disturbance. No graph roadblock or silk-resource model has been added to Mulder.</p>
<p>IPyHOP adds per-segment refinement tasks with finite current-target refresh alternatives. Fresh starts at the root; retained invokes upstream replan at the real failed/current leaf and replaces the full unexecuted suffix. Legacy retains its historical component-splicing policy and unpinned GTPyhop strategy, so cross-engine method counts are not directly comparable.</p>
<p>Planning wall time includes state adaptation and leaf mapping. Backend order rotates by seed; timing remains environment-dependent. Elapsed construction time excludes CPU planning time and includes the same configured repair delay. Physical costs are compared only for jointly successful pairs; computational costs include failures. Bootstrap intervals are pointwise, 2,000 resamples, not multiplicity-adjusted.</p>
<h2>All outcomes</h2>'''
    page += table(summaries, columns)
    page += '<h2>Paired contrasts</h2>'+table(contrasts,('complexity','profile','controller','contrast','metric','n','mean_difference','ci95'))
    (output/'report.html').write_text(page)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path)
    parser.add_argument('--seeds',type=int,default=10,help='Number of seeds, beginning at 0')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--trace',action='store_true')
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('Output directory must be empty')
    settings,_ = load_settings(args.config)
    settings = replace(settings,method_policy='direct')
    sizes = {'small':dict(radial_count=4,auxiliary_turns=1,capture_turns=1),
             'configured':dict(radial_count=settings.radial_count,auxiliary_turns=settings.auxiliary_turns,capture_turns=settings.capture_turns)}
    root = Path(__file__).resolve().parents[1]
    sources = [Path(__file__).with_name(name) for name in
               ('model.py','experiment.py','tracking.py','measurements.py','reentrant.py','recovery_comparison.py')]
    upstream_path = root/'third_party/IPyHOP/UPSTREAM.json'
    upstream = json.loads(upstream_path.read_text())
    metadata = dict(study_version=4,base_settings=asdict(settings),profiles=PROFILES,complexities=sizes,
        seeds=list(range(args.seeds)),controllers=list(CONTROLLERS),backends=BACKENDS,
        python=platform.python_version(),versions={name:importlib.metadata.version(name) for name in ('gtpyhop','networkx','numpy')},
        source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        upstream=upstream,config_path=str(args.config or Path(__file__).with_name('config.yaml')),
        config_sha256=hashlib.sha256((args.config or Path(__file__).with_name('config.yaml')).read_bytes()).hexdigest(),
        backend_order='rotated left by seed modulo 3 within each controller',
        actor='Mulder v3 executor; optional single synthetic rejection at segment 10',
        uncertainty='pointwise paired bootstrap, 2000 replicates, RNG seed 20261020')
    metadata['branch'] = subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    import gtpyhop.main as engine
    metadata['legacy_strategy'] = engine._current_seek_plan.__name__
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    rows = []
    with (args.output/'trials.csv').open('w',newline='') as stream:
        writer = None
        for size,size_options in sizes.items():
            for profile,options in PROFILES.items():
                case = replace(settings,**size_options,**options)
                for seed in range(args.seeds):
                    for controller in CONTROLLERS:
                        order = BACKENDS[seed%3:]+BACKENDS[:seed%3]
                        for backend in order:
                            keep = args.trace and seed==0 and size=='configured' and profile in ('moving_005','transient_miss') and controller in ('local_repair','full')
                            row, trace = run_trial(case,controller,seed,planner_backend=backend,
                                forced_miss_index=10 if profile=='transient_miss' else None,
                                record_planner_tree=keep)
                            row.update(planner_backend=backend,reentries=row.get('reentries',0),complexity=size,profile=profile,
                                       injected_miss_count=sum(e.get('injected_miss',False) for e in trace))
                            rows.append(row)
                            if writer is None:
                                writer = csv.DictWriter(stream,fieldnames=list(row))
                                writer.writeheader()
                            writer.writerow(row)
                            if keep:
                                (args.output/f'trace_{profile}_{controller}_{backend}.json').write_text(json.dumps(trace,indent=2)+'\n')
                    stream.flush()
                print(f'{size} {profile}: {len(rows)} trials complete',flush=True)
    summaries,contrasts = analyze(rows)
    (args.output/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    (args.output/'paired.json').write_text(json.dumps(contrasts,indent=2)+'\n')
    report(args.output,summaries,contrasts)
    print(f'Report: {args.output.resolve()}/report.html',flush=True)


if __name__ == '__main__':
    main()
