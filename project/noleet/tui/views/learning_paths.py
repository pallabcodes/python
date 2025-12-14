"""
TUI Views for Learning Paths System.

This module provides rich terminal interfaces for browsing, creating,
and managing learning paths in NoLeet.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, Input, TextArea,
    Select, Tabs, Tab, DataTable, ProgressBar, Checkbox,
    Collapsible, ListView, ListItem
)
from textual.widget import Widget
from textual import on
from textual.validation import Number, Length

from learning_paths.path_engine import PathEngine
from learning_paths.path_recommender import PathRecommender
from learning_paths.community_paths import CommunityPathManager
from learning_paths.models import LearningPathData, PathRecommendationData
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class LearningPathsView(Vertical):
    """Main learning paths view with tabs for different functionalities."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session

        # Initialize engines
        self.path_engine = PathEngine(db_session)
        self.path_recommender = PathRecommender(db_session)
        self.community_manager = CommunityPathManager(db_session)

    def compose(self) -> ComposeResult:
        yield Header()

        with Tabs():
            with Tab("Browse Paths", id="browse-tab"):
                yield PathBrowserView(self.user_id, self.db)

            with Tab("My Paths", id="my-paths-tab"):
                yield MyPathsView(self.user_id, self.db)

            with Tab("Recommendations", id="recommendations-tab"):
                yield PathRecommendationsView(self.user_id, self.db)

            with Tab("Create Path", id="create-tab"):
                yield CreatePathView(self.user_id, self.db)

            with Tab("Community", id="community-tab"):
                yield CommunityPathsView(self.user_id, self.db)

        yield Footer()


class PathBrowserView(Vertical):
    """Browse available learning paths."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session
        self.path_engine = PathEngine(db_session)
        self.current_page = 0
        self.page_size = 10
        self.paths = []

    def compose(self) -> ComposeResult:
        with Vertical():
            # Search and filter controls
            with Horizontal(id="search-controls"):
                yield Input(placeholder="Search paths...", id="search-input")
                yield Select(
                    [("all", "All"), ("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                    prompt="Difficulty",
                    id="difficulty-filter"
                )
                yield Button("Search", id="search-btn")

            # Results table
            yield DataTable(id="paths-table")

            # Pagination controls
            with Horizontal(id="pagination"):
                yield Button("Previous", id="prev-btn", disabled=True)
                yield Static("Page 1", id="page-info")
                yield Button("Next", id="next-btn", disabled=True)

    async def on_mount(self) -> None:
        """Load initial path data."""
        await self.load_paths()

    async def load_paths(self, search_query: str = "", difficulty: str = "all") -> None:
        """Load paths based on search and filter criteria."""
        try:
            # This would integrate with a path search/indexing system
            # For now, show some example paths
            self.paths = [
                {
                    'id': 1,
                    'title': 'Dynamic Programming Mastery',
                    'difficulty': 'hard',
                    'duration': 8,
                    'projects': 12,
                    'rating': 4.8,
                    'enrolled': 245
                },
                {
                    'id': 2,
                    'title': 'Graph Algorithms Fundamentals',
                    'difficulty': 'medium',
                    'duration': 6,
                    'projects': 8,
                    'rating': 4.6,
                    'enrolled': 189
                }
            ]

            await self.update_table()

        except Exception as e:
            logger.error(f"Failed to load paths: {e}")

    async def update_table(self) -> None:
        """Update the paths table with current data."""
        table = self.query_one("#paths-table", DataTable)
        table.clear()

        table.add_columns(
            "Title", "Difficulty", "Duration", "Projects",
            "Rating", "Enrolled", "Action"
        )

        for path in self.paths:
            table.add_row(
                path['title'],
                path['difficulty'].title(),
                f"{path['duration']} weeks",
                str(path['projects']),
                f"★ {path['rating']}",
                str(path['enrolled']),
                "View Details"
            )

    @on(Button.Pressed, "#search-btn")
    async def search_paths(self) -> None:
        """Handle search button press."""
        search_input = self.query_one("#search-input", Input)
        difficulty_select = self.query_one("#difficulty-filter", Select)

        query = search_input.value
        difficulty = difficulty_select.value or "all"

        await self.load_paths(query, difficulty)


class MyPathsView(Vertical):
    """View and manage user's enrolled learning paths."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session
        self.path_engine = PathEngine(db_session)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("### My Learning Paths", classes="section-header")

            # Enrolled paths
            yield Static("#### Active Paths", classes="subsection-header")
            yield DataTable(id="active-paths-table")

            # Completed paths
            yield Static("#### Completed Paths", classes="subsection-header")
            yield DataTable(id="completed-paths-table")

            # Path progress details (when selected)
            with Collapsible(title="Path Details", id="path-details"):
                yield PathProgressView(self.user_id, self.db)

    async def on_mount(self) -> None:
        """Load user's path data."""
        await self.load_user_paths()

    async def load_user_paths(self) -> None:
        """Load user's enrolled and completed paths."""
        try:
            # This would query actual enrollment data
            # For now, show example data
            active_paths = [
                {'id': 1, 'title': 'Dynamic Programming Mastery', 'progress': 65, 'current_step': 8, 'total_steps': 12},
                {'id': 2, 'title': 'Graph Algorithms Fundamentals', 'progress': 30, 'current_step': 3, 'total_steps': 8}
            ]

            completed_paths = [
                {'id': 3, 'title': 'Array Manipulation Techniques', 'completed_at': '2024-01-15', 'rating': 5}
            ]

            # Update active paths table
            active_table = self.query_one("#active-paths-table", DataTable)
            active_table.clear()
            active_table.add_columns("Path", "Progress", "Current Step", "Action")

            for path in active_paths:
                progress_bar = ProgressBar(total=100, id=f"progress-{path['id']}")
                progress_bar.progress = path['progress']
                active_table.add_row(
                    path['title'],
                    f"{path['progress']}%",
                    f"{path['current_step']}/{path['total_steps']}",
                    "Continue"
                )

            # Update completed paths table
            completed_table = self.query_one("#completed-paths-table", DataTable)
            completed_table.clear()
            completed_table.add_columns("Path", "Completed", "Rating", "Certificate")

            for path in completed_paths:
                completed_table.add_row(
                    path['title'],
                    path['completed_at'],
                    f"★ {path['rating']}",
                    "Download"
                )

        except Exception as e:
            logger.error(f"Failed to load user paths: {e}")


class PathProgressView(Vertical):
    """Detailed view of a specific path's progress."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session
        self.current_path_id = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Path Progress Details", id="progress-title")

            # Overall progress
            with Horizontal():
                yield Static("Overall Progress: ", id="overall-progress-label")
                yield ProgressBar(total=100, id="overall-progress-bar")

            # Current step info
            yield Static("Current Step", classes="subsection-header")
            yield Static("Loading...", id="current-step-info")

            # Next steps
            yield Static("Next Steps", classes="subsection-header")
            yield ListView(id="next-steps-list")

            # Path statistics
            with Horizontal():
                yield MetricCard("Time Spent", "0h 0m", id="time-spent-card")
                yield MetricCard("Steps Completed", "0/0", id="steps-completed-card")
                yield MetricCard("Est. Completion", "0 weeks", id="completion-estimate-card")

    def update_path(self, path_id: int) -> None:
        """Update view for a specific path."""
        self.current_path_id = path_id
        # This would load actual path progress data
        # For now, show example data

        self.query_one("#progress-title").update(f"Progress: Sample Path")
        self.query_one("#overall-progress-bar", ProgressBar).progress = 65
        self.query_one("#overall-progress-label").update("Overall Progress: 65%")

        self.query_one("#current-step-info").update(
            "**Step 8: Advanced DP Optimization**\n"
            "Learn advanced techniques for optimizing dynamic programming solutions."
        )

        # Update next steps
        next_steps_list = self.query_one("#next-steps-list", ListView)
        next_steps_list.clear()
        next_steps = [
            "Step 9: Space Optimization Techniques",
            "Step 10: Real-world DP Applications",
            "Step 11: Performance Analysis",
            "Step 12: Final Project"
        ]
        for step in next_steps:
            next_steps_list.append(ListItem(Static(step)))

        # Update metrics
        self.query_one("#time-spent-card", MetricCard).update_value("24h 30m")
        self.query_one("#steps-completed-card", MetricCard).update_value("7/12")
        self.query_one("#completion-estimate-card", MetricCard).update_value("3 weeks")


class PathRecommendationsView(Vertical):
    """View personalized path recommendations."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session
        self.path_recommender = PathRecommender(db_session)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("### Personalized Recommendations", classes="section-header")
            yield Static("AI-powered suggestions based on your skills and goals", classes="subtitle")

            # Recommendations list
            yield ScrollableContainer(id="recommendations-container")

            # Refresh button
            yield Button("🔄 Refresh Recommendations", id="refresh-btn")

    async def on_mount(self) -> None:
        """Load initial recommendations."""
        await self.load_recommendations()

    async def load_recommendations(self) -> None:
        """Load personalized path recommendations."""
        try:
            container = self.query_one("#recommendations-container", ScrollableContainer)
            container.remove_children()

            # Get recommendations
            recommendations = await self.path_recommender.get_recommendations(self.user_id)

            if not recommendations:
                container.mount(Static("No recommendations available. Complete more projects to get personalized suggestions!"))
                return

            for rec in recommendations:
                recommendation_card = RecommendationCard(rec)
                container.mount(recommendation_card)

        except Exception as e:
            logger.error(f"Failed to load recommendations: {e}")
            container = self.query_one("#recommendations-container", ScrollableContainer)
            container.mount(Static(f"Error loading recommendations: {str(e)}"))

    @on(Button.Pressed, "#refresh-btn")
    async def refresh_recommendations(self) -> None:
        """Refresh recommendations."""
        await self.load_recommendations()


class RecommendationCard(Vertical):
    """Card displaying a single path recommendation."""

    def __init__(self, recommendation: PathRecommendationData, **kwargs):
        super().__init__(**kwargs)
        self.recommendation = recommendation

    def compose(self) -> ComposeResult:
        with Vertical(classes="recommendation-card"):
            # Header with title and score
            with Horizontal():
                yield Static(f"**{self.recommendation.path_title}**", classes="rec-title")
                score_color = "green" if self.recommendation.recommendation_score > 0.8 else "yellow" if self.recommendation.recommendation_score > 0.6 else "red"
                yield Static(f"Match: {self.recommendation.recommendation_score:.1%}", classes=f"rec-score-{score_color}")

            # Path details
            yield Static(f"Difficulty: {self.recommendation.difficulty.title()} | "
                        f"Duration: {self.recommendation.estimated_duration} weeks | "
                        f"Projects: {self.recommendation.total_projects}")

            # Reasoning
            yield Static(f"**Why recommended:** {self.recommendation.reasoning}", classes="rec-reasoning")

            # Matching topics
            if self.recommendation.matching_topics:
                yield Static(f"**Matching interests:** {', '.join(self.recommendation.matching_topics)}")

            # Action buttons
            with Horizontal():
                yield Button("View Details", classes="primary-btn")
                yield Button("Enroll Now", classes="success-btn")

    @on(Button.Pressed, ".success-btn")
    async def enroll_in_path(self) -> None:
        """Handle enrollment button press."""
        # This would trigger actual enrollment
        self.notify(f"Enrolling in: {self.recommendation.path_title}")


class CreatePathView(Vertical):
    """Interface for creating new learning paths."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session
        self.community_manager = CommunityPathManager(db_session)
        self.steps = []

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("### Create Learning Path", classes="section-header")

            # Basic information
            yield Input(placeholder="Path Title", id="path-title", validators=[Length(minimum=5)])
            yield TextArea(placeholder="Path Description", id="path-description", validators=[Length(minimum=20)])

            with Horizontal():
                yield Select(
                    [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                    prompt="Difficulty Level",
                    id="path-difficulty",
                    value="medium"
                )
                yield Input(placeholder="Tags (comma-separated)", id="path-tags")

            # Steps section
            yield Static("### Path Steps", classes="section-header")
            yield Button("➕ Add Step", id="add-step-btn")

            # Steps container
            yield Vertical(id="steps-container")

            # Action buttons
            with Horizontal():
                yield Button("Preview Path", id="preview-btn")
                yield Button("Submit for Review", id="submit-btn", disabled=True)

    @on(Button.Pressed, "#add-step-btn")
    def add_step(self) -> None:
        """Add a new step to the path."""
        step_widget = PathStepWidget(step_number=len(self.steps) + 1)
        self.query_one("#steps-container", Vertical).mount(step_widget)
        self.steps.append(step_widget)

        # Enable submit button if we have minimum steps
        submit_btn = self.query_one("#submit-btn", Button)
        submit_btn.disabled = len(self.steps) < 3

    @on(Button.Pressed, "#preview-btn")
    async def preview_path(self) -> None:
        """Preview the path before submission."""
        # Collect path data
        path_data = self.collect_path_data()

        if not path_data['title'] or not path_data['description']:
            self.notify("Please fill in title and description", severity="warning")
            return

        # Validate path
        validation = await self.community_manager.validate_path_data(path_data)

        # Show preview modal or section
        self.notify(f"Path validation: {validation.quality_score:.1%} quality score")

    @on(Button.Pressed, "#submit-btn")
    async def submit_path(self) -> None:
        """Submit the path for community review."""
        path_data = self.collect_path_data()

        try:
            path, validation = await self.community_manager.submit_community_path(
                self.user_id, path_data
            )

            self.notify(
                f"Path submitted successfully! Quality score: {validation.quality_score:.1%}",
                severity="success"
            )

            # Reset form
            self.reset_form()

        except Exception as e:
            self.notify(f"Failed to submit path: {str(e)}", severity="error")

    def collect_path_data(self) -> Dict[str, Any]:
        """Collect path data from form inputs."""
        return {
            'title': self.query_one("#path-title", Input).value,
            'description': self.query_one("#path-description", TextArea).value,
            'difficulty': self.query_one("#path-difficulty", Select).value,
            'tags': [tag.strip() for tag in self.query_one("#path-tags", Input).value.split(',') if tag.strip()],
            'steps': [step.collect_data() for step in self.steps]
        }

    def reset_form(self) -> None:
        """Reset the form to initial state."""
        self.query_one("#path-title", Input).value = ""
        self.query_one("#path-description", TextArea).value = ""
        self.query_one("#path-tags", Input).value = ""

        # Clear steps
        steps_container = self.query_one("#steps-container", Vertical)
        steps_container.remove_children()
        self.steps = []

        self.query_one("#submit-btn", Button).disabled = True


class PathStepWidget(Vertical):
    """Widget for editing a single path step."""

    def __init__(self, step_number: int, **kwargs):
        super().__init__(**kwargs)
        self.step_number = step_number

    def compose(self) -> ComposeResult:
        with Vertical(classes="step-widget"):
            yield Static(f"**Step {self.step_number}**", classes="step-header")

            yield Input(placeholder="Step Title", id=f"step-{self.step_number}-title")
            yield TextArea(placeholder="Step Description", id=f"step-{self.step_number}-description")

            with Horizontal():
                yield Input(
                    placeholder="Time (minutes)",
                    id=f"step-{self.step_number}-time",
                    validators=[Number(minimum=15, maximum=480)]
                )
                yield Input(
                    placeholder="Required Skills (comma-separated)",
                    id=f"step-{self.step_number}-skills"
                )

            yield Button("🗑️ Remove Step", id=f"remove-step-{self.step_number}", classes="danger-btn")

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id and event.button.id.startswith("remove-step-"):
            self.remove()

    def collect_data(self) -> Dict[str, Any]:
        """Collect step data."""
        return {
            'title': self.query_one(f"#step-{self.step_number}-title", Input).value,
            'description': self.query_one(f"#step-{self.step_number}-description", TextArea).value,
            'estimated_time': int(self.query_one(f"#step-{self.step_number}-time", Input).value or 60),
            'required_skills': [
                skill.strip() for skill in
                self.query_one(f"#step-{self.step_number}-skills", Input).value.split(',')
                if skill.strip()
            ]
        }


class CommunityPathsView(Vertical):
    """View community path creation and moderation."""

    def __init__(self, user_id: int, db_session, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = db_session
        self.community_manager = CommunityPathManager(db_session)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("### Community Path Hub", classes="section-header")

            with Tabs():
                with Tab("My Contributions", id="my-contributions"):
                    yield DataTable(id="my-paths-table")

                with Tab("Pending Review", id="pending-review"):
                    yield DataTable(id="pending-table")

                with Tab("Top Contributors", id="contributors"):
                    yield DataTable(id="contributors-table")

            # Quick stats
            with Horizontal(id="community-stats"):
                yield MetricCard("Your Paths", "0", id="your-paths-card")
                yield MetricCard("Total Upvotes", "0", id="upvotes-card")
                yield MetricCard("Avg Quality", "0%", id="quality-card")

    async def on_mount(self) -> None:
        """Load community data."""
        await self.load_community_data()

    async def load_community_data(self) -> None:
        """Load community statistics and data."""
        try:
            # Load user's contributions
            my_paths = [
                {'title': 'Advanced Graph Algorithms', 'status': 'approved', 'upvotes': 25, 'quality': 0.85},
                {'title': 'System Design Patterns', 'status': 'pending', 'upvotes': 0, 'quality': 0.78}
            ]

            my_table = self.query_one("#my-paths-table", DataTable)
            my_table.clear()
            my_table.add_columns("Title", "Status", "Upvotes", "Quality", "Actions")

            for path in my_paths:
                my_table.add_row(
                    path['title'],
                    path['status'].title(),
                    str(path['upvotes']),
                    f"{path['quality']:.1%}",
                    "Edit" if path['status'] == 'pending' else "View"
                )

            # Load top contributors
            contributors = self.community_manager.get_top_contributors()

            contrib_table = self.query_one("#contributors-table", DataTable)
            contrib_table.clear()
            contrib_table.add_columns("Contributor", "Paths Created", "Total Upvotes", "Avg Quality")

            for contrib in contributors:
                contrib_table.add_row(
                    f"User {contrib['user_id']}",
                    str(contrib['paths_created']),
                    str(contrib['total_upvotes']),
                    f"{contrib['avg_quality']:.1%}"
                )

            # Update stats
            self.query_one("#your-paths-card", MetricCard).update_value(str(len(my_paths)))
            self.query_one("#upvotes-card", MetricCard).update_value("25")
            self.query_one("#quality-card", MetricCard).update_value("81%")

        except Exception as e:
            logger.error(f"Failed to load community data: {e}")


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
