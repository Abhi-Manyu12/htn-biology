# Controller audit — model version 2

This audit checks whether the implemented policies follow their stated rules.
It does not establish biological validity or optimal controller behaviour.

## Corrections

1. **Motion detection could alias a complete cycle.** Previously `full` compared
   only the frame displacement at two action boundaries. Equal positions could
   hide substantial intervening movement. `Shear.changed_between()` now checks
   the interval's endpoints and sinusoidal extrema. This is an ideal observer
   using the known forcing, not a model of a spider's sensory sampling.
2. **A reactive retry could pay for another immediate proactive refresh.** The
   failure handler already replans the affected component at the current time.
   The next decision now skips its proactive trigger once, then executes that
   fresh retry. Further failures still use the common retry budget.
3. **Filtered drift mixed unrelated endpoints.** The filter now starts with the
   current drift when entering a different component. Within a component it
   uses the time-aware exponential update, and a refresh clears the estimate.
   The first observation of a component can consequently trigger a refresh
   immediately. This filters the repair decision, not sensory feedback.
4. **Policy capabilities were scattered through name comparisons.** `POLICIES`
   now explicitly specifies feedback, failure retries, and proactive trigger
   for each controller. The simulation engine remains shared.

Earlier `pilot` and `frequency_0049_vs_005` outputs are preserved and are model
version 1. New runs are version 2; do not combine them into a single result set
without accounting for these changes. The source hashes in new output metadata
identify the actual code used.

## Controller contracts

| Controller | Endpoint feedback | Retry after miss | Proactive trigger | Proactive scope |
|---|---|---|---|---|
| fixed | No | No | None | None |
| local | Yes | No | None | None |
| local_repair | Yes | Yes | None | None |
| filtered | Yes | Yes | Filtered drift > threshold | Current component |
| full | Yes | Yes | Motion since previous action boundary | Remaining web |
| predictive | Yes | Yes | Sampled margin < 0 | Current component |

All failure retries affect the current component. Completed actions are never
repeated. A component refresh preserves later components' saved commands; a
full refresh updates all remaining commands. Each refreshed target records
its own creation timestamp and plan ID. Proactive refreshes are counted in
`repairs`, but do not consume the failed-attempt retry budget.

## Verification

`tests/test_diagnostics.py` checks:

- Motion detection across a whole cycle and many cycles, plus stationary cases.
- Policy-specific feedback and permitted repair reasons for all six controllers.
- Trigger predicates, plan/repair counts, timestamps, retry limits and aggregate costs.
- Preservation of completed work and absence of an immediate duplicate refresh.
- Component-local filter initialization and target timestamp bookkeeping.
- Exact reproduction of first failures by diagnostic replay, without mutating
  original traces or changing the replay's starting state/time.
- Stationary and frozen-frame controls, report artifacts and output protection.

The existing experiment tests still check identical stationary execution,
seeded reproducibility, future-drift prediction, finite correction time,
integration convergence, failure budgets, configuration and CLI outputs.

## Execution assumptions retained deliberately

- `execute()` follows a straight world-space command, then performs one endpoint
  correction. It is not continuous tracking.
- The configured travel speed sets a nominal duration in departure-frame
  coordinates. Integrated frame-relative speed along the resulting world path
  is not enforced as a hard physical speed bound.
- Attachment time is currently included in the interpolated movement duration,
  rather than represented as a separate contact/anchoring phase.
- The forecast uses ideal segment lengths and sampled target drift over a capped
  horizon. It does not simulate the resulting correction, repair delay or later
  method choices. Positive margin is therefore not a feasibility guarantee.
- The elapsed-time budget is checked at action boundaries and after execution;
  it does not interrupt integration midway through a long action.
- GTPyhop uses process-global domain state. Trials run serially, not concurrently.
- Replanning refreshes coordinates in the same method, rather than choosing
  alternate supports or rebuilding a damaged structure.

These assumptions are visible in the diagnostics rather than changed merely
to improve completion. In particular, failures of this movement rule are not
proof of physical unreachability.

## Diagnostic command

```sh
python3 -m spider_web_mulder.diagnostics --amplitude 5 --frequency 0.05 --seed 0 --output mulder_results/my_diagnostic_run
python3 -m pytest -q spider_web_mulder/tests spider_web_htn_updated/tests
```

The report contains every event, timelines over frame displacement, error
plots and six isolated replays of each controller's first missed action.
The arrival oracle uses a dense search with refined roots and perfect future
forcing to select a bounded horizontal correction; it is a diagnostic
intervention, not an additional production controller or a reachability proof.
