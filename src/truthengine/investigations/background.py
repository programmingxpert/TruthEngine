"""Background execution helpers for investigation workflows."""

import logging
from uuid import UUID

from truthengine.core.di import AppContainer
from truthengine.investigations.candidates.persistence import (
    SqlAlchemyCandidatePassageRepository,
    SqlAlchemyDocumentSegmentRepository,
)
from truthengine.investigations.graphs.persistence import SqlAlchemyEvidenceGraphRepository
from truthengine.investigations.persistence import (
    SqlAlchemyInvestigationRepository,
    SqlAlchemyTimelineEventRepository,
)
from truthengine.investigations.planning.persistence import SqlAlchemyInvestigationPlanRepository
from truthengine.investigations.service import InvestigationService
from truthengine.sources.persistence import (
    SqlAlchemySourceRepository,
    SqlAlchemySourceSnapshotRepository,
)

logger = logging.getLogger(__name__)


def run_investigation_workflow(container: AppContainer, investigation_id: UUID) -> None:
    """Execute an investigation workflow using a background-owned database session."""
    logger.info("Background workflow task scheduled for investigation: %s", investigation_id)
    try:
        logger.info("Creating session factory for background task...")
        with container.session_factory() as session:
            logger.info("Background session successfully created. Initializing service...")
            service = InvestigationService(
                repository=SqlAlchemyInvestigationRepository(session),
                timeline_repository=SqlAlchemyTimelineEventRepository(session),
                plan_repository=SqlAlchemyInvestigationPlanRepository(session),
                graph_repository=SqlAlchemyEvidenceGraphRepository(session),
                snapshot_repository=SqlAlchemySourceSnapshotRepository(session),
                segment_repository=SqlAlchemyDocumentSegmentRepository(session),
                passage_repository=SqlAlchemyCandidatePassageRepository(session),
                source_repository=SqlAlchemySourceRepository(session),
            )
            try:
                logger.info("Executing run_workflow in background...")
                service.run_workflow(
                    investigation_id=investigation_id,
                    search_provider=container.search_provider,
                    llm_provider=container.llm_provider,
                )
                logger.info("Workflow completed. Committing background session...")
                session.commit()
                logger.info("Background session successfully committed.")
            except Exception as exc:
                logger.error("Error executing workflow in background: %s", exc, exc_info=True)
                session.rollback()
                logger.info("Background session rolled back.")
    except Exception as exc:
        logger.error("Background task wrapper failed: %s", exc, exc_info=True)
