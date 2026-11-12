"""Curate v4 integration evidence and verify the executed source manifest."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]


def snapshot(output):
    metadata = json.loads((output/'metadata.json').read_text())
    summary = json.loads((output/'summary.json').read_text())
    paired = json.loads((output/'paired.json').read_text())
    for name,digest in metadata['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    for name,digest in metadata['upstream']['sha256'].items():
        assert hashlib.sha256((ROOT/'third_party/IPyHOP'/name).read_bytes()).hexdigest() == digest, name
    rows = list(csv.DictReader((output/'trials.csv').open()))
    index = {}
    for row in rows:
        key = (row['complexity'],row['profile'],row['controller'],int(row['seed']),row['planner_backend'])
        assert key not in index
        index[key] = row
        assert int(row['completed_actions']) <= int(row['total_actions'])
    assert len(rows) == len(metadata['seeds'])*len(metadata['controllers'])*len(metadata['backends'])*len(metadata['complexities'])*len(metadata['profiles'])
    disagreements = []
    maxima = dict.fromkeys(('elapsed_s','travel_cm','completed_actions','repairs'),0.)
    for key,row in index.items():
        if key[-1] != 'ipyhop_retained':
            continue
        fresh = index[(*key[:-1],'ipyhop_fresh')]
        assert row['trajectory_id'] == fresh['trajectory_id']
        if row['success'] != fresh['success']:
            disagreements.append(key[:-1])
        for metric in maxima:
            maxima[metric] = max(maxima[metric],abs(float(row[metric])-float(fresh[metric])))
    tree_checks = []
    for path in sorted(output.glob('trace_*.json')):
        trace = json.loads(path.read_text())
        accepted = [e['index'] for e in trace if e['event']=='action' and e['accepted']]
        assert accepted == list(range(len(accepted))), path
        snapshots = [e for e in trace if e['event']=='planner_tree']
        for old,new in zip(snapshots,snapshots[1:]):
            if new['reentry']:
                assert new['failed_node'] in {n['id'] for n in old['nodes']}, path
        tree_checks.append(dict(path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               accepted_actions=len(accepted),snapshots=len(snapshots)))
    timings = []
    for profile in metadata['profiles']:
        for controller in metadata['controllers']:
            fresh = [float(r['planning_wall_s']) for r in rows if r['complexity']=='configured' and
                     r['profile']==profile and r['controller']==controller and r['planner_backend']=='ipyhop_fresh' and int(r['seed'])>0]
            retained = [float(r['planning_wall_s']) for r in rows if r['complexity']=='configured' and
                        r['profile']==profile and r['controller']==controller and r['planner_backend']=='ipyhop_retained' and int(r['seed'])>0]
            timings.append(dict(profile=profile,controller=controller,n=len(fresh),
                                fresh_mean_s=statistics.mean(fresh),retained_mean_s=statistics.mean(retained)))
    result = dict(study='Mulder HTN IPyHOP integration v4',trial_count=len(rows),metadata=metadata,
                  report_postprocessing=json.loads((output/'report_notes.json').read_text()) if (output/'report_notes.json').exists() else None,
                  snapshot_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  bulk_output=str(output.relative_to(ROOT)),
                  artifact_sha256={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in
                                   ('trials.csv','metadata.json','summary.json','paired.json','report.html')},
                  same_engine_completion_disagreements=disagreements,
                  same_engine_max_absolute_difference=maxima,
                  summaries=summary,
                  configured_paired_contrasts=[r for r in paired if r['complexity']=='configured'],
                  configured_timing_excluding_seed0=timings,trace_verification=tree_checks)
    target = ROOT/'docs/research/evidence/mulder_reentrant_v4_summary.json'
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(target)
    print('Trial count:',len(rows),'same-engine physical differences:',maxima)


if __name__=='__main__':
    snapshot(Path(sys.argv[1]).resolve())
