"""Companies API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db.session import get_db
from app.services.company_service import CompanyService

router = APIRouter()


@router.get("/", response_model=List[schemas.Company])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all companies with pagination."""
    company_service = CompanyService(db)
    companies = await company_service.get_companies(skip=skip, limit=limit)
    return companies


@router.post("/", response_model=schemas.Company)
async def create_company(
    company: schemas.CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new company."""
    company_service = CompanyService(db)
    return await company_service.create_company(company)


@router.get("/{company_id}", response_model=schemas.Company)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get company by ID."""
    company_service = CompanyService(db)
    company = await company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=schemas.Company)
async def update_company(
    company_id: int,
    company_update: schemas.CompanyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update company information."""
    company_service = CompanyService(db)
    company = await company_service.update_company(company_id, company_update)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a company."""
    company_service = CompanyService(db)
    success = await company_service.delete_company(company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}


@router.post("/{company_id}/research")
async def start_research(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Start research collection for a company."""
    company_service = CompanyService(db)
    success = await company_service.start_research(company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Research started successfully"}
