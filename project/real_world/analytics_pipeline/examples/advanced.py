"""
Advanced usage examples for the analytics pipeline.

This module contains advanced usage examples for the Real-Time Multi-Source Analytics Pipeline,
demonstrating API usage, storage backends, and complex configurations.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from output import PipelineOrchestrator, PipelineConfig


def example_4_api_usage():
    """Example 4: Using the pipeline API."""
    print("Example 4: API Usage")
    print("=" * 40)

    # Start pipeline
    config = PipelineConfig(name="API Example Pipeline")
    orchestrator = PipelineOrchestrator(config)
    orchestrator.start()

    print("Pipeline started for API example")

    # Demonstrate API usage
    try:
        # Get pipeline status
        status_response = orchestrator.get_status()
        print(f"API Status: {status_response}")

        # Get uptime
        uptime = orchestrator.get_uptime()
        print(f"Uptime: {uptime:.1f} seconds")

        # Get metrics
        metrics = orchestrator.get_metrics()
        print(f"Messages processed: {metrics.get('messages_processed', 0)}")
        print(f"Active stages: {metrics.get('active_stages', 0)}")

        # Get stage metrics
        stage_metrics = orchestrator.get_all_stage_metrics()
        print(f"Stage metrics available: {len(stage_metrics)}")

        # Get dashboard data
        dashboard_data = orchestrator.get_dashboard_data()
        if dashboard_data:
            print("Dashboard data retrieved successfully")
        else:
            print("Dashboard not available")

    except Exception as e:
        print(f"API usage example error: {e}")

    # Stop pipeline
    orchestrator.stop()
    print("Pipeline stopped")
    print()


def example_5_storage_backends():
    """Example 5: Multiple storage backends."""
    print("Example 5: Multiple Storage Backends")
    print("=" * 40)

    # Configure multiple storage backends
    config = PipelineConfig(
        name="Multi-Storage Pipeline",
        storage_backends={
            'primary': {
                'backend_type': 'sqlite',
                'connection_string': 'sqlite:///data/primary.db'
            },
            'archive': {
                'backend_type': 'sqlite',
                'connection_string': 'sqlite:///data/archive.db'
            }
        }
    )

    orchestrator = PipelineOrchestrator(config)
    orchestrator.start()

    print("Pipeline started with multiple storage backends")
    print("Backends: primary (SQLite), archive (SQLite)")

    # Let it run and collect some data
    time.sleep(2)

    # Show storage metrics
    storage_metrics = orchestrator.get_all_storage_metrics()
    print(f"Storage backends active: {len(storage_metrics)}")

    for backend_name, metrics in storage_metrics.items():
        print(f"  {backend_name}: {metrics}")

    # Try exporting from different backends
    for backend_name in storage_metrics.keys():
        try:
            result = orchestrator.export_data(
                backend_name, 'messages', 'json',
                f'./exports/{backend_name}_data.json'
            )
            print(f"Exported from {backend_name}: {result}")
        except Exception as e:
            print(f"Export from {backend_name} failed: {e}")

    orchestrator.stop()
    print("Pipeline stopped")
    print()


def run_advanced_examples():
    """Run all advanced examples."""
    print("Running Advanced Usage Examples")
    print("=" * 50)
    print()

    try:
        example_4_api_usage()
        example_5_storage_backends()

        print("All advanced examples completed successfully!")

    except Exception as e:
        print(f"Error running advanced examples: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for examples."""
    print("Real-Time Multi-Source Analytics Pipeline Examples")
    print("=" * 60)
    print()

    # Run basic examples
    from .basic import run_basic_examples
    run_basic_examples()

    print()

    # Run advanced examples
    run_advanced_examples()

    print()
    print("All examples completed!")
    print("Check the 'exports' directory for any generated files.")


if __name__ == '__main__':
    main()
