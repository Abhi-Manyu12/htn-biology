# Empirical Ethological Data — Citation-Ready Table

Extracted from primary (Zschokke 1996, in-repo PDF) and secondary ethological sources. Organized by relevance to the four experimental metrics: **P_s** (Success Rate), **η** (Efficiency Ratio), **T_a** (Adaptation Time), **D** (Decomposition Depth).

**Verification status:** Numbers tagged `[VERIFIED]` were extracted directly from `zschokke1996rsz.pdf` (pages indicated). Numbers tagged `[CITED]` come from secondary sources as listed in the project's empirical-data table.

---

## Table 1 — Construction Sequence & Behavioral Hierarchy

Maps directly to the HTN method decomposition depth (D).

| Stage | Behavior | Variability | Source |
|---|---|---|---|
| 1. Exploration | Spider walks new frame, lays dragline, samples environment | Highly variable | Zschokke 1996, p.711 [VERIFIED] |
| 2. Bridging | Crosses gap via walk / drop / swing (Tarzan) | Variable | Zschokke 1996, p.713 [VERIFIED] |
| 3. Proto-hub establishment | Threads converge at a knot | "Highly variable… no pattern can be discovered" | Zschokke 1996, p.713 [VERIFIED] |
| 4. Proto-radius construction | Three methods: walk / drop / Tarzan swing | 31/34 = 91.2% follow 6 variants of one basic pattern | Zschokke 1996, p.713 [VERIFIED] |
| 5. Hub relocation | Move proto-hub to final position | Stereotyped | Zschokke 1996, p.715 [VERIFIED] |
| 6. Frame + radii | Top frame first, then radially | "Quite a rigid pattern" | Zschokke 1996, p.716 [VERIFIED] |
| 7. Auxiliary spiral | Smooth continuation of circling | Stereotyped | Zschokke 1996, p.716 [VERIFIED] |
| 8. Capture spiral | Final sticky spiral | Stereotyped | Zschokke 1996, p.716 [VERIFIED] |

**Biological principle (Zschokke 1996, p.711 [VERIFIED]):** "Once the spider had established this proto-hub, its behaviour became more stereotyped and predictable." This is the empirical anchor for the HTN's multi-method early stages + single-method late stages design.

---

## Table 2 — Quantitative Metrics for Each Experiment Variable

### 2.1 Behavioral Variability → Maps to Metric **D** (Decomposition Depth)

| Datum | Value | Sample | Source |
|---|---|---|---|
| Proto-radius constructions following one of 6 variants | 31 / 34 (91.2%) | n=34 proto-radii | Zschokke 1996, p.713 [VERIFIED] |
| Number of distinct behavioral variants for one proto-radius | 6 | — | Zschokke 1996, p.713 [VERIFIED] |
| Methods to reach supporting structure | 3 (walk / drop / Tarzan swing) | — | Zschokke 1996, p.713 [VERIFIED] |
| Primary frame threads observed | 47 | n=9 webs | Zschokke 1996, p.716 [VERIFIED] |
| Secondary frame threads observed | 8 / 55 (14.5%) | n=9 webs | Zschokke 1996, p.716 [VERIFIED] |
| Primary frames built without simultaneous new radius | 19 / 47 (40.4%) | n=9 webs | Zschokke 1996, p.716 [VERIFIED] |

**Use in experiment:** Calibration target for D. Your HTN's proto-hub task has 3 alternative methods; spider biology shows 3 methods with 91.2% coverage. Match this ratio.

### 2.2 Distance Walked → Maps to Metric **η** (Efficiency Ratio) via silk proxy

Zschokke 1996, p.712 [VERIFIED]: "the distance covered is the roughly the same as the length of silk produced; the distance covered is also roughly proportional to the locomotory energy used."

| Datum | Simple structure | Complex structure | Source |
|---|---|---|---|
| **Exploration distance** (m) | range 2.79–63.21; median **5.61**; MAD 3.79 | range 6.55–212.53; median **27.60**; MAD 13.35 | Zschokke 1996, p.716–717 [VERIFIED] |
| **Construction distance** (radii + spirals) (m) | range 7.86–18.46; median **13.64**; MAD 2.61 | range 8.24–24.09; median **14.37**; MAD 2.72 | Zschokke 1996, p.717 [VERIFIED] |
| Sample size (webs) | n=37 | n=38 | Zschokke 1996, p.716 [VERIFIED] |
| **Second web (no re-exploration)** distance | significantly smaller than exploration (U=1, p=0.005) | (U=0, p<0.001) | Zschokke 1996, p.717 [VERIFIED] |
| Construction distance simple vs complex | p=0.096 (n.s.) | — | Zschokke 1996, p.717 [VERIFIED] |

**Use in experiment:** S_initial calibration. Median exploration on complex environment is **~5×** that on simple. Use this ratio to set your S_initial axis: e.g., if S_budget = 50 m, simple env ≈ 9 trials feasible, complex ≈ 2. The 5× ratio is your expected P_s drop point.

**Key statistical finding:** Construction distance does **not** differ significantly between simple/complex (p=0.096). Only *exploration* does. This means your HTN vs A* comparison should show HTN saving energy primarily in exploration, not in late-stage construction. This is a falsifiable prediction.

### 2.3 Web Geometry → Maps to **A_web** (denominator of η)

| Datum | Value ± SE | Sample | Source |
|---|---|---|---|
| Radial length | 284 ± 14 cm | Control (undrugged) webs | Hesselberg & Vollrath 2004 [CITED] |
| Capture spiral length | 1083 ± 72 cm | Control webs | Hesselberg & Vollrath 2004 [CITED] |
| **Capture area** | **239 ± 16 cm²** | Control webs | Hesselberg & Vollrath 2004 [CITED] |
| Mesh size | 2.33 ± 0.07 mm | Control webs | Hesselberg & Vollrath 2004 [CITED] |
| Eccentricity | 0.47 ± 0.04 | Control webs | Hesselberg & Vollrath 2004 [CITED] |
| Quadrant-specific radial counts | per-quadrant means and variances | n=194 webs | ap Rhisiart & Vollrath 1994 [CITED] |

**Use in experiment:** A_web ≈ 239 cm² is the target for "biologically valid" web. Compute η_real = silk_length_used / 239 cm². Your simulation's η should be in the same order of magnitude (within ~2×). If η_simulation is 10× higher, your model is doing too much work; if 10× lower, it's underbuilding.

**Variability as noise floor:** ±16 cm² on capture area means a real spider's A_web varies by ~7%. If your simulation has higher variance, the model is too noisy. Lower variance → model is too deterministic.

### 2.4 Environmental Complexity → Maps to **P_s** and **D** axes

| Complexity level | Description | Sample | Source |
|---|---|---|---|
| Simple | 1 cross-bar parallel to perspex plate | n=37 webs | Zschokke 1996, p.711 [VERIFIED] |
| Complex | 6 cross-bars turned 45° out of plane | n=38 webs | Zschokke 1996, p.711 [VERIFIED] |

**Key empirical fact:** The 5× exploration-distance ratio (5.61 → 27.60 m) between simple and complex environments is the strongest available calibration point for your "environmental complexity" axis. If your randomized N-anchor environments don't reproduce a comparable P_s drop / D increase between low-N and high-N, your complexity model isn't matching biology.

### 2.5 Failure Modes / Adaptation → Maps to Metric **T_a** (Adaptation Time)

| Datum | Value | Source |
|---|---|---|
| Spiders "re-build and existing web costs much less compared to building a web from scratch" | Abstract claim | Zschokke 1996, p.709 [VERIFIED] |
| Web removal distance significantly smaller than exploration | U-test, p=0.005 / p<0.001 | Zschokke 1996, p.717 [VERIFIED] |
| Spiders usually build several webs at the same site, re-using the framework | Behavioral observation | Zschokke 1996, p.711 [VERIFIED] |
| Spiders pause during early stages: "a few minutes… several hours" | Behavioral observation | Zschokke 1996, p.713 [VERIFIED] |

**Use in experiment:** T_a should be measured in *cycles to resume task after perturbation*. The biological analog is "cycles of leg movement to re-establish after damage." Concrete numbers for repair-cycle timing are **not directly in Zschokke 1996** — flag this as a gap and supplement with Craig 2003 / Eberhard 1990 (recommended primary citations for T_a in writeup).

---

## Table 3 — Predictions the HTN Model Should Match

These are falsifiable claims your experiment can test:

| Empirical Observation | HTN Prediction | A* Prediction | Source |
|---|---|---|---|
| Construction distance independent of complexity | HTN cost stable across N | A* cost grows with N | Zschokke 1996, p.717 [VERIFIED] |
| Exploration distance ~5× higher on complex env | HTN D grows ~5× | A* nodes expanded grows >>5× | Zschokke 1996, p.716 [VERIFIED] |
| 91.2% of proto-radii fall into ≤6 variants | HTN proto-hub methods ≤ 6, success rate ≥ 91.2% | N/A (no method structure) | Zschokke 1996, p.713 [VERIFIED] |
| Re-building < exploration | HTN with reused frame: P_s ~1 even at low S_initial | A* no memory: must re-explore | Zschokke 1996, p.717 [VERIFIED] |
| Frame construction "quite a rigid pattern" | HTN single deterministic method | A* still explores | Zschokke 1996, p.716 [VERIFIED] |

---

## Gaps / Data Not Available in Current Sources

| Metric | Gap | Recommended Source |
|---|---|---|
| T_a (cycles to resume after perturbation) | No cycle-level repair timing in Zschokke 1996 | Craig 2003, *Spiderwebs and Silk*; Eberhard 1990, *Annu. Rev. Ecol. Syst.* |
| Failure mode taxonomy | No systematic catalog of what spiders do when an anchor fails | Vollrath & Clark 1996, *Manipulations of spider silk* |
| Real-time perturbation response | Zschokke 1996 used computerised tracking but didn't report cycle-level recovery | Zschokke & Vollrath 1995, *Unfreezing the behaviour of two orb spiders* (cited methodology) |

---

## Source Verification Notes

- **[VERIFIED]** — extracted directly from `zschokke1996rsz.pdf` in repo; page numbers refer to the printed page numbers in the PDF.
- **[CITED]** — taken from the project's empirical-data table; primary sources not yet inspected in this repo.
- The 31/34 = 91.2% number is verified from p.713 ("Most (31 out of 34) proto-radii constructions followed one of six variants of the same basic pattern").
- The exploration distance 5.61 m median and the construction distance 13.64 m median are both verified from p.716–717.
- The "5× complexity ratio" is computed from the verified medians (27.60 / 5.61 ≈ 4.92).
- The "8/55 secondary frames" figure is verified from p.716. Note: this differs slightly from the project's earlier table which said "8 secondary frames" without the 55 denominator — both refer to the same data.
- The "19/47 primary frames without simultaneous radius" is verified from p.716.
