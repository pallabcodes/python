"""Company service for business logic."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


class CompanyService:
    """Service for company operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def get_companies(self, skip: int = 0, limit: int = 100) -> List[models.Company]:
        """Get all companies with pagination."""
        query = select(models.Company).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_company(self, company_id: int) -> Optional[models.Company]:
        """Get company by ID."""
        query = select(models.Company).where(models.Company.id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_company(self, company: schemas.CompanyCreate) -> models.Company:
        """Create a new company."""
        db_company = models.Company(**company.model_dump())
        self.db.add(db_company)
        await self.db.commit()
        await self.db.refresh(db_company)
        return db_company

    async def update_company(
        self, company_id: int, company_update: schemas.CompanyUpdate
    ) -> Optional[models.Company]:
        """Update company information."""
        company = await self.get_company(company_id)
        if not company:
            return None

        update_data = company_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def delete_company(self, company_id: int) -> bool:
        """Delete a company."""
        company = await self.get_company(company_id)
        if not company:
            return False

        await self.db.delete(company)
        await self.db.commit()
        return True

    async def start_research(self, company_id: int) -> bool:
        """Start research collection for a company."""
        company = await self.get_company(company_id)
        if not company:
            return False

        # Update research status
        company.research_status = "in_progress"
        await self.db.commit()
        await self.db.refresh(company)

        # TODO: Trigger research collection workflow
        # This would integrate with the research collectors

        return True
