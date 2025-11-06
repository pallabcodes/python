"""
Basic usage examples for the analytics pipeline.

This module contains basic usage examples for the Real-Time Multi-Source Analytics Pipeline,
demonstrating fundamental operations and configurations.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from output import PipelineOrchestrator, PipelineConfig


def example_1_basic_pipeline():
    """Example 1: Basic pipeline with default configuration."""
    print("Example 1: Basic Pipeline")
    print("=" * 40)

    # Create a basic configuration
    config = PipelineConfig(
        name="Basic Example Pipeline",
        max_workers=2,
        enable_monitoring=True,
        enable_dashboard=False
    )

    # Create and start orchestrator
    orchestrator = PipelineOrchestrator(config)
    orchestrator.start()

    print("Pipeline started with basic configuration")
    print(f"Status: {orchestrator.get_status()}")

    # Let it run for a bit
    time.sleep(2)

    # Get some metrics
    metrics = orchestrator.get_metrics()
    print(f"Messages processed: {metrics.get('messages_processed', 0)}")
    print(f"Active stages: {metrics.get('active_stages', 0)}")

    # Stop the pipeline
    orchestrator.stop()
    print("Pipeline stopped")
    print()


def example_2_custom_sources():
    """Example 2: Pipeline with custom data sources."""
    print("Example 2: Custom Sources")
    print("=" * 40)

    # Create configuration with custom sources
    config = PipelineConfig(
        name="Custom Sources Pipeline",
        sources={
            'demo_rss': {
                'type': 'rss',
                'url': 'https://feeds.bbci.co.uk/news/rss.xml',
                'poll_interval': 60
            }
        },
        processing_stages=[
            {'type': 'enrichment', 'name': 'content_enrichment'},
            {'type': 'quality', 'name': 'quality_check'}
        ],
        storage_backends={
            'local': {
                'backend_type': 'sqlite',
                'connection_string': 'sqlite:///data/example.db'
            }
        }
    )

    # Create and configure orchestrator
    orchestrator = PipelineOrchestrator(config)
    orchestrator.start()

    print("Pipeline started with custom RSS source")
    print("Processing stages: enrichment, quality")
    print(f"Status: {orchestrator.get_status()}")

    # Let it run for a bit
    time.sleep(3)

    # Show storage metrics
    storage_metrics = orchestrator.get_all_storage_metrics()
    print(f"Storage backends: {len(storage_metrics)}")

    # Stop the pipeline
    orchestrator.stop()
    print("Pipeline stopped")
    print()


def example_3_data_export():
    """Example 3: Data export functionality."""
    print("Example 3: Data Export")
    print("=" * 40)

    # Create pipeline with export configuration
    config = PipelineConfig(
        name="Export Example Pipeline",
        export_configs={
            'json_export': {
                'format': 'json',
                'output_path': './exports/example_data.json'
            }
        }
    )

    orchestrator = PipelineOrchestrator(config)
    orchestrator.start()

    print("Pipeline started for export example")
    print("Configured exports: JSON format")

    # Let it process some data
    time.sleep(2)

    # Try to export data (this might fail if no data exists yet)
    try:
        result = orchestrator.export_data(
            'default', 'messages', 'json', './exports/example_output.json'
        )
        print(f"Export completed: {result}")
    except Exception as e:
        print(f"Export example (expected if no data): {e}")

    orchestrator.stop()
    print("Pipeline stopped")
    print()


def run_basic_examples():
    """Run all basic examples."""
    print("Running Basic Usage Examples")
    print("=" * 50)
    print()

    try:
        example_1_basic_pipeline()
        example_2_custom_sources()
        example_3_data_export()

        print("All basic examples completed successfully!")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_basic_examples()
