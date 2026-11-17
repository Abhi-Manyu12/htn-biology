"""Shared paths and helpers for the recovery-domain figure scripts."""
import json
import math
import sys
from pathlib import Path

W = Path("<WORKSPACE>")
R = W / "repo" / "htn-biology"
OUT = W / "report" / "figures" / "recovery"
sys.path.insert(0, str(W / "tools"))
import plotstyle  # noqa: E402

REC = R / "mulder_results" / "recovery_v1_verified"
V4 = R / "mulder_results" / "mulder_reentrant_v4"
EVID = R / "docs" / "research" / "evidence"

SCENARIOS = ["clean", "transient_attachment", "permanent_anchor", "route_block",
             "prefix_damage", "silk_depletion", "unreachable"]
SCEN_LABEL = {"clean": "clean", "transient_attachment": "transient attach.",
              "permanent_anchor": "permanent anchor", "route_block": "route block",
              "prefix_damage": "prefix damage", "silk_depletion": "silk depletion",
              "unreachable": "unreachable"}
BACKENDS = ["fresh_root", "component", "ipyhop_fresh", "ipyhop"]
BACK_LABEL = {"fresh_root": "fresh_root (GTPyhop DFS)", "component": "component (GTPyhop DFS)",
              "ipyhop_fresh": "ipyhop_fresh", "ipyhop": "ipyhop (retained)"}
POLICIES = ["fixed", "local", "filtered", "local_repair", "full", "predictive"]
V4_BACK = ["legacy", "ipyhop_fresh", "ipyhop_retained"]
V4_BACK_COLOR = {"legacy": plotstyle.BACKEND_COLORS["legacy"],
                 "ipyhop_fresh": plotstyle.BACKEND_COLORS["ipyhop_fresh"],
                 "ipyhop_retained": plotstyle.BACKEND_COLORS["ipyhop"]}
PROFILES = ["rigid", "moving_0049", "moving_005", "transient_miss", "lag_1s", "endpoint"]
PROFILE_LABEL = {"rigid": "rigid", "moving_0049": "10 cm, 0.049 Hz", "moving_005": "10 cm, 0.05 Hz",
                 "transient_miss": "one miss", "lag_1s": "1 s lag", "endpoint": "endpoint"}


def load_json(path):
    return json.loads(Path(path).read_text())


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
