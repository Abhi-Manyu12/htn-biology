# E1: recovery from observed web structure

Protocol version 1, fixed 2026-11-12 before the main sweep. Branch:
`development/E1`. Literature motivation: Peters (1970) and Eberhard (2019),
as assessed in [SPIDER_HTN_LITERATURE.md](SPIDER_HTN_LITERATURE.md).
This is a computational sector benchmark inspired by those observations,
not a replication of their animal protocols.

## Question and implementation scope

Does HTN recovery improve completion or construction costs over an equally
informed state-based controller after the web's current structure changes?
Does retaining an IPyHOP task tree improve on fresh planning?

Reuse `spider_web_recovery`'s World, validity predicates, primitive actions,
graph routing, resource lower bound, upstream IPyHOP adapter and Mulder tracking
executor. Add an independent E1 actor/protocol and report module. Existing
recovery and Mulder runs and default entry points stay unchanged.

Four controllers receive the same physical observations and primitive actions:

- `history`: initial IPyHOP plan, cached continuation; no recovery. This is an
  intentionally limited diagnostic ablation, not the main competing approach.
- `state_rules`: observe before each action; repair invalid radii in index order
  with primary/backup anchors, return to hub, restore invalidated capture effects,
  then construct outstanding capture sectors. Shared routing/validity/resource
  knowledge; no HTN or search over task decompositions.
- `fresh_htn`: fresh-root IPyHOP on initial planning, event notification and
  rejected commands.
- `retained_htn`: same domain/engine; retain the tree and re-enter at the actual
  next action's tree-node identifier after notification or rejection.

All controllers use the same precondition validator and terminal physical-goal
check. The history ablation receives no automatic corrective plan. Anchor choice
and work ordering are authored knowledge, not learning. Rule decisions and HTN
method calls are different quantities; compare overall decision wall time for
implementation costs and method calls only within the same HTN engine.

## Events and accounting

Trigger immediately after the first `floor(sectors/2)` captures complete, with
all radii built and the actor at the hub. Record and compare pre/post checkpoint
hashes across controllers. Failure to reach a checkpoint is counted and reported.
An event occurs once; it does not reject or consume an otherwise successful
construction action. HTN actors proactively refresh at the next queued leaf.

The seed selects a sector among already completed capture sectors. Cases:

1. `intact`: observation-only sham; no forced refresh.
2. `damage_single`: permanently remove the selected primary anchor and its
   dependent effects; backup remains available.
3. `damage_multi`: remove selected and next primary anchors and dependent effects.
4. `transfer_partial`: externally replace the web by a donor partial web in an
   aligned frame. Donor radii use backup anchors, except the selected missing
   radius; donor captures occupy the initial half where dependencies exist.
   All anchors remain available. The actor stays at the common hub coordinate.
   Handling takes 5 simulated seconds, external displacement is 0 cm by design,
   and no locomotor travel is credited. Actor silk stock and expenditure carry
   over; displaced and donor structural silk are recorded separately. This
   aligned transfer is not a model of free navigation or arbitrary transport.
5. `damage_unavailable`: selected primary and backup anchors unavailable.
6. `damage_resource`: single-anchor damage followed by an external stock reduction
   to one cm below the shared necessary completion bound. Lost stock is recorded.

Maintain actor-stock conservation: used + remaining + externally lost = initial
stock. Damage removes effects without refunding consumed silk. Transfer does not
charge imported donor silk to the actor. Count reconstruction of invalidated
effects separately from repetition of still-valid work and from first construction.

## Frozen primary sweep and analysis

- Sectors: 4 and 8; wrapper depth: 0.
- Supports: stationary and 10 cm amplitude at 0.05 Hz.
- Seeds: 0–19; each selects forcing phase and intervention sector, not a spider.
- Four controllers × six scenarios × two sizes × two amplitudes × 20 seeds:
  **1,920 trials**. Rotate controller execution order with seed.
- Other values are the existing `Config` defaults (including 500 cm stock,
  1 cm/s movement, 500 attempts, 20 replans, 20,000 s deadline), recorded verbatim.
- Primary: valid completion, exposure, intact-work repetition and reconstruction.
- Secondary: rejected stale commands, elapsed time, travel, actor silk,
  decision wall time and same-engine method-call counts.
- Contrasts: fresh HTN minus state rules, retained HTN minus state rules,
  retained HTN minus fresh HTN. Pair by scenario, size, amplitude and seed.
- Completion/computational contrasts include failures. Physical-cost contrasts
  require both paired constructions to complete; report denominators.
- Stratified Wilson completion intervals; paired bootstrap differences with
  2,000 resamples and analysis seed 20261112. Pointwise descriptive intervals,
  no multiple-testing or population-level biological claims.
- Primary sweep disables tree snapshots. Save first-seed action traces and
  separate diagnostic tree examples; do not mix diagnostic timings into results.

## Acceptance criteria

| ID | Criterion |
|---|---|
| AC-1 | WHEN the common checkpoint is reached, every controller SHALL receive identical event state for each matched case. |
| AC-2 | WHEN damage/transfer changes effects, the actor SHALL preserve actual position, elapsed costs and stock conservation; donor structure SHALL be separately accounted. |
| AC-3 | WHEN a primitive is attempted, it SHALL satisfy observed route/resource/dependency preconditions before effects are committed. |
| AC-4 | WHEN valid work exists, capable controllers SHALL avoid rebuilding it; invalidated prior effects SHALL count as restoration. |
| AC-5 | IF a case is infeasible or a budget is exhausted, execution SHALL terminate and SHALL NOT report success from an empty plan. |
| AC-6 | WHEN retained recovery occurs, IPyHOP SHALL receive a real queued leaf ID; fresh recovery SHALL start from the root. |
| AC-7 | WHEN a sweep runs, it SHALL retain trial outcomes, settings, seeds, engine/source hashes and conditional paired denominators, and SHALL refuse an existing output directory. |
| AC-8 | WHEN the implementation is complete, existing software tests SHALL pass and prior numerical artifacts SHALL remain unchanged. |

Success means a correct, fair and reproducible comparison, including a possible
tie or worse HTN outcome. No parameter tuning to create a planner advantage.
