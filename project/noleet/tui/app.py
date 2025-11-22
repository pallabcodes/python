"""Main Textual application for NoLeet."""

import asyncio
from typing import Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    ListView, ListItem, Label, ProgressBar, Tabs, Tab
)
from textual import events
from textual.binding import Binding

from .screens.main_screen import MainScreen
from .screens.project_browser import ProjectBrowser
from .screens.agent_status import AgentStatusScreen


class NoLeetApp(App):
    """Main NoLeet Textual application."""

    TITLE = "NoLeet - Build Products from DSA"
    SUB_TITLE = "Transform algorithm learning into real-world projects"
    CSS_PATH = "app.css"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize NoLeet app.

        Args:
            data_dir: Directory containing project data
        """
        super().__init__()
        self.data_dir = data_dir or Path.home() / ".noleet" / "data"
        self.current_screen = "main"

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Container(id="main-container"):
            yield MainScreen(id="main-screen")
            yield ProjectBrowser(id="project-browser", classes="hidden")
            yield AgentStatusScreen(id="agent-status", classes="hidden")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE

        # Show main screen initially
        self.show_screen("main")

    def show_screen(self, screen_name: str) -> None:
        """
        Show a specific screen.

        Args:
            screen_name: Name of screen to show
        """
        # Hide all screens
        for screen_id in ["main-screen", "project-browser", "agent-status"]:
            self.query_one(f"#{screen_id}").add_class("hidden")

        # Show target screen
        target_id = f"{screen_name.replace('_', '-')}-screen"
        if screen_name == "project_browser":
            target_id = "project-browser"
        elif screen_name == "agent_status":
            target_id = "agent-status"

        try:
            self.query_one(f"#{target_id}").remove_class("hidden")
            self.current_screen = screen_name
        except Exception as e:
            self.notify(f"Error showing screen {screen_name}: {e}", severity="error")

    def action_show_help(self) -> None:
        """Show help dialog."""
        help_text = """
        NoLeet - Build Products from DSA

        Navigation:
        - Tab: Switch between screens
        - Enter: Select/Execute
        - Arrow Keys: Navigate lists
        - q: Quit application

        Screens:
        - Main: Topic selection and project discovery
        - Projects: Browse and view project details
        - Agents: Monitor agent activity and workflows

        Features:
        - Intelligent project recommendations
        - Multi-agent analysis system
        - Research paper integration
        - Sentiment analysis
        - Semantic search

        Press any key to close this help.
        """

        # Show help in a modal or notification
        self.notify(help_text, title="Help", timeout=10)

    async def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if event.key == "tab":
            # Cycle through screens
            screens = ["main", "project_browser", "agent_status"]
            current_idx = screens.index(self.current_screen) if self.current_screen in screens else 0
            next_idx = (current_idx + 1) % len(screens)
            self.show_screen(screens[next_idx])
            self.notify(f"Switched to {screens[next_idx].replace('_', ' ').title()}")

    def notify_user(self, message: str, title: str = "Info", severity: str = "information") -> None:
        """
        Notify user with a message.

        Args:
            message: Notification message
            title: Notification title
            severity: Severity level (information, warning, error)
        """
        self.notify(message, title=title, severity=severity)

    def get_data_dir(self) -> Path:
        """Get the data directory."""
        return self.data_dir

    def run_async_task(self, coro) -> None:
        """
        Run an async task in the background.

        Args:
            coro: Coroutine to run
        """
        asyncio.create_task(coro)
