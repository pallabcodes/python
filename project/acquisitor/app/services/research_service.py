"""Research service for managing research operations."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from research import ResearchOrchestrator


class ResearchService:
    """Service for research operations."""

    def __init__(self, db: AsyncSession):
        """Initialize research service."""
        self.db = db
        self.orchestrator = ResearchOrchestrator()
        self.logger = logging.getLogger(__name__)

    async def start_research(
        self,
        company_id: int,
        sources: Optional[List[str]] = None,
        validate_config: bool = True
    ) -> Dict[str, any]:
        """Start research collection for a company.

        Args:
            company_id: Company to research
            sources: Specific sources to collect from (default: all)
            validate_config: Whether to validate source configurations

        Returns:
            Research operation results
        """
        # Validate sources if specified
        if sources:
            available_sources = await self.orchestrator.get_available_sources()
            invalid_sources = [s for s in sources if s not in available_sources]
            if invalid_sources:
                raise ValidationError(f"Invalid sources: {invalid_sources}")

        # Validate configurations if requested
        if validate_config:
            config_issues = []
            sources_to_check = sources or await self.orchestrator.get_available_sources()

            for source in sources_to_check:
                config_status = await self.orchestrator.validate_source_config(source)
                if not config_status.get("configured", False):
                    config_issues.append(source)

            if config_issues:
                self.logger.warning(f"Configuration issues for sources: {config_issues}")
                # Continue but log warning

        # Start collection
        self.logger.info(f"Starting research for company {company_id}")
        results = await self.orchestrator.collect_company_research(company_id, sources)

        return {
            "company_id": company_id,
            "status": "completed",
            "sources_collected": results,
            "total_items": sum(results.values()),
            "timestamp": "now",  # TODO: Add proper timestamp
        }

    async def get_research_status(self, company_id: int) -> Dict[str, any]:
        """Get research status for a company."""
        return await self.orchestrator.get_collection_status(company_id)

    async def get_available_sources(self) -> List[str]:
        """Get list of available research sources."""
        return await self.orchestrator.get_available_sources()

    async def validate_source_configs(self) -> Dict[str, Dict[str, bool]]:
        """Validate configurations for all research sources."""
        sources = await self.orchestrator.get_available_sources()
        configs = {}

        for source in sources:
            configs[source] = await self.orchestrator.validate_source_config(source)

        return configs

    async def get_research_summary(self, company_id: int) -> Dict[str, any]:
        """Get research summary for a company."""
        status = await self.get_research_status(company_id)

        if "error" in status:
            return status

        # Add additional summary information
        summary = {
            **status,
            "research_coverage": self._calculate_coverage(status),
            "data_quality_score": self._estimate_data_quality(status),
            "recommendations": self._generate_research_recommendations(status),
        }

        return summary

    def _calculate_coverage(self, status: Dict[str, any]) -> float:
        """Calculate research coverage score (0-1)."""
        sources_completed = len(status.get("research_sources", []))
        total_sources = 4  # reddit, github, medium, twitter

        if sources_completed == 0:
            return 0.0

        # Weight by data volume and quality
        base_coverage = min(sources_completed / total_sources, 1.0)

        # Boost for having pain points found
        if status.get("pain_points_count", 0) > 0:
            base_coverage = min(base_coverage + 0.1, 1.0)

        return round(base_coverage, 2)

    def _estimate_data_quality(self, status: Dict[str, any]) -> float:
        """Estimate data quality score (0-1)."""
        pain_points = status.get("pain_points_count", 0)

        # Simple heuristic: more pain points = better research
        if pain_points == 0:
            return 0.3  # Baseline for completed research
        elif pain_points < 5:
            return 0.6
        elif pain_points < 15:
            return 0.8
        else:
            return 0.9

    def _generate_research_recommendations(self, status: Dict[str, any]) -> List[str]:
        """Generate research recommendations."""
        recommendations = []

        if status.get("research_status") == "not_started":
            recommendations.append("Start initial research collection")
            return recommendations

        sources_used = set(status.get("research_sources", []))
        available_sources = {"reddit", "github", "medium", "twitter"}
        unused_sources = available_sources - sources_used

        if unused_sources:
            recommendations.append(f"Consider collecting from: {', '.join(unused_sources)}")

        pain_points = status.get("pain_points_count", 0)
        if pain_points == 0:
            recommendations.append("No pain points found - consider broader search terms")
        elif pain_points < 5:
            recommendations.append("Limited pain points found - research may be incomplete")

        if status.get("last_researched"):
            # TODO: Check if research is stale (>30 days)
            pass

        return recommendations
