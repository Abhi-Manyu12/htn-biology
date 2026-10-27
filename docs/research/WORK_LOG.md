# Research work log

Append substantive changes here. Dates below identify session stages; exact
execution timestamps were not reconstructed retroactively.

## 2026-10-19 — Mulder scope and branch

- Read the supplied Mulder et al. (2021) PDF and the user's separate proposed
  disturbance-aware HTN analysis. The proposal was treated as a hypothesis,
  not evidence from the biological experiment.
- Created feat_mulder from local main. Existing uncommitted work on
  feat/adaptive-web-planner was saved in a named Git stash, not incorporated
  into this branch's experiments.
- Distinguished biological validation from demonstrating a computational
  mechanism consistent with the published stationary/moving comparison.

## Initial implementation — version 1

- Added the independent spider_web_mulder package with affine support shear,
  frame/radial/auxiliary/capture construction, explicit time, and six execution
  policies: fixed, local, local_repair, filtered, full and predictive.
- Used straight world-space commands and one bounded endpoint correction.
  Recovery was fresh component/root planning with completed-index guards.
- Ran a 270-trial pilot and a 180-trial 0.049-versus-0.05 Hz comparison.
  Stationary runs completed; moving runs frequently failed on attachment.
  Changing frequency by 2% did not establish a consistent improvement.
- Outputs: mulder_results/pilot and mulder_results/frequency_0049_vs_005.
  These are historical v1 results, not results for continuous tracking.

## 2026-10-20 — Controller audit and diagnostics, version 2

- Added complete action/decision/repair ledgers, intended-versus-attempted maps,
  timelines, error plots and isolated first-failure replays.
- Corrected full-controller movement detection across complete cycles,
  redundant proactive refresh immediately after a retry replan, and filtering
  across unrelated component endpoints. Made policy capabilities explicit.
- Replays showed some refreshed targets still failed during endpoint correction;
  freezing the frame or aiming a correction at arrival could succeed. This
  implicated the execution rule, not only saved-target staleness.
- Ran the matched diagnostic and a new 180-trial comparison. At that stage,
  98 tests passed. Outputs: mulder_results/controller_audit_v2/report and
  mulder_results/controller_audit_v2/verified_sweep.
- Limits: oracles do not prove physical unreachability, endpoint correction
  is not continuous tracking, and task refresh is not tree re-entrancy.

## 2026-10-20 — Paper-facing study, version 3

- Added continuous feedback with no-slip passive advection and bounded
  locomotion relative to instantaneous substrate geometry. Separated contact
  dwell, imposed action deadlines, and added independent sensory lag.
- Retained the endpoint executor as an explicit mechanism comparison.
  Preserved the user's environment frequency 0.049; experiment sweeps select
  their own recorded frequencies explicitly.
- Added polygonal area estimates, cardinal capture intersections/counts,
  Table 1 eccentricity/mesh formulas, phase allocation and 10 s sampled travel.
  Failed constructions have missing final-web geometry.
- Added flat-sequence ablations and an HTN direct-versus-phase_wait method
  comparison. The latter estimates nominal shear-dependent construction cost;
  it does not select a different anchor.
- Added rigid-only calibration/import support with moving observations held
  out, explicit raw-data availability status, paired bootstrap contrasts and
  completion intervals. Biological raw observations were not supplied.
- Ran:

  ```sh
  python3 -m spider_web_mulder.validation --seeds 30 --output mulder_results/paper_validation_v3
  python3 -m spider_web_mulder.validation --analyse-existing mulder_results/paper_validation_v3 --output mulder_results/paper_validation_v3_report
  python3 -m pytest -q spider_web_mulder/tests spider_web_htn_updated/tests
  ```

- Study: 2,280 trials; 30 phases in primary comparisons, 12 in each sensitivity
  profile. Primary comparisons include 5/10 cm peak at 0.049/0.05 Hz; stationary
  controls run once per seed/profile/controller. No simulated biological
  population or repeated-spider mixed model is claimed.
- At 10 cm, 0.05 Hz: legacy endpoint policies each completed 0/30; ideal local
  tracking, full replanning and predictive control each completed 30/30.
  Local duration increased 0.980713% (95% paired bootstrap 0.963429–0.996403%);
  full replanning increased 3.923865% (3.893372–3.953719%).
- Camera-sampled local travel increased 1.130044% (1.079618–1.180734%).
  Exact ideal material-coordinate travel and much of the geometry are imposed
  by construction and do not independently validate biological invariance.
- Flat tracking matched the HTN sequence's duration exactly on the 12 matched
  phases. One- and five-second sensory lag profiles each completed 0/12 trials.
  The phase_wait method was slower by 22.703291 s on matched moving local runs.
- Last validation of the simulation code: 114 tests passed. Generated figures
  were visually inspected. Curated evidence/figures are now under docs/ so the
  manuscript does not depend solely on ignored result directories.
- Interpretation: ideal local feedback is sufficient for this benchmark;
  a hierarchy/replanning advantage and quantitative biological validation
  have not been demonstrated.

## 2026-10-20 — Manuscript record and Bansod recovery review

- Created the repository research index, claim ledger, curated evidence,
  manuscript-ready Methods/Results/limitations prose and bibliography.
  Added root AGENTS.md instructions to maintain this record in future work.
- Read Bansod et al. (HPlan 2021), including Algorithms 1–4, Example 2 and
  experimental limitations; checked the author repository and related 2022
  publication. Assessment: a strong candidate recovery backend/baseline for
  dependency-changing failures, not a cure for low-level tracking errors.
- Audited current recovery: fresh find_plan calls plus state.done guards;
  no persistent solution tree, failed-node re-entry, general suffix invalidation,
  physical retracing, roadblock routing or damaged-structure repair.
- Found the installed GTPyhop 1.9.7 default is iterative greedy, not full DFS
  backtracking. The repository does not pin its strategy. A standalone toy
  probe failed under that default and succeeded under explicit iterative DFS
  backtracking. This corrects earlier generic backtracking descriptions.
- Ran:

  ```sh
  python3 docs/research/probes/planner_strategy.py --output docs/research/evidence/planner_strategy_audit.json
  ```

- The probe is a process-isolated audit; application algorithms, dependencies,
  strategy settings and historical numerical results were not changed.
  IPyHOP integration and the conformance experiments in the literature review
  are proposals, not implemented results.

## 2026-10-20 — Retained-tree recovery integration, separate recovery v1

- Following authorization, obtained upstream IPyHOP revision
  bdda21012b2396aed9a91980af8fbb71dbcb7075 and vendored the unmodified source,
  BSD-3-Clause license and per-file hash manifest under third_party/IPyHOP.
  Added NetworkX and pinned the tested GTPyhop 1.9.7 dependency.
- Added spider_web_recovery rather than changing the numerical meaning of
  existing Mulder v3 results. It models scaffold/radial traversal, primary and
  backup attachments, dependent capture sectors, actual position, resource
  consumption/loss and structural validity separately from history.
- Integrated actual planner.replan(observed_state, failed_node_id) calls,
  extracting newly marked leaves from the retained tree. Added fresh IPyHOP
  as a same-engine baseline and explicit GTPyhop DFS root/component baselines.
- Added transient retry without permanent blacklisting, anchor replacement,
  graph-valid route detours, restoration after prefix damage, and infeasibility
  termination. Empty plans do not imply success unless the objective holds.
- Added action/repair/time budgets and checked the final attachment cannot
  claim completion past its deadline. Planning-effort contrasts include failed
  cases; successful construction costs remain conditional on completed pairs.
- Ran:

  ```sh
  python3 -m spider_web_recovery --seeds 10 --trace --output mulder_results/recovery_v1_verified
  python3 -m pytest -q spider_web_recovery/tests spider_web_mulder/tests spider_web_htn_updated/tests
  ```

- 2,240 trials: four backends, seven scenarios, ten seeds, two sector counts,
  two wrapper depths and two amplitudes. Feasible scenarios completed 80/80
  declared cases per backend/scenario; unreachable and resource-infeasible
  cases terminated at 0/80 completion. These are descriptive pooled counts.
- Permanent-anchor component refresh produced two stale downstream detections
  and three repairs on average; retained-tree IPyHOP used one recovery with
  no stale downstream detections. Fresh-root baselines also avoided them.
- At 8 sectors/depth 2/A=10, retained-minus-fresh IPyHOP method calls were
  -19.6 for anchor failure, -10 for route block and -38 for prefix damage.
  Silk-depletion infeasibility instead cost +11.2 calls (95% interval 7.6–14.8).
  There is no universal planning-cost improvement claim.
- No unnecessary repetition of still-valid completed work occurred in the
  declared cases. Legitimate reconstruction after damage was counted separately;
  resource conservation and observed-position preservation were verified.
- 158 tests passed. Scope limits: abstract capture operations, authored repair
  dependencies, initial scaffold assumptions, logical event triggers, wrapper
  depth rather than new semantic decisions, and a custom immediate-precondition
  actor rather than a verbatim replication of the full published actor study.
- Curated the numerical evidence and example trees under docs/, updated the
  claim ledger and added manuscript recovery prose. The six original Mulder
  policies and all their historical outputs remain unchanged.

## 2026-10-20 — IPyHOP integrated into the actual Mulder HTN (v4)

- User requested integrating the algorithm into the existing HTN and measuring
  whether results improve. Added `spider_web_mulder/reentrant.py` and optional
  `planner_backend` selection to the existing `run_trial` actor. The default
  legacy runner remains available; old output directories are preserved.
- Both new modes share web/component/segment-refinement methods. Fresh IPyHOP
  restarts at the root; retained IPyHOP calls the unmodified pinned upstream
  `replan` with the actual current action leaf. Finite equivalent target-refresh
  methods permit bounded transient retries. The observed completion set and
  clock go to planning; the actor preserves actual movement position and costs.
- Recovery returns the entire unexecuted suffix; runtime assertions reject
  missing, repeated or reordered segment indices. Original policy names retain
  their feedback/trigger rules; IPyHOP determines tree recovery scope instead of
  the legacy component-splicing rule. This is not the full published actor.
- Added a single explicitly logged synthetic rejection at segment 10, after an
  otherwise successful physical attempt. This is not structural damage or a
  calibrated biological disturbance. The sector experiment's graph/resource
  abstractions were not imported into Mulder.
- Added `recovery_comparison.py`: three backends × six policies × ten seeds ×
  two sizes × six profiles. Profiles include both 0.049/0.05 Hz, rigid support,
  one miss, one-second sensing lag, and endpoint execution. Direct methods;
  settings, upstream/dependency versions and executed-source hashes are recorded.
- Commands:

  ```sh
  python3 -m spider_web_mulder.recovery_comparison --seeds 10 --trace --output mulder_results/mulder_reentrant_v4
  python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests spider_web_htn_updated/tests
  ```

- Verification: **176 tests passed**, including same-engine execution agreement,
  repeated re-entry from an updated clock, early/mid/late attachment misses,
  actual-position preservation, accepted-prefix nonrepetition, lag failure,
  failed-run computational contrasts, and CLI evidence/no-overwrite behavior.
- Interpretation and exact results are in
  `docs/manuscript/mulder_reentrant_results.md`; curated evidence is generated by
  `docs/research/probes/snapshot_mulder_reentrant.py`. CPU timing includes adapter
  overhead, and recorded seed-0 examples include tree snapshots. The curated
  snapshot also provides means excluding seed 0 to assess timing sensitivity.
- Completed the 2,160-trial sweep. All 720 retained/fresh IPyHOP pairs had
  identical completion, completed actions, repairs, elapsed time and travel.
  At configured size/0.05 Hz/full, retention saved 434 method calls (1.67%) but
  increased mean planning wall time from 1.816 to 2.658 s. Excluding recorded
  seed 0 still yielded 1.823 versus 2.628 s. No speed advantage is established.
- A scoped gain over legacy appeared for configured-size lagged filtered
  control: 0/10 → 5/10 completion with either IPyHOP mode. Ran a further 10
  diagnostic trials using the original GTPyhop domain with whole-suffix refresh:

  ```sh
  python3 -m docs.research.probes.mulder_suffix_control
  ```

  This control also achieved 5/10 and matched every IPyHOP physical outcome and
  repair count, isolating refresh scope as the explanation in these cases.
  The small lagged filtered case instead regressed from 3/10 to 2/10. Preserve
  both observations; there is no universal benefit or unique re-entry effect.
- Curated exact outcomes, source/version evidence and control trials in
  `docs/research/evidence/mulder_reentrant_v4_summary.json` and
  `mulder_suffix_control.json`. Annotated the HTML overview with the finished
  comparison and control interpretation, recording report-only provenance.
  All source manifests and recorded tree/prefix assertions were verified by:

  ```sh
  python3 docs/research/probes/finalize_mulder_reentrant_report.py mulder_results/mulder_reentrant_v4
  python3 docs/research/probes/snapshot_mulder_reentrant.py mulder_results/mulder_reentrant_v4
  ```

## 2026-10-20 — Re-centering the Mulder objective

- Reviewed the original biological objective after the user asked where the
  project stands and whether it is publishable. Distinguished simulator/software
  verification, computational mechanism testing and empirical biological validation.
- Added `MULDER_OBJECTIVE_ROADMAP.md`: current evidence, imposed-output risks,
  missing cohort data/calibration, ordered milestones, and a conditional publication
  assessment. These are proposed research steps, not completed analyses.
- Rechecked the publisher's article: data and statistical code are listed as
  available from the corresponding author upon reasonable request. No outreach
  was sent. Existing runs remain unchanged.

## 2026-10-27 — Branch backup for workspace restart

- Prepared the Mulder/recovery source, tests, manuscript records and vendored
  IPyHOP for committing to `feat_mulder` at the user's request.
- Archived all 3,046 ignored result files in
  `research_snapshots/mulder_results_2026-10-27.tar.gz` (19,120,445 bytes).
  Verified every archived file against its source SHA-256; retained a manifest
  and restoration instructions alongside the archive.
- No model changes or new scientific runs were made for this backup. The last
  reported software check passed 176 tests on 2026-10-24.
