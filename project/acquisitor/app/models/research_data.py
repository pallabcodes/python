"""Research data models for Acquisitor."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class ResearchData(Base):
    """Research data model for storing collected data from various sources."""

    __tablename__ = "research_data"

    id: int = Column(Integer, primary_key=True, index=True)
    company_id: int = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    # Source information
    source_type: str = Column(String(50), nullable=False, index=True)  # reddit, github, medium, etc.
    source_url: str = Column(String(1000), nullable=False, index=True)
    source_title: str = Column(String(500), nullable=True)
    source_author: str = Column(String(255), nullable=True)
    source_date: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    # Content
    content_type: str = Column(String(50), nullable=False)  # post, comment, article, issue, etc.
    title: str = Column(String(500), nullable=True)
    content: str = Column(Text, nullable=False)  # Main text content
    summary: str = Column(Text, nullable=True)  # AI-generated summary

    # Metadata
    tags: List[str] = Column(JSON, default=list)
    keywords: List[str] = Column(JSON, default=list)
    language: str = Column(String(10), default="en")

    # Engagement metrics
    upvotes: Optional[int] = Column(Integer, nullable=True)
    downvotes: Optional[int] = Column(Integer, nullable=True)
    comments_count: Optional[int] = Column(Integer, nullable=True)
    views: Optional[int] = Column(Integer, nullable=True)
    shares: Optional[int] = Column(Integer, nullable=True)

    # Sentiment and analysis
    sentiment_score: float = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_label: str = Column(String(20), nullable=True)  # positive, negative, neutral
    relevance_score: float = Column(Float, default=0.0)  # Relevance to company pain points

    # Processing status
    processed: bool = Column(JSON, default=False)
    extracted_pain_points: List[int] = Column(JSON, default=list)  # IDs of extracted pain points
    processing_errors: str = Column(Text, nullable=True)

    # AI analysis results
    entities: List[Dict] = Column(JSON, default=list)  # Named entities found
    themes: List[str] = Column(JSON, default=list)  # Identified themes
    sentiment_analysis: Dict = Column(JSON, nullable=True)  # Detailed sentiment analysis

    # Quality metrics
    content_quality_score: float = Column(Float, default=0.0)  # 0-1 scale
    spam_likelihood: float = Column(Float, default=0.0)  # 0-1 scale
    duplicate_score: float = Column(Float, default=0.0)  # Similarity to other content

    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="research_data")

    def __repr__(self) -> str:
        """String representation of ResearchData."""
        return f"<ResearchData(id={self.id}, company_id={self.company_id}, source='{self.source_type}', title='{self.title[:50] if self.title else 'N/A'}...')>"
