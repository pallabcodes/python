"""
Pipeline execution utilities.

This module contains execution and interactive mode functions for the pipeline runner script,
separated for better modularity and to keep file sizes under limits.
"""

import sys
import time
import signal
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from output import PipelineOrchestrator
from .config import setup_logging, load_config, create_demo_config


def run_interactive_mode(orchestrator: PipelineOrchestrator):
    """Run pipeline in interactive mode with command interface."""
    print("\n" + "="*60)
    print("Real-Time Multi-Source Analytics Pipeline")
    print("="*60)
    print("Commands:")
    print("  status    - Show pipeline status")
    print("  start     - Start the pipeline")
    print("  stop      - Stop the pipeline")
    print("  metrics   - Show current metrics")
    print("  export    - Export data")
    print("  dashboard - Show dashboard URL")
    print("  help      - Show this help")
    print("  quit      - Exit")
    print("="*60)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        orchestrator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            try:
                cmd = input("\nPipeline> ").strip().lower()

                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'help':
                    print("Available commands: status, start, stop, metrics, export, dashboard, help, quit")
                elif cmd == 'status':
                    status = orchestrator.get_status()
                    metrics = orchestrator.get_metrics()
                    print(f"Status: {status}")
                    print(f"Uptime: {metrics.get('uptime', 0):.1f}s")
                    print(f"Messages processed: {metrics.get('messages_processed', 0)}")
                    print(f"Active stages: {metrics.get('active_stages', 0)}")
                elif cmd == 'start':
                    if orchestrator.get_status() != 'running':
                        orchestrator.start()
                        print("Pipeline started")
                    else:
                        print("Pipeline is already running")
                elif cmd == 'stop':
                    orchestrator.stop()
                    print("Pipeline stopped")
                elif cmd == 'metrics':
                    metrics = orchestrator.get_metrics()
                    print("Current Metrics:")
                    for key, value in metrics.items():
                        if key != 'stage_metrics' and key != 'storage_metrics':
                            print(f"  {key}: {value}")
                elif cmd == 'export':
                    # Simple export example
                    try:
                        result = orchestrator.export_data('local_sqlite', 'messages', 'json', './export.json')
                        print(f"Export completed: {result}")
                    except Exception as e:
                        print(f"Export failed: {e}")
                elif cmd == 'dashboard':
                    print("Dashboard available at: http://localhost:8000")
                elif cmd:
                    print(f"Unknown command: {cmd}")

            except KeyboardInterrupt:
                break
            except EOFError:
                break

    finally:
        orchestrator.stop()
        print("\nPipeline shutdown complete")


def main():
    """Main entry point for the pipeline runner."""
    import argparse

    parser = argparse.ArgumentParser(description='Real-Time Multi-Source Analytics Pipeline')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--demo', action='store_true', help='Run with demo configuration')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Load configuration
    if args.config:
        config = load_config(args.config)
        print(f"Loaded configuration from {args.config}")
    else:
        config = create_demo_config()
        if args.demo:
            print("Using demo configuration")
        else:
            print("Using default demo configuration (use --config for custom config)")

    # Create and configure orchestrator
    orchestrator = PipelineOrchestrator(config)

    if args.interactive:
        # Run in interactive mode
        run_interactive_mode(orchestrator)
    else:
        # Run in automatic mode
        print(f"Starting pipeline: {config.name}")
        orchestrator.start()

        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
                status = orchestrator.get_status()
                if status != 'running':
                    print(f"Pipeline stopped with status: {status}")
                    break

        except KeyboardInterrupt:
            print("\nShutting down pipeline...")
        finally:
            orchestrator.stop()
            print("Pipeline shutdown complete")


if __name__ == '__main__':
    main()
