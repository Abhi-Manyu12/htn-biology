# Spider behavior and HTN: literature and experiment opportunities

Research date: 2026-11-12. Role: researcher. Target: Programming and Computer
Software. This is a targeted literature search, not a systematic review.

## Decision and recommendation

Which spider papers should support the manuscript, and which motivate additional
computational experiments? Use the existing moving-support study as the main
result, position it against earlier rule-based spider models, and consider one
additional experiment on observed-structure-dependent recovery. Do not expand
into prey capture or jumping-spider navigation for this manuscript by default.

Confidence: **Established** that the listed literature is relevant; **Uncertain**
that an HTN implementation will outperform equally informed local-rule or
state-machine models. The latter is an experimental question.

Searches for spiders with “hierarchical task network” and “HTN planning” did not
identify a verified biological HTN application in the screened results. This is
not proof that none exists and does not justify a first-ever claim. Hierarchical
hidden Markov models, behavioral stages, and hierarchical planning are different
concepts. All HTN mappings below are our proposed interpretations, not claims
made by the biological papers. Bansod's existing planner papers remain the
technical references for the implemented recovery engine.

## Papers to use

### 1. Zschokke (1996): early construction and reuse

**Early stages of orb web construction in Araneus diadematus Clerck.** Revue
Suisse de Zoologie, hors série, 709–720. Key: `zschokke1996early`.
[Author-hosted paper](https://bio.staern.li/pdf/zschokke1996rsz.pdf).

- Checked: indexed author PDF abstract and bibliographic header; also already
  present locally as `zschokke1996rsz.pdf`. Direct remote opening timed out.
- Reported finding: variable early construction uses recurring behavioral
  patterns; behavior becomes more stereotyped after proto-hub establishment.
  Reusing an existing framework reduces travel cost relative to a new site.
- Manuscript use: motivate alternative early methods and staged construction.
- Proposed test: new-site construction versus reuse of valid existing supports,
  measuring exploration travel, new silk and completion. Existing scaffold
  initialization is not evidence that the spider discovered or reused it.

### 2. Gotts and Vollrath (1991): essential AI modeling prior work

**Artificial intelligence modelling of web-building in the garden cross spider.**
Journal of Theoretical Biology 152, 485–511. Key: `gotts1991modelling`.
[Publisher abstract](https://doi.org/10.1016/S0022-5193(05)80394-7).

- Checked: publisher abstract and author publication list; not a full algorithm audit.
- Reported approach: temporary-spiral models initialized from reconstructed real
  partial webs, with progressively simpler computational rules.
- Manuscript use: AI modeling of spider construction is established prior work.
  Our contribution must be the particular formulation and evaluation.
- Proposed connection: compare an HTN phase method with a local construction
  rule under the same observations. Reproducing their model requires full-text
  rule extraction first; current flat execution is not that reproduction.

### 3. Krink and Vollrath (1997): rule-based models and parameter fitting

**Analysing Spider Web-building Behaviour with Rule-based Simulations and Genetic
Algorithms.** Journal of Theoretical Biology 185, 321–331.
Key: `krink1997analysing`.
[Publisher abstract](https://doi.org/10.1006/jtbi.1996.0306).

- Checked: publisher abstract and indexed paper text.
- Reported approach: optimize construction-rule parameters and compare resulting
  artificial webs with laboratory Araneus diadematus webs.
- Manuscript use: establish rule-based modeling and hypothesis testing as a
  relevant baseline tradition, independent of inventing a planning algorithm.
- Proposed test: equal-information local-rule versus HTN models, with shared
  parameter-fitting budgets and held-out conditions. A fit is not validation on
  the same observations, and geometry must become an output before this test.

### 4. Krink and Vollrath (1998): emergent geometry

**Emergent properties in the behaviour of a virtual spider robot.** Proceedings
of the Royal Society B 265, 2051–2055. Key: `krink1998emergent`.
[Primary article record](https://pmc.ncbi.nlm.nih.gov/articles/PMC1689493/).

- Checked: article abstract and metadata; full PDF rules not audited.
- Reported result: local interactions with existing threads produce matching
  auxiliary/capture spiral pitch as an emergent property in the model.
- Manuscript use: explain why realistic final geometry does not by itself show
  an advantage for a planner or reveal the animal's internal representation.
- Proposed connection: let HTN choose construction subtasks while local rules
  choose attachment sites. Test predicted pitch relations on held-out structures.
  The current prescribed waypoint generator cannot perform this test honestly.

### 5. Vollrath and Krink (2020): sensory rules and embodied construction

**Spider webs inspiring soft robotics.** Journal of the Royal Society Interface
17, 20200569. Key: `vollrath2020robotics`.
[Author institutional record](https://ora.ox.ac.uk/objects/uuid%3A35da2e64-2b92-4f9d-8ecd-c144e62f3c97).

- Checked: institutional metadata/abstract and indexed author-institution PDF.
- Describes virtual spiders, local sensing, rule-based construction and
  morphological contributions to feedback.
- Manuscript use: motivate separating task selection from physical execution.
- Proposed test: sensing availability, noise and latency under a common executor.
  Do not attribute our chosen latency values to this paper or claim that varying
  a delay alone reproduces its tactile or morphological mechanisms.

### 6. Corver et al. (2021): highest-priority behavioral hierarchy source

**Distinct movement patterns generate stages of spider web building.** Current
Biology 31, 4983–4997.e5. Key: `corver2021stages`.
[Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC8612999/).

- Checked: Results (atypical stage progression; Figures 2 and 6), abstract,
  and Data and Code Availability.
- Reported result: a hierarchical hidden Markov model describes stage-specific
  action sequences in Uloborus diversus, including atypical stage progressions.
- Proposed HTN connection: reusable subtasks with conditional stage repetition.
  This is not evidence of symbolic HTN cognition or an HTN outperforming an HHMM.
- The paper lists [analysis code](https://github.com/GordusLab/Corver-Wilkerson-Miller-Gordus-2021)
  and [raw video/data](https://doi.org/10.7281/T1/BMATHH). Archive download and
  license suitability have not been verified; DOI opening failed in this session.
- Proposed experiment: compare stage-order coverage on held-out individuals.
  Cross-species results must remain separate from Araneus comparisons.

### 7. Peters (1970): partial-web transfer and phase repetition

**Orb web construction: Interaction of spider (Araneus diadematus Cl.) and thread
configuration.** Animal Behaviour 18, 478–484. Key: `peters1970configuration`.
[Publisher abstract](https://doi.org/10.1016/0003-3472(70)90043-6).

- Checked: publisher abstract and author-paper scan header identifying Paul J. Peters.
- Reported experiments: altering building sequences and transferring spiders to
  partial webs; external structure affects subsequent construction and phase repetition.
- Manuscript use: motivate observed-state preconditions rather than relying only
  on a completed-action history.
- Proposed experiment: transfer the simulated actor to a different partial web
  at a stage boundary. Compare history-only execution, state-based rules and HTN
  recovery. This needs structural state and a defined transfer protocol; merely
  clearing a completion flag would be an inadequate implementation.

### 8. Eberhard (2019): flexible construction cues and repair

**Adaptive flexibility in cues guiding spider web construction and its possible
implications for spider cognition.** Behaviour 156, 331–362.
Key: `eberhard2019flexibility`.
[DOI](https://doi.org/10.1163/1568539X-00003544);
[author-uploaded paper](https://www.researchgate.net/publication/331396443_Adaptive_flexibility_in_cues_guiding_spider_web_construction_and_its_possible_implications_for_spider_cognition).

- Checked: author-uploaded abstract and paper text; Smithsonian metadata confirms DOI.
  Publisher DOI access was unavailable through the browsing tool.
- Reports flexibility in use of construction cues in Zosis geniculata and
  Uloborus diversus, including temporary exceptions allowing access to web regions.
- Proposed HTN connection: alternative methods whose applicability depends on
  available structure. A sufficiently expressive local rule can also implement
  exceptions; winning against an intentionally rigid baseline proves little.
- Proposed test: single- versus multiple-region damage, preserving intact effects.
  Treat cognitive interpretations as the author's argument, not established HTN evidence.

### 9. Vollrath, Downes and Krackow (1997): adaptive geometry

**Design Variability in Web Geometry of an Orb-Weaving Spider.** Physiology &
Behavior 62, 735–743. Key: `vollrath1997variability`.
[Publisher abstract](https://doi.org/10.1016/S0031-9384(97)00186-8).

- Checked: indexed publisher metadata/abstract; direct full-page access returned 403.
- Reports changes associated with support geometry, wind, temperature, humidity
  and silk supply in Araneus diadematus.
- Proposed HTN connection: resource- and support-dependent construction methods.
- Proposed test: vary frame shape and resource budget; predict counts, spacing
  and area instead of prescribing them. Wind is not equivalent to the existing
  moving-support shear. This is a larger model extension, not a parameter sweep.

### 10. Cross and Jackson (2016): optional, different behavioral domain

**The execution of planned detours by spider-eating predators.** Journal of the
Experimental Analysis of Behavior 105, 194–210. Key: `cross2016detours`.
[Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4751061/).

- Checked: primary article abstract and experimental apparatus description.
- Tests detour behavior in spider-eating jumping spiders, not orb construction.
- Proposed connection: hierarchical navigation subtasks and memory ablation when
  the goal becomes hidden. The repository's graph routes are not a replication.
- Recommendation: optional discussion only; implementing this would broaden the
  biological and software scope substantially and cannot validate orb-weaver cognition.

### 11. Hung, Corver and Gordus (2026): recent feedback context

**Dynamic vibration-driven feedback shapes predator–prey interactions in an
orb-weaving spider.** PLOS Computational Biology 22(9), e1014802.
Published September 15, 2026. Key: `hung2026feedback`.
[Publisher article](https://doi.org/10.1371/journal.pcbi.1014802).

- Checked: primary publisher abstract, author list, date and citation metadata.
- Studies vibration-guided predator–prey sensorimotor feedback, not web construction.
- Proposed HTN connection: future integration of construction, sensing and prey
  capture tasks; the present repository has no corresponding predation model.
- Recommendation: optional recent context, not justification for a construction
  latency parameter or evidence that our model captures vibration mechanics.

## Proposed experiments, in priority order

All experiments below are **proposed, not implemented or run**. Experiment plans
are not evidence of an advantage. No additional animal experiment is assumed.

### E1: recovery determined by current web structure

Status update, 2026-11-12: implemented and tested on `development/E1` under the
[fixed E1 protocol](E1_PROTOCOL.md). The [1,920-trial results](../manuscript/e1_methods_results.md)
show equal completion and successful physical costs for state rules and both
HTN variants. The proposal below records the original motivation; it is no
longer unimplemented. Biological protocol replication remains unperformed.

Motivation: Peters and Eberhard. Start from the separate recovery domain; extend
its physical-effect abstraction before attempting a Mulder integration. Define
partial-web transfer separately from actual damage so experimental causes remain
distinguishable. Transfer must specify actor position, available supports, existing
silk and resource accounting rather than teleporting at zero cost implicitly.

Compare (a) history-only execution as a diagnostic ablation, (b) a state-based
rule/finite-state controller, (c) fresh-root HTN, and (d) retained HTN. Share
observations, primitive actions, repair alternatives and budgets among the capable
baselines. Test intact, single-sector and dependent multi-sector changes, including
feasible and infeasible cases. Measure valid completion, stale commands rejected,
unnecessary intact-work repetition, legitimate repair, silk/travel and CPU costs.

Primary question: does structured recovery improve outcomes or computation beyond
an equally informed state-based controller? A tie is informative. Initial scope
would be a literature-inspired computational benchmark, not reproduction of the
animal experiments. Extract full biological protocols before making that claim.

### E2: typical and atypical stage progression

Motivation: Corver and Zschokke. First inspect the public dataset, annotations and
reuse terms. Align observed behavioral stages with model tasks; do not treat leg
movements as interchangeable with segment-placement primitives. Split by spider,
not video frames, and reserve atypical sequences for an explicit held-out test.

Compare fixed-order HTN, conditional/repeating-stage HTN and an equally informed
finite-state model. Use HHMM results only with a compatible predictive task; HTNs
do not natively provide probabilities. A symbolic test can score held-out sequence
coverage, invalid accepted sequences and method complexity; likelihood comparisons
require a separately specified probabilistic model. If no biological observations
are successfully acquired, call the study synthetic coverage testing.

### E3: local geometry rules under task-level control

Motivation: Gotts, Krink/Vollrath and design-variability studies. Replace prescribed
spiral waypoints with sensory construction rules. Compare the same local rules
with and without HTN scheduling across held-out support shapes and resource levels.
Measure geometry error against reference observations, coverage, silk use and
completion. Include missing/noisy cues. Fit only on training conditions.

This is the most substantial extension and not necessary merely to begin writing.
Do not call our existing flat prescribed sequence a Theseus or stigmergic baseline.

## Implementation map and differences

| Current code | Relevant concept | Important difference |
|---|---|---|
| `spider_web_mulder/model.py:158` (`construction`) | Spiral generation, geometry comparisons | Counts and ideal waypoints are imposed; not emergent local-rule construction |
| `spider_web_mulder/model.py:264` (`build_web`) | Task decomposition | Remaining components follow prescribed sequence; no learned biological stage transitions |
| `spider_web_mulder/tracking.py:15` | Feedback/sensing | Kinematic executor; no tactile leg model or vibration propagation |
| `spider_web_recovery/domain.py:186` | Valid effects versus completed history | Authored validity predicates, not an empirically identified spider observer |
| `spider_web_recovery/domain.py:230` | Restoration/re-entry | Explicit repair methods and abstract sectors; not Eberhard's detailed spiral repair |
| `spider_web_recovery/domain.py:117` | Navigation | Graph routing with known state; not hidden-goal detour cognition |

## Currency, access and manuscript placement

Search coverage included exact spider/HTN phrases, web construction hierarchy,
virtual spiders, construction flexibility and 2024–2026 behavior studies. Newer
materials papers using “hierarchical spider-web structures” were excluded because
mechanical hierarchy is not task planning. A 2025 conference abstract was not
used as a replacement for the peer-reviewed Corver study. The 2026 predation paper
adds current context without superseding construction studies.

Use Zschokke, Gotts, Krink, Corver, Peters and Eberhard in Introduction/Related
Work; use sensory and geometry papers in Model Assumptions/Discussion. The existing
Mulder (2021) citation remains central. Cite Cross and Hung only if their distinct
domains are actually discussed. Adding entries to a bibliography does not mean
all must appear in the submitted reference list.

Some sources were verified at abstract/metadata level only, as labeled above.
Numerical protocol reproduction requires full-text review and data access. The
public-data statement in Corver is promising, not confirmation of downloaded data.
No biological parameters, sample sizes or effect sizes were imported into our
model by this literature task.

Original literature-task handoff: **data-scientist**, to assess feasibility and
write a fixed analysis protocol. E1 has since completed that workflow, including
implementation and measurement; E2/E3 remain proposed.
