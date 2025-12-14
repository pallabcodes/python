"""Reporting service for analytics and dashboard generation."""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.company import Company
from app.models.pain_point import PainPoint
from app.models.product_idea import ProductIdea
from app.models.hypothesis import Hypothesis
from app.models.validation_experiment import ValidationExperiment


class ReportingService:
    """Service for generating reports and analytics."""

    def __init__(self, db: AsyncSession):
        """Initialize reporting service."""
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data."""
        try:
            # Get overall statistics
            companies_count = await self._get_companies_count()
            total_pain_points = await self._get_total_pain_points()
            total_ideas = await self._get_total_ideas()
            total_hypotheses = await self._get_total_hypotheses()

            # Get recent activity
            recent_activity = await self._get_recent_activity()

            # Get top insights
            top_insights = await self._get_top_insights()

            # Get validation pipeline status
            validation_status = await self._get_validation_pipeline_status()

            return {
                "summary": {
                    "companies": companies_count,
                    "pain_points": total_pain_points,
                    "product_ideas": total_ideas,
                    "hypotheses": total_hypotheses,
                    "last_updated": datetime.utcnow().isoformat(),
                },
                "recent_activity": recent_activity,
                "top_insights": top_insights,
                "validation_pipeline": validation_status,
            }

        except Exception as e:
            self.logger.error(f"Failed to generate dashboard data: {e}")
            raise

    async def get_company_report(self, company_id: int) -> Dict:
        """Generate detailed report for a specific company."""
        try:
            # Get company info
            company = await self._get_company_info(company_id)
            if not company:
                raise ValueError(f"Company {company_id} not found")

            # Get company statistics
            stats = await self._get_company_statistics(company_id)

            # Get pain point analysis
            pain_analysis = await self._get_pain_point_analysis(company_id)

            # Get product ideation analysis
            ideation_analysis = await self._get_ideation_analysis(company_id)

            # Get validation status
            validation_status = await self._get_company_validation_status(company_id)

            return {
                "company": {
                    "id": company.id,
                    "name": company.name,
                    "domain": company.domain,
                    "industry": company.industry,
                    "description": company.description,
                },
                "statistics": stats,
                "pain_point_analysis": pain_analysis,
                "ideation_analysis": ideation_analysis,
                "validation_status": validation_status,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to generate company report: {e}")
            raise

    async def get_validation_report(self) -> Dict:
        """Generate validation pipeline report."""
        try:
            # Get hypothesis status breakdown
            hypothesis_status = await self._get_hypothesis_status_breakdown()

            # Get experiment status breakdown
            experiment_status = await self._get_experiment_status_breakdown()

            # Get validation success rates
            success_rates = await self._get_validation_success_rates()

            # Get recent validation results
            recent_results = await self._get_recent_validation_results()

            return {
                "hypothesis_status": hypothesis_status,
                "experiment_status": experiment_status,
                "success_rates": success_rates,
                "recent_results": recent_results,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to generate validation report: {e}")
            raise

    async def _get_companies_count(self) -> int:
        """Get total number of companies."""
        query = select(func.count(Company.id))
        result = await self.db.execute(query)
        return result.scalar()

    async def _get_total_pain_points(self) -> int:
        """Get total number of pain points."""
        query = select(func.count(PainPoint.id))
        result = await self.db.execute(query)
        return result.scalar()

    async def _get_total_ideas(self) -> int:
        """Get total number of product ideas."""
        query = select(func.count(ProductIdea.id))
        result = await self.db.execute(query)
        return result.scalar()

    async def _get_total_hypotheses(self) -> int:
        """Get total number of hypotheses."""
        query = select(func.count(Hypothesis.id))
        result = await self.db.execute(query)
        return result.scalar()

    async def _get_recent_activity(self) -> List[Dict]:
        """Get recent activity across the system."""
        activities = []

        # Recent hypotheses
        query = select(Hypothesis).order_by(Hypothesis.created_at.desc()).limit(5)
        result = await self.db.execute(query)
        hypotheses = result.scalars().all()

        for hyp in hypotheses:
            activities.append({
                "type": "hypothesis_created",
                "description": f"New hypothesis: {hyp.title[:50]}...",
                "timestamp": hyp.created_at.isoformat(),
                "entity_id": hyp.id,
            })

        # Recent experiments
        query = select(ValidationExperiment).order_by(ValidationExperiment.created_at.desc()).limit(5)
        result = await self.db.execute(query)
        experiments = result.scalars().all()

        for exp in experiments:
            activities.append({
                "type": "experiment_created",
                "description": f"New experiment: {exp.title[:50]}...",
                "timestamp": exp.created_at.isoformat(),
                "entity_id": exp.id,
            })

        # Sort by timestamp and return top 10
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:10]

    async def _get_top_insights(self) -> List[str]:
        """Generate top insights from the data."""
        insights = []

        # Most active companies
        query = select(
            Company.name,
            func.count(PainPoint.id).label("pain_points")
        ).join(PainPoint).group_by(Company.id).order_by(func.count(PainPoint.id).desc()).limit(3)

        result = await self.db.execute(query)
        active_companies = result.all()

        if active_companies:
            top_company = active_companies[0]
            insights.append(f"{top_company.name} has the most identified pain points ({top_company.pain_points})")

        # Highest rated ideas
        query = select(ProductIdea).order_by(ProductIdea.acquisition_fit_score.desc()).limit(1)
        result = await self.db.execute(query)
        top_idea = result.scalar_one_or_none()

        if top_idea:
            insights.append(f"Top acquisition opportunity: {top_idea.title[:50]}... ({top_idea.acquisition_fit_score:.1%} fit)")

        # Validation progress
        query = select(func.count(Hypothesis.id)).where(
            or_(Hypothesis.status == "validated", Hypothesis.status == "invalidated")
        )
        result = await self.db.execute(query)
        validated_count = result.scalar()

        total_hypotheses = await self._get_total_hypotheses()
        if total_hypotheses > 0:
            validation_rate = validated_count / total_hypotheses
            insights.append(f"{validation_rate:.1%} of hypotheses have been validated")

        return insights

    async def _get_validation_pipeline_status(self) -> Dict:
        """Get validation pipeline status."""
        # Count hypotheses by status
        status_counts = {}
        statuses = ["proposed", "testing", "validated", "invalidated", "paused"]

        for status in statuses:
            query = select(func.count(Hypothesis.id)).where(Hypothesis.status == status)
            result = await self.db.execute(query)
            status_counts[status] = result.scalar()

        # Count experiments by status
        exp_status_counts = {}
        exp_statuses = ["planned", "running", "completed", "cancelled"]

        for status in exp_statuses:
            query = select(func.count(ValidationExperiment.id)).where(ValidationExperiment.status == status)
            result = await self.db.execute(query)
            exp_status_counts[status] = result.scalar()

        return {
            "hypotheses_by_status": status_counts,
            "experiments_by_status": exp_status_counts,
        }

    async def _get_company_info(self, company_id: int) -> Optional[Company]:
        """Get company information."""
        query = select(Company).where(Company.id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_company_statistics(self, company_id: int) -> Dict:
        """Get statistics for a company."""
        # Pain points count
        query = select(func.count(PainPoint.id)).where(PainPoint.company_id == company_id)
        result = await self.db.execute(query)
        pain_points_count = result.scalar()

        # Product ideas count
        query = select(func.count(ProductIdea.id)).where(ProductIdea.company_id == company_id)
        result = await self.db.execute(query)
        ideas_count = result.scalar()

        # Hypotheses count
        query = select(func.count(Hypothesis.id)).where(Hypothesis.company_id == company_id)
        result = await self.db.execute(query)
        hypotheses_count = result.scalar()

        return {
            "pain_points_count": pain_points_count,
            "product_ideas_count": ideas_count,
            "hypotheses_count": hypotheses_count,
        }

    async def _get_pain_point_analysis(self, company_id: int) -> Dict:
        """Get pain point analysis for a company."""
        query = select(PainPoint).where(PainPoint.company_id == company_id)
        result = await self.db.execute(query)
        pain_points = result.scalars().all()

        if not pain_points:
            return {"total": 0, "by_category": {}, "by_severity": {}, "insights": []}

        # Category breakdown
        categories = {}
        severities = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for pp in pain_points:
            # Category count
            cat = pp.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1

            # Severity count
            impact = pp.impact or "medium"
            if impact in severities:
                severities[impact] += 1

        # Generate insights
        insights = []
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            insights.append(f"Most common pain point category: {top_category[0]} ({top_category[1]} issues)")

        avg_severity = sum(pp.severity for pp in pain_points) / len(pain_points)
        if avg_severity > 7.0:
            insights.append("High average pain point severity indicates critical user issues")
        elif avg_severity > 5.0:
            insights.append("Moderate to high severity suggests significant improvement opportunities")

        return {
            "total": len(pain_points),
            "by_category": categories,
            "by_severity": severities,
            "average_severity": avg_severity,
            "insights": insights,
        }

    async def _get_ideation_analysis(self, company_id: int) -> Dict:
        """Get product ideation analysis for a company."""
        query = select(ProductIdea).where(ProductIdea.company_id == company_id)
        result = await self.db.execute(query)
        ideas = result.scalars().all()

        if not ideas:
            return {"total": 0, "by_category": {}, "top_ideas": [], "insights": []}

        # Category breakdown
        categories = {}
        for idea in ideas:
            cat = idea.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1

        # Top ideas by acquisition fit
        top_ideas = sorted(ideas, key=lambda x: x.acquisition_fit_score or 0, reverse=True)[:5]
        top_ideas_data = [
            {
                "title": idea.title,
                "category": idea.category,
                "acquisition_fit_score": idea.acquisition_fit_score,
                "target_users": idea.target_users,
            }
            for idea in top_ideas
        ]

        # Generate insights
        insights = []
        avg_fit = sum((idea.acquisition_fit_score or 0) for idea in ideas) / len(ideas)
        if avg_fit > 0.7:
            insights.append("Strong average acquisition fit score across generated ideas")
        elif avg_fit > 0.5:
            insights.append("Moderate acquisition potential - some ideas show strong promise")

        if len(ideas) > 10:
            insights.append("Large number of ideas generated - consider prioritization")

        return {
            "total": len(ideas),
            "by_category": categories,
            "average_acquisition_fit": avg_fit,
            "top_ideas": top_ideas_data,
            "insights": insights,
        }

    async def _get_company_validation_status(self, company_id: int) -> Dict:
        """Get validation status for a company."""
        query = select(Hypothesis).where(Hypothesis.company_id == company_id)
        result = await self.db.execute(query)
        hypotheses = result.scalars().all()

        if not hypotheses:
            return {"total_hypotheses": 0, "by_status": {}, "experiments_count": 0}

        # Status breakdown
        statuses = {}
        for hyp in hypotheses:
            status = hyp.status
            statuses[status] = statuses.get(status, 0) + 1

        # Count experiments
        hypothesis_ids = [h.id for h in hypotheses]
        query = select(func.count(ValidationExperiment.id)).where(
            ValidationExperiment.hypothesis_id.in_(hypothesis_ids)
        )
        result = await self.db.execute(query)
        experiments_count = result.scalar()

        return {
            "total_hypotheses": len(hypotheses),
            "by_status": statuses,
            "experiments_count": experiments_count,
        }

    async def _get_hypothesis_status_breakdown(self) -> Dict:
        """Get hypothesis status breakdown across all companies."""
        statuses = ["proposed", "testing", "validated", "invalidated", "paused"]
        breakdown = {}

        for status in statuses:
            query = select(func.count(Hypothesis.id)).where(Hypothesis.status == status)
            result = await self.db.execute(query)
            breakdown[status] = result.scalar()

        return breakdown

    async def _get_experiment_status_breakdown(self) -> Dict:
        """Get experiment status breakdown across all hypotheses."""
        statuses = ["planned", "running", "completed", "cancelled"]
        breakdown = {}

        for status in statuses:
            query = select(func.count(ValidationExperiment.id)).where(ValidationExperiment.status == status)
            result = await self.db.execute(query)
            breakdown[status] = result.scalar()

        return breakdown

    async def _get_validation_success_rates(self) -> Dict:
        """Get validation success rates."""
        # Get validated hypotheses
        query = select(Hypothesis).where(Hypothesis.status.in_(["validated", "invalidated"]))
        result = await self.db.execute(query)
        validated_hypotheses = result.scalars().all()

        success_count = sum(1 for h in validated_hypotheses if h.status == "validated")
        total_validated = len(validated_hypotheses)

        success_rate = success_count / total_validated if total_validated > 0 else 0

        # Get average validation score
        scores = [h.validation_score for h in validated_hypotheses if h.validation_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "success_rate": success_rate,
            "total_validated": total_validated,
            "successful_validations": success_count,
            "average_validation_score": avg_score,
        }

    async def _get_recent_validation_results(self) -> List[Dict]:
        """Get recent validation results."""
        # Get recently updated hypotheses
        query = select(Hypothesis).where(
            Hypothesis.status.in_(["validated", "invalidated"])
        ).order_by(Hypothesis.validated_at.desc()).limit(10)

        result = await self.db.execute(query)
        recent_hypotheses = result.scalars().all()

        results = []
        for hyp in recent_hypotheses:
            results.append({
                "hypothesis_id": hyp.id,
                "title": hyp.title,
                "status": hyp.status,
                "validation_score": hyp.validation_score,
                "validated_at": hyp.validated_at.isoformat() if hyp.validated_at else None,
            })

        return results
