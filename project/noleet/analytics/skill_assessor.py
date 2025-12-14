"""
Skill assessment algorithms for NoLeet.

This module provides advanced algorithms to assess user skills based on
project completions, code quality, peer reviews, and learning patterns.
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from noleet.app.models import User, Project, UserInteraction
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SkillAssessment:
    """Comprehensive skill assessment for a user."""
    overall_level: float  # 0.0 to 1.0
    topic_breakdown: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    learning_trajectory: str  # 'beginner', 'intermediate', 'advanced', 'expert'
    confidence_score: float  # 0.0 to 1.0
    recommended_focus_areas: List[str]


@dataclass
class CodeQualityMetrics:
    """Code quality assessment metrics."""
    readability_score: float  # 0.0 to 1.0
    efficiency_score: float  # 0.0 to 1.0
    best_practices_score: float  # 0.0 to 1.0
    overall_quality: float  # 0.0 to 1.0
    improvement_areas: List[str]


class SkillAssessor:
    """Advanced skill assessment engine using multiple signals."""

    # Skill level thresholds
    SKILL_THRESHOLDS = {
        'beginner': (0.0, 0.25),
        'intermediate': (0.25, 0.60),
        'advanced': (0.60, 0.85),
        'expert': (0.85, 1.0)
    }

    # Topic difficulty weights
    TOPIC_DIFFICULTY = {
        'algorithms': 0.7,
        'data-structures': 0.8,
        'dynamic-programming': 0.9,
        'graph-theory': 0.85,
        'string-algorithms': 0.75,
        'mathematics': 0.8,
        'system-design': 0.95,
        'database': 0.7,
        'bit-manipulation': 0.6,
        'greedy': 0.65,
        'backtracking': 0.8,
        'divide-and-conquer': 0.75
    }

    def __init__(self, db_session: Session):
        self.db = db_session

    def assess_user_skills(self, user_id: int) -> SkillAssessment:
        """
        Perform comprehensive skill assessment for a user.

        Args:
            user_id: The user's ID

        Returns:
            SkillAssessment with detailed analysis
        """
        logger.info(f"Assessing skills for user {user_id}")

        # Gather multiple signals
        project_completions = self._get_project_completions(user_id)
        interaction_patterns = self._analyze_interaction_patterns(user_id)
        peer_feedback = self._get_peer_feedback(user_id)
        learning_consistency = self._calculate_learning_consistency(user_id)

        # Calculate topic-specific skills
        topic_skills = self._calculate_topic_skills(project_completions)

        # Calculate overall skill level
        overall_level = self._calculate_overall_skill_level(topic_skills)

        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(topic_skills)

        # Determine learning trajectory
        trajectory = self._determine_learning_trajectory(overall_level, learning_consistency)

        # Calculate confidence score
        confidence = self._calculate_confidence_score(project_completions, peer_feedback)

        # Recommend focus areas
        focus_areas = self._recommend_focus_areas(topic_skills, interaction_patterns)

        return SkillAssessment(
            overall_level=round(overall_level, 3),
            topic_breakdown={k: round(v, 3) for k, v in topic_skills.items()},
            strengths=strengths,
            weaknesses=weaknesses,
            learning_trajectory=trajectory,
            confidence_score=round(confidence, 3),
            recommended_focus_areas=focus_areas
        )

    def assess_code_quality(self, user_id: int, project_id: Optional[int] = None) -> CodeQualityMetrics:
        """
        Assess code quality based on peer reviews and automated analysis.

        Args:
            user_id: The user's ID
            project_id: Optional specific project to assess

        Returns:
            CodeQualityMetrics with detailed quality analysis
        """
        # This would integrate with code review system
        # For now, return placeholder metrics
        return CodeQualityMetrics(
            readability_score=0.7,
            efficiency_score=0.6,
            best_practices_score=0.8,
            overall_quality=0.7,
            improvement_areas=["Consider more descriptive variable names", "Add error handling"]
        )

    def _get_project_completions(self, user_id: int) -> List[Dict]:
        """Get detailed project completion data."""
        # Get completed projects with metadata
        completions = self.db.query(
            Project,
            UserInteraction.created_at.label('completed_at'),
            UserInteraction.metadata.label('completion_metadata')
        ).join(
            UserInteraction,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id,
                UserInteraction.user_id == user_id,
                UserInteraction.interaction_type == 'complete'
            )
        ).all()

        return [{
            'project': project,
            'completed_at': completed_at,
            'difficulty': project.difficulty,
            'topics': project.tags or [],
            'metadata': completion_metadata or {}
        } for project, completed_at, completion_metadata in completions]

    def _analyze_interaction_patterns(self, user_id: int) -> Dict:
        """Analyze user interaction patterns for skill insights."""
        # Get interaction history
        interactions = self.db.query(
            UserInteraction.interaction_type,
            UserInteraction.target_type,
            func.count(UserInteraction.id).label('count'),
            func.avg(func.extract('hour', UserInteraction.created_at)).label('avg_hour')
        ).filter(
            UserInteraction.user_id == user_id
        ).group_by(
            UserInteraction.interaction_type,
            UserInteraction.target_type
        ).all()

        patterns = {
            'total_interactions': sum(i.count for i in interactions),
            'interaction_types': {},
            'preferred_time': None,
            'consistency_score': 0.0
        }

        for interaction_type, target_type, count, avg_hour in interactions:
            key = f"{interaction_type}_{target_type}"
            patterns['interaction_types'][key] = count

        # Calculate preferred learning time
        if interactions:
            avg_hour = sum(i.avg_hour for i in interactions if i.avg_hour) / len([i for i in interactions if i.avg_hour])
            if 6 <= avg_hour < 12:
                patterns['preferred_time'] = 'morning'
            elif 12 <= avg_hour < 18:
                patterns['preferred_time'] = 'afternoon'
            elif 18 <= avg_hour < 22:
                patterns['preferred_time'] = 'evening'
            else:
                patterns['preferred_time'] = 'night'

        return patterns

    def _get_peer_feedback(self, user_id: int) -> List[Dict]:
        """Get peer feedback from code reviews and collaborations."""
        # Placeholder for peer feedback system
        # This would integrate with code review system when implemented
        return []

    def _calculate_learning_consistency(self, user_id: int) -> float:
        """Calculate learning consistency score."""
        # Analyze activity over last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)

        daily_activity = self.db.query(
            func.date(UserInteraction.created_at).label('date'),
            func.count(UserInteraction.id).label('count')
        ).filter(
            and_(
                UserInteraction.user_id == user_id,
                UserInteraction.created_at >= cutoff_date
            )
        ).group_by(func.date(UserInteraction.created_at)).all()

        if not daily_activity:
            return 0.0

        # Calculate consistency (lower variance = higher consistency)
        activity_counts = [activity.count for activity in daily_activity]
        if len(activity_counts) > 1:
            mean_activity = statistics.mean(activity_counts)
            variance = statistics.variance(activity_counts) if len(activity_counts) > 1 else 0
            consistency = 1 / (1 + variance / (mean_activity + 1))  # Normalize
        else:
            consistency = 0.5  # Neutral for single data point

        return round(consistency, 3)

    def _calculate_topic_skills(self, project_completions: List[Dict]) -> Dict[str, float]:
        """Calculate skill levels for individual topics."""
        topic_stats = {}

        # Group by topic
        for completion in project_completions:
            for topic in completion['topics']:
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        'projects': 0,
                        'total_difficulty': 0,
                        'recent_completions': 0,
                        'avg_time': []
                    }

                topic_stats[topic]['projects'] += 1
                difficulty_value = {'easy': 1, 'medium': 2, 'hard': 3}.get(completion['difficulty'], 1)
                topic_stats[topic]['total_difficulty'] += difficulty_value

                # Check if recent (last 30 days)
                if completion['completed_at'] > datetime.now() - timedelta(days=30):
                    topic_stats[topic]['recent_completions'] += 1

        # Calculate skill scores
        topic_skills = {}
        for topic, stats in topic_stats.items():
            # Base score from projects completed
            project_score = min(stats['projects'] / 10.0, 1.0)  # 10 projects = max score

            # Difficulty adjustment
            avg_difficulty = stats['total_difficulty'] / stats['projects']
            difficulty_multiplier = avg_difficulty / 2.0  # Normalize to 0-1

            # Recency bonus
            recency_bonus = min(stats['recent_completions'] / 5.0, 0.2)  # Up to 20% bonus

            # Topic difficulty adjustment
            topic_difficulty = self.TOPIC_DIFFICULTY.get(topic, 0.7)
            difficulty_adjustment = topic_difficulty * 0.3  # 30% weight

            skill_score = (project_score * 0.5 + difficulty_multiplier * 0.3 + recency_bonus) * (1 + difficulty_adjustment)
            topic_skills[topic] = min(skill_score, 1.0)

        return topic_skills

    def _calculate_overall_skill_level(self, topic_skills: Dict[str, float]) -> float:
        """Calculate overall skill level from topic skills."""
        if not topic_skills:
            return 0.0

        # Weighted average based on topic importance
        total_weight = 0
        weighted_sum = 0

        for topic, skill in topic_skills.items():
            weight = self.TOPIC_DIFFICULTY.get(topic, 0.7)
            weighted_sum += skill * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _identify_strengths_weaknesses(self, topic_skills: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """Identify user's strengths and weaknesses."""
        if not topic_skills:
            return [], []

        # Sort topics by skill level
        sorted_topics = sorted(topic_skills.items(), key=lambda x: x[1], reverse=True)

        # Top 3 strengths (skill > 0.6)
        strengths = [
            topic for topic, skill in sorted_topics[:3]
            if skill > 0.6
        ]

        # Bottom 3 weaknesses (skill < 0.4)
        weaknesses = [
            topic for topic, skill in sorted_topics[-3:]
            if skill < 0.4
        ]

        return strengths, weaknesses

    def _determine_learning_trajectory(self, overall_level: float, consistency: float) -> str:
        """Determine user's learning trajectory."""
        # Combine skill level and consistency
        trajectory_score = (overall_level * 0.7) + (consistency * 0.3)

        if trajectory_score < 0.25:
            return 'beginner'
        elif trajectory_score < 0.60:
            return 'intermediate'
        elif trajectory_score < 0.85:
            return 'advanced'
        else:
            return 'expert'

    def _calculate_confidence_score(self, project_completions: List[Dict], peer_feedback: List[Dict]) -> float:
        """Calculate confidence score for skill assessment."""
        # Base confidence from sample size
        sample_size = len(project_completions)
        base_confidence = min(sample_size / 20.0, 1.0)  # 20 projects = full confidence

        # Adjust for peer feedback
        feedback_confidence = min(len(peer_feedback) / 5.0, 0.2)  # Up to 20% bonus

        # Adjust for recency (recent activity increases confidence)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_count = sum(1 for c in project_completions if c['completed_at'] > recent_cutoff)
        recency_confidence = min(recent_count / 5.0, 0.1)  # Up to 10% bonus

        total_confidence = base_confidence + feedback_confidence + recency_confidence
        return min(total_confidence, 1.0)

    def _recommend_focus_areas(self, topic_skills: Dict[str, float], interaction_patterns: Dict) -> List[str]:
        """Recommend focus areas for improvement."""
        recommendations = []

        # Find weakest topics
        weak_topics = sorted(topic_skills.items(), key=lambda x: x[1])[:3]
        recommendations.extend([topic for topic, skill in weak_topics if skill < 0.5])

        # Consider learning patterns
        if interaction_patterns.get('preferred_time') == 'night':
            recommendations.append("Consider morning study sessions for better focus")

        if interaction_patterns.get('consistency_score', 0) < 0.5:
            recommendations.append("Focus on consistent daily practice")

        # Add high-value topics not yet explored
        unexplored_topics = [
            topic for topic in self.TOPIC_DIFFICULTY.keys()
            if topic not in topic_skills
        ]
        if unexplored_topics:
            recommendations.append(f"Explore new areas: {', '.join(unexplored_topics[:2])}")

        return recommendations[:5]  # Limit to top 5 recommendations

    def predict_skill_growth(self, user_id: int, days_ahead: int = 30) -> Dict[str, float]:
        """
        Predict skill growth over time based on current trajectory.

        Args:
            user_id: The user's ID
            days_ahead: Number of days to predict ahead

        Returns:
            Dictionary of topic -> predicted skill level
        """
        assessment = self.assess_user_skills(user_id)

        # Simple linear growth model based on current velocity
        # This could be enhanced with ML models in the future
        growth_predictions = {}

        for topic, current_skill in assessment.topic_breakdown.items():
            # Assume 5% monthly growth for active topics
            monthly_growth = 0.05
            predicted_growth = monthly_growth * (days_ahead / 30.0)
            predicted_skill = min(current_skill + predicted_growth, 1.0)
            growth_predictions[topic] = round(predicted_skill, 3)

        return growth_predictions

    def get_skill_gap_analysis(self, user_id: int, target_level: float = 0.8) -> Dict[str, Dict]:
        """
        Analyze skill gaps to reach target proficiency level.

        Args:
            user_id: The user's ID
            target_level: Target skill level (0.0 to 1.0)

        Returns:
            Analysis of projects needed to reach target levels
        """
        assessment = self.assess_user_skills(user_id)

        gap_analysis = {}

        for topic, current_skill in assessment.topic_breakdown.items():
            if current_skill < target_level:
                gap = target_level - current_skill
                # Estimate projects needed (rough heuristic)
                projects_needed = max(1, int(gap * 10))  # ~10 projects per skill level

                gap_analysis[topic] = {
                    'current_level': current_skill,
                    'target_level': target_level,
                    'gap': gap,
                    'projects_needed': projects_needed,
                    'estimated_weeks': projects_needed // 2  # 2 projects per week
                }

        return gap_analysis
