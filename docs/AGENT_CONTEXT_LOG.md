# TruthEngine Agent Context Log

Date created: 2026-07-17
Purpose: Living project memory for humans and agentic coding platforms.

This file should be updated whenever meaningful work happens in this repository. Future agents should read this file before making changes.

## How To Use This File

When an agent, engineer, or founder changes the project, append a new entry under "Work Log" with:

- Date.
- Actor.
- Request or goal.
- Files changed.
- Decisions made.
- Open questions.
- Next recommended steps.

Keep entries factual. Do not delete older entries unless the project owner explicitly requests cleanup.

## Current Project State

TruthEngine is at the founding architecture stage.

No application code has been written yet.

The repository currently contains founding documentation only:

- `docs/TRUTHENGINE_ENGINEERING_VISION.md`: canonical mission, product definition, architecture blueprint, evidence graph model, risks, roadmap, and technical principles.
- `docs/TRUTHENGINE_SOFTWARE_ARCHITECTURE.md`: production-oriented internal software architecture blueprint covering bounded contexts, services, agents, data flow, event flow, storage, security, observability, configuration, dependency injection, provider plugins, caching, and testing.
- `docs/TRUTHENGINE_ARCHITECTURE_REVIEW.md`: critical architecture review that identifies over-engineering, premature abstractions, security risks, scaling risks, and the corrected V1 architecture.
- `docs/AGENT_CONTEXT_LOG.md`: this living handoff and decision log.

## Founder Intent Captured

The founder does not want a normal coding assistant relationship for this project. The expected posture is founding engineer and principal architect.

Core intent:

- Build one of the most trustworthy AI systems on the internet.
- Optimize for evidence exposure, not answer generation.
- Treat TruthEngine as an evidence reasoning platform, not a chatbot.
- Make reasoning inspectable.
- Make uncertainty visible.
- Detect unsupported claims and repeated evidence.
- Distinguish marketing claims from verified facts.
- Track evidence lineage and source independence.

Important framing:

- A claim repeated many times is not necessarily stronger evidence.
- Repeated evidence should be traced back to its origin when possible.
- Marketing pages, school websites, university sites, product pages, and SEO blogs often present claims confidently without proof.
- TruthEngine should classify those claims before evaluating them.

## Standing Architecture Direction

The system should be graph-first.

The evidence graph is the product. Human-readable summaries are secondary convenience outputs generated from graph state.

Core objects expected in future implementation:

- Investigation.
- Question.
- Claim.
- Evidence item.
- Source.
- Source snapshot.
- Source family.
- Evidence relation.
- Lineage hypothesis.
- Contradiction.
- Missing evidence marker.
- Confidence factor.
- User annotation.
- Model run.
- Retrieval run.

## Standing Product Direction

Initial recommended wedge:

Webpage Audit Mode for unsupported public claims, especially in education and SaaS marketing.

Why this wedge:

- It directly attacks the hidden problem of unsupported claims.
- It differentiates TruthEngine from chatbots and search engines.
- It can produce visible evidence graphs from real webpages.
- It allows narrow but meaningful first-domain evaluation.

Avoid early overreach:

- Do not build a universal fact checker first.
- Do not make a generic chatbot UI the center of the product.
- Do not reduce output to a single true/false label.
- Do not trust citation count as evidence strength.
- Do not let polished summaries hide uncertainty.

## Standing Engineering Principles

- Evidence objects should be durable.
- Claims should be versioned.
- Sources should be snapshotted.
- Retrieval metadata should be stored.
- Model outputs that affect reasoning should be stored.
- Confidence should be decomposed and explainable.
- Repeated sources should be clustered.
- Missing evidence should be a first-class result.
- LLMs may assist reasoning, but should not be the sole source of truth.
- The graph should remain the source of truth.

## Work Log

### 2026-07-17 - Codex

Request:

- Create necessary Markdown files for TruthEngine.
- One file should contain the whole founding vision and blueprint.
- Another file should keep updating as more work is requested, so other agentic coding platforms can understand what is happening.

Files changed:

- Added `docs/TRUTHENGINE_ENGINEERING_VISION.md`.
- Added `docs/AGENT_CONTEXT_LOG.md`.

Decisions made:

- Established `TRUTHENGINE_ENGINEERING_VISION.md` as the canonical engineering vision document.
- Established this file as the living context and handoff log.
- Chose a graph-first architecture direction.
- Recommended Webpage Audit Mode as the initial product wedge.
- Recorded that no implementation code should be written yet.

Open questions:

- Which first domain should the product target: universities/schools, SaaS marketing, health claims, or another high-value category?
- Should the first prototype be local-only, web app, browser extension, or API-first?
- What level of source snapshotting is required for the first prototype?
- Which retrieval providers should be used first?
- What should the first claim taxonomy benchmark include?

Next recommended steps:

- Define the V1 product scope in a short product requirements document.
- Create the first claim taxonomy and evidence standard for one domain.
- Design the initial evidence graph schema.
- Build a small hand-labeled dataset of unsupported and supported claims.
- Only then begin implementation.

### 2026-07-17 - Codex

Request:

- Translate the product vision into internal software architecture.
- Think as Chief Software Architect preparing the first production system.
- Cover maintainability, modularity, observability, scalability, and AI agent orchestration.
- Include overall architecture, domain model, entities, bounded contexts, services, agents, communication flow, request lifecycle, data flow, event flow, errors, logging, monitoring, configuration, dependency injection, AI provider plugins, storage, caching, security, and testing.
- Explain why, alternatives, tradeoffs, and scalability for architectural decisions.
- Do not write application code.
- Update this context log after completion.

Files changed:

- Added `docs/TRUTHENGINE_SOFTWARE_ARCHITECTURE.md`.
- Updated `docs/AGENT_CONTEXT_LOG.md`.

Decisions made:

- Recommended a modular monolith first, organized by bounded contexts and designed for later service extraction.
- Established async workflow orchestration as the backbone for evidence investigations.
- Defined the investigation graph as the central system of record for reasoning state, with summaries treated as derived outputs.
- Recommended PostgreSQL as the initial durable system of record, with object storage for snapshots, search/vector indexes for retrieval, Redis-style caching for hot paths, and a warehouse for analytics/evals.
- Defined specialized AI agents as bounded, auditable workers whose outputs must be validated and persisted through domain services.
- Recommended a provider-agnostic AI plugin architecture using task capabilities, policy, budget, and eval quality for routing.
- Defined source independence, lineage analysis, missing evidence, and confidence factors as first-class architectural concerns.
- Established partial failure, progressive results, structured observability, and reasoning-quality evals as production requirements.

Open questions:

- Which domain should receive the first concrete evidence profile: education rankings/schools, SaaS marketing/security claims, health claims, or another vertical?
- Which workflow orchestration technology should be selected for V1?
- Should the first production deployment use a managed search provider immediately or begin with PostgreSQL full-text search behind an interface?
- Which AI provider plugins should be supported in the first release?
- What are the first tenant/privacy constraints: consumer-only, team workspace, or enterprise-ready from day one?

Next recommended steps:

- Create a V1 Product Requirements Document for Webpage Audit Mode.
- Create the first domain evidence profile and claim taxonomy.
- Create the initial database/schema design document for the core entities.
- Create the first evaluation plan and golden dataset specification.
- Decide the implementation stack only after the V1 scope and domain profile are fixed.

### 2026-07-17 - Codex

Request:

- Perform a brutal architecture review from the perspective of a Google Staff Engineer, Anthropic Infrastructure Engineer, Microsoft Principal Engineer, and Senior FastAPI maintainer.
- Review every architectural decision.
- Find unnecessary complexity, premature optimization, bad abstractions, scalability bottlenecks, security issues, maintainability risks, coupling, hidden technical debt, and junior-engineer traps.
- Redesign anything that should be redesigned.
- Simplify anything over-engineered.
- Update the engineering vision accordingly.

Files changed:

- Added `docs/TRUTHENGINE_ARCHITECTURE_REVIEW.md`.
- Updated `docs/TRUTHENGINE_SOFTWARE_ARCHITECTURE.md`.
- Updated `docs/TRUTHENGINE_ENGINEERING_VISION.md`.
- Updated `docs/AGENT_CONTEXT_LOG.md`.

Decisions made:

- Marked the previous broad architecture as directionally useful but too heavy for V1.
- Corrected V1 toward a narrow product, not a general evidence platform.
- Selected education ranking and school/university marketing claims as the recommended first domain.
- Collapsed the V1 architecture into a modular monolith with five product modules: `investigations`, `ingestion`, `analysis`, `ai_tasks`, `presentation`, plus `evals`.
- Replaced the vague "Agent Runtime" framing with a typed `AI Task Executor`.
- Established that AI tasks must not directly write durable state or control workflow.
- Separated durable jobs from domain events; recommended a durable job queue plus transactional outbox for V1.
- Removed internal search clusters, vector databases, graph databases, Kafka, and enterprise policy engines from V1 unless justified by measured need.
- Replaced exact confidence percentages with support bands and confidence factors until calibration exists.
- Added a stricter source snapshot policy to avoid blindly archiving web content.
- Reframed lineage as probabilistic hypotheses rather than definitive origin claims.

Open questions:

- Should the first backend be FastAPI/Python, Node/TypeScript, or another framework based on team strength?
- Which durable queue should be used for V1?
- Which external search provider should be used first?
- What exact education evidence profile should be encoded for rankings, accreditation, placement claims, and "best/no. 1" claims?
- What are the minimum legal and retention requirements for source artifacts?

Next recommended steps:

- Write the V1 PRD for Education Webpage Audit Mode.
- Write the education claim taxonomy and evidence profile.
- Write the V1 data model/schema design.
- Write the AI task contract specification.
- Write the first golden eval dataset specification before implementation.

### 2026-07-17 - Codex

Request:

- Treat the architecture as frozen.
- Act as founding backend engineer.
- Initialize only the production backend foundation.
- Follow the engineering vision and architecture documents exactly.
- Create folder structure, Python project config, dependency management, environment variable management, logging, configuration, FastAPI app, dependency injection, health endpoint, middleware, exception handling, request IDs, Docker, Docker Compose, tests, linting, formatting, GitHub Actions CI, pre-commit hooks, and README files for major folders.
- Do not implement business logic, AI agents, claim extraction, evidence retrieval, or confidence scoring.
- Ensure the service starts with `docker compose up` and exposes only `GET /health`.

Files changed:

- Added `pyproject.toml`.
- Added `Dockerfile`.
- Added `docker-compose.yml`.
- Added `.env.example`.
- Added `.gitignore`.
- Added `.dockerignore`.
- Added `.pre-commit-config.yaml`.
- Added `.github/workflows/ci.yml`.
- Added root `README.md`.
- Added folder READMEs under `docs`, `src`, `src/truthengine`, `src/truthengine/api`, `src/truthengine/core`, `src/truthengine/schemas`, and `tests`.
- Added FastAPI foundation under `src/truthengine`.
- Added tests under `tests`.
- Updated `docs/AGENT_CONTEXT_LOG.md`.

Decisions made:

- Chose FastAPI/Python for the backend foundation because the user explicitly requested FastAPI application setup and Python best practices.
- Used a `src/` package layout to keep imports consistent between development, tests, and installed production packages.
- Exposed only `GET /health`; FastAPI docs, ReDoc, and OpenAPI routes are disabled for this milestone.
- Used Pydantic Settings for typed environment configuration with the `TRUTHENGINE_` prefix.
- Implemented structured JSON logging without adding a logging vendor dependency.
- Added request ID middleware using `X-Request-ID`, context variables, and response header propagation.
- Added conservative security headers middleware.
- Added centralized JSON exception handling without exposing internal errors.
- Added a tiny explicit dependency container rather than a framework-heavy DI library.
- Added Docker and Docker Compose for the single API service only.
- Added Ruff, mypy, pytest, pre-commit, and GitHub Actions CI.
- Did not create business modules such as `investigations`, `ingestion`, `analysis`, `ai_tasks`, or `presentation` yet, because this milestone is infrastructure only.

Verification:

- `python -m pip install -e ".[dev]"` succeeded.
- `ruff format .` succeeded.
- `ruff check .` succeeded.
- `mypy src tests` succeeded.
- `pytest` succeeded with 3 passing tests.
- Direct Uvicorn runtime check succeeded: `GET /health` returned HTTP 200 with the expected JSON payload.
- `docker compose config` succeeded.
- `docker compose up --build -d` could not be completed because the local Docker Desktop daemon was not running: the Docker API pipe was unavailable.

Open questions:

- Which durable queue should be selected when the first real workflow step is introduced?
- What is the exact V1 education evidence profile?
- What source artifact retention policy should be adopted before URL ingestion is implemented?
- Should CI later add Docker image build verification once a repository and runner environment exist?

Next recommended steps:

- Start Docker Desktop and run `docker compose up --build` to verify the container path end to end.
- Write the V1 PRD for Education Webpage Audit Mode before adding any business endpoint.
- Write the education claim taxonomy and evidence profile.
- Write the V1 data model/schema design.
- Write the AI task contract specification before implementing any AI-assisted task.

### 2026-07-17 - Codex

Request:

- Continue from a partially completed Antigravity implementation.
- Make TruthEngine work as a real investigation system using existing backend/frontend code.
- Do not use mock data, hardcoded JSON, placeholders, fake outputs, Tavily, or simulated agents.
- Use self-hosted SearXNG for search, `httpx` for crawling, `trafilatura` for readable content extraction, DeepSeek for structured AI stages, and algorithmic confidence.
- Connect the existing frontend to backend execution data.
- Allow the project to run with a single command rather than separate backend and frontend startup commands.

Files changed:

- Updated `pyproject.toml`.
- Updated `.env.example`.
- Updated `docker-compose.yml`.
- Updated `.dockerignore`.
- Updated `README.md`.
- Added `docs/HANDOFF.md`.
- Added `frontend/Dockerfile`.
- Added `frontend/.dockerignore`.
- Added `searxng/README.md`.
- Added `searxng/settings.yml`.
- Added `migrations/versions/20260717_0007_add_original_html_to_snapshots.py`.
- Updated `src/truthengine/sources/domain.py`.
- Updated `src/truthengine/sources/persistence.py`.
- Updated `src/truthengine/sources/pipeline.py`.
- Updated `src/truthengine/sources/service.py`.
- Updated `src/truthengine/investigations/workflow.py`.
- Updated `frontend/src/core/api.ts`.
- Updated `frontend/src/features/workspace/Workspace.tsx`.
- Updated `frontend/src/features/workspace/VerdictSummary.tsx`.
- Updated `frontend/src/features/workspace/DossierView.tsx`.
- Updated `frontend/src/features/workspace/PipelineStack.tsx`.
- Updated tests in `tests/test_health.py`, `tests/test_investigations.py`, `tests/test_sources.py`, and `tests/test_candidates.py`.
- Updated `docs/AGENT_CONTEXT_LOG.md`.

Decisions made:

- Kept the backend as a modular monolith and used provider interfaces instead of introducing new service boundaries.
- Added SearXNG to Docker Compose as the local search provider and avoided paid search APIs.
- Added a frontend Docker service so `docker compose up --build` starts the database, SearXNG, API, and frontend together.
- Added `trafilatura` as the primary readable text extraction library while retaining BeautifulSoup fallback behavior.
- Extended source snapshots to store original HTML in addition to clean text, metadata, timestamps, and hashes.
- Made missing DeepSeek configuration fail clearly at the AI analysis stage with an `ANALYSIS_BLOCKED` event instead of fabricating results.
- Kept verdict/confidence generation algorithmic, derived from graph relations, source count, contradiction count, and coverage factors.
- Rewired frontend workspace panels to use backend investigation, timeline, plan, and graph responses rather than hardcoded prototype content.
- Normalized backend response shapes in `frontend/src/core/api.ts` so existing UI components did not require a redesign.

Verification:

- `python -m pip install -e ".[dev]"` succeeded.
- `ruff format .` succeeded.
- `ruff check .` succeeded.
- `mypy src tests` succeeded.
- `pytest` succeeded with 26 passing tests.
- `npm run build` in `frontend` succeeded.
- `docker compose config` succeeded.
- `docker compose up --build -d` could not be completed because Docker Desktop was not running and the Docker API pipe was unavailable.

Known limitations:

- A live end-to-end investigation was not demonstrated in this environment because Docker Desktop was unavailable and no `TRUTHENGINE_DEEPSEEK_API_KEY` was configured.
- The complete runtime path still needs verification on a machine with Docker Desktop running and a valid DeepSeek API key.
- Source independence, lineage detection, and source quality scoring remain early implementations and need dedicated product/eval work before being treated as production-grade.
- Authentication, authorization, quotas, and public abuse protections are still absent.

Next recommended steps:

- Start Docker Desktop.
- Set `TRUTHENGINE_DEEPSEEK_API_KEY` in `.env` or the shell.
- Run `docker compose up --build`.
- Create a real investigation from the frontend, such as `Is creatine bad for kidneys?`.
- Verify visible search results, crawled source snapshots, segments, claims, matched evidence, contradictions, confidence factors, and final verdict.
