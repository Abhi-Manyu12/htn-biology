# Paper-facing experiment, version 3

The target is the stationary-versus-moving pattern in Mulder et al. (2021),
[DOI 10.1007/s00114-021-01725-1](https://link.springer.com/article/10.1007/s00114-021-01725-1).
The supplied PDF, especially Table 1 and pages 2–7, is the measurement source.
`paper_reference.json` records apparatus, sampling, reported p-values and
available sample sizes. No biological observations are invented.

## Run the complete study

```sh
python3 -m pip install -r requirements.txt
python3 -m spider_web_mulder.validation --seeds 30 --output mulder_results/paper_validation
python3 -m pytest -q spider_web_mulder/tests spider_web_htn_updated/tests
```

Default study: 2,280 trials. There are 30 paired initial phases in the two
primary executor profiles, and 12 in each sensitivity/ablation profile.
For a fast pipeline check, use `--seeds 2 --bootstrap 100 --suite core`.
Output must be a new or empty directory. The saved plots are standalone PNG
and SVG, produced using Matplotlib; reports require no network access.

Primary conditions use 5 and 10 cm peak displacement at 0.049 and 0.05 Hz.
Each seed/profile/controller has a single stationary control, reused across
frequency comparisons. The paper's roughly 40° shear swing provides an
additional consistency check: 30*tan(20°) ≈ 10.92 cm peak displacement for
affine shear, supporting the 10 cm peak convention. The 5 cm condition tests
apparatus uncertainty. Flexible corners need not deform exactly affinely.

## Mechanisms and ablations

| Profile | Question |
|---|---|
| endpoint | What happened under the old endpoint-only movement assumption? |
| tracking | Does continuous local feedback preserve construction without repeated planning? |
| tracking_dt_half | Do conclusions survive a smaller numerical step? |
| tracking_slow / tracking_fast | How sensitive are results to locomotion speed? |
| sensor_lag_1s / sensor_lag_5s | How much does ideal instantaneous sensing matter? |
| tracking_tight | Does a smaller attachment tolerance change completion? |
| repair_delay_1s | How does repair overhead affect conclusions? |
| flat_tracking / flat_slow | Does compound-task decomposition add value over the same prescribed action sequence? |
| phase_wait | Does an alternative HTN method improve outcomes enough to pay for waiting? |

All six controllers share the same executor within each primary profile.
Sensitivity profiles use local and predictive control to reduce duplication.
The phase-wait profile uses 0.5 cm/s and must be compared with tracking_slow
and flat_slow, not with a faster baseline. A method can choose a bounded pause
using a frozen-shear cost approximation; actual execution remains continuous.
Estimated waiting benefits are hypotheses, not guaranteed improvements.

Continuous execution bounds motion relative to the instantaneous substrate,
which carries the spider passively. It can consequently follow a rapidly
moving support without spending locomotion solely to compensate for room-frame
translation. This is an explicit no-slip contact assumption. It is not a
mechanical model of silk elasticity, tension, adhesion or breakage.

## Measurements

| Paper quantity | Implementation | Qualification |
|---|---|---|
| Construction time | Movement, separate contact dwell, waits and repair delays | Timing parameters require observational calibration |
| Distance covered | Exact frame-relative path and 10 s camera-sampled path | Paper-facing travel uses the latter cadence; interpolation is simulated |
| Phase allocation | Time and travel percentages for each phase | Frame remains separate; its assignment to the paper's radial phase is not guessed |
| Total web area | Convex polygonal envelope of accepted structural chords | An estimate of the image-defined area |
| Capture spiral area | Capture envelope minus inner hub envelope | Envelope is reconstructed from chords and radial intersections |
| Eccentricity | abs(1 − width/height), from cardinal extents | Exactly Table 1's formula, not conic-section eccentricity |
| Capture spiral count | Mean of deduplicated north and south ray crossings | Segment vertices count once |
| Mean mesh space | (North width + south width)/(North count + south count − 2) | Widths and counts come from accepted capture chords |
| Radial count | Count of definitive radial chords | Prescribed by the generator, so not independent evidence |

Only completed webs receive final geometry measurements. Failures retain
partial progress, attempted travel/time and failure reasons. A shorter failed
run is never interpreted as more efficient construction.

## Statistical interpretation

`comparisons.csv` and `comparisons.json` contain completion rates with Wilson
95% intervals and paired-bootstrap mean differences for each moving condition
against its stationary control. Continuous-cost and geometry contrasts include
only seed pairs in which both conditions complete. Pair counts are always
reported. Bootstrap resampling uses whole paired seeds, with a fixed analysis
seed. Intervals are pointwise and descriptive; no multiple-testing-adjusted
claim or biological equivalence threshold is inferred.

The uncertainty unit is an initial forcing phase, not a spider. Repeated
stationary runs are deterministic controls rather than simulated individual
biological variation. The paper used repeated observations and mixed models;
this simulation's bootstrap is not a reproduction of those statistical models.

Under zero-lag tracking, endpoints in material coordinates are imposed. Equal
ideal geometry and true corrected travel therefore follow partly by design.
Those metrics can check implementation consistency but cannot independently
validate the biological finding. Lagged sensing and movement constraints are
necessary stress tests. Time, failures, sampling effects and computational
cost remain useful outcomes.

## Empirical calibration and held-out comparisons

The publication states raw data are available from the corresponding author
upon reasonable request. They have not been supplied here; no email has been
sent. Supplementary figure/measurement links are identified on the publisher
page, but numerical trajectory data from the experimental cohort are not
silently replaced with measurements from an unrelated source.

The pipeline writes `biological_reference_template.csv`. To use genuine raw
observations later:

```sh
python3 -m spider_web_mulder.validation --reference-csv observations.csv --seeds 30 --output mulder_results/calibrated_validation
```

Rows require `spider_id`, `trial_id`, and `condition` (`rigid` or `moving`),
plus whichever measurement columns are available. Units are seconds, cm and
cm², with phase allocations in percent. Missing measurements stay missing.
Duplicate observations and non-finite measurements are rejected.

Calibration gives each spider equal weight after averaging its rigid trials.
It fits rectangular web width/height fractions from area and the tall-web
eccentricity branch, radial/capture counts from control observations, and
locomotion speed from control construction time with dwell held fixed. All
moving observations remain held out. Unfitted quantities and control residuals
are saved. Rectangular-envelope assumptions can make a fit inappropriate;
out-of-frame fits are rejected instead of silently clamped.

Without these observations the report explicitly says **not empirically
calibrated**. It can evaluate mechanisms and numerical consistency, but cannot
claim quantitative agreement with the original animals or infer their internal
planning mechanism. Graph-based traversal, silk mechanics, damaged-anchor
repair and willingness to build remain separate, unvalidated hypotheses.
