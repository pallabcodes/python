"""Hypothesis model for tracking product hypotheses."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class Hypothesis(Base):
    """Product hypothesis model."""

    __tablename__ = "hypotheses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    product_idea_id = Column(Integer, ForeignKey("product_ideas.id"), nullable=True)

    # Hypothesis details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    hypothesis_statement = Column(Text, nullable=False)  # "If X, then Y will happen"

    # Hypothesis components
    assumption = Column(Text, nullable=False)  # The core assumption
    expected_outcome = Column(Text, nullable=False)  # What we expect to happen
    success_criteria = Column(JSON, nullable=False)  # Metrics for success

    # Metadata
    category = Column(String(100), nullable=False)  # product, market, technical, etc.
    priority = Column(String(20), nullable=False, default="medium")  # critical, high, medium, low
    confidence_level = Column(Float, nullable=False, default=0.5)  # 0.0-1.0

    # Status tracking
    status = Column(String(50), nullable=False, default="proposed")  # proposed, testing, validated, invalidated, paused
    validation_method = Column(String(100), nullable=True)  # survey, prototype, landing_page, etc.

    # Validation results
    validation_score = Column(Float, nullable=True)  # 0.0-1.0 overall validation score
    key_findings = Column(JSON, nullable=True)  # List of key findings
    lessons_learned = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="hypotheses")
    product_idea = relationship("ProductIdea", back_populates="hypotheses")
    validation_experiments = relationship("ValidationExperiment", back_populates="hypothesis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Hypothesis(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"
