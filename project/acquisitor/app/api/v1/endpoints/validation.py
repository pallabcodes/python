"""Validation API endpoints."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.validation_service import ValidationService

router = APIRouter()


@router.post("/companies/{company_id}/ideas/{idea_id}/hypotheses")
async def create_hypothesis(
    company_id: int,
    idea_id: int,
    hypothesis_data: Dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a hypothesis for a product idea."""
    validation_service = ValidationService(db)

    try:
        hypothesis = await validation_service.create_hypothesis_from_idea(idea_id, hypothesis_data)
        return {
            "id": hypothesis.id,
            "title": hypothesis.title,
            "status": hypothesis.status,
            "category": hypothesis.category,
            "created_at": hypothesis.created_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hypothesis creation failed: {str(e)}")


@router.post("/hypotheses/{hypothesis_id}/experiments")
async def create_validation_experiment(
    hypothesis_id: int,
    experiment_data: Dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a validation experiment for a hypothesis."""
    validation_service = ValidationService(db)

    try:
        experiment = await validation_service.create_validation_experiment(hypothesis_id, experiment_data)
        return {
            "id": experiment.id,
            "title": experiment.title,
            "experiment_type": experiment.experiment_type,
            "status": experiment.status,
            "target_sample_size": experiment.target_sample_size,
            "created_at": experiment.created_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment creation failed: {str(e)}")


@router.post("/experiments/{experiment_id}/results")
async def record_experiment_result(
    experiment_id: int,
    result_data: Dict,
    db: AsyncSession = Depends(get_db),
):
    """Record a result for a validation experiment."""
    validation_service = ValidationService(db)

    try:
        result = await validation_service.record_experiment_result(experiment_id, result_data)
        return {
            "id": result.id,
            "result_type": result.result_type,
            "metric_name": result.metric_name,
            "metric_value": result.metric_value,
            "collected_at": result.collected_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Result recording failed: {str(e)}")


@router.put("/hypotheses/{hypothesis_id}/status")
async def update_hypothesis_status(
    hypothesis_id: int,
    status_update: Dict,
    db: AsyncSession = Depends(get_db),
):
    """Update hypothesis status and validation results."""
    validation_service = ValidationService(db)

    try:
        hypothesis = await validation_service.update_hypothesis_status(
            hypothesis_id,
            status_update["status"],
            status_update.get("validation_score"),
            status_update.get("key_findings")
        )
        return {
            "id": hypothesis.id,
            "status": hypothesis.status,
            "validation_score": hypothesis.validation_score,
            "key_findings": hypothesis.key_findings,
            "updated_at": hypothesis.updated_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hypothesis update failed: {str(e)}")


@router.get("/hypotheses/{hypothesis_id}/validation-summary")
async def get_hypothesis_validation_summary(
    hypothesis_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive validation summary for a hypothesis."""
    validation_service = ValidationService(db)

    try:
        summary = await validation_service.get_hypothesis_validation_summary(hypothesis_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary retrieval failed: {str(e)}")


@router.get("/companies/{company_id}/validation-overview")
async def get_company_validation_overview(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get validation overview for all hypotheses in a company."""
    from sqlalchemy import select
    from app.models.hypothesis import Hypothesis

    try:
        query = select(Hypothesis).where(Hypothesis.company_id == company_id)
        result = await db.execute(query)
        hypotheses = result.scalars().all()

        overview = {
            "company_id": company_id,
            "total_hypotheses": len(hypotheses),
            "status_breakdown": {},
            "category_breakdown": {},
            "priority_breakdown": {},
            "hypotheses": [],
        }

        for hypothesis in hypotheses:
            # Count by status
            status = hypothesis.status
            overview["status_breakdown"][status] = overview["status_breakdown"].get(status, 0) + 1

            # Count by category
            category = hypothesis.category
            overview["category_breakdown"][category] = overview["category_breakdown"].get(category, 0) + 1

            # Count by priority
            priority = hypothesis.priority
            overview["priority_breakdown"][priority] = overview["priority_breakdown"].get(priority, 0) + 1

            # Add hypothesis summary
            overview["hypotheses"].append({
                "id": hypothesis.id,
                "title": hypothesis.title,
                "status": hypothesis.status,
                "validation_score": hypothesis.validation_score,
                "category": hypothesis.category,
                "priority": hypothesis.priority,
            })

        return overview

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview retrieval failed: {str(e)}")
