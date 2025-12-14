"""Analysis service for research data analysis and product ideation."""

import logging
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from ideation import ProductIdeationEngine
from research import AnalysisOrchestrator


class AnalysisService:
    """Service for analysis operations."""

    def __init__(self, db: AsyncSession):
        """Initialize analysis service."""
        self.db = db
        self.orchestrator = AnalysisOrchestrator(db)
        self.ideation_engine = ProductIdeationEngine(db)
        self.logger = logging.getLogger(__name__)

    async def run_full_analysis(self, company_id: int) -> Dict[str, any]:
        """Run complete analysis pipeline for a company."""
        try:
            self.logger.info(f"Starting full analysis for company {company_id}")

            # Step 1: Analyze pain points
            pain_point_results = await self.orchestrator.analyze_company_data(company_id)

            # Step 2: Generate product ideas
            ideation_results = await self.ideation_engine.generate_product_ideas(company_id)

            # Combine results
            full_results = {
                "company_id": company_id,
                "status": "completed",
                "pain_points_found": pain_point_results.get("pain_points_found", 0),
                "product_ideas_generated": len(ideation_results),
                "analysis_summary": pain_point_results.get("summary", {}),
                "top_ideas": [
                    {
                        "id": idea.id,
                        "title": idea.title,
                        "acquisition_fit_score": idea.acquisition_fit_score,
                        "category": idea.category,
                        "target_users": idea.target_users,
                    }
                    for idea in ideation_results[:5]  # Top 5 ideas
                ],
                "timestamp": "now",  # TODO: Add proper timestamp
            }

            self.logger.info(f"Full analysis completed for company {company_id}")
            return full_results

        except Exception as e:
            self.logger.error(f"Full analysis failed for company {company_id}: {e}")
            raise

    async def analyze_pain_points(self, company_id: int) -> Dict[str, any]:
        """Analyze pain points for a company."""
        return await self.orchestrator.analyze_company_data(company_id)

    async def generate_product_ideas(self, company_id: int) -> Dict[str, any]:
        """Generate product ideas for a company."""
        try:
            ideas = await self.ideation_engine.generate_product_ideas(company_id)

            return {
                "company_id": company_id,
                "status": "completed",
                "ideas_generated": len(ideas),
                "top_ideas": [
                    {
                        "id": idea.id,
                        "title": idea.title,
                        "acquisition_fit_score": idea.acquisition_fit_score,
                        "category": idea.category,
                    }
                    for idea in ideas[:10]
                ],
            }

        except Exception as e:
            self.logger.error(f"Product ideation failed for company {company_id}: {e}")
            raise

    async def get_analysis_status(self, company_id: int) -> Dict[str, any]:
        """Get analysis status for a company."""
        return await self.orchestrator.get_analysis_status(company_id)

    async def get_analysis_summary(self, company_id: int) -> Dict[str, any]:
        """Get comprehensive analysis summary for a company."""
        # Get basic status
        status = await self.get_analysis_status(company_id)

        if not status.get("analysis_completed", False):
            return {
                "company_id": company_id,
                "status": "not_analyzed",
                "message": "Analysis has not been run for this company yet.",
            }

        # Get pain points
        from sqlalchemy import select
        from app.models.pain_point import PainPoint
        from app.models.product_idea import ProductIdea

        pain_points_query = select(PainPoint).where(PainPoint.company_id == company_id)
        pain_points_result = await self.db.execute(pain_points_query)
        pain_points = pain_points_result.scalars().all()

        # Get product ideas
        ideas_query = select(ProductIdea).where(ProductIdea.company_id == company_id)
        ideas_result = await self.db.execute(ideas_query)
        product_ideas = ideas_result.scalars().all()

        # Build comprehensive summary
        summary = {
            "company_id": company_id,
            "status": "analyzed",
            "pain_points": {
                "total": len(pain_points),
                "by_severity": self._group_by_attribute(pain_points, "impact"),
                "by_category": self._group_by_attribute(pain_points, "category"),
                "top_pain_points": [
                    {
                        "id": pp.id,
                        "title": pp.title,
                        "severity": pp.severity,
                        "impact": pp.impact,
                        "category": pp.category,
                    }
                    for pp in sorted(pain_points, key=lambda x: x.severity, reverse=True)[:5]
                ],
            },
            "product_ideas": {
                "total": len(product_ideas),
                "by_category": self._group_by_attribute(product_ideas, "category"),
                "top_ideas": [
                    {
                        "id": idea.id,
                        "title": idea.title,
                        "acquisition_fit_score": idea.acquisition_fit_score,
                        "category": idea.category,
                        "target_users": idea.target_users,
                    }
                    for idea in sorted(product_ideas, key=lambda x: x.acquisition_fit_score, reverse=True)[:10]
                ],
            },
            "insights": self._generate_insights(pain_points, product_ideas),
        }

        return summary

    def _group_by_attribute(self, items: List, attribute: str) -> Dict[str, int]:
        """Group items by an attribute and count occurrences."""
        groups = {}
        for item in items:
            value = getattr(item, attribute, "unknown")
            groups[value] = groups.get(value, 0) + 1
        return groups

    def _generate_insights(self, pain_points: List, product_ideas: List) -> List[str]:
        """Generate insights from analysis results."""
        insights = []

        # Pain point insights
        if pain_points:
            avg_severity = sum(pp.severity for pp in pain_points) / len(pain_points)
            if avg_severity > 7.0:
                insights.append("Critical severity pain points indicate major market opportunities.")
            elif avg_severity > 5.0:
                insights.append("Moderate to high severity issues suggest room for significant improvements.")

            # Category insights
            categories = self._group_by_attribute(pain_points, "category")
            if categories:
                top_category = max(categories.items(), key=lambda x: x[1])
                insights.append(f"Most common pain point category: {top_category[0]} ({top_category[1]} instances)")

        # Product idea insights
        if product_ideas:
            avg_acquisition_fit = sum(idea.acquisition_fit_score for idea in product_ideas) / len(product_ideas)
            high_potential_ideas = [idea for idea in product_ideas if idea.acquisition_fit_score > 0.7]

            if high_potential_ideas:
                insights.append(f"{len(high_potential_ideas)} product ideas show high acquisition potential (>70% fit).")

            if avg_acquisition_fit > 0.6:
                insights.append("Generated ideas show strong acquisition potential on average.")

        # Overall insights
        if len(pain_points) > 0 and len(product_ideas) > 0:
            ratio = len(product_ideas) / len(pain_points)
            if ratio > 2:
                insights.append("Multiple solution ideas generated per pain point indicate rich opportunity space.")
            elif ratio < 1:
                insights.append("Consider generating more solution ideas for identified pain points.")

        return insights
