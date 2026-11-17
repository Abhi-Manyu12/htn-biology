# Figures — domain `core` (original + config-driven "updated" HTN model)

All paths below: `W/report/scripts/core/` for scripts, repo = `W/repo/htn-biology` (commit 61d18d8),
derived = `W/work/core/derived/` (outputs of our own re-runs in private checkouts: `W/work/core/repo` = clone at
61d18d8, `W/work/core/repo_39b89f3` = git worktree at 39b89f3, the commit that produced the committed sweep CSVs).
Every figure exists as `<stem>.pdf` and `<stem>.png`. Run scripts from `W/report/scripts/core` with
`W/.venv/bin/python`.

| Stem | Script | Source data | What it shows | n |
|---|---|---|---|---|
| `web_final_three_plans` | `fig_webs.py` | repo `visualization/plan_data.js`, `visualization/plan_data_updated.js`; derived `plan_checkpoint2_39b89f3.json` (from `export_plan.py` at 39b89f3, stochastic disabled) | Final simulated web of (i) the plan whose numbers the Checkpoint 2 report quotes (updated package at 39b89f3: 71 actions, 600.1 cm), (ii) the original package `spider_web_htn` (128 actions, 751.6 cm), (iii) the current updated package (105 actions, 701.6 cm); threads coloured by `THREAD_COLORS`, rig in light grey, equal aspect | 1 deterministic plan each |
| `web_buildup_updated` | `fig_webs.py` | repo `visualization/plan_data_updated.js` | Updated plan's web after the last action of each macro phase (steps 10, 25, 36, 52, 74, 104) with cumulative energy | 1 plan |
| `ui_original_final` | `capture_ui.sh` (+ `ui_goto_last.js`) | repo `visualization/index.html` + `plan_data.js` | Screenshot of the repo's interactive visualiser driven to its final step (128/128, 752 cm, 90 threads) | 1 |
| `ui_updated_final` | `capture_ui.sh` (+ `ui_goto_last.js`) | repo `visualization/index_updated.html` + `plan_data_updated.js` | Same for the updated page (105/105, 702 cm); at completion the page hides the auxiliary spiral and draws plain silk | 1 |
| `ui_updated_precomplete` | `capture_ui.sh` (+ `ui_goto_before_complete.js`) | as above | Updated page at step 104 (`mark_capture_spiral_done`), still colour-coded, auxiliary spiral visible | 1 |
| `energy_cumulative` | `fig_energy.py` | derived `plan_updated_61d18d8.json`, `plan_original_61d18d8.json`, `plan_checkpoint2_39b89f3.json` (action sequences asserted identical to the committed `plan_data*.js`) | (a) cumulative locomotory energy vs action index for the updated plan, shaded by macro phase (redo of Checkpoint 2 Fig. 2); (b) the three plans overlaid | 1 plan each |
| `energy_per_phase` | `fig_energy.py` | same | Actions and energy per macro phase, three plans side by side | 1 plan each |
| `spiral_geometry` | `fig_spiral.py` | `spider_web_htn_updated/spiral_geometry.py` + `config.yaml` (imported from the private clone at 61d18d8); derived `spiral_fraction_sweep_61d18d8.json` (`rerun_spiral_fraction.py`) | (a) auxiliary (log) and capture (Archimedean) waypoints in the plane; (b) r/r_T vs rotations; (c) radial gap between successive loops per direction vs config `empirical.mesh_size_mm`; (d) plan and spiral-phase energy vs `start_radius_fraction` (our sweep, 10 values) | 20 + 28 waypoints; 10 sweep points |
| `sens_anchor_success` | `fig_sensitivity.py` | repo `sensitivity_comparison.csv`; derived `htn_success_audit_39b89f3.json` (`rerun_htn_success_audit.py`) | (a) success rate vs anchor-removal p, HTN vs baseline, Wilson 95% CI, with 1−p^8; (b) our audit of the HTN successes: share of plans that lay all 8 radii and mean radii laid | 1000 per group per p (9 values) |
| `sens_anchor_energy` | `fig_sensitivity.py` | repo `sensitivity_comparison.csv` | Energy of successful runs vs p (mean, ±SD band, median) per group, and baseline/HTN ratios of means and medians | 1000 trials per group per p (successful runs only) |
| `wind_sensitivity` | `fig_wind.py` | repo `wind_sensitivity.csv` | Every metric vs wind σ for both groups: success (Wilson CI), HTN energy (mean ±SD, median, analytic clamp expectation), SD of energy (log), baseline mean/median | 1000 per group per σ (9 values), p = 0 |
| `compare_summary` | `fig_compare.py` | repo `single_run_comparison.csv`; derived `rerun61_compare_n300_hash0.json`, `rerun{39,61}_compare_n30_hash{0..9}.json` (`rerun_compare.py` via `rerun_checks.sh compare`) | (a) HTN vs baseline energy and action counts, log scale (committed CSV and our 300-seed re-run, ±SD); (b) 30-seed baseline mean ± SD under 10 values of PYTHONHASHSEED at both commits, with the Checkpoint 2 Table 5 value | 300 seeds; 10 × 30 seeds per commit |
| `compare_distributions` | `fig_compare.py` | derived `rerun61_compare_n300_hash0.json` | Per-seed baseline energy and step-count histograms (log x) with the deterministic HTN value | 299 successful of 300 seeds |
| `perturbation_trials_historical` | `fig_perturbation.py` | repo `perturbation_trials.csv` (restored, historical, unaudited — claim C28); derived `rerun61_perturbation_trials.csv` (`rerun_checks.sh pert`) | Success rate (Wilson CI over triggered trials), mean energy, adaptation time ±SD for three perturbations; restored CSV (filled) vs our default-settings re-run (open) | 200 per group per perturbation |
| `tests_per_file` | `fig_tests.py` | derived `pytest_39b89f3.xml`, `pytest_61d18d8.xml` (pytest junit output in private checkouts) | Tests per file in `spider_web_htn_updated/tests` at both commits | 55 / 56 tests |

Supporting scripts (no figure of their own): `_common.py` (loaders, replay, Wilson interval), `export_plan.py`
(plan export with unrounded per-step energies), `rerun_checks.sh` (sensitivity/wind reproduction checks,
compare.py re-runs, perturbation re-run), `rerun_compare.py`, `rerun_htn_success_audit.py`,
`rerun_spiral_fraction.py`, `rerun_protohub_variants.py` (counts drop/Tarzan actions in plans; numbers quoted in the text, no figure), `png_to_pdf.py` (the three `ui_*` PDFs wrap the PNG screenshot, because Chrome's print-to-PDF draws the page's gradient title with an outline box).
