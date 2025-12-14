"""Integration model for DocuMind."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Integration(Base):
    """External service integration model."""

    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=True, index=True)  # Null for org-level integrations

    # Integration details
    service_type = Column(String(50), nullable=False, index=True)  # github, gitlab, slack, etc.
    service_name = Column(String(100), nullable=False)  # Display name
    external_id = Column(String(100), nullable=True)   # Service-specific ID

    # Authentication
    auth_type = Column(String(20), nullable=False)     # oauth, token, webhook
    access_token = Column(Text, nullable=True)         # Encrypted access token
    refresh_token = Column(Text, nullable=True)        # Encrypted refresh token
    token_expires_at = Column(DateTime, nullable=True)

    # Configuration
    config = Column(JSON, nullable=True)               # Service-specific configuration
    webhook_url = Column(String(500), nullable=True)   # Webhook endpoint URL
    webhook_secret = Column(String(100), nullable=True)  # Webhook verification secret

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)       # Whether integration is verified/working
    last_sync_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)

    # Permissions and scope
    permissions = Column(JSON, nullable=True)          # Granted permissions
    scope = Column(JSON, nullable=True)                # Integration scope

    # Metadata
    owner_id = Column(String(100), nullable=True)      # User/system that owns this integration
    tags = Column(JSON, nullable=True)                 # Custom tags

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="integrations")

    def __repr__(self):
        return f"<Integration(id={self.id}, service='{self.service_type}', name='{self.service_name}', active={self.is_active})>"
