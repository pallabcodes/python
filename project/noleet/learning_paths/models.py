"""
Learning paths data models and database schemas.

This module defines the core data structures for learning paths,
including path definitions, steps, enrollments, and progress tracking.
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


class LearningPath(Base):
    """Learning path definition."""
    __tablename__ = 'learning_paths'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    difficulty = Column(String(20), nullable=False, default='intermediate')  # easy, medium, hard
    estimated_duration = Column(Integer)  # weeks
    total_projects = Column(Integer, default=0)
    is_community_created = Column(Boolean, default=False)
    creator_id = Column(Integer, ForeignKey('users.id'))
    upvotes = Column(Integer, default=0)
    tags = Column(JSON)  # Array of topic tags
    metadata = Column(JSON)  # Additional metadata (prerequisites, outcomes, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User")
    steps = relationship("LearningPathStep", back_populates="path", order_by="LearningPathStep.step_order")
    enrollments = relationship("UserPathEnrollment", back_populates="path")

    def __repr__(self):
        return f"<LearningPath(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"


class LearningPathStep(Base):
    """Individual step within a learning path."""
    __tablename__ = 'learning_path_steps'

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey('learning_paths.id'), nullable=False)
    step_order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey('projects.id'))  # Optional project assignment
    required_skills = Column(JSON)  # Array of required skills/topics
    estimated_time = Column(Integer)  # minutes
    prerequisites = Column(JSON)  # Complex prerequisite logic
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    path = relationship("LearningPath", back_populates="steps")
    project = relationship("Project")

    def __repr__(self):
        return f"<LearningPathStep(id={self.id}, path_id={self.path_id}, order={self.step_order}, title='{self.title}')>"


class UserPathEnrollment(Base):
    """User enrollment and progress in a learning path."""
    __tablename__ = 'user_path_enrollments'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    path_id = Column(Integer, ForeignKey('learning_paths.id'), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    current_step_id = Column(Integer, ForeignKey('learning_path_steps.id'))
    progress_percentage = Column(Float, default=0.0)
    total_time_spent = Column(Integer, default=0)  # minutes
    last_activity_at = Column(DateTime(timezone=True))
    metadata = Column(JSON)  # Additional progress data

    # Relationships
    user = relationship("User")
    path = relationship("LearningPath", back_populates="enrollments")
    current_step = relationship("LearningPathStep")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<UserPathEnrollment(user_id={self.user_id}, path_id={self.path_id}, progress={self.progress_percentage}%)>"


class PathRecommendation(Base):
    """AI-generated path recommendations for users."""
    __tablename__ = 'path_recommendations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    path_id = Column(Integer, ForeignKey('learning_paths.id'), nullable=False)
    recommendation_score = Column(Float, nullable=False)  # 0.0 to 1.0
    reasoning = Column(Text)  # AI explanation for recommendation
    recommended_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    metadata = Column(JSON)  # Additional recommendation data

    # Relationships
    user = relationship("User")
    path = relationship("LearningPath")

    def __repr__(self):
        return f"<PathRecommendation(user_id={self.user_id}, path_id={self.path_id}, score={self.recommendation_score})>"


# In-memory data structures for path processing
@dataclass
class PathStepData:
    """Data structure for path step information."""
    step_id: int
    order: int
    title: str
    description: str
    project_id: Optional[int]
    required_skills: List[str]
    estimated_time: int
    prerequisites: Dict[str, Any]
    is_completed: bool = False
    completed_at: Optional[datetime] = None


@dataclass
class PathProgressData:
    """Data structure for user path progress."""
    enrollment_id: int
    path_id: int
    current_step: Optional[int]
    progress_percentage: float
    total_time_spent: int
    last_activity: Optional[datetime]
    completed_steps: List[int]
    remaining_steps: List[int]


@dataclass
class PathRecommendationData:
    """Data structure for path recommendations."""
    path_id: int
    path_title: str
    path_description: str
    difficulty: str
    estimated_duration: int
    total_projects: int
    recommendation_score: float
    reasoning: str
    matching_topics: List[str]
    skill_gaps_addressed: List[str]


@dataclass
class LearningPathData:
    """Complete learning path data structure."""
    path_id: int
    title: str
    description: str
    difficulty: str
    estimated_duration: int
    total_projects: int
    tags: List[str]
    creator_id: Optional[int]
    is_community_created: bool
    upvotes: int
    created_at: datetime
    steps: List[PathStepData] = field(default_factory=list)
    enrolled_users_count: int = 0
    average_completion_rate: float = 0.0
    average_completion_time: int = 0  # days
