"""Project browser screen for viewing project details."""

from typing import Optional
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Button, Label, ListView, ListItem,
    TextArea, Tabs, Tab, TabbedContent
)
from textual import on
from textual.screen import Screen

from ...storage.repository import ProjectRepository
from ...core.models import Project


class ProjectBrowser(Screen):
    """Screen for browsing and viewing project details."""

    def __init__(self, **kwargs):
        """Initialize project browser."""
        super().__init__(**kwargs)
        self.projects: list[Project] = []
        self.current_project: Optional[Project] = None
        self.repository = ProjectRepository()

    def compose(self):
        """Compose the project browser layout."""
        with ScrollableContainer():
            # Header
            with Horizontal():
                yield Button("⬅️ Back to Main", id="back-btn")
                yield Static("📂 Project Browser", classes="card-title")

            # Project list
            with Container(classes="card"):
                yield Label("Available Projects:")
                yield ListView(id="project-list")

            # Project details (shown when project selected)
            with Container(classes="card", id="project-details", classes="hidden"):
                yield Label("Project Details", classes="card-title", id="project-title")

                with TabbedContent():
                    with Tab("Overview"):
                        yield TextArea("", id="overview-text", read_only=True)

                    with Tab("Tasks"):
                        yield ListView(id="tasks-list")

                    with Tab("Research"):
                        yield ListView(id="research-list")

                    with Tab("Topics"):
                        yield Static("", id="topics-info")

                # Action buttons
                with Horizontal():
                    yield Button("🚀 Start Project", id="start-project-btn", variant="primary")
                    yield Button("⭐ Favorite", id="favorite-btn")
                    yield Button("📋 Export", id="export-btn")

    def on_mount(self):
        """Initialize when screen is mounted."""
        self._load_projects()

    def _load_projects(self):
        """Load projects from repository."""
        try:
            self.projects = self.repository.load_projects()
            project_list = self.query_one("#project-list", ListView)

            for project in self.projects:
                display_text = f"{project.title} ({project.difficulty.title()})"
                project_list.append(ListItem(Static(display_text)))

            self.app.notify_user(f"Loaded {len(self.projects)} projects", "Info")

        except Exception as e:
            self.app.notify_user(f"Error loading projects: {e}", "Error", "error")

    @on(ListView.Selected, "#project-list")
    def on_project_selected(self, event):
        """Handle project selection."""
        try:
            selected_index = event.list_view.index
            if 0 <= selected_index < len(self.projects):
                self.current_project = self.projects[selected_index]
                self._display_project_details()
        except Exception as e:
            self.app.notify_user(f"Error selecting project: {e}", "Error", "error")

    def _display_project_details(self):
        """Display details of the selected project."""
        if not self.current_project:
            return

        project = self.current_project

        # Show details container
        details_container = self.query_one("#project-details")
        details_container.remove_class("hidden")

        # Update title
        title_label = self.query_one("#project-title", Label)
        title_label.update(f"📋 {project.title}")

        # Overview tab
        overview_text = self.query_one("#overview-text", TextArea)
        overview = f"""
{project.description}

Difficulty: {project.difficulty.title()}
Estimated Hours: {project.estimated_hours}
Tags: {', '.join(project.tags) if project.tags else 'None'}

Short Description: {project.short_description}
        """.strip()
        overview_text.text = overview

        # Tasks tab
        tasks_list = self.query_one("#tasks-list", ListView)
        tasks_list.clear()

        for task in project.tasks:
            task_text = f"Task {task.order + 1}: {task.title}"
            if task.dsa_involvements:
                topics = [inv.topic.value.replace("_", " ").title() for inv in task.dsa_involvements]
                task_text += f" (DSA: {', '.join(topics)})"
            tasks_list.append(ListItem(Static(task_text)))

        # Research tab
        research_list = self.query_one("#research-list", ListView)
        research_list.clear()

        if project.research_references:
            for ref in project.research_references:
                ref_text = f"{ref.title} by {', '.join(ref.authors)}"
                research_list.append(ListItem(Static(ref_text)))
        else:
            research_list.append(ListItem(Static("No research references available")))

        # Topics tab
        topics_info = self.query_one("#topics-info", Static)
        coverage = project.get_topic_coverage()

        if coverage:
            topics_text = "DSA Topic Coverage:\n\n"
            for topic, percentage in sorted(coverage.items(), key=lambda x: x[1], reverse=True):
                display_name = topic.value.replace("_", " ").title()
                topics_text += ".1f"
        else:
            topics_text = "No topic coverage information available"

        topics_info.update(topics_text)

        self.app.notify_user(f"Loaded details for {project.title}", "Info")

    @on(Button.Pressed, "#back-btn")
    def on_back_pressed(self):
        """Handle back button press."""
        self.app.show_screen("main")

    @on(Button.Pressed, "#start-project-btn")
    def on_start_project(self):
        """Handle start project button press."""
        if self.current_project:
            self.app.notify_user(
                f"Starting project: {self.current_project.title}",
                "Success",
                "information"
            )
            # Here we could integrate with a project tracking system
        else:
            self.app.notify_user("No project selected", "Warning", "warning")

    @on(Button.Pressed, "#favorite-btn")
    def on_favorite_project(self):
        """Handle favorite project button press."""
        if self.current_project:
            self.app.notify_user(
                f"Added {self.current_project.title} to favorites",
                "Success"
            )
            # Here we could save to user preferences
        else:
            self.app.notify_user("No project selected", "Warning", "warning")

    @on(Button.Pressed, "#export-btn")
    def on_export_project(self):
        """Handle export project button press."""
        if self.current_project:
            try:
                # Export project details to a file
                export_data = {
                    "title": self.current_project.title,
                    "description": self.current_project.description,
                    "difficulty": self.current_project.difficulty,
                    "tasks": [
                        {
                            "title": task.title,
                            "description": task.description,
                            "order": task.order
                        }
                        for task in self.current_project.tasks
                    ],
                    "topics": [t.value for t in self.current_project.primary_topics],
                    "research": [
                        {
                            "title": ref.title,
                            "authors": ref.authors,
                            "url": ref.url
                        }
                        for ref in self.current_project.research_references
                    ]
                }

                import json
                from pathlib import Path

                export_path = Path.home() / f"{self.current_project.id}_export.json"
                with open(export_path, "w") as f:
                    json.dump(export_data, f, indent=2)

                self.app.notify_user(
                    f"Project exported to {export_path}",
                    "Success"
                )

            except Exception as e:
                self.app.notify_user(f"Export failed: {e}", "Error", "error")
        else:
            self.app.notify_user("No project selected", "Warning", "warning")
