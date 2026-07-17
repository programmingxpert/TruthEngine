# TruthEngine Handoff

This document is the fastest way for another coding agent to continue TruthEngine without rereading the entire repository.

## Project Vision

TruthEngine is an evidence reasoning platform. It should expose claims, evidence, contradictions, missing evidence, lineage, uncertainty, and confidence factors. Users should inspect the reasoning rather than trust an AI answer.

## Current Architecture

TruthEngine is a modular full-stack application:

- Backend: FastAPI modular monolith under `src/truthengine`.
- Database: PostgreSQL with SQLAlchemy models and Alembic migrations.
- Frontend: React/Vite under `frontend`.
- Search: replaceable provider interface, currently SearXNG.
- Crawling: `httpx` download plus `trafilatura` readable text extraction.
- AI: replaceable LLM provider interface, currently DeepSeek for structured claim extraction and evidence relation verification.
- Confidence: computed algorithmically from graph/source factors.

The runtime pipeline is:

```text
Question
-> Planner
-> Search
-> Crawler
-> Snapshot
-> Segmentation
-> Candidate Selection
-> Claim Extraction
-> Evidence Matching
-> Contradiction Detection
-> Confidence
-> Verdict
```

## Folder Responsibilities

- `src/truthengine/api`: FastAPI routers and transport boundary.
- `src/truthengine/core`: settings, logging, database, middleware, exceptions, and dependency container.
- `src/truthengine/investigations`: investigation domain, persistence, service orchestration, workflow, plans, candidate passages, and evidence graphs.
- `src/truthengine/search`: search provider contracts and SearXNG implementation.
- `src/truthengine/sources`: source and snapshot domain, crawler, persistence, and service logic.
- `src/truthengine/llm`: LLM provider contracts and DeepSeek implementation.
- `migrations`: Alembic migrations. Import new SQLAlchemy records in `migrations/env.py`.
- `frontend/src`: existing UI. Keep visual design intact unless explicitly asked to redesign.
- `tests`: backend unit and integration tests.
- `docs`: engineering vision, architecture, review notes, project memory, and agent context log.
- `searxng`: local SearXNG configuration for Docker Compose.

## Completed Milestones

- Engineering vision and architecture documents.
- Backend production foundation.
- Investigation domain and persistence.
- Frontend prototype.
- Real pipeline wiring through search, crawl, snapshot, segmentation, candidates, graph, and report events.
- Frontend data normalization so UI artifacts come from backend responses.
- Single-command Docker Compose stack for frontend, backend, database, and SearXNG.

## Remaining Milestones

- Run a live end-to-end investigation with a real DeepSeek key and Docker Desktop running.
- Add durable background execution if investigation latency grows beyond acceptable request time.
- Improve source quality scoring and independence/lineage detection.
- Add embedding provider implementation if current candidate matching is only lexical or incomplete.
- Add golden evaluation datasets for claim extraction, evidence matching, contradiction detection, and verdict calibration.
- Add authentication, rate limiting, and user/workspace ownership before public deployment.

## Current Constraints

- No mock data, hardcoded investigation artifacts, placeholder agents, or simulated pipeline outputs.
- Do not redesign the frontend while making backend data functional.
- External dependencies must stay behind provider interfaces.
- AI must not own final confidence. Confidence is computed from transparent factors.
- Every public Python class/function should have type hints and docstrings.
- Keep modules small, cohesive, and readable.

## Coding Standards

- Run before handoff: `ruff format .`, `ruff check .`, `mypy src tests`, `pytest`, and `npm run build` in `frontend`.
- Use typed Pydantic schemas at API boundaries.
- Use SQLAlchemy records only in persistence modules.
- Keep domain models free of FastAPI and SQLAlchemy concerns.
- Use structured timeline events for user-visible workflow progress.
- Prefer explicit errors over silent fallbacks.

## Architectural Rules That Must Never Be Violated

- Do not write AI output directly to durable state without validation and normalization.
- Do not let an LLM perform search or crawling.
- Do not treat repeated copied sources as independent evidence.
- Do not convert marketing claims into verified facts without independent evidence.
- Do not make confidence a free-form LLM opinion.
- Do not add new infrastructure without a concrete product need.
- Do not bypass repository/provider interfaces from API handlers.

## Important Design Decisions

- SearXNG is used because it can run locally and avoids paid search APIs.
- Source snapshots store URL, title, metadata, clean text, original HTML, timestamp, and SHA256 hash.
- `trafilatura` is the primary readable-content extractor; BeautifulSoup is a fallback.
- DeepSeek is currently required for claim extraction and relation verification.
- Investigation timeline events are the frontend's source of truth for live pipeline progress.
- Evidence graph data is the frontend's source of truth for claims, evidence, support, contradiction, and unverified counts.
- Docker Compose is the intended local startup path.

## Current Technical Debt

- Full Docker startup was not verified in this environment because Docker Desktop was not running.
- Full live investigation was not demonstrated because no DeepSeek API key was available in the environment.
- Embedding-based matching may still need a concrete provider and tests if it is not fully implemented in the current code.
- Source independence and lineage detection are not yet production-grade.
- Authentication, authorization, quotas, and abuse controls are not implemented.
- Public OpenAPI exposure changed from the original backend-foundation milestone and should be reviewed before deployment.

## Known Limitations

- Search quality depends on the local SearXNG configuration and upstream engines.
- Crawling may fail for JavaScript-heavy, blocked, paywalled, or bot-protected pages.
- The first working AI stages depend on DeepSeek structured JSON reliability.
- Verdict quality is bounded by retrieved evidence coverage.
- Long investigations currently execute in-process unless the workflow has already been moved to a worker.

## Open Questions

- Which embedding provider should be the default local/development option?
- What source quality rubric should be encoded first?
- What retention policy should apply to original HTML snapshots?
- Should investigations run synchronously for local development and asynchronously in production?
- Which first domain should receive golden eval coverage: health, education rankings, software trends, or product claims?

## Recommended Next Step

Start Docker Desktop, set `TRUTHENGINE_DEEPSEEK_API_KEY`, run `docker compose up --build`, and execute a real investigation such as:

```text
Is creatine bad for kidneys?
```

Verify that the frontend shows search/crawl timeline events, ingested sources, claims, evidence relations, contradiction results, and an algorithmic verdict from backend data.

## Files To Read First

1. `README.md`
2. `docs/HANDOFF.md`
3. `docs/AGENT_CONTEXT_LOG.md`
4. `src/truthengine/investigations/workflow.py`
5. `src/truthengine/investigations/service.py`
6. `src/truthengine/sources/pipeline.py`
7. `src/truthengine/search/searxng.py`
8. `src/truthengine/llm/deepseek.py`
9. `frontend/src/core/api.ts`
10. `frontend/src/features/workspace/Workspace.tsx`
