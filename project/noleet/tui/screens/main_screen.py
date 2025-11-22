"""Main screen for topic selection and project discovery."""

from typing import List, Optional
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Button, Input, Label, ListView, ListItem,
    ProgressBar, TextArea
)
from textual import on
from textual.screen import Screen

from ...core.models import Topic
from ...agents.agent_orchestrator import AgentOrchestrator
from ...llm.llm_config import LLMConfig


class MainScreen(Screen):
    """Main screen with topic selection and project discovery."""

    def __init__(self, **kwargs):
        """Initialize main screen."""
        super().__init__(**kwargs)
        self.selected_topics: List[str] = []
        self.orchestrator: Optional[AgentOrchestrator] = None

    def compose(self):
        """Compose the main screen layout."""
        with ScrollableContainer(id="main-scroll"):
            # Title and description
            yield Static("🎯 NoLeet: Build Products from DSA", id="title", classes="card-title")
            yield Static(
                "Transform algorithm learning into real-world projects. "
                "Select DSA topics and get intelligent project recommendations.",
                id="subtitle"
            )

            # Topic selection section
            with Container(classes="card"):
                yield Label("📚 Select DSA Topics", classes="card-title")
                yield Static("Choose one or more topics to find matching projects:")

                # Topic list
                with Horizontal():
                    # Available topics
                    with Vertical():
                        yield Label("Available Topics:")
                        yield ListView(
                            *[ListItem(Static(self._format_topic_name(topic))) for topic in Topic],
                            id="topic-list"
                        )

                    # Selected topics
                    with Vertical():
                        yield Label("Selected Topics:")
                        yield ListView(id="selected-topics")
                        yield Button("🔍 Find Projects", id="find-projects-btn", variant="primary")

            # Query input section
            with Container(classes="card"):
                yield Label("💭 Natural Language Query", classes="card-title")
                yield Static("Describe what you want to build or learn:")
                yield Input(placeholder="e.g., 'projects with dynamic programming and sliding window'", id="query-input")
                yield Button("🚀 Get Recommendations", id="recommend-btn", variant="primary")

            # Results section
            with Container(classes="card", id="results-section"):
                yield Label("📋 Project Recommendations", classes="card-title", id="results-title")
                yield ListView(id="recommendations-list")
                yield Button("👁️ View Details", id="view-details-btn", disabled=True)

            # Status section
            with Container(classes="card"):
                yield Label("⚡ System Status", classes="card-title")
                yield Static("Agent Status: Initializing...", id="agent-status")
                yield ProgressBar(id="progress-bar", total=100)

    def on_mount(self):
        """Initialize when screen is mounted."""
        # Initialize orchestrator
        config = LLMConfig()
        self.orchestrator = AgentOrchestrator(config)

        # Update status
        self._update_status("Ready to analyze topics and queries")

    def _format_topic_name(self, topic: Topic) -> str:
        """Format topic name for display."""
        return topic.value.replace("_", " ").title()

    @on(ListView.Selected, "#topic-list")
    def on_topic_selected(self, event: ListView.Selected):
        """Handle topic selection."""
        topic_item = event.item
        topic_name = topic_item.renderable.plain

        # Convert back to enum value
        topic_value = topic_name.lower().replace(" ", "_")

        if topic_value not in self.selected_topics:
            self.selected_topics.append(topic_value)

            # Add to selected topics list
            selected_list = self.query_one("#selected-topics", ListView)
            selected_list.append(ListItem(Static(f"✅ {topic_name}")))

            self._update_status(f"Selected {len(self.selected_topics)} topics")
        else:
            # Remove from selection
            self.selected_topics.remove(topic_value)
            selected_list = self.query_one("#selected-topics", ListView)

            # Find and remove the item
            for item in selected_list.children:
                if topic_name in item.renderable.plain:
                    selected_list.remove_children(item)
                    break

            self._update_status(f"Deselected {topic_name}")

    @on(Button.Pressed, "#find-projects-btn")
    async def on_find_projects(self):
        """Handle find projects button press."""
        if not self.selected_topics:
            self._show_error("Please select at least one topic")
            return

        self._update_status("Analyzing topics and finding projects...")
        self._set_progress(25)

        try:
            # Create recommendation workflow
            workflow_name = self.orchestrator.create_recommendation_workflow()

            # Execute workflow
            result = await self.app.run_async_task(
                self.orchestrator.execute_workflow(
                    workflow_name,
                    {
                        "topics": self.selected_topics,
                        "user_id": "tui_user",
                        "max_recommendations": 5
                    }
                )
            )

            self._display_recommendations(result)
            self._set_progress(100)
            self._update_status("Project recommendations ready")

        except Exception as e:
            self._show_error(f"Error finding projects: {e}")
            self._set_progress(0)

    @on(Button.Pressed, "#recommend-btn")
    async def on_get_recommendations(self):
        """Handle get recommendations button press."""
        query_input = self.query_one("#query-input", Input)
        query = query_input.value.strip()

        if not query:
            self._show_error("Please enter a query")
            return

        self._update_status("Processing natural language query...")
        self._set_progress(25)

        try:
            # Execute recommendation workflow
            result = await self.app.run_async_task(
                self.orchestrator.execute_recommendation_workflow(
                    user_query=query,
                    user_id="tui_user",
                    topics=self.selected_topics if self.selected_topics else None
                )
            )

            self._display_recommendations(result)
            self._set_progress(100)
            self._update_status("Intelligent recommendations ready")

        except Exception as e:
            self._show_error(f"Error getting recommendations: {e}")
            self._set_progress(0)

    def _display_recommendations(self, result):
        """Display recommendation results."""
        recommendations_list = self.query_one("#recommendations-list", ListView)
        recommendations_list.clear()

        if not result.get("success"):
            self._show_error(f"Recommendation failed: {result.get('error', 'Unknown error')}")
            return

        workflow_results = result.get("results", {})
        rec_result = workflow_results.get("project_recommendation_agent", {})

        recommendations = rec_result.get("recommendations", [])

        if not recommendations:
            recommendations_list.append(ListItem(Static("❌ No matching projects found")))
            return

        for rec in recommendations:
            title = rec.get("title", "Unknown")
            score = rec.get("score", 0)
            difficulty = rec.get("difficulty", "unknown")

            display_text = f"⭐ {title} (Score: {score:.2f}, {difficulty.title()})"
            recommendations_list.append(ListItem(Static(display_text)))

        # Enable view details button
        view_btn = self.query_one("#view-details-btn", Button)
        view_btn.disabled = False

        self._update_status(f"Found {len(recommendations)} project recommendations")

    @on(Button.Pressed, "#view-details-btn")
    def on_view_details(self):
        """Handle view details button press."""
        # Switch to project browser screen
        self.app.show_screen("project_browser")

    def _update_status(self, message: str):
        """Update status display."""
        status_label = self.query_one("#agent-status", Static)
        status_label.update(f"Agent Status: {message}")

    def _set_progress(self, value: int):
        """Set progress bar value."""
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.progress = value

    def _show_error(self, message: str):
        """Show error message."""
        self.app.notify_user(message, "Error", "error")
        self._update_status(f"Error: {message}")
        self._set_progress(0)

    def _show_success(self, message: str):
        """Show success message."""
        self.app.notify_user(message, "Success", "information")
        self._update_status(message)
