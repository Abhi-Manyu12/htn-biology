# E1 expanded study: scaling, resources and support movement

Fixed 2026-11-13 before the primary expanded sweep. This extends the separate
E1 sector domain, without changing its actor, methods, interventions or old
artifacts. Questions: (1) how do completion and controller decision costs
change as sector count grows, with sufficient stock? (2) what happens when
stock approaches the model's construction requirement? (3) how sensitive are
completion and physical costs to larger/faster assumed support motion?

An exploratory implementation-speed pilot preceded this protocol: 4 controllers,
sectors 8/16/24/32, 1,000 cm initial stock, 10 cm amplitude, 0.05 Hz, single
seed 101, `damage_multi`; it is excluded from the expanded study. Its purpose
was to estimate runtime and test feasibility; no paper conclusion uses it.

## Prespecified configurations

Every case uses the same four E1 controllers and shared observed state/action
preconditions. All runs use E1 wrapper depth 0, speed 1 cm/s, max 500 action
attempts, max 20 replans, 20,000 s deadline and deterministic seeds 20–29,
not used in the original E1 sweep. The same seed selects phase and target via
separate initializations of the same PRNG; these are coupled and not animals.

1. **Scaling:** sectors 4, 8, 16, 24, 32; amplitudes 0 and 10 cm; frequency
   0.05 Hz; stock 1,000 cm. All six original E1 scenarios. Sufficient stock
   separates scaling from the old 500 cm limit; `damage_resource` still removes
   stock at the event. 2,400 trials.
2. **Resource boundary:** sectors 8, 16, 32; stock equal to `19 × sectors` cm
   plus −1, 0, 20 or 60 cm. The nominal 19 cm/sector is 14 cm radius plus
   5 cm capture, *before damage and restoration*, and is a property of this
   prescribed model, not a biological silk estimate. Amplitude 10 cm, frequency
   0.05 Hz; scenarios intact, single damage, multiple damage and transfer.
   1,920 trials. Negative or exhausted stock may prevent the event entirely;
   expose and count such cases rather than claiming equal intervention exposure.
3. **Movement stress:** sectors 8 and 24; amplitude 20 or 30 cm; frequency
   0.05 or 0.10 Hz; stock 1,000 cm; scenarios intact, single damage and partial
   transfer. 960 trials. Scaling cases at amplitudes 0 and 10 cm / 0.05 Hz
   provide contextual references for the same sizes and seeds; comparisons
   across these suites are exploratory and must retain exact case identities.

Total: **5,280 primary trials**, 1,320 four-controller cases. Rotate controller
order by seed. Save all outcomes including unexposed/failed runs, pre/post state
hashes, first-seed traces, exact configurations and code/upstream hashes; primary
tree snapshots disabled. Refuse an existing output directory. Since the full
configurations differ, match/stratify by suite, all configuration fields,
scenario and seed; never silently pair across stock or frequency.

## Analysis and figures

Report exposure separately from completion. Audit four unique controllers per
case and require either all unexposed or identical pre/post intervention hashes.
Prespecified controller contrasts: fresh minus rules, retained minus rules,
retained minus fresh; completion and wall times include all attempted pairs,
physical costs require both successful; retain denominators. Ten deterministic
seeds per stratum; bootstrap 2,000 paired resamples, seed 20261113, and Wilson
completion intervals are pointwise descriptive, not population claims. Wall
time is machine-specific decision timing, not theoretical complexity or
biological time. Comparisons involving separate suites are exploratory.

Create stand-alone PNG and SVG figures: (1) decision time versus web size for
all controllers during multiple damage, (2) completion versus stock margin for
multiple damage, split by size, (3) simulated physical recovery cost versus
size for feasible single/multiple damage, and (4) movement stress, including
success denominators. Include underlying data and generation code. Show zero
denominators as missing, never as zero cost. Sample seeds are not independent
spiders; web geometry, support deformation, transfer and sensing are imposed.

## Completion criteria

Verify controller matching, event exposure, true final goal, shared physical
preconditions, stock conservation, output/source hashes, historical-artifact
preservation and existing tests. Save complete tabular outcomes, stratified
summaries, paired contrasts, provenance and figures under `docs/`; bulk traces
and raw JSON under a new ignored `mulder_results/` directory. Update work log,
claim ledger and manuscript evidence; distinguish software tests, model outcomes
and empirical biological validation. Negative outcomes are reportable.
