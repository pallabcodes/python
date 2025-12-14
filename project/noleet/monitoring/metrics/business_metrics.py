"""
Business metrics collection for monitoring user engagement and product metrics.
"""

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
from typing import Optional


class BusinessMetricsCollector:
    """Collects business metrics for NoLeet application."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        # User engagement metrics
        self.user_sessions_total = Counter(
            'noleet_user_sessions_total',
            'Total user sessions',
            ['user_type', 'device_type'],
            registry=registry
        )

        self.user_session_duration_seconds = Histogram(
            'noleet_user_session_duration_seconds',
            'User session duration in seconds',
            ['user_type'],
            buckets=[60, 300, 600, 1800, 3600, 7200, 18000],  # 1min to 5hours
            registry=registry
        )

        # Content engagement metrics
        self.content_views_total = Counter(
            'noleet_content_views_total',
            'Total content views',
            ['content_type', 'content_id'],
            registry=registry
        )

        self.content_interactions_total = Counter(
            'noleet_content_interactions_total',
            'Total content interactions',
            ['content_type', 'interaction_type'],
            registry=registry
        )

        # Project creation and usage metrics
        self.projects_created_total = Counter(
            'noleet_projects_created_total',
            'Total projects created',
            ['project_type', 'user_type'],
            registry=registry
        )

        self.projects_completed_total = Counter(
            'noleet_projects_completed_total',
            'Total projects completed',
            ['project_type', 'completion_time_hours'],
            registry=registry
        )

        # Recommendation metrics
        self.recommendations_served_total = Counter(
            'noleet_recommendations_served_total',
            'Total recommendations served',
            ['recommendation_type', 'algorithm'],
            registry=registry
        )

        self.recommendation_acceptance_total = Counter(
            'noleet_recommendation_acceptance_total',
            'Total recommendation acceptances',
            ['recommendation_type', 'position'],
            registry=registry
        )

        self.recommendation_rejections_total = Counter(
            'noleet_recommendation_rejections_total',
            'Total recommendation rejections',
            ['recommendation_type', 'reason'],
            registry=registry
        )

        # Learning progress metrics
        self.learning_sessions_total = Counter(
            'noleet_learning_sessions_total',
            'Total learning sessions',
            ['skill_level', 'topic'],
            registry=registry
        )

        self.skill_assessments_completed_total = Counter(
            'noleet_skill_assessments_completed_total',
            'Total skill assessments completed',
            ['assessment_type', 'skill_area'],
            registry=registry
        )

        # Agent interaction metrics
        self.agent_interactions_total = Counter(
            'noleet_agent_interactions_total',
            'Total agent interactions',
            ['agent_type', 'interaction_type', 'outcome'],
            registry=registry
        )

        # Business KPIs
        self.active_users_daily = Gauge(
            'noleet_active_users_daily',
            'Daily active users',
            registry=registry
        )

        self.active_users_monthly = Gauge(
            'noleet_active_users_monthly',
            'Monthly active users',
            registry=registry
        )

        self.user_engagement_rate = Gauge(
            'noleet_user_engagement_rate',
            'User engagement rate (interactions per session)',
            registry=registry
        )

        self.conversion_rate = Gauge(
            'noleet_conversion_rate',
            'Conversion rate (projects completed / projects started)',
            registry=registry
        )

    def record_user_session(self, user_type: str = 'anonymous', device_type: str = 'unknown',
                          duration: Optional[float] = None):
        """Record user session metrics."""
        self.user_sessions_total.labels(
            user_type=user_type,
            device_type=device_type
        ).inc()

        if duration is not None:
            self.user_session_duration_seconds.labels(
                user_type=user_type
            ).observe(duration)

    def record_content_view(self, content_type: str, content_id: str):
        """Record content view."""
        self.content_views_total.labels(
            content_type=content_type,
            content_id=content_id
        ).inc()

    def record_content_interaction(self, content_type: str, interaction_type: str):
        """Record content interaction."""
        self.content_interactions_total.labels(
            content_type=content_type,
            interaction_type=interaction_type
        ).inc()

    def record_project_created(self, project_type: str, user_type: str = 'registered'):
        """Record project creation."""
        self.projects_created_total.labels(
            project_type=project_type,
            user_type=user_type
        ).inc()

    def record_project_completed(self, project_type: str, completion_time_hours: float):
        """Record project completion."""
        # Bucket completion time
        if completion_time_hours <= 1:
            bucket = '0-1h'
        elif completion_time_hours <= 4:
            bucket = '1-4h'
        elif completion_time_hours <= 12:
            bucket = '4-12h'
        elif completion_time_hours <= 24:
            bucket = '12-24h'
        else:
            bucket = '24h+'

        self.projects_completed_total.labels(
            project_type=project_type,
            completion_time_hours=bucket
        ).inc()

    def record_recommendation_served(self, recommendation_type: str, algorithm: str = 'default'):
        """Record recommendation served."""
        self.recommendations_served_total.labels(
            recommendation_type=recommendation_type,
            algorithm=algorithm
        ).inc()

    def record_recommendation_accepted(self, recommendation_type: str, position: int):
        """Record recommendation acceptance."""
        self.recommendation_acceptance_total.labels(
            recommendation_type=recommendation_type,
            position=str(position)
        ).inc()

    def record_recommendation_rejected(self, recommendation_type: str, reason: str = 'unknown'):
        """Record recommendation rejection."""
        self.recommendation_rejections_total.labels(
            recommendation_type=recommendation_type,
            reason=reason
        ).inc()

    def record_learning_session(self, skill_level: str, topic: str):
        """Record learning session."""
        self.learning_sessions_total.labels(
            skill_level=skill_level,
            topic=topic
        ).inc()

    def record_skill_assessment(self, assessment_type: str, skill_area: str):
        """Record skill assessment completion."""
        self.skill_assessments_completed_total.labels(
            assessment_type=assessment_type,
            skill_area=skill_area
        ).inc()

    def record_agent_interaction(self, agent_type: str, interaction_type: str, outcome: str):
        """Record agent interaction."""
        self.agent_interactions_total.labels(
            agent_type=agent_type,
            interaction_type=interaction_type,
            outcome=outcome
        ).inc()

    def update_business_kpis(self, daily_active: int, monthly_active: int,
                           engagement_rate: float, conversion_rate: float):
        """Update business KPI gauges."""
        self.active_users_daily.set(daily_active)
        self.active_users_monthly.set(monthly_active)
        self.user_engagement_rate.set(engagement_rate)
        self.conversion_rate.set(conversion_rate)
