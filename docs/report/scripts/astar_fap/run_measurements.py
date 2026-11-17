#!/usr/bin/env python3
"""run_measurements.py -- every planner run used in the astar_fap section.

Creates (if missing) two private copies of the repo under W/work/astar_fap/:
    repo/           clone of the read-only repo at 61d18d8 (HEAD)
    repo_1e1bd44/   worktree at 1e1bd44 (2026-08-30, "Add spider web A* implementation")
and runs planner_worker.py in subprocesses (2 lanes; the h=0 A* runs use ~3 GB each).
Results: W/work/astar_fap/data/runs.jsonl (one JSON record per run, with a "tag").

    python run_measurements.py            # all runs (~15 min)
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

W = "<WORKSPACE>"
PY = os.path.join(W, ".venv/bin/python")
HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, "planner_worker.py")
BASE = os.path.join(W, "work/astar_fap")
HEAD = os.path.join(BASE, "repo")
OLD = os.path.join(BASE, "repo_1e1bd44")
OUT = os.path.join(BASE, "data/runs.jsonl")


def ensure_repos():
    if not os.path.isdir(HEAD):
        subprocess.check_call(["git", "clone", "-q", os.path.join(W, "repo/htn-biology"), HEAD])
    if not os.path.isdir(OLD):
        subprocess.check_call(["git", "-C", HEAD, "worktree", "add", "-q", OLD, "1e1bd44"])


def job(tag, repo, which, *extra, seed=0):
    return (tag, repo, which, list(extra), seed)


def run(j):
    tag, repo, which, extra, seed = j
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    cmd = [PY, WORKER, "--repo", repo, which, *extra]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    line = [l for l in p.stdout.splitlines() if l.startswith("@@JSON@@")]
    if not line:
        rec = {"error": p.stderr[-2000:]}
    else:
        rec = json.loads(line[0][8:])
    rec.update({"tag": tag, "repo_commit": "1e1bd44" if repo == OLD else "61d18d8",
                "pythonhashseed": seed, "cmd": " ".join(cmd[2:])})
    print(tag, rec.get("success"), rec.get("nodes_expanded"), rec.get("energy"), flush=True)
    return rec


def main():
    ensure_repos()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    jobs = []
    # comparison planners at HEAD
    jobs += [job("htn", HEAD, "htn", "--reps", "20"),
             job("htn_updated", HEAD, "htn_updated", "--reps", "20"),
             job("fap", HEAD, "fap", "--reps", "20")]
    for pert in ["start_top_right", "start_hub", "y_frame_prebuilt"]:
        for strat in [None, "iterative_dfs_backtracking"]:
            ex = ["--reps", "3", "--perturb", pert] + (["--strategy", strat] if strat else [])
            jobs.append(job(f"fap_perturb:{pert}:{strat or 'default'}", HEAD, "fap", *ex))
    # A* as committed on 2026-08-30 (heuristic evaluates every distance as the 2.0 fallback)
    jobs.append(job("astar_old_trace", OLD, "astar", "--weight", "3", "--time", "120",
                    "--trace", "--trace-every", "1"))
    for seed in range(10):
        jobs.append(job("astar_old_seed", OLD, "astar", "--weight", "3", "--time", "120", seed=seed))
    for w in ["1", "1.5", "2", "3", "5", "10"]:
        jobs.append(job("astar_old_weight", OLD, "astar", "--weight", w, "--time", "120"))
    for k in range(1, 9):
        jobs.append(job("astar_old_k", OLD, "astar", "--weight", "3", "--time", "120", "--k", str(k)))
    # A* at HEAD as committed (heuristic is identically 0) -- the repo's default budget
    jobs.append(job("astar_head_default", HEAD, "astar", "--weight", "3", "--time", "120",
                    "--max-nodes", "200000", "--trace", "--trace-every", "25"))
    for k in [1, 2, 3]:
        jobs.append(job("astar_head_k", HEAD, "astar", "--weight", "3", "--time", "60", "--k", str(k)))
    # A* at HEAD with our one-line heuristic repair (distances on coordinates), NOT repo code
    for w in ["1", "3", "5"]:
        jobs.append(job("astar_hfix_weight", HEAD, "astar", "--weight", w, "--time", "60", "--hfix"))
    for k in [1, 2, 3, 4, 6, 8]:
        jobs.append(job("astar_hfix_k", HEAD, "astar", "--weight", "3", "--time", "60", "--k", str(k), "--hfix"))

    with ThreadPoolExecutor(max_workers=2) as ex:
        recs = list(ex.map(run, jobs))
    with open(OUT, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    print("wrote", OUT, len(recs))


if __name__ == "__main__":
    sys.exit(main())
