"""Concrete domain planning profiles defining rule sets for different fields."""

import re
from typing import Any

from truthengine.investigations.planning.domain import DomainProfile


class EducationProfile(DomainProfile):
    """Planning rules and constraints for the Education domain."""

    @property
    def name(self) -> str:
        """Return the Education domain name."""
        return "Education"

    def matches(self, query: str) -> bool:
        """Check if the query matches the Education domain keywords."""
        pattern = re.compile(
            r"\b(university|college|school|ranked|ranking|accreditation|placement)\b",
            re.IGNORECASE,
        )
        return bool(pattern.search(query))

    @property
    def preferred_source_categories(self) -> list[str]:
        """Preferred source categories for Education."""
        return ["Government", "Ranking organizations", "Official university website"]

    @property
    def excluded_source_categories(self) -> list[str]:
        """Excluded source categories for Education."""
        return ["Reddit", "Blogs", "Marketing pages", "AI-generated summaries"]

    @property
    def success_criteria_templates(self) -> list[str]:
        """Templates of success criteria for Education."""
        return [
            "At least two independent ranking organizations verified",
            "Ranking methodology identified",
            "Publication year verified",
        ]

    def generate_plan_details(self, query: str) -> dict[str, Any]:
        """Generate specific planning details for Education."""
        return {
            "objective": (
                "Determine the ranking or placement status of the educational institution."
            ),
            "assumptions": [
                "Rankings are published by recognizable agencies.",
                "Official university claims might be marketing-heavy.",
            ],
            "required_evidence_categories": [
                "Government rankings",
                "Independent rankings",
                "International rankings",
                "Official university claims",
            ],
            "retrieval_strategy": "Query ranking bodies and verify methodology of the ranking.",
            "limitations": ["Rankings can vary by year, discipline, and methodology."],
        }


class TechnologyProfile(DomainProfile):
    """Planning rules and constraints for the Technology domain."""

    @property
    def name(self) -> str:
        """Return the Technology domain name."""
        return "Technology"

    def matches(self, query: str) -> bool:
        """Check if the query matches the Technology domain keywords."""
        pattern = re.compile(
            r"\b(rust|c\+\+|python|java|programming|github|framework|library|"
            r"replace|benchmarks|software)\b",
            re.IGNORECASE,
        )
        return bool(pattern.search(query))

    @property
    def preferred_source_categories(self) -> list[str]:
        """Preferred source categories for Technology."""
        return [
            "Official documentation",
            "GitHub repositories",
            "Industry surveys",
            "Benchmark study publications",
        ]

    @property
    def excluded_source_categories(self) -> list[str]:
        """Excluded source categories for Technology."""
        return ["Reddit", "Forums", "Marketing blogs", "AI-generated summaries"]

    @property
    def success_criteria_templates(self) -> list[str]:
        """Templates of success criteria for Technology."""
        return [
            "At least two independent benchmark studies analyzed",
            "GitHub trend data verified",
            "Official language adoption statistics cited",
        ]

    def generate_plan_details(self, query: str) -> dict[str, Any]:
        """Generate specific planning details for Technology."""
        return {
            "objective": "Evaluate tech adoption, performance benchmarks, or replacement trends.",
            "assumptions": [
                "Performance is benchmarked.",
                "Developer adoption is indicated by public code repositories and surveys.",
            ],
            "required_evidence_categories": [
                "Official language adoption",
                "Industry surveys",
                "GitHub trends",
                "Job market data",
                "Benchmark studies",
            ],
            "retrieval_strategy": (
                "Query package registries, GitHub API, "
                "StackOverflow developer surveys, and benchmark suites."
            ),
            "limitations": ["Developer sentiment does not map 1:1 to enterprise production usage."],
        }


class GeneralProfile(DomainProfile):
    """Fallback planning rules for general queries that do not match other domains."""

    @property
    def name(self) -> str:
        """Return the General domain name."""
        return "General"

    def matches(self, query: str) -> bool:
        """Return True as this is the fallback profile matching all queries."""
        return True

    @property
    def preferred_source_categories(self) -> list[str]:
        """Preferred source categories for General queries."""
        return ["Primary news organizations", "Official reports", "Academic journals"]

    @property
    def excluded_source_categories(self) -> list[str]:
        """Excluded source categories for General queries."""
        return ["Forums", "Blogs", "Social media"]

    @property
    def success_criteria_templates(self) -> list[str]:
        """Templates of success criteria for General queries."""
        return [
            "Primary source identified",
            "Cross-reference with at least one independent authority",
        ]

    def generate_plan_details(self, query: str) -> dict[str, Any]:
        """Generate specific planning details for General queries."""
        return {
            "objective": "Investigate the general query for factual validity.",
            "assumptions": ["Information is publicly indexed by reputable sources."],
            "required_evidence_categories": [
                "Direct quotes from primary sources",
                "Expert statements",
            ],
            "retrieval_strategy": "Search general search engines, news feeds, and open registries.",
            "limitations": ["Highly specialized fields may have limited public resources."],
        }
