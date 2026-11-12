# E1 observed-structure recovery

1,920 computational trials; 480 matched cases with identical checkpoint states; 0 unexposed cases.

Counts below pool sizes, amplitudes and seeds. See summary.csv for strata and Wilson intervals.

| Scenario | Controller | Complete / attempted | Events | Redundant effects |
|---|---|---:|---:|---:|
| intact | history | 80/80 | 80 | 0 |
| intact | state_rules | 80/80 | 80 | 0 |
| intact | fresh_htn | 80/80 | 80 | 0 |
| intact | retained_htn | 80/80 | 80 | 0 |
| damage_single | history | 0/80 | 80 | 0 |
| damage_single | state_rules | 80/80 | 80 | 0 |
| damage_single | fresh_htn | 80/80 | 80 | 0 |
| damage_single | retained_htn | 80/80 | 80 | 0 |
| damage_multi | history | 0/80 | 80 | 0 |
| damage_multi | state_rules | 80/80 | 80 | 0 |
| damage_multi | fresh_htn | 80/80 | 80 | 0 |
| damage_multi | retained_htn | 80/80 | 80 | 0 |
| transfer_partial | history | 0/80 | 80 | 0 |
| transfer_partial | state_rules | 80/80 | 80 | 0 |
| transfer_partial | fresh_htn | 80/80 | 80 | 0 |
| transfer_partial | retained_htn | 80/80 | 80 | 0 |
| damage_unavailable | history | 0/80 | 80 | 0 |
| damage_unavailable | state_rules | 0/80 | 80 | 0 |
| damage_unavailable | fresh_htn | 0/80 | 80 | 0 |
| damage_unavailable | retained_htn | 0/80 | 80 | 0 |
| damage_resource | history | 0/80 | 80 | 0 |
| damage_resource | state_rules | 0/80 | 80 | 0 |
| damage_resource | fresh_htn | 0/80 | 80 | 0 |
| damage_resource | retained_htn | 0/80 | 80 | 0 |

## Interpretation limits

This is a prescribed sector/scaffold computational model, not empirical biological validation. The cached-plan controller is a weak diagnostic ablation. The state-rule controller shares the HTN's routing, primary/backup choices, validity and necessary resource-bound knowledge. A tie against that baseline does not establish an HTN advantage.

Transfer uses an aligned donor frame, a common hub and five seconds of external handling. Donor silk is separate from actor expenditure. Geometry, capture cost and damage are imposed.

Decision timings are implementation wall times on one machine, including feasibility checks and adapter work, with tree snapshots disabled. They are not CPU complexity or biological costs. Physical paired differences condition on both constructions succeeding; infeasible strata have zero eligible physical pairs, not zero physical cost. Computational contrasts include failures. Recovery-only timing conditions on event exposure. Method calls compare only the two HTN controllers. Bootstrap intervals are pointwise descriptive, with no multiplicity adjustment.

## Reproduction and artifacts

See provenance.json for exact settings, seeds, engine versions, source hashes and command. trials.json/csv contain every outcome; summary and paired files retain strata/denominators. traces/ holds first-seed action ledgers. diagnostics/ contains separately timed retained trees. artifact_sha256.json hashes all completed artifacts. Existing output directories are refused.
