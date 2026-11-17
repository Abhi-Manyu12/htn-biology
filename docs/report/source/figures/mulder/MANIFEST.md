# Figure manifest — domain `mulder` (moving-support benchmark, spider_web_mulder)

All source paths are relative to the read-only repo `W/repo/htn-biology` (commit 61d18d8). Scripts live in
`W/report/scripts/mulder/`; run them from that directory with `W/.venv/bin/python <script>` (galleries and
SVG conversions need Node + Chrome via `W/tools/shot.mjs`). Every figure exists as `<stem>.pdf` and `<stem>.png`.

Model versions are never pooled: **v1** = `pilot`, `frequency_0049_vs_005` (metadata `model_version: 1`);
**v2** = `controller_audit_v2/*`, `diagnostics_a5_f005_seed0` (`model_version: 2`); **v3** = `paper_validation_v3`
(= `paper_validation_v3_report`; trials.csv and comparisons.csv are byte-identical).

| Stem | Script | Source data | What it shows | n |
|---|---|---|---|---|
| repo_v3_completion | capture_repo_svgs.sh | docs/manuscript/figures/mulder_v3_completion.svg | Repo's own manuscript figure, converted unchanged: completion at 0.05 Hz by executor/policy (v3) | 30 per cell |
| repo_v3_paired_effects | capture_repo_svgs.sh | docs/manuscript/figures/mulder_v3_paired_effects.svg | Repo's own manuscript figure: paired moving−stationary % change, duration and 10 s-sampled travel, 10 cm/0.05 Hz (v3) | 30 pairs |
| v3_completion | fig_v3.py | mulder_results/paper_validation_v3/trials.csv | Regenerated completion heatmap, all five conditions incl. 0.049 Hz, k/n annotated | 30 per cell |
| v3_completion_wilson | fig_v3.py | paper_validation_v3/trials.csv | Completion rate with Wilson 95% intervals, moving conditions, endpoint vs tracking | 30 per point |
| v3_endpoint_progress | fig_v3.py | paper_validation_v3/trials.csv (profile endpoint) | Accepted actions (of 218) per trial under endpoint execution; bars = median | 30 per policy/condition |
| v3_paired_effects | fig_v3.py | paper_validation_v3/comparisons.csv (profile tracking) | Paired moving−stationary % change (duration, sampled travel) for 5 policies × 4 conditions, paired-bootstrap 95% CI | 30 pairs each |
| v3_paired_effects_primary | fig_v3.py | paper_validation_v3/comparisons.csv | Shared-style regeneration of the repo's paired-effects figure (local/full/predictive, 10 cm, 0.05 Hz) | 30 pairs |
| v3_phase_allocation | fig_v3.py | paper_validation_v3/comparisons.csv | Paired change in share of construction time (radii/auxiliary/capture), percentage points, 95% CI | 30 pairs |
| v3_cost_distributions | fig_v3.py | paper_validation_v3/trials.csv (tracking) | Per-trial time, sampled travel, repairs, planning calls, method calls, planning wall time; stationary vs 10 cm/0.05 Hz | 30 + 30 per policy (fixed moving: 0 completed) |
| v3_sensitivity | fig_v3.py | paper_validation_v3/trials.csv, comparisons.csv | Completion (Wilson) and duration change (bootstrap CI) for all 11 tracking-based profiles at 10 cm/0.05 Hz | 30 (tracking) or 12 per profile/controller |
| v3_sensor_lag | fig_v3.py | paper_validation_v3/trials.csv | C10: accepted actions per trial at sensory lag 0 (tracking, seeds 0–11), 1 s, 5 s; failure reasons | 12 per controller per lag |
| v3_phase_wait | fig_v3.py | paper_validation_v3/trials.csv, comparisons.csv | C11: per-seed phase_wait − tracking_slow duration and time spent waiting; slow-profile moving−stationary differences; waits per trial | 12 matched seeds |
| v3_flat_vs_htn | fig_v3.py | paper_validation_v3/trials.csv, comparisons.csv | C06: per-seed flat − HTN duration (all exactly 0) and moving−stationary % for HTN vs flat | 12 matched seeds; 30/12 pairs |
| v3_geometry_vs_paper | fig_v3.py | paper_validation_v3/comparisons.csv; spider_web_mulder/paper_reference.json | C09/C12: model paired differences for the 11 measures with a published p-value, the paper's p-values, and imposed/predicted status. No biological means exist in the repo. | 30 pairs |
| v1_pilot_completion | fig_v1_v2.py | mulder_results/pilot/trials.csv | v1 pilot completion per policy over amplitude × frequency (k/5) | 5 per cell |
| v1_pilot_progress | fig_v1_v2.py | pilot/trials.csv | v1 accepted actions per trial, six moving conditions | 5 per policy/condition |
| v1_pilot_costs | fig_v1_v2.py | pilot/trials.csv | v1 completed-trial costs (time, normalised travel, repairs, planning calls, mean error, planning wall time): stationary vs 0.01 Hz | 15 stationary (3 freq × 5, identical runs) + 5 + 5 per policy |
| freq_0049_vs_005 | fig_v1_v2.py | frequency_0049_vs_005/trials.csv (v1); controller_audit_v2/verified_sweep/trials.csv (v2); paper_validation_v3/trials.csv (v3 endpoint) | Per-seed accepted actions at 5 cm, 0.049 vs 0.05 Hz, lines join the same seed; "a\|b" = completions | 5 (v1, v2) / 30 (v3) per policy per freq |
| v1_vs_v2_progress | fig_v1_v2.py | frequency_0049_vs_005/trials.csv, controller_audit_v2/verified_sweep/trials.csv | Same seed/condition accepted actions, v1 vs v2 (effect of the audit corrections) | 60 trials per panel |
| v1_webs_six_policies | fig_traces.py | pilot/trace_6_0_<policy>.json, pilot/trace_4_0_<policy>.json, pilot/trials.csv | Own drawing: accepted silk chords (material coordinates) and missed-attempt endpoints; 10 cm/0.01 Hz and 5 cm/0.05 Hz, seed 0 | 12 trials |
| v1_trial_timeseries | fig_traces.py | same traces + pilot/trials.csv (initial phase) | Bottom-edge displacement, cumulative accepted actions, per-attempt attachment error vs time | 12 trials |
| v1_world_snapshots | fig_traces.py | pilot/trace_6_0_local_repair.json, pilot/trials.csv | Own drawing: the same completed web in room coordinates at 4 times (affine shear applied) | 1 trial |
| audit_v2_replays | fig_audit.py | controller_audit_v2/report/replays.csv | Six isolated replays of each controller's first missed action: accepted/missed and final error | 36 replays |
| audit_v2_attempts | fig_audit.py | controller_audit_v2/report/ledger.csv, trials.csv | Every attempt (final error, error before correction) and every repair by reason, per controller | 41 attempts, 26 repairs |
| audit_v2_timeline_repo | build_galleries.py | controller_audit_v2/report/timeline.svg | Repo's controller timeline (green accepted, red missed, purple repair) and frame motion; SVG text enlarged to 20 px by CSS for print | 6 trials |
| audit_v2_errors_repo | build_galleries.py | controller_audit_v2/report/errors_<policy>.svg | Repo's per-controller attachment-error-by-attempt plots, stacked in one labelled column; SVG text enlarged to 20 px by CSS | 6 trials |
| gallery_v1_pilot_A5_f001 | build_galleries.py | pilot/trace_0_0_*.svg, pilot/trace_3_<seed>_*.svg, pilot/trials.csv | Repo SVG webs: stationary seed 0 + all 5 seeds at 5 cm, 0.01 Hz | 36 trials |
| gallery_v1_pilot_A10_f001 | build_galleries.py | pilot/trace_6_<seed>_*.svg | Repo SVG webs: all 5 seeds at 10 cm, 0.01 Hz | 30 trials |
| gallery_v1_A5_f005 | build_galleries.py | frequency_0049_vs_005/trace_3_<seed>_*.svg | Repo SVG webs, v1: all 5 seeds at 5 cm, 0.05 Hz | 30 trials |
| gallery_v2_A5_f005 | build_galleries.py | controller_audit_v2/verified_sweep/trace_3_<seed>_*.svg | Repo SVG webs, v2: all 5 seeds at 5 cm, 0.05 Hz | 30 trials |

## Skipped (and why)

- `web_<policy>.svg` in `controller_audit_v2/{report,matched_trial,a5_f005_seed0}` and `diagnostics_a5_f005_seed0`:
  every file contains 1–2 `<line>` elements (only the top frame edge; the trials stop at 2–3 of 218 actions),
  so a six-policy grid would be blank. Not shipped; the same trials are shown in `audit_v2_attempts`.
- Trace SVG galleries for the 0.1 Hz pilot conditions and for 10 cm at 0.05/0.049 Hz (v1, v2): every panel
  shows ≤ 22 accepted actions (mostly 2); nearly empty, not shipped. Their outcomes are in
  `v1_pilot_progress` and `freq_0049_vs_005`/`v1_vs_v2_progress`.
- `controller_audit_v2/frequency_comparison` duplicates `verified_sweep` in every column except wall-clock
  time (checked), so it is not plotted separately. `action_map.csv` (218 segments × 6 controllers) only
  reaches segments 0–3 and is summarised in text instead of a figure.
- v3 has no per-trial traces in the repo (only trials/comparisons), so no v3 web drawings exist.

## Notes

- Gallery thread colours are the repo's own SVG colours (frame #555, radii #2a6fbb, auxiliary #bbb,
  capture #d17626); only the stroke width was fixed at 0.8 px and gallery labels enlarged by CSS. Own drawings use `THREAD_COLORS`.
- Test count (not a figure): `pytest spider_web_mulder/tests --ignore=.../test_reentrant.py` in a private clone
  at 61d18d8 → 59 passed (output in `W/work/mulder/pytest_mulder.txt`).
