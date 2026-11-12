# E1 full rerun: detailed results

Run started 2026-11-12 at 18:26:40 UTC on `development/E1`. This is an exact
repeat of the frozen E1 design with the same source and seeds, conducted to
check reproducibility and give a detailed breakdown. It is not another 1,920
independent observations and should not be pooled with the original run as if
it were additional evidence.

## Question and design

Can an HTN recover from changes in the currently observed web better than an
equally informed controller using state-based rules? Does retaining an IPyHOP
tree improve on starting a fresh plan?

Four controllers are compared:

1. **Cached plan (`history`)**: executes the original IPyHOP plan and has no
   recovery logic. This is a deliberately limited diagnostic baseline.
2. **State rules (`state_rules`)**: checks the observed web and uses authored
   rules to rebuild missing structure without HTN decomposition.
3. **Fresh HTN (`fresh_htn`)**: replans from the root using IPyHOP.
4. **Retained HTN (`retained_htn`)**: uses the same IPyHOP engine and re-enters
   its retained solution tree at the next queued action node.

All share the same web representation, routing, action preconditions and goal
test. The capable state and HTN controllers share primary/backup anchor choices
and a necessary material bound. The actor is observed at the hub after building
all radii and half the capture sectors. One of six interventions then occurs:

- **Intact:** observe without damage.
- **Single damage:** remove one primary anchor and its dependent structure;
  the backup remains available.
- **Multiple damage:** remove two primary anchors and dependent structure.
- **Partial transfer:** replace the current web with a specified incomplete
  donor web in an aligned frame, with the actor at a common hub. The model
  charges five seconds of handling; it assumes zero external displacement.
- **Unavailable anchors:** remove both the primary and backup for one radius.
- **Insufficient silk:** damage one anchor, then reduce the remaining stock to
  one centimetre below the model's necessary completion bound.

The last two cases are intentionally infeasible controls. A safe failure is
the expected outcome, not a failure of the benchmark itself. Imported donor
silk is tracked separately from the actor's own stock and expenditure.

The design crosses four controllers, six scenarios, 4 or 8 sectors, support
amplitudes 0 or 10 cm at 0.05 Hz, and seeds 0–19. This gives 1,920 trials and
480 matched scenario/size/amplitude/seed cases. Each seed determines forcing
phase and target sector; the two draws are initialized from the same seed and
are not independent samples of animals. Depth is 0, stock is 500 cm, speed is
1 cm/s, and the budgets are 500 action attempts, 20 replans and 20,000 s.

## Completion and failure

Every table cell pools 80 trials: two sizes × two amplitudes × 20 seeds.

| Scenario | Cached plan | State rules | Fresh HTN | Retained HTN |
|---|---:|---:|---:|---:|
| Intact | 80/80 | 80/80 | 80/80 | 80/80 |
| Single damage | 0/80 | 80/80 | 80/80 | 80/80 |
| Multiple damage | 0/80 | 80/80 | 80/80 | 80/80 |
| Partial transfer | 0/80 | 80/80 | 80/80 | 80/80 |
| Unavailable anchors | 0/80 | 0/80 | 0/80 | 0/80 |
| Insufficient silk | 0/80 | 0/80 | 0/80 | 0/80 |

Each capable controller completed 320/320 feasible trials, including the 80
intact controls, and correctly stopped on 160/160 infeasible trials. Across
the cached plan's 400 disrupted trials, 222 terminated on a rejected stale
precondition and 178 exhausted the original plan without satisfying the goal.
The exact split by scenario is 28/52 for single damage, 58/22 for multiple
damage, 80/0 for transfer, and 28/52 for each infeasible control. No conclusion
about all possible disturbances follows from these six authored scenarios.

All 480 cases reached the event; hashes of pre- and post-intervention observed
states matched across all four controllers in each case. There were zero
repetitions of still-valid effects and the maximum stock-conservation residual
was 0 cm in the stored rows. A restoration is different: previously built work
was invalidated by the intervention and had to be constructed again.

For each of fresh-minus-rules, retained-minus-rules and retained-minus-fresh:
completion agreed for 480/480 matched pairs. Of these, 320 pairs had both
controllers complete, and **all 320 matched exactly** in simulated elapsed
time, travel and actor silk used. The other 160 pairs were infeasible on both
sides and have no eligible successful-pair physical-cost difference. A zero
bootstrap interval for the paired success/physical metrics here reflects the
identical values in these cases; it is not proof of equivalence in all cases.

Each size/amplitude/scenario stratum contains 20 seeds. The reported pointwise
Wilson 95% interval is approximately [0.839, 1.000] for 20/20 success, and
[0.000, 0.161] for 0/20. Paired bootstrap intervals use 2,000 resamples and
analysis seed 20261112. These describe the specified simulated seed cases;
they do not represent uncertainty across spiders or independently sampled
biological populations. No multiple-testing adjustment was made.

## Physical work in successful trials

The table uses state rules; fresh and retained HTN have exactly the same
physical result in each matching successful case. Each mean is over 20 seeds.
Times are in simulated seconds, travel and actor silk in centimetres. Travel
and silk below were identical across the two support amplitudes; time is shown
separately. Transfer includes the stipulated five-second handling time and
excludes imported donor silk from the actor's own silk use.

| Sectors | Scenario | Time, stationary | Time, 10 cm motion | Travel | Actor silk | Mean restorations |
|---:|---|---:|---:|---:|---:|---:|
| 4 | Intact | 148.41 | 149.39 | 138.41 | 76.00 | 0 |
| 4 | Single damage | 186.00 | 187.26 | 173.23 | 97.75 | 2.55 |
| 4 | Multiple damage | 221.63 | 222.99 | 206.85 | 111.75 | 3.55 |
| 4 | Partial transfer | 191.45 | 192.59 | 173.67 | 97.75 | 2.55 |
| 8 | Intact | 294.01 | 295.83 | 274.01 | 152.00 | 0 |
| 8 | Single damage | 331.17 | 333.59 | 308.29 | 174.75 | 2.75 |
| 8 | Multiple damage | 367.16 | 369.65 | 342.01 | 191.50 | 4.30 |
| 8 | Partial transfer | 336.43 | 338.46 | 308.56 | 174.75 | 2.75 |

For example, at four sectors with stationary supports, single-anchor damage
adds approximately 37.60 simulated seconds, 34.82 cm of travel and 21.75 cm of
actor silk relative to intact construction, averaged over the matched seeds.
Multiple damage adds approximately 73.22 s, 68.45 cm and 35.75 cm. These are
effects within the imposed sector model, not estimates measured in spiders.

The moving-support means are longer than the stationary means in these eight
scenario/size comparisons. Travel is measured in material/frame-relative
coordinates under the executor's no-slip assumptions; its equality across
amplitudes should not be interpreted as proof that real spiders travel the
same distance in wind.

## Controller decision effort

Mean total measured decision wall time per trial in milliseconds, pooled over
80 trials per cell. This excludes simulated action execution and is not added
to the simulated times above. Tree snapshots are disabled for this timing.

| Scenario | State rules | Fresh HTN | Retained HTN |
|---|---:|---:|---:|
| Intact | 0.717 | 5.445 | 5.372 |
| Single damage | 0.839 | 8.392 | 9.950 |
| Multiple damage | 0.933 | 8.872 | 10.604 |
| Partial transfer | 0.828 | 8.508 | 9.566 |
| Unavailable anchors | 0.689 | 6.396 | 10.424 |
| Insufficient silk | 0.686 | 5.536 | 10.359 |

These are implementation wall-clock measurements on one machine. The rule
controller is timed when it selects actions; the HTN controllers are timed
when they make planning calls, including adapter/feasibility work. Initialization,
physical execution and tree snapshots are outside these timings. Operating
system scheduling and other machine load can affect the results; neither the
numbers nor ratios are algorithmic complexity or biological-speed claims.

Fresh versus retained mean **method calls**, compared within the same IPyHOP
engine, were 111.30 versus 93.95 for single damage; 117.85 versus 101.775 for
multiple damage; and 110.30 versus 92.95 for transfer. Retention therefore
reduced this count in those feasible disruptions, while its mean decision wall
time was higher in the same scenarios. In both infeasible controls fresh used
70 mean calls versus 91 for retained. In the intact case both used 69 and made
no event-triggered replan. Method calls and rule-controller decisions are not
equivalent quantities and are not compared as if they were.

For a specific prespecified stratum (8 sectors, 10 cm amplitude, 20 seeds),
retained minus fresh total decision time was +2.83 ms for single damage, with
a pointwise paired bootstrap interval [1.84, 4.60] ms. It used 23.25 fewer
method calls on average, interval [−23.45, −23.10]. These intervals describe
this run's paired measurements, and should not be generalized across machines
or treated as multiplicity-adjusted hypothesis tests.

## Reproducibility and interpretation

Compared with the original 1,920-trial run, the matched keys and source-hash
manifests were identical. Every saved non-timing field was identical for all
1,920 pairs of trial records, including outcomes, pre/post hashes, costs,
failure reasons and method counts. Measured wall-time values varied; the
recovery-time field is zero in some cases and did not vary there. The rerun
therefore verifies deterministic reproduction under the same inputs and local
software, while supplying no new set of phases, animals or experimental cases.

The test command `python3 -m pytest -q spider_web_mulder/tests
spider_web_recovery/tests spider_web_htn_updated/tests` passed **226 tests**.
All 114 recorded bulk artifact hashes were verified. The current run's
source, protocol, settings, upstream planner revision and runtime versions are
in its [provenance manifest](evidence/e1_v1_rerun/provenance.json). Source was
uncommitted above base `61d18d8`; the manifest's hashes identify the actual
files used. Same-session data review found no blocking issue; source graph was
unavailable, so the implementation and records were read directly.

The experiment supports a scoped statement that current-state observation and
authored repair rules handle these simulated structure changes. It does **not**
show a completion or physical-cost advantage of HTN over those rules, or a
measured wall-time benefit from retaining the tree. It does not show that real
spiders use HTN planning. Scaffold geometry, ideal observations, simple capture
costs and aligned transfer are assumptions, and the experiment does not
reproduce the Peters or Eberhard biological protocols.

## Files

- [Curated summary and exact run-to-run/controller audits](evidence/e1_v1_rerun_summary.json)
- [All 1,920 trial records](evidence/e1_v1_rerun/trials.csv)
- [Stratified completion and effort summaries](evidence/e1_v1_rerun/summary.json)
- [Paired contrasts and denominators](evidence/e1_v1_rerun/paired.csv)
- [Generated experiment report](evidence/e1_v1_rerun/report.md)
- [Completion figure](evidence/e1_v1_rerun/completion.svg)
- Full local run including traces and diagnostic trees:
  `mulder_results/e1_v1_20261112_rerun/`.

Exact command, run from the repository root:

```sh
python3 -m spider_web_recovery.e1_benchmark --output mulder_results/e1_v1_20261112_rerun
```

Use a new output directory for another run; existing directories are refused.
