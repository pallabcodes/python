"""Validation result model for storing detailed experiment results."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class ValidationResult(Base):
    """Detailed validation result model."""

    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("validation_experiments.id"), nullable=False)

    # Result metadata
    result_type = Column(String(100), nullable=False)  # quantitative, qualitative, mixed
    data_source = Column(String(200), nullable=False)  # survey_response, user_feedback, analytics, etc.
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Quantitative data
    metric_name = Column(String(200), nullable=True)
    metric_value = Column(Float, nullable=True)
    metric_unit = Column(String(50), nullable=True)  # percentage, count, dollars, etc.
    confidence_interval_low = Column(Float, nullable=True)
    confidence_interval_high = Column(Float, nullable=True)

    # Qualitative data
    qualitative_data = Column(JSON, nullable=True)  # Themes, quotes, insights
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0

    # Demographics/context
    participant_demographics = Column(JSON, nullable=True)  # age, role, experience, etc.
    context_notes = Column(Text, nullable=True)  # Additional context

    # Raw data reference
    raw_data_location = Column(String(500), nullable=True)  # File path or external reference
    data_quality_score = Column(Float, nullable=True)  # 0.0-1.0 quality assessment

    # Analysis notes
    analyst_notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Categorization tags

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    experiment = relationship("ValidationExperiment", back_populates="validation_results")

    def __repr__(self):
        return f"<ValidationResult(id={self.id}, type='{self.result_type}', metric='{self.metric_name}')>"