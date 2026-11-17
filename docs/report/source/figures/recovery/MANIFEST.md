# Figure manifest: `recovery` domain

All paths to data are relative to the repository root `W/repo/htn-biology` (commit `61d18d8`). Scripts are in
`W/report/scripts/recovery/`; run each with `"$W/.venv/bin/python" <script>` from that directory (the `.sh`
needs `node` + Chrome via `W/tools/shot.mjs`). No figure uses re-run simulation data; every value comes from
the committed result files listed. `check_recovery_runs.py` prints the consistency checks quoted in the text
(output saved in `W/work/recovery/check_output.txt`).

| Stem | Script | Source data | What it shows | n |
|---|---|---|---|---|
| `tree_manuscript_initial` | `convert_tree_svgs.sh` | `docs/manuscript/figures/recovery_v1_tree_initial.svg` (byte-identical to `mulder_results/recovery_v1_verified/traces/case1_permanent_anchor_ipyhop/tree_0.svg`) | Repo's own rendering of the initial upstream IPyHOP solution tree (4 sectors, depth 0, 10 cm, seed 0, permanent_anchor). Breadth-first layout, node labels are tiny at print width; colour: blue = tag old, orange-brown = any other tag (incl. root) | 1 tree, 52 nodes |
| `tree_manuscript_replanned` | `convert_tree_svgs.sh` | `docs/manuscript/figures/recovery_v1_tree_replanned.svg` (= `.../tree_1.svg`) | Same, after `replan(observed state, failed node 31)` | 1 tree, 52 nodes |
| `tree_example_before_after` | `fig_trees.py` | `docs/research/evidence/recovery_example/trees.json`, `events.json` | Legible redraw of the same two trees: executed leaves, failed leaf 31 (attach A3), un-refined suffix, old/new tags, method switch at `build_radius 3` (primary -> backup) | 2 trees |
| `tree_gallery` | `fig_trees.py` | `mulder_results/recovery_v1_verified/traces/case1_<scenario>_ipyhop/{trees,events}.json` for all 7 scenarios | Initial tree and tree after re-entry, one case per scenario (4 sectors, depth 0, 10 cm, seed 0, retained IPyHOP); clean/transient have no re-entry; silk_depletion/unreachable collapse to the root | 7 cases, 12 trees |
| `rec_outcome_matrix` | `fig_recovery_v1.py` | `mulder_results/recovery_v1_verified/trials.csv` | Completed/trials with Wilson 95% CI, mean re-planning calls, mean stale-precondition detections; scenario x back-end, pooled over 8 strata | 80 trials per cell, 2,240 total |
| `rec_planning_effort` | `fig_recovery_v1.py` | same `trials.csv` | Method calls and planning wall time per trial, all four back-ends; stratum 8 sectors / depth 2 / 10 cm; mean +- SD | 10 seeds per bar |
| `rec_paired_effort` | `fig_recovery_v1.py` | `mulder_results/recovery_v1_verified/paired.json` | Retained minus fresh IPyHOP (same engine) method calls, IPyHOP iterations, planning wall time; mean and pointwise paired-bootstrap 95% CI (2,000 reps, seed 20261020, as computed by the repo) for all 56 scenario x stratum cells; wall-time axis clipped at -10 ms | 10 paired seeds per point |
| `rec_execution_outcomes` | `fig_recovery_v1.py` | same `trials.csv` | Travel, silk used, elapsed time, re-planning calls, stale preconditions, retraced distance; stratum 8/2/10; mean +- SD (no bar when SD = 0) | 10 seeds per bar |
| `rec_event_timeline` | `fig_event_timeline.py` | `docs/research/evidence/recovery_example/events.json`; `mulder_results/recovery_v1_verified/traces/case1_permanent_anchor_<backend>/events.json` | Action ledger of the worked example on the simulated clock (owners R0-R3, C0-C3), silk remaining, the replan event; and the last 35 s of the same case for all four back-ends (component shows two stale-precondition rejections and two extra re-plans) | 1 case x 4 back-ends |
| `v4_completion` | `fig_mulder_v4.py` | `mulder_results/mulder_reentrant_v4/trials.csv` | Completion count (of 10 seeds) per profile x policy x back-end (legacy / fresh IPyHOP / retained IPyHOP), both construction sizes | 2,160 trials, 10 per cell |
| `v4_pair_differences` | `fig_mulder_v4.py` | same `trials.csv` | Per-pair retained minus fresh IPyHOP differences: five physical outcomes (all exactly 0), method calls (symlog), planning wall time | 720 matched pairs |
| `v4_calls_vs_time` | `fig_mulder_v4.py` | `mulder_results/mulder_reentrant_v4/paired.json`, `trials.csv` (fresh means for normalisation) | For the 32 size x profile x policy cells where retention changed method calls: relative change in method calls vs relative change in planning wall time, with the repo's paired bootstrap 95% CIs; one off-scale cell annotated | 32 cells x 10 pairs |
| `v4_lag_control` | `fig_mulder_v4.py` | `mulder_results/mulder_reentrant_v4/trials.csv`; `docs/research/evidence/mulder_suffix_control.json` | 1 s lag, filtered policy: completion with Wilson 95% CI (small: L/F/R; configured: L/F/R and GTPyhop whole-suffix control C), per-seed outcomes and completed actions, planning wall time (mean +- SD over the 10 runs, failures included) | 10 per bar; 70 v4 trials + 10 control trials |

Intermediate (not shipped): `W/work/recovery/raw_trees/*.png` are headless-Chrome renders of the other
case-1 `tree_k.svg` files; at print width their labels are unreadable and edges cross (breadth-first layout),
so the gallery is redrawn from `trees.json` instead (`tree_gallery`). `W/work/recovery/v4_calls_vs_time_cells.csv`
holds the 32 plotted cells.
