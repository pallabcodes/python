"""
Peer Learning data models and database schemas.

This module defines the core data structures for peer learning features:
- Code Review System
- Live Collaboration Sessions
- Implementation Showcase Gallery
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

from noleet.app.core.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


# Code Review System Models
class CodeSubmission(Base):
    """Code submission for peer review."""
    __tablename__ = 'code_submissions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    code_content = Column(Text, nullable=False)
    language = Column(String(50), default='python')
    topics = Column(JSON)  # Array of topic tags
    difficulty_level = Column(String(20))  # easy, medium, hard
    status = Column(String(20), default='draft')  # draft, submitted, in_review, approved, rejected
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    project = relationship("Project")
    reviews = relationship("CodeReview", back_populates="submission")

    def __repr__(self):
        return f"<CodeSubmission(id={self.id}, title='{self.title}', status='{self.status}')>"


class CodeReview(Base):
    """Peer code review for a submission."""
    __tablename__ = 'code_reviews'

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey('code_submissions.id'), nullable=False)
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending')  # pending, in_progress, completed
    overall_rating = Column(Integer)  # 1-5 stars
    feedback_text = Column(Text)
    feedback_categories = Column(JSON)  # readability, efficiency, best_practices, etc.
    detailed_feedback = Column(JSON)  # Structured feedback by category
    review_started_at = Column(DateTime(timezone=True))
    review_completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("CodeSubmission", back_populates="reviews")
    reviewer = relationship("User")

    def __repr__(self):
        return f"<CodeReview(id={self.id}, submission_id={self.submission_id}, rating={self.overall_rating})>"


class ReviewComment(Base):
    """Individual comments within a code review."""
    __tablename__ = 'review_comments'

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey('code_reviews.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    line_number = Column(Integer)
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(20))  # suggestion, issue, praise, question
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    review = relationship("CodeReview")
    user = relationship("User")

    def __repr__(self):
        return f"<ReviewComment(id={self.id}, review_id={self.review_id}, type='{self.comment_type}')>"


# Live Collaboration Models
class CollaborationSession(Base):
    """Live collaboration session for pair programming."""
    __tablename__ = 'collaboration_sessions'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    host_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    session_type = Column(String(20), default='pair_programming')  # pair_programming, code_review, debugging
    status = Column(String(20), default='scheduled')  # scheduled, active, completed, cancelled
    max_participants = Column(Integer, default=2)
    is_public = Column(Boolean, default=True)
    scheduled_start = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    topics = Column(JSON)
    session_metadata = Column(JSON)  # WebRTC info, recording URL, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    host = relationship("User")
    project = relationship("Project")
    participants = relationship("SessionParticipant", back_populates="session")

    def __repr__(self):
        return f"<CollaborationSession(id={self.id}, title='{self.title}', status='{self.status}')>"


class SessionParticipant(Base):
    """Participant in a collaboration session."""
    __tablename__ = 'session_participants'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('collaboration_sessions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), default='participant')  # host, participant, observer
    joined_at = Column(DateTime(timezone=True))
    left_at = Column(DateTime(timezone=True))
    participation_score = Column(Float, default=0.0)  # Engagement metric
    feedback_rating = Column(Integer)  # 1-5 rating of session
    feedback_text = Column(Text)

    # Relationships
    session = relationship("CollaborationSession", back_populates="participants")
    user = relationship("User")

    def __repr__(self):
        return f"<SessionParticipant(session_id={self.session_id}, user_id={self.user_id}, role='{self.role}')>"


class SessionMessage(Base):
    """Chat messages within a collaboration session."""
    __tablename__ = 'session_messages'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('collaboration_sessions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_type = Column(String(20), default='text')  # text, code, system, file
    message_content = Column(Text, nullable=False)
    metadata = Column(JSON)  # Code location, file info, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("CollaborationSession")
    user = relationship("User")

    def __repr__(self):
        return f"<SessionMessage(session_id={self.session_id}, user_id={self.user_id}, type='{self.message_type}')>"


# Implementation Showcase Models
class ImplementationShowcase(Base):
    """Outstanding implementation in the community showcase."""
    __tablename__ = 'implementation_showcases'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    code_content = Column(Text, nullable=False)
    language = Column(String(50), default='python')
    topics = Column(JSON)
    difficulty_level = Column(String(20))
    approach_description = Column(Text)  # How they solved it
    key_insights = Column(JSON)  # Array of key learning points
    performance_metrics = Column(JSON)  # Time/space complexity, benchmarks
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    featured = Column(Boolean, default=False)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    project = relationship("Project")
    votes = relationship("ShowcaseVote", back_populates="showcase")

    def __repr__(self):
        return f"<ImplementationShowcase(id={self.id}, title='{self.title}', upvotes={self.upvotes})>"


class ShowcaseVote(Base):
    """User votes on showcase implementations."""
    __tablename__ = 'showcase_votes'

    id = Column(Integer, primary_key=True, index=True)
    showcase_id = Column(Integer, ForeignKey('implementation_showcases.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    vote_type = Column(String(10), nullable=False)  # upvote, downvote
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    showcase = relationship("ImplementationShowcase", back_populates="votes")
    user = relationship("User")

    def __repr__(self):
        return f"<ShowcaseVote(showcase_id={self.showcase_id}, user_id={self.user_id}, type='{self.vote_type}')>"


class ShowcaseComment(Base):
    """Comments on showcase implementations."""
    __tablename__ = 'showcase_comments'

    id = Column(Integer, primary_key=True, index=True)
    showcase_id = Column(Integer, ForeignKey('implementation_showcases.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment_text = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('showcase_comments.id'))  # For threaded comments
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    showcase = relationship("ImplementationShowcase")
    user = relationship("User")
    parent_comment = relationship("ShowcaseComment", remote_side=[id])

    def __repr__(self):
        return f"<ShowcaseComment(showcase_id={self.showcase_id}, user_id={self.user_id})>"


# In-memory data structures for processing
@dataclass
class CodeReviewData:
    """Data structure for code review information."""
    review_id: int
    submission_id: int
    reviewer_id: int
    status: str
    overall_rating: Optional[int]
    feedback_text: Optional[str]
    feedback_categories: List[str]
    detailed_feedback: Dict[str, Any]
    review_started_at: Optional[datetime]
    review_completed_at: Optional[datetime]
    comments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CollaborationSessionData:
    """Data structure for collaboration session information."""
    session_id: int
    title: str
    description: Optional[str]
    host_user_id: int
    session_type: str
    status: str
    max_participants: int
    current_participants: int
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]
    topics: List[str]
    participants: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ShowcaseImplementationData:
    """Data structure for showcase implementation."""
    showcase_id: int
    user_id: int
    title: str
    description: str
    language: str
    topics: List[str]
    difficulty_level: str
    upvotes: int
    downvotes: int
    views: int
    featured: bool
    submitted_at: datetime
    user_name: str
    user_reputation: int
    approach_description: Optional[str]
    key_insights: List[str]
    performance_metrics: Dict[str, Any]


@dataclass
class PeerLearningStats:
    """Statistics for peer learning activities."""
    total_code_reviews: int
    active_collaboration_sessions: int
    showcase_implementations: int
    total_upvotes_received: int
    total_helpful_reviews: int
    collaboration_hours: float
    top_languages: List[Dict[str, int]]
    most_helpful_topics: List[Dict[str, int]]
