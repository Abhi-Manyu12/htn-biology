# Retained-tree execution recovery

This package integrates the **actual upstream IPyHOP planner** with an observed-
state construction actor. It is separate from the six-controller Mulder v3
experiment: existing outputs and its execution policies are unchanged.

## Run

```sh
python3 -m pip install -r requirements.txt
python3 -m spider_web_recovery --seeds 10 --trace --output mulder_results/recovery_v1
python3 -m pytest -q spider_web_recovery/tests spider_web_mulder/tests spider_web_htn_updated/tests
```

The default study runs 2,240 trials: four backends × seven scenarios × ten
seeds × two sector counts × two wrapper depths × two movement amplitudes.
For a short case:

```sh
python3 -m spider_web_recovery --seeds 1 --sectors 4 --depths 0 --amplitudes 10 --scenarios permanent_anchor --trace --output mulder_results/recovery_example
```

Output directories must be empty. `--trace` saves representative seed-0 action
ledgers, observed states, solution-tree snapshots and SVGs. `report.html` links
to one permanent-anchor example. Old/new tree colours indicate refinement tags,
not a guarantee that an old physical effect remains valid.

## Source and dependencies

The author's BSD-licensed source is preserved without modification at
[`third_party/IPyHOP`](../third_party/IPyHOP), revision
`bdda21012b2396aed9a91980af8fbb71dbcb7075`.
`UPSTREAM.json` records individual hashes and `LICENSE` retains its terms.
The adapter checks that the vendored module is actually imported; the runner
checks source integrity. Upstream's historical requirements are retained for
provenance, not installed verbatim. The tested runtime uses GTPyhop 1.9.7 and
NetworkX 3.4.2; each run records runtime versions.

## Shared domain

`domain.py` defines a hub, scaffold junctions, primary and backup attachment
sites, definitive radii and dependent capture sectors. Scaffolds exist at the
start. Completed valid radii become traversable links; losing an attachment
invalidates its radius and dependent capture sectors. The planner sees actual
position, traversable/blocked links, attachment availability, valid structure,
remaining silk, and clock time.

Travel methods compute a shortest path over the current graph. Execution uses
the v3 continuous tracker on every individual edge, starting at the actual
position. Failed attachments do not teleport the spider to the hub. Returning
over a previously traversed edge during repair is measured as physical
retracing. A new route may instead use scaffold edges not previously visited.

The second travel method re-evaluates the same routing function after re-entry;
it supplies an untried refinement under changed observations. Both backends
receive this same domain-engineering choice. There are two attachment choices,
not a learned or unlimited method generator. Wrapper depth adds nested task
nodes but does not itself add semantically different construction decisions.

Capture construction is an abstract 5 cm resource-consuming operation at the
hub, dependent on its own and previous radius. It is not a physically simulated
capture spiral. Silk values, scaffolds and event effects are benchmark
assumptions. These outputs are not quantitative biological measurements and
must not be pooled with the 2,280-trial Mulder study.

## Backends

| Name | Planning and recovery |
|---|---|
| fresh_root | Fresh GTPyhop call for build_web, with progress guards and explicitly selected iterative DFS backtracking |
| component | Same GTPyhop search, re-decomposing only the failed action's owner and retaining later cached actions |
| ipyhop_fresh | The pinned IPyHOP engine, calling plan() afresh on every recovery |
| ipyhop | Same IPyHOP engine, preserving its solution tree and calling replan(observed_state, failed_node_id) |

The same-engine IPyHOP contrast is important: GTPyhop's eager alternative
evaluation and IPyHOP's method iteration differ. Comparing their method counts
alone would conflate engine differences with retained-tree recovery.

`backends.py` converts None/False failure conventions and maps the returned
primitive sequence to concrete tree leaf IDs. No tree is fabricated from a
flat plan. Re-entry is delegated to upstream IPyHOP, including its suffix
un-refinement and backtracking. An empty returned plan is considered successful
only if the actual observed construction objective holds. The GTPyhop adapter
restores the previous global search strategy after each call.

The actor checks immediate preconditions and observes actual outcomes. This
is an IPyHOP-backed actor inspired by the published integration, not a verbatim
reproduction of the complete Run-Lazy-Refineahead simulator/actor experiment.
It does not run an expensive whole-suffix physical simulator before every step.

## Failure cases

| Scenario | Observation and response tested |
|---|---|
| clean | Common construction without an injected event |
| transient_attachment | A single failed attempt consumes time/silk; retry the same command within budget, without permanent blacklisting |
| permanent_anchor | A primary attachment becomes unavailable; select a backup and update later dependent commitments |
| route_block | An observed edge is blocked; travel must use another actual graph path |
| unreachable | All edges leaving the current site are blocked; terminate infeasible |
| silk_depletion | Remaining resource is reduced below a necessary lower bound; terminate without restoring spent resource |
| prefix_damage | Previously completed structure loses support; invalidate effects and explicitly reconstruct affected radius/capture work |

The observer separates history from current valid effects. Reconstructing a
damaged completed sector is legitimate; blindly repeating still-valid work is
counted separately. Resource accounting satisfies initial silk = consumed +
remaining + externally lost. A shared necessary resource bound rejects known
infeasibility before exponential exploration; it is domain knowledge supplied
equally to every backend.

Events are reproducible logical-action triggers, not identical absolute-time
signals. Each non-clean trial has one declared event; exposure is recorded.
Seeds control initial motion phase and the target sector. No stream of random
draws is consumed differently by different planners.

## Outputs and interpretation

- trials.json/CSV: success and failure, observed terminal state, resources,
  attempts, stale-precondition detections, physical travel and repairs.
- summary.json/CSV: stratified results by backend, scenario, size, depth and
  amplitude. The compact report also shows descriptive pooled counts.
- paired.json/CSV: retained-minus-fresh IPyHOP effects with pointwise paired
  bootstrap intervals over matched seeds. Planning effort includes infeasible
  cases; construction costs include only pairs that both complete.
- provenance.json: source hashes, runtime versions, declared event protocol,
  complete case settings and upstream revision/license/hash manifest.

`planning_wall_s` includes adapter setup and tree snapshot overhead. Upstream
iteration counts are recorded as reported by IPyHOP. Actor attempt/repair/time
limits terminate execution; they are not a general hard timeout for arbitrary
recursive planning domains. The provided domain uses finite refinement choices
and bounded wrapper depth.

This benchmark tests known recovery mechanisms with authored dependencies. It
does not establish a new recovery algorithm, general biological cognition,
silk mechanics, or superiority on arbitrary roadblocks.
