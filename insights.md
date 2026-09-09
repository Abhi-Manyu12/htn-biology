# Insights Log

## 2026-09-09 — Why wind noise can never fail a plan (scope limitation, not a bug)

**The question:** if wind is genuinely random per run, shouldn't it ever
cause the web construction to fail, the way a real storm could snap a
thread or exhaust a spider's energy mid-build?

**Verified exhaustively:** grepped every operator in
`spider_web_htn_updated/operators.py` for every `return False` precondition
check (13 operators, ~20 checks total). Every single one gates on
*structural* state — `spider_pos`, `_can_reach` (BFS reachability over
threads/edges), thread existence, or `_is_available` (anchor removal). Not
one references `energy_expended`, a distance, or any cost value.
`energy_expended` itself is grepped across the whole package: it is
incremented in every movement operator, and never read back anywhere —
not in a precondition, not in a method, not in `config.yaml`. It exists
purely as a write-only bookkeeping field for the reported metric.

**Conclusion:** this is a real scope limitation of the current model, not
a bug being explained away. The domain has no notion of an energy budget,
thread fragility, fatigue, or a storm that could snap a thread and force
replanning — Zschokke's own distance-as-energy metric is tracked here only
as an efficiency *measurement*, never as a *constraint* the spider can run
out of. Wind noise, as currently modelled, can only ever change how much
silk gets reported as used, never whether the spider can physically
continue. A model that wanted wind to be able to fail a build would need
an explicit energy cap (reject actions once `energy_expended` exceeds some
threshold) or a thread-breakage mechanic — neither exists in
`spider_web_htn_updated`. Note this is exactly the kind of thing the
"storm event" / risk-adjusted utility extension (Archimedean vs.
logarithmic spiral switching, thread-breakage risk ω) sketched earlier in
this project would add, if pursued — it's a natural next step, not
something already covered.


Running log of findings from experiments, bug fixes, and analysis on the
`spider-web-updated` branch. Newest entries at the top. Each entry records
what changed, what we found, and why it matters — not just "ran X."

---

## 2026-09-09 — Wind-noise energy bug in `sensitivity.py` (fixed)

**What we found:** `_run_once_htn`'s reported energy under wind noise was
wrong. It replayed the found plan on the *original* `state` object after
`gtpyhop.find_plan` returned, redrawing wind noise from `state.rng` — but
GTPyhop never mutates the state you pass it. Internally it deep-copies state
on every action application and backtracks across many discarded branches,
returning only the plan (a list of action tuples), never the final state.
So `state.rng`'s position after planning reflects however many branches the
search tried and abandoned, not the accepted plan — the replay was drawing
fresh, meaningless noise, not reconstructing what the search actually paid.

This produced a spurious upward drift in reported HTN energy as wind σ
increased (600.1 → 605.9 across σ=0→0.5) that had nothing to do with the
real planning cost.

**What was never actually wrong:** HTN's *success rate* is genuinely,
structurally invariant to wind. Traced every operator precondition in
`operators.py` — none reads a cost value or `energy_expended`, only
positional/structural state (`spider_pos`, reachability, anchor
availability). A flat 100% success rate under wind is the mathematically
correct behavior of this domain, not a symptom of a bug.

**The fix:** `_run_once_htn` now executes the found plan exactly once, for
real, on a fresh copy of the initial state, using a dedicated RNG seeded
deterministically per trial (`f"htn-exec-{seed}"`) instead of continuing to
draw from the exhausted `state.rng`. Verified: energy now stays close to the
wind-free baseline (600.1 → 604.7 across σ=0→0.5) with variance that scales
correctly and linearly with σ (stdev 0 → 39.7).

**Why the residual small rise at σ≥0.4 is real, not a bug:** `wind_noise_factor`
clamps its multiplier at a floor of 0.1 (`max(1.0 + rng.gauss(0, std), 0.1)`)
so a gust can never fully cancel or reverse a cost. At low σ this floor is
rarely hit and has no effect on the mean. At σ=0.5, enough of the Gaussian's
left tail falls below the floor that the clamp introduces a measurable
positive bias — confirmed by simulating the clamp alone (100k draws):
mean multiplier is 1.0002 at σ=0.1, but 1.0082 at σ=0.5. Applied to a ~600cm
base plan, that's ~5cm — matches the observed ~4.6cm rise almost exactly.
This is the wind model behaving as documented, not a computation error.

**Files touched:** `spider_web_htn_updated/sensitivity.py` (`_run_once_htn`).
**Not touched, same bug likely present:** `spider_web_htn_updated/main.py`
(`_estimate_energy`) uses the identical stale-replay pattern. It's currently
harmless there because `compare.py`'s default config has wind disabled, so
the bug is latent, not active — but it would reproduce the same issue if
wind were ever turned on for a `compare.py`/`main.py` run.

---

## 2026-09-09 — HTN vs. flat-state baseline: full sensitivity sweep results

**Setup:** `spider_web_htn_updated/sensitivity.py`, 1000 seeded trials per
condition per group, HTN (Group A, `gtpyhop`-based) vs. the flat-state
random-walker baseline (Group B, `baseline.py`). Both groups see the same
seed per trial index (paired comparison) — identical anchor-removal draw
and wind stream for a given trial.

### Anchor-removal sweep (`sensitivity_comparison.csv`)

Each of the 8 usable anchor points independently removed with probability
*p* before construction starts, modelling a damaged/incomplete supporting
structure.

| p | HTN success | HTN energy (mean) | Baseline success | Baseline energy (mean) |
|---|---|---|---|---|
| 0.0 | 100.0% | 600.1 | 96.2% | 7911.4 |
| 0.1 | 100.0% | 565.8 | 96.1% | 7604.5 |
| 0.2 | 100.0% | 531.6 | 97.6% | 7434.8 |
| 0.3 | 100.0% | 498.8 | 98.6% | 7097.7 |
| 0.4 | 100.0% | 459.9 | 99.2% | 6506.3 |
| 0.5 | 99.7% | 425.0 | 99.3% | 6055.9 |
| 0.6 | 98.0% | 389.3 | 99.2% | 5658.5 |
| 0.7 | 93.2% | 359.1 | 99.8% | 5190.1 |
| 0.8 | 82.2% | 326.8 | 99.9% | 4788.9 |

**Findings:**
- HTN uses **8–14× less energy** than the baseline at every single removal
  probability tested. This is the most stable result in the whole study —
  it never crosses over in either sweep (anchor or wind).
- HTN's success rate degrades gracefully from 100% down to 82.2% as anchor
  loss increases past p≈0.5. This is not the planner crashing —
  `gtpyhop.find_plan` returns `False` cleanly every time, confirmed across
  18,000+ trials with zero exceptions. It's the proto-hub gate correctly
  refusing to proceed once fewer than `min_proto_radii` (4) anchors remain
  to converge on.
- Counter-intuitively, the **baseline's success rate stays flat-to-rising**
  (96%→~100%) as anchor loss increases, the opposite direction from HTN.
  This isn't a baseline bug — `baseline.py`'s own docstring already flags
  the reason: its completion check (`mark_*_spiral_done`) has no real
  structural-coherence requirement, unlike HTN's proto-hub gate, so it's a
  weaker bar to clear and doesn't get harder as anchors disappear the same
  way HTN's does.
- Practical reading for the write-up: anchor loss is the one place the two
  planners genuinely disagree — HTN trades some robustness at extreme
  anchor scarcity for a large, consistent energy advantage everywhere.

### Wind-noise sweep (`wind_sensitivity.csv`, corrected)

Anchor removal held at 0 to isolate wind alone. Every movement/thread cost
perturbed by `1 + 𝒩(0, σ)`, floored at 0.1×.

| σ | HTN success | HTN energy (mean / stdev) | Baseline success | Baseline energy (mean) |
|---|---|---|---|---|
| 0.00 | 100.0% | 600.1 / 0.0 | 96.4% | 8224.4 |
| 0.05 | 100.0% | 600.1 / 4.1 | 96.4% | 8225.6 |
| 0.10 | 100.0% | 600.1 / 8.2 | 96.4% | 8226.8 |
| 0.20 | 100.0% | 600.1 / 16.3 | 96.4% | 8229.1 |
| 0.30 | 100.0% | 600.2 / 24.5 | 96.4% | 8232.3 |
| 0.40 | 100.0% | 601.3 / 32.3 | 96.4% | 8247.3 |
| 0.50 | 100.0% | 604.7 / 39.7 | 96.4% | 8293.6 |

**Findings:**
- **Success rate is completely flat for both groups across all wind
  levels.** Wind perturbs cost, not reachability, so it structurally
  cannot block completion for either planner. See the bug entry above for
  why this is provably correct, not just an observed pattern.
- HTN's energy variance (stdev) grows linearly with σ — expected, since
  its plan structure is fixed/deterministic and wind is the *only* source
  of variance once a plan is chosen.
- Baseline's stdev barely moves (5613→6102, roughly flat) because it's
  already dominated by which random path the walker takes each run; wind
  noise is a small addition on top of much larger structural variance.
- The small rise in HTN's mean energy at σ≥0.4 is the wind model's floor
  clamp, not noise or a bug (see entry above for the derivation).

**Data files (repo root, untracked, regenerate via
`python -m spider_web_htn_updated.sensitivity`):**
`sensitivity_comparison.csv`, `wind_sensitivity.csv`,
`single_run_comparison.csv`.

---

## 2026-09-09 — Runtime notes for `sensitivity.py`

The full 1000-trial × 9-condition × 2-group sweep takes roughly 5–7 minutes
wall-clock (not a hang). Each `_run_once_htn` call creates a fresh
`gtpyhop.Domain` and re-registers all operators/methods, which has real
overhead multiplied across thousands of calls. `_run_once_baseline` calls
run at comparable per-trial cost (~10–20ms). Budget time accordingly before
concluding a sweep is stuck — check `ps -o pid,etime,time,pcpu` and compare
`etime` to `time`; if they're advancing together, it's working, just slow.

---

## 2026-09-09 — `spider_web_astar/` A* module: not part of the working comparison

The standalone A* planner in `spider_web_astar/main.py` fails to find a
plan within its own default budget (120s / 200k nodes / weight=3.0) — gets
stuck mid-frame-construction, ~25k nodes expanded, no solution. This is not
a bug to fix: `spider_web_htn_updated/baseline.py`'s own docstring already
explains why — true A*/BFS over this domain's action space is intractable
without baking in the same anchor/ordering domain knowledge the HTN
encodes, which would defeat the purpose of a *non-hierarchical* baseline.
The team already worked around this by building the flat-state random
walker (`baseline.py`) instead, which is what `compare.py` and
`sensitivity.py` both actually use. `spider_web_astar/` is a superseded
early attempt left in the repo, not wired into the active comparison
pipeline.
