"""Figures for the `record` section (project timeline, composition, claim ledger, evidence volume).

Inputs (all read-only):
  - REPO: the committed repository (CLAIMS.md, CSVs, mulder_results/, evidence JSONs)
  - HIST: history.csv written by repo_history.py (run that first, on the private clone)

    python make_figures.py
"""
import csv
import datetime as dt
import json
import os
import re
import sys

import numpy as np

W = "<WORKSPACE>"
sys.path.insert(0, os.path.join(W, "tools"))
from plotstyle import apply, save, C, FIG_WIDE, FIG_2PANEL  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
from matplotlib.patches import Rectangle, Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

REPO = os.path.join(W, "repo", "htn-biology")
HIST = os.path.join(W, "work", "record", "history", "history.csv")
OUT = os.path.join(W, "report", "figures", "record")
apply()


def d(s):
    return dt.datetime.fromisoformat(s[:19])


# --------------------------------------------------------------------------------------------
# 1. Timeline
# --------------------------------------------------------------------------------------------
def fig_timeline():
    rows = list(csv.DictReader(open(HIST)))
    by_sha = {r["sha"]: r for r in rows}
    # parent links from the clone (first/second parent)
    import subprocess
    clone = os.path.join(W, "work", "record", "repo")
    parents = {}
    for line in subprocess.check_output(["git", "-C", clone, "log", "--format=%h %p"], text=True).splitlines():
        p = line.split()
        parents[p[0]] = p[1:]
    feat_mulder = {"20e7015", "7e59389"}
    side = {"1e1bd44", "b6793d0", "9431a50", "60be973", "25fbb71", "94516e0", "114e39b", "4a5608e",
            "1bc1ef9", "39b89f3", "1c04157"}

    def branch(s):
        return "feat_mulder" if s in feat_mulder else ("spider-web-updated" if s in side else "main")

    BR = {"main": C["black"], "spider-web-updated": C["blue"], "feat_mulder": C["vermillion"]}
    authors = []
    for r in rows:
        if r["author"] not in authors:
            authors.append(r["author"])
    AUTH = {a: c for a, c in zip(authors, [C["blue"], C["green"], C["orange"]])}

    fig = plt.figure(figsize=(7.0, 5.6))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.55, 1, 1], hspace=0.12)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    cp2 = dt.datetime(2026, 9, 18, 22, 21)

    # --- event strip: one lane per author; same-day commits are stacked vertically within the lane
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[(r["author"], r["date"][:10])].append(r)
    for (a, day), rs in groups.items():
        i = authors.index(a)
        n = len(rs)
        for k, r in enumerate(sorted(rs, key=lambda r: r["date"])):
            yy = i + (k - (n - 1) / 2) * 0.2
            if r["n_parents"] == "2":
                ax0.scatter([d(r["date"])], [yy], s=20, facecolor="white", edgecolor=AUTH[a], linewidth=1.0, zorder=3)
            else:
                ax0.scatter([d(r["date"])], [yy], s=20, color=AUTH[a], zorder=3, edgecolor="white", linewidth=0.4)
    for i, a in enumerate(authors):
        n = sum(1 for r in rows if r["author"] == a)
        ax0.text(dt.datetime(2026, 7, 29), i, f"{a} ({n})", ha="right", va="center", fontsize=7.5, color=AUTH[a])
    ax0.set_yticks([])
    ax0.set_ylim(-0.75, 6.9)
    ax0.spines["left"].set_visible(False)
    ax0.grid(False)
    # work-log session band (uncommitted until 2026-10-27)
    for ax in (ax0, ax1, ax2):
        ax.axvspan(dt.datetime(2026, 10, 19), dt.datetime(2026, 10, 24, 23), color=C["vermillion"], alpha=0.10, lw=0)
        ax.axvline(cp2, color=C["grey"], ls="--", lw=0.9)
    ax0.text(cp2 + dt.timedelta(days=1), 6.75, "Checkpoint 2\n(2026-09-18)", ha="left", va="top", fontsize=7,
             color=C["grey"])
    # milestones: (date, label, y of label, x offset days)
    ms = [
        (dt.datetime(2026, 8, 4, 19), "Original HTN + FAP\n(first commit)", 3.1, 0),
        (dt.datetime(2026, 8, 30, 10), "A* planner", 4.7, -9),
        (dt.datetime(2026, 9, 4, 0), "Updated HTN: config,\ntests, stochasticity", 2.9, -2),
        (dt.datetime(2026, 9, 8, 9), "Flat baseline", 5.6, -4),
        (dt.datetime(2026, 9, 9, 19), "Sensitivity\nsweeps", 4.0, 3),
        (dt.datetime(2026, 10, 21, 12), "Work-log sessions:\nMulder v1–v4,\nrecovery v1", 4.3, -3),
        (dt.datetime(2026, 10, 27, 14), "Mulder + recovery\ncommitted; results\nsnapshot", 2.7, 2),
        (dt.datetime(2026, 11, 12, 14), "Literature review,\nresult files committed,\nadaptive planner\nrestored", 4.4, -1),
    ]
    for x, lab, y, off in ms:
        ax0.annotate(lab, xy=(x, 2.25), xytext=(x + dt.timedelta(days=off), y), fontsize=6.6, ha="center",
                     va="bottom", arrowprops=dict(arrowstyle="-", lw=0.5, color="#555555"))
    ax0.tick_params(axis="x", labelbottom=False)

    # --- DAG-drawn metrics
    def dag(ax, col, ylabel):
        for r in rows:
            for k, p in enumerate(parents.get(r["sha"], [])):
                if p in by_sha:
                    ax.plot([d(by_sha[p]["date"]), d(r["date"])], [float(by_sha[p][col]), float(r[col])],
                            color=BR[branch(r["sha"])], lw=0.8, ls="-" if k == 0 else ":", zorder=1)
        for r in rows:
            ax.scatter([d(r["date"])], [float(r[col])], s=16, color=BR[branch(r["sha"])], zorder=3,
                       edgecolor="white", linewidth=0.4)
        ax.set_ylabel(ylabel)

    dag(ax1, "project_py_lines", "Python lines\n(excl. vendored)")
    dag(ax2, "tests_total", "Tests collected\n(pytest)")
    ax1.set_ylim(0, 13500)
    ax2.set_ylim(-8, 200)
    ax1.tick_params(axis="x", labelbottom=False)
    head = rows[-1]
    cp = by_sha["c9144e6"]
    ax1.annotate(f"{int(cp['project_py_lines']):,}", (d(cp["date"]), float(cp["project_py_lines"])),
                 xytext=(-4, 6), textcoords="offset points", ha="right", fontsize=7)
    ax1.annotate(f"{int(head['project_py_lines']):,}", (d(head["date"]), float(head["project_py_lines"])),
                 xytext=(4, 2), textcoords="offset points", ha="left", fontsize=7)
    dm = by_sha["d2e639b"]
    ax1.annotate("d2e639b (main, data only)", (d(dm["date"]), float(dm["project_py_lines"])),
                 xytext=(-6, -2), textcoords="offset points", ha="right", va="top", fontsize=6.3, color="#444444")
    ax2.annotate(f"{cp['tests_total']}", (d(cp["date"]), float(cp["tests_total"])), xytext=(-4, 5),
                 textcoords="offset points", ha="right", fontsize=7)
    ax2.annotate(f"{head['tests_total']}", (d(head["date"]), float(head["tests_total"])), xytext=(4, 0),
                 textcoords="offset points", ha="left", va="center", fontsize=7)
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    ax2.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    ax2.set_xlim(dt.datetime(2026, 7, 28), dt.datetime(2026, 11, 20))
    ax2.set_xlabel("Commit date (author date, IST)")
    handles = [Line2D([], [], color=BR[b], marker="o", ms=4, lw=0.8, label=b) for b in BR]
    handles.append(Line2D([], [], color="#555555", ls=":", lw=0.8, label="second-parent (merge) link"))
    handles.append(Patch(color=C["vermillion"], alpha=0.15, label="work-log sessions, 19–24 Oct"))
    ax1.legend(handles=handles, loc="upper left", fontsize=6.6, ncol=1, handlelength=1.6)
    save(fig, os.path.join(OUT, "record_timeline"))


# --------------------------------------------------------------------------------------------
# 2. Repository composition
# --------------------------------------------------------------------------------------------
PKG_LABEL = [
    ("spider_web_htn", "spider_web_htn (original HTN)", False),
    ("spider_web_fap", "spider_web_fap (FAP)", False),
    ("spider_web_astar", "spider_web_astar (A*)", False),
    ("spider_web_htn_updated", "spider_web_htn_updated", False),
    ("spider_web_mulder", "spider_web_mulder", True),
    ("spider_web_recovery", "spider_web_recovery", True),
    ("docs/research/probes", "docs/research/probes", True),
    ("root_scripts", "root scripts (run*.py, visualize.py)", False),
]


def fig_composition():
    rows = list(csv.DictReader(open(HIST)))
    head, cp = rows[-1], [r for r in rows if r["sha"] == "c9144e6"][0]
    labels, src, tst, src0, tests, new = [], [], [], [], [], []
    for key, lab, isnew in PKG_LABEL:
        labels.append(lab + (" *" if isnew else ""))
        src.append(int(head[key + ":src"]))
        tst.append(int(head.get(key + ":testlines") or 0))
        src0.append(int(cp[key + ":src"]) + int(cp.get(key + ":testlines") or 0))
        tests.append(int(head.get("tests:" + key, 0) or 0))
        new.append(isnew)
    labels.append("third_party/IPyHOP (vendored) *")
    src.append(int(head["third_party_py_lines"]))
    tst.append(0)
    src0.append(0)
    tests.append(0)
    new.append(True)
    y = np.arange(len(labels))[::-1]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.3), gridspec_kw={"width_ratios": [2.3, 1]}, sharey=True)
    a.barh(y, src, color=[C["grey"] if "vendored" in l else C["blue"] for l in labels], height=0.62,
           label="source lines")
    a.barh(y, tst, left=src, color=C["sky"], height=0.62, label="test lines")
    keep = [k for k, v in enumerate(src0) if v > 0]
    a.scatter([src0[k] for k in keep], [y[k] for k in keep], marker="|", s=90, color=C["black"], zorder=4,
              label="total at Checkpoint 2 (c9144e6)")
    for yi, s_, t_ in zip(y, src, tst):
        a.text(s_ + t_ + 60, yi, f"{s_:,}" + (f" + {t_:,}" if t_ else ""), va="center", fontsize=7)
    a.set_yticks(y)
    a.set_yticklabels(labels, fontsize=7.5)
    a.set_xlabel("Python lines (wc -l) at HEAD 61d18d8")
    a.set_xlim(0, 5200)
    a.legend(loc="lower right", fontsize=7)
    a.grid(axis="y", visible=False)
    b.barh(y, tests, color=C["green"], height=0.62)
    for yi, t in zip(y, tests):
        b.text(t + 2 if t else 2, yi, str(t) if t else "no test suite", va="center", fontsize=7,
               color="black" if t else "#666666")
    b.set_xlabel("Tests collected (pytest)")
    b.set_xlim(0, 115)
    b.grid(axis="y", visible=False)
    fig.subplots_adjust(wspace=0.06)
    save(fig, os.path.join(OUT, "record_composition"))


# --------------------------------------------------------------------------------------------
# 3. Claim ledger summary
# --------------------------------------------------------------------------------------------
# Category assignment, with the status-column wording that justifies it (checked against CLAIMS.md).
CAT = {
    "S": ("Implemented / tested, supported", C["green"]),
    "N": ("Tested: not supported, contradicted or false", C["vermillion"]),
    "U": ("Not established / not implemented / unsupported without a test", C["orange"]),
    "X": ("Not claimed", C["grey"]),
}
ASSIGN = {
    "C01": ("S", "Implemented"), "C02": ("S", "Tested"), "C03": ("S", "Tested"), "C04": ("N", "Unsupported"),
    "C05": ("S", "Tested"), "C06": ("N", "Not supported"), "C07": ("N", "Not demonstrated"),
    "C08": ("N", "Not supported"), "C09": ("U", "Unsupported"), "C10": ("N", "Contradicted"),
    "C11": ("N", "Not supported"), "C12": ("U", "Not established"), "C13": ("N", "False"),
    "C14": ("U", "Not implemented"), "C15": ("U", "Not established"), "C16": ("S", "Implemented/tested"),
    "C17": ("U", "Not established"), "C18": ("S", "Tested"), "C19": ("S", "Tested"), "C20": ("S", "Tested"),
    "C21": ("N", "Unsupported"), "C22": ("S", "Implemented"), "C23": ("X", "Not claimed"),
    "C24": ("S", "Implemented/tested"), "C25": ("N", "Not supported"), "C26": ("N", "Contradicted"),
    "C27": ("S", "Tested"), "C28": ("U", "Not established"),
}
# Evidence source named in each ledger row (study/version), abbreviated for the strip.
SOURCE = {
    **{f"C{i:02d}": "M1–3" for i in (1, 2)},
    **{f"C{i:02d}": "M3" for i in range(3, 15)},
    "C15": "SA", "C16": "R1+M4", "C17": "all", "C18": "R1", "C19": "R1", "C20": "R1", "C21": "R1",
    "C22": "R1", "C23": "R1/M4", "C24": "M4", "C25": "M4", "C26": "M4", "C27": "M4", "C28": "AP",
}


def read_claims():
    out = []
    for line in open(os.path.join(REPO, "docs", "research", "CLAIMS.md"), encoding="utf-8"):
        m = re.match(r"\|\s*(C\d\d)\s*\|(.*)\|(.*)\|(.*)\|\s*$", line)
        if m:
            out.append([m.group(1)] + [x.strip() for x in m.groups()[1:]])
    return out


def fig_claims():
    claims = read_claims()
    assert [c[0] for c in claims] == [f"C{i:02d}" for i in range(1, 29)], "ledger IDs changed"
    for cid, stmt, status, perm in claims:
        cat, word = ASSIGN[cid]
        assert status.lower().startswith(word.lower()) or word.lower() in status.lower(), (cid, status)
    counts = {k: sum(1 for c in claims if ASSIGN[c[0]][0] == k) for k in CAT}
    fig = plt.figure(figsize=(7.0, 3.2))
    a = fig.add_axes([0.42, 0.56, 0.54, 0.42])
    keys = list(CAT)[::-1]
    a.barh(range(len(keys)), [counts[k] for k in keys], color=[CAT[k][1] for k in keys], height=0.6)
    for i, k in enumerate(keys):
        a.text(counts[k] + 0.15, i, str(counts[k]), va="center", fontsize=8)
    a.set_yticks(range(len(keys)))
    a.set_yticklabels([CAT[k][0] for k in keys], fontsize=7.5)
    a.set_xlabel(f"Number of ledger claims (n = {len(claims)})")
    a.set_xlim(0, 12.5)
    a.grid(axis="y", visible=False)
    b = fig.add_axes([0.075, 0.13, 0.92, 0.27])
    for i, (cid, *_rest) in enumerate(claims):
        cat = ASSIGN[cid][0]
        b.add_patch(Rectangle((i, 1), 0.92, 0.9, color=CAT[cat][1]))
        b.add_patch(Rectangle((i, 0), 0.92, 0.9, fc="#EEEEEE", ec="none"))
        b.text(i + 0.46, 1.45, cid, ha="center", va="center", fontsize=5.6, color="white", weight="bold")
        b.text(i + 0.46, 0.45, SOURCE[cid], ha="center", va="center", fontsize=5.6, rotation=90)
    b.set_xlim(-0.1, len(claims))
    b.set_ylim(-0.05, 1.95)
    b.set_yticks([0.45, 1.45])
    b.set_yticklabels(["evidence", "status"], fontsize=7.5)
    b.set_xticks([])
    for s in ("left", "bottom"):
        b.spines[s].set_visible(False)
    b.grid(False)
    b.set_xlabel("Claim C01–C28 (ledger order). Evidence: M1–3/M3/M4 = Mulder v1–v3/v3/v4, "
                 "R1 = recovery v1, SA = strategy audit,\nAP = adaptive planner, all = all packages", fontsize=7)
    save(fig, os.path.join(OUT, "record_claims"))
    return counts


# --------------------------------------------------------------------------------------------
# 4. Evidence volume
# --------------------------------------------------------------------------------------------
def trials_rows(rel):
    with open(os.path.join(REPO, rel)) as f:
        return sum(1 for _ in f) - 1


def nruns(rel):
    return sum(int(r["n_runs"]) for r in csv.DictReader(open(os.path.join(REPO, rel))))


def fig_evidence():
    st = {
        "cur": ("Curated evidence JSON (input hashes re-verified)", C["blue"]),
        "raw": ("Raw per-trial table, cited in work log", C["sky"]),
        "unc": ("Raw per-trial table, not cited in work log", "#BBBBBB"),
        "agg": ("Aggregate CSV only (pre-Checkpoint 2)", C["orange"]),
        "his": ("Aggregate CSV, historical/unaudited (C28)", C["vermillion"]),
    }
    suffix = json.load(open(os.path.join(REPO, "docs/research/evidence/mulder_suffix_control.json")))
    diag = ["mulder_results/controller_audit_v2/a5_f005_seed0/trials.csv",
            "mulder_results/controller_audit_v2/matched_trial/trials.csv",
            "mulder_results/controller_audit_v2/report/trials.csv",
            "mulder_results/diagnostics_a5_f005_seed0/trials.csv"]
    items = [
        ("HTN-upd. anchor-removal sweep", nruns("sensitivity_comparison.csv"), "agg", "sensitivity_comparison.csv"),
        ("HTN-upd. wind sweep", nruns("wind_sensitivity.csv"), "agg", "wind_sensitivity.csv"),
        ("HTN-upd. perturbation trials", nruns("perturbation_trials.csv"), "his", "perturbation_trials.csv"),
        ("Mulder v1 pilot", trials_rows("mulder_results/pilot/trials.csv"), "raw", ""),
        ("Mulder v1 0.049 vs 0.05 Hz", trials_rows("mulder_results/frequency_0049_vs_005/trials.csv"), "raw", ""),
        ("Mulder v2 frequency_comparison", trials_rows("mulder_results/controller_audit_v2/frequency_comparison/trials.csv"), "unc", ""),
        ("Mulder v2 verified_sweep", trials_rows("mulder_results/controller_audit_v2/verified_sweep/trials.csv"), "raw", ""),
        ("Mulder v2 matched diagnostic (report/)", trials_rows(diag[2]), "raw", ""),
        ("Other seed-0 diagnostic tables (3)", sum(trials_rows(p) for p in diag if p != diag[2]), "unc", ""),
        ("Mulder v3 paper validation", trials_rows("mulder_results/paper_validation_v3/trials.csv"), "cur", ""),
        ("Recovery v1 (earlier run)", trials_rows("mulder_results/recovery_v1/trials.csv"), "unc", ""),
        ("Recovery v1 verified", trials_rows("mulder_results/recovery_v1_verified/trials.csv"), "cur", ""),
        ("Mulder v4 re-entrant sweep", trials_rows("mulder_results/mulder_reentrant_v4/trials.csv"), "cur", ""),
        ("Mulder v4 suffix control", len(suffix["trials"]), "cur", ""),
    ]
    order = ["pilot", "frequency_0049_vs_005", "controller_audit_v2", "diagnostics_a5_f005_seed0",
             "paper_validation_v3", "paper_validation_v3_report", "recovery_v1", "recovery_v1_verified",
             "mulder_reentrant_v4"]
    resdirs = sorted(os.listdir(os.path.join(REPO, "mulder_results")))
    assert sorted(order) == resdirs, resdirs
    resdirs = order
    nfiles = []
    for rd in resdirs:
        n = 0
        for _r, _d, fs in os.walk(os.path.join(REPO, "mulder_results", rd)):
            n += len(fs)
        nfiles.append(n)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 4.3), gridspec_kw={"width_ratios": [1.6, 1]})
    y = np.arange(len(items))[::-1]
    a.barh(y, [it[1] for it in items], color=[st[it[2]][1] for it in items], height=0.65)
    for yi, it in zip(y, items):
        a.text(it[1] * 1.12, yi, f"{it[1]:,}", va="center", fontsize=7)
    a.set_xscale("log")
    a.set_xlim(5, 2e5)
    a.set_yticks(y)
    a.set_yticklabels([it[0] for it in items], fontsize=7)
    a.set_xlabel("Simulated trials (log scale)")
    a.grid(axis="y", visible=False)
    fig.legend(handles=[Patch(color=v[1], label=v[0]) for v in st.values()], fontsize=7, loc="lower center",
               ncol=2, bbox_to_anchor=(0.5, -0.01))
    yb = np.arange(len(resdirs))[::-1]
    b.barh(yb, nfiles, color=C["sky"], height=0.65)
    for yi, n in zip(yb, nfiles):
        b.text(n + 10, yi, str(n), va="center", fontsize=7)
    b.set_yticks(yb)
    b.set_yticklabels(resdirs, fontsize=7)
    b.set_xlabel(f"Files (total {sum(nfiles):,})")
    b.set_ylabel("mulder_results/ subdirectory")
    b.set_xlim(0, 980)
    b.grid(axis="y", visible=False)
    fig.subplots_adjust(wspace=1.05, bottom=0.25)
    save(fig, os.path.join(OUT, "record_evidence_volume"))
    return items, dict(zip(resdirs, nfiles))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig_timeline()
    fig_composition()
    print("claims", fig_claims())
    items, nf = fig_evidence()
    print(items)
    print(nf)
