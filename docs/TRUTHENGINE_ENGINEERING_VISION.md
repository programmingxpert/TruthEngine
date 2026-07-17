# TruthEngine Engineering Vision

Date: 2026-07-17
Status: Founding architecture blueprint
Audience: founders, engineering leads, product leads, research leads, agentic coding systems

## One-Sentence Mission

TruthEngine exists to make evidence inspectable.

It should not ask users to trust an AI answer. It should help users inspect what is known, what is disputed, what is missing, where claims came from, and how strongly conclusions are supported.

## Founding Premise

The internet has become increasingly difficult to trust.

Search engines optimize for ranking and traffic. Social platforms optimize for engagement. Marketing websites optimize for persuasion. LLMs optimize for producing plausible answers. Even official websites, schools, universities, companies, and products often present claims like "No. 1", "most trusted", "industry-leading", or "best in India" without showing independent proof.

The deeper problem is not only misinformation. It is unverified claims presented with confidence.

Unsupported claims can spread through repetition:

```text
Original marketing page
    -> Blog repeats the claim
    -> News article quotes the blog
    -> Search result snippet repeats it
    -> AI answer summarizes it
```

This creates an illusion of credibility. A statement repeated 1,000 times is not 1,000 independent pieces of evidence if all versions trace back to the same original source.

TruthEngine should recognize that pattern.

## What TruthEngine Is Not

TruthEngine is not:

- ChatGPT with citations.
- Another RAG chatbot.
- A search engine.
- A binary fact checker that simply labels claims true or false.
- A summarizer.
- A wrapper around an LLM.
- A confidence theater system that hides uncertainty behind polished prose.

## What TruthEngine Is

TruthEngine is an evidence reasoning platform.

Given a question, claim, webpage, document, advertisement, institution profile, product page, or public statement, the system should:

- Identify important factual claims.
- Classify claim types before evaluating them.
- Determine what evidence would be required to support each claim.
- Retrieve evidence from multiple sources.
- Distinguish primary, secondary, tertiary, and repeated evidence.
- Detect contradictions and missing evidence.
- Trace claim lineage whenever possible.
- Estimate confidence through transparent reasoning.
- Separate facts, opinions, marketing language, predictions, and interpretations.
- Expose every meaningful step to the user.

The product is not the paragraph answer. The product is the inspectable evidence graph.

## Core Principles

1. Evidence before conclusions.
2. Transparency before confidence.
3. Multiple independent sources over repeated sources.
4. Explain uncertainty instead of hiding it.
5. Separate facts from opinions.
6. Treat marketing claims as claims, not facts.
7. Trace claims back to origins whenever possible.
8. Users should always be able to inspect how the system reached a conclusion.
9. Every architectural decision should support long-term trust.
10. The system should encourage critical thinking instead of replacing it.

## Product North Star

TruthEngine should become an operating system for evidence.

For any important question, the user should be able to see:

```text
Question
    -> Claims
    -> Required Evidence
    -> Evidence Collection
    -> Source Analysis
    -> Evidence Lineage
    -> Independence Analysis
    -> Contradictions
    -> Missing Evidence
    -> Confidence Explanation
    -> Interactive Evidence Graph
    -> Human-Readable Summary
```

The graph is the durable artifact. The summary is only a convenience layer.

## The Critical Insight: Evidence Independence

TruthEngine must distinguish between independent evidence and repeated evidence.

Example:

```text
Company website says: "We are the leading platform."
    -> Blog copies company language.
    -> News article quotes the blog.
    -> Comparison page repeats the phrase.
    -> AI article summarizes the comparison page.
```

This is not five sources. It may be one original claim with four repetitions.

TruthEngine should model:

- Source origin.
- Copying or paraphrase relationships.
- Citation chains.
- Shared language similarity.
- Shared data provenance.
- Whether a source independently verified the claim.
- Whether the source has incentive to promote the claim.

Confidence should decrease when evidence is repeated rather than independently verified.

## Claim Classification

Before evaluating a claim, TruthEngine should classify it. This prevents the system from treating every sentence as the same kind of proposition.

### Claim Types

- Verifiable factual claim: "The company was founded in 2018."
- Quantitative claim: "The product has 2 million users."
- Ranking claim: "Ranked No. 1 in India."
- Superlative claim: "The most trusted platform."
- Comparative claim: "Faster than C++."
- Causal claim: "Remote work increased productivity."
- Prediction: "AI will replace lawyers."
- Opinion: "This is the best school."
- Marketing claim: "Industry-leading solution."
- Credential claim: "Government approved."
- Safety or security claim: "Most secure."
- Scientific claim: "Clinically proven."
- Legal or compliance claim: "GDPR compliant."
- Historical claim: "First company to do X."
- Attribution claim: "Experts say..."

### Claim Evaluation Questions

For each claim, the system should ask:

- What would count as support?
- What would count as contradiction?
- Who is making the claim?
- Does the claimant benefit if the claim is believed?
- Is the claim measurable?
- Is there an independent standard or authority?
- Is the claim time-sensitive?
- Is the claim geographic or context-dependent?
- Is it actually a factual claim, or just persuasive language?

## Marketing Claims vs Verifiable Facts

TruthEngine should treat marketing claims as a first-class category.

Example:

```text
Claim: "We are India's No. 1 University."
```

The system should ask:

- According to whom?
- According to which ranking system?
- Which year?
- Which category?
- Which geography?
- What methodology?
- Is the ranking independent?
- Is the ranking paid, sponsored, self-reported, or editorial?
- Are there competing rankings that disagree?

Possible evidence:

- NIRF rankings.
- QS rankings.
- Times Higher Education rankings.
- Government data.
- Independent research.
- Accreditation bodies.
- Audited enrollment or placement data.

If no independent evidence exists, the system should label the claim as a marketing claim, not a verified fact.

Example output:

```text
Claim: University X is the best private university.
Origin: University X website.
Repeated by: Education Blog A, Education Blog B.
Independent verification: None found.
Evidence independence: Low.
Confidence: 18%.
Classification: Marketing claim.
Reason: The claim is superlative, undefined, and appears to originate from the institution itself.
```

## Evidence Lineage

Every important claim should have an origin hypothesis.

TruthEngine should attempt to answer:

- Who first made this claim?
- Who repeated it?
- Who independently verified it?
- Has the claim changed over time?
- Are later sources citing the original source, copying the language, or independently measuring the fact?
- Do multiple sources depend on the same dataset?
- Is the cited source still available?
- Has the source changed its wording over time?

Lineage is probabilistic. The system will not always know the true origin. It should expose this uncertainty instead of pretending certainty.

## Product Surface

TruthEngine should have several product modes, but all should share the same evidence reasoning core.

### 1. Ask Mode

User asks a question:

```text
Is Rust replacing C++?
```

TruthEngine decomposes the question into claims:

- Rust adoption is increasing.
- C++ adoption is declining.
- Rust is replacing C++ in some domains.
- Rust is not replacing C++ universally.
- Migration differs by industry.

It then builds an evidence graph and exposes source-level reasoning.

### 2. Claim Audit Mode

User enters a claim:

```text
Company X is the most secure AI platform.
```

TruthEngine classifies it, finds support and contradiction, checks independence, and explains whether the claim is verifiable.

### 3. Webpage Audit Mode

User enters a URL. TruthEngine extracts claims from the page, groups them by type, highlights unsupported claims, and shows which claims have independent evidence.

This is especially important for university pages, school advertisements, SaaS landing pages, investment memos, health websites, and "best product" blogs.

### 4. Evidence Graph Mode

The user explores:

- Claims.
- Evidence nodes.
- Source nodes.
- Contradiction edges.
- Repetition edges.
- Confidence factors.
- Missing evidence.
- Timeline of claim propagation.

This is the core product experience.

### 5. Research Workspace Mode

Users can save investigations, add notes, compare evidence, export graphs, and invite collaborators.

Target users:

- Researchers.
- Students.
- Journalists.
- Engineers.
- Founders.
- Investors.
- Policy makers.
- Legal and compliance teams.

## The Evidence Graph

The evidence graph is the central data structure.

### Core Node Types

- Question.
- Claim.
- Subclaim.
- Evidence item.
- Source.
- Author or organization.
- Dataset.
- Ranking system.
- Methodology.
- Quote.
- Measurement.
- Contradiction.
- Missing evidence marker.
- User annotation.

### Core Edge Types

- Supports.
- Contradicts.
- Qualifies.
- Repeats.
- Cites.
- Originates from.
- Depends on.
- Derived from.
- Same underlying source as.
- Methodologically related to.
- Time-bound update.
- User disputes.

### Important Node Properties

Every evidence item should store:

- URL or document reference.
- Retrieval timestamp.
- Publication timestamp if available.
- Author or publisher.
- Source type.
- Extracted quote or passage.
- Claim it relates to.
- Whether it is primary or secondary.
- Whether it is independent or repeated.
- Confidence contribution.
- Known limitations.
- Hash or snapshot reference.

### Why Graph First

A linear answer hides reasoning. A graph exposes structure:

- Many sources can support one claim.
- One source can support multiple claims.
- One claim can have both support and contradiction.
- Many sources can trace back to one origin.
- Missing evidence can be represented explicitly.

## Source Classification

TruthEngine should classify sources before weighing them.

### Source Types

- Primary official source.
- Primary data source.
- Independent regulator or government source.
- Independent academic source.
- Independent ranking or benchmark source.
- News reporting.
- Industry analyst report.
- Blog or commentary.
- Marketing page.
- User-generated content.
- AI-generated or suspected AI-generated content.
- Aggregator or scraper.
- Archived source.

### Source Quality Factors

- Independence from the claimant.
- Methodology transparency.
- Data availability.
- Correction history.
- Conflict of interest.
- Publication date.
- Author identity.
- Citation quality.
- Original reporting vs repetition.
- Domain expertise.
- Incentive alignment.

Source quality is not the same as truth. A high-quality source can be wrong. A low-quality source can contain true facts. TruthEngine should avoid simplistic authority worship.

## Confidence Model

TruthEngine should not output a single unexplained confidence score.

It should output a confidence explanation with components.

### Confidence Inputs

- Evidence relevance.
- Evidence strength.
- Source independence.
- Source quality.
- Number of independent source families.
- Recency.
- Methodology quality.
- Claim specificity.
- Contradiction strength.
- Missing evidence severity.
- Domain uncertainty.
- Lineage clarity.

### Example Confidence Breakdown

```text
Claim: Rust is replacing C++.

Confidence in broad claim: Low to moderate.

Why:
- Strong evidence that Rust adoption is growing.
- Limited evidence that C++ usage is broadly declining.
- Strong evidence that Rust is replacing C++ in some safety-critical new projects.
- Weak evidence that Rust is replacing C++ across all systems programming.
- Evidence varies by domain.

Better conclusion:
Rust is gaining adoption and replacing C++ in some contexts, but the broad claim that Rust is replacing C++ overall is not well supported.
```

### Confidence Should Be Explainable

Users should be able to click any confidence factor and inspect:

- Which evidence contributed to it.
- Which evidence weakened it.
- Which assumptions were made.
- What missing data would change the conclusion.

## Contradiction Handling

TruthEngine should make conflicts visible.

Contradictions may happen because:

- Sources disagree.
- Data is from different time periods.
- Definitions differ.
- Metrics differ.
- Geographies differ.
- Marketing language overstates a narrow fact.
- One source is outdated.
- One source misquotes another.
- Evidence supports a weaker version of the claim but not the stronger one.

The system should not flatten contradictions into a fake average. It should show the disagreement and explain possible reasons.

## Missing Evidence as a First-Class Output

Missing evidence is not a failure. It is useful information.

TruthEngine should explicitly show:

- No independent source found.
- No primary data found.
- Claim is too vague to verify.
- Claim depends on undefined terms.
- Claim is time-sensitive and available evidence is outdated.
- Claim requires private data.
- Claim requires expert interpretation.
- Claim depends on a ranking methodology that is not public.

This is one of the product's core trust advantages.

## First-Principles Architecture

TruthEngine should be designed around evidence objects, not chat messages.

### Architectural Tenets

1. Evidence objects are durable.
2. Claims are versioned.
3. Sources are snapshotted.
4. Retrieval is reproducible where possible.
5. Reasoning steps are inspectable.
6. Models are replaceable.
7. The system stores uncertainty explicitly.
8. The graph is the source of truth.
9. Summaries are generated from graph state, not directly from raw search results.
10. User trust depends on auditability, not model charisma.

## High-Level System Components

### 1. Intake Layer

Accepts:

- Questions.
- Claims.
- URLs.
- Documents.
- Screenshots.
- Research tasks.

Outputs:

- Normalized investigation request.
- User intent.
- Scope boundaries.
- Time and geography constraints.

### 2. Claim Extraction Layer

Extracts and normalizes claims.

Responsibilities:

- Split complex questions into atomic factual claims.
- Preserve original user wording.
- Detect implied claims.
- Identify vague or undefined terms.
- Classify claims by type.
- Mark claims that are not directly verifiable.

### 3. Evidence Requirement Planner

For each claim, determines what evidence would be needed.

Example:

```text
Claim: "School X is the best in India."

Required evidence:
- Definition of "best".
- Independent ranking or benchmark.
- Ranking year.
- Ranking methodology.
- Comparison set.
- Whether the school category matches the claim.
```

### 4. Retrieval Layer

Retrieves evidence from multiple channels.

Possible retrieval channels:

- Web search APIs.
- Official websites.
- Government datasets.
- Academic indexes.
- Ranking databases.
- News APIs.
- Public registries.
- Archived web snapshots.
- Domain-specific databases.
- User-provided documents.

Retrieval must preserve metadata, timestamps, snippets, raw passages, and source URLs.

### 5. Source Canonicalization Layer

Groups URLs and documents by underlying source.

Responsibilities:

- Resolve canonical domains.
- Detect syndication.
- Detect copied content.
- Identify citation chains.
- Cluster near-duplicate passages.
- Map sources to organizations.
- Detect source families.

This is essential for evidence independence.

### 6. Evidence Extraction Layer

Extracts relevant evidence from sources.

Responsibilities:

- Extract passages.
- Link passages to claims.
- Classify passage relationship: support, contradiction, qualification, irrelevant.
- Preserve exact quotes where legally and technically appropriate.
- Identify whether evidence is direct or indirect.

### 7. Lineage and Independence Layer

Builds source dependency hypotheses.

Signals:

- Citations and hyperlinks.
- Publication timestamps.
- Similar wording.
- Quoted phrases.
- Shared datasets.
- Press release reuse.
- Author or publisher relationships.
- Canonical URL relationships.
- Syndication metadata.

Outputs:

- Independent source families.
- Repeated evidence clusters.
- Origin hypotheses.
- Confidence penalty for repetition.

### 8. Reasoning Layer

Computes claim-level assessment.

Responsibilities:

- Aggregate evidence by claim.
- Weigh support and contradiction.
- Account for independence.
- Identify missing evidence.
- Produce confidence explanation.
- Generate alternative formulations of the claim that are better supported.

Important: this layer should not be a single opaque LLM call. It should be a pipeline of explicit intermediate artifacts, with LLMs used as replaceable components where useful.

### 9. Evidence Graph Store

Stores the durable investigation graph.

Requirements:

- Versioned nodes and edges.
- Snapshot references.
- Audit trails.
- User annotations.
- Re-runnable retrieval metadata.
- Confidence factor provenance.

Candidates over time:

- PostgreSQL for core relational data.
- pgvector or a dedicated vector store for semantic retrieval.
- Neo4j, Memgraph, Kuzu, or PostgreSQL graph patterns for graph traversal.
- Object storage for snapshots.
- Search index such as OpenSearch, Elasticsearch, Typesense, or Meilisearch for source and passage search.

Early product can start simpler with PostgreSQL plus graph-shaped tables. Do not prematurely overbuild distributed graph infrastructure.

### 10. Presentation Layer

The UI should expose:

- Claim cards.
- Evidence graph.
- Source lineage.
- Confidence explanation.
- Contradiction view.
- Missing evidence view.
- Source family clustering.
- Human-readable synthesis.
- Exportable research artifacts.

The summary should always be downstream of the evidence graph.

## Model Strategy

TruthEngine will likely use LLMs, but the architecture should not depend on trusting them.

LLMs are useful for:

- Claim extraction.
- Claim classification.
- Query planning.
- Passage relevance judgments.
- Natural-language explanation.
- Contradiction candidate detection.
- Summarizing graph state.

LLMs should not be the sole authority for:

- Final confidence.
- Source independence.
- Provenance.
- Citation correctness.
- Whether a source exists.
- Whether a claim is true.

Every model-generated decision should produce a structured artifact that can be inspected, tested, and challenged.

## Trust Boundary

TruthEngine's trust boundary should be clear:

- The system can retrieve evidence.
- The system can classify and organize evidence.
- The system can estimate support.
- The system can expose uncertainty.
- The system cannot magically know truth when evidence is unavailable.

The product should say "we did not find enough independent evidence" more often than typical AI systems.

## Evaluation Strategy

TruthEngine needs an evaluation program from the beginning.

### Eval Dimensions

- Claim extraction accuracy.
- Claim classification accuracy.
- Evidence retrieval recall.
- Evidence relevance precision.
- Source independence detection.
- Lineage detection.
- Contradiction detection.
- Missing evidence detection.
- Confidence calibration.
- Citation correctness.
- User comprehension.
- Resistance to SEO spam.
- Resistance to repeated-claim amplification.

### Golden Datasets

Create benchmark sets for:

- University ranking claims.
- SaaS "leading platform" claims.
- Health claims.
- Product comparison claims.
- Public policy claims.
- Scientific claims.
- Investment and market-size claims.
- Historical claims.
- AI-generated content farms.

Each benchmark should include:

- Input claim.
- Expected claim classification.
- Known primary sources.
- Known repeated sources.
- Known contradictions.
- Expected confidence explanation.

## Product UX Principles

1. The user should see evidence before the generated answer.
2. Every conclusion should be expandable.
3. Confidence should be explained, not merely displayed.
4. Missing evidence should feel like a useful result, not an error.
5. Users should be able to challenge the system.
6. The UI should teach critical thinking through interaction.
7. The product should avoid over-polished certainty.

## Example UX Object

```text
Claim
"University X is India's No. 1 private university."

Classification
Ranking claim + marketing claim.

Evidence Required
Independent ranking, year, category, methodology, comparison set.

Evidence Found
1 independent ranking source mentions University X at rank 14 in category A.
3 blogs repeat the university's claim without methodology.
1 archived university page appears to be the origin.

Contradictions
NIRF 2025 does not rank University X as No. 1 in the relevant category.

Missing Evidence
No independent source found supporting "No. 1 private university" as written.

Evidence Independence
Low. Most repetitions trace back to the university's own website.

Confidence
18%.

Better Supported Statement
University X claims to be No. 1, but independent evidence found in this investigation does not support the claim as written.
```

## Security, Abuse, and Integrity

TruthEngine will be attacked if it becomes useful.

Expected attack vectors:

- SEO spam designed to look independent.
- Coordinated content farms.
- Fake citations.
- Synthetic academic papers.
- Paid ranking sites.
- Review manipulation.
- Prompt injection in webpages.
- Source poisoning.
- Legal pressure from criticized organizations.
- Attempts to make the system defame competitors.

Defensive principles:

- Treat retrieved text as untrusted input.
- Never allow webpage content to instruct the system.
- Preserve source snapshots.
- Maintain audit logs.
- Separate evidence from generated commentary.
- Support dispute workflows.
- Avoid making claims beyond the evidence.
- Build red-team datasets early.

## Governance and Editorial Neutrality

TruthEngine should not become an unaccountable arbiter of truth.

It should be:

- Transparent about methods.
- Honest about limitations.
- Configurable by domain.
- Open to user challenge.
- Capable of showing multiple interpretations.
- Strict about provenance.

Where possible, the system should expose "why this source was weighted this way" instead of hiding behind internal authority.

## Strategic Risks

### Risk 1: Becoming Another Chatbot

If the summary becomes the main product, TruthEngine loses its differentiation.

Mitigation: make the graph, source lineage, and claim cards the primary product surface.

### Risk 2: Fake Confidence

Users may still treat a percentage as truth.

Mitigation: confidence must always be decomposed into visible factors, and the UI should emphasize evidence state rather than score alone.

### Risk 3: Source Ranking Bias

The system may over-trust official or high-authority sources.

Mitigation: separate source authority from independence, methodology, and incentive analysis.

### Risk 4: Lineage Detection Is Hard

Detecting copied claims and true origins will often be uncertain.

Mitigation: represent lineage as hypotheses with confidence, not absolute truth.

### Risk 5: Retrieval Gaps Become False Negatives

Failure to find evidence does not mean evidence does not exist.

Mitigation: distinguish "not found" from "disproven" and expose retrieval scope.

### Risk 6: Domain Complexity

Different domains require different evidence standards.

Mitigation: build domain evidence profiles for education, health, software, finance, science, policy, and consumer products.

### Risk 7: Cost and Latency

Deep evidence analysis can be expensive.

Mitigation: use progressive depth. Start with a quick evidence scan, then let users request deeper lineage and contradiction analysis.

## Domain Evidence Profiles

TruthEngine should eventually maintain domain-specific evidence profiles.

### Education

Relevant sources:

- Government education data.
- Accreditation bodies.
- Ranking bodies.
- Placement reports.
- Audited disclosures.
- Independent surveys.

Common claim traps:

- "Best school."
- "No. 1 university."
- "Highest placements."
- "100% placement."
- "World-class faculty."

### Software and SaaS

Relevant sources:

- Product documentation.
- Security audits.
- Compliance reports.
- Customer case studies.
- Benchmarks.
- Third-party reviews.
- Public incident history.

Common claim traps:

- "Most secure."
- "Industry-leading."
- "AI-powered."
- "Trusted by thousands."
- "Enterprise-grade."

### Health and Science

Relevant sources:

- Peer-reviewed studies.
- Clinical trial registries.
- Regulatory bodies.
- Meta-analyses.
- Systematic reviews.

Common claim traps:

- "Clinically proven."
- "Doctor recommended."
- "Scientifically backed."
- "Natural cure."

### Finance and Investing

Relevant sources:

- Regulatory filings.
- Audited financials.
- Market data.
- Independent analyst reports.
- Company disclosures.

Common claim traps:

- "Guaranteed returns."
- "Market leader."
- "Undervalued."
- "Recession proof."

## Data Model Sketch

Minimum durable entities:

- Investigation.
- Question.
- Claim.
- Claim version.
- Source.
- Source snapshot.
- Evidence item.
- Evidence quote or passage.
- Evidence relation.
- Source family.
- Lineage hypothesis.
- Confidence factor.
- Contradiction.
- Missing evidence marker.
- User annotation.
- Model run.
- Retrieval run.

Minimum durable relations:

- Investigation has questions.
- Question has claims.
- Claim has evidence relations.
- Evidence item belongs to source snapshot.
- Source belongs to source family.
- Source cites source.
- Source repeats source.
- Evidence supports claim.
- Evidence contradicts claim.
- Confidence factor depends on evidence relation.
- Missing evidence applies to claim.

## Technical Principles for the First Version

The first version should be narrow, honest, and operationally boring.

Recommended initial wedge:

Webpage Audit Mode for education ranking and school/university marketing claims.

Why:

- It directly addresses the hidden problem.
- It is visually understandable.
- It differentiates from chatbots.
- It creates useful evidence graphs.
- It targets one concrete domain the founder repeatedly identified: schools and universities making ranking or "best" claims.
- It gives the team clear evidence standards: rankings, accreditation, government data, audited placement disclosures, and independent methodology.

Initial scope:

- Input: URL or pasted claim.
- Output: claim list, claim classification, evidence search, source independence notes, missing evidence, confidence explanation.
- Domain: education ranking and institution marketing claims only.
- Graph: simple but real.
- Confidence: support bands and visible factors, not exact percentages.

Avoid in V1:

- Universal truth engine.
- Fully autonomous deep research.
- Complex multi-user workflows.
- Overly broad domain coverage.
- Permanent claims of correctness.
- Exact numeric confidence scores before calibration.
- Internal search clusters, graph databases, vector databases, Kafka, or enterprise policy engines before measured need.
- Autonomous agents that control workflow.

## Architecture Review Corrections

A critical architecture review found that the original platform direction was right but too broad for the first production system.

Corrections:

- Build a narrow product first, not a general evidence platform.
- Use a modular monolith with clear module boundaries before extracting services.
- Treat AI "agents" as typed AI tasks with schemas, budgets, validation, and audit records.
- Keep the workflow deterministic; models should assist steps, not decide the workflow.
- Use a durable job queue plus transactional outbox. Do not confuse jobs with domain events.
- Use PostgreSQL as the source of truth. Keep graph, search, vector, and warehouse systems as later projections or additions.
- Treat lineage as a hypothesis, not a fact.
- Use confidence bands until domain-specific calibration exists.
- Apply an explicit source snapshot policy instead of blindly archiving the web.
- Build a small golden eval set before production release.

The detailed review is recorded in `docs/TRUTHENGINE_ARCHITECTURE_REVIEW.md`.

## Suggested 3-5 Year Roadmap

### Phase 0: Founding Research and Prototype

Goals:

- Define core claim taxonomy.
- Build initial evidence graph schema.
- Prototype claim extraction.
- Prototype webpage claim audit.
- Manually evaluate 100-300 real claims.
- Build golden datasets.

Success:

- The system can show unsupported marketing claims better than a normal chatbot.
- Users understand the evidence graph.

### Phase 1: Narrow Production Product

Goals:

- Launch webpage and claim audit for selected domains.
- Build durable investigations.
- Support source snapshots.
- Add confidence explanations.
- Add basic lineage clustering.
- Add user annotations.

Success:

- Researchers, students, journalists, and founders can use the product for real audits.
- The system reliably distinguishes repeated evidence from independent evidence in common cases.

### Phase 2: Evidence Graph Platform

Goals:

- Expand domains.
- Improve lineage detection.
- Add collaboration.
- Add exports and citations.
- Add domain evidence profiles.
- Add browser extension or share sheet.
- Add APIs for evidence audits.

Success:

- TruthEngine becomes a repeatable research workflow, not just a demo.

### Phase 3: Trust Infrastructure

Goals:

- Public evidence graph references.
- Organization-level source reputation over time.
- Claim propagation timelines.
- Integrations with media, education, investment, and policy workflows.
- Third-party audit and dispute systems.

Success:

- TruthEngine becomes a trust layer other products can build on.

### Phase 4: Standard for Evidence-Based AI

Goals:

- Open evidence schemas.
- Interoperable trust artifacts.
- Institutional adoption.
- Domain-specific evaluation standards.
- Verified evidence bundles.

Success:

- Evidence inspectability becomes expected behavior in serious AI systems.

## Early Technology Recommendations

Technology should serve the product, not define it.

Reasonable starting stack:

- A mature web framework for the product API. FastAPI, Node/TypeScript, or another production-grade framework can work; the decision should follow team strength and workflow needs.
- PostgreSQL for durable entities.
- Graph-shaped relational schema before specialized graph DB.
- Object storage for controlled source artifacts under an explicit snapshot policy.
- Search API integration for retrieval.
- Browser automation for webpage extraction where needed.
- Optional embeddings behind a narrow experimental interface, not a required V1 dependency.
- LLM providers behind a small typed provider adapter.
- Structured outputs for model-generated artifacts.
- Durable job queue for retrieval and analysis. Do not use request-local background tasks for durable investigations.
- OpenTelemetry for observability.

Potential later additions:

- Dedicated graph database.
- Dedicated search cluster.
- Dedicated vector database.
- Entity resolution service.
- Explainable source quality signal service.
- Large-scale crawler.
- Domain-specific parsers.
- Claim lineage index.
- Public API and evidence bundle format.

## Non-Negotiable Engineering Standards

- Every claim must be traceable.
- Every evidence item must have source metadata.
- Every source snapshot must record retrieval time.
- Every confidence output must have an explanation.
- Every model output that affects reasoning must be stored.
- Every summary must link back to graph nodes.
- Every unsupported claim must be allowed to remain unsupported.
- Every contradiction must be visible.
- Every "not found" result must include retrieval scope.

## The Founding Product Bet

Most AI products compete on answer quality.

TruthEngine should compete on evidence quality.

The system wins when a user says:

"I do not just know the answer. I understand why the evidence supports it, where it is weak, and what I should check next."

That is the product.
