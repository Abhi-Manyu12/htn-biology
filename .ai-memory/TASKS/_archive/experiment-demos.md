# Experiment demos

- Intent confirmed: simulated videos from saved experiment traces; tabs and side-by-side comparisons.
- Contract: [spec](../../wiki/spec-experiment-demos.md), AC-1–AC-8.
- Analyst complete: existing local canvas viewers; raw saved traces and study records available; historical evidence remains immutable.

## Design

- Extend static `visualization/` with a shared study viewer; add navigation to existing pages, preserve their renderer and entry commands.
- Reuse saved JSON ledgers and domain geometry/affine-motion definitions in an offline Python asset exporter. Bundle compact replay data as JavaScript so file:// remains supported; no runtime API or dependencies.
- Keep selected matched case together; allow only its recorded controllers to be compared. Shared clock uses simulated seconds, never normalized progress.
- Native Canvas captureStream/MediaRecorder exports labeled single/paired replay. Feature-detect support, release stream/object URLs and handle failure.
- Study/context text centralized in catalog; snapshots compacted without removing state-changing interventions. Source paths and SHA-256 manifest retained.
- Security surfaces: generated script escaping and browser-generated download; no uploads, arbitrary URLs or remote execution. Security review required.
- Performance: representative saved seeds only; lazy-load one study bundle at a time.

## Phases and gate

- Gate: AC-1–AC-8 covered; no constitution present; no dependency/schema/API changes; no unresolved scope questions.
- `frontend-engineer`: read `visualization/index_updated.html:1`, `spider_web_recovery/domain.py:1`, study ledgers and spec; exporter, UI, native export, data verification tests. Done when every study loads real traces and asset verification passes (AC-1–AC-8).
- `frontend-reviewer`: reread changed source adversarially; check matching, animation timing, accessibility and regressions against spec. Done when blocking findings resolved.
- `security-engineer`: inspect script serialization, source paths and recording/download lifecycle. Done when blocking findings resolved.
- Verification: recorded Python suite plus exporter tests and available browser checks; update README/research log/memory, then archive task and move roadmap to Done.

## Status

- Done 2026-11-17: analyst/design/planner, frontend implementation, adversarial frontend re-review and security review complete; no blocking findings remain.
- Files: shared static experiment viewer/catalog/renderer/styles, offline exporter and 4 data bundles/manifest, existing-viewer navigation, Python/browser checks, usage guide and research review/log/index.
- Verification: 240 Python tests passed (231 existing + 9 replay checks); replay tests rerun after exporter refinements. Thirty Chrome assertions passed at desktop and exact 390 px, including native video generation/download/decoding and loading/error/race regressions; screenshots inspected; whitespace check passed.
- Documentation and roadmap updated; final review/AC mapping: [review](../../../docs/research/DEMO_UI_REVIEW.md). Stable commands and guide indexed in PROJECT_MEMORY.md.
- Limits: curated first-seed replays, schematic sector capture links and interpolated paths; Chrome capture verified, other browsers feature-detected. No new scientific trials or biological claims.
- Next phase: done.

## Frontend review findings

- Request changes: narrow scenario selector shrinks to an unreadable width; switching to Construction during a pending study load can leave `aria-busy=true`; rejected attempts are preserved in data but need explicit replay captions.
- Trace fidelity and matched strata reviewed against original runners; recorded costs remain distinct from presentation interpolation and aggregate means.
- Resolved 2026-11-17: focused UI fixes, centralized runtime labels, load/race/rejection browser regressions, graceful QA-browser shutdown and final desktop/mobile verification; security review passed for this static change.
