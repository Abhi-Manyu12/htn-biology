# Experiment demo UI verification — 2026-11-17

- Intent: replay saved simulated experiment traces, with experiment tabs,
  matched comparisons and downloadable labeled video.
- Scope: `visualization/experiments.html`, catalog, replay/time selection,
  viewer/capture, styles, offline exporter, replay bundles and browser checks;
  existing construction pages gain navigation only.
- Roles: analyst → architect → planner → frontend-engineer →
  frontend-reviewer → frontend rework → security-engineer. Reviews were
  same-session adversarial rereads; no independent external review claimed.
- No project constitution is present. Existing research-record and claim
  boundaries apply. No model, controller, historical result or dependency
  manifest changed, and no new experiment was executed.

## Acceptance traceability

| Criteria | Implementation | Verification |
| --- | --- | --- |
| AC-1 | `visualization/experiment_viewer.js:104`, study catalog | Browser checks: five tabs, loaded cases, missing-bundle error/retry |
| AC-2 | `visualization/experiment_replay.js:1`, viewer rendering | Exact damage-time sampling, event seeking, failed-run final-state hold, rejected attempt |
| AC-3 | `visualization/export_experiments.py:148`, viewer pair selection | Bundled group checks; same-case controller selection and single/pair browser flow |
| AC-4 | Exporter outcome/aggregate functions; viewer outcome cards/table | Empty successful strata test; tie, failure, donor and unexposed browser checks |
| AC-5 | `visualization/experiment_viewer.js:394` | Native video generated, blob downloaded and decoded at expected dimensions; encoder error and unsupported-browser paths |
| AC-6 | Catalog caveats, provenance panel and escaped script serialization | Script injection payload round-trip; original-source hashes; tie/negative-result assertions |
| AC-7 | `visualization/experiments.html:24`, responsive CSS, old-viewer links | Home key/roving tab focus, embedded old viewer, desktop/390 px page fit |
| AC-8 | Exporter source matching, domain hash and endpoint checks | Curated E1 CSV/transfer ledger comparison, deliberately mismatched outcome rejected, bundle/source manifest checks |

## Frontend review and rework

- Resolved: mobile scenario select shrank excessively; now occupies a full row.
- Resolved: entering Construction during a pending bundle load left an
  accessible busy state; branch resets it and stale results are ignored.
- Resolved: rejected attachment attempts needed an explicit caption; recorded
  acceptance state now reaches the renderer.
- Exported captions include study, conditions, seed, playback speed and the
  model-simulation label. Clock and planning wall time remain separate.
- Lazy bundles contain 59 matched demo cases / 232 representative saved runs.
  Coverage is documented in `visualization/README.md`; across-seed means use
  all matching saved seeds, not just the replay seed.
- Final frontend recommendation: approve after focused rework and browser
  regression checks. Motion begins only on user action; controls and numeric
  outcomes are available outside canvas.

## Security review

- Recommendation: pass for this local static change; no blocking finding.
- Injection: data uses text nodes, not HTML; generated script JSON escapes
  markup and separator characters. Dataset names are catalog-allowlisted.
- Downloads: canvas-only capture, no microphone/camera acquisition, uploads
  or server calls; Blob URL and stream lifecycle reviewed. Selections are
  locked during capture and failure restores controls. Leaving/hidden tabs
  stops capture; stale recorder callbacks cannot affect a new recording.
- Source integrity: SHA-256 hashes for trial/provenance/trace inputs and output
  bundles. Sector geometry source must match its historical manifest.
- QA tooling: subprocess argument arrays, fresh temporary browser profile,
  loopback-only remote debugging and graceful browser shutdown. No normal
  browser profile or shell command interpolation used.
- Secrets: scoped secret-pattern scan over new code and bundles returned no
  matches. No tokens, browser storage, analytics or third-party runtime
  scripts introduced.
- Dependencies: `requirements.txt` diff empty; browser playback/capture uses
  native APIs, exporter reuses existing domain/stdlib. Optional browser QA
  uses existing local aiohttp tooling, not an added application requirement.
  A full dependency CVE scan was not performed; this is not a repository-wide
  vulnerability certification.

## Results and limits

- `python3 -m pytest -q spider_web_mulder/tests spider_web_recovery/tests spider_web_htn_updated/tests visualization/tests`:
  **240 passed**. Nine replay tests were rerun after exporter refinements.
- Chrome: **30 browser assertions passed** at desktop and 390 px, including
  actual video encode/download/decode; screenshots inspected.
- `git diff --check` passed. Code & Source Graph unavailable; source read
  directly. Browser checks cover Chrome, not every browser/codec combination.
- Replay paths interpolate observed endpoints. Sector capture links are
  schematic; the numeric silk metric comes from recorded domain costs.
- Demo assets and software checks are presentation/verification artifacts,
  not new simulation evidence, biological validation or evidence of an HTN
  advantage. Existing claim ledger remains unchanged.
