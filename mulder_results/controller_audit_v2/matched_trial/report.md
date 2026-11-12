# Matched controller diagnostics

Amplitude **5 cm**, frequency **0.05 Hz**, seed **0**.

Open [report.html](report.html) for the filterable complete ledger, controller timelines and error plots.
CSV/JSON ledgers retain every decision, attempt and repair, including repeated attempts of the same action.

| Controller | Completed actions | Repairs | First missed action | Error at first miss (cm) |
|---|---:|---:|---:|---:|
| fixed | 2/218 | 0 | 2 | 4.316027 |
| local | 2/218 | 0 | 2 | 3.220693 |
| filtered | 3/218 | 7 | 2 | 1.095774 |
| local_repair | 3/218 | 4 | 2 | 3.220693 |
| full | 3/218 | 8 | 2 | 0.608760 |
| predictive | 3/218 | 7 | 2 | 1.095774 |

## Isolated first-failure replays

Each controller's replays share its original start position and time. Different controllers may have different start times.
No repair delay is introduced. All correction limits and speeds remain unchanged.

| Controller | Replay | Accepted | Final error (cm) |
|---|---|---|---:|
| fixed | original | False | 4.316027 |
| fixed | refreshed_target | False | 2.016590 |
| fixed | frozen_saved_target | False | 5.538066 |
| fixed | frozen_refreshed_target | True | 0.000000 |
| fixed | arrival_oracle | False | 3.220693 |
| fixed | refreshed_arrival_oracle | True | 0.497064 |
| local | original | False | 3.220693 |
| local | refreshed_target | False | 1.576342 |
| local | frozen_saved_target | False | 1.538066 |
| local | frozen_refreshed_target | True | 0.000000 |
| local | arrival_oracle | False | 3.220693 |
| local | refreshed_arrival_oracle | True | 0.497064 |
| filtered | original | False | 1.095774 |
| filtered | refreshed_target | False | 1.095774 |
| filtered | frozen_saved_target | True | 0.000000 |
| filtered | frozen_refreshed_target | True | 0.000000 |
| filtered | arrival_oracle | True | 0.499947 |
| filtered | refreshed_arrival_oracle | True | 0.499947 |
| local_repair | original | False | 3.220693 |
| local_repair | refreshed_target | False | 1.576342 |
| local_repair | frozen_saved_target | False | 1.538066 |
| local_repair | frozen_refreshed_target | True | 0.000000 |
| local_repair | arrival_oracle | False | 3.220693 |
| local_repair | refreshed_arrival_oracle | True | 0.497064 |
| full | original | False | 0.608760 |
| full | refreshed_target | False | 0.608760 |
| full | frozen_saved_target | True | 0.000000 |
| full | frozen_refreshed_target | True | 0.000000 |
| full | arrival_oracle | True | 0.498541 |
| full | refreshed_arrival_oracle | True | 0.498541 |
| predictive | original | False | 1.095774 |
| predictive | refreshed_target | False | 1.095774 |
| predictive | frozen_saved_target | True | 0.000000 |
| predictive | frozen_refreshed_target | True | 0.000000 |
| predictive | arrival_oracle | True | 0.499947 |
| predictive | refreshed_arrival_oracle | True | 0.499947 |

## Reading the evidence

- `original` must reproduce the recorded action exactly; automated tests check this.
- `refreshed_target` isolates stale commands by updating the target at departure with no added delay.
- `frozen_saved_target` removes subsequent frame movement while retaining stale-command error.
- `frozen_refreshed_target` removes both staleness and subsequent frame movement.
- The arrival oracles use perfect future motion to search for a bounded horizontal correction. They enable feedback even for `fixed`.
- A successful intervention identifies an execution strategy that works for this isolated action. It does not guarantee completion of a whole web.
- A failed oracle search is not proof that the target is physically unreachable. Continuous tracking, path alternatives and silk mechanics are not tested.
- The current predictive margin is a sampled drift estimate over nominal timings, not a forecast of the actual finite correction dynamics.
- Old result directories use the earlier controller logic. This report uses model version 2; compare versions explicitly.
