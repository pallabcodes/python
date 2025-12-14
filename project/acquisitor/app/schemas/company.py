"""Company schemas for request/response validation."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class CompanyBase(BaseModel):
    """Base company schema."""

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    industry: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1800, le=datetime.now().year + 1)
    headquarters: Optional[str] = Field(None, max_length=255)
    funding_stage: Optional[str] = Field(None, max_length=50)
    market_cap: Optional[float] = Field(None, ge=0)
    main_product: Optional[str] = Field(None, max_length=255)
    product_categories: List[str] = Field(default_factory=list)

    @validator("domain")
    def validate_domain(cls, v):
        """Validate domain format."""
        if not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        return v

    @validator("funding_stage")
    def validate_funding_stage(cls, v):
        """Validate funding stage."""
        if v:
            valid_stages = [
                "idea", "pre-seed", "seed", "series_a", "series_b", "series_c",
                "series_d", "growth", "ipo", "acquired", "public"
            ]
            if v.lower() not in valid_stages:
                raise ValueError(f"Invalid funding stage. Must be one of: {valid_stages}")
        return v


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    industry: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1800, le=datetime.now().year + 1)
    headquarters: Optional[str] = Field(None, max_length=255)
    funding_stage: Optional[str] = Field(None, max_length=50)
    market_cap: Optional[float] = Field(None, ge=0)
    main_product: Optional[str] = Field(None, max_length=255)
    product_categories: Optional[List[str]] = None

    @validator("domain")
    def validate_domain(cls, v):
        """Validate domain format."""
        if v and not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        return v

    @validator("funding_stage")
    def validate_funding_stage(cls, v):
        """Validate funding stage."""
        if v:
            valid_stages = [
                "idea", "pre-seed", "seed", "series_a", "series_b", "series_c",
                "series_d", "growth", "ipo", "acquired", "public"
            ]
            if v.lower() not in valid_stages:
                raise ValueError(f"Invalid funding stage. Must be one of: {valid_stages}")
        return v


class Company(CompanyBase):
    """Schema for company response."""

    id: int
    acquisition_history: List[Dict] = Field(default_factory=list)
    acquisition_criteria: Optional[Dict] = None
    research_status: str = "not_started"
    last_researched: Optional[datetime] = None
    research_sources: List[str] = Field(default_factory=list)
    pain_points_count: int = 0
    product_ideas_count: int = 0
    avg_acquisition_potential: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
