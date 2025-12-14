"""
Progress calculation engine for NoLeet learning analytics.

This module provides algorithms to calculate user skill levels, learning velocity,
and progress metrics based on project completions and interaction patterns.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from noleet.app.models import User, Project, UserInteraction, Question
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SkillLevel:
    """Represents a user's skill level in a specific topic."""
    topic: str
    level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    projects_completed: int
    total_time_spent: int  # minutes
    last_activity: Optional[datetime] = None


@dataclass
class LearningVelocity:
    """Represents learning speed and consistency."""
    topics_per_week: float
    projects_per_week: float
    consistency_score: float  # 0.0 to 1.0
    current_streak: int
    longest_streak: int


@dataclass
class ProgressMetrics:
    """Comprehensive progress metrics for a user."""
    skill_levels: Dict[str, SkillLevel]
    learning_velocity: LearningVelocity
    total_projects_completed: int
    total_questions_solved: int
    total_time_spent: int  # minutes
    current_learning_streak: int
    favorite_topics: List[str]
    recommended_difficulty: str  # 'easy', 'medium', 'hard'


class ProgressCalculator:
    """Core engine for calculating user learning progress and analytics."""

    # Difficulty multipliers for skill calculation
    DIFFICULTY_MULTIPLIERS = {
        'easy': 1.0,
        'medium': 1.5,
        'hard': 2.0
    }

    # Topic weights for skill assessment
    TOPIC_WEIGHTS = {
        'algorithms': 1.2,
        'data-structures': 1.3,
        'dynamic-programming': 1.8,
        'graph-theory': 1.7,
        'string-algorithms': 1.4,
        'mathematics': 1.6,
        'system-design': 1.9,
        'database': 1.5
    }

    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_user_progress(self, user_id: int) -> ProgressMetrics:
        """
        Calculate comprehensive progress metrics for a user.

        Args:
            user_id: The user's ID

        Returns:
            ProgressMetrics object with all calculated metrics
        """
        logger.info(f"Calculating progress for user {user_id}")

        # Get user's project completions
        project_completions = self._get_project_completions(user_id)
        question_solutions = self._get_question_solutions(user_id)
        interactions = self._get_user_interactions(user_id)

        # Calculate skill levels
        skill_levels = self._calculate_skill_levels(user_id, project_completions)

        # Calculate learning velocity
        learning_velocity = self._calculate_learning_velocity(user_id, project_completions)

        # Calculate other metrics
        total_projects = len(project_completions)
        total_questions = len(question_solutions)
        total_time = sum(p['time_spent'] for p in project_completions)

        current_streak = self._calculate_current_streak(user_id)
        favorite_topics = self._get_favorite_topics(user_id)
        recommended_difficulty = self._calculate_recommended_difficulty(skill_levels)

        return ProgressMetrics(
            skill_levels=skill_levels,
            learning_velocity=learning_velocity,
            total_projects_completed=total_projects,
            total_questions_solved=total_questions,
            total_time_spent=total_time,
            current_learning_streak=current_streak,
            favorite_topics=favorite_topics,
            recommended_difficulty=recommended_difficulty
        )

    def _get_project_completions(self, user_id: int) -> List[Dict]:
        """Get user's completed projects with metadata."""
        # Get projects where user has 'complete' interaction
        completed_projects = self.db.query(
            Project,
            UserInteraction.created_at,
            func.extract('epoch', func.now() - UserInteraction.created_at).label('days_since_completion')
        ).join(
            UserInteraction,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id,
                UserInteraction.user_id == user_id,
                UserInteraction.interaction_type == 'complete'
            )
        ).all()

        completions = []
        for project, completed_at, days_since in completed_projects:
            # Estimate time spent based on project difficulty and user interactions
            time_spent = self._estimate_time_spent(user_id, project.id, completed_at)

            completions.append({
                'project': project,
                'completed_at': completed_at,
                'time_spent': time_spent,
                'difficulty_multiplier': self.DIFFICULTY_MULTIPLIERS.get(project.difficulty, 1.0),
                'topics': project.tags or []
            })

        return completions

    def _get_question_solutions(self, user_id: int) -> List[Dict]:
        """Get user's solved questions."""
        # This would typically come from a question-solving tracking system
        # For now, return empty list as this feature might be implemented separately
        return []

    def _get_user_interactions(self, user_id: int) -> List[Dict]:
        """Get user's interaction history."""
        interactions = self.db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id
        ).order_by(UserInteraction.created_at.desc()).limit(1000).all()

        return [{
            'type': i.interaction_type,
            'target_type': i.target_type,
            'target_id': i.target_id,
            'created_at': i.created_at,
            'metadata': i.metadata or {}
        } for i in interactions]

    def _calculate_skill_levels(self, user_id: int, project_completions: List[Dict]) -> Dict[str, SkillLevel]:
        """Calculate skill levels for different topics."""
        skill_levels = {}

        # Group completions by topic
        topic_completions = {}
        for completion in project_completions:
            for topic in completion['topics']:
                if topic not in topic_completions:
                    topic_completions[topic] = []
                topic_completions[topic].append(completion)

        # Calculate skill level for each topic
        for topic, completions in topic_completions.items():
            skill_level = self._calculate_topic_skill_level(topic, completions)
            skill_levels[topic] = skill_level

        return skill_levels

    def _calculate_topic_skill_level(self, topic: str, completions: List[Dict]) -> SkillLevel:
        """Calculate skill level for a specific topic."""
        if not completions:
            return SkillLevel(
                topic=topic,
                level=0.0,
                confidence=0.0,
                projects_completed=0,
                total_time_spent=0
            )

        # Base skill calculation
        total_projects = len(completions)
        total_time = sum(c['time_spent'] for c in completions)
        avg_difficulty = sum(c['difficulty_multiplier'] for c in completions) / len(completions)

        # Apply topic weight
        topic_weight = self.TOPIC_WEIGHTS.get(topic, 1.0)

        # Calculate raw skill score
        # Projects completed * difficulty * topic weight / time efficiency
        time_efficiency = min(total_time / (total_projects * 60), 10)  # Cap at 10 hours per project
        raw_score = (total_projects * avg_difficulty * topic_weight) / time_efficiency

        # Normalize to 0-1 scale with diminishing returns
        skill_level = 1 - math.exp(-raw_score / 5.0)

        # Calculate confidence based on sample size
        confidence = min(total_projects / 5.0, 1.0)  # 5 projects for full confidence

        # Get last activity
        last_completion = max(c['completed_at'] for c in completions)

        return SkillLevel(
            topic=topic,
            level=round(skill_level, 3),
            confidence=round(confidence, 3),
            projects_completed=total_projects,
            total_time_spent=total_time,
            last_activity=last_completion
        )

    def _calculate_learning_velocity(self, user_id: int, project_completions: List[Dict]) -> LearningVelocity:
        """Calculate learning velocity metrics."""
        if not project_completions:
            return LearningVelocity(0.0, 0.0, 0.0, 0, 0)

        # Get recent activity (last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        recent_completions = [
            c for c in project_completions
            if c['completed_at'] > cutoff_date
        ]

        if not recent_completions:
            return LearningVelocity(0.0, 0.0, 0.0, 0, 0)

        # Calculate rates
        days_span = 90
        projects_per_week = len(recent_completions) / (days_span / 7)

        # Calculate topic diversity
        all_topics = set()
        for completion in recent_completions:
            all_topics.update(completion['topics'])
        topics_per_week = len(all_topics) / (days_span / 7)

        # Calculate consistency (projects per week variance)
        weekly_counts = {}
        for completion in recent_completions:
            week = completion['completed_at'].isocalendar()[1]
            weekly_counts[week] = weekly_counts.get(week, 0) + 1

        if weekly_counts:
            avg_weekly = sum(weekly_counts.values()) / len(weekly_counts)
            variance = sum((count - avg_weekly) ** 2 for count in weekly_counts.values()) / len(weekly_counts)
            consistency_score = 1 / (1 + variance)  # Lower variance = higher consistency
        else:
            consistency_score = 0.0

        # Calculate streaks
        current_streak = self._calculate_current_streak(user_id)
        longest_streak = self._calculate_longest_streak(user_id)

        return LearningVelocity(
            topics_per_week=round(topics_per_week, 2),
            projects_per_week=round(projects_per_week, 2),
            consistency_score=round(consistency_score, 3),
            current_streak=current_streak,
            longest_streak=longest_streak
        )

    def _calculate_current_streak(self, user_id: int) -> int:
        """Calculate current learning streak in days."""
        # Get recent activity
        recent_activity = self.db.query(
            func.date(UserInteraction.created_at)
        ).filter(
            and_(
                UserInteraction.user_id == user_id,
                UserInteraction.created_at >= datetime.now() - timedelta(days=60)
            )
        ).distinct().order_by(func.date(UserInteraction.created_at).desc()).limit(30).all()

        active_dates = {date[0] for date in recent_activity}
        current_date = datetime.now().date()
        streak = 0

        # Count consecutive days backwards from today
        for i in range(60):
            check_date = current_date - timedelta(days=i)
            if check_date in active_dates:
                streak += 1
            else:
                break

        return streak

    def _calculate_longest_streak(self, user_id: int) -> int:
        """Calculate longest learning streak ever."""
        # This would require historical streak tracking
        # For now, return current streak as approximation
        return self._calculate_current_streak(user_id)

    def _get_favorite_topics(self, user_id: int) -> List[str]:
        """Get user's favorite topics based on activity."""
        # Count topic frequency in recent projects
        topic_counts = {}
        cutoff_date = datetime.now() - timedelta(days=90)

        recent_projects = self.db.query(Project).join(
            UserInteraction,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id,
                UserInteraction.user_id == user_id,
                UserInteraction.interaction_type.in_(['complete', 'like', 'view']),
                UserInteraction.created_at >= cutoff_date
            )
        ).all()

        for project in recent_projects:
            for topic in (project.tags or []):
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Return top 5 topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:5]]

    def _calculate_recommended_difficulty(self, skill_levels: Dict[str, SkillLevel]) -> str:
        """Calculate recommended difficulty level for user."""
        if not skill_levels:
            return 'easy'

        avg_skill_level = sum(sl.level for sl in skill_levels.values()) / len(skill_levels)

        if avg_skill_level < 0.3:
            return 'easy'
        elif avg_skill_level < 0.7:
            return 'medium'
        else:
            return 'hard'

    def _estimate_time_spent(self, user_id: int, project_id: int, completion_date: datetime) -> int:
        """Estimate time spent on a project."""
        # Count interactions with this project around completion time
        interactions = self.db.query(UserInteraction).filter(
            and_(
                UserInteraction.user_id == user_id,
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == project_id,
                UserInteraction.created_at >= completion_date - timedelta(hours=24),
                UserInteraction.created_at <= completion_date + timedelta(hours=1)
            )
        ).count()

        # Estimate 15-30 minutes per interaction
        base_time = interactions * 20  # 20 minutes average per interaction

        # Add project complexity factor
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project:
            difficulty_multiplier = self.DIFFICULTY_MULTIPLIERS.get(project.difficulty, 1.0)
            base_time = int(base_time * difficulty_multiplier)

        return max(base_time, 30)  # Minimum 30 minutes

    def predict_completion_time(self, user_id: int, project_id: int) -> int:
        """
        Predict how long it will take a user to complete a project.

        Args:
            user_id: The user's ID
            project_id: The project's ID

        Returns:
            Predicted completion time in minutes
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return 60  # Default 1 hour

        # Get user's skill in relevant topics
        user_progress = self.calculate_user_progress(user_id)
        relevant_skills = [
            skill for topic, skill in user_progress.skill_levels.items()
            if topic in (project.tags or [])
        ]

        if relevant_skills:
            avg_skill = sum(s.level for s in relevant_skills) / len(relevant_skills)
            # Higher skill = faster completion
            skill_factor = 2.0 - avg_skill  # 1.0 for expert, 2.0 for beginner
        else:
            skill_factor = 1.5  # Default for unknown topics

        # Base time based on difficulty
        difficulty_base = {
            'easy': 45,
            'medium': 90,
            'hard': 180
        }.get(project.difficulty, 90)

        # Adjust for user's learning velocity
        velocity_factor = 1.0
        if user_progress.learning_velocity.projects_per_week > 0:
            # Faster learners complete projects quicker
            velocity_factor = 1.0 / (1.0 + user_progress.learning_velocity.projects_per_week / 7.0)

        predicted_time = int(difficulty_base * skill_factor * velocity_factor)
        return max(predicted_time, 30)  # Minimum 30 minutes
