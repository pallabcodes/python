"""
Analytics service providing API endpoints for dashboard data.

This module provides the main service layer for analytics, combining
progress calculation, skill assessment, community analytics, and AI insights.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from noleet.analytics.progress_calculator import ProgressCalculator
from noleet.analytics.skill_assessor import SkillAssessor, SkillAssessment
from noleet.analytics.community_analytics import CommunityAnalytics
from noleet.analytics.insights_engine import InsightsEngine, PersonalizedInsights
from noleet.app.core.logging import get_logger
from noleet.app.core.caching import CacheManager

logger = get_logger(__name__)


class AnalyticsService:
    """Main analytics service coordinating all analytics functionality."""

    def __init__(self, db_session: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db_session
        self.cache = cache_manager

        # Initialize analytics engines
        self.progress_calc = ProgressCalculator(db_session)
        self.skill_assessor = SkillAssessor(db_session)
        self.community_analytics = CommunityAnalytics(db_session)
        self.insights_engine = InsightsEngine(db_session)

        # Cache TTL settings (in seconds)
        self.CACHE_TTL = {
            'user_progress': 300,      # 5 minutes
            'user_skills': 600,        # 10 minutes
            'community_overview': 1800,  # 30 minutes
            'user_insights': 3600,     # 1 hour
            'topic_analytics': 1800,   # 30 minutes
        }

    async def get_user_dashboard(self, user_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get complete dashboard data for a user.

        Args:
            user_id: The user's ID
            force_refresh: Whether to bypass cache

        Returns:
            Complete dashboard data dictionary
        """
        cache_key = f"user_dashboard:{user_id}"

        # Check cache first (unless force refresh)
        if not force_refresh and self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached dashboard data for user {user_id}")
                return cached_data

        logger.info(f"Generating fresh dashboard data for user {user_id}")

        try:
            # Gather all dashboard data concurrently
            progress_task = asyncio.create_task(self._get_progress_data(user_id))
            skills_task = asyncio.create_task(self._get_skills_data(user_id))
            community_task = asyncio.create_task(self._get_community_overview())
            insights_task = asyncio.create_task(self._get_insights_data(user_id))

            # Wait for all tasks to complete
            progress_data, skills_data, community_data, insights_data = await asyncio.gather(
                progress_task, skills_task, community_task, insights_task
            )

            # Structure the dashboard data
            dashboard_data = {
                'user_id': user_id,
                'generated_at': datetime.now().isoformat(),
                'progress': self._serialize_progress_data(progress_data),
                'skills': self._serialize_skills_data(skills_data),
                'community': community_data,
                'insights': self._serialize_insights_data(insights_data),
                'summary': self._generate_dashboard_summary(progress_data, skills_data, insights_data)
            }

            # Cache the result
            if self.cache:
                await self.cache.set(cache_key, dashboard_data, ttl=self.CACHE_TTL['user_progress'])

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to generate dashboard for user {user_id}: {e}")
            # Return minimal error response
            return {
                'user_id': user_id,
                'error': 'Failed to generate dashboard data',
                'generated_at': datetime.now().isoformat()
            }

    async def get_user_progress(self, user_id: int) -> Dict[str, Any]:
        """Get user's learning progress data."""
        cache_key = f"user_progress:{user_id}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        progress_data = self.progress_calc.calculate_user_progress(user_id)
        serialized = self._serialize_progress_data(progress_data)

        if self.cache:
            await self.cache.set(cache_key, serialized, ttl=self.CACHE_TTL['user_progress'])

        return serialized

    async def get_user_skills(self, user_id: int) -> Dict[str, Any]:
        """Get user's skill assessment data."""
        cache_key = f"user_skills:{user_id}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        skills_data = self.skill_assessor.assess_user_skills(user_id)
        serialized = self._serialize_skills_data(skills_data)

        if self.cache:
            await self.cache.set(cache_key, serialized, ttl=self.CACHE_TTL['user_skills'])

        return serialized

    async def get_community_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get community overview analytics."""
        cache_key = f"community_overview:{days}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        community_data = self.community_analytics.get_community_overview(days)

        if self.cache:
            await self.cache.set(cache_key, community_data, ttl=self.CACHE_TTL['community_overview'])

        return community_data

    async def get_topic_analytics(self, topic: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific topic."""
        cache_key = f"topic_analytics:{topic}:{days}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        topic_data = self.community_analytics.get_topic_analytics(topic, days)

        if self.cache:
            await self.cache.set(cache_key, topic_data, ttl=self.CACHE_TTL['topic_analytics'])

        return topic_data

    async def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Get AI-generated personalized insights for a user."""
        cache_key = f"user_insights:{user_id}"

        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        insights_data = await self.insights_engine.generate_personalized_insights(user_id)
        serialized = self._serialize_insights_data(insights_data)

        if self.cache:
            await self.cache.set(cache_key, serialized, ttl=self.CACHE_TTL['user_insights'])

        return serialized

    async def get_learning_effectiveness(self, days: int = 90) -> Dict[str, Any]:
        """Get learning effectiveness metrics for the community."""
        return self.community_analytics.get_learning_effectiveness_metrics(days)

    async def get_user_engagement_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get user engagement insights."""
        return self.community_analytics.get_user_engagement_insights(days)

    async def invalidate_user_cache(self, user_id: int) -> None:
        """Invalidate all cached data for a user."""
        if not self.cache:
            return

        cache_keys = [
            f"user_dashboard:{user_id}",
            f"user_progress:{user_id}",
            f"user_skills:{user_id}",
            f"user_insights:{user_id}"
        ]

        for key in cache_keys:
            await self.cache.delete(key)

        logger.info(f"Invalidated cache for user {user_id}")

    async def invalidate_community_cache(self) -> None:
        """Invalidate community-wide cached data."""
        if not self.cache:
            return

        # This would need a more sophisticated cache invalidation strategy
        # For now, we'll skip community cache invalidation
        logger.info("Community cache invalidation not implemented")

    # Private helper methods

    async def _get_progress_data(self, user_id: int):
        """Get progress data (synchronous call wrapped for async)."""
        return self.progress_calc.calculate_user_progress(user_id)

    async def _get_skills_data(self, user_id: int):
        """Get skills data (synchronous call wrapped for async)."""
        return self.skill_assessor.assess_user_skills(user_id)

    async def _get_community_overview(self):
        """Get community overview (synchronous call wrapped for async)."""
        return self.community_analytics.get_community_overview()

    async def _get_insights_data(self, user_id: int):
        """Get insights data (async call)."""
        return await self.insights_engine.generate_personalized_insights(user_id)

    def _serialize_progress_data(self, progress_data) -> Dict[str, Any]:
        """Serialize progress data for API response."""
        return {
            'total_projects_completed': progress_data.total_projects_completed,
            'total_questions_solved': progress_data.total_questions_solved,
            'total_time_spent': progress_data.total_time_spent,
            'current_learning_streak': progress_data.current_learning_streak,
            'favorite_topics': progress_data.favorite_topics,
            'recommended_difficulty': progress_data.recommended_difficulty,
            'learning_velocity': {
                'projects_per_week': progress_data.learning_velocity.projects_per_week,
                'topics_per_week': progress_data.learning_velocity.topics_per_week,
                'consistency_score': progress_data.learning_velocity.consistency_score,
                'current_streak': progress_data.learning_velocity.current_streak,
                'longest_streak': progress_data.learning_velocity.longest_streak
            }
        }

    def _serialize_skills_data(self, skills_data: SkillAssessment) -> Dict[str, Any]:
        """Serialize skills data for API response."""
        return {
            'overall_level': skills_data.overall_level,
            'topic_breakdown': skills_data.topic_breakdown,
            'strengths': skills_data.strengths,
            'weaknesses': skills_data.weaknesses,
            'learning_trajectory': skills_data.learning_trajectory,
            'confidence_score': skills_data.confidence_score,
            'recommended_focus_areas': skills_data.recommended_focus_areas
        }

    def _serialize_insights_data(self, insights_data: PersonalizedInsights) -> Dict[str, Any]:
        """Serialize insights data for API response."""
        return {
            'insights': [
                {
                    'category': insight.category,
                    'priority': insight.priority,
                    'title': insight.title,
                    'description': insight.description,
                    'actionable_steps': insight.actionable_steps,
                    'expected_impact': insight.expected_impact,
                    'confidence_score': insight.confidence_score
                }
                for insight in insights_data.insights
            ],
            'overall_summary': insights_data.overall_summary,
            'next_best_actions': insights_data.next_best_actions,
            'learning_goals': insights_data.learning_goals,
            'generated_at': insights_data.generated_at.isoformat(),
            'ai_model_used': insights_data.ai_model_used
        }

    def _generate_dashboard_summary(self, progress, skills, insights) -> Dict[str, Any]:
        """Generate a concise dashboard summary."""
        return {
            'key_metrics': {
                'skill_level': skills.overall_level,
                'projects_completed': progress.total_projects_completed,
                'current_streak': progress.current_learning_streak,
                'learning_velocity': progress.learning_velocity.projects_per_week
            },
            'status': 'healthy' if skills.overall_level > 0.3 else 'growing',
            'focus_areas': skills.recommended_focus_areas[:3],
            'next_actions': insights.next_best_actions[:2] if insights else []
        }

    # Analytics methods for deeper insights

    async def analyze_learning_patterns(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze detailed learning patterns for a user.

        Returns advanced analytics about learning behavior, optimal times,
        topic preferences, and improvement trajectories.
        """
        # Get historical data
        progress = self.progress_calc.calculate_user_progress(user_id)

        # Analyze learning patterns
        patterns = {
            'peak_learning_times': self._analyze_peak_learning_times(user_id),
            'topic_mastery_timeline': self._analyze_topic_mastery_timeline(user_id),
            'improvement_velocity': self._calculate_improvement_velocity(user_id),
            'consistency_patterns': self._analyze_consistency_patterns(user_id),
            'learning_style': self._infer_learning_style(user_id)
        }

        return patterns

    def _analyze_peak_learning_times(self, user_id: int) -> Dict[str, Any]:
        """Analyze when the user learns most effectively."""
        # This would analyze historical interaction times
        # Placeholder implementation
        return {
            'best_day': 'Tuesday',
            'best_time': '14:00-16:00',
            'consistency_score': 0.75
        }

    def _analyze_topic_mastery_timeline(self, user_id: int) -> List[Dict]:
        """Analyze how skill mastery evolved over time."""
        # Placeholder for timeline analysis
        return [
            {'date': '2024-01-01', 'algorithms': 0.2, 'data_structures': 0.1},
            {'date': '2024-02-01', 'algorithms': 0.4, 'data_structures': 0.3},
            {'date': '2024-03-01', 'algorithms': 0.6, 'data_structures': 0.5}
        ]

    def _calculate_improvement_velocity(self, user_id: int) -> Dict[str, float]:
        """Calculate how quickly the user improves."""
        # Analyze skill growth over time
        return {
            'overall_velocity': 0.05,  # skill points per week
            'recent_acceleration': 1.2,  # how much faster recently
            'predicted_next_month': 0.8  # projected skill level
        }

    def _analyze_consistency_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze learning consistency patterns."""
        return {
            'average_daily_sessions': 1.5,
            'weekend_vs_weekday_ratio': 0.8,
            'longest_gap_days': 5,
            'consistency_trend': 'improving'  # improving, declining, stable
        }

    def _infer_learning_style(self, user_id: int) -> str:
        """Infer the user's learning style based on behavior."""
        # This would use machine learning to classify learning style
        return 'hands_on'  # hands_on, theoretical, visual, etc.

    # Bulk analytics methods

    async def get_leaderboard(self, metric: str = 'skill_level', limit: int = 50) -> List[Dict]:
        """
        Get community leaderboard for various metrics.

        Args:
            metric: The metric to rank by ('skill_level', 'projects_completed', 'streak', etc.)
            limit: Maximum number of results to return
        """
        # This would implement leaderboard logic
        # Placeholder for now
        return [
            {'rank': 1, 'user_id': 123, 'username': 'learner123', 'value': 0.85, 'metric': metric},
            {'rank': 2, 'user_id': 456, 'username': 'coder456', 'value': 0.82, 'metric': metric}
        ]

    async def get_trending_content(self, days: int = 7) -> List[Dict]:
        """
        Get trending learning content based on community engagement.

        Returns projects, topics, or other content that's gaining popularity.
        """
        trending_topics = self.community_analytics._get_trending_topics(days)
        return [
            {
                'topic': topic,
                'growth_rate': growth_rate,
                'current_popularity': count,
                'trend': 'rising' if growth_rate > 0.5 else 'steady'
            }
            for topic, growth_rate in trending_topics
            for count, _ in [self.community_analytics._get_popular_topics(1)[0] if self.community_analytics._get_popular_topics(1) else (0, '')]
        ]
