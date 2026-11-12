# Project memory

- Verification command recorded in the research work log:
  `python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests spider_web_htn_updated/tests`.
- Main recovery experiment:
  `python3 -m spider_web_mulder.recovery_comparison --seeds 10 --trace --output mulder_results/NEW_UNIQUE_DIRECTORY`.
  Preserve historical directories; choose a new output path for each study.
- Python dependencies: `requirements.txt`; pinned GTPyhop and vendored IPyHOP.
- Research evidence and claims: `docs/research/README.md`, `CLAIMS.md`, `WORK_LOG.md`.
- Research-record guidelines: `RESEARCH_RECORD_GUIDELINES.md`.
- Manuscript fragments and bibliography: `docs/manuscript/`.
- Target journal specified by user: Programming and Computer Software,
  https://link.springer.com/journal/11086. Contribution may be computational
  modeling and evaluation; a new planning algorithm is not the project objective.
- [Spider literature research index](wiki/research-spider-htn.md).
- E1 is implemented on `development/E1`: `python3 -m
  spider_web_recovery.e1_benchmark --output mulder_results/NEW_UNIQUE_DIRECTORY`.
  Fixed protocol: `docs/research/E1_PROTOCOL.md`; 1,920-trial result:
  `docs/manuscript/e1_methods_results.md`; curated evidence under
  `docs/research/evidence/e1_v1/`. All capable controllers tie on physical
  outcomes; do not claim an HTN advantage. Full verification now has 226 tests.
- E1 provenance records uncommitted source hashes above base HEAD `61d18d8`;
  do not treat the base commit alone as the tested E1 implementation.
- Expanded E1: `python3 -m spider_web_recovery.e1_expanded --output
  mulder_results/NEW_UNIQUE_DIRECTORY`; fixed design
  `docs/research/E1_EXPANDED_PROTOCOL.md`, results/figures
  `docs/manuscript/e1_expanded_results.md`, curated rows and provenance
  `docs/research/evidence/e1_expanded_v1/`. 5,280 trials, 231 tests; outcomes
  still tie across capable controllers, and 120 cases were unexposed. Runtime
  differences are variable; 24-sector retained mean was slightly lower with a
  paired interval spanning zero. Do not claim retained planning always slower.
