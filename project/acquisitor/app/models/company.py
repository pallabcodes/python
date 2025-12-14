"""Company models for Acquisitor."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.db.base import Base


class Company(Base):
    """Company model for target companies (Notion, Canva, etc.)."""

    __tablename__ = "companies"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(255), nullable=False, unique=True, index=True)
    domain: str = Column(String(255), nullable=False, index=True)
    description: str = Column(Text, nullable=True)
    industry: str = Column(String(100), nullable=True)
    founded_year: Optional[int] = Column(Integer, nullable=True)
    headquarters: str = Column(String(255), nullable=True)
    funding_stage: str = Column(String(50), nullable=True)  # startup, series_a, etc.
    market_cap: Optional[float] = Column(Float, nullable=True)

    # Product ecosystem
    main_product: str = Column(String(255), nullable=True)
    product_categories: List[str] = Column(JSON, default=list)  # ["productivity", "design", etc.]

    # Acquisition data
    acquisition_history: List[Dict] = Column(JSON, default=list)  # Past acquisitions
    acquisition_criteria: Dict = Column(JSON, nullable=True)  # What they look for

    # Research metadata
    research_status: str = Column(String(50), default="not_started")  # not_started, in_progress, completed
    last_researched: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    research_sources: List[str] = Column(JSON, default=list)  # Sources used for research

    # Analysis results
    pain_points_count: int = Column(Integer, default=0)
    product_ideas_count: int = Column(Integer, default=0)
    avg_acquisition_potential: float = Column(Float, default=0.0)

    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pain_points = relationship("PainPoint", back_populates="company", cascade="all, delete-orphan")
    product_ideas = relationship("ProductIdea", back_populates="company", cascade="all, delete-orphan")
    research_data = relationship("ResearchData", back_populates="company", cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of Company."""
        return f"<Company(id={self.id}, name='{self.name}', domain='{self.domain}')>"
