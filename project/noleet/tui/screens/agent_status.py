"""Agent status screen for monitoring agent activity."""

from typing import Dict, Any
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Button, Label, ListView, ListItem,
    ProgressBar, TextArea
)
from textual import on
from textual.screen import Screen


class AgentStatusScreen(Screen):
    """Screen for monitoring agent activity and workflows."""

    def __init__(self, **kwargs):
        """Initialize agent status screen."""
        super().__init__(**kwargs)
        self.agent_status: Dict[str, Any] = {}
        self.workflow_history: list[Dict[str, Any]] = []

    def compose(self):
        """Compose the agent status layout."""
        with ScrollableContainer():
            # Header
            with Horizontal():
                yield Button("⬅️ Back to Main", id="back-btn")
                yield Static("🤖 Agent Status Monitor", classes="card-title")

            # Agent status overview
            with Container(classes="card"):
                yield Label("Agent Overview", classes="card-title")
                yield ListView(id="agent-list")

                with Horizontal():
                    yield Button("🔄 Refresh Status", id="refresh-btn")
                    yield Button("⚡ Run Diagnostics", id="diagnostics-btn")

            # Active workflows
            with Container(classes="card"):
                yield Label("Active Workflows", classes="card-title")
                yield ListView(id="workflow-list")
                yield ProgressBar(id="workflow-progress", total=100)

            # Recent activity
            with Container(classes="card"):
                yield Label("Recent Activity", classes="card-title")
                yield TextArea("", id="activity-log", read_only=True)

            # System metrics
            with Container(classes="card"):
                yield Label("System Metrics", classes="card-title")
                yield Static("Loading metrics...", id="metrics-display")

    def on_mount(self):
        """Initialize when screen is mounted."""
        self._load_agent_status()
        self._update_metrics()

    def _load_agent_status(self):
        """Load current agent status."""
        # This would integrate with the actual agent orchestrator
        # For now, show mock data
        mock_agents = [
            {"name": "sentiment_analysis", "status": "idle", "last_active": "2 min ago"},
            {"name": "question_analysis", "status": "idle", "last_active": "1 min ago"},
            {"name": "project_recommendation", "status": "idle", "last_active": "30 sec ago"},
            {"name": "research_matching", "status": "idle", "last_active": "5 min ago"},
        ]

        agent_list = self.query_one("#agent-list", ListView)
        agent_list.clear()

        for agent in mock_agents:
            status_indicator = "🟢" if agent["status"] == "active" else "⚪"
            display_text = f"{status_indicator} {agent['name']} - {agent['status']} ({agent['last_active']})"
            agent_list.append(ListItem(Static(display_text)))

            # Store status
            self.agent_status[agent["name"]] = agent

    @on(Button.Pressed, "#refresh-btn")
    def on_refresh_status(self):
        """Handle refresh status button press."""
        self._load_agent_status()
        self._update_metrics()
        self.app.notify_user("Agent status refreshed", "Info")

    @on(Button.Pressed, "#diagnostics-btn")
    async def on_run_diagnostics(self):
        """Handle run diagnostics button press."""
        self.app.notify_user("Running agent diagnostics...", "Info")

        # Simulate diagnostics
        await self._simulate_diagnostics()

        self.app.notify_user("Diagnostics completed", "Success")

    async def _simulate_diagnostics(self):
        """Simulate running diagnostics."""
        import asyncio

        progress_bar = self.query_one("#workflow-progress", ProgressBar)

        # Simulate progress
        for i in range(0, 101, 20):
            progress_bar.progress = i
            await asyncio.sleep(0.2)

        # Update activity log
        activity_log = self.query_one("#activity-log", TextArea)
        activity_log.text += "\n✅ All agents responding\n✅ Memory usage normal\n✅ Network connectivity OK\n✅ LLM services available\n"

    @on(Button.Pressed, "#back-btn")
    def on_back_pressed(self):
        """Handle back button press."""
        self.app.show_screen("main")

    def update_agent_activity(self, agent_name: str, activity: str):
        """
        Update agent activity display.

        Args:
            agent_name: Name of the agent
            activity: Activity description
        """
        activity_log = self.query_one("#activity-log", TextArea)
        activity_log.text += f"\n[{agent_name}] {activity}"

        # Scroll to bottom
        activity_log.scroll_to_bottom()

    def update_workflow_status(self, workflow_name: str, status: str, progress: int = 0):
        """
        Update workflow status.

        Args:
            workflow_name: Name of the workflow
            status: Status description
            progress: Progress percentage
        """
        workflow_list = self.query_one("#workflow-list", ListView)

        # Find existing workflow or add new one
        existing_item = None
        for item in workflow_list.children:
            if workflow_name in item.renderable.plain:
                existing_item = item
                break

        display_text = f"⚙️ {workflow_name}: {status}"

        if existing_item:
            existing_item.renderable.update(display_text)
        else:
            workflow_list.append(ListItem(Static(display_text)))

        # Update progress bar
        progress_bar = self.query_one("#workflow-progress", ProgressBar)
        progress_bar.progress = progress

        # Add to activity log
        activity_log = self.query_one("#activity-log", TextArea)
        activity_log.text += f"\n[WORKFLOW] {workflow_name}: {status}"

    def _update_metrics(self):
        """Update system metrics display."""
        # Mock metrics - in real implementation, get from actual system
        metrics = """
System Metrics:
• Memory Usage: 245 MB
• CPU Usage: 12%
• Active Agents: 4
• Completed Workflows: 3
• LLM Requests (last hour): 12
• Average Response Time: 2.3s
        """.strip()

        metrics_display = self.query_one("#metrics-display", Static)
        metrics_display.update(metrics)

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get status of a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent status information
        """
        return self.agent_status.get(agent_name, {"status": "unknown"})

    def log_system_event(self, event_type: str, message: str):
        """
        Log a system event.

        Args:
            event_type: Type of event (INFO, ERROR, etc.)
            message: Event message
        """
        activity_log = self.query_one("#activity-log", TextArea)
        activity_log.text += f"\n[{event_type}] {message}"

        # Keep log size manageable
        lines = activity_log.text.split('\n')
        if len(lines) > 100:
            activity_log.text = '\n'.join(lines[-100:])
