"""Analysis API endpoints."""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/companies/{company_id}/analyze")
async def run_full_analysis(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Run complete analysis pipeline for a company."""
    analysis_service = AnalysisService(db)

    try:
        result = await analysis_service.run_full_analysis(company_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/companies/{company_id}/pain-points/analyze")
async def analyze_pain_points(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Analyze pain points for a company."""
    analysis_service = AnalysisService(db)

    try:
        result = await analysis_service.analyze_pain_points(company_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pain point analysis failed: {str(e)}")


@router.post("/companies/{company_id}/ideas/generate")
async def generate_product_ideas(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate product ideas for a company."""
    analysis_service = AnalysisService(db)

    try:
        result = await analysis_service.generate_product_ideas(company_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product ideation failed: {str(e)}")


@router.get("/companies/{company_id}/analysis/status")
async def get_analysis_status(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis status for a company."""
    analysis_service = AnalysisService(db)
    status = await analysis_service.get_analysis_status(company_id)
    return status


@router.get("/companies/{company_id}/analysis/summary")
async def get_analysis_summary(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive analysis summary for a company."""
    analysis_service = AnalysisService(db)
    summary = await analysis_service.get_analysis_summary(company_id)
    return summary
