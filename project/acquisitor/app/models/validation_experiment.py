"""Validation experiment model for tracking hypothesis testing."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class ValidationExperiment(Base):
    """Validation experiment model."""

    __tablename__ = "validation_experiments"

    id = Column(Integer, primary_key=True, index=True)
    hypothesis_id = Column(Integer, ForeignKey("hypotheses.id"), nullable=False)

    # Experiment details
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    experiment_type = Column(String(100), nullable=False)  # survey, prototype, landing_page, user_interview, etc.

    # Experiment design
    methodology = Column(JSON, nullable=False)  # Detailed experiment methodology
    target_sample_size = Column(Integer, nullable=False)
    actual_sample_size = Column(Integer, nullable=True)

    # Metrics to track
    primary_metric = Column(String(200), nullable=False)  # Main success metric
    secondary_metrics = Column(JSON, nullable=True)  # Additional metrics
    baseline_value = Column(Float, nullable=True)  # Expected baseline
    target_value = Column(Float, nullable=True)  # Target to achieve

    # Status and results
    status = Column(String(50), nullable=False, default="planned")  # planned, running, completed, cancelled
    actual_result = Column(Float, nullable=True)  # Actual metric value achieved
    result_confidence = Column(Float, nullable=True)  # 0.0-1.0 confidence in result
    statistical_significance = Column(Float, nullable=True)  # p-value or significance level

    # Analysis
    results_summary = Column(Text, nullable=True)
    key_insights = Column(JSON, nullable=True)  # Key findings from experiment
    recommendations = Column(Text, nullable=True)  # What to do next

    # Outcome
    experiment_outcome = Column(String(50), nullable=True)  # validated, invalidated, inconclusive, needs_more_data
    supports_hypothesis = Column(Boolean, nullable=True)  # True if experiment supports hypothesis

    # Resources and costs
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    resources_used = Column(JSON, nullable=True)  # Tools, platforms, people involved

    # Timestamps
    planned_start_date = Column(DateTime, nullable=True)
    actual_start_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    hypothesis = relationship("Hypothesis", back_populates="validation_experiments")
    validation_results = relationship("ValidationResult", back_populates="experiment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ValidationExperiment(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"
