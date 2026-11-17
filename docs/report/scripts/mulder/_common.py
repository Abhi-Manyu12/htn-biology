"""Shared paths/helpers for the Mulder figure scripts (domain `mulder`).

All data are read from the read-only repo copy at W/repo/htn-biology (commit 61d18d8).
"""
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
R = W / "repo" / "htn-biology"
RES = R / "mulder_results"
OUT = W / "report" / "figures" / "mulder"
WORK = W / "work" / "mulder"
sys.path.insert(0, str(W / "tools"))

import plotstyle  # noqa: E402
from plotstyle import apply, save, C, POLICY_COLORS, THREAD_COLORS, FIG_1COL, FIG_WIDE, FIG_2PANEL, FIG_GRID, FIG_SQUARE  # noqa: E402,F401

ORDER = ["fixed", "local", "local_repair", "filtered", "predictive", "full"]
LABEL = {"fixed": "fixed", "local": "local", "local_repair": "local_repair",
         "filtered": "filtered", "predictive": "predictive", "full": "full"}
# Trace phase name -> shared thread colour
PHASE_THREAD = {"frame": THREAD_COLORS["frame"], "radials": THREAD_COLORS["radius"],
                "auxiliary": THREAD_COLORS["aux_spiral"], "capture": THREAD_COLORS["capture_spiral"]}
TOTAL_ACTIONS = 218


def wilson(k, n, z=1.959963984540054):
    """Wilson 95% interval, same formula as spider_web_mulder.validation.wilson."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - r), min(1.0, c + r)


def out(stem):
    OUT.mkdir(parents=True, exist_ok=True)
    return str(OUT / stem)


def load_trace(path):
    with open(path) as f:
        return json.load(f)


def shear_dx(y, t, A, f, phase, H=30.0):
    """World-frame horizontal displacement of material height y (model.Shear.world)."""
    return (1 - y / H) * A * math.sin(2 * math.pi * f * t + phase)
