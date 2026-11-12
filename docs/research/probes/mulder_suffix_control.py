"""Isolate whole-suffix refresh using the original GTPyhop domain.

This diagnostic substitutes only the optional backend adapter; movement,
controller rules and original symbolic methods are unchanged. It is not IPyHOP.
"""
import contextlib
import hashlib
import io
import importlib.metadata
import platform
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import gtpyhop
from spider_web_mulder.experiment import run_trial
from spider_web_mulder.model import load_settings

ROOT = Path(__file__).resolve().parents[3]


class FreshRootControl:
    def __init__(self, mode, counter, record_trees=False):
        self.reentries = 0
        self.snapshots = []

    def completed(self):
        pass

    def plan(self, state):
        old = gtpyhop.get_verbose_level()
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                gtpyhop.set_verbose_level(0)
                return gtpyhop.find_plan(state, [('build_web',)])
            finally:
                gtpyhop.set_verbose_level(old)


def main():
    settings, _ = load_settings()
    settings = replace(settings, amplitude_cm=10., frequency_hz=.05,
                       execution_mode='tracking', method_policy='direct',sensor_tau_s=1.)
    rows = []
    for seed in range(10):
        with patch('spider_web_mulder.reentrant.MulderPlanner', FreshRootControl):
            row, _ = run_trial(settings,'filtered',seed,planner_backend='ipyhop_fresh')
        row['planner_backend'] = 'gtpyhop_fresh_root_control'
        rows.append(row)
    from dataclasses import asdict
    import gtpyhop.main as engine
    inputs = ['docs/research/probes/mulder_suffix_control.py',
              'spider_web_mulder/experiment.py','spider_web_mulder/model.py',
              'spider_web_mulder/tracking.py','spider_web_mulder/measurements.py',
              'spider_web_mulder/config.yaml']
    payload = dict(description=__doc__,settings=asdict(settings),seeds=list(range(10)),
        strategy=engine._current_seek_plan.__name__,
        python=platform.python_version(),
        versions={name:importlib.metadata.version(name) for name in ('gtpyhop','networkx','numpy')},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
        trials=rows,successes=sum(r['success'] for r in rows))
    target = ROOT/'docs/research/evidence/mulder_suffix_control.json'
    target.write_text(json.dumps(payload,indent=2)+'\n')
    print('Fresh-root GTPyhop control:',payload['successes'],'/ 10')


if __name__ == '__main__':
    main()
