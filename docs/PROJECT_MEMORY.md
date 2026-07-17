# TruthEngine Project Memory

## Project Mission
TruthEngine is an evidence reasoning platform designed to make evidence inspectable and transparent. It opposes opaque AI summaries and fact-checking, focusing instead on showing claims, required evidence, source lineage, and confidence calibration.

## Technology Stack
* **Framework**: FastAPI (modular monolith architecture)
* **Language**: Python 3.12+ (strict mypy type checking)
* **Database**: PostgreSQL 16+ via SQLAlchemy 2.0 ORM & Alembic migrations
* **Code Quality**: Ruff linter & formatter, Pytest suite
* **Logging**: Custom JSON logging in production/staging, plaintext logging with dynamic Request ID tracing in local/test configurations.

---

## Bounded Contexts & Active Modules

1. **`core`**: Contains database connections, configuration settings, custom logging formatters, custom exception handlers, request context tracing, and security/request middlewares.
2. **`api`**: Top-level API gateways, routers, and system health checks (`GET /health`).
3. **`investigations`**: Exposes CRUD, lifecycle stage transitions, and immutable audit logs.
   * **Domain Entities**: `Investigation`, `TimelineEvent`, and `InvestigationStatus`.
   * **Repositories**: `SqlAlchemyInvestigationRepository` and `SqlAlchemyTimelineEventRepository`.
   * **Orchestration**: `InvestigationWorkflowOrchestrator` manages synchronous state transitions and error checkpoints.

---

## Completed Milestones

### Milestone 1: Production Backend Foundation & Health Checks
* Established the modular monolith structure, FastAPI factory, and Pydantic configuration settings.
* Implemented JSON structured logging, exception handlers, and security headers.
* Set up database connection engine, session scope provider, and SQLAlchemy base classes.
* Set up tests, Ruff, mypy, pre-commit, and CI workflows.

### Milestone 2: Investigations Domain, Workflow Engine, & Audit Timeline
* Updated `InvestigationStatus` lifecycle stages to: `CREATED` → `COLLECTING_SOURCES` → `ANALYZING` → `GENERATING_REPORT` → `COMPLETED` (or `FAILED`).
* Created `investigation_timeline_events` schema with an indexed foreign key referencing `investigations.id` (`ondelete="CASCADE"`).
* Designed and built the synchronous **State Machine Orchestrator** (`workflow.py`) mapping the linear progression of an investigation.
* Integrated nested transaction savepoints (`session.begin_nested()`) wrapping each stage execution. This guarantees that individual step failures roll back step-specific DB modifications while committing status updates to `FAILED` and error timeline logs.
* Added endpoints:
  * `POST /investigations/{id}/run`: Synchronously runs or resumes execution.
  * `GET /investigations/{id}/timeline`: Retrieves chronological immutable events for the audit log.
* Wrote integration tests covering successful transitions, endpoint routes, database state consistency, and restartability scenarios.

### Milestone 2: Product Architecture Review (Completed)
* Performed a first-principles architectural review of the entire product design.
* Challenged aggregate root boundaries and established clear ownership rules (Investigation, Evidence Graph, Source Registry, and Audit Log aggregates).
* Proposed UML model mapping domain entities to SQLite/PostgreSQL-compatible relational nodes.
* Structured a comprehensive engineering roadmap spanning Milestones 3 through 10, detailing objectives, architectural impact, files, testing, and exit criteria.
* Documented findings permanently in [PRODUCT_ARCHITECTURE_REVIEW.md](file:///C:/Projects/TruthEngine/docs/PRODUCT_ARCHITECTURE_REVIEW.md).

### Milestone 3: Investigation Planning (Completed)
* Introduced a deterministic, extensible planning engine in the `planning` sub-module.
* Added `DomainProfile` and `InvestigationPlan` domain entities.
* Created `EducationProfile`, `TechnologyProfile`, and `GeneralProfile` concrete profiles defining matching rules, evidence requirements, preferred/excluded sources, and limitations.
* Persisted plans in the `investigation_plans` table using SQLAlchemy `InvestigationPlanRecord` and `SqlAlchemyInvestigationPlanRepository` with cascading foreign keys.
* Exposed `POST /investigations/{id}/plan` and `GET /investigations/{id}/plan` REST endpoints.
* Wrote unit tests for domain matching, snapshot verification, and API integration tests (all green).

### Milestone 4: Evidence Graph Storage Model (Completed)
* Implemented the relational storage schema for versioned, immutable evidence graphs.
* Created database migrations in `20260717_0004_create_evidence_graphs.py` for tables: `evidence_graphs`, `claims`, `evidence_items`, and `evidence_relations`.
* Added domain models (`Claim`, `EvidenceItem`, `EvidenceRelation`, `EvidenceGraph`) and type enums (`ClaimType`, `ClaimStatus`, `RelationType`) in the `graphs` sub-module.
* Persisted graphs using SQLAlchemy records with cascade deletions and eager relationship joins (`lazy="joined"`).
* Exposed REST endpoints:
  * `POST /investigations/{id}/graphs`: Creates version 1 of the graph (initially empty).
  * `GET /investigations/{id}/graphs/latest`: Returns the latest version of the graph for the investigation.
  * `GET /graphs/{id}`: Returns the full graph by its specific ID.
* Added comprehensive tests in `tests/test_graphs.py` covering repository CRUD, versioning logic, and REST routes.

### Milestone 5: Source Snapshot & Ingestion Layer (Completed)
* Implemented the secure, relational Source Ingestion and Snapshotting context in the `sources` sub-module.
* Created database migration `20260717_0005_create_sources_and_snapshots.py` mapping `sources` (publisher domain registry) and `source_snapshots` (versioned resource snapshots).
* Added domain models (`Source`, `SourceSnapshot`) and enums (`SourceCategory`) in `sources/domain.py`.
* Implemented URL normalization, DNS host resolution verification, and SSRF shielding in `sources/security.py`.
* Developed a chunk-streaming HTTP fetcher using HTTPX (timeout policy: 10s, redirect limit: 5, max size: 5 MB) and raw HTML parser using BeautifulSoup in `sources/pipeline.py`.
* Modeled network and host blocking failures as immutable failed snapshots to record scraping audit trails.
* Exposed REST endpoints:
  * `POST /sources/ingest`: Crawls and deduplicates URL content.
  * `GET /sources/{source_id}`: Fetches publisher details.
  * `GET /snapshots/{snapshot_id}`: Fetches a specific versioned snapshot.
* Wrote integration tests in `tests/test_sources.py` validating SSRF blocking, deduplication, and failed fetches (22/22 tests passing).

### Milestone 6: Candidate Passage Selection (Completed)
* Introduced Candidate Passage Selection under the `investigations/candidates/` context.
* Renamed the candidate aggregate from `EvidenceCandidate` to `CandidatePassage` because evidence only exists once a passage has been linked to a claim; a candidate passage is merely a highlighted text snippet.
* Created database migration `20260717_0006_create_document_segments_and_passages.py` for tables: `document_segments` and `candidate_passages`.
* Implemented paragraph-level segmentation in `selector.py` mapping structural heading, heading levels, paragraph order, and parent section context to preserve document hierarchy.
* Developed a deterministic lexical ranking selector applying configurable `SelectionPolicy` boundaries (min threshold, capacity limits) and domain profile heuristics.
* Persisted structured selection explanations in a machine-readable JSON format, capturing query term overlaps, heading matches, and matching domain rules for traceability.
* Exposed REST endpoints:
  * `POST /investigations/{id}/candidates`: Segments snapshots, scores passages, and persists candidates.
  * `GET /investigations/{id}/candidates`: Retrieves previously persisted candidate passages.
* Wrote integration and unit tests in `tests/test_candidates.py` covering segmentation, ranking, repository, and endpoint pipelines (26/26 tests passing).



