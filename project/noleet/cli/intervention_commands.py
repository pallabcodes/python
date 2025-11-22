"""CLI commands for manual intervention workflows."""

import argparse
from pathlib import Path
from typing import Optional

from ..agents.agent_orchestrator import AgentOrchestrator
from ..manual_intervention.intervention_config import InterventionConfig
from ..llm.llm_config import LLMConfig


def add_intervention_parser(subparsers) -> None:
    """Add intervention command parser."""
    intervention_parser = subparsers.add_parser(
        "intervention",
        help="Manual intervention workflow commands"
    )
    intervention_subparsers = intervention_parser.add_subparsers(
        dest="intervention_command",
        required=True
    )

    # Status command
    status_parser = intervention_subparsers.add_parser(
        "status",
        help="Show status of paused workflows"
    )
    status_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Data directory"
    )

    # Resume command
    resume_parser = intervention_subparsers.add_parser(
        "resume",
        help="Resume a paused workflow"
    )
    resume_parser.add_argument(
        "session_id",
        help="Intervention session ID to resume"
    )
    resume_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Data directory"
    )

    # Cancel command
    cancel_parser = intervention_subparsers.add_parser(
        "cancel",
        help="Cancel a manual intervention session"
    )
    cancel_parser.add_argument(
        "session_id",
        help="Intervention session ID to cancel"
    )
    cancel_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Data directory"
    )

    # Stats command
    stats_parser = intervention_subparsers.add_parser(
        "stats",
        help="Show manual intervention statistics"
    )
    stats_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Data directory"
    )

    # Configure command
    config_parser = intervention_subparsers.add_parser(
        "config",
        help="Configure manual intervention settings"
    )
    config_parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable manual intervention"
    )
    config_parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable manual intervention"
    )
    config_parser.add_argument(
        "--agents",
        nargs="+",
        help="Agent types that should trigger intervention (e.g., project_recommendation_agent)"
    )
    config_parser.add_argument(
        "--export-dir",
        type=Path,
        help="Directory for intervention data export"
    )
    config_parser.add_argument(
        "--timeout",
        type=int,
        help="Maximum wait time in seconds"
    )
    config_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / ".noleet" / "data",
        help="Data directory"
    )


class InterventionCommands:
    """Handles manual intervention CLI commands."""

    def __init__(self, data_dir: Path):
        """Initialize intervention commands."""
        self._data_dir = data_dir
        self._orchestrator = None

    def _get_orchestrator(self) -> AgentOrchestrator:
        """Get or create orchestrator instance."""
        if self._orchestrator is None:
            # Load intervention config
            config_path = self._data_dir.parent / "intervention_config.json"
            intervention_config = InterventionConfig.from_json_file(config_path)

            # Create orchestrator with intervention support
            llm_config = LLMConfig()
            self._orchestrator = AgentOrchestrator(
                llm_config=llm_config,
                intervention_config=intervention_config
            )

        return self._orchestrator

    def status(self) -> None:
        """Show status of paused workflows."""
        try:
            orchestrator = self._get_orchestrator()
            status_info = orchestrator.get_paused_workflows()

            print("\n📋 Manual Intervention Status")
            print("=" * 50)

            if status_info["total_paused"] == 0:
                print("✅ No workflows currently paused for manual intervention")
                return

            print(f"Total paused workflows: {status_info['total_paused']}\n")

            for workflow_id, sessions in status_info["workflows"].items():
                print(f"🔄 Workflow: {workflow_id}")
                for session in sessions:
                    print(f"  Session: {session['session_id']}")
                    print(f"  Agent: {session['agent_type']}")
                    print(f"  Paused: {session['paused_at']}")
                    if session['export_path']:
                        print(f"  Data: {session['export_path']}")
                    print()

        except Exception as e:
            print(f"❌ Error getting intervention status: {e}")

    def resume(self, session_id: str) -> None:
        """Resume a paused workflow."""
        try:
            orchestrator = self._get_orchestrator()

            print(f"🔄 Resuming workflow session: {session_id}")
            print("Checking for manual input...")

            # Attempt to resume
            resume_result = orchestrator.resume_workflow(session_id)

            if resume_result["success"]:
                print("✅ Workflow resumed successfully!")
                print(f"Resumed from agent: {resume_result.get('resumed_from', 'unknown')}")
                print(f"Manual data applied: {resume_result.get('manual_data_applied', False)}")
                print(f"Completed agents: {len(resume_result.get('completed_agents', []))}")

                # Show results summary
                results = resume_result.get("results", {})
                if results:
                    print("\n📊 Final Results:")
                    for agent, result in results.items():
                        status = "✅" if isinstance(result, dict) and "error" not in result else "❌"
                        print(f"  {status} {agent}")

            else:
                error = resume_result.get("error", "Unknown error")
                print(f"❌ Failed to resume workflow: {error}")

        except Exception as e:
            print(f"❌ Error resuming workflow: {e}")

    def cancel(self, session_id: str) -> None:
        """Cancel a manual intervention session."""
        try:
            orchestrator = self._get_orchestrator()

            if orchestrator.cancel_manual_intervention(session_id):
                print(f"✅ Successfully cancelled intervention session: {session_id}")
            else:
                print(f"❌ Failed to cancel session: {session_id} (session not found)")

        except Exception as e:
            print(f"❌ Error cancelling intervention: {e}")

    def stats(self) -> None:
        """Show manual intervention statistics."""
        try:
            orchestrator = self._get_orchestrator()
            stats = orchestrator.get_intervention_statistics()

            print("\n📈 Manual Intervention Statistics")
            print("=" * 50)
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Active sessions: {stats['active_sessions']}")
            print(f"Completed sessions: {stats['completed_sessions']}")
            print(f"Cancelled sessions: {stats['cancelled_sessions']}")
            print(f"Timed out sessions: {stats['timed_out_sessions']}")

            if stats['average_completion_time_seconds'] > 0:
                avg_time = stats['average_completion_time_seconds']
                print(f"Average completion time: {avg_time:.1f} seconds")

            if stats.get('most_common_agent'):
                print(f"Most intervened agent: {stats['most_common_agent']}")

        except Exception as e:
            print(f"❌ Error getting intervention statistics: {e}")

    def configure(self, args) -> None:
        """Configure manual intervention settings."""
        try:
            config_path = self._data_dir.parent / "intervention_config.json"

            # Load existing config or create default
            if config_path.exists():
                config = InterventionConfig.from_json_file(config_path)
            else:
                config = InterventionConfig()

            # Apply configuration changes
            if args.enable:
                config.enabled = True
                print("✅ Manual intervention enabled")
            elif args.disable:
                config.enabled = False
                print("❌ Manual intervention disabled")

            if args.agents:
                config.intervention_points = args.agents
                print(f"📋 Intervention agents set to: {', '.join(args.agents)}")

            if args.export_dir:
                config.export_directory = args.export_dir
                print(f"📁 Export directory set to: {args.export_dir}")

            if args.timeout:
                config.max_wait_time_seconds = args.timeout
                print(f"⏰ Max wait time set to: {args.timeout} seconds")

            # Save configuration
            config.save_to_file(config_path)
            print(f"💾 Configuration saved to: {config_path}")

            # Show current config summary
            print("\n📋 Current Configuration:")
            print(f"  Enabled: {config.enabled}")
            print(f"  Intervention agents: {', '.join(config.intervention_points)}")
            print(f"  Export directory: {config.export_directory}")
            print(f"  Max wait time: {config.max_wait_time_seconds}s")

        except Exception as e:
            print(f"❌ Error configuring intervention settings: {e}")


def handle_intervention_commands(args, data_dir: Path) -> None:
    """Handle intervention command execution."""
    commands = InterventionCommands(data_dir)

    if args.intervention_command == "status":
        commands.status()
    elif args.intervention_command == "resume":
        commands.resume(args.session_id)
    elif args.intervention_command == "cancel":
        commands.cancel(args.session_id)
    elif args.intervention_command == "stats":
        commands.stats()
    elif args.intervention_command == "config":
        commands.configure(args)
    else:
        print("Unknown intervention command")
