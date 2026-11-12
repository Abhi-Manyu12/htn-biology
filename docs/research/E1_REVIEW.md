# E1 review and acceptance record

Date: 2026-11-12. Branch: `development/E1`, based on `61d18d8`.
Scope: `e1.py`, `e1_benchmark.py`, `tests/test_e1.py`, protocol, primary outputs
and manuscript interpretation. Roles: data-scientist, backend-engineer,
data-reviewer, security-engineer and QA. Reviews were performed in the same
session by rereading the implementation; this is not independent external review.
The source graph was unavailable; relevant files were read directly.

## Data review summary

**Recommendation: approve within the declared computational scope. Risk: medium
for interpretation, low for changes to existing experiments. No blocking issues.**

The comparison includes a strong rule baseline sharing observed predicates,
repair choices, routing and resource knowledge. The weak cached-plan baseline
is identified as an ablation. The primary question and analysis were fixed in
`E1_PROTOCOL.md` before the full sweep. No parameters were tuned after seeing
primary results. There is no fitted model, train/test split or imported animal
dataset; the 20 seeds are simulation cases, not biological replicates.

All 480 matched cases have identical pre/post checkpoint hashes across four
controllers. The three prespecified contrasts each contain 480 attempted pairs
and 320 successful physical-cost pairs. Inspection of every eligible pair,
rather than only mean differences, confirms exact equality of elapsed time,
travel and silk. The 160 infeasible pairs per contrast are excluded only from
physical-cost comparisons and remain in completion/computational comparisons.
There is no unnecessary repetition; conservation error is zero in all 1,920
trial rows. Failures are retained, including cached plans whose executable
suffix ends without a complete web.

Lineage includes source and protocol hashes, exact Config/Settings, seeds,
versions, pinned upstream manifest and Git state. The runner rejects existing
directories, journals completed trials, checks source stability across the run
and writes its artifact manifest last. All 114 bulk artifact hashes were checked;
selected outputs were copied byte-for-byte into `docs/research/evidence/e1_v1/`.
The curated summary adds an exact pair audit and hashes of curated copies/figures.
Repeated runs create separate directories. An interrupted run is identifiable
by the absence of its final artifact manifest; automatic resume is not provided.

Timing includes controller decisions and planner adapter work; it excludes
physical execution and separately collected tree snapshots. Fresh and retained
use the same upstream engine. Method counts are not compared to rule decisions.
Timing is machine/implementation dependent. Pointwise bootstrap intervals are
descriptive and not a test of biological equivalence. Prescribed geometry,
ideal sensing, aligned transfer and authored repair order limit generality.

## QA summary

**Recommendation: ready for this scoped experiment. Coverage: sufficient.
No unmet or silently dropped acceptance criteria.**

Acceptance criteria are fixed, observable and indexed AC-1–AC-8. Test functions
below are in `spider_web_recovery/tests/test_e1.py`; line references identify
implementation entry points, not the entire covered code range.

| Criterion | Implemented in | Covering verification | Status |
|---|---|---|---|
| AC-1 identical exposure | `spider_web_recovery/e1.py:177`, `e1_benchmark.py:47` | `test_matched_case_contract`, mismatch rejection test; full 480-case hash audit | Met |
| AC-2 state/cost/stock accounting | `spider_web_recovery/e1.py:40`, `e1.py:145` | `test_transfer_keeps_actor_costs_and_accounts_for_donor_separately`, common contract; full stock audit | Met |
| AC-3 observed primitive preconditions | `spider_web_recovery/e1.py:145` | `test_matched_case_contract` independently replays primitives; `test_precondition_rejection_and_deadline_do_not_commit_effects` | Met |
| AC-4 preserve valid work, count reconstruction | `spider_web_recovery/e1.py:95`, `e1.py:177` | `test_matched_case_contract`; full zero-repeat audit, legitimate restoration records | Met |
| AC-5 infeasibility/budget termination | `spider_web_recovery/e1.py:177` | `test_early_failure_is_not_success_or_event_exposure`, `test_repair_budget_stops_before_replanning`, unavailable/resource cases | Met |
| AC-6 actual retained action leaf | `spider_web_recovery/e1.py:177` | `test_retained_reentry_uses_real_unexecuted_leaf_and_retains_prefix` for three disruption types; diagnostic trees | Met |
| AC-7 reproducible records/no overwrite | `spider_web_recovery/e1_benchmark.py:89`, `e1_benchmark.py:120`, `e1_benchmark.py:204` | `test_runner_saves_provenance_and_refuses_overwrite`, `test_analysis_rejects_mismatch_and_reports_conditional_denominators`; artifact audit | Met |
| AC-8 legacy behavior/data preserved | New E1 entry points only | Existing 177 tests plus 49 E1 tests; Git diff against `61d18d8` shows no changes to old model/planner/actor source or numerical artifacts | Met |

Commands executed successfully:

```sh
python3 -m pytest -q spider_web_recovery/tests/test_e1.py
# 49 passed
python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests spider_web_htn_updated/tests
# 226 passed
python3 -m spider_web_recovery.e1_benchmark --output mulder_results/e1_v1_20261112
# 1,920 primary trials, 480 matched cases, zero exposure mismatches
```

Tests cover stationary/moving supports, both primary sizes, all scenarios and
controllers, zero stock, tiny time/action budgets, zero repair budget, rejected
effect atomicity, invalid seeds and unaligned transfer. They use the existing
pytest structure and actual vendored planner. No timing thresholds are used in
tests. Runner smoke verification includes its end-to-end report/export path.
The completion figure was visually inspected. First-seed action traces and
separate tree diagnostics provide observability. No UI, API, migrations,
background service or empirical-data pipeline is added.

## Security review summary

**Overall security recommendation: pass for the local research CLI. Risk: low.
No critical, high or medium findings in the changed scope.**

- Scope: local numeric CLI arguments, output creation, JSON/CSV/SVG export,
  read-only Git subprocesses, pinned planner imports and tests. No dependencies,
  auth, network endpoints, infrastructure or CI permissions changed.
- Input validation: argparse choice/type checks, duplicate sweep rejection and
  existing Config numeric validation. Simulation action/time/repair budgets are
  enforced. Sweep size is operator-selected; this is not a public service.
- Injection/SSRF: no shell interpolation, eval, pickle or URL fetching. Git
  subprocesses use fixed argument arrays. SVG diagnostic labels use the existing
  HTML-escaping renderer. Output filenames are fixed or use enumerated scenarios.
- File handling/data integrity: caller chooses a new destination; atomic
  directory creation refuses existing targets. There is no upload, archive
  extraction or untrusted input-file parser. Output-parent permissions follow
  the local operator's filesystem permissions.
- Secrets/privacy: synthetic state only. Targeted secret-pattern scan found no
  matches in the new Python files. Provenance includes local executable/platform
  and Git-status paths intentionally; no environment-variable values or secrets.
- Dependencies: `requirements.txt` and vendored sources unchanged; upstream
  hashes verified. `pip-audit` and `gitleaks` were unavailable, so no new CVE or
  repository-wide secret-scan assurance is claimed. No new package installed.
- OWASP applicability: injection and file/integrity boundaries reviewed;
  access control, sessions, tenancy, browser XSS/CSRF, OAuth and SSRF endpoints
  are absent from this change. Cryptographic hashes identify artifacts and are
  not an authentication mechanism.
- Verification: invalid-seed and CLI/overwrite tests, manual subprocess/export
  inspection and checksum audit. No blocking remediation or human decision is
  required. This is a changed-scope review, not a full repository security audit.

## Release and research limits

Implementation, validation, fixed sweep and evidence curation are complete.
The work is local on the requested branch. Publication still requires manuscript
assembly and scientific review; the experiment supplies no empirical biological
validation or HTN superiority claim. E2/E3 are outside this implementation.
