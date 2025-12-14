"""Documentation model for DocuMind."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Documentation(Base):
    """Generated documentation model."""

    __tablename__ = "documentations"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    code_entity_id = Column(Integer, ForeignKey("code_entities.id"), nullable=True, index=True)

    # Documentation content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Main documentation content
    summary = Column(Text, nullable=True)  # Short summary
    description = Column(Text, nullable=True)  # Detailed description

    # Structured documentation
    sections = Column(JSON, nullable=True)  # {"parameters": [...], "returns": [...], "examples": [...]}
    parameters = Column(JSON, nullable=True)  # Parameter documentation
    returns = Column(JSON, nullable=True)   # Return value documentation
    raises = Column(JSON, nullable=True)    # Exceptions/errors documentation
    examples = Column(JSON, nullable=True)  # Code examples
    notes = Column(JSON, nullable=True)     # Additional notes/warnings

    # Metadata
    doc_type = Column(String(50), nullable=False, index=True)  # api, guide, tutorial, reference
    format = Column(String(20), default="markdown")  # markdown, html, plaintext
    language = Column(String(50), nullable=True)   # Programming language
    version = Column(String(20), nullable=True)    # API version, etc.

    # Generation info
    generated_by = Column(String(50), nullable=True)  # 'ai', 'template', 'manual'
    generation_model = Column(String(100), nullable=True)  # GPT-4, Claude, etc.
    generation_prompt = Column(Text, nullable=True)   # Prompt used for generation

    # Quality metrics
    quality_score = Column(Float, nullable=True)     # 0.0-1.0 overall quality
    completeness_score = Column(Float, nullable=True)  # How complete the docs are
    accuracy_score = Column(Float, nullable=True)    # How accurate the docs are
    readability_score = Column(Float, nullable=True)  # How readable the docs are

    # Status
    status = Column(String(20), default="draft", index=True)  # draft, published, archived
    is_auto_generated = Column(String(10), default="True")    # True if AI-generated
    needs_review = Column(String(10), default="False")       # True if needs human review

    # Version control
    commit_sha = Column(String(40), nullable=True)    # Git commit this docs corresponds to
    previous_version_id = Column(Integer, ForeignKey("documentations.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    repository = relationship("Repository", back_populates="documentations")
    code_entity = relationship("CodeEntity", back_populates="documentation")

    def __repr__(self):
        return f"<Documentation(id={self.id}, title='{self.title[:50]}...', type='{self.doc_type}', status='{self.status}')>"
