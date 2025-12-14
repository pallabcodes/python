"""
Peer Learning Module - Community-driven learning features for NoLeet.

This module provides three core peer learning features:

1. Code Review System - Structured peer code review process
2. Live Collaboration Sessions - Real-time pair programming and collaborative coding
3. Implementation Showcase Gallery - Community-curated gallery of outstanding implementations

Key Components:
- Data models for all peer learning entities
- Business logic engines for each feature
- TUI interfaces for user interaction
- REST API endpoints for programmatic access
- Comprehensive analytics and statistics

Architecture:
- Service-oriented design with clear separation of concerns
- Asynchronous operations for scalability
- Caching integration for performance
- Comprehensive error handling and logging
- Type-safe interfaces with Pydantic models

Usage:
    from peer_learning.peer_learning_service import PeerLearningService

    service = PeerLearningService(db_session, cache_manager)
    result = await service.submit_code_for_review(user_id, submission_data)
"""

from peer_learning.peer_learning_service import PeerLearningService
from peer_learning.models import (
    CodeSubmission, CodeReview, ReviewComment,
    CollaborationSession, SessionParticipant, SessionMessage,
    ImplementationShowcase, ShowcaseVote, ShowcaseComment,
    CodeReviewData, CollaborationSessionData, ShowcaseImplementationData,
    PeerLearningStats
)

__all__ = [
    # Main service
    'PeerLearningService',

    # Data models
    'CodeSubmission', 'CodeReview', 'ReviewComment',
    'CollaborationSession', 'SessionParticipant', 'SessionMessage',
    'ImplementationShowcase', 'ShowcaseVote', 'ShowcaseComment',

    # Data structures
    'CodeReviewData', 'CollaborationSessionData', 'ShowcaseImplementationData',
    'PeerLearningStats'
]

__version__ = "1.0.0"
