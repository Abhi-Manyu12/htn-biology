"""Galleries of the repo's own simulated-web SVGs (trace_<case>_<seed>_<policy>.svg) and audit error plots.

Each gallery is an HTML page that inlines the unmodified SVG files in a labelled grid; it is captured
to PDF (vector) and PNG with W/tools/shot.mjs. The only presentation change is a CSS rule that draws
web threads with a fixed 0.8 px non-scaling stroke (the repo files use stroke-width 0.06 cm, which is
sub-pixel at gallery size). Label "k/218" = accepted actions from the matching trials.csv row.

Trace naming (experiment.py main()): trace_<case>_<seed>_<policy>; case enumerates amplitudes x
frequencies of that run's metadata.json, amplitude outer loop.
  pilot: amps [0,5,10] x freqs [0.01,0.05,0.1]  -> case 0 = (0, 0.01), 3 = (5, 0.01), 6 = (10, 0.01)
  frequency_0049_vs_005 and controller_audit_v2/verified_sweep: amps [0,5,10] x freqs [0.049,0.05]
                                                -> case 3 = (5, 0.05)
"""
import re
import subprocess

import numpy as np
import pandas as pd

from _common import RES, ORDER, W, WORK, OUT

SHOT = W / "tools" / "shot.mjs"
HTML_DIR = WORK / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)

CSS = """
body{margin:0;background:#fff;font-family:'Latin Modern Roman','CMU Serif','STIX Two Text',Georgia,serif;color:#000}
.g{display:grid;gap:4px 6px;padding:6px;align-items:center}
.cell{text-align:center;font-size:19px}
.cell svg{width:100%;height:auto;display:block;border:0.5px solid #ddd}
.web line{vector-effect:non-scaling-stroke;stroke-width:0.8px}
.rowh{font-size:18px;text-align:right;padding-right:6px;line-height:1.2}
.colh{font-size:20px;text-align:center;font-weight:bold}
.big svg{overflow:visible}
.big text{font-size:20px}
"""


def svg_inline(path):
    txt = path.read_text()
    txt = re.sub(r"<\?xml[^>]*\?>", "", txt)
    txt = re.sub(r"<!DOCTYPE[^>]*>", "", txt)
    return txt


def capture(html_name, stem, width):
    html = HTML_DIR / html_name
    for ext in ("pdf", "png"):
        subprocess.run(["node", str(SHOT), str(html), f"{OUT / stem}.{ext}", "--width", str(width), "--height", "200",
                        "--full", "--selector", ".g"], check=True)


def web_gallery(rows, stem, colw=150):
    """rows: list of (row label, directory, trials DataFrame, case, seed, amplitude, frequency)."""
    head = '<div></div>' + "".join(f'<div class="colh">{p}</div>' for p in ORDER)
    cells = []
    for label, d, tr, case, seed, a, f in rows:
        cells.append(f'<div class="rowh">{label}</div>')
        for p in ORDER:
            r = tr[(tr.controller == p) & (tr.seed == seed) & (tr.amplitude_cm == a) & np.isclose(tr.frequency_hz, f)]
            assert len(r) == 1, (d, p, seed, a, f)
            k = int(r.completed_actions.iloc[0])
            svg = svg_inline(d / f"trace_{case}_{seed}_{p}.svg")
            cells.append(f'<div class="cell web">{svg}<div>{k}/218</div></div>')
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}"
            f".g{{grid-template-columns:150px repeat(6,{colw}px)}}</style></head><body>"
            f"<div class='g'>{head}{''.join(cells)}</div></body></html>")
    (HTML_DIR / f"{stem}.html").write_text(html)
    capture(f"{stem}.html", stem, 150 + 6 * (colw + 6) + 20)


def errors_gallery():
    """Six repo error plots stacked in one column; SVG text enlarged to 18 px by CSS for print."""
    d = RES / "controller_audit_v2" / "report"
    cells = []
    for p in ORDER:
        cells.append(f'<div class="cell big"><div class="colh" style="text-align:left">{p}</div>{svg_inline(d / f"errors_{p}.svg")}</div>')
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}"
            ".g{grid-template-columns:960px;gap:2px}.cell svg{border:0}</style></head><body>"
            f"<div class='g'>{''.join(cells)}</div></body></html>")
    (HTML_DIR / "audit_v2_errors_repo.html").write_text(html)
    capture("audit_v2_errors_repo.html", "audit_v2_errors_repo", 1000)


def timeline():
    """Repo timeline.svg; SVG text enlarged to 18 px by CSS for print (content unchanged)."""
    d = RES / "controller_audit_v2" / "report"
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}"
            ".g{grid-template-columns:1150px;padding:6px 6px 14px 6px}.cell svg{border:0}</style></head><body>"
            f"<div class='g'><div class='cell big'>{svg_inline(d / 'timeline.svg')}</div></div></body></html>")
    (HTML_DIR / "audit_v2_timeline_repo.html").write_text(html)
    capture("audit_v2_timeline_repo.html", "audit_v2_timeline_repo", 1190)


if __name__ == "__main__":
    pilot_dir = RES / "pilot"
    pilot = pd.read_csv(pilot_dir / "trials.csv")
    rows = [("stationary<br>seed 0", pilot_dir, pilot, 0, 0, 0.0, 0.01)]
    rows += [(f"5 cm, 0.01 Hz<br>seed {s}", pilot_dir, pilot, 3, s, 5.0, 0.01) for s in range(5)]
    web_gallery(rows, "gallery_v1_pilot_A5_f001")
    rows = [(f"10 cm, 0.01 Hz<br>seed {s}", pilot_dir, pilot, 6, s, 10.0, 0.01) for s in range(5)]
    web_gallery(rows, "gallery_v1_pilot_A10_f001")
    for tag, d in (("v1", RES / "frequency_0049_vs_005"), ("v2", RES / "controller_audit_v2" / "verified_sweep")):
        tr = pd.read_csv(d / "trials.csv")
        rows = [(f"{tag}, 5 cm, 0.05 Hz<br>seed {s}", d, tr, 3, s, 5.0, 0.05) for s in range(5)]
        web_gallery(rows, f"gallery_{tag}_A5_f005")
    errors_gallery()
    timeline()
