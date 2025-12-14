"""Research API endpoints."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.research_service import ResearchService

router = APIRouter()


@router.post("/companies/{company_id}/collect")
async def start_research(
    company_id: int,
    sources: List[str] = Query(None, description="Sources to collect from"),
    db: AsyncSession = Depends(get_db),
):
    """Start research collection for a company."""
    research_service = ResearchService(db)

    try:
        result = await research_service.start_research(
            company_id=company_id,
            sources=sources,
            validate_config=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research collection failed: {str(e)}")


@router.get("/companies/{company_id}/status")
async def get_research_status(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get research status for a company."""
    research_service = ResearchService(db)
    status = await research_service.get_research_status(company_id)
    return status


@router.get("/companies/{company_id}/summary")
async def get_research_summary(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get research summary for a company."""
    research_service = ResearchService(db)
    summary = await research_service.get_research_summary(company_id)
    return summary


@router.get("/sources")
async def get_available_sources(
    db: AsyncSession = Depends(get_db),
):
    """Get list of available research sources."""
    research_service = ResearchService(db)
    sources = await research_service.get_available_sources()
    return {"sources": sources}


@router.get("/sources/config")
async def validate_source_configs(
    db: AsyncSession = Depends(get_db),
):
    """Validate configurations for all research sources."""
    research_service = ResearchService(db)
    configs = await research_service.validate_source_configs()
    return configs
