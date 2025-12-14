"""Repository model for DocuMind."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Repository(Base):
    """Git repository model."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)

    # Repository identification
    name = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False, unique=True, index=True)  # owner/repo
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    clone_url = Column(String(500), nullable=False)

    # Platform information
    platform = Column(String(50), nullable=False, index=True)  # github, gitlab, bitbucket
    platform_id = Column(String(100), nullable=True)  # Platform-specific ID
    owner = Column(String(255), nullable=False, index=True)
    is_private = Column(Boolean, default=False)
    is_fork = Column(Boolean, default=False)

    # Repository metadata
    default_branch = Column(String(100), default="main")
    language = Column(String(50), nullable=True, index=True)
    languages = Column(JSON, nullable=True)  # Language breakdown with percentages
    topics = Column(JSON, nullable=True)  # Repository topics/tags

    # Statistics
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    size_kb = Column(Integer, nullable=True)  # Repository size in KB

    # DocuMind-specific metadata
    is_active = Column(Boolean, default=True)  # Whether to analyze this repo
    analysis_enabled = Column(Boolean, default=True)
    webhook_active = Column(Boolean, default=False)
    last_analysis_at = Column(DateTime, nullable=True)
    last_commit_sha = Column(String(40), nullable=True)

    # Configuration
    analysis_config = Column(JSON, nullable=True)  # Custom analysis settings
    ignore_patterns = Column(JSON, nullable=True)  # Files/patterns to ignore

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    code_entities = relationship("CodeEntity", back_populates="repository", cascade="all, delete-orphan")
    documentations = relationship("Documentation", back_populates="repository", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="repository", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(id={self.id}, full_name='{self.full_name}', platform='{self.platform}')>"
