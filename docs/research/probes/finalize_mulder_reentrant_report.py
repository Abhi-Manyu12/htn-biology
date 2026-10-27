"""Add an evidence-backed overview after the numerical sweep and scope control."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
output = Path(sys.argv[1]).resolve()
evidence = json.loads((ROOT/'docs/research/evidence/mulder_reentrant_v4_summary.json').read_text())
control_path = ROOT/'docs/research/evidence/mulder_suffix_control.json'
control = json.loads(control_path.read_text())
assert evidence['same_engine_completion_disagreements'] == []
assert all(v==0 for v in evidence['same_engine_max_absolute_difference'].values())
summary = json.loads((output/'summary.json').read_text())
def value(profile,controller,backend):
    return next(r for r in summary if (r['complexity'],r['profile'],r['controller'],r['backend'])==
                ('configured',profile,controller,backend))
lag = [value('lag_1s','filtered',b)['successes'] for b in ('legacy','ipyhop_fresh','ipyhop_retained')]
assert lag == [0,5,5] and control['successes']==5
full = [value('moving_005','full',b) for b in ('ipyhop_fresh','ipyhop_retained')]
section = '''<!-- findings-start --><h2>Key findings</h2>
<p><b>Retained-tree recovery changes planning work, but does not improve physical outcomes over fresh IPyHOP in this sweep.</b> All 720 same-engine pairs have identical completion, completed actions, repairs, elapsed construction time and travel.</p>
<p>There is a scoped improvement over legacy component repair: the configured-size filtered controller under 1 s sensor lag improves from 0/10 to 5/10 completion with either IPyHOP mode. A separate 10-trial control using the original GTPyhop domain with whole-suffix refresh also achieves 5/10, with identical physical outcomes and repair counts per seed. This gain is explained by refresh scope in these cases, not a unique benefit of retaining the IPyHOP tree. In the small lag profile, filtered completion instead decreases from 3/10 to 2/10.</p>
<p>For configured-size full control at 10 cm, 0.05 Hz, mean method calls decrease from 25,966 (fresh IPyHOP) to 25,532 (retained), about 1.67%. Physical costs are identical. Planning wall time excluding the recorded seed 0 is about 1.823 s versus 2.628 s: tree handling is slower despite fewer method calls. Timing is implementation/environment-specific.</p>
<p>All four retry-capable policies recover from the single synthetic miss, with either IPyHOP mode and with legacy repair. Endpoint execution remains unsuccessful in all declared cases. These are computational model results, not biological validation.</p>
<!-- findings-end -->'''
path = output/'report.html'
page = path.read_text()
if '<!-- findings-start -->' in page:
    before,rest = page.split('<!-- findings-start -->',1)
    _,after = rest.split('<!-- findings-end -->',1)
    page = before+section+after
else:
    page = page.replace('<h2>All outcomes</h2>',section+'<h2>All outcomes</h2>')
path.write_text(page)
notes = dict(description=__doc__,
    script=str(Path(__file__).resolve().relative_to(ROOT)),
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    control_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),
    scope='Report-only annotation; numerical trials and their executed-source manifest unchanged.')
(output/'report_notes.json').write_text(json.dumps(notes,indent=2)+'\n')
print(path)
