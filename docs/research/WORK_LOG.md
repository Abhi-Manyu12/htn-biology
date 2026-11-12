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


## 2026-11-12 — Spider literature and proposed HTN experiments

- Followed the external researcher role selected by AGENTS.md. User requested
  relevant spider papers for the manuscript, including experiment opportunities.
- Added docs/research/SPIDER_HTN_LITERATURE.md with 11 candidate sources, source
  access depth, biological versus proposed HTN distinctions, code mappings,
  manuscript placement and three proposed computational experiment directions.
- Added 11 entries to docs/manuscript/references.bib, preserving the three
  existing entries. Updated indexes and CLAIMS.md with interpretation limits.
- Established .ai-memory research pointers and archived task record; roadmap
  marks the literature task done. Source graph absent; direct reads used.
- Validation: checked primary publisher/author metadata and abstracts, selected
  full-text sections, 14 unique bibliography keys, balanced braces, report key
  references and memory links. Some full texts and the Corver data-archive DOI
  were inaccessible; the report records these limits. This was not a complete
  systematic review or full algorithm replication audit.
- No models or datasets changed, no simulation seeds generated, and no software
  tests or biological validation performed. E1/E2/E3 remain proposed. Existing
  claims of no demonstrated hierarchy/re-entrancy advantage are unchanged.
- Recommendation: contextualize the current manuscript with prior rule-based
  models; consider observed-structure recovery first, stage-sequence comparison
  second. Next role: data-scientist for feasibility and a fixed analysis protocol.

## 2026-11-12 — Restore literature and adaptive-planner work

- Restored the literature/manuscript changes from the `feat_mulder` stash and
  the earlier adaptive-planner changes from its stash. Both stashes remain
  intact. The latter depended on the committed adaptive branch at `3a51a8b`,
  so its spiral geometry, instrumentation, configuration and associated
  tests/visualization were also integrated into the current checkout.
- Resolved the spiral operator conflict by calculating movement cost and
  enforcing the resource bound before creating the dynamic waypoint or thread.
  Added a regression test covering rejection without mutation and success.
- Kept the original `wind_sensitivity.csv` after verifying that branch changes
  only altered whitespace. Recovered `perturbation_trials.csv` has SHA-256
  `c9d30b18118b930c1bf3b8a9ad3c86364193e3ec6d4fb1afc3a4fb22cdc9e2f8`;
  the historical run's full settings and source provenance have not been
  verified, so its values are not evidence for manuscript claims.
- Verification: `python3 -m pytest -q spider_web_mulder/tests
  spider_web_recovery/tests spider_web_htn_updated/tests` passed 177 tests.
  A one-seed command-line smoke check used `python3 -m
  spider_web_htn_updated.perturbations --n-runs 1 --seed 0 --out
  /private/tmp/htn_perturbation_restore_check.csv`; Python 3.12.0, GTPyhop
  1.9.7 and NetworkX 3.4.2. This is software verification, not a new study;
  the baseline did not reach the event in these cases, and the result is not
  an equal-exposure comparison. The E1 experiment remains unimplemented.
- No prior Mulder or recovery evidence was changed. An independent audit of
  the adaptive-planner model, benchmark design and its old outputs is needed
  before adding quantitative claims to the manuscript.

## 2026-11-12 — E1 observed-structure recovery on development/E1

- User requested branch creation and E1 implementation. Created `development/E1`
  from clean `main` at `61d18d8`. Added an independent E1 actor and benchmark
  entry point, reusing recovery-v1 domain/primitives/routing/resource bounds,
  pinned IPyHOP and Mulder-v3 tracking. Existing runners and historical outputs
  remain unchanged. No new dependency or planner algorithm was introduced.
- Fixed `E1_PROTOCOL.md` before the primary sweep. Four controllers (cached
  history, state rules, fresh HTN, retained HTN) share physical observations,
  preconditions and final-goal validation. Six cases distinguish intact sham,
  single/multiple damage, aligned donor transfer and two infeasible controls.
  Transfer retains actor costs/stock and records donor/displaced silk separately;
  retained recovery uses a real queued action-node ID. Diagnostic trees are
  collected separately from primary timings.
- Software verification: 49 new E1 tests passed, and the full command
  `python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests
  spider_web_htn_updated/tests` passed **226 tests**. Same-session adversarial
  data/security/QA review and AC-1–AC-8 traceability are in `E1_REVIEW.md`.
  This is software verification, not biological validation.
- Computational run: `python3 -m spider_web_recovery.e1_benchmark --output
  mulder_results/e1_v1_20261112`. Exactly **1,920** primary trials: four controllers
  × six scenarios × sectors [4,8] × amplitudes [0,10] cm × seeds 0–19. Frequency
  0.05 Hz, depth 0, stock 500 cm, speed 1 cm/s, 500 attempts, 20 replans, 20,000 s
  deadline. Python 3.12.0, GTPyhop 1.9.7, NetworkX 3.4.2, NumPy 2.2.6; IPyHOP
  revision `bdda21012b2396aed9a91980af8fbb71dbcb7075`. Bootstrap 2,000 resamples,
  seed 20261112; pointwise descriptive intervals. Exact Config/Settings, strategy,
  command, runtime, source/protocol hashes and uncommitted Git state are in
  `docs/research/evidence/e1_v1/provenance.json`. HEAD identifies the base commit;
  source hashes identify the actual new E1 code used in the run.
- Results: all 480 matched cases reached identical pre/post intervention states;
  no unnecessary reconstruction and zero actor-stock conservation error. Each
  capable controller completed all 320 feasible trials (including 80 intact)
  and stopped in all 160 infeasible trials. Cached history completed only 80
  intact trials. Each prespecified capable-controller contrast had identical
  completion in 480/480 pairs and exact time/travel/silk equality in 320/320
  both-successful pairs. There is **no HTN performance advantage over state
  rules** in this benchmark. Retention saves mean method calls in feasible
  disruptions but increases mean decision wall time; infeasibility costs more
  calls as well. C29–C32 record the findings and interpretation limits.
- Preserved output: `mulder_results/e1_v1_20261112/` contains complete JSON/CSV
  trials, strata, paired analysis, first-seed traces, separate tree diagnostics,
  figures, source manifest and final artifact checksums. Verified all 114 bulk
  artifact hashes. Curated trial CSV, summaries, contrasts, manifests and selected
  traces were copied byte-for-byte to `docs/research/evidence/e1_v1/`. Added
  `e1_v1_summary.json` with pooled descriptive values, exact pair checks and
  curated checksums. Copied completion PNG/SVG to `docs/manuscript/figures/` and
  visually inspected the figure. The ignored output directory is not the sole
  research record.
- Added manuscript fragment `docs/manuscript/e1_methods_results.md`, updated
  indexes and claim ledger. This is a literature-inspired computational study,
  not reproduction of Peters/Eberhard animal protocols; structure, geometry,
  aligned transfer and ideal sensing remain imposed. E2/E3 remain proposed.
- Role workflow and task memory completed; source graph unavailable, direct
  reads used. No earlier numerical artifact or existing model/planner/actor
  source changed relative to `61d18d8`. New code/results are local to the
  requested branch; no commit or push performed in this task.

## 2026-11-12 — Repeat E1 and produce detailed results

- User requested a run and comprehensive results. On `development/E1`, reran
  `python3 -m spider_web_recovery.e1_benchmark --output
  mulder_results/e1_v1_20261112_rerun` using the frozen protocol, same source
  and seeds. Started 18:26:40 UTC. Settings, complete dependency versions,
  command, Git status, source SHA-256 and IPyHOP revision are preserved in
  `docs/research/evidence/e1_v1_rerun/provenance.json`.
- Completed 1,920 trials with 480/480 equal-exposure matched cases. Compared
  every trial with the first run: all saved non-timing fields match for all
  1,920 matched records, and the source-hash manifests are identical. Wall time
  differs as expected; this is a same-seed reproducibility check, not 1,920 new
  independent cases. All 114 bulk artifact hashes verified. No prior output
  directory was overwritten.
- Results reproduce the first study: each state-aware controller completes all
  320 feasible cases, stops for all 160 infeasible cases, and is exactly tied
  in completion across 480 pairs and in time/travel/silk across 320 successful
  pairs for each capable-controller contrast. Each paired comparison includes
  160 infeasible pairs with no eligible physical-cost outcome. No unnecessary
  work or stock-conservation error was observed. Timings in this run vary by
  scenario and implementation; see the detailed report rather than substituting
  them into the original run's numerical table.
- Reran `python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests
  spider_web_htn_updated/tests`: **226 passed**. Data-scientist and same-session
  data-reviewer inspection covered matching, exposure, conditioning, timing,
  assumptions, traceability and preserved inputs. Graph unavailable; used
  direct file reads. This is software and computational evidence, not empirical
  biological validation.
- Curated all trial records, stratified summaries, paired contrasts, settings,
  exposure, generated report, figures and artifact checksums under
  `docs/research/evidence/e1_v1_rerun/`; exact audits and checksums are in
  `docs/research/evidence/e1_v1_rerun_summary.json`. Detailed narrative, failure
  counts, physical costs and method/wall-time breakdowns are in
  `docs/research/E1_RERUN_RESULTS.md`. Updated C33 and research/manuscript
  indexes. Physical seed/sector assumptions and wall-clock limits are explicit.

## 2026-11-13 — E1 expanded conditions and manuscript graphs

- User requested more experimental conditions, including larger webs, and
  graphs. Before fixing the design, a runtime/feasibility pilot ran 4 controllers
  on 8/16/24/32 sectors, 1,000 cm stock, 10 cm amplitude, 0.05 Hz, seed 101,
  multiple damage. It is excluded from primary data. The expanded protocol was
  then fixed in `E1_EXPANDED_PROTOCOL.md` before the 5,280-trial run.
- Added `spider_web_recovery/e1_expanded.py`, reusing the unchanged E1 actor,
  domain, planning backends, validator and statistical helpers. It keeps suite,
  full configuration, scenario and seed distinct; audits all-controller
  exposure and checkpoint hashes; retains unsuccessful pairs and records
  conditional physical-cost denominators. It refuses existing output paths and
  verifies original and expanded protocol/source hashes before completion.
  No dependencies, historical E1 source or original output directories changed.
- Three fixed suites, seeds 20–29: scaling 4/8/16/24/32 sectors, 0/10 cm
  amplitude, 1,000 cm stock, six E1 scenarios (2,400 trials); resources
  8/16/32 sectors, intact requirement 19n plus −1/0/20/60 cm, four scenarios,
  amplitude 10 cm (1,920 trials); movement 8/24 sectors, 20/30 cm amplitude,
  0.05/0.10 Hz, three scenarios, 1,000 cm stock (960 trials). All use the four
  controllers. Depth 0, speed 1 cm/s, max 500 actions, 20 replans and 20,000 s.
  Complete `Config`/`Settings`, runtime versions, command, Git state, source
  hashes, pinned upstream manifest and bootstrap settings in
  `docs/research/evidence/e1_expanded_v1/provenance.json`.
- A first `/private/tmp/` smoke run correctly refused completion because an
  import was moved while it ran: the source-stability check detected the edit.
  Its partial output was not used as evidence. A clean movement-suite smoke
  with seed 20 then completed 96 trials. Four focused expanded-protocol tests
  passed alongside 49 existing E1 tests. The full verification command
  `python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests
  spider_web_htn_updated/tests` passed **230 tests**.
- Primary command: `python3 -m spider_web_recovery.e1_expanded --output
  mulder_results/e1_expanded_v1_20261113`. Started 2026-11-12 19:01 UTC
  (2026-11-13 00:31 India time), Python 3.12.0, GTPyhop 1.9.7, NetworkX 3.4.2,
  NumPy 2.2.6; IPyHOP revision `bdda21012b2396aed9a91980af8fbb71dbcb7075`.
  Source hash for expanded runner:
  `0046614f6e26ac3bf3acf6573dcd474301cfc64ae610fcbbefed54a50538a797`.
  Bootstrap 2,000 samples, analysis seed 20261113; pointwise descriptive.
- Results: 5,280 trials; 1,320 matched cases. All 1,200 exposed cases have
  identical pre/post hashes across controllers; 120 cases (−1 cm stock margin)
  were unexposed for every controller. For each of the three capable-controller
  contrasts, completion matched in 1,320/1,320 cases, and time/travel/silk were
  exactly equal in all 830/830 pairs where both succeeded. No unnecessary
  repeats; maximum stock-conservation residual 0 cm. Tight +20 cm margin gave
  3/10, 1/10 and 1/10 single-damage completions at 8/16/32 sectors; multiple
  damage gave 0/10 at each, versus 10/10 at +60 cm. Imposed stock requirements
  and incomplete exposure preclude a biological threshold claim.
- In the 32-sector multiple-damage, 10 cm movement case, the measured mean
  decision times were 46.216/133.045/154.647 ms (state/fresh/retained), 10
  seeds each. At 24 sectors retained averaged 85.333 ms versus fresh 86.270 ms;
  the paired mean −0.937 ms has descriptive interval [−11.961, 8.241] ms.
  Therefore do not state retained is always slower. Counts are machine-specific
  and the rule/planner timing boundaries differ. C31 was narrowed and C34/C35
  added. The 20–29 seeds are not individual spiders or independent sources of
  phase and target; no real-wind or empirical-web validation was performed.
- Saved complete trial CSV, summary, paired contrasts, provenance, exposure and
  checksums under `docs/research/evidence/e1_expanded_v1/`; exact pair audits and
  curated/figure hashes in `e1_expanded_v1_summary.json`. Verified all **545**
  bulk artifact checksums. First-seed traces and full JSON remain in the new
  `mulder_results/e1_expanded_v1_20261113/`; prior numerical artifacts preserved.
- Added four PNG/SVG figures under `docs/manuscript/figures/e1_expanded_*` and
  captions/results in `docs/manuscript/e1_expanded_results.md`. The stock figure
  was regenerated after the sweep from saved trial JSON using the separately
  hashed `e1_expanded_figures.py`, with categorical stock points and Wilson
  intervals; the original graph is preserved in the bulk output. A first plot
  attempt exposed tiny floating-point negative error lengths at 0/10 or 10/10;
  clamping those round-off residuals to zero fixed it, and the figure was
  regenerated and visually inspected. The separate figure script also accepts
  the curated CSV; its regenerated PNG matched the archived PNG byte for byte
  on the recorded runtime. The original generator remains unchanged.
- Added one regression test for reading curated CSV failures and configurations
  correctly; reran the complete verification command and **231 tests passed**.
- Data-scientist implementation and same-session adversarial data/security/QA
  review checked matching keys, duplicate rejection, failure denominators,
  checkpoint exposure, stock accounting, source provenance, CLI file writes,
  no shell execution and no new dependency. No blocking findings in this local
  study; external independent review was not performed. Source graph unavailable,
  so relevant files were read directly. No biological experiment was performed.

## 2026-11-13 — Expanded E1 post-hoc analysis

- User requested analysis of the expanded results. Read the fixed protocol,
  code/model assumptions, curated trial CSV and paired contrasts; no model,
  planner, controller, historical output or experimental settings changed.
- Verified each of the 30 state-rule +20 cm, single-damage trials: success
  occurs exactly when the randomly selected target is the last completed capture
  sector. The model then requires one 14 cm radius plus one 5 cm capture (19 cm
  extra), versus 24 cm for an earlier target that invalidates two previously
  completed captures. Seeds select that target 3/10, 1/10, 1/10 times at 8, 16,
  32 sectors; both HTN controllers have identical completion. Added C36; this is
  an imposed-model mechanism, not a claim about biological silk requirements.
- Compared 8/24-sector single-damage simulated elapsed time under 0.05 Hz
  support amplitudes 10/20/30 cm versus matched-seed stationary cases. The latter
  amplitudes span separate prespecified suites, so this is explicitly post hoc.
  Paired descriptive percentile bootstrap: 2,000 resamples, seed 20261114,
  10 pairs per comparison, no multiple-testing adjustment. Means, intervals,
  exact input SHA-256, target-seed results and original timing contrasts are
  recorded in `docs/research/evidence/e1_expanded_posthoc_analysis.json`.
- Added `docs/research/E1_EXPANDED_ANALYSIS.md` with evidence, mechanism,
  denominators, uncertainty, study limits and manuscript implications. Updated
  research index and claims. This is interpretation of existing computational
  evidence, not a new experiment or empirical biological validation. No tests
  rerun because the analysis changed no implementation. Existing 231-test
  result applies to the previously tested code.
