# TruthEngine AI Handoff Document

This document provides a comprehensive takeover summary and guides the next AI agent or engineer through the codebase architecture, recent fixes, verified state, and next steps.

---

## 1. Codebase Context & Current State

TruthEngine is designed as a **modular monolith** backend using FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Ruff, and strict mypy type checking.

Two core milestones are now complete, audited, and verified:
1. **Milestone 1: Production Backend Foundation & Health Checks**
2. **Milestone 2: Investigations Domain, Workflow Engine, & Audit Timeline**

### API Endpoints Covered
* `POST /investigations`: Creates a new investigation in the `CREATED` state.
* `GET /investigations/{id}`: Retrieves metadata of a single investigation.
* `POST /investigations/{id}/run`: Synchronously starts or resumes execution.
* `GET /investigations/{id}/timeline`: Fetches all immutable timeline audit logs for an investigation.

### 1.5 Product Architecture Review
A first-principles product architecture review has been conducted and documented in [PRODUCT_ARCHITECTURE_REVIEW.md](file:///C:/Projects/TruthEngine/docs/PRODUCT_ARCHITECTURE_REVIEW.md).
* **Aggregate Boundaries**: We decomposed the system from a single `Investigation` aggregate into four distinct aggregates: `Investigation`, `EvidenceGraph` (immutable, versioned), `SourceRegistry` (global, canonical), and `AuditLog`.
* **Engineering Roadmap**: Established a 10-milestone roadmap detailing milestones 3 through 10 (Ingestion, Graph Schema, Claim Extraction, AI Matcher, Contradiction Analyzer, Confidence Calibrator, Async Workers, and Sharing).

---

## 2. The Workflow Engine: State Machine Orchestrator Design

We rejected a generic, heavy "Workflow Engine" framework in favor of a database-backed **State Machine Orchestrator** (`workflow.py`). 

### Core State Lifecycle
An investigation proceeds sequentially through the following states:
`CREATED` (or `FAILED`) → `COLLECTING_SOURCES` → `ANALYZING` → `GENERATING_REPORT` → `COMPLETED`.

### Key Design Decisions
1. **Transaction Savepoints (`begin_nested`)**: Each stage function (e.g. `_collect_sources_mock`, `_analyze_mock`) is executed inside a SQLAlchemy nested transaction block (`session.begin_nested()`). If a stage throws an exception, the savepoint rolls back all database modifications made inside that stage's scope.
2. **Explicit Commit on Error Checkpoints**: If an exception is raised, the orchestrator catches it, transitions the investigation status to `FAILED`, registers a `WORKFLOW_FAILED` timeline event, commits these changes explicitly via `session.commit()`, and then re-raises the error. This guarantees that:
   * Bad state is discarded (rolled back by savepoint).
   * Status transitions to `FAILED` and crash details are committed (saved in DB).
   * The workflow can be **restarted** from the last successfully completed checkpoint.
3. **Immutable Audit Timeline**: Every transition, start, completion, or failure registers a `TimelineEvent` record mapping to the `investigation_timeline_events` table. This serves as the foundation for user transparency and auditability.

---

## 3. Verified Standards & Metrics

* **Tests**: `pytest` -> **26 tests passed**, 100% test success rate (includes full integration tests, error checkpoints, and restartability verification).
* **Linting**: `ruff check .` -> **Passed**, 0 lint errors.
* **Formatting**: `ruff format --check .` -> **Passed**, all files correctly formatted.
* **Type Safety**: `mypy src tests` -> **Passed**, 0 errors in strict type checking.

---

## 3.5 Investigation Planning: Deterministic Planner Architecture

We completed **Milestone 3: Investigation Planning**, introducing a deterministic domain-based planner in the `planning` sub-module.

### Rationale: Determinism Before AI
In a truth-seeking engine, the standards of proof (the objective, preferred/excluded source categories, and success criteria) must be **hard, deterministic constraints**.
* Relying on LLMs to generate planning constraints leads to "hallucinated validation rules" where different runs of the same query enforce different evidence levels.
* By codifying these rules inside domain-specific `DomainProfile` classes (e.g. `EducationProfile`, `TechnologyProfile`), the platform guarantees that every execution for a domain follows identical, explainable, and reproducible constraints.

### Extensibility & Future AI Integration
* **Adding New Domains**: Future domains (Medicine, Finance, Law) can be added simply by subclassing `DomainProfile`, defining their regex keyword matching and rule sets, and registering them in `profiles.py`. No planner code needs modification.
* **Future AI-Assisted Planning**: If we want to introduce LLM assistance later, we can do so **complementarily**:
  1. An LLM can classify the query and recommend the appropriate `DomainProfile` if regex keyword matching has low confidence.
  2. The LLM can generate a list of custom search queries/keywords based on the planner's structured strategy, while the preferred/excluded source categories and success criteria remain strictly enforced by the profile code.

---

## 3.6 Evidence Graph Storage: Relational Bipartite Graph Architecture

We completed **Milestone 4: Evidence Graph Storage Model**, implementing versioned, immutable bipartite directed graph schemas.

### Brutal Architecture Review

#### Why PostgreSQL/Relational Instead of Neo4j/Graph Database?
1. **Consistency & Transaction Safety**: In an engine tracking claims and audit logs, transactional consistency is critical. Foreign keys and cascade deletions are natively and highly performant in PostgreSQL, whereas Neo4j lacks strict ACID constraints across nested tabular relationships without extra overhead.
2. **Operational Simplicity**: TruthEngine is a modular monolith. Running a separate database server (like Neo4j) increases deployment complexity, memory footprint, and network latency for zero immediate product benefit.
3. **Structured Queries**: TruthEngine does not perform arbitrary multi-hop path traversals (which Neo4j is optimized for). Instead, it queries a strict **bipartite graph** (Claims -> Relations -> EvidenceItems -> Snapshots). This is highly performant in Postgres using simple, indexed join queries (which are eagerly loaded via `lazy="joined"`).

#### Why Immutable Graph Versions?
* **Unverifiable Mutations**: If the graph were mutable in place, updating a claim or adding an annotation would wipe out the historical context of what evidence supported a claim at a specific timestamp.
* **Audit Lineage**: By making every modification generate a new `version` of the graph, we can trace exactly how an investigation progressed over time, compare versions, and audit downstream calculations without mutating historical data.

#### Future Scaling Considerations & Limitations
* **Storage Footprint**: Since each graph version clones the nodes/edges (if they are modified), a high-frequency change cycle will generate duplicate records.
* **Mitigation**: We can transition to an **Event Sourcing** model or delta-based graph model in the future, where we only record differences (add node, delete edge) between versions instead of full graph copies.
* **Index Contention**: As the number of claims/relations grows, table indices on foreign keys will become large. Proper indexing on `graph_id`, `claim_id`, and `evidence_item_id` has been implemented in the migrations to prevent slow sequential scans.

#### How Future AI Stages Will Populate the Graph
* AI stages (e.g. claim extraction, passage matching) will execute during the workflow transitions.
* The output of the AI (Pydantic objects) will be translated into new `Claim`, `EvidenceItem`, and `EvidenceRelation` domain entities by the domain service layer.
* The service will load the latest version, copy the existing nodes, append the new AI-extracted nodes and relation edges, and save them as a *new version* of the graph under a single transaction. This keeps the graph model completely isolated from model providers or AI logic.

---

## 3.7 Source Snapshot & Ingestion Layer: Relational Registry Architecture

We completed **Milestone 5: Source Snapshot & Ingestion Layer**, implementing publisher domain-based Source Identities, failure audit trails, and security policies.

### Brutal Architecture Review & Compromises

#### How this Design Supports Future Retrieval Adapters
* **Decoupled Fetch/Scrape Sequence**: The service interacts with a generic URL crawling interface. Future custom adapters (e.g. academic API clients, PDF extractors, or custom headless browser sessions) can be added as specialized fetch pipeline adapters without altering the core database structure or service logic.
* **Open Metadata Mapping**: The `metadata` JSON field on the snapshot stores headers, scraping parameters, and credentials (if any) dynamically, letting adapters save proprietary fields without altering database tables.

#### How Immutable Snapshots Improve Explainability
* **Anti-Drift Citation**: Webpages mutate constantly. If a fact-checking model cites a page that undergoes edits, the citation becomes broken, creating reputational risk for TruthEngine. By maintaining immutable, hashed text snapshots, the system preserves a permanent proof of what text was analyzed at the exact moment of investigation.
* **Deterministic Audits**: Any downstream confidence scoring algorithm can run repeatedly on the same snapshot text and yield identical ratings, ensuring explainability.

#### Limitations of HTML-Only Ingestion
* **No Javascript Execution**: SPA (Single Page Applications) relying on Client-Side Rendering (CSR) like React or Angular will return empty/shell tags, preventing content analysis.
* **Paywalls and CAPTCHAs**: Sites using Cloudflare shields or session tokens will block straightforward HTTPX requests.
* **File Format Exclusions**: We reject binary types (PDF, DOCX) in V1.

#### How Future Formats (PDF, DOCX, Markdown, API responses) Fit into this Model
* **Publisher domain maps**: PDF/DOCX files downloaded from academic links (e.g. `arxiv.org/pdf/...`) belong to the `arxiv.org` Source (domain identity).
* **Text Extraction mapping**: An adapter will parse the PDF bytes (e.g., using `PyPDF` or `pypandoc`), extract clean text, and output it directly to the `extracted_text` column.
* **API payloads**: JSON payloads from API endpoints can be serialized to a readable JSON-text format (or markdown string) and stored in `extracted_text`, while raw JSON maps to the `metadata` column. The fingerprinting and deduplication logic runs identically on this text, requiring no schema changes.

#### Every Design Compromise Made
1. **Synchronous Ingestion Block**: Scrapes are executed synchronously inside the API thread. A slow site blocks the thread for up to 10 seconds. (Compromise: Accepted to keep execution synchronous and simple before async workers are introduced).
2. **First-IP Selection**: Our SSRF shield checks all resolved IPs, but selects the first IP for request execution. A DNS rebinding attack could potentially bypass this if the host name rotates its IP list dynamically during HTTPX's internal socket connection. (Compromise: Deemed acceptable for V1, but will require custom HTTPX socket binders in production).
3. **Regex Content-Type parsing**: Simple substring searches are used to validate content types. This could be bypassed by malformed MIME structures.

---

## 4. Remaining Technical Debt

* **No Authentication/Authorization**: Endpoints do not enforce user/tenant token boundaries yet.
* **Synchronous Thread Blocking**: The execution is synchronous and blocking in FastAPI. Once workers are introduced, execution should be offloaded to asynchronous background jobs.
* **Mock Execution Stages**: Stage methods in `workflow.py` contain mock logs. They need real scraping and analytical implementations.

---

## 5. Evolution Path (Adding Ingestion and AI)

When source collection and AI tasks are implemented in subsequent milestones, the orchestrator is designed to scale cleanly:

1. **Integrating Source Ingestion**:
   * Replace `_collect_sources_mock()` with a call to the `ingestion` module to crawl/scrape target URLs.
   * Save extracted source metadata and snapshots to the DB inside the nested transaction. If ingestion fails (e.g. timeout, paywall), the savepoint will discard partial source writes while the orchestrator marks the investigation `FAILED` and records the error details on the timeline.
2. **Integrating AI Tasks**:
   * Replace `_analyze_mock()` with typed, schema-validated AI task requests routed to the `ai_tasks` module.
   * Model outputs, claim extractions, and evidence relation proposals will be validated by domain services and saved within the stage's nested transaction.
3. **Moving to Asynchronous execution**:
   * When async queue processing is introduced (e.g. celery or arq), the endpoint `POST /investigations/{id}/run` should enqueue a background job. The worker will execute `InvestigationWorkflowOrchestrator(repo, timeline_repo).run(id)` asynchronously, allowing the API gateway to return immediately with a `QUEUED` status.

---

## 3.8 Candidate Passage Selection: Deterministic Lexical Filter Architecture

We completed **Milestone 6: Candidate Passage Selection**, implementing paragraph-level segmentation, structured explainability metadata, and SelectionPolicy boundaries.

### Brutal Architecture Review & Compromises

#### Why this Stage Exists Before Claim Extraction
Directly passing full crawled documents to an LLM for Claim Extraction is highly inefficient:
1. **Context Window Costs & Latency**: LLM pricing is heavily input-token biased. Processing 100k characters of raw HTML boilerplate for every query quickly drains budget.
2. **Lost-in-the-Middle Phenomenon**: Massive, unstructured text contexts degrade extraction accuracy. LLMs routinely miss critical statements buried inside long documents.
3. **Traceability**: By filtering raw documents down to discrete, high-relevance `CandidatePassage` snippets *before* AI extraction, TruthEngine guarantees that every extracted claim references a specific, audit-inspectable paragraph.

#### Why Lexical Overlap and Policies over Vector Search?
1. **Explainable Matching**: A vector search cosine similarity score (e.g. `0.84`) is a black-box. Lexical scoring (matched term frequency + heading boost + domain profile keyword checks) produces a fully inspectable match statement showing exactly why the paragraph was selected.
2. **Predictable Capacity Control**: Incorporating `SelectionPolicy` ensures the pipeline caps and thresholds passage selection dynamically, keeping downstream token budgets bounded.

#### Design Compromises & Shortcomings
1. **Heading Classification Heuristic**: Headings are classified in plain text based on character length limits (< 80 chars) and absence of ending punctuation. While extremely fast, it can misclassify short sentences.
2. **Global Snapshot Scan**: Currently, the selector scans all snapshots in the database to select candidates. For a production scale of millions of pages, this will require adding a link table or direct indexing queries to constrain searches.
3. **English-Only Stop Words**: Stop-word filtering uses a hardcoded English set. Multilingual support will require loading language-specific dictionaries.

---

## 6. Guidelines for the Next AI Agent

1. **Do not add AI or queues prematurely**: Maintain the synchronous monolith pattern until explicitly instructed to scale.
2. **Maintain Strict Quality Checks**: Before checking in code, run:
   ```bash
   python -m pytest
   ruff check .
   ruff format --check .
   mypy src tests
   ```

