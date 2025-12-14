"""Product idea models for Acquisitor."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProductIdea(Base):
    """Product idea model for relative product concepts."""

    __tablename__ = "product_ideas"

    id: int = Column(Integer, primary_key=True, index=True)
    company_id: int = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    pain_point_id: Optional[int] = Column(Integer, ForeignKey("pain_points.id"), nullable=True, index=True)

    # Core idea
    title: str = Column(String(500), nullable=False)
    description: str = Column(Text, nullable=False)
    tagline: str = Column(String(200), nullable=True)  # Short, catchy description

    # Product details
    category: str = Column(String(100), nullable=False)  # tool, platform, service, etc.
    target_users: List[str] = Column(JSON, default=list)  # ["developers", "designers", etc.]
    key_features: List[str] = Column(JSON, default=list)  # Main features
    value_proposition: str = Column(Text, nullable=True)  # Why it matters

    # Business analysis
    market_size: str = Column(String(100), nullable=True)  # TAM estimate
    competition_level: str = Column(String(50), nullable=True)  # low, medium, high
    differentiation: str = Column(Text, nullable=True)  # How it differs

    # Acquisition potential
    acquisition_fit_score: float = Column(Float, default=0.0)  # 0-1 scale
    strategic_value: str = Column(Text, nullable=True)  # Why target company would buy
    integration_potential: str = Column(Text, nullable=True)  # How it fits their ecosystem

    # Technical feasibility
    technical_complexity: str = Column(String(50), nullable=True)  # low, medium, high
    development_effort: str = Column(String(50), nullable=True)  # weeks/months
    required_technologies: List[str] = Column(JSON, default=list)

    # MVP definition
    mvp_features: List[str] = Column(JSON, default=list)
    mvp_timeline: str = Column(String(100), nullable=True)
    success_metrics: List[str] = Column(JSON, default=list)

    # AI generation data
    ai_generated: bool = Column(JSON, default=True)
    generation_prompt: str = Column(Text, nullable=True)
    ai_confidence_score: float = Column(Float, nullable=True)

    # Status and validation
    status: str = Column(String(50), default="generated")  # generated, validated, prototyped, launched
    validation_status: str = Column(String(50), default="pending")  # pending, validated, rejected
    priority_score: float = Column(Float, default=0.0)

    # User feedback and validation
    user_feedback: List[Dict] = Column(JSON, default=list)  # [{rating, comment, user_type}]
    market_research_notes: str = Column(Text, nullable=True)

    # Metadata
    tags: List[str] = Column(JSON, default=list)
    notes: str = Column(Text, nullable=True)
    researcher: str = Column(String(255), nullable=True)

    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="product_ideas")
    hypotheses = relationship("Hypothesis", back_populates="product_idea", cascade="all, delete-orphan")
    pain_point = relationship("PainPoint", back_populates="product_ideas")
    validation_results = relationship("ValidationResult", back_populates="product_idea", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of ProductIdea."""
        return f"<ProductIdea(id={self.id}, title='{self.title[:50]}...', acquisition_fit={self.acquisition_fit_score:.2f})>"
