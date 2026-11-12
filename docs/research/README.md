# Repository research record

This is the durable index for assembling the manuscript for the whole
repository. It supplements the implementation notes and generated reports.

| Record | Purpose |
|---|---|
| [MULDER_OBJECTIVE_ROADMAP.md](MULDER_OBJECTIVE_ROADMAP.md) | Original objective, remaining gaps and proposed validation/publication route |
| [WORK_LOG.md](WORK_LOG.md) | What changed, why, checks performed, and experiment locations |
| [CLAIMS.md](CLAIMS.md) | Supported claims, limitations, and claims not yet supported |
| [BANSOD_REENTRANT_REVIEW.md](BANSOD_REENTRANT_REVIEW.md) | Literature assessment and current recovery audit |
| [evidence/mulder_v3_summary.json](evidence/mulder_v3_summary.json) | Curated exact results and input hashes from the 2,280-trial study |
| [evidence/planner_strategy_audit.json](evidence/planner_strategy_audit.json) | Installed planner strategy and a reproducible fallback probe |
| [evidence/recovery_v1_summary.json](evidence/recovery_v1_summary.json) | Separate retained-tree recovery study and pinned upstream provenance |
| [evidence/mulder_reentrant_v4_summary.json](evidence/mulder_reentrant_v4_summary.json) | Integrated Mulder recovery outcomes and paired contrasts |
| [evidence/mulder_suffix_control.json](evidence/mulder_suffix_control.json) | Control isolating whole-suffix refresh |
| [../manuscript/mulder_reentrant_results.md](../manuscript/mulder_reentrant_results.md) | Actual Mulder HTN integration and v4 comparison |
| [../manuscript/README.md](../manuscript/README.md) | Draft prose, figures and bibliography for manuscript integration |

## Documentation workflow

After each substantive change, record the research question, implementation
version, exact run command, settings/seed manifest, output paths, checks,
observations, interpretation limits, and next unresolved issue. Label design
proposals separately from measured results. Keep negative results and changes
of interpretation; a later model version does not erase earlier observations.

The root AGENTS.md makes this documentation practice part of future repository
work. This is a working research record, not a claim that all components are
ready for publication.

## Repository scope

`spider_web_htn`, `spider_web_htn_updated`, `spider_web_fap` and
`spider_web_astar` predate the Mulder branch. Existing README.md,
project_summary.md, insights.md, and spider_web_astar/empirical_data.md provide
context. They have not all been independently audited or experimentally
validated in this documentation pass. Their prior results must be checked
before integration into the combined manuscript.

The current detailed record covers `spider_web_mulder` versions 1–3 and a
literature/code audit, the separate `spider_web_recovery` v1 study, and the
integrated Mulder v4 comparison.
The user's earlier adaptive-planner
work remains in a stash from branch creation; it must not be presented as code
currently executed on feat_mulder.

## Important current correction

The installed GTPyhop 1.9.7 selects iterative greedy planning by default.
The historical Mulder runner does not pin the search strategy. Consequently,
generic descriptions saying the current runs use full method backtracking
are not established. See the strategy audit and Bansod review. No historical
run has been retroactively changed to a different search strategy. New recovery
baselines explicitly select full DFS and include a same-engine fresh-versus-
retained IPyHOP comparison.
