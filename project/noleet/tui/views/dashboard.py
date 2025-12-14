"""
TUI Dashboard for learning progress and analytics.

This module provides the main dashboard interface for users to view
their learning progress, skills, insights, and community analytics.
"""

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, Label,
    ProgressBar, Tabs, Tab, DataTable
)
from textual.widget import Widget
from textual import on

from noleet.analytics.progress_calculator import ProgressCalculator
from noleet.analytics.skill_assessor import SkillAssessor
from noleet.analytics.community_analytics import CommunityAnalytics
from noleet.analytics.insights_engine import InsightsEngine
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class DashboardView(Vertical):
    """Main dashboard view showing learning progress and insights."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session

        # Initialize analytics engines
        self.progress_calc = ProgressCalculator(db_session)
        self.skill_assessor = SkillAssessor(db_session)
        self.community_analytics = CommunityAnalytics(db_session)
        self.insights_engine = InsightsEngine(db_session)

        # Data caches
        self.progress_data = None
        self.skills_data = None
        self.community_data = None
        self.insights_data = None

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        with Container(id="dashboard-container"):
            # Header section
            yield Header()

            # Main content tabs
            with Tabs():
                with Tab("Overview", id="overview-tab"):
                    yield OverviewPanel(self.user_id, self.db)

                with Tab("Skills", id="skills-tab"):
                    yield SkillsPanel(self.user_id, self.db)

                with Tab("Progress", id="progress-tab"):
                    yield ProgressPanel(self.user_id, self.db)

                with Tab("Insights", id="insights-tab"):
                    yield InsightsPanel(self.user_id, self.db)

                with Tab("Community", id="community-tab"):
                    yield CommunityPanel(self.db)

            # Footer
            yield Footer()

    async def on_mount(self) -> None:
        """Load data when the dashboard mounts."""
        await self.load_dashboard_data()

    async def load_dashboard_data(self) -> None:
        """Load all dashboard data."""
        try:
            logger.info(f"Loading dashboard data for user {self.user_id}")

            # Load data in parallel
            self.progress_data = self.progress_calc.calculate_user_progress(self.user_id)
            self.skills_data = self.skill_assessor.assess_user_skills(self.user_id)
            self.community_data = self.community_analytics.get_community_overview()
            self.insights_data = await self.insights_engine.generate_personalized_insights(self.user_id)

            # Update all panels
            await self.update_panels()

        except Exception as e:
            logger.error(f"Failed to load dashboard data: {e}")
            # Show error state

    async def update_panels(self) -> None:
        """Update all dashboard panels with new data."""
        # Update each panel with the loaded data
        for panel in self.query("DashboardPanel"):
            panel.update_data(
                progress=self.progress_data,
                skills=self.skills_data,
                community=self.community_data,
                insights=self.insights_data
            )


class DashboardPanel(Widget):
    """Base class for dashboard panels."""

    def __init__(self, user_id: Optional[int] = None, db_session=None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session

    def update_data(self, progress=None, skills=None, community=None, insights=None):
        """Update panel with new data. Override in subclasses."""
        pass


class OverviewPanel(DashboardPanel):
    """Overview panel showing key metrics and summary."""

    def compose(self) -> ComposeResult:
        with Vertical(id="overview-content"):
            # Key metrics row
            with Horizontal(id="metrics-row"):
                yield MetricCard("Projects Completed", "0", id="projects-card")
                yield MetricCard("Current Streak", "0 days", id="streak-card")
                yield MetricCard("Skill Level", "0%", id="skill-card")
                yield MetricCard("Learning Velocity", "0/wk", id="velocity-card")

            # Progress summary
            yield Static("### Learning Summary", id="summary-header")
            yield Static("Loading your personalized summary...", id="summary-text")

            # Recent achievements
            yield Static("### Recent Achievements", id="achievements-header")
            yield Static("No recent achievements to display.", id="achievements-list")

    def update_data(self, progress=None, skills=None, community=None, insights=None):
        """Update overview panel with data."""
        if not progress or not skills:
            return

        # Update metrics
        self.query_one("#projects-card", MetricCard).update_value(str(progress.total_projects_completed))
        self.query_one("#streak-card", MetricCard).update_value(f"{progress.current_learning_streak} days")
        self.query_one("#skill-card", MetricCard).update_value(f"{skills.overall_level:.1%}")
        self.query_one("#velocity-card", MetricCard).update_value(f"{progress.learning_velocity.projects_per_week:.1f}/wk")

        # Update summary
        if insights and insights.overall_summary:
            self.query_one("#summary-text").update(insights.overall_summary)
        else:
            summary = f"You've completed {progress.total_projects_completed} projects and are on a {progress.current_learning_streak}-day learning streak. "
            summary += f"Your overall skill level is {skills.overall_level:.1%} with a {skills.learning_trajectory} trajectory."
            self.query_one("#summary-text").update(summary)

        # Update achievements (simplified)
        achievements = []
        if progress.current_learning_streak >= 7:
            achievements.append(f"🔥 {progress.current_learning_streak}-day learning streak!")
        if progress.total_projects_completed >= 10:
            achievements.append(f"🏆 {progress.total_projects_completed} projects completed!")

        if achievements:
            self.query_one("#achievements-list").update("\n".join(achievements))
        else:
            self.query_one("#achievements-list").update("Keep learning to unlock achievements!")


class SkillsPanel(DashboardPanel):
    """Skills panel showing topic-specific skill levels."""

    def compose(self) -> ComposeResult:
        with Vertical(id="skills-content"):
            # Skill level summary
            yield Static("### Skill Assessment", id="skills-header")
            with Horizontal():
                yield Static("Overall Level: ", id="overall-level")
                yield ProgressBar(total=100, id="overall-progress")

            # Topic breakdown
            yield Static("### Topic Skills", id="topics-header")
            yield DataTable(id="skills-table")

            # Strengths and weaknesses
            with Horizontal():
                with Vertical(id="strengths-column"):
                    yield Static("### Strengths", id="strengths-header")
                    yield Static("Loading...", id="strengths-list")

                with Vertical(id="weaknesses-column"):
                    yield Static("### Areas for Growth", id="weaknesses-header")
                    yield Static("Loading...", id="weaknesses-list")

    def update_data(self, progress=None, skills=None, community=None, insights=None):
        """Update skills panel with data."""
        if not skills:
            return

        # Update overall level
        self.query_one("#overall-level").update(f"Overall Level: {skills.overall_level:.1%}")
        self.query_one("#overall-progress", ProgressBar).update(progress=skills.overall_level * 100)

        # Update skills table
        table = self.query_one("#skills-table", DataTable)
        table.clear()
        table.add_columns("Topic", "Skill Level", "Confidence", "Projects")

        for topic, skill_data in skills.topic_breakdown.items():
            table.add_row(
                topic.title(),
                f"{skill_data.level:.1%}",
                f"{skill_data.confidence:.1%}",
                str(skill_data.projects_completed)
            )

        # Update strengths and weaknesses
        strengths_text = "\n".join(f"• {strength}" for strength in skills.strengths) if skills.strengths else "No major strengths identified yet."
        weaknesses_text = "\n".join(f"• {weakness}" for weakness in skills.weaknesses) if skills.weaknesses else "Keep learning to identify growth areas!"

        self.query_one("#strengths-list").update(strengths_text)
        self.query_one("#weaknesses-list").update(weaknesses_text)


class ProgressPanel(DashboardPanel):
    """Progress panel showing learning journey and trends."""

    def compose(self) -> ComposeResult:
        with Vertical(id="progress-content"):
            # Learning velocity
            yield Static("### Learning Velocity", id="velocity-header")
            with Horizontal():
                yield MetricCard("Projects/Week", "0.0", id="projects-week-card")
                yield MetricCard("Topics/Week", "0.0", id="topics-week-card")
                yield MetricCard("Consistency", "0%", id="consistency-card")

            # Learning streak
            yield Static("### Learning Streaks", id="streaks-header")
            with Horizontal():
                yield MetricCard("Current", "0 days", id="current-streak-card")
                yield MetricCard("Longest", "0 days", id="longest-streak-card")

            # Time spent
            yield Static("### Time Investment", id="time-header")
            yield MetricCard("Total Learning Time", "0 minutes", id="time-spent-card")

            # Favorite topics
            yield Static("### Favorite Topics", id="favorites-header")
            yield Static("Loading favorite topics...", id="favorites-list")

    def update_data(self, progress=None, skills=None, community=None, insights=None):
        """Update progress panel with data."""
        if not progress:
            return

        velocity = progress.learning_velocity

        # Update velocity metrics
        self.query_one("#projects-week-card", MetricCard).update_value(f"{velocity.projects_per_week:.1f}")
        self.query_one("#topics-week-card", MetricCard).update_value(f"{velocity.topics_per_week:.1f}")
        self.query_one("#consistency-card", MetricCard).update_value(f"{velocity.consistency_score:.1%}")

        # Update streaks
        self.query_one("#current-streak-card", MetricCard).update_value(f"{velocity.current_streak} days")
        self.query_one("#longest-streak-card", MetricCard).update_value(f"{velocity.longest_streak} days")

        # Update time
        hours = progress.total_time_spent // 60
        minutes = progress.total_time_spent % 60
        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} minutes"
        self.query_one("#time-spent-card", MetricCard).update_value(time_str)

        # Update favorites
        if progress.favorite_topics:
            favorites_text = "\n".join(f"• {topic.title()}" for topic in progress.favorite_topics)
        else:
            favorites_text = "Complete more projects to discover your favorite topics!"

        self.query_one("#favorites-list").update(favorites_text)


class InsightsPanel(DashboardPanel):
    """Insights panel showing AI-generated recommendations."""

    def compose(self) -> ComposeResult:
        with Vertical(id="insights-content"):
            # Next best actions
            yield Static("### 🎯 Next Best Actions", id="actions-header")
            yield Static("Loading personalized recommendations...", id="actions-list")

            # Learning goals
            yield Static("### 🎯 Learning Goals", id="goals-header")
            yield Static("Loading your learning goals...", id="goals-list")

            # Key insights
            yield Static("### 💡 Key Insights", id="insights-header")
            yield Static("Loading AI insights...", id="insights-list")

    def update_data(self, progress=None, skills=None, community=None, insights=None):
        """Update insights panel with data."""
        if not insights:
            return

        # Update next actions
        if insights.next_best_actions:
            actions_text = "\n".join(f"• {action}" for action in insights.next_best_actions)
            self.query_one("#actions-list").update(actions_text)

        # Update learning goals
        if insights.learning_goals:
            goals_text = "\n".join(f"• {goal}" for goal in insights.learning_goals)
            self.query_one("#goals-list").update(goals_text)

        # Update key insights
        if insights.insights:
            insights_text = ""
            for insight in insights.insights[:5]:  # Show top 5
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(insight.priority, "⚪")
                insights_text += f"{priority_icon} **{insight.title}**\n"
                insights_text += f"   {insight.description}\n\n"
            self.query_one("#insights-list").update(insights_text)


class CommunityPanel(DashboardPanel):
    """Community panel showing community-wide analytics."""

    def compose(self) -> ComposeResult:
        with Vertical(id="community-content"):
            # Community metrics
            with Horizontal(id="community-metrics"):
                yield MetricCard("Active Users", "0", id="active-users-card")
                yield MetricCard("New Users", "0", id="new-users-card")
                yield MetricCard("Engagement Rate", "0%", id="engagement-card")
                yield MetricCard("Total Projects", "0", id="total-projects-card")

            # Popular topics
            yield Static("### 🔥 Popular Topics", id="popular-header")
            yield Static("Loading trending topics...", id="popular-list")

            # Community health
            yield Static("### 🌱 Community Health", id="health-header")
            with Horizontal():
                yield MetricCard("Retention Rate", "0%", id="retention-card")
                yield MetricCard("Growth Rate", "0%", id="growth-card")

    def update_data(self, progress=None, skills=None, community=None, insights=None):
        """Update community panel with data."""
        if not community:
            return

        metrics = community['user_metrics']
        content = community['content_metrics']

        # Update community metrics
        self.query_one("#active-users-card", MetricCard).update_value(str(metrics['active_users']))
        self.query_one("#new-users-card", MetricCard).update_value(str(metrics['new_users']))
        self.query_one("#engagement-card", MetricCard).update_value(f"{metrics['engagement_rate']:.1%}")
        self.query_one("#total-projects-card", MetricCard).update_value(str(content['total_projects']))

        # Update popular topics
        popular_topics = community['topic_analytics']['popular_topics'][:5]
        if popular_topics:
            topics_text = "\n".join(f"• {topic[0].title()} ({topic[1]} interactions)" for topic in popular_topics)
            self.query_one("#popular-list").update(topics_text)

        # Update health metrics (simplified)
        self.query_one("#retention-card", MetricCard).update_value(f"{metrics['retention_rate']:.1%}")
        self.query_one("#growth-card", MetricCard).update_value("Calculating...")


class MetricCard(Widget):
    """A card displaying a single metric."""

    def __init__(self, title: str, value: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical(classes="metric-card"):
            yield Label(self.title, classes="metric-title")
            yield Label(self.value, classes="metric-value")

    def update_value(self, new_value: str):
        """Update the displayed value."""
        self.value = new_value
        label = self.query_one(".metric-value", Label)
        label.update(new_value)
