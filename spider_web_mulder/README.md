# Moving-support HTN experiments

An independent experiment package on `feat_mulder`, inspired by Mulder et al.
(2021), **Dynamic environments do not appear to constrain spider web building
behaviour**, DOI: [10.1007/s00114-021-01725-1](https://doi.org/10.1007/s00114-021-01725-1).
The existing Zschokke packages and their configuration are unchanged.

**Version 3:** continuous tracking is now the configured executor. Start with
[PAPER_VALIDATION.md](PAPER_VALIDATION.md) for the paper-facing study, confidence
intervals, sensitivity profiles, flat-planner ablations, and calibration rules.

```sh
python3 -m spider_web_mulder.validation --seeds 30 --output mulder_results/paper_validation
```

This runs 2,280 trials by default. Stationary controls are not duplicated across
frequencies. Old version 1/2 artifacts remain unchanged and must not be pooled
with the new executor's results.

For a step-by-step controller comparison, run:

```sh
python3 -m spider_web_mulder.diagnostics --amplitude 5 --frequency 0.05 --seed 0 --output mulder_results/diagnostics
```

Open the generated `report.html` for a filterable complete event ledger,
controller timelines, attachment-error plots and first-failure controlled
replays. `report.md` is a plain-text companion; `ledger.csv` / `ledger.json`
retain all decision values, target coordinates, target ages, plan IDs and
attempts. `action_map.csv` / `action_map.json` map every prescribed segment
against the six controllers, including retries and segments never reached.
[CONTROLLER_AUDIT.md](CONTROLLER_AUDIT.md) documents the controller
fixes, tested contracts, and remaining model assumptions in version 2.
Earlier output directories retain their original version 1/2 results.
The diagnostic command defaults to the legacy endpoint executor for comparison;
add `--execution-mode tracking` to inspect the new executor.

The question is which controller capabilities preserve construction under
moving supports, and when extra planning earns its computational cost. Results
are tests of this computational model, not a reproduction of spider cognition
or independent verification of the biological experiment.

## Run

From the repository root, with Python 3, GTPyhop and PyYAML installed:

```sh
python3 -m pip install -r requirements.txt
python3 -m spider_web_mulder --output mulder_results/pilot
```

The default pilot runs 270 trials: six controllers × five seeds × three
amplitudes × three frequencies. Each seed selects an initial phase of the same
continuous sinusoid for all controllers in its condition. The five seeds are
a smoke/pilot sample, not a sufficient scientific evaluation.

For a small run with action traces and SVG drawings:

```sh
python3 -m spider_web_mulder --seeds 0 1 --amplitudes 0 10 --frequencies 0.05 --output mulder_results/quick --trace
python3 -m pytest -q spider_web_mulder/tests spider_web_htn_updated/tests
```

Edit this package's `config.yaml`, or provide `--config path/to/config.yaml`.
CLI sweep flags override the experiment section. Output directories must be
empty to avoid overwriting results. Do not apply the old `SPIDER_WEB_CONFIG`
environment override to this package; it has its own configuration loader.

## Model and units

Lengths are centimetres and time is seconds. In material/frame coordinates,
the frame is a 30 × 30 square. Configurable web width/height fractions allow
fitting a smaller rectangular envelope while retaining the apparatus size.
Its world coordinates are

```text
x_world = x_material + (1 - y / height) * A * sin(2π f t + phase)
y_world = y_material
```

The top is fixed; the bottom translates horizontally. This is an affine shear
approximation to the paper's flexible frame. Affine shear preserves area;
invariance of the ideal frame area is consequently imposed by this geometry,
not independent evidence supporting the biological finding. `amplitude_cm` is displacement
from the centre, so 10 cm gives 20 cm peak-to-peak. The paper describes the
movement approximately; this convention is explicit and amplitude should be
swept rather than treated as an exact apparatus calibration. The 0.1 Hz
condition is an extrapolation: pilot spiders in the paper refused to build
above 0.05 Hz. This simulator has no willingness/abandonment mechanism.

The HTN decomposes construction into frame edges, individual radii, auxiliary
turns, and capture turns, then segment actions. It begins with an established
hub and assumes traversal access. Exploration, bridging, support selection,
route connectivity, thread failure, tension and viscoelastic mechanics are
outside this version. Auxiliary threads remain present. The segment order and
counts are prescribed. The optional `phase_wait` method policy chooses between
immediate construction and a bounded wait for a nominally cheaper support phase;
it does not choose new supports or learn the web geometry.

GTPyhop generates ordered symbolic plans. `execution_mode: tracking` moves
continuously toward the current sensed destination, bounding locomotion relative
to the instantaneous substrate geometry and assuming passive no-slip advection.
Attachment dwell is separate from movement. `sensor_tau_s` independently controls
sensory lag; zero is ideal instantaneous feedback. Speed, sensor lag, dwell and
action deadline are assumptions unless fitted against independent observations.

`execution_mode: endpoint` preserves the previous world-space interpolation and
single bounded correction. Its correction limit/speed remain available for
historical and mechanism comparisons. Continuous tracking does not use that
endpoint correction budget.

Accepted endpoints become the starting points of subsequent actions, retaining
geometric error. Failed attempts consume time/travel but do not commit a
finished thread. Repair waits preserve the spider's material position. This
is a deliberately simplified kinematic construction model, not a physical
simulation of how the spider reaches or remains attached to silk.

## Controllers

| Name | Behavior |
|---|---|
| `fixed` | One initial plan with frozen world-space endpoint commands; no correction or repair. |
| `local` | Same plan plus executor feedback; stops on attachment failure. |
| `local_repair` | Feedback plus reactive replanning of the current compound task after a failed attachment. |
| `filtered` | Feedback and reactive repair, plus task refresh when exponentially filtered endpoint drift exceeds a threshold. |
| `full` | Feedback and reactive repair, plus rebuilding the remaining web plan at action boundaries when support displacement changes. |
| `predictive` | Feedback and reactive repair, plus task refresh when the executor-specific margin is negative. |

`filtered` filters the **repair trigger**, not the spider's sensory feedback.
The estimate initializes to the current drift on entering a new component,
then uses time-aware exponential updates; refreshing the component clears it.
`full` detects changes at action boundaries, not at every integration sample.
Its ideal observer checks whether motion occurred during the interval, even
when the frame returns to its previous position. After a failed-action replan,
the fresh retry executes once without a duplicate proactive refresh.
With endpoint execution the predictive policy samples drift over a capped
horizon. With tracking it bounds deformation-dependent task duration and
estimates error from sensory lag. Neither is a general feasibility guarantee
under unknown disturbances. Method selection is a separate HTN ablation.
A repair refreshes endpoint commands after
a configured simulated delay. Completed actions are preserved. All controllers
that repair share the same retry budget per action.

This comparison deliberately gives all adaptive planners the same local
feedback capability. `local` and `local_repair` are important controls: more
replanning is not assumed to improve construction. Failure is a valid outcome;
parameters must not be tuned merely to make a preferred planner win.

## Outputs and interpretation

- `metadata.json`: settings, sweep parameters, seeds and assumptions.
- `trials.csv`: success, failure reason, partial progress, elapsed time,
  frame-relative travel, phase time/travel, accepted thread chord lengths,
  planning calls, compound-method invocations, repairs and prediction cost.
- `summary.json`: Wilson 95% success intervals, paired success differences
  against `local`, mean repairs, and travel conditional on success.
- With `--trace`: per-action/per-repair JSON and a material-coordinate SVG of
  accepted threads for each trial, including partial constructions.

`planning_wall_s` measures GTPyhop calls. `prediction_wall_s` separately measures
forecast checks, so planning-call savings cannot conceal predictive overhead.
Wall times vary across runs; all other trial metrics and traces are seeded and
deterministic. Simulated repair delay is configurable and is not measured CPU
time. Phase times include repair delay and failed attempts.

`normalized_travel` divides total attempted travel by the ideal complete static
construction path. It is misleading by itself for failed runs that stop early;
always read it alongside success and completed actions. Thread chord length
is material-coordinate geometric length, not deposited silk or energy.
`frame_area_cm2` is the accepted frame-endpoint polygon, not capture area.
`capture_mesh_proxy_cm` is the mean distance between accepted capture points
one prescribed turn apart; it is not the exact ImageJ mesh measure from the
paper. Counts are imposed by the model, not independent validation evidence.
The SVG is a kinematic drawing, not a mechanically relaxed web.

Success intervals describe variability over initial phases, not biological
individuals. The same external forcing is used across controllers in absolute
simulation time; controllers with different durations encounter different
phases at corresponding task boundaries. No comparative significance claim
is inferred from five seeds or from overlapping intervals. Report failure
rates alongside success-conditioned cost to avoid survivorship bias.

## Next research steps

1. Sweep speed, correction limits, tolerances, sampling step and repair delay;
   check whether conclusions survive these assumptions.
2. Add continuous local tracking and independently vary sensory filtering.
3. Introduce graph-based traversal and dependencies between radii and spiral
   attachments, then structural damage and repairs that invalidate dependents.
4. Compare uncertain forecasts, conservative bounds and sampled prediction.
5. Add alternative HTN methods for support choice, reinforcement, task ordering
   and resource-aware construction. Separate method selection from parameter
   changes so hierarchy complexity has a measurable meaning.
6. Calibrate geometry and timing against the paper's supplementary material
   and observational data before attempting biological model validation.

## Integrated IPyHOP recovery (v4)

The actual Mulder construction HTN now supports a retained-tree IPyHOP backend,
using the same physical movement and geometry as the original controllers:

```sh
python3 -m spider_web_mulder.recovery_comparison --seeds 10 --trace --output mulder_results/mulder_reentrant_v4
```

Use a fresh output directory. This comparison runs all six controller policies
with the legacy backend, fresh-root IPyHOP and retained-tree IPyHOP. It loads the
config, overrides construction sizes/motion/execution in six declared profiles,
and writes exact settings, source hashes, paired summaries and an HTML report.
The ordinary `python3 -m spider_web_mulder` command retains historical behavior.

For individual trials:

```python
from spider_web_mulder.model import load_settings
from spider_web_mulder.experiment import run_trial
settings, _ = load_settings()
result, events = run_trial(settings, 'filtered', seed=0,
    planner_backend='ipyhop_retained', record_planner_tree=True)
```

The other backend values are `legacy` (default) and `ipyhop_fresh`.
`forced_miss_index=10` injects one explicitly logged synthetic rejection after
an otherwise successful attempt. This option tests recovery software and does
not model measured biological failures. Snapshots include actual tree IDs;
`scope` in controller decision events denotes the requested repair scope, while
IPyHOP determines recovery through tree re-entry and replaces the full remaining
suffix. Completed segments are guarded against repetition. No permanent
blacklisting is applied to transient misses. Finite current-target refinement
alternatives permit bounded retries without modifying upstream IPyHOP.

See [the manuscript integration record](../docs/manuscript/mulder_reentrant_results.md)
for experimental design, results and limits. The separate `spider_web_recovery`
package remains the graph/dependency/resource recovery experiment; these features
have not been silently added to the Mulder physical model.
