"""Text segmenter and ranking selector logic for candidate passages."""

import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from truthengine.investigations.candidates.domain import (
    CandidatePassage,
    DocumentSegment,
    SelectionPolicy,
)
from truthengine.investigations.planning.domain import DomainProfile

STOP_WORDS = {
    "is",
    "a",
    "the",
    "of",
    "and",
    "in",
    "for",
    "to",
    "on",
    "with",
    "at",
    "by",
    "from",
    "up",
    "about",
    "into",
    "over",
    "after",
    "it",
    "that",
    "this",
    "are",
    "was",
    "were",
    "or",
    "as",
    "an",
    "be",
    "but",
}

TECH_KEYWORDS = {
    "code",
    "software",
    "hardware",
    "system",
    "performance",
    "benchmark",
    "api",
    "database",
    "algorithm",
    "framework",
    "developer",
}
EDU_KEYWORDS = {
    "student",
    "teacher",
    "school",
    "curriculum",
    "learning",
    "degree",
    "academic",
    "education",
    "university",
    "college",
}


def segment_snapshot(
    snapshot_id: UUID, extracted_text: str, default_heading: str | None = None
) -> list[DocumentSegment]:
    """Parse raw text into paragraph segments, maintaining heading hierarchy."""
    segments = []
    lines = [line.strip() for line in extracted_text.split("\n") if line.strip()]

    current_heading = default_heading
    current_heading_level = 1 if default_heading else None
    paragraph_order = 0
    segment_order = 0
    running_index = 0

    for line in lines:
        start_idx = extracted_text.find(line, running_index)
        if start_idx == -1:
            start_idx = running_index
        end_idx = start_idx + len(line)
        running_index = end_idx

        # Heuristic for heading lines
        is_heading = len(line) < 80 and not line.endswith((".", "!", "?", ":", '"', "'"))

        if is_heading:
            current_heading = line
            current_heading_level = 2 if line.isupper() else 3
        else:
            paragraph_order += 1
            segment_order += 1
            token_est = max(1, len(line) // 4)

            segments.append(
                DocumentSegment(
                    id=uuid4(),
                    snapshot_id=snapshot_id,
                    order=segment_order,
                    heading=current_heading,
                    heading_level=current_heading_level,
                    paragraph_order=paragraph_order,
                    parent_section=current_heading,
                    content=line,
                    character_range_start=start_idx,
                    character_range_end=end_idx,
                    token_estimate=token_est,
                )
            )

    return segments


def rank_and_select_passages(
    investigation_id: UUID,
    query: str,
    segments: list[DocumentSegment],
    snapshot_version: int,
    policy: SelectionPolicy,
    profile: DomainProfile,
) -> list[CandidatePassage]:
    """Rank segments using lexical overlap and SelectionPolicy, producing candidate passages."""
    query_clean = re.sub(r"[^\w\s]", "", query.lower())
    query_terms = [term for term in query_clean.split() if term not in STOP_WORDS and len(term) > 1]

    passages = []

    for segment in segments:
        matched_query_terms = []
        score = 0.0
        content_lower = segment.content.lower()
        heading_lower = (segment.heading or "").lower()

        # 1. Lexical content overlap
        for term in query_terms:
            if term in content_lower:
                matched_query_terms.append(term)
                score += 1.0

        # 2. Heading overlap bonus
        heading_match = segment.heading
        if segment.heading:
            matched_header_terms = []
            for term in query_terms:
                if term in heading_lower:
                    matched_header_terms.append(term)
                    score += 2.0

        # 3. Domain profile adjustments
        matched_domain_rules = []
        domain_name = profile.name.lower()

        if "technology" in domain_name or "programming" in domain_name:
            matches = [kw for kw in TECH_KEYWORDS if kw in content_lower]
            if matches:
                score += 1.5
                matched_domain_rules.append(f"technology_profile_match: {list(set(matches))}")
        elif "education" in domain_name or "academic" in domain_name:
            matches = [kw for kw in EDU_KEYWORDS if kw in content_lower]
            if matches:
                score += 1.5
                matched_domain_rules.append(f"education_profile_match: {list(set(matches))}")

        if score >= policy.min_lexical_threshold:
            explanation = {
                "matched_query_terms": list(set(matched_query_terms)),
                "matched_heading": heading_match,
                "matched_domain_rules": matched_domain_rules,
                "lexical_score": score,
                "selection_algorithm_version": "1.0.0",
            }

            passages.append(
                CandidatePassage(
                    id=uuid4(),
                    investigation_id=investigation_id,
                    segment_id=segment.id,
                    snapshot_version=snapshot_version,
                    algorithm_version="1.0.0",
                    paragraph_order=segment.paragraph_order,
                    selection_explanation=explanation,
                    selected_at=datetime.now(UTC),
                )
            )

    # Sort in descending order of lexical score
    passages.sort(key=lambda p: float(p.selection_explanation["lexical_score"]), reverse=True)

    # Apply capacity limit
    return passages[: policy.max_returned_passages]
