"""
Community analytics for NoLeet platform.

This module provides analytics about community-wide learning patterns,
popular topics, user engagement trends, and collaborative insights.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from noleet.app.models import User, Project, UserInteraction, Category
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class CommunityAnalytics:
    """Analytics engine for community-wide insights."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_community_overview(self, days: int = 30) -> Dict:
        """
        Get comprehensive community overview statistics.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with community metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Basic community stats
        total_users = self.db.query(User).filter(User.is_active == True).count()
        active_users = self._get_active_users_count(days)
        new_users = self._get_new_users_count(days)

        # Project and interaction stats
        total_projects = self.db.query(Project).count()
        new_projects = self._get_new_projects_count(days)

        total_interactions = self.db.query(UserInteraction).filter(
            UserInteraction.created_at >= cutoff_date
        ).count()

        # Popular topics and trends
        popular_topics = self._get_popular_topics(days)
        trending_topics = self._get_trending_topics(days)

        # Engagement metrics
        engagement_rate = self._calculate_engagement_rate(days)
        retention_rate = self._calculate_retention_rate(days)

        return {
            'time_period_days': days,
            'user_metrics': {
                'total_users': total_users,
                'active_users': active_users,
                'new_users': new_users,
                'engagement_rate': round(engagement_rate, 3),
                'retention_rate': round(retention_rate, 3)
            },
            'content_metrics': {
                'total_projects': total_projects,
                'new_projects': new_projects,
                'total_interactions': total_interactions,
                'interactions_per_user': round(total_interactions / max(active_users, 1), 2)
            },
            'topic_analytics': {
                'popular_topics': popular_topics[:10],
                'trending_topics': trending_topics[:10]
            }
        }

    def get_topic_analytics(self, topic: str, days: int = 30) -> Dict:
        """
        Get detailed analytics for a specific topic.

        Args:
            topic: Topic name to analyze
            days: Number of days to analyze

        Returns:
            Topic-specific analytics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Projects in this topic
        topic_projects = self.db.query(Project).filter(
            and_(
                func.array_to_string(Project.tags, ',').ilike(f'%{topic}%'),
                Project.status == 'published'
            )
        ).all()

        # User interactions with this topic
        topic_interactions = self.db.query(UserInteraction).join(
            Project,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id,
                func.array_to_string(Project.tags, ',').ilike(f'%{topic}%')
            )
        ).filter(
            UserInteraction.created_at >= cutoff_date
        ).all()

        # Calculate metrics
        unique_users = len(set(i.user_id for i in topic_interactions))
        total_views = sum(1 for i in topic_interactions if i.interaction_type == 'view')
        total_completions = sum(1 for i in topic_interactions if i.interaction_type == 'complete')
        avg_completion_rate = total_completions / max(total_views, 1)

        # Difficulty distribution
        difficulty_counts = Counter(p.difficulty for p in topic_projects)

        # User skill distribution for this topic
        user_skill_levels = self._calculate_topic_skill_distribution(topic, days)

        return {
            'topic': topic,
            'time_period_days': days,
            'project_metrics': {
                'total_projects': len(topic_projects),
                'difficulty_distribution': dict(difficulty_counts),
                'avg_difficulty': self._calculate_avg_difficulty(topic_projects)
            },
            'engagement_metrics': {
                'unique_users': unique_users,
                'total_views': total_views,
                'total_completions': total_completions,
                'completion_rate': round(avg_completion_rate, 3),
                'interactions_per_user': round(len(topic_interactions) / max(unique_users, 1), 2)
            },
            'skill_distribution': user_skill_levels
        }

    def get_user_engagement_insights(self, days: int = 30) -> Dict:
        """
        Get insights about user engagement patterns.

        Args:
            days: Number of days to analyze

        Returns:
            User engagement insights
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Daily activity patterns
        daily_activity = self.db.query(
            func.date(UserInteraction.created_at).label('date'),
            func.count(func.distinct(UserInteraction.user_id)).label('active_users'),
            func.count(UserInteraction.id).label('total_interactions')
        ).filter(
            UserInteraction.created_at >= cutoff_date
        ).group_by(func.date(UserInteraction.created_at)).all()

        # Hourly activity patterns
        hourly_activity = self.db.query(
            func.extract('hour', UserInteraction.created_at).label('hour'),
            func.count(func.distinct(UserInteraction.user_id)).label('active_users'),
            func.count(UserInteraction.id).label('total_interactions')
        ).filter(
            UserInteraction.created_at >= cutoff_date
        ).group_by(func.extract('hour', UserInteraction.created_at)).all()

        # User segmentation
        power_users = self._get_power_users(days)
        casual_users = self._get_casual_users(days)
        inactive_users = self._get_inactive_users(days)

        # Engagement trends
        engagement_trend = self._calculate_engagement_trend(daily_activity)

        return {
            'time_period_days': days,
            'activity_patterns': {
                'daily': [{'date': str(d.date), 'active_users': d.active_users, 'interactions': d.total_interactions}
                         for d in daily_activity],
                'hourly': [{'hour': int(h.hour), 'active_users': h.active_users, 'interactions': h.total_interactions}
                          for h in hourly_activity]
            },
            'user_segments': {
                'power_users': len(power_users),
                'casual_users': len(casual_users),
                'inactive_users': len(inactive_users)
            },
            'engagement_trend': engagement_trend
        }

    def get_learning_effectiveness_metrics(self, days: int = 90) -> Dict:
        """
        Calculate metrics on learning effectiveness across the community.

        Args:
            days: Number of days to analyze

        Returns:
            Learning effectiveness metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get users who completed projects in the period
        active_learners = self.db.query(
            UserInteraction.user_id,
            func.count(UserInteraction.id).label('total_interactions'),
            func.count(func.case((UserInteraction.interaction_type == 'complete', 1))).label('completions'),
            func.avg(func.extract('epoch', func.now() - UserInteraction.created_at) / 86400).label('avg_days_ago')
        ).filter(
            and_(
                UserInteraction.created_at >= cutoff_date,
                UserInteraction.interaction_type.in_(['view', 'complete', 'like'])
            )
        ).group_by(UserInteraction.user_id).having(
            func.count(func.case((UserInteraction.interaction_type == 'complete', 1))) >= 1
        ).all()

        if not active_learners:
            return {'error': 'No active learners found in the period'}

        # Calculate learning metrics
        completion_rates = [user.completions / max(user.total_interactions, 1) for user in active_learners]
        avg_completion_rate = sum(completion_rates) / len(completion_rates)

        # Learning velocity (completions per week)
        avg_velocity = sum(user.completions for user in active_learners) / max(days / 7, 1)

        # Consistency score (lower standard deviation = more consistent)
        completion_std = (sum((rate - avg_completion_rate) ** 2 for rate in completion_rates) / len(completion_rates)) ** 0.5
        consistency_score = 1 / (1 + completion_std)

        # Recency analysis
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_learners = [u for u in active_learners if u.avg_days_ago <= 30]
        recent_engagement_rate = len(recent_learners) / len(active_learners)

        return {
            'time_period_days': days,
            'total_active_learners': len(active_learners),
            'learning_metrics': {
                'avg_completion_rate': round(avg_completion_rate, 3),
                'avg_learning_velocity': round(avg_velocity, 2),  # completions per week
                'learning_consistency': round(consistency_score, 3),
                'recent_engagement_rate': round(recent_engagement_rate, 3)
            },
            'distribution_stats': {
                'completion_rate_std': round(completion_std, 3),
                'velocity_percentiles': self._calculate_percentiles([u.completions / max(days / 7, 1) for u in active_learners])
            }
        }

    def get_collaboration_insights(self, days: int = 30) -> Dict:
        """
        Get insights about community collaboration patterns.

        Args:
            days: Number of days to analyze

        Returns:
            Collaboration insights
        """
        # This would integrate with future collaboration features
        # For now, return basic social interaction metrics

        cutoff_date = datetime.now() - timedelta(days=days)

        # Basic social interactions (likes, comments if implemented)
        social_interactions = self.db.query(
            UserInteraction.interaction_type,
            func.count(UserInteraction.id).label('count')
        ).filter(
            and_(
                UserInteraction.created_at >= cutoff_date,
                UserInteraction.interaction_type.in_(['like', 'comment', 'share'])  # Add as implemented
            )
        ).group_by(UserInteraction.interaction_type).all()

        social_stats = {interaction.interaction_type: interaction.count for interaction in social_interactions}

        # Community size and growth
        total_users = self.db.query(User).filter(User.is_active == True).count()
        new_users = self._get_new_users_count(days)

        return {
            'time_period_days': days,
            'social_interactions': social_stats,
            'community_health': {
                'total_users': total_users,
                'new_users': new_users,
                'growth_rate': round(new_users / max(total_users, 1), 3),
                'social_interaction_rate': round(sum(social_stats.values()) / max(total_users, 1), 2)
            }
        }

    def _get_active_users_count(self, days: int) -> int:
        """Get count of active users in the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        return self.db.query(func.count(func.distinct(UserInteraction.user_id))).filter(
            UserInteraction.created_at >= cutoff_date
        ).scalar()

    def _get_new_users_count(self, days: int) -> int:
        """Get count of new users in the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        return self.db.query(User).filter(
            User.created_at >= cutoff_date
        ).count()

    def _get_new_projects_count(self, days: int) -> int:
        """Get count of new projects in the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        return self.db.query(Project).filter(
            Project.created_at >= cutoff_date
        ).count()

    def _get_popular_topics(self, days: int) -> List[Tuple[str, int]]:
        """Get most popular topics by interaction count."""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get topic interaction counts
        topic_counts = defaultdict(int)

        interactions = self.db.query(UserInteraction, Project).join(
            Project,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id
            )
        ).filter(
            UserInteraction.created_at >= cutoff_date
        ).all()

        for interaction, project in interactions:
            for tag in (project.tags or []):
                topic_counts[tag] += 1

        return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

    def _get_trending_topics(self, days: int) -> List[Tuple[str, float]]:
        """Get trending topics based on recent growth."""
        # Compare last 7 days vs previous 7 days
        recent_cutoff = datetime.now() - timedelta(days=7)
        previous_cutoff = datetime.now() - timedelta(days=14)

        recent_counts = defaultdict(int)
        previous_counts = defaultdict(int)

        # Recent interactions
        recent_interactions = self.db.query(UserInteraction, Project).join(
            Project,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id
            )
        ).filter(
            UserInteraction.created_at >= recent_cutoff
        ).all()

        for interaction, project in recent_interactions:
            for tag in (project.tags or []):
                recent_counts[tag] += 1

        # Previous interactions
        previous_interactions = self.db.query(UserInteraction, Project).join(
            Project,
            and_(
                UserInteraction.target_type == 'project',
                UserInteraction.target_id == Project.id
            )
        ).filter(
            and_(
                UserInteraction.created_at >= previous_cutoff,
                UserInteraction.created_at < recent_cutoff
            )
        ).all()

        for interaction, project in previous_interactions:
            for tag in (project.tags or []):
                previous_counts[tag] += 1

        # Calculate growth rates
        trending = []
        for topic in set(list(recent_counts.keys()) + list(previous_counts.keys())):
            recent = recent_counts[topic]
            previous = previous_counts[topic]

            if previous > 0:
                growth_rate = (recent - previous) / previous
            elif recent > 0:
                growth_rate = 1.0  # New topic
            else:
                growth_rate = 0.0

            trending.append((topic, growth_rate))

        return sorted(trending, key=lambda x: x[1], reverse=True)

    def _calculate_engagement_rate(self, days: int) -> float:
        """Calculate overall community engagement rate."""
        total_users = self.db.query(User).filter(User.is_active == True).count()
        active_users = self._get_active_users_count(days)

        return active_users / max(total_users, 1)

    def _calculate_retention_rate(self, days: int) -> float:
        """Calculate user retention rate."""
        # Simple retention: active users who were active 30 days ago
        retention_period = 30
        current_active = set(self._get_active_user_ids(days))

        retention_cutoff = datetime.now() - timedelta(days=days + retention_period)
        previously_active = set(
            uid[0] for uid in self.db.query(UserInteraction.user_id.distinct()).filter(
                UserInteraction.created_at >= retention_cutoff
            ).all()
        )

        retained_users = current_active.intersection(previously_active)

        return len(retained_users) / max(len(previously_active), 1)

    def _calculate_topic_skill_distribution(self, topic: str, days: int) -> Dict[str, int]:
        """Calculate skill level distribution for a topic."""
        # This would integrate with skill assessment
        # Placeholder implementation
        return {
            'beginner': 45,
            'intermediate': 35,
            'advanced': 20
        }

    def _calculate_avg_difficulty(self, projects: List) -> str:
        """Calculate average difficulty of projects."""
        if not projects:
            return 'unknown'

        difficulty_values = {'easy': 1, 'medium': 2, 'hard': 3}
        total = sum(difficulty_values.get(p.difficulty, 2) for p in projects)
        avg = total / len(projects)

        if avg < 1.5:
            return 'easy'
        elif avg < 2.5:
            return 'medium'
        else:
            return 'hard'

    def _get_power_users(self, days: int) -> List[int]:
        """Get power users (high activity)."""
        cutoff_date = datetime.now() - timedelta(days=days)

        power_users = self.db.query(
            UserInteraction.user_id,
            func.count(UserInteraction.id).label('activity_count')
        ).filter(
            UserInteraction.created_at >= cutoff_date
        ).group_by(UserInteraction.user_id).having(
            func.count(UserInteraction.id) >= 50  # Threshold for power user
        ).all()

        return [user.user_id for user in power_users]

    def _get_casual_users(self, days: int) -> List[int]:
        """Get casual users (moderate activity)."""
        cutoff_date = datetime.now() - timedelta(days=days)

        casual_users = self.db.query(
            UserInteraction.user_id,
            func.count(UserInteraction.id).label('activity_count')
        ).filter(
            UserInteraction.created_at >= cutoff_date
        ).group_by(UserInteraction.user_id).having(
            and_(
                func.count(UserInteraction.id) >= 5,
                func.count(UserInteraction.id) < 50
            )
        ).all()

        return [user.user_id for user in casual_users]

    def _get_inactive_users(self, days: int) -> List[int]:
        """Get inactive users."""
        active_user_ids = set(self._get_active_user_ids(days))
        all_user_ids = set(uid[0] for uid in self.db.query(User.id).filter(User.is_active == True).all())

        return list(all_user_ids - active_user_ids)

    def _get_active_user_ids(self, days: int) -> List[int]:
        """Get list of active user IDs."""
        cutoff_date = datetime.now() - timedelta(days=days)

        active_users = self.db.query(UserInteraction.user_id.distinct()).filter(
            UserInteraction.created_at >= cutoff_date
        ).all()

        return [user[0] for user in active_users]

    def _calculate_engagement_trend(self, daily_activity) -> str:
        """Calculate engagement trend direction."""
        if len(daily_activity) < 7:
            return 'insufficient_data'

        # Simple trend analysis
        recent_avg = sum(d.active_users for d in daily_activity[-7:]) / 7
        previous_avg = sum(d.active_users for d in daily_activity[:-7]) / max(len(daily_activity[:-7]), 1)

        if recent_avg > previous_avg * 1.1:
            return 'increasing'
        elif recent_avg < previous_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for a list of values."""
        if not values:
            return {'p25': 0, 'p50': 0, 'p75': 0, 'p95': 0}

        values.sort()
        n = len(values)

        return {
            'p25': values[int(n * 0.25)],
            'p50': values[int(n * 0.50)],
            'p75': values[int(n * 0.75)],
            'p95': values[int(n * 0.95)]
        }
