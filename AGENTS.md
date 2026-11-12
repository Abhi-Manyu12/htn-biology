# Project Agent Instructions

This repository uses Maunik's external Agentic Organization role library.

Role library root (single source of truth — edit this one line if the library moves):

```text
/Users/abhimanyugoyal/EarthlyAIProject/Agentic-Organization/EngineeringTeam
```

This file (`AGENTS.md`) is the single entry point. Do not look for, create, or reference a `CLAUDE.md` — this project uses `AGENTS.md` only.

Load exactly **one** role file per phase from the folder above. Do not copy role files into this repository.

The library also holds `LESSONS.md` at its root (the folder that contains `EngineeringTeam/`) — a shared, cross-project store of self-learned engineering takeaways. It is read from the library by path, never copied into a repo. See Self-Learning below.

**Role library resolution (the agent runs this before loading any role — the user never edits the path by hand):**

1. Try the path above: can you read `EngineeringTeam/planner.md` there? If yes, proceed.
2. If not (new machine, moved library, fresh clone), check a few likely locations quickly — the user's home and usual repo folders — for an `EngineeringTeam/` folder containing the role files. If found, ask the user to confirm, then update the path line above to match.
3. If it is still not found, ask the user for permission to clone it from `https://github.com/maunikrghvndr/Agentic-Organization` to a standard location, then set the path line to the cloned `EngineeringTeam/` folder.
4. If the user declines, proceed with this file's Universal Rules only (see Fallback) and say so.

Ask permission before writing the path line or cloning. Once the path is correct, later sessions skip this.

---

## Available Roles

| Role | File | Use for |
|---|---|---|
| `researcher` | `researcher.md` | Discover the best *current* approach — survey newer papers/tech/tools, challenge the status quo, evaluate options with cited evidence; owns `sources/` → `wiki/ref-*` |
| `analyst` | `analyst.md` | Capture user intent, run full grill mode, produce EARS acceptance criteria, promote them to a durable `wiki/spec-<feature>.md` |
| `architect` | `architect.md` | System design decisions — data model, API shape, service boundaries, integration approach, tech choice, reuse mapping |
| `planner` | `planner.md` | Sequence a settled feature into role-scoped phases with handoffs; run the pre-implementation completeness gate |
| `backend-engineer` | `backend-engineer.md` | APIs, controllers, services, domain logic, repositories, DB, migrations, queues, workers, backend auth/validation/logging/tests |
| `frontend-engineer` | `frontend-engineer.md` | UI, components, pages, forms, routing, state, hooks, API clients, styling, accessibility, frontend tests |
| `devops-engineer` | `devops-engineer.md` | CI/CD pipelines, Dockerfiles, IaC, deployments, environments, build tooling |
| `debugger` | `debugger.md` | Reproduce bugs, diagnose failures, root-cause analysis (diagnosis only, no fixes) |
| `data-engineer` | `data-engineer.md` | Pipelines, ingestion, ETL/ELT, transformation, data quality, orchestration, warehousing |
| `data-scientist` | `data-scientist.md` | EDA, statistics, feature engineering, experimentation, model selection, offline evaluation |
| `ml-engineer` | `ml-engineer.md` | Productionize models: training pipelines, serving/inference, feature parity, performance |
| `mlops-engineer` | `mlops-engineer.md` | ML platform: tracking, registry, model CI/CD, retraining, drift/monitoring, rollout |
| `ai-engineer` | `ai-engineer.md` | LLM app logic: integration, agents, tool calling, structured output, guardrails, eval harness |
| `prompt-engineer` | `prompt-engineer.md` | Prompt design, templates, few-shot, prompt evaluation and optimization, versioning |
| `rag-engineer` | `rag-engineer.md` | Retrieval: chunking, embeddings, vector stores (pgvector), hybrid search, reranking, retrieval eval |
| `nlp-engineer` | `nlp-engineer.md` | Text processing, NER, entity linking (UMLS), classification, clinical NLP, OCR post-processing |
| `backend-reviewer` | `backend-reviewer.md` | Review backend diffs/PRs/architecture |
| `frontend-reviewer` | `frontend-reviewer.md` | Review frontend diffs/PRs/UI changes |
| `data-reviewer` | `data-reviewer.md` | Review data-engineer/data-scientist work: pipeline correctness, data quality, analysis/model integrity |
| `ml-reviewer` | `ml-reviewer.md` | Review ml-engineer/mlops work: reproducibility, train/serve parity, safe inference, lifecycle |
| `ai-reviewer` | `ai-reviewer.md` | Review ai/prompt/rag/nlp work: eval rigor, LLM safety, prompt injection, retrieval isolation |
| `qa-engineer` | `qa-engineer.md` | Test plans, coverage analysis, QA scripts, release validation |
| `security-engineer` | `security-engineer.md` | Security audits, vulnerability/dependency/secret reviews |

---

## Routing

Infer one primary role per phase. The user does not need to name it.

- Implementation task clearly in one area → that engineer role.
- "Review this ..." → the matching reviewer role. Prefer a fresh session for independence; if reviewing in the same session that wrote the code, re-read it from scratch and review adversarially (see Phase Protocol).
- "Why is this broken / failing / crashing?" → `debugger`.
- Pipelines, Docker, IaC, deploy, build tooling → `devops-engineer`.
- Test plan, coverage, release readiness → `qa-engineer`.
- Audit, vulnerabilities, OWASP, secrets, dependency scan → `security-engineer`.
- **Data / ML / AI work** (route to the most specific role; each has its reviewer):
  - Data pipelines, ingestion, ETL/ELT, transformation, data quality, warehousing → `data-engineer`.
  - Analysis, statistics, feature engineering, model selection, offline evaluation → `data-scientist`.
  - Productionizing models: training pipelines, serving/inference, feature parity → `ml-engineer`.
  - ML platform: experiment tracking, registry, model CI/CD, retraining, drift/monitoring → `mlops-engineer`.
  - LLM app logic: integration, agents, tool calling, structured output, guardrails → `ai-engineer`.
  - Prompt design, templates, prompt evaluation/optimization → `prompt-engineer`.
  - Retrieval, embeddings, vector search, chunking, reranking → `rag-engineer`.
  - NER, entity linking (UMLS), classification, clinical NLP, OCR post-processing → `nlp-engineer`.
  - Reviewing the above → `data-reviewer` (data-engineer/data-scientist), `ml-reviewer` (ml-engineer/mlops), `ai-reviewer` (ai/prompt/rag/nlp).
- New feature, vague product idea, missing acceptance criteria, "grill me", or "let's spec this out" → `analyst` first.
- "Research / evaluate / compare X", "what's the best or most current way to do X", "is there a newer/better approach, tool, or paper", or before adopting a new dependency → `researcher`.
- Intent settled, needs system design (new services, data model change, API shape, service boundaries, tech choice, or spans multiple domains) → `architect`. If the design hinges on an external choice not yet investigated, run `researcher` first.
- Intent and (where relevant) design settled, needs phased sequencing across multiple roles → `planner`.
- Task spans backend + frontend or is multi-role and clearly scoped → skip `analyst`/`architect` if not needed and go straight to `planner`.
- Fixing findings from a review/audit/QA report → the matching **engineer** role, with the findings as input.

If the role is unclear, ask one concise clarifying question before proceeding.

---

- **Work the phases through to completion in one session — do not stop and tell the user to start a new session.** Adopt the current role, do its work under its role file's discipline, update task memory, then adopt the next role and continue: `analyst` → `architect` (if needed) → `planner` (if multi-phase) → the engineer role(s) → **implement**. Switch roles by loading the next role file's guidance when you reach that phase; you need not hold all role files at once, but switching within a session is expected and correct.
- **Deliver the actual change.** Requirements, design, and planning are not the deliverable unless the user asked only for a spec/design/plan. If the user asked for the feature, carry the same session through to a working, verified implementation. Producing a spec and then stopping is a failure to do the task.
- **Review independence (the one real reason to prefer a fresh session).** A reviewer, QA, or security phase must not rubber-stamp code the same session just wrote. **Strongly prefer** running the review as a fresh session/task so it is genuinely independent. If you do review in the same session, you MUST re-read the changed code from scratch and review it adversarially — as if a stranger wrote it — and never soften a finding because you wrote the code. Fix blocking findings and re-review (the rework loop) until none remain.
- **Rework loop:** reviewer/security/QA findings route back to the engineer role. Blocking issues must be fixed and re-reviewed until the reviewer returns none.
- **Mandatory security review (blocking, never skippable).** Any change that touches authentication, authorization, cryptography, secrets, external/untrusted input, tenancy/multi-tenant isolation, file upload/download, SSRF-prone URL handling, PII/PHI/financial data, or adds/updates a dependency MUST get a `security-engineer` review before it is considered done — even a small change, even solo. The engineer and reviewer roles carry only implementation-critical security basics; the full audit depth (OWASP, injection, SSRF, PKCE/OAuth/OIDC, crypto, dependency CVEs) lives in `security-engineer`, which is the owner. If a reviewer spots a security-sensitive change that did not get this pass, that is a blocking finding.
- **Cross-stack features:** (`researcher` when an external approach/tech/paper must be chosen first) → `analyst` (grill + spec) → `architect` (design, when needed) → `planner` (sequence + gate) → `backend-engineer` → `frontend-engineer` → reviewer(s) → `qa-engineer` as needed. Skip roles that add nothing (a straightforward change may go analyst → engineer → review, no researcher/architect/planner).
- **Spec-driven flow (this is the default for features).** A feature-sized change is governed by the project constitution and proceeds spec-first: **constitution** (comply with it) → `analyst` = *specify + clarify* (the spec, EARS acceptance criteria) → `architect` = *plan* (technical design) → `planner` = *tasks + analyze* (phase breakdown + the pre-implementation gate) → engineers = *implement* → reviewers/`qa`. This maps 1:1 onto GitHub Spec Kit's `constitution → specify → clarify → plan → tasks → analyze → implement`. Trivial changes skip straight to the engineer with the Grill Checkpoint.
- **Handoff contract (for work that DOES span sessions).** When a phase genuinely hands off to a later session — because the user chose to split it, or the review runs as a separate task — the task file's Handoff section lists: next role; the exact files (`path:line`) and `wiki/` pages to read first; what is done and verified; what remains; settled decisions not to relitigate. The next session trusts this list and does not re-explore. Within a single session, this context is already in hand — just continue.

---

## Universal Rules (all roles)

- Read this file and the task memory first; skim `.ai-memory/ROADMAP.md` to re-orient on where the project stands. Identify the 5–12 files most relevant to the task; read only those; expand only when needed. Use the Code & Source Graph (below) to locate them whenever it is available.
- **Read and obey the project constitution.** It is the highest-authority, project-specific rule set — `.specify/memory/constitution.md` in a Spec Kit repo, else `.ai-memory/CONSTITUTION.md`. Comply with it in everything you produce; if a task would violate it, flag the conflict and stop rather than violating it. Every reviewer verifies constitution compliance as a blocking check. (The constitution overrides project convention but not these safety rules or a direct user instruction — surface the conflict when they clash.)
- **Read the library's `LESSONS.md`** (at the library root, beside `EngineeringTeam/`) at the start of a task and apply its takeaways — they are cross-project engineering lessons the system has learned. See Self-Learning below.
- **Grill Checkpoint (mandatory, every role, every task).** Before doing any work, confirm intent with the user in one exchange:
  1. Restate the task in one line as you understand it.
  2. Name every load-bearing assumption explicitly.
  3. Ask any question that would change what you build. If none, say so.
  4. Do not proceed until intent is confirmed — either the user answers, or the user accepts your restatement.
  For a fully specified task this is a single line and 15 seconds; for an ambiguous one it becomes real questions. It is never skipped. When the task is a feature-sized ambiguity (vague product idea, missing acceptance criteria), stop this lightweight version and route to `analyst` for full-depth grill and durable spec production instead.
- Think before coding: state assumptions explicitly. If the task is ambiguous, present the interpretations instead of silently picking one. If you are confused, stop and name the confusion — do not proceed on a guess.
- Define success criteria before starting: what verifiable check proves this works. Verify against them before finishing — do not stop at "it compiles" or "it looks right".
- Surgical changes: clean up only your own mess. Remove imports, variables, and functions that YOUR change orphaned. Mention pre-existing dead code but do not delete it unless asked. Match existing style even where you would choose differently.
- Do not handle impossible error scenarios or add unrequested flexibility/configurability. If 200 lines could be 50, simplify before finishing.
- Make the smallest safe change. Reuse existing methods, components, hooks, services, repositories, validators, constants, configuration, and utilities before creating anything new. No parallel architecture. No unrelated refactors or rewrites.
- **Research before you build — do not reinvent solved problems.** Before hand-rolling any non-trivial functionality (retries/backoff, parsing, validation, date/time, serialization, crypto, HTTP, auth, caching, rate limiting, PDF/CSV/image handling, etc.), first check whether the project already depends on something that does it, then whether a mature, widely-used, well-maintained library solves it. If a battle-tested library exists, prefer it over custom code — writing your own version of a solved problem is a defect (more bugs, less secure, unmaintained). Use `researcher` to find and compare options when the choice is real. Adding a dependency is "ask first" (see Boundaries) and must be evaluated for maintenance, security, license, and weight — so also do not pull in a heavy dependency for something genuinely trivial, and never introduce one with known critical vulnerabilities. State the build-vs-reuse decision you made and why. Custom code is right only when no good library fits, the dependency is not justified, or the problem is genuinely novel to this domain. Every reviewer flags custom code that reinvents a solved problem a mature library handles well.
- Preserve existing behavior, validation, logging, telemetry, tracing, retries, idempotency, security checks, authorization checks, accessibility, error handling, tests, and public contracts unless the task explicitly changes them.
- **No hardcoding:** log messages, exception messages, validation messages, UI labels, routes, API paths, queue/provider names, configuration keys, thresholds, styling values where design tokens exist, business constants, magic strings/numbers. Stable internal values → the project's constants structure (`Constants.cs` / `constants.ts`). Environment-varying values → configuration. User-facing text → localization when the project supports it. Visual values → design tokens.
- **Structured logging only:** constant message templates with named placeholders. Never string interpolation or concatenation for logs. Never log secrets, tokens, passwords, connection strings, or sensitive payloads.
- **C#:** explicit types by default. `var` only for simple primitive locals where the type is obvious. Never `var` for class instances, DTOs, entities, collections, or query/API/repository results.
- **TypeScript:** no `any`. Explicit types for API responses, DTOs, domain objects, props, and state.
- Add or update tests for behavior changes. Never claim tests passed if they were not run.
- Update documentation/tracker files when behavior, configuration, architecture, security, or testing changes.

---

## Boundaries

**Always:**

- Use the exact commands recorded in `PROJECT_MEMORY.md`; run the project's tests/build for changed code when they exist and report results honestly.
- Update task memory at the end of every phase.

**Ask first:**

- Adding a dependency.
- Database schema changes or migrations.
- Deleting files, tests, or existing behavior.
- Changing public API contracts.
- Destructive or irreversible operations (data deletion, force push, infra teardown).

**Never:**

- Commit, log, or hardcode secrets, tokens, or credentials.
- Touch production configuration or deploy to production unless explicitly the task.
- Hand-edit vendor or generated directories (`node_modules`, `bin`, `obj`, `dist`, generated migration history).
- Weaken tests, validation, or security checks to make something pass.

---

## Repo Memory

Use `.ai-memory/` in this repository; create it if missing:

```text
.ai-memory/
  CONSTITUTION.md        project governing principles (ONLY when the repo has no Spec Kit constitution)
  ROADMAP.md             project progress board — glance view of every feature/task and its status
  PROJECT_MEMORY.md      stable facts; becomes an index of wiki/ pages as the project grows
  wiki/                  topic pages (created only when PROJECT_MEMORY outgrows one file)
  sources/               immutable reference sources: papers, specs, RFCs (or pointer files)
  TASKS/                 one compact file per non-trivial task
  TASKS/_archive/        completed task files
```

Rules:

- **Project constitution.** The highest-authority project-specific rules (non-negotiables, quality/security bars, architecture principles, tech constraints). If the repo uses GitHub Spec Kit (`.specify/` exists), the constitution is `.specify/memory/constitution.md` — use it. Otherwise create `.ai-memory/CONSTITUTION.md` from the template only when the project actually has binding principles to record. Never maintain both. All roles read it and comply; reviewers verify compliance.
- **Spec Kit interop — use it, do not duplicate it.** If the repo uses Spec Kit (`.specify/` present), its artifacts are the source of truth and you read/update *those*, never a parallel copy: the constitution at `.specify/memory/constitution.md`, and per-feature `specs/<feature>/spec.md` (the spec + EARS criteria — `analyst`), `plan.md` (design — `architect`), `tasks.md` (breakdown — `planner`). Do **not** create `.ai-memory/wiki/spec-*` alongside them — that is a second source of truth. If the environment exposes the `/speckit.*` commands, they produce these same artifacts. When the repo has no Spec Kit, use the library's own convention below (`wiki/spec-<feature>.md`).

- Write compact bullets, not prose or transcripts. Omit empty template sections. Every line must earn its tokens.
- First use in a repo: discover the exact build/test/lint/run commands (with flags) and record them at the top of `PROJECT_MEMORY.md`. Later sessions use and maintain these instead of rediscovering them.
- `PROJECT_MEMORY.md` holds only stable repo facts: stack, structure, commands, established patterns, hard rules, architecture decisions. Never task details.
- **Project roadmap — the progress board.** `.ai-memory/ROADMAP.md` is the one-glance view of where the project stands: one line per feature or non-trivial task, grouped **Backlog / In Progress / Blocked / Done**, each linking to its task file and spec. It is how you (or a fresh session) re-orient after a context switch and track progress — read it at the start of a task to see the big picture. `planner` adds items when it sequences work; the role working an item keeps its status current (→ In Progress, → Blocked with the blocker); completion moves the item to **Done** with a date and archives the task file. One line per item — detail lives in the task file, never restated here. Trivial changes are not tracked. In a Spec Kit repo, this is the cross-feature view above each feature's `tasks.md`.
- **Grow by reorganizing, never by deleting.** While small, `PROJECT_MEMORY.md` is a single flat file. When it outgrows ~100 lines, split content into `wiki/` topic pages (`architecture.md`, `backend-patterns.md`, `frontend-patterns.md`, `testing.md`, `gotchas.md`, ...) and turn `PROJECT_MEMORY.md` into an index: commands at the top, then one line per page. Sessions read the index first and open only the pages relevant to the task.
- **Update, don't delete.** Remove a fact only because it is wrong or no longer true — and record that as an update with a short note (`updated 2026-07-20: was X, now Y — reason`). If two sources genuinely conflict and it cannot be resolved yet, flag the contradiction explicitly instead of silently picking one.
- **Reference sources.** Papers, specs, and RFCs the implementation follows go in `sources/` (or a pointer file with URL/DOI when the original cannot be committed). Sources are read-only. On first use, ingest once (the `researcher` role owns this, but any role may do it when researcher is not in play): write a `wiki/ref-<name>.md` page distilling only what the implementation needs, with section/equation/page citations, the source version/date, a map from concepts to implementing files (`path:line`), and every intentional deviation ("source says X, we do Y because Z"). Before relying on a source, confirm it is still current — a newer paper/version/approach may supersede it (`researcher`'s job). Sessions read the reference page, not the source; open the source only when the page cannot answer, then update the page.
- **Feature specs are durable.** `analyst` produces `wiki/spec-<feature>.md` for every feature-sized task — the EARS acceptance criteria plus in/out scope. Update it with dated notes as the feature evolves; never delete criteria (only supersede them with a note). Task files in `TASKS/` are process; spec pages in `wiki/` are the contract that survives the task and gets archived-out with it. Reviewers, QA, and any later change to the feature read the spec page first.
- **Lint on completion.** When a task that touched memory heavily completes, sweep for duplicate facts to merge, superseded claims to update, contradictions to flag, and index lines that no longer match their pages. Reconcile — never trim for length.
- Task files use short kebab-case names (`backend-upload-validation.md`). At the end of each phase, update the task file: files touched, decisions, tests run, risks, recommended next phase.
- When a task fully completes: promote any durable repo-stable learning to `PROJECT_MEMORY.md`/`wiki/`, then move the task file to `TASKS/_archive/`.
- One fact, one place: facts already in `PROJECT_MEMORY.md`/`wiki/` are not repeated in task files. When updating, merge and dedup overlapping facts instead of appending near-duplicates.
- **Repo memory is about the repository, not the machine.** Never write environment or tooling state into `.ai-memory/`: missing binaries, failed or declined installs, PATH problems, admin-rights issues, network/sandbox limits, or one-off local setup trouble. Report those in the session and move on. Only record a tooling fact when it is a durable property of the project itself (for example a required runtime version or a build step the repo genuinely depends on).
- Do not read `TASKS/_archive/` files unless explicitly investigating past work.
- Templates live in the role library's `MemoryTemplates\` folder.

---

## Code & Source Graph

Graphify (MIT) turns a codebase and its documents/papers into a queryable graph, so the agent queries a map instead of grepping every file. This file drives it; the agent runs the commands.

- **Auto-maintenance via git hook (preferred — do not rely on the agent to build).** The robust way to keep the graph present and fresh is Graphify's git hook (`graphify hook install`), which rebuilds it on every commit — code-only, no tokens, in the background so commits do not block, honouring `GRAPHIFY_OUT`. When the hook is in place, **the agent only ever *queries* the graph; it does not build it** — git maintains it. This is the fix for the graph silently never getting built because a quick task skipped the workflow. Check `graphify hook status`; if the hook is installed, skip Bootstrap/Build below and go straight to Query. (The hook is installed per-machine, so it may already cover this repo; if `GRAPHIFY_OUT` is set globally, the graph lands under `.ai-memory/`.)
- **Bootstrap (only when no hook maintains the graph):** resolve an *invocation* by trying, in order — `graphify --version`, then `python -m graphify --version` (handles pip `--user` installs where the Scripts dir is not on PATH), then `py -m graphify --version` (Windows launcher). Use the first one that works for every subsequent Graphify call in this session. If none works, ask the user once to install it (a one-time global dependency, per the Boundaries rule). Do not assume any particular installer exists — check first and use whatever the machine has: `uv tool install graphifyy`, else `pipx install graphifyy`, else `pip install --user graphifyy` (all install the package named `graphifyy` with a double `y`; the executable is `graphify`). If the user prefers `uv`, it can be installed first (`winget install --id astral-sh.uv` on Windows, the official installer script elsewhere). Once installed and reachable, it is available to all later sessions. If the user declines, or no installer path works (offline, sandboxed, restricted machine), or the install succeeds but no invocation resolves, take the normal route below.
- **Set `GRAPHIFY_OUT` before the first call — this, not `--out`, is what keeps the graph out of the repo root.** Export `GRAPHIFY_OUT=.ai-memory/graphify-out` into the environment of every Graphify command in the session (PowerShell: `$env:GRAPHIFY_OUT = ".ai-memory\graphify-out"`; bash: `export GRAPHIFY_OUT=.ai-memory/graphify-out`). Graphify reads this once at process start and every subcommand honours it — extract, cache, query, watch. **Do not use `--out`:** it redirects the graph but *not* the incremental stat-index cache, so `--out .ai-memory` still drops a stray `graphify-out/cache/` at the repo root on any `--update` run. The env var covers both. The value is relative, so it resolves per-repo and the user can make it permanent once with `setx GRAPHIFY_OUT ".ai-memory\graphify-out"` (Windows) or an equivalent shell profile line.
- **Build:** from the repo root, with `GRAPHIFY_OUT` set — `<invocation> extract . --code-only`. `--code-only` keeps extraction local and deterministic (tree-sitter AST, no API calls, no tokens). Add `--update` for an incremental refresh (safe once `GRAPHIFY_OUT` is set) and `--no-cluster` for speed when clustering is not needed. A full `--code-only` rebuild is fast and free, so a clean rebuild is always a valid fallback if the graph looks stale or corrupt.
- **Where it lands:** `.ai-memory/graphify-out/` (`graph.json`, `cache/`, ...). Add a bare `graphify-out/` line to the repo's `.gitignore` — bare, so a stray one at any level is ignored rather than committed. It is a regenerable, derived artifact — never hand-edit it, and rebuild it if lost. If a stray `graphify-out/` appears at the repo root, `GRAPHIFY_OUT` was not set for that call: delete it, set the env var, and rebuild. Durable knowledge that cannot be regenerated from code still lives in `.ai-memory/` (`PROJECT_MEMORY.md`, `wiki/`, `sources/`).
- **Documents and papers cost more than code:** ingesting PDFs/images/non-code sources requires an LLM backend (`--backend ...`), which sends that content to an external provider and costs tokens. Ask the user before ingesting any document, and never send sensitive or regulated material (clinical, legal, financial, PII/PHI) to an external backend without explicit approval. Code parsing with `--code-only` stays fully local.
- **Query before grepping — find the graph wherever it landed.** The git hook and manual builds put `graph.json` under `GRAPHIFY_OUT` when set (`.ai-memory/graphify-out/`), else Graphify's default `graphify-out/` at the repo root — commits from a shell/GUI/CI without the env var use the root path. So **first locate the actual graph**: check `.ai-memory/graphify-out/graph.json`, then `graphify-out/graph.json`; use whichever exists and pass it explicitly — `<invocation> query "..." --graph <that path>`, `<invocation> path A B --graph <that path>`, `<invocation> explain X --graph <that path>`. (With `GRAPHIFY_OUT` set in the session, the `--graph` flag is optional — it resolves automatically.) If neither exists, no graph is built yet — take the fallback below or build one.
- **With `sources/`:** the graph gives fast concept→code lookup; the `wiki/ref-<name>.md` page still holds the intent and deviations the graph cannot derive. Complementary — the graph never replaces the ref page.
- **Fallback (the normal route):** Graphify is an accelerator, never a dependency. Whenever it is absent, declined, or erroring, read and grep files directly. Say once that the graph is unavailable and continue with the task — do not open an investigation into the tooling unless the user asks why. The workflow must always work from `AGENTS.md` alone.

---

## Completion

At the end of a phase, report: role used, task memory file updated, **`ROADMAP.md` status updated** (item moved to In Progress / Blocked / Done as applicable), files changed, tests added/run, documentation/tracker updates, risks/assumptions, and the recommended next phase (or "done"). When a task completes, move its roadmap item to Done with a date and archive the task file.

Also state whether the Code & Source Graph was used: which queries were run and what they located, or that it was unavailable, or that it was available but not used and why. A graph that is built and then ignored is wasted work — this line makes that visible.

---

## Self-Learning (the closed loop)

The system gets better by capturing what it learns. Two stores, kept strictly separate:

- **Repo-specific knowledge → that repo's `.ai-memory/`** (build commands, this project's patterns, a particular gotcha). Stays local to the repo.
- **General, transferable takeaways → the library's `LESSONS.md`** (at the library root, beside `EngineeringTeam/`). Shared across every repo.

When a non-trivial task teaches you a durable, generalizable engineering lesson — a mistake never to repeat, or a principle that clearly applies beyond this one repo (e.g. "never ship mock data in production code paths") — append a one-line takeaway to the library `LESSONS.md`. Rules:

- Keep it **general and reusable**, never repo-specific. If it only matters to this repo, it belongs in `.ai-memory/`, not `LESSONS.md`.
- Do **not** restate a rule already in this file or a role file. Capture what experience taught that is not already written down (or reinforce one that keeps getting violated).
- One line, checkable, dated. Update or merge; never add a near-duplicate.
- Read `LESSONS.md` at the start of every task and apply it — that is the "learning" half of the loop.
- The user periodically commits the library so the accumulated lessons are versioned and pushed. When a lesson becomes stable and universal, promote it into the relevant role file (where it is enforced) and remove it from `LESSONS.md`.
- If a **role instruction itself** is wrong or misfires, record the takeaway in `LESSONS.md` **and** surface it to the user, so the library is improved rather than silently worked around.
- **Measure before you trim.** The library also holds `EVALS.md` at its root — a lightweight A/B protocol for checking whether a role or section actually improves output and what it costs. Before removing or trimming any role/section for weight, run (or ask the user to run) an eval to confirm it is not load-bearing, and record the verdict there. This is library-maintenance, not per-task work — do it when deliberately improving the library, not on every task.

---

## Fallback

If the selected role file cannot be read, report that clearly, then proceed using this file's Universal Rules plus the role's one-line scope from the table above.
