"""Analysis run model for DocuMind."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class AnalysisRun(Base):
    """Analysis run tracking model."""

    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)

    # Run identification
    run_id = Column(String(50), nullable=False, unique=True, index=True)
    trigger_type = Column(String(50), nullable=False)  # manual, webhook, scheduled, api
    trigger_source = Column(String(100), nullable=True)  # github, gitlab, cli, api

    # Status and progress
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    progress_percentage = Column(Float, default=0.0)  # 0.0-100.0
    current_step = Column(String(100), nullable=True)  # Current analysis step

    # Configuration
    analysis_config = Column(JSON, nullable=True)  # Analysis settings used
    target_branch = Column(String(100), default="main")
    commit_sha = Column(String(40), nullable=True)

    # Results summary
    entities_found = Column(Integer, default=0)
    entities_analyzed = Column(Integer, default=0)
    docs_generated = Column(Integer, default=0)
    docs_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Performance metrics
    duration_seconds = Column(Float, nullable=True)
    files_processed = Column(Integer, default=0)
    lines_of_code = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Metadata
    initiated_by = Column(String(100), nullable=True)  # User or system that started analysis
    environment = Column(String(50), nullable=True)   # dev, staging, prod
    version = Column(String(20), nullable=True)       # DocuMind version used

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="analysis_runs")

    def __repr__(self):
        return f"<AnalysisRun(id={self.id}, run_id='{self.run_id}', status='{self.status}', progress={self.progress_percentage}%)>"
