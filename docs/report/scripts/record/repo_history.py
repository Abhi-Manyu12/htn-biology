"""Measure every commit's tree: Python source lines per package and pytest-collected tests.

Run against the PRIVATE clone (W/work/record/repo), never the read-only repo:

    python repo_history.py <clone> <out_dir>

Writes <out_dir>/history.csv (one row per commit) and <out_dir>/packages_head.csv (HEAD composition).
Each commit is exported with `git archive` into <out_dir>/trees/<sha>; tests are collected with
`python -m pytest --collect-only -q` on whichever tests/ directories exist in that tree.
Source lines = `wc -l`-equivalent newline counts of tracked *.py files outside tests/.
Vendored third_party/ and generated mulder_results/ are excluded from the project total and
reported separately.
"""
import csv
import os
import re
import shutil
import subprocess
import sys

clone, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
PY = sys.executable

PACKAGES = [
    "spider_web_htn", "spider_web_fap", "spider_web_astar", "spider_web_htn_updated",
    "spider_web_mulder", "spider_web_recovery", "docs/research/probes",
]
TEST_DIRS = ["spider_web_htn_updated/tests", "spider_web_mulder/tests", "spider_web_recovery/tests"]


def git(*a):
    return subprocess.check_output(["git", "-C", clone, *a], text=True)


def nlines(path):
    with open(path, "rb") as f:
        return f.read().count(b"\n")


def measure(tree, files):
    row = {}
    total = 0
    for p in PACKAGES:
        src = [f for f in files if f.startswith(p + "/") and f.endswith(".py") and "/tests/" not in f]
        tst = [f for f in files if f.startswith(p + "/") and f.endswith(".py") and "/tests/" in f]
        s = sum(nlines(os.path.join(tree, f)) for f in src)
        t = sum(nlines(os.path.join(tree, f)) for f in tst)
        row[p + ":src"] = s
        row[p + ":testlines"] = t
        total += s + t
    root_py = [f for f in files if "/" not in f and f.endswith(".py")]
    rs = sum(nlines(os.path.join(tree, f)) for f in root_py) + sum(
        nlines(os.path.join(tree, f)) for f in files if f.startswith("visualization/") and f.endswith(".py"))
    row["root_scripts:src"] = rs
    total += rs
    row["project_py_lines"] = total
    row["third_party_py_lines"] = sum(
        nlines(os.path.join(tree, f)) for f in files if f.startswith("third_party/") and f.endswith(".py"))
    tests = {}
    for d in TEST_DIRS:
        if not os.path.isdir(os.path.join(tree, d)):
            tests[d] = 0
            continue
        r = subprocess.run([PY, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", d],
                           cwd=tree, capture_output=True, text=True)
        m = re.search(r"(\d+) tests? collected", r.stdout + r.stderr)
        tests[d] = int(m.group(1)) if m else -1
        if not m:
            print("COLLECTION FAILED", tree, d, (r.stdout + r.stderr)[-400:])
    for d, n in tests.items():
        row["tests:" + d.split("/")[0]] = n
    row["tests_total"] = sum(max(n, 0) for n in tests.values())
    return row


log = git("log", "--reverse", "--date=iso-strict", "--format=%H|%h|%ad|%an|%P|%s").strip().splitlines()
rows = []
for line in log:
    full, short, date, author, parents, subject = line.split("|", 5)
    tree = os.path.join(out, "trees", short)
    if not os.path.isdir(tree):
        os.makedirs(tree)
        # exclude the huge generated result folder from extraction (not needed for code metrics)
        arch = subprocess.Popen(["git", "-C", clone, "archive", full], stdout=subprocess.PIPE)
        subprocess.check_call(["tar", "-x", "-C", tree, "--exclude", "mulder_results"], stdin=arch.stdout)
        arch.wait()
    files = git("ls-tree", "-r", "--name-only", full).splitlines()
    files_nores = [f for f in files if not f.startswith("mulder_results/")]
    stat = git("show", "--shortstat", "--format=", full).strip()
    ins = re.search(r"(\d+) insertion", stat)
    row = {"sha": short, "date": date, "author": author, "n_parents": len(parents.split()),
           "subject": subject, "tracked_files": len(files), "insertions": int(ins.group(1)) if ins else 0,
           "result_files": len(files) - len(files_nores)}
    row.update(measure(tree, files_nores))
    rows.append(row)
    print(short, date[:10], row["project_py_lines"], row["tests_total"])

with open(os.path.join(out, "history.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[-1].keys()))
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in rows[-1].keys()})
shutil.rmtree(os.path.join(out, "trees"))
