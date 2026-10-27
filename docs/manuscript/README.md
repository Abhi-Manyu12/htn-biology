# Manuscript staging

These fragments support the combined manuscript for the repository. Model
versions, evidence status and caveats remain explicit when incorporating them.

- [mulder_methods_results.md](mulder_methods_results.md): reusable Methods,
  Results, recovery description and limitations for the Mulder study.
- [references.bib](references.bib): bibliography entries used by these fragments.
- [recovery_methods_results.md](recovery_methods_results.md): the separate
  IPyHOP-backed dependency-changing recovery study.
- [mulder_reentrant_results.md](mulder_reentrant_results.md): IPyHOP integrated
  into the actual Mulder HTN, with same-engine and legacy comparisons.
- [figures/](figures/): curated figures from the version-3 study.
- [../research/WORK_LOG.md](../research/WORK_LOG.md): research history and commands.
- [../research/CLAIMS.md](../research/CLAIMS.md): claim/evidence ledger.
- [../research/BANSOD_REENTRANT_REVIEW.md](../research/BANSOD_REENTRANT_REVIEW.md):
  related-work analysis and proposed recovery experiments.

Citation keys in prose use Pandoc-style `[@key]` notation for easy adaptation.
These are draft sections, not a complete submitted article. The original HTN,
updated HTN, FAP and A* work should each be audited before adding quantitative
cross-package comparisons. Do not import their earlier README assertions as
verified measurements without checking source data and implementations.

After new research runs, update the work log, claim ledger and corresponding
fragment, preserving which observations belong to each simulator version.
Keep bulk artifacts externally or under mulder_results/; retain a curated
evidence snapshot and figure provenance in docs/.
