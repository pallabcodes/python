"""Main CLI interface for NoLeet."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Set

from noleet.core.models import Topic
from noleet.matching.matcher import ProjectMatcher
from noleet.storage.repository import ProjectRepository
from noleet.cli.data_commands import DataCommands, add_data_parser, handle_data_commands
from noleet.cli.intervention_commands import add_intervention_parser, handle_intervention_commands

# Optional TUI import
try:
    from noleet.tui.app import NoLeetApp
    TUI_AVAILABLE = True
except ImportError:
    TUI_AVAILABLE = False
    NoLeetApp = None


class NoLeetCLI:
    """Command-line interface for NoLeet platform."""
    
    def __init__(self, data_dir: Path) -> None:
        """
        Initialize CLI.
        
        Args:
            data_dir: Directory containing project data
        """
        self._data_dir = data_dir
        self._repository = ProjectRepository(data_dir)
        self._matcher = ProjectMatcher()
        self._logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def list_topics(self) -> None:
        """List all available DSA topics."""
        print("\nAvailable DSA Topics:")
        print("=" * 50)
        topics = list(Topic)
        for i, topic in enumerate(topics, 1):
            display_name = topic.value.replace("_", " ").title()
            print(f"{i:2d}. {display_name}")
        print()
    
    def find_projects(self, topic_names: list[str]) -> None:
        """
        Find projects matching selected topics.
        
        Args:
            topic_names: List of topic names to search for
        """
        try:
            selected_topics = self._parse_topics(topic_names)
            if not selected_topics:
                print("Error: No valid topics selected.")
                self.list_topics()
                return
            
            projects = self._repository.load_projects()
            if not projects:
                print("No projects available. Please add projects first.")
                return
            
            matching_projects = self._matcher.find_matching_projects(
                projects,
                selected_topics
            )
            
            if not matching_projects:
                print(f"\nNo projects found matching topics: {', '.join(topic_names)}")
                print("\nTry selecting different topics or check available topics with:")
                print("  noleet topics")
                return
            
            print(f"\nFound {len(matching_projects)} matching project(s):")
            print("=" * 70)
            
            for i, project in enumerate(matching_projects, 1):
                coverage = project.get_topic_coverage()
                primary_topics = [
                    topic.value.replace("_", " ").title()
                    for topic, percentage in coverage.items()
                    if percentage >= 15.0
                ]
                
                print(f"\n{i}. {project.title}")
                print(f"   {project.short_description}")
                print(f"   Difficulty: {project.difficulty.title()}")
                print(f"   Estimated Hours: {project.estimated_hours}")
                print(f"   Primary Topics: {', '.join(primary_topics)}")
                if project.tags:
                    print(f"   Tags: {', '.join(project.tags)}")
            
            print("\n" + "=" * 70)
            print("\nTo view project details, use:")
            print(f"  noleet show <project_id>")
            
        except Exception as e:
            self._logger.error(f"Error finding projects: {e}", exc_info=True)
            print(f"Error: {e}")
    
    def show_project(self, project_id: str) -> None:
        """
        Show detailed project information.
        
        Args:
            project_id: ID of project to display
        """
        projects = self._repository.load_projects()
        project = next((p for p in projects if p.id == project_id), None)
        
        if not project:
            print(f"Project '{project_id}' not found.")
            return
        
        print("\n" + "=" * 70)
        print(f"Project: {project.title}")
        print("=" * 70)
        print(f"\nDescription:\n{project.description}\n")
        print(f"Difficulty: {project.difficulty.title()}")
        print(f"Estimated Hours: {project.estimated_hours}")
        
        coverage = project.get_topic_coverage()
        if coverage:
            print("\nDSA Topic Coverage:")
            for topic, percentage in sorted(
                coverage.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                display_name = topic.value.replace("_", " ").title()
                print(f"  {display_name}: {percentage:.1f}%")
        
        if project.research_references:
            print("\nResearch References:")
            for ref in project.research_references:
                print(f"  - {ref.title}")
                if ref.authors:
                    print(f"    Authors: {', '.join(ref.authors)}")
                if ref.url:
                    print(f"    URL: {ref.url}")
                if ref.github_repo:
                    print(f"    GitHub: {ref.github_repo}")
        
        print("\n" + "=" * 70)
        print("Tasks:")
        print("=" * 70)
        
        for task in sorted(project.tasks, key=lambda t: t.order):
            print(f"\nTask {task.order + 1}: {task.title}")
            print(f"  {task.description}")
            
            if task.dsa_involvements:
                print("  DSA Involvement:")
                for inv in task.dsa_involvements:
                    display_name = inv.topic.value.replace("_", " ").title()
                    print(f"    {display_name}: {inv.percentage:.1f}%")
            
            if task.subtasks:
                print("  Subtasks:")
                for subtask in sorted(task.subtasks, key=lambda st: st.order):
                    print(f"    {subtask.order + 1}. {subtask.title}")
                    print(f"       {subtask.description}")
                    if subtask.dsa_involvements:
                        print("       DSA Involvement:")
                        for inv in subtask.dsa_involvements:
                            display_name = inv.topic.value.replace("_", " ").title()
                            print(f"         {display_name}: {inv.percentage:.1f}%")
        
        print("\n" + "=" * 70)
    
    def _parse_topics(self, topic_names: list[str]) -> Set[Topic]:
        """
        Parse topic names into Topic enum set.
        
        Args:
            topic_names: List of topic name strings
            
        Returns:
            Set of Topic enums
        """
        selected_topics: Set[Topic] = set()
        
        for name in topic_names:
            normalized = name.lower().replace(" ", "_")
            try:
                topic = Topic(normalized)
                selected_topics.add(topic)
            except ValueError:
                self._logger.warning(f"Unknown topic: {name}")
        
        return selected_topics


def launch_tui(data_dir: Path) -> None:
    """
    Launch the Terminal User Interface.

    Args:
        data_dir: Directory containing project data
    """
    if not TUI_AVAILABLE:
        print("❌ TUI not available. Install textual: pip install textual")
        print("💡 Continuing with CLI-only mode")
        return

    try:
        app = NoLeetApp(data_dir=data_dir)
        app.run()
    except KeyboardInterrupt:
        print("\nTUI closed by user.")
    except Exception as e:
        print(f"Error launching TUI: {e}")
        logging.getLogger(__name__).error(f"TUI launch failed: {e}", exc_info=True)


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="NoLeet: Learn DSA by building real-world products"
    )
    
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Directory containing project data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    topics_parser = subparsers.add_parser("topics", help="List all available topics")
    
    find_parser = subparsers.add_parser("find", help="Find projects by topics")
    find_parser.add_argument(
        "topics",
        nargs="+",
        help="DSA topics to search for (e.g., dynamic_programming sliding_window)"
    )
    
    show_parser = subparsers.add_parser("show", help="Show project details")
    show_parser.add_argument("project_id", help="Project ID to display")

    add_data_parser(subparsers)
    add_intervention_parser(subparsers)

    # TUI command
    tui_parser = subparsers.add_parser("tui", help="Launch Terminal User Interface")
    tui_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Path to data directory"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = NoLeetCLI(args.data_dir)
    
    if args.command == "topics":
        cli.list_topics()
    elif args.command == "find":
        cli.find_projects(args.topics)
    elif args.command == "show":
        cli.show_project(args.project_id)
    elif args.command == "data":
        handle_data_commands(args, args.data_dir)
    elif args.command == "intervention":
        handle_intervention_commands(args, args.data_dir)
    elif args.command == "tui":
        launch_tui(args.data_dir or args.data_dir)


if __name__ == "__main__":
    main()

