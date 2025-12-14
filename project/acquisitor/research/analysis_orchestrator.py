"""Analysis orchestrator for coordinating research data analysis."""

import logging
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AnalysisError
from app.models.pain_point import PainPoint
from .processors import PainPointAnalyzer


class AnalysisOrchestrator:
    """Orchestrates analysis of research data."""

    def __init__(self, db: AsyncSession):
        """Initialize analysis orchestrator."""
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.pain_point_analyzer = PainPointAnalyzer(db)

    async def analyze_company_data(self, company_id: int) -> Dict[str, any]:
        """Run complete analysis pipeline for a company."""
        try:
            self.logger.info(f"Starting analysis for company {company_id}")

            # Extract pain points
            pain_points = await self.pain_point_analyzer.analyze_company_pain_points(company_id)

            # Update company statistics
            await self._update_company_statistics(company_id, pain_points)

            # Generate analysis summary
            summary = await self._generate_analysis_summary(company_id, pain_points)

            self.logger.info(f"Analysis completed for company {company_id}: {len(pain_points)} pain points found")

            return {
                "company_id": company_id,
                "status": "completed",
                "pain_points_found": len(pain_points),
                "summary": summary,
                "analysis_timestamp": "now",  # TODO: Add proper timestamp
            }

        except Exception as e:
            self.logger.error(f"Analysis failed for company {company_id}: {e}")
            raise AnalysisError("analysis", f"Analysis orchestration failed: {e}")

    async def _update_company_statistics(self, company_id: int, pain_points: List[PainPoint]):
        """Update company statistics based on analysis results."""
        from sqlalchemy import select, update

        # Get company
        query = select("Company").where("Company".id == company_id)
        result = await self.db.execute(query)
        company = result.scalar_one_or_none()

        if company:
            # Update pain points count
            company.pain_points_count = len(pain_points)

            # Calculate average severity
            if pain_points:
                avg_severity = sum(pp.severity for pp in pain_points) / len(pain_points)
                # Could store this in a new field if needed

            await self.db.commit()

    async def _generate_analysis_summary(self, company_id: int, pain_points: List[PainPoint]) -> Dict[str, any]:
        """Generate analysis summary."""
        summary = {
            "total_pain_points": len(pain_points),
            "severity_distribution": {},
            "category_distribution": {},
            "top_pain_points": [],
            "insights": [],
        }

        if not pain_points:
            summary["insights"].append("No significant pain points identified in the research data.")
            return summary

        # Severity distribution
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for pp in pain_points:
            impact = pp.impact
            if impact in severity_counts:
                severity_counts[impact] += 1
        summary["severity_distribution"] = severity_counts

        # Category distribution
        category_counts = {}
        for pp in pain_points:
            category = pp.category
            category_counts[category] = category_counts.get(category, 0) + 1
        summary["category_distribution"] = category_counts

        # Top pain points (by severity)
        top_pain_points = sorted(pain_points, key=lambda x: x.severity, reverse=True)[:5]
        summary["top_pain_points"] = [
            {
                "id": pp.id,
                "title": pp.title,
                "severity": pp.severity,
                "impact": pp.impact,
                "category": pp.category,
            }
            for pp in top_pain_points
        ]

        # Generate insights
        insights = []

        # Severity insights
        critical_count = severity_counts.get("critical", 0)
        if critical_count > 0:
            insights.append(f"Found {critical_count} critical pain points that need immediate attention.")

        high_count = severity_counts.get("high", 0)
        if high_count > 3:
            insights.append(f"Multiple high-impact issues ({high_count}) suggest significant user frustration.")

        # Category insights
        if category_counts:
            top_category = max(category_counts.items(), key=lambda x: x[1])
            insights.append(f"Most common issue category: {top_category[0]} ({top_category[1]} instances)")

        # Overall assessment
        avg_severity = sum(pp.severity for pp in pain_points) / len(pain_points)
        if avg_severity > 7.0:
            insights.append("High average pain point severity indicates major product issues.")
        elif avg_severity > 5.0:
            insights.append("Moderate pain point severity suggests room for significant improvements.")
        else:
            insights.append("Lower pain point severity indicates generally positive user experience.")

        summary["insights"] = insights
        return summary

    async def get_analysis_status(self, company_id: int) -> Dict[str, any]:
        """Get analysis status for a company."""
        from sqlalchemy import select

        # Get pain points count
        query = select(PainPoint).where(PainPoint.company_id == company_id)
        result = await self.db.execute(query)
        pain_points = result.scalars().all()

        return {
            "company_id": company_id,
            "pain_points_analyzed": len(pain_points),
            "analysis_completed": True,  # TODO: Add proper status tracking
            "last_analyzed": "now",  # TODO: Add timestamp field
        }
