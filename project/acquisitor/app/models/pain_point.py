"""Pain point models for Acquisitor."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class PainPoint(Base):
    """Pain point model for company-specific problems."""

    __tablename__ = "pain_points"

    id: int = Column(Integer, primary_key=True, index=True)
    company_id: int = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    # Core information
    title: str = Column(String(500), nullable=False)
    description: str = Column(Text, nullable=False)
    category: str = Column(String(100), nullable=False)  # technical, ux, business, etc.

    # Analysis data
    severity: float = Column(Float, nullable=False)  # 1.0-10.0 scale
    frequency: str = Column(String(50), nullable=False)  # rare, occasional, frequent, constant
    impact: str = Column(String(50), nullable=False)  # low, medium, high, critical

    # Source information
    source_type: str = Column(String(50), nullable=False)  # reddit, github, medium, etc.
    source_url: str = Column(String(1000), nullable=True)
    source_title: str = Column(String(500), nullable=True)
    source_author: str = Column(String(255), nullable=True)
    source_date: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    # Sentiment analysis
    sentiment_score: float = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_label: str = Column(String(20), nullable=True)  # positive, negative, neutral

    # Validation data
    user_quotes: List[str] = Column(JSON, default=list)  # Direct user quotes
    evidence_links: List[str] = Column(JSON, default=list)  # Links supporting the pain point

    # AI analysis
    ai_summary: str = Column(Text, nullable=True)  # AI-generated summary
    keywords: List[str] = Column(JSON, default=list)  # Extracted keywords
    related_topics: List[str] = Column(JSON, default=list)  # Related problem areas

    # Status and validation
    status: str = Column(String(50), default="identified")  # identified, validated, prioritized
    validation_score: float = Column(Float, default=0.0)  # Confidence in validity
    priority_rank: Optional[int] = Column(Integer, nullable=True)

    # Metadata
    tags: List[str] = Column(JSON, default=list)
    notes: str = Column(Text, nullable=True)
    researcher_notes: str = Column(Text, nullable=True)

    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="pain_points")
    product_ideas = relationship("ProductIdea", back_populates="pain_point", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of PainPoint."""
        return f"<PainPoint(id={self.id}, company_id={self.company_id}, title='{self.title[:50]}...', severity={self.severity})>"
