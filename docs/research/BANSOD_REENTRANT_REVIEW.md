# Failure recovery and Bansod et al.: assessment

**Subsequent v4 integration:** retained-tree IPyHOP is now also wired into the
actual Mulder construction HTN, with a same-engine fresh-root comparison and
all six original trigger/feedback policies. See the
[Mulder integration record](../manuscript/mulder_reentrant_results.md).
The descriptions below audit historical v3 behavior; the default legacy mode
still uses that behavior. The new Mulder backend does not add the separate
sector model's graph/resource/damage semantics.

Initial review: 2026-10-20. The assessment below describes the original Mulder
actor and the proposal made at that time. **Subsequent implementation:** actual
upstream IPyHOP is now integrated and benchmarked in the separate
`spider_web_recovery` package. See its README and the later work-log entry.
The six Mulder v3 policies remain unchanged; the new actor is not a verbatim
reproduction of the paper's entire Run-Lazy-Refineahead experimental setup.

Primary source: Bansod, Nau, Patra and Roberts (2021), *Integrating Planning
and Acting With a Re-Entrant HTN Planner*, HPlan, pp. 26–34.
The supplied HPlan2021-paper5.pdf was read in full. Public author copy:
https://www.cs.umd.edu/users/nau/papers/bansod2021integrating.pdf.

## Three distinct meanings of going back

1. **Search backtracking:** abandon a hypothetical method refinement during
   planning and try another. No physical spider motion has occurred.
2. **Execution recovery:** use observations after a real action fails to revise
   unfinished work. Real time, travel, partial effects and position remain.
3. **Physical retracing:** navigate back along an existing web route to a hub,
   attachment or checkpoint. This requires explicit traversal actions and
   reachability constraints. Neither search backtracking nor re-entrancy
   automatically implements this behaviour.

The present Mulder package has domain-specific execution retries and fresh
re-decomposition. It has no general physical retracing or tree-resuming planner.
Ordinary planned returns to the hub in construction() are not failure recovery.

## What our code does

See `spider_web_mulder/experiment.py`, run_trial(), and
`spider_web_mulder/model.py`, make_state()/build_component().

```text
execute the next segment from the actual executor position
if accepted:
    record its geometry and add its index to state.done
    remove it from the pending list
else:
    retain time/travel and the actual reached position
    fixed/local: stop
    repair-capable policy: if an attachment miss and retry budget remains:
        wait the configured repair delay
        call find_plan() afresh for the current build_component task
        replace that component's pending actions
        keep later components' cached actions
    terminal time/action limits: stop
```

Proactive policies can instead request a component refresh or rebuild the
remaining web plan. Repaired targets get timestamps and plan IDs. A fresh retry
does not immediately pay for a second proactive refresh. The default failed
attachment retry budget is three additional attempts.

The replan input contains segments, support motion, symbolic completed indices
and snapshot time. Actual spider position is an executor-local variable; the
planner does not receive a complete geometric/resource state abstraction.
No search stack or full solution tree is retained. Task labels and segment
indices are manually supplied recovery context, not preserved decomposition
history with selected and untried methods.

`state.done` keeps accepted work from being repeated in this model. It is not
a proof that the work remains physically valid after damage. Failed attempts
do not commit a finished thread, and partial failed silk is not represented.
There is no blocked-route, anchor-loss or damaged-thread recovery model here.
Refreshing coordinates cannot itself solve a missing support or an unreachable
route. The phase_wait method offers timing alternatives, not alternate anchors.

The custom actor does not call gtpyhop.run_lazy_lookahead(). Calling it an
implementation of the paper's Run-Lazy-Lookahead would therefore be inaccurate.

## Search-strategy correction

The supplied paper describes the GTPyhop implementation of its time as
recursive. Our installed package is GTPyhop 1.9.7 and defaults to
`seek_plan_iterative`, documented by that package as iterative greedy with
irrevocable commitment to the first applicable method. It separately offers
`iterative_dfs_backtracking`. Repository code does not select either explicitly.

The [strategy probe](probes/planner_strategy.py) verifies this on a task whose
first applicable method has an impossible descendant and whose second method
succeeds: installed default returns False after trying only the first method;
explicit iterative DFS backtracking finds the second method's plan.
Exact observations and source hashes are in
[planner_strategy_audit.json](evidence/planner_strategy_audit.json).

This corrects prior generic descriptions of full backtracking in our current
runs. It does not invalidate every successful construction, but search
completeness, fallback behaviour and method-comparison claims require an
explicit strategy. Iteration alone is not retained-tree re-entrancy. Historical
runs have not been silently switched to DFS or relabelled as IPyHOP results.

## What the 2021 paper adds

Sections 4–5 and Algorithms 1–4 supply the relevant mechanisms:

- **IPyHOP** retains a solution task network, including task/method hierarchy
  and refinement context, rather than returning only a primitive sequence.
- A failure identifies a node in that network. The actor works from the newly
  observed state, not an imagined rollback of the physical world.
- **Un-Refine-Post**, Algorithm 3, removes refinements of later tasks along the
  ancestor/successor structure. This is conservative suffix invalidation, not
  a computation of the smallest causal dependency closure.
- **Backtrack**, Algorithm 2, exposes an earlier refinement choice. Planning
  resumes on the modified network and can consider another applicable method.
- **Run-Lazy-Refineahead**, Algorithm 4, simulates/executes a plan while it remains
  usable, observes execution, and re-enters the planner when continuation fails.
  Replanning marks new refinements; the actor extracts marked primitive tasks
  for subsequent execution instead of blindly replaying the original prefix.

This reduces repeated completed work in their setting; it is not an unconditional
guarantee that no earlier action will ever need to be executed again. Changed
physical conditions and task semantics can make reconstruction necessary.

Their RoboSub experiments used 17 primitive operators, 21 methods and 10
compound tasks. They report lower planning effort and action cost with similar
reward. Table 2's ratios (0.796 iterations, 0.682 action cost) are from the
matched-failure post-processing set, not universal wall-time speedups or
predictions for our spider domain. The domain and failure model differ.

## The most relevant counterexample for our implementation

In Section 5.2, Example 2, the paper shows why restarting only the failed
action's parent is insufficient: a failed action's effects may be needed by
a later task. Our component repair literally appends cached later components.

Illustrative future web domain, **not currently implemented**:

```text
build radius R on anchor A
build capture sector C using R and A

A becomes unavailable while completing R
repair R using an alternative anchor B
cached C still assumes A -> continuation may be invalid
```

A persistent network can expose affected future refinements for replanning.
It does not discover physical effects without suitable state observations and
operator/method models. If already-built silk subsequently loses support, even
earlier completed effects may need invalidation or an explicit restoration task.
Maintain execution history separately from currently valid structure.

## Usability assessment

**Recommendation: use IPyHOP as a serious candidate backend and baseline for
execution recovery when we add dependency-changing failures.** It directly
addresses retained planning context and repeated-task problems. Simply adding
more retries or changing our greedy planner to iterative DFS would not provide
that functionality.

It is unlikely to cure our earlier endpoint-tracking failures by itself. The
v3 study shows local continuous tracking can complete without replanning under
ideal sensing. Recovery algorithms need failures that require method changes
or invalidate downstream commitments to demonstrate their value.

Our disturbance logic asks **when to intervene**. The paper supplies a method
for **how to resume hierarchical planning**. These can be composed and tested
independently, using the same movement executor and domain knowledge.

The [author's repository](https://github.com/YashBansod/IPyHOP) documents
`planner.replan(state, fail_node_id)` and deterministic-command blacklisting.
Do not blacklist a periodic/transient miss permanently without a model of
its context; a permanent missing anchor is a different failure class.
The repository cites the related 2022 paper *HTN Replanning from the Middle*;
see the bibliography for both publications. The subsequent integration vendors
the unmodified implementation at bdda21012b2396aed9a91980af8fbb71dbcb7075,
preserving its BSD license and source hashes.

## Proposed experiment, not implemented

First add a small conformance domain before a larger web domain:

1. Completed-prefix case: two top-level tasks, late failure in the second.
   Check that the first task is not blindly repeated.
2. Dependent-suffix case: the repaired method changes a resource or attachment
   required later. Check that stale later refinements are reconsidered.
3. Irreversible-prefix case: an action consumes silk or creates structure.
   Recovery must use actual observed effects, not reset resource counters.
4. Transient versus permanent failure: distinguish retry, timed wait, method
   replacement and infeasibility; test termination budgets explicitly.
5. Physical roadblock: navigation must find a valid existing-thread path or
   construct an authorised alternative. Search-tree backtracking is not motion.

Then compare fresh-root replanning with progress guards, current component
refresh, conservative suffix replanning, and IPyHOP/Run-Lazy-Refineahead.
Pin comparable search strategies; keep the current greedy baseline separately
labelled rather than attributing a search-strategy difference to re-entrancy.
Use the same methods, world model, executor, disturbance schedule and budgets.

Increase decomposition depth, number of real alternatives, dependency fan-out
and construction size independently. Current segment count alone does not
measure hierarchy complexity. Record search effort, failure/retry counts,
repeated actions, invalidated refinements, repair scope, planning/monitoring
time, construction quality and domain-authoring burden. Method-call counts
in our instrumentation are not directly the paper's planner-iteration metric.

Failure schedules should be explicit and reproducible. Equal random seeds do
not guarantee equal events when execution paths consume draws differently.
Record event time, target identity and controller exposure; report any policy-
dependent differences instead of claiming perfectly matched failures.

## Manuscript positioning

Retained-tree recovery and selective replanning are prior work. We should cite
Bansod et al., not claim that bounded retries or component refresh invented
them. A possible future contribution is a validated disturbance/feasibility
trigger combined with a dependency-aware recovery backend, supported by fair
ablations. That novelty and benefit remain hypotheses requiring broader
literature review and experiments.
