"""Validation service for hypothesis testing and experiment management."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.models.hypothesis import Hypothesis
from app.models.validation_experiment import ValidationExperiment
from app.models.validation_result import ValidationResult
from app.models.product_idea import ProductIdea


class ValidationService:
    """Service for managing hypothesis validation and experiments."""

    def __init__(self, db: AsyncSession):
        """Initialize validation service."""
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def create_hypothesis_from_idea(
        self,
        product_idea_id: int,
        hypothesis_data: Dict
    ) -> Hypothesis:
        """Create a hypothesis based on a product idea."""
        try:
            # Get the product idea
            query = select(ProductIdea).where(ProductIdea.id == product_idea_id)
            result = await self.db.execute(query)
            product_idea = result.scalar_one_or_none()

            if not product_idea:
                raise ValidationError("validation", f"Product idea {product_idea_id} not found")

            # Create hypothesis
            hypothesis = Hypothesis(
                company_id=product_idea.company_id,
                product_idea_id=product_idea_id,
                **hypothesis_data
            )

            self.db.add(hypothesis)
            await self.db.commit()
            await self.db.refresh(hypothesis)

            self.logger.info(f"Created hypothesis {hypothesis.id} for product idea {product_idea_id}")
            return hypothesis

        except Exception as e:
            self.logger.error(f"Failed to create hypothesis: {e}")
            raise ValidationError("validation", f"Hypothesis creation failed: {e}")

    async def create_validation_experiment(
        self,
        hypothesis_id: int,
        experiment_data: Dict
    ) -> ValidationExperiment:
        """Create a validation experiment for a hypothesis."""
        try:
            # Verify hypothesis exists
            query = select(Hypothesis).where(Hypothesis.id == hypothesis_id)
            result = await self.db.execute(query)
            hypothesis = result.scalar_one_or_none()

            if not hypothesis:
                raise ValidationError("validation", f"Hypothesis {hypothesis_id} not found")

            # Create experiment
            experiment = ValidationExperiment(
                hypothesis_id=hypothesis_id,
                **experiment_data
            )

            self.db.add(experiment)
            await self.db.commit()
            await self.db.refresh(experiment)

            self.logger.info(f"Created validation experiment {experiment.id} for hypothesis {hypothesis_id}")
            return experiment

        except Exception as e:
            self.logger.error(f"Failed to create validation experiment: {e}")
            raise ValidationError("validation", f"Experiment creation failed: {e}")

    async def record_experiment_result(
        self,
        experiment_id: int,
        result_data: Dict
    ) -> ValidationResult:
        """Record a result for a validation experiment."""
        try:
            # Verify experiment exists
            query = select(ValidationExperiment).where(ValidationExperiment.id == experiment_id)
            result = await self.db.execute(query)
            experiment = result.scalar_one_or_none()

            if not experiment:
                raise ValidationError("validation", f"Experiment {experiment_id} not found")

            # Create result record
            result = ValidationResult(
                experiment_id=experiment_id,
                **result_data
            )

            self.db.add(result)
            await self.db.commit()
            await self.db.refresh(result)

            # Update experiment status if this completes it
            await self._update_experiment_status(experiment_id)

            self.logger.info(f"Recorded result for experiment {experiment_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to record experiment result: {e}")
            raise ValidationError("validation", f"Result recording failed: {e}")

    async def update_hypothesis_status(
        self,
        hypothesis_id: int,
        status: str,
        validation_score: Optional[float] = None,
        key_findings: Optional[List[str]] = None
    ) -> Hypothesis:
        """Update hypothesis status and validation results."""
        try:
            query = select(Hypothesis).where(Hypothesis.id == hypothesis_id)
            result = await self.db.execute(query)
            hypothesis = result.scalar_one_or_none()

            if not hypothesis:
                raise ValidationError("validation", f"Hypothesis {hypothesis_id} not found")

            hypothesis.status = status
            if validation_score is not None:
                hypothesis.validation_score = validation_score
            if key_findings is not None:
                hypothesis.key_findings = key_findings

            if status in ['validated', 'invalidated']:
                from datetime import datetime
                hypothesis.validated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(hypothesis)

            self.logger.info(f"Updated hypothesis {hypothesis_id} status to {status}")
            return hypothesis

        except Exception as e:
            self.logger.error(f"Failed to update hypothesis status: {e}")
            raise ValidationError("validation", f"Hypothesis update failed: {e}")

    async def get_hypothesis_validation_summary(self, hypothesis_id: int) -> Dict:
        """Get comprehensive validation summary for a hypothesis."""
        try:
            # Get hypothesis
            query = select(Hypothesis).where(Hypothesis.id == hypothesis_id)
            result = await self.db.execute(query)
            hypothesis = result.scalar_one_or_none()

            if not hypothesis:
                raise ValidationError("validation", f"Hypothesis {hypothesis_id} not found")

            # Get experiments
            query = select(ValidationExperiment).where(ValidationExperiment.hypothesis_id == hypothesis_id)
            result = await self.db.execute(query)
            experiments = result.scalars().all()

            # Build summary
            summary = {
                "hypothesis": {
                    "id": hypothesis.id,
                    "title": hypothesis.title,
                    "statement": hypothesis.hypothesis_statement,
                    "status": hypothesis.status,
                    "validation_score": hypothesis.validation_score,
                    "category": hypothesis.category,
                    "priority": hypothesis.priority,
                },
                "experiments": {
                    "total": len(experiments),
                    "completed": len([e for e in experiments if e.status == "completed"]),
                    "running": len([e for e in experiments if e.status == "running"]),
                    "planned": len([e for e in experiments if e.status == "planned"]),
                },
                "results_summary": await self._calculate_validation_summary(experiments),
                "recommendations": await self._generate_validation_recommendations(hypothesis, experiments),
            }

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get validation summary: {e}")
            raise ValidationError("validation", f"Summary generation failed: {e}")

    async def _update_experiment_status(self, experiment_id: int):
        """Update experiment status based on results."""
        # Get experiment and its results
        query = select(ValidationExperiment).where(ValidationExperiment.id == experiment_id)
        result = await self.db.execute(query)
        experiment = result.scalar_one_or_none()

        if not experiment:
            return

        # Get results count
        query = select(ValidationResult).where(ValidationResult.experiment_id == experiment_id)
        result = await self.db.execute(query)
        results = result.scalars().all()

        # If we have results and target sample size, check completion
        if results and experiment.target_sample_size:
            if len(results) >= experiment.target_sample_size:
                experiment.status = "completed"
                await self.db.commit()

    async def _calculate_validation_summary(self, experiments: List[ValidationExperiment]) -> Dict:
        """Calculate validation summary from experiments."""
        summary = {
            "overall_confidence": 0.0,
            "supporting_evidence": 0,
            "contradicting_evidence": 0,
            "inconclusive_evidence": 0,
            "key_metrics": {},
            "experiment_types": {},
        }

        if not experiments:
            return summary

        total_confidence = 0
        completed_experiments = 0

        for experiment in experiments:
            # Count experiment types
            exp_type = experiment.experiment_type
            summary["experiment_types"][exp_type] = summary["experiment_types"].get(exp_type, 0) + 1

            # Only consider completed experiments for confidence
            if experiment.status == "completed" and experiment.supports_hypothesis is not None:
                completed_experiments += 1
                total_confidence += experiment.result_confidence or 0.5

                if experiment.supports_hypothesis:
                    summary["supporting_evidence"] += 1
                else:
                    summary["contradicting_evidence"] += 1

            # Track key metrics
            if experiment.primary_metric and experiment.actual_result is not None:
                metric = experiment.primary_metric
                if metric not in summary["key_metrics"]:
                    summary["key_metrics"][metric] = []
                summary["key_metrics"][metric].append(experiment.actual_result)

        # Calculate overall confidence
        if completed_experiments > 0:
            summary["overall_confidence"] = total_confidence / completed_experiments

        # Calculate averages for metrics
        for metric, values in summary["key_metrics"].items():
            summary["key_metrics"][metric] = {
                "values": values,
                "average": sum(values) / len(values),
                "count": len(values),
            }

        return summary

    async def _generate_validation_recommendations(
        self,
        hypothesis: Hypothesis,
        experiments: List[ValidationExperiment]
    ) -> List[str]:
        """Generate validation recommendations based on current state."""
        recommendations = []

        completed_experiments = [e for e in experiments if e.status == "completed"]
        running_experiments = [e for e in experiments if e.status == "running"]
        planned_experiments = [e for e in experiments if e.status == "planned"]

        # Check if we need more experiments
        if len(completed_experiments) == 0:
            recommendations.append("Start with a simple validation experiment to test core assumptions")

        # Check for contradictory evidence
        contradictory = [e for e in completed_experiments if e.supports_hypothesis is False]
        if contradictory:
            recommendations.append("Review contradictory evidence and consider refining the hypothesis")

        # Check for inconclusive results
        inconclusive = [e for e in completed_experiments if e.experiment_outcome == "inconclusive"]
        if inconclusive:
            recommendations.append("Design more rigorous experiments to reduce inconclusive results")

        # Suggest next steps based on hypothesis status
        if hypothesis.status == "proposed":
            recommendations.append("Begin validation with low-cost experiments like surveys or landing pages")
        elif hypothesis.status == "testing" and not running_experiments:
            recommendations.append("Launch additional experiments to gather more evidence")
        elif hypothesis.status in ["validated", "invalidated"]:
            if hypothesis.status == "validated":
                recommendations.append("Consider building a prototype or MVP based on validation results")
            else:
                recommendations.append("Pivot the hypothesis or explore alternative assumptions")

        # Suggest experiment types if limited variety
        experiment_types = set(e.experiment_type for e in experiments)
        if len(experiment_types) < 2 and len(experiments) > 2:
            recommendations.append("Diversify experiment types to validate from multiple angles")

        return recommendations
