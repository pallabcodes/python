"""
AI-powered Learning Path Recommender System.

This module provides intelligent path recommendations based on user skills,
learning patterns, and goals using machine learning and rule-based algorithms.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from learning_paths.path_engine import PathEngine
from learning_paths.models import LearningPath, UserPathEnrollment, PathRecommendationData
from noleet.analytics.skill_assessor import SkillAssessor, SkillAssessment
from noleet.analytics.progress_calculator import ProgressCalculator, ProgressMetrics
from noleet.llm.llm_factory import LLMFactory
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


@dataclass
class RecommendationContext:
    """Context data for making path recommendations."""
    user_skills: SkillAssessment
    user_progress: ProgressMetrics
    enrolled_paths: List[int]
    completed_paths: List[int]
    learning_velocity: float
    preferred_difficulty: str
    favorite_topics: List[str]
    time_available_per_week: int  # minutes


class PathRecommender:
    """AI-powered learning path recommendation engine."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager
        self.path_engine = PathEngine(db_session, cache_manager)
        self.skill_assessor = SkillAssessor(db_session)
        self.progress_calc = ProgressCalculator(db_session)
        self.llm_factory = LLMFactory()

        # Recommendation weights
        self.WEIGHTS = {
            'skill_match': 0.25,
            'difficulty_appropriateness': 0.20,
            'topic_relevance': 0.20,
            'learning_pace_match': 0.15,
            'community_rating': 0.10,
            'completion_probability': 0.10
        }

    async def get_recommendations(self, user_id: int, limit: int = 5,
                                context: Optional[RecommendationContext] = None) -> List[PathRecommendationData]:
        """
        Get personalized path recommendations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            context: Pre-computed context (optional)

        Returns:
            List of PathRecommendationData objects
        """
        logger.info(f"Generating path recommendations for user {user_id}")

        # Build or use provided context
        if context is None:
            context = await self._build_recommendation_context(user_id)

        # Get candidate paths
        candidate_paths = await self._get_candidate_paths(context)

        # Score and rank paths
        scored_paths = []
        for path in candidate_paths:
            score, reasoning = await self._calculate_recommendation_score(context, path)
            if score > 0.3:  # Minimum threshold
                path_data = await self.path_engine.get_path(path.id)
                if path_data:
                    recommendation = PathRecommendationData(
                        path_id=path.id,
                        path_title=path.title,
                        path_description=path.description,
                        difficulty=path.difficulty,
                        estimated_duration=path.estimated_duration,
                        total_projects=path.total_projects,
                        recommendation_score=round(score, 3),
                        reasoning=reasoning,
                        matching_topics=self._find_matching_topics(context.favorite_topics, path.tags or []),
                        skill_gaps_addressed=self._identify_skill_gaps(context.user_skills, path)
                    )
                    scored_paths.append((score, recommendation))

        # Sort by score and return top recommendations
        scored_paths.sort(key=lambda x: x[0], reverse=True)
        recommendations = [rec for _, rec in scored_paths[:limit]]

        logger.info(f"Generated {len(recommendations)} path recommendations for user {user_id}")
        return recommendations

    async def _build_recommendation_context(self, user_id: int) -> RecommendationContext:
        """Build comprehensive context for making recommendations."""
        # Get user analytics data
        user_skills = self.skill_assessor.assess_user_skills(user_id)
        user_progress = self.progress_calc.calculate_user_progress(user_id)

        # Get enrollment data
        enrollments = self.db.query(UserPathEnrollment).filter(
            UserPathEnrollment.user_id == user_id
        ).all()

        enrolled_paths = [e.path_id for e in enrollments]
        completed_paths = [e.path_id for e in enrollments if e.completed_at is not None]

        # Determine learning velocity and preferences
        learning_velocity = user_progress.learning_velocity.projects_per_week
        preferred_difficulty = self._infer_preferred_difficulty(user_progress, user_skills)
        favorite_topics = user_progress.favorite_topics
        time_available = self._estimate_time_availability(user_progress)

        return RecommendationContext(
            user_skills=user_skills,
            user_progress=user_progress,
            enrolled_paths=enrolled_paths,
            completed_paths=completed_paths,
            learning_velocity=learning_velocity,
            preferred_difficulty=preferred_difficulty,
            favorite_topics=favorite_topics,
            time_available_per_week=time_available
        )

    async def _get_candidate_paths(self, context: RecommendationContext) -> List[LearningPath]:
        """Get candidate paths for recommendation."""
        # Start with community-created paths
        query = self.db.query(LearningPath).filter(
            LearningPath.is_community_created == True
        )

        # Exclude already enrolled paths
        if context.enrolled_paths:
            query = query.filter(~LearningPath.id.in_(context.enrolled_paths))

        # Prioritize paths matching user's skill level and interests
        paths = query.all()

        # Filter and rank candidates
        candidates = []
        for path in paths:
            # Basic filtering
            if self._is_path_suitable(context, path):
                candidates.append(path)

        # Limit to top 20 candidates for scoring
        return candidates[:20]

    def _is_path_suitable(self, context: RecommendationContext, path: LearningPath) -> bool:
        """Check if a path is suitable for the user."""
        # Skip if difficulty gap is too large
        difficulty_levels = {'easy': 1, 'medium': 2, 'hard': 3}
        user_level = context.user_skills.overall_level
        path_level = difficulty_levels.get(path.difficulty, 2) / 3.0  # Normalize to 0-1

        difficulty_gap = abs(user_level - path_level)

        # Allow larger gaps for advanced users, smaller for beginners
        max_gap = 0.6 if user_level > 0.7 else 0.4 if user_level > 0.4 else 0.3

        if difficulty_gap > max_gap:
            return False

        # Check topic relevance
        path_topics = set(path.tags or [])
        user_topics = set(context.favorite_topics)

        if not path_topics.intersection(user_topics) and len(path_topics) > 0:
            # Some topic overlap required unless it's a discovery path
            return False

        return True

    async def _calculate_recommendation_score(self, context: RecommendationContext,
                                           path: LearningPath) -> Tuple[float, str]:
        """
        Calculate comprehensive recommendation score for a path.

        Returns:
            Tuple of (score, reasoning)
        """
        scores = {}
        reasons = []

        # Skill match score
        skill_score = self._calculate_skill_match(context.user_skills, path)
        scores['skill_match'] = skill_score
        reasons.append(f"Skills match: {skill_score:.2f}")

        # Difficulty appropriateness
        difficulty_score = self._calculate_difficulty_appropriateness(context.user_skills.overall_level, path.difficulty)
        scores['difficulty_appropriateness'] = difficulty_score
        reasons.append(f"Difficulty fit: {difficulty_score:.2f}")

        # Topic relevance
        topic_score = self._calculate_topic_relevance(context.favorite_topics, path.tags or [])
        scores['topic_relevance'] = topic_score
        reasons.append(f"Topic relevance: {topic_score:.2f}")

        # Learning pace match
        pace_score = self._calculate_learning_pace_match(context.learning_velocity, path)
        scores['learning_pace_match'] = pace_score
        reasons.append(f"Pace match: {pace_score:.2f}")

        # Community rating
        rating_score = min(path.upvotes / 10.0, 1.0)  # Normalize upvotes
        scores['community_rating'] = rating_score
        reasons.append(f"Community rating: {rating_score:.2f}")

        # Completion probability
        completion_score = self._estimate_completion_probability(context, path)
        scores['completion_probability'] = completion_score
        reasons.append(f"Completion likelihood: {completion_score:.2f}")

        # Calculate weighted total score
        total_score = sum(scores[metric] * self.WEIGHTS[metric] for metric in scores)

        # Generate AI-enhanced reasoning
        ai_reasoning = await self._generate_ai_reasoning(context, path, scores)

        detailed_reasoning = f"{ai_reasoning} Score breakdown: {'; '.join(reasons)}. Total: {total_score:.2f}"

        return total_score, detailed_reasoning

    def _calculate_skill_match(self, user_skills: SkillAssessment, path: LearningPath) -> float:
        """Calculate how well path matches user's skill profile."""
        path_topics = set(path.tags or [])

        # Check topic overlap with user strengths
        strength_overlap = len(path_topics.intersection(set(user_skills.strengths)))
        strength_score = strength_overlap / max(len(path_topics), 1)

        # Check if path addresses weaknesses (good for growth)
        weakness_overlap = len(path_topics.intersection(set(user_skills.weaknesses)))
        weakness_score = weakness_overlap / max(len(user_skills.weaknesses), 1)

        # Balance strength utilization with growth opportunities
        return (strength_score * 0.6) + (weakness_score * 0.4)

    def _calculate_difficulty_appropriateness(self, user_level: float, path_difficulty: str) -> float:
        """Calculate how appropriate the path difficulty is."""
        difficulty_levels = {'easy': 0.3, 'medium': 0.6, 'hard': 0.9}
        target_level = difficulty_levels.get(path_difficulty, 0.6)

        # Perfect match at user's level
        if abs(user_level - target_level) < 0.1:
            return 1.0

        # Allow slight challenges or reviews
        gap = abs(user_level - target_level)
        return max(0, 1.0 - gap * 2)  # More forgiving than strict matching

    def _calculate_topic_relevance(self, user_topics: List[str], path_topics: List[str]) -> float:
        """Calculate topic relevance based on overlap."""
        if not user_topics or not path_topics:
            return 0.0

        user_set = set(user_topics)
        path_set = set(path_topics)

        overlap = len(user_set.intersection(path_set))
        union = len(user_set.union(path_set))

        return overlap / union if union > 0 else 0.0

    def _calculate_learning_pace_match(self, user_velocity: float, path: LearningPath) -> float:
        """Calculate how well path matches user's learning pace."""
        # Estimate path duration in weeks
        estimated_weeks = path.estimated_duration or 4  # Default 4 weeks

        # Calculate required pace (projects per week)
        required_pace = path.total_projects / max(estimated_weeks, 1)

        # Compare with user velocity
        if user_velocity <= 0:
            # New learner, match to conservative pace
            return 1.0 if required_pace <= 2 else 0.5

        # Calculate pace match
        pace_ratio = user_velocity / required_pace

        # Ideal ratio is 0.8-1.2 (slightly challenging but achievable)
        if 0.8 <= pace_ratio <= 1.2:
            return 1.0
        elif 0.5 <= pace_ratio <= 1.5:
            return 0.7
        else:
            return 0.3

    def _estimate_completion_probability(self, context: RecommendationContext, path: LearningPath) -> float:
        """Estimate probability of user completing the path."""
        base_probability = 0.5  # Base completion rate

        # Adjust based on skill level match
        skill_match = self._calculate_skill_match(context.user_skills, path)
        base_probability += skill_match * 0.2

        # Adjust based on difficulty appropriateness
        difficulty_match = self._calculate_difficulty_appropriateness(
            context.user_skills.overall_level, path.difficulty
        )
        base_probability += difficulty_match * 0.15

        # Adjust based on learning consistency
        consistency = context.user_progress.learning_velocity.consistency_score
        base_probability += consistency * 0.1

        # Adjust based on time availability
        time_match = self._calculate_time_match(context.time_available_per_week, path)
        base_probability += time_match * 0.05

        return min(base_probability, 0.95)  # Cap at 95%

    def _calculate_time_match(self, available_time: int, path: LearningPath) -> float:
        """Calculate if user has time for the path."""
        # Estimate weekly time requirement
        total_time = sum(step.estimated_time for step in path.steps) if path.steps else 240  # Default 4 hours
        weekly_requirement = total_time / max(path.estimated_duration or 4, 1)

        if available_time >= weekly_requirement:
            return 1.0
        elif available_time >= weekly_requirement * 0.7:
            return 0.7
        else:
            return available_time / weekly_requirement

    async def _generate_ai_reasoning(self, context: RecommendationContext, path: LearningPath,
                                   scores: Dict[str, float]) -> str:
        """Generate AI-enhanced reasoning for recommendation."""
        try:
            prompt = f"""
            Based on user profile and path details, explain why this learning path would be beneficial:

            User Profile:
            - Skill Level: {context.user_skills.overall_level:.1%}
            - Strengths: {', '.join(context.user_skills.strengths[:3])}
            - Weaknesses: {', '.join(context.user_skills.weaknesses[:3])}
            - Favorite Topics: {', '.join(context.favorite_topics[:3])}
            - Learning Pace: {context.learning_velocity:.1f} projects/week

            Path Details:
            - Title: {path.title}
            - Difficulty: {path.difficulty}
            - Topics: {', '.join(path.tags or [])}
            - Duration: {path.estimated_duration or 4} weeks

            Provide a concise, personalized explanation (2-3 sentences) of why this path is recommended.
            """

            llm = await self.llm_factory.create_llm()
            response = await llm.agenerate([{"role": "user", "content": prompt}])
            return response.content.strip()

        except Exception as e:
            logger.error(f"AI reasoning failed: {e}")
            return f"This {path.difficulty} path covers relevant topics and matches your learning pace."

    def _find_matching_topics(self, user_topics: List[str], path_topics: List[str]) -> List[str]:
        """Find overlapping topics between user preferences and path."""
        user_set = set(user_topics)
        path_set = set(path_topics)
        return list(user_set.intersection(path_set))

    def _identify_skill_gaps(self, user_skills: SkillAssessment, path: LearningPath) -> List[str]:
        """Identify skill gaps this path would help address."""
        gaps = []
        path_topics = set(path.tags or [])

        # Check if path addresses user weaknesses
        weakness_overlap = path_topics.intersection(set(user_skills.weaknesses))
        if weakness_overlap:
            gaps.extend([f"Strengthen {weakness}" for weakness in weakness_overlap])

        # Check difficulty progression
        if path.difficulty == 'hard' and user_skills.overall_level < 0.6:
            gaps.append("Build confidence with challenging projects")
        elif path.difficulty == 'easy' and user_skills.overall_level > 0.8:
            gaps.append("Apply advanced skills to fundamental concepts")

        return gaps

    def _infer_preferred_difficulty(self, progress: ProgressMetrics, skills: SkillAssessment) -> str:
        """Infer user's preferred difficulty level."""
        # Base on skill level
        if skills.overall_level < 0.4:
            return 'easy'
        elif skills.overall_level < 0.75:
            return 'medium'
        else:
            return 'hard'

    def _estimate_time_availability(self, progress: ProgressMetrics) -> int:
        """Estimate user's weekly time availability."""
        # Base estimate on recent activity
        recent_time = progress.total_time_spent

        # Assume current pace indicates availability
        weekly_time = (recent_time / max(progress.learning_velocity.projects_per_week, 0.5)) * 60  # Convert to minutes

        # Reasonable bounds
        return max(60, min(int(weekly_time), 600))  # 1-10 hours per week

    async def get_path_success_prediction(self, user_id: int, path_id: int) -> Dict[str, Any]:
        """
        Predict user's success probability for a specific path.

        Args:
            user_id: User ID
            path_id: Path ID

        Returns:
            Success prediction with factors and recommendations
        """
        context = await self._build_recommendation_context(user_id)
        path = self.db.query(LearningPath).filter(LearningPath.id == path_id).first()

        if not path:
            return {'error': 'Path not found'}

        completion_prob = self._estimate_completion_probability(context, path)
        time_match = self._calculate_time_match(context.time_available_per_week, path)

        factors = {
            'skill_match': self._calculate_skill_match(context.user_skills, path),
            'difficulty_fit': self._calculate_difficulty_appropriateness(context.user_skills.overall_level, path.difficulty),
            'time_availability': time_match,
            'learning_consistency': context.user_progress.learning_velocity.consistency_score
        }

        recommendations = []
        if completion_prob < 0.6:
            recommendations.append("Consider starting with an easier path to build confidence")
        if time_match < 0.7:
            recommendations.append("You may need more time per week for this path")
        if factors['skill_match'] < 0.5:
            recommendations.append("This path covers different topics than your current focus")

        return {
            'path_id': path_id,
            'completion_probability': round(completion_prob, 3),
            'estimated_completion_time_weeks': path.estimated_duration or 4,
            'success_factors': {k: round(v, 3) for k, v in factors.items()},
            'recommendations': recommendations,
            'overall_assessment': 'high' if completion_prob > 0.8 else 'medium' if completion_prob > 0.6 else 'low'
        }
