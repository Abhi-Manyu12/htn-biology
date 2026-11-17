"""Test-suite composition of spider_web_htn_updated/tests at 39b89f3 and 61d18d8 (tests per file).

Sources: work/core/derived/pytest_{39b89f3,61d18d8}.xml, written by
    cd <private checkout>/spider_web_htn_updated && "$PY" -m pytest -q -p no:cacheprovider --junitxml=<xml>
(all tests passed in both runs: 55 at 39b89f3, 56 at 61d18d8).
"""
import collections
import os
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np

from _common import DERIVED, FIG
import plotstyle

plotstyle.apply()
res = {}
for tag in ("39b89f3", "61d18d8"):
    r = ET.parse(os.path.join(DERIVED, f"pytest_{tag}.xml")).getroot()
    cnt = collections.Counter()
    fails = 0
    for tc in r.iter("testcase"):
        cnt[tc.get("classname").split(".")[-1] + ".py"] += 1
        fails += any(ch.tag in ("failure", "error") for ch in tc)
    res[tag] = (cnt, fails)
files = sorted(set(res["61d18d8"][0]) | set(res["39b89f3"][0]), key=lambda f: -res["61d18d8"][0][f])
y = np.arange(len(files))
fig, ax = plt.subplots(figsize=(5.0, 2.3))
for k, (tag, col) in enumerate((("39b89f3", plotstyle.C["grey"]), ("61d18d8", plotstyle.C["blue"]))):
    cnt, fails = res[tag]
    v = [cnt[f] for f in files]
    ax.barh(y + (k - 0.5) * 0.38, v, 0.38, color=col,
            label=f"{tag}: {sum(v)} tests, {sum(v) - fails} passed")
    for yy, vv in zip(y + (k - 0.5) * 0.38, v):
        ax.text(vv + 0.3, yy, str(vv), va="center", fontsize=6.5)
ax.set_yticks(y)
ax.set_yticklabels([f"tests/{f}" for f in files], fontsize=7.5)
ax.invert_yaxis()
ax.set_xlabel("Number of tests")
ax.grid(axis="y", visible=False)
ax.set_xlim(0, 25)
ax.legend(fontsize=6.8, loc="lower right")
plotstyle.save(fig, f"{FIG}/tests_per_file")
print({t: dict(c) for t, (c, f) in res.items()})
