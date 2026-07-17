"""Orchestration of real pipeline stages and workflow state transitions."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from truthengine.investigations.candidates.domain import SelectionPolicy
from truthengine.investigations.domain import Investigation, InvestigationStatus, TimelineEvent
from truthengine.investigations.graphs.domain import (
    Claim,
    ClaimStatus,
    ClaimType,
    EvidenceGraph,
    EvidenceItem,
    EvidenceRelation,
    RelationType,
)
from truthengine.investigations.repository import InvestigationRepository, TimelineEventRepository

if TYPE_CHECKING:
    from truthengine.investigations.candidates.repository import (
        CandidatePassageRepository,
        DocumentSegmentRepository,
    )
    from truthengine.investigations.graphs.repository import EvidenceGraphRepository
    from truthengine.investigations.planning.repository import InvestigationPlanRepository
    from truthengine.llm.provider import LLMProvider
    from truthengine.search.provider import SearchProvider
    from truthengine.sources.repository import SourceRepository, SourceSnapshotRepository

logger = logging.getLogger(__name__)

_ALGORITHM_VERSION = "2.0.0"


class InvestigationWorkflowOrchestrator:
    """State Machine Orchestrator that executes the full investigation pipeline."""

    def __init__(  # noqa: PLR0913
        self,
        investigation_repo: InvestigationRepository,
        timeline_repo: TimelineEventRepository,
        plan_repo: "InvestigationPlanRepository | None" = None,
        graph_repo: "EvidenceGraphRepository | None" = None,
        snapshot_repo: "SourceSnapshotRepository | None" = None,
        segment_repo: "DocumentSegmentRepository | None" = None,
        passage_repo: "CandidatePassageRepository | None" = None,
        source_repo: "SourceRepository | None" = None,
        search_provider: "SearchProvider | None" = None,
        llm_provider: "LLMProvider | None" = None,
    ) -> None:
        """Initialize the orchestrator with required repositories and optional providers."""
        self._investigation_repo = investigation_repo
        self._timeline_repo = timeline_repo
        self._plan_repo = plan_repo
        self._graph_repo = graph_repo
        self._snapshot_repo = snapshot_repo
        self._segment_repo = segment_repo
        self._passage_repo = passage_repo
        self._source_repo = source_repo
        self._search_provider = search_provider
        self._llm_provider = llm_provider

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, investigation_id: UUID) -> Investigation:
        """Execute or resume the investigation workflow synchronously."""
        investigation = self._investigation_repo.get_by_id(investigation_id)
        if investigation is None:
            msg = f"Investigation {investigation_id} not found."
            raise ValueError(msg)

        if investigation.status == InvestigationStatus.COMPLETED:
            logger.info("Investigation %s is already completed.", investigation_id)
            return investigation

        status: InvestigationStatus = investigation.status

        if status in (
            InvestigationStatus.CREATED,
            InvestigationStatus.QUEUED,
            InvestigationStatus.FAILED,
        ):
            if status in (InvestigationStatus.CREATED, InvestigationStatus.QUEUED):
                self._add_event(
                    investigation_id,
                    "WORKFLOW_STARTED",
                    "Investigation workflow execution started.",
                )
            investigation = self._transition(investigation, InvestigationStatus.COLLECTING_SOURCES)
            status = investigation.status

        try:
            if status == InvestigationStatus.COLLECTING_SOURCES:
                current_investigation = investigation
                self._run_stage(
                    current_investigation,
                    "COLLECTING_SOURCES",
                    lambda: self._collect_sources(current_investigation),
                )
                investigation = self._transition(investigation, InvestigationStatus.ANALYZING)
                status = investigation.status

            if status == InvestigationStatus.ANALYZING:
                current_investigation = investigation
                self._run_stage(
                    current_investigation,
                    "ANALYZING",
                    lambda: self._analyze(current_investigation),
                )
                investigation = self._transition(
                    investigation, InvestigationStatus.GENERATING_REPORT
                )
                status = investigation.status

            if status == InvestigationStatus.GENERATING_REPORT:
                current_investigation = investigation
                self._run_stage(
                    current_investigation,
                    "GENERATING_REPORT",
                    lambda: self._generate_report(current_investigation),
                )
                investigation = self._transition(investigation, InvestigationStatus.COMPLETED)
                self._add_event(
                    investigation_id,
                    "WORKFLOW_COMPLETED",
                    "Investigation workflow execution completed successfully.",
                )
                status = investigation.status  # noqa: F841

        except Exception as exc:
            logger.exception("Investigation %s failed: %s", investigation_id, exc)
            investigation = self._transition(investigation, InvestigationStatus.FAILED)
            self._add_event(
                investigation_id,
                "WORKFLOW_FAILED",
                f"Workflow execution failed: {exc}",
                {"error": str(exc), "stage": status.value},
            )
            session = getattr(self._investigation_repo, "_session", None)
            if session is not None:
                session.commit()
            raise

        return investigation

    # ------------------------------------------------------------------
    # Stage 1: COLLECTING_SOURCES
    # ------------------------------------------------------------------

    def _collect_sources(self, investigation: Investigation) -> None:
        """Search the web, ingest URLs, segment docs, select candidate passages."""
        from truthengine.investigations.candidates.selector import (
            rank_and_select_passages,
            segment_snapshot,
        )
        from truthengine.investigations.planning.planner import InvestigationPlanner
        from truthengine.investigations.planning.profiles import (
            EducationProfile,
            GeneralProfile,
            TechnologyProfile,
        )
        from truthengine.sources.domain import Source, SourceCategory, SourceSnapshot
        from truthengine.sources.pipeline import compute_fingerprint, fetch_url
        from truthengine.sources.security import normalize_url

        inv_id = investigation.id
        query = investigation.query

        # 1. Generate investigation plan
        plan = None
        if self._plan_repo is not None:
            plan = self._plan_repo.get_by_investigation_id(inv_id)
            if plan is None:
                planner = InvestigationPlanner()
                plan = planner.plan(investigation_id=inv_id, query=query)
                self._plan_repo.add(plan)
                self._add_event(
                    inv_id,
                    "PLAN_GENERATED",
                    f"Investigation plan generated. Domain: {plan.detected_domain}",
                    {"domain": plan.detected_domain, "planner_version": plan.planner_version},
                )

        # 2. Determine domain profile for candidate selection
        domain_lower = (plan.detected_domain if plan else "").lower()
        if "technology" in domain_lower or "programming" in domain_lower:
            profile: Any = TechnologyProfile()
        elif "education" in domain_lower:
            profile = EducationProfile()
        else:
            profile = GeneralProfile()

        # 3. Search for URLs
        search_results = []
        if self._search_provider is not None:
            try:
                search_results = self._search_provider.search(query, max_results=6)
                self._add_event(
                    inv_id,
                    "SEARCH_COMPLETED",
                    f"Web search completed. Found {len(search_results)} candidate URLs.",
                    {"count": len(search_results), "urls": [r.url for r in search_results]},
                )
            except Exception as exc:
                logger.warning("Search failed for investigation %s: %s", inv_id, exc)
                self._add_event(
                    inv_id,
                    "SEARCH_FAILED",
                    f"Web search failed: {exc}",
                    {"error": str(exc)},
                )

        # 4. Ingest each URL
        ingested_count = 0
        for result in search_results:
            try:
                normalized_url = normalize_url(result.url)
                fetch_result = fetch_url(normalized_url)

                if not fetch_result.success:
                    logger.info("Fetch failed for %s: %s", result.url, fetch_result.error_type)
                    continue

                if self._source_repo is None or self._snapshot_repo is None:
                    continue

                from urllib.parse import urlparse

                parsed_url = urlparse(normalized_url)
                domain = parsed_url.hostname or parsed_url.netloc or "unknown"

                # Get or create Source record
                source = self._source_repo.get_by_domain(domain)
                if source is None:
                    from uuid import uuid4 as _uuid4

                    source = Source(
                        id=_uuid4(),
                        domain=domain,
                        source_category=SourceCategory.GENERAL,
                        created_at=datetime.now(UTC),
                    )
                    self._source_repo.add(source)

                # Fingerprint and dedup
                content_hash = compute_fingerprint(fetch_result.extracted_text)
                existing = self._snapshot_repo.get_by_hash(source.id, content_hash)
                if existing is not None:
                    logger.info("Duplicate snapshot for %s; reusing.", result.url)
                    ingested_count += 1
                    self._add_event(
                        inv_id,
                        "SOURCE_INGESTED",
                        f"Reused snapshot: {existing.title or domain}",
                        {
                            "url": existing.url,
                            "domain": domain,
                            "snapshot_id": str(existing.id),
                            "content_length": existing.content_length,
                            "reused_snapshot": True,
                        },
                    )
                    continue
                latest_ver = self._snapshot_repo.get_latest_version(source.id)
                snapshot = SourceSnapshot(
                    id=uuid4(),
                    source_id=source.id,
                    url=normalized_url,
                    fetched_at=fetch_result.fetched_at,
                    content_hash=content_hash,
                    content_type=fetch_result.content_type,
                    http_status=fetch_result.http_status,
                    title=fetch_result.title or result.title,
                    extracted_text=fetch_result.extracted_text,
                    original_html=fetch_result.original_html,
                    content_length=fetch_result.content_length,
                    fetch_duration_ms=fetch_result.fetch_duration_ms,
                    etag=fetch_result.etag,
                    last_modified=fetch_result.last_modified,
                    encoding=fetch_result.encoding,
                    metadata={"crawler_user_agent": "TruthEngineBot/1.0.0"},
                    snapshot_version=latest_ver + 1,
                )
                self._snapshot_repo.add(snapshot)
                ingested_count += 1
                self._add_event(
                    inv_id,
                    "SOURCE_INGESTED",
                    f"Ingested: {fetch_result.title or domain}",
                    {
                        "url": normalized_url,
                        "domain": domain,
                        "snapshot_id": str(snapshot.id),
                        "content_length": fetch_result.content_length,
                    },
                )

            except Exception as exc:
                logger.warning("Failed to ingest %s: %s", result.url, exc, exc_info=True)

        self._add_event(
            inv_id,
            "INGESTION_COMPLETED",
            f"Source ingestion complete. {ingested_count} sources ingested.",
            {"ingested_count": ingested_count},
        )

        # 5. Segment + select candidate passages from all available snapshots
        if self._snapshot_repo is None or self._segment_repo is None or self._passage_repo is None:
            return

        all_snapshots = self._get_investigation_snapshots(inv_id)
        if not all_snapshots:
            self._add_event(
                inv_id,
                "PASSAGES_SKIPPED",
                "No snapshots available to segment.",
            )
            return

        policy = SelectionPolicy(max_returned_passages=12)
        selected: list[Any] = []

        for snapshot in all_snapshots:
            segs = self._segment_repo.get_by_snapshot_id(snapshot.id)
            if not segs:
                segs = segment_snapshot(
                    snapshot.id,
                    snapshot.extracted_text,
                    default_heading=snapshot.title,
                )
                self._segment_repo.add_all(segs)

            passages = rank_and_select_passages(
                investigation_id=inv_id,
                query=query,
                segments=segs,
                snapshot_version=snapshot.snapshot_version,
                policy=policy,
                profile=profile,
            )
            selected.extend(passages)

        selected.sort(
            key=lambda p: float(p.selection_explanation["lexical_score"]),
            reverse=True,
        )
        final = selected[: policy.max_returned_passages]
        self._passage_repo.add_all(final)

        self._add_event(
            inv_id,
            "PASSAGES_SELECTED",
            f"Selected {len(final)} candidate passages from {len(all_snapshots)} sources.",
            {
                "passage_count": len(final),
                "snapshot_count": len(all_snapshots),
                "algorithm_version": _ALGORITHM_VERSION,
            },
        )

    # ------------------------------------------------------------------
    # Stage 2: ANALYZING
    # ------------------------------------------------------------------

    def _analyze(self, investigation: Investigation) -> None:
        """Extract claims from candidate passages and map evidence relations via DeepSeek."""
        from truthengine.llm.prompts import (
            CLAIM_EXTRACTION_SYSTEM,
            CLAIM_EXTRACTION_USER,
            CLAIM_EXTRACTION_VERSION,
            EVIDENCE_MAPPING_SYSTEM,
            EVIDENCE_MAPPING_USER,
            EVIDENCE_MAPPING_VERSION,
        )

        inv_id = investigation.id

        if self._passage_repo is None or self._segment_repo is None:
            self._add_event(inv_id, "ANALYSIS_SKIPPED", "Repositories not available.")
            return

        passages = self._passage_repo.get_by_investigation_id(inv_id)
        if not passages:
            self._add_event(inv_id, "ANALYSIS_SKIPPED", "No candidate passages to analyse.")
            return

        llm_provider = self._llm_provider
        if llm_provider is None:
            message = (
                "DeepSeek API key is required for claim extraction and evidence matching. "
                "Set TRUTHENGINE_DEEPSEEK_API_KEY and rerun the investigation."
            )
            self._add_event(inv_id, "ANALYSIS_BLOCKED", message)
            raise RuntimeError(message)

        snapshot_urls: dict[UUID, str] = {}
        if self._snapshot_repo is not None:
            for snap in self._snapshot_repo.get_all():
                snapshot_urls[snap.id] = snap.url

        graph_id = uuid4()
        all_claims: list[Claim] = []
        all_evidence: list[EvidenceItem] = []
        all_relations: list[EvidenceRelation] = []

        for passage in passages:
            segment = self._segment_repo.get_by_id(passage.segment_id)
            if segment is None:
                continue

            passage_text = segment.content
            heading = segment.heading or ""
            try:
                user_prompt = CLAIM_EXTRACTION_USER.format(
                    query=investigation.query,
                    heading=heading,
                    passage_text=passage_text[:2000],
                )
                result = llm_provider.complete_json(
                    system=CLAIM_EXTRACTION_SYSTEM,
                    user=user_prompt,
                )
                raw_claims = result.get("claims", [])
            except Exception as exc:
                logger.warning("Claim extraction failed for segment %s: %s", segment.id, exc)
                raw_claims = []

            for claim_data in raw_claims:
                claim_text = str(claim_data.get("text", "")).strip()
                if not claim_text:
                    continue
                raw_type = str(claim_data.get("claim_type", "SUPPORTING")).upper()
                claim_type = ClaimType.PRIMARY if raw_type == "PRIMARY" else ClaimType.SUPPORTING
                claim = Claim(
                    id=uuid4(),
                    graph_id=graph_id,
                    text=claim_text,
                    claim_type=claim_type,
                    status=ClaimStatus.UNVERIFIED,
                )
                all_claims.append(claim)

                snap_url = snapshot_urls.get(segment.snapshot_id, "unknown")
                evidence_item = EvidenceItem(
                    id=uuid4(),
                    graph_id=graph_id,
                    source_snapshot_id=segment.snapshot_id,
                    quote=passage_text[:500],
                    location=snap_url,
                    extracted_at=datetime.now(UTC),
                )
                all_evidence.append(evidence_item)
                self._add_event(
                    inv_id,
                    "CLAIM_EXTRACTED",
                    f"Extracted claim from {snap_url}: {claim_text}",
                    {
                        "claim_id": str(claim.id),
                        "claim_text": claim_text,
                        "claim_type": claim_type.value,
                        "segment_id": str(segment.id),
                        "snapshot_id": str(segment.snapshot_id),
                        "source_url": snap_url,
                        "evidence_quote": evidence_item.quote,
                    },
                )

                try:
                    map_user = EVIDENCE_MAPPING_USER.format(
                        claim_text=claim_text,
                        passage_text=passage_text[:2000],
                    )
                    map_result = llm_provider.complete_json(
                        system=EVIDENCE_MAPPING_SYSTEM,
                        user=map_user,
                    )
                    raw_rel = str(map_result.get("relation_type", "CONTEXT")).upper()
                    relation_type = self._parse_relation_type(raw_rel)
                except Exception as exc:
                    logger.warning("Evidence mapping failed: %s", exc)
                    relation_type = RelationType.CONTEXT

                relation = EvidenceRelation(
                    id=uuid4(),
                    graph_id=graph_id,
                    claim_id=claim.id,
                    evidence_item_id=evidence_item.id,
                    relation_type=relation_type,
                )
                all_relations.append(relation)
                self._add_event(
                    inv_id,
                    "EVIDENCE_MAPPED",
                    f"Mapped evidence as {relation_type.value} for claim: {claim_text}",
                    {
                        "claim_id": str(claim.id),
                        "evidence_item_id": str(evidence_item.id),
                        "relation_type": relation_type.value,
                        "source_url": snap_url,
                    },
                )

        if self._graph_repo is not None:
            graph = EvidenceGraph(
                id=graph_id,
                investigation_id=inv_id,
                version=1,
                created_at=datetime.now(UTC),
                claims=all_claims,
                evidence_items=all_evidence,
                relations=all_relations,
            )
            self._graph_repo.add(graph)

        supporting = sum(1 for r in all_relations if r.relation_type == RelationType.SUPPORTS)
        contradicting = sum(1 for r in all_relations if r.relation_type == RelationType.CONTRADICTS)
        self._add_event(
            inv_id,
            "ANALYSIS_COMPLETED",
            (
                f"Analysis complete. {len(all_claims)} claims extracted, "
                f"{len(all_evidence)} evidence items mapped. "
                f"Supporting: {supporting}, Contradicting: {contradicting}."
            ),
            {
                "claims_count": len(all_claims),
                "evidence_count": len(all_evidence),
                "relations_count": len(all_relations),
                "supporting_count": supporting,
                "contradicting_count": contradicting,
                "claim_extraction_version": CLAIM_EXTRACTION_VERSION,
                "evidence_mapping_version": EVIDENCE_MAPPING_VERSION,
            },
        )

    # ------------------------------------------------------------------
    # Stage 3: GENERATING_REPORT
    # ------------------------------------------------------------------

    def _generate_report(self, investigation: Investigation) -> None:
        """Compute an algorithmic confidence verdict from persisted graph statistics."""
        verdict_version = "algorithmic-confidence-1.0.0"
        inv_id = investigation.id

        graph = (
            self._graph_repo.get_latest_by_investigation_id(inv_id) if self._graph_repo else None
        )
        passage_count = (
            len(self._passage_repo.get_by_investigation_id(inv_id))
            if self._passage_repo is not None
            else 0
        )
        sources_count = len(self._snapshot_repo.get_all()) if self._snapshot_repo is not None else 0

        if graph is None:
            supporting = contradicting = total_claims = total_evidence = 0
            supporting_excerpts = "None available."
            contradicting_excerpts = "None available."
        else:
            supporting = sum(1 for r in graph.relations if r.relation_type == RelationType.SUPPORTS)
            contradicting = sum(
                1 for r in graph.relations if r.relation_type == RelationType.CONTRADICTS
            )
            total_claims = len(graph.claims)
            total_evidence = len(graph.evidence_items)
            supporting_items = [
                ev
                for ev in graph.evidence_items
                if any(
                    r.evidence_item_id == ev.id and r.relation_type == RelationType.SUPPORTS
                    for r in graph.relations
                )
            ]
            contradicting_items = [
                ev
                for ev in graph.evidence_items
                if any(
                    r.evidence_item_id == ev.id and r.relation_type == RelationType.CONTRADICTS
                    for r in graph.relations
                )
            ]
            supporting_excerpts = (
                "\n".join(f"- {ev.quote[:200]}" for ev in supporting_items[:3]) or "None."
            )
            contradicting_excerpts = (
                "\n".join(f"- {ev.quote[:200]}" for ev in contradicting_items[:3]) or "None."
            )

        verdict = self._algorithmic_verdict(
            query=investigation.query,
            supporting=supporting,
            contradicting=contradicting,
            total_passages=passage_count,
            total_claims=total_claims,
            total_evidence=total_evidence,
            sources_count=sources_count,
            supporting_excerpts=supporting_excerpts,
            contradicting_excerpts=contradicting_excerpts,
        )
        verdict["verdict_version"] = verdict_version
        verdict["generated_at"] = datetime.now(UTC).isoformat()
        verdict["confidence_factors"] = {
            "source_count": sources_count,
            "coverage_passages": passage_count,
            "supporting_relations": supporting,
            "contradicting_relations": contradicting,
            "claim_count": total_claims,
            "evidence_count": total_evidence,
        }

        self._add_event(
            inv_id,
            "VERDICT_GENERATED",
            f"Verdict: {verdict.get('verdict', 'UNKNOWN')} "
            f"(confidence: {verdict.get('confidence', 0)}%)",
            verdict,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _algorithmic_verdict(
        *,
        query: str,
        supporting: int,
        contradicting: int,
        total_passages: int,
        total_claims: int,
        total_evidence: int,
        sources_count: int,
        supporting_excerpts: str,
        contradicting_excerpts: str,
    ) -> dict[str, Any]:
        """Produce a deterministic rule-based verdict when LLM is unavailable."""
        total = supporting + contradicting
        if total == 0:
            verdict_label = "INSUFFICIENT_EVIDENCE"
            confidence = 10
            explanation = (
                "Not enough evidence was collected to evaluate this claim. "
                f"The investigation found {sources_count} source(s) and {total_passages} "
                "relevant passages, but could not extract verifiable claims. "
                "Try again with a more specific query."
            )
        elif supporting > contradicting * 2:
            verdict_label = "TRUE"
            confidence = min(90, 50 + int((supporting / total) * 40))
            explanation = (
                f"The available evidence predominantly supports this claim. "
                f"{supporting} of {total} evidence items provide supporting information."
            )
        elif contradicting > supporting * 2:
            verdict_label = "FALSE"
            confidence = min(90, 50 + int((contradicting / total) * 40))
            explanation = (
                f"The available evidence predominantly contradicts this claim. "
                f"{contradicting} of {total} evidence items provide contradicting information."
            )
        else:
            verdict_label = "MIXED"
            confidence = 40
            explanation = (
                f"The evidence is split. {supporting} items support and "
                f"{contradicting} items contradict the claim. "
                "More research may be needed to reach a definitive conclusion."
            )

        return {
            "verdict": verdict_label,
            "confidence": confidence,
            "explanation": explanation,
            "key_findings": [
                f"Analysed {total_passages} relevant passages from {sources_count} sources.",
                f"Extracted {total_claims} claims with {total_evidence} evidence mappings.",
                f"Supporting evidence: {supporting} items.",
                f"Contradicting evidence: {contradicting} items.",
            ],
            "algorithm": "deterministic_rule_based",
        }

    @staticmethod
    def _parse_relation_type(raw: str) -> RelationType:
        """Parse a relation type string, defaulting to CONTEXT on unknown values."""
        mapping = {
            "SUPPORTS": RelationType.SUPPORTS,
            "CONTRADICTS": RelationType.CONTRADICTS,
            "CONTEXT": RelationType.CONTEXT,
            "UNRELATED": RelationType.UNRELATED,
        }
        return mapping.get(raw, RelationType.CONTEXT)

    def _transition(
        self, investigation: Investigation, target_status: InvestigationStatus
    ) -> Investigation:
        """Transition the investigation to a new status and record a timeline event."""
        old_status = investigation.status
        updated = investigation.update_status(target_status)
        self._investigation_repo.update(updated)
        self._add_event(
            investigation.id,
            "STATUS_CHANGED",
            f"Transitioned from {old_status} to {target_status}.",
            {"old_status": old_status.value, "new_status": target_status.value},
        )
        logger.info(
            "Investigation status transition",
            extra={
                "investigation_id": str(investigation.id),
                "old_status": old_status.value,
                "new_status": target_status.value,
            },
        )
        return updated

    def _add_event(
        self,
        investigation_id: UUID,
        event_type: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create and persist an immutable timeline event."""
        event = TimelineEvent(
            id=uuid4(),
            investigation_id=investigation_id,
            event_type=event_type,
            message=message,
            created_at=datetime.now(UTC),
            metadata=metadata or {},
        )
        self._timeline_repo.add(event)
        self._commit_checkpoint()

    def _run_stage(
        self, investigation: Investigation, stage_name: str, stage_func: Callable[[], None]
    ) -> None:
        """Execute a stage wrapped in a database savepoint nested transaction."""
        logger.info("Starting stage %s for investigation %s", stage_name, investigation.id)
        stage_func()

    def _commit_checkpoint(self) -> None:
        """Commit current workflow progress so polling clients can observe it live."""
        session = getattr(self._investigation_repo, "_session", None)
        if session is not None:
            session.commit()

    def _get_investigation_snapshots(self, investigation_id: UUID) -> list[Any]:
        """Return snapshots explicitly ingested for the current investigation."""
        if self._snapshot_repo is None:
            return []

        snapshot_ids: list[UUID] = []
        for event in self._timeline_repo.get_by_investigation_id(investigation_id):
            if event.event_type != "SOURCE_INGESTED":
                continue
            raw_snapshot_id = event.metadata.get("snapshot_id")
            if raw_snapshot_id is None:
                continue
            try:
                snapshot_id = UUID(str(raw_snapshot_id))
            except ValueError:
                continue
            if snapshot_id not in snapshot_ids:
                snapshot_ids.append(snapshot_id)

        snapshots = []
        for snapshot_id in snapshot_ids:
            snapshot = self._snapshot_repo.get_by_id(snapshot_id)
            if snapshot is not None:
                snapshots.append(snapshot)
        return snapshots
