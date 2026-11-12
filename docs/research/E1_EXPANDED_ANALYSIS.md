# Analysis of the expanded E1 results

This is a post-hoc analysis of the prespecified expanded study, not another
experiment. Full methods and figures are in
[the expanded results](../manuscript/e1_expanded_results.md). Input trial and
paired-table hashes, numerical outputs and exploratory-bootstrap settings are
in [e1_expanded_posthoc_analysis.json](evidence/e1_expanded_posthoc_analysis.json).

## Main result: observation and repair knowledge, not an HTN advantage

For each of the three comparisons among the state-rule, fresh-HTN and
retained-HTN controllers, completion agrees in 1,320/1,320 cases. There are
830 pairs in which both controllers succeed, and all 830 pairs have exactly
the same simulated elapsed time, travel and actor silk cost. The other 490
pairs fail and cannot contribute to successful-pair physical comparisons.
This outcome extends to the largest tested webs and the tested resource and
motion settings. These are shared-state, shared-repair implementations with
authored work ordering: the finding is a boundary case for this design, not a
proof that rule-based control and HTN planning are generally equivalent.

Of the 1,320 matched cases, 1,200 have identical pre- and post-intervention
observed state for all controllers. The remaining 120 are −1 cm stock-margin
cases, where every controller stops before reaching the intervention. These
unexposed cases cannot demonstrate success or failure *in response to damage*.
The necessary resource guard rejects them at the start; this is not a model of
an animal spending its stock and discovering scarcity later.

## Why the 20 cm stock margin sometimes succeeds

In the model, each newly built radius costs 14 cm, each capture sector costs
5 cm, and damage to a radius invalidates adjacent capture sectors that have
already been built. The event occurs after the first half of capture sectors.
When the selected radius is the last sector in that completed half, only one
already-built capture sector is invalidated. Rebuilding that radius and capture
requires an extra **19 cm**. If an earlier completed sector is selected, two
already-built capture sectors are invalidated, requiring **24 cm** extra. Thus
the supplied **20 cm** margin succeeds in the first case and fails in the
second under this implementation's guard and fixed action costs.

This explanation matches **all 30 state-rule single-damage cases** at +20 cm:

| Size | Last completed capture sector selected | Completion |
|---:|---:|---:|
| 8 sectors | 3/10 seeds | 3/10 |
| 16 sectors | 1/10 seeds | 1/10 |
| 32 sectors | 1/10 seeds | 1/10 |

The same outcomes occur for both HTN controllers. The apparent decline across
sizes reflects these sampled target choices and the model's checkpoint and
cost rules; it is not established evidence that larger real webs are less
repairable. The sector is chosen from the first half of the web, and phase and
target are derived from the same seed. Ten seeds per stratum are not a sample
of ten spiders. Multiple damage requires two radii to be restored, at least
28 cm before capture restoration, explaining 0/10 at +20 cm. Every tested
multiple-damage case completed at +60 cm, but the design tested only four
discrete stock margins; it did not measure a continuous threshold.

## Scale and planning effort

With 10 cm amplitude, multiple damage and 1,000 cm stock, all capable
controllers completed 10/10 cases at each tested size. At 32 sectors, mean
measured decision times were 46.216 ms (rules), 133.045 ms (fresh) and
154.647 ms (retained). Fresh used 535.6 mean method calls; retained used
442.4, approximately 17.4% fewer, while taking approximately 16.2% more
measured wall time in that case. Fewer decompositions are therefore not a
sufficient explanation of actual implementation time; the measurement
includes work other than method calls.

The retained-minus-fresh mean was −0.937 ms at 24 sectors, with a paired
pointwise bootstrap interval [−11.961, 8.241] ms. At 32 sectors the mean
was +21.602 ms, interval [9.785, 35.946] ms. Only 10 cases were used in each
stratum, and the intervals are descriptive, pointwise and unadjusted. The
variation rules out a claim that this experiment proves retained planning is
always faster or always slower. Single-machine wall times are not a complexity
bound; initial planning and per-action rule selection have different timing
boundaries. The history-only line in the graph consists of failed cases.

## Stronger modeled support movement

As an **exploratory** matched-seed comparison, compare single-damage cases at
0.05 Hz against stationary supports. The 0/10 cm cases come from the scaling
suite and the 20/30 cm cases from the movement suite; all use 1,000 cm stock,
the same sector sizes and seeds. The state-rule values below also match both
HTN controllers' successful physical outcomes.

| Sectors | Amplitude | Extra simulated time, mean | Relative to stationary mean | Pointwise 95% paired bootstrap interval |
|---:|---:|---:|---:|---:|
| 8 | 10 cm | 2.14 s | 0.64% | 1.55–2.77 s |
| 8 | 20 cm | 7.55 s | 2.28% | 6.68–8.41 s |
| 8 | 30 cm | 18.79 s | 5.67% | 15.93–21.80 s |
| 24 | 10 cm | 7.53 s | 0.82% | 5.89–9.17 s |
| 24 | 20 cm | 17.43 s | 1.90% | 14.25–20.68 s |
| 24 | 30 cm | 50.13 s | 5.47% | 48.81–51.44 s |

Each comparison contains 10 both-successful pairs. These cross-suite
contrasts were not a prespecified primary analysis; bootstrap seed 20261114
and 2,000 resamples were chosen for this descriptive analysis, with no
multiplicity adjustment. All 240 state-rule motion-stress trials completed,
as did the matching fresh and retained trials. Movement is an imposed affine,
no-slip support model with ideal sensing; the values are not estimates of
spider performance in natural wind.

## What this contributes to a paper

A defensible contribution is an implementation and evaluation of
observed-structure recovery, showing that in this authored sector benchmark
a state-rule controller matches the tested HTN variants on completion and
physical costs. The partial-stock result is useful because the dependency
structure explains *why* some otherwise matched trials succeed. The planning
result shows that counting method calls alone can miss wall-time overhead.
These conclusions are conditional on the current simulation, test cases and
machine. Independent biological observations, alternative structures, less
complete sensing and broader performance studies remain possible future work.
No new experiment here establishes that spiders use HTN planning.
