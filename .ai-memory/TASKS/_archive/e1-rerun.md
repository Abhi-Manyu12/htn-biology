# E1 same-seed rerun — complete, 2026-11-12

- User requested a full run and comprehensive results on `development/E1`.
- Data-scientist and same-session data-reviewer phases; source graph unavailable.
- Ran frozen 1,920-trial sweep into `mulder_results/e1_v1_20261112_rerun/`.
  Original directory preserved. Full suite: 226 tests passed.
- Every matched trial's non-timing fields reproduce the first run; source-hash
  manifests match. This is a repeat of the same seeds, not new evidence.
- Matched exposure: 480/480. Each capable controller: 320/320 feasible successes,
  160/160 infeasible stops. Three contrasts: 480/480 equal completion and
  320/320 exact physical-cost ties among pairs completing. Wall timings differ.
- Detailed report: `docs/research/E1_RERUN_RESULTS.md`; curated source manifest,
  all trial rows, strata, contrasts and figure: `docs/research/evidence/e1_v1_rerun/`;
  exact comparison and checksums: `evidence/e1_v1_rerun_summary.json`.
- C33 and `WORK_LOG.md` updated. Scientific limits: simulated, imposed geometry,
  ideal sensing, aligned transfer; no HTN superiority or biological validation.
- At task completion, source was uncommitted locally. Roadmap updated; next step is
  manuscript assembly/review when requested, with E2/E3 separately proposed.
