"""Code entity model for DocuMind."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class CodeEntity(Base):
    """Code entity model (functions, classes, modules, etc.)."""

    __tablename__ = "code_entities"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)

    # Entity identification
    entity_type = Column(String(50), nullable=False, index=True)  # function, class, module, method, etc.
    name = Column(String(255), nullable=False, index=True)
    qualified_name = Column(String(500), nullable=False)  # Full path (module.Class.method)
    file_path = Column(String(500), nullable=False, index=True)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=True)
    start_column = Column(Integer, nullable=True)
    end_column = Column(Integer, nullable=True)

    # Code content
    source_code = Column(Text, nullable=True)  # Raw source code
    signature = Column(String(1000), nullable=True)  # Function signature or class declaration
    docstring = Column(Text, nullable=True)  # Existing docstring

    # Analysis results
    language = Column(String(50), nullable=False, index=True)
    complexity_score = Column(Float, nullable=True)  # Cyclomatic complexity
    parameter_count = Column(Integer, nullable=True)
    return_type = Column(String(100), nullable=True)
    is_async = Column(String(10), nullable=True)  # True, False, or None

    # Dependencies and relationships
    dependencies = Column(JSON, nullable=True)  # Functions/classes this entity depends on
    dependents = Column(JSON, nullable=True)   # Entities that depend on this one
    inheritance = Column(JSON, nullable=True)  # For classes: parent classes

    # Metadata
    visibility = Column(String(20), nullable=True)  # public, private, protected
    decorators = Column(JSON, nullable=True)  # Python decorators, Java annotations, etc.
    tags = Column(JSON, nullable=True)  # Custom tags for categorization

    # Analysis metadata
    last_analyzed_at = Column(DateTime, nullable=True)
    analysis_version = Column(String(20), nullable=True)  # Version of analysis that created this

    # Documentation status
    has_documentation = Column(String(10), nullable=True)  # True, False, or None
    documentation_quality = Column(Float, nullable=True)  # 0.0-1.0 quality score
    needs_update = Column(String(10), nullable=True)  # True if code changed since docs

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="code_entities")
    documentation = relationship("Documentation", back_populates="code_entity", uselist=False)

    def __repr__(self):
        return f"<CodeEntity(id={self.id}, name='{self.name}', type='{self.entity_type}', file='{self.file_path}')>"
