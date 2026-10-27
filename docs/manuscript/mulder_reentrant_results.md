# Re-entrant recovery in the Mulder construction HTN (v4)

## Research question and integration

We integrated the pinned upstream IPyHOP implementation [@bansod2021reentrant]
into `spider_web_mulder`, rather than transferring conclusions from the separate
sector-recovery benchmark. All six existing feedback/trigger policies can now
use the original GTPyhop backend, fresh-root IPyHOP, or retained-tree IPyHOP.
Both IPyHOP modes share identical methods and action adapters. The original
Mulder geometric construction, sinusoidal shear and movement executor remain
in use. Historical v3 outputs are preserved.

The hierarchy is web → construction components → segment refinement → physical
command. A segment refinement has a finite family of equivalent current-target
methods, each recomputing its endpoint command from the observed clock. These
are explicit command-refresh alternatives, not new physical construction
strategies. Their number is the per-action repair budget plus two, allowing a
proactive refresh and subsequent bounded execution retries. Domain action
failure conventions are adapted from GTPyhop's `False` to IPyHOP's `None`.

The actor retains the actual position, elapsed time and successful attachments.
For retained recovery it passes the current action's actual tree-node ID and
observed completion set/time to upstream `replan`. A proactive trigger similarly
invalidates the current command. The returned unexecuted suffix replaces the
queued suffix; it is not spliced into a cached component plan. Fresh IPyHOP
instead calls `plan` from the root. The legacy backend keeps its original
component/root repair scopes. Consequently, policy names identify feedback and
trigger rules; requested component/root scope is superseded by tree recovery
for IPyHOP. Explicit runtime assertions reject omitted, reordered or repeated
construction indices. Temporary misses are not permanently blacklisted.

Both IPyHOP modes use the same extra segment refinements. Comparisons between
them isolate tree retention more closely than comparisons with legacy GTPyhop,
which has fewer task nodes and retains its historical default search strategy.
The full published Run-Lazy-Refineahead actor is not reproduced.

## Experimental design

The reproducible command is:

```sh
python3 -m spider_web_mulder.recovery_comparison --seeds 10 --trace --output mulder_results/mulder_reentrant_v4
```

The factorial design uses three backends, six controller policies, ten paired
initial-phase seeds (0–9), two construction sizes and six profiles: 2,160 trials.
The small size uses 4 radii/1 auxiliary turn/1 capture turn; the configured size
uses 16/3/8. Profiles are rigid support, 10 cm motion at 0.049 Hz, 10 cm motion at
0.05 Hz, one synthetic miss at 0.05 Hz, one-second sensing lag at 0.05 Hz, and
legacy endpoint execution at 0.05 Hz. All use the direct method policy.
Other parameter values and source/dependency hashes are in `metadata.json`.
The configured input file is recorded verbatim by hash; profile overrides mean
this is a sweep, not a single run of the current frequency setting.

For the synthetic miss, the actor rejects the first otherwise accepted attempt
at segment index 10 exactly once, after paying its physical movement/time cost.
The override is explicitly logged. Controllers that fail before that point
receive no such event, and controllers without retries are allowed to fail.
This is a logical attachment-triggered disturbance, not a synchronized
absolute-time disturbance or measured failure process.

Within controller/seed, backend order rotates with seed. Success and computation
contrasts include failed trials; elapsed-time/travel contrasts require both runs
to complete. Intervals use 2,000 paired bootstrap replicates with analysis seed
20261020 and are pointwise without multiplicity correction. Simulated elapsed
time includes the configured repair delay, but excludes CPU planning time.
Planning wall time includes adaptation and leaf mapping; for the recorded seed-0
examples it also includes tree-snapshot instrumentation. Timing must therefore
be treated as implementation- and environment-dependent. Method-call contrasts
are unaffected by snapshot recording. Seeds describe forcing phases, not spiders.

## Interpretation limits

This integration adds retained symbolic recovery to the actual Mulder HTN; it
does not import the separate sector model's graph connectivity, alternative
anchors, silk resources or physical-damage observer. Mulder's geometry remains
prescribed and its movement is kinematic. Observed position remains in the
physical actor; the symbolic methods use completion indices and time, without
route planning. Additional structural dependencies and alternative construction
methods would be required to test those recovery abilities in this simulator.

A reduction in method calls does not establish faster planning, shorter
construction, greater biological plausibility or empirical validation of
Mulder's observations. Computational results below must retain these distinctions.

## Results

The main sweep completed **2,160 trials**. Across **all 720 matched
retained-versus-fresh IPyHOP pairs**, completion, number of completed actions,
repair counts, elapsed simulated time and total travel were exactly identical,
including failed runs. Tree retention did not improve physical outcomes in
these declared cases.

For the configured 16-radius HTN, selected results were:

| Profile and policy | Legacy component/root repair | Fresh IPyHOP | Retained IPyHOP |
|---|---:|---:|---:|
| 10 cm, 0.05 Hz, local feedback: completion | 10/10 | 10/10 | 10/10 |
| Synthetic miss, local_repair: completion | 10/10 | 10/10 | 10/10 |
| 1 s sensing lag, filtered: completion | 0/10 | 5/10 | 5/10 |
| Endpoint execution, each policy: completion | 0/10 | 0/10 | 0/10 |
| 10 cm, 0.05 Hz, full: mean method calls | 2,095 | 25,966 | 25,532 |

The last row's counts are directly comparable between the two IPyHOP modes;
legacy uses a different planner and fewer refinement tasks. Under full control,
retention reduced method invocations by 434 (1.67%; paired pointwise bootstrap
95% interval −434 to −434). It did not reduce repairs, construction time or
travel. Mean planning wall time increased from 1.816 s to 2.658 s, a paired
increase of 0.842 s (95% interval 0.748–0.945). Excluding recorded seed 0 leaves
1.823 s versus 2.628 s for nine seeds, so tree recording does not explain away
the observed slowdown. These measurements describe this implementation and
runtime, not an asymptotic comparison of the algorithms.

For filtered control at 0.05 Hz, retention reduced method calls by 175.4 on
average (95% interval −179.2 to −171.4), while planning wall time increased by
0.306 s (95% interval 0.232–0.363). Relative to legacy filtered repair, the
ordinary-motion elapsed-time difference was only −0.162 s (95% interval
−0.415 to 0.060); it does not establish a consistent improvement.

The one-second-lag filtered result is a real scoped completion gain over legacy:
5/10 versus 0/10, paired difference 0.5 (pointwise 95% bootstrap interval
0.2–0.8). It is shared by fresh and retained IPyHOP. To isolate the cause, we
ran **10 additional diagnostic trials** with the original GTPyhop symbolic
domain and controller, changing component replacement to whole-suffix/root
refresh. This control also completed 5/10 trials and matched each IPyHOP trial's
completion, completed actions, repair count, elapsed time and travel exactly.
Thus the improvement in this profile follows from refreshing the whole suffix;
it is not evidence of a unique benefit from retained-tree re-entry. The control
script and full results are retained under the research record.

This improvement is not universal: the small HTN's lagged filtered completion
decreased from 3/10 with legacy repair to 2/10 with either IPyHOP mode. All four
retry-capable policies recovered from the single synthetic miss with every
backend and both construction sizes. Endpoint execution still failed in all
360 declared endpoint trials. Changes to planning do not automatically remove
movement-model or sensing limitations.

These results support keeping retained recovery available as an experimental
backend. They do not support making it the default for this fixed construction
sequence on the basis of speed or completion. The separate graph/dependency
study tests richer recovery mechanisms; testing those mechanisms in Mulder
requires adding explicit physical dependencies and alternative methods.

## Evidence and verification

- [Curated main-study evidence](../research/evidence/mulder_reentrant_v4_summary.json)
- [Whole-suffix control evidence](../research/evidence/mulder_suffix_control.json)
- [Control script](../research/probes/mulder_suffix_control.py)
- Bulk report: `mulder_results/mulder_reentrant_v4/report.html`; trials, paired
  contrasts, settings/hashes and recorded actual trees are alongside it.
- **176 automated tests passed** across Mulder, retained recovery and the earlier
  updated HTN package. These checks establish software behavior, not biological
  validation. The report overview was added after the scope-control experiment;
  `report_notes.json` records that report-only postprocessing.
