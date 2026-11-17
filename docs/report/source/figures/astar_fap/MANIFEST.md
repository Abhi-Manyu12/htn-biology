# Figure manifest — astar_fap

All scripts live in `W/report/scripts/astar_fap/`. "runs.jsonl" means
`W/work/astar_fap/data/runs.jsonl`, written by `run_measurements.py` (which calls
`planner_worker.py` in subprocesses) from two private copies of the repo:
`W/work/astar_fap/repo` (clone at 61d18d8 = HEAD) and `W/work/astar_fap/repo_1e1bd44`
(worktree at 1e1bd44, the commit that added `spider_web_astar/`, 2026-08-30).
Regenerate everything with:

    python run_measurements.py          # ~15 min, 2 lanes, writes runs.jsonl
    python astar_witness.py --repo <repo_1e1bd44 | repo> [--hfix] > W/work/astar_fap/data/witness_*.json
    python fig_astar_web.py; python fig_webs.py; python fig_astar_search.py; python fig_compare.py
    sh capture_ui.sh

| Stem | Script | Source data | What it shows | n |
|---|---|---|---|---|
| `astar_web_final` | `fig_astar_web.py` | repo `visualization/plan_data_astar.js` (replayed through `spider_web_htn/operators.py`) | Final web of the committed A* plan; inset zooms on the 3 cm edge right_stick_top–anchor_right_upper that carries 4 proto-radii, 4 radii and 1 frame thread (parallel copies drawn offset; ×m = multiplicity) | 1 plan, 26 actions, 18 threads |
| `astar_web_buildup` | `fig_astar_web.py` | same | Web after steps 9, 17, 21, 26 with cumulative cost | 1 plan |
| `ui_astar_final` | `capture_ui.sh` (headless Chrome via `tools/shot.mjs`) | repo `visualization/index_astar.html` + `visualization/plan_data_astar.js` | Screenshot of the repo's own A* viewer jumped to its last step (26/26) | 1 plan |
| `fap_web_final` | `fig_webs.py` | runs.jsonl tag `fap` (spider_web_fap at 61d18d8, our run) | Final FAP web: Y-frame, 8 radii, capture spiral, stabilimentum, remaining auxiliary segment; recycled auxiliary segments dashed | 1 plan, 61 actions |
| `webs_four_planners` | `fig_webs.py` | runs.jsonl tags `htn`, `htn_updated`, `fap`; repo `visualization/plan_data_astar.js` | Final webs of original HTN, updated HTN, A*, FAP at identical scale | 1 plan each |
| `astar_search_path` | `fig_astar_search.py` | runs.jsonl tags `astar_old_trace` (1e1bd44, w=3, every heap pop logged) and `astar_head_default` (61d18d8, w=3, 120 s / 200k budget, every 25th pop) | (a) g, h, f = g+3h and remaining plan cost along the returned plan; (b) f of popped heap entries vs pop index | 1 run each |
| `astar_scaling` | `fig_astar_search.py` | runs.jsonl tags `astar_old_k`, `astar_hfix_k`, `astar_head_k`, `astar_old_weight`, `astar_hfix_weight` | (a) states expanded vs goal size k (min_radii = min_capture_spiral = k); (b) states expanded and plan cost vs weight w; open markers = no plan within the time budget | 1 run per point (deterministic for PYTHONHASHSEED=0) |
| `compare_cumcost` | `fig_compare.py` | repo `visualization/plan_data.js`, `plan_data_updated.js`, `plan_data_astar.js`; runs.jsonl tag `fap` | Cumulative locomotory cost vs action index for the four planners | 1 plan each |
| `compare_bars` | `fig_compare.py` | runs.jsonl tags `htn`, `htn_updated`, `fap` (20 timed repetitions each), `astar_old_seed` (10 processes, PYTHONHASHSEED 0–9), `astar_head_default` | Plan length, cost, planning wall time (bar = median, whisker = min–max) | 20 / 20 / 10 / 20 timings |

Witness files (no figure): `W/work/astar_fap/data/witness_1e1bd44.json`, `witness_head.json`,
`witness_head_hfix.json` from `astar_witness.py` — a generator-validated 33-action plan of cost
71.70 cm and a reachable state where h > h* (inadmissibility).
