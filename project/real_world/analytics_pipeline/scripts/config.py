"""
Pipeline configuration utilities.

This module contains configuration loading and setup functions for the pipeline runner script,
separated for better modularity and to keep file sizes under limits.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from output import PipelineConfig


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )


def load_config(config_path: str) -> PipelineConfig:
    """Load pipeline configuration from YAML file."""
    try:
        import yaml
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Convert dict to PipelineConfig
        pipeline_data = config_data.get('pipeline', {})

        return PipelineConfig(
            name=pipeline_data.get('name', 'Analytics Pipeline'),
            max_workers=pipeline_data.get('max_workers', 10),
            batch_size=pipeline_data.get('batch_size', 100),
            processing_timeout=pipeline_data.get('processing_timeout', 30.0),
            enable_monitoring=pipeline_data.get('enable_monitoring', True),
            enable_dashboard=pipeline_data.get('enable_dashboard', True),
            auto_start=pipeline_data.get('auto_start', False),
            sources=pipeline_data.get('sources', {}),
            processing_stages=pipeline_data.get('processing_stages', []),
            storage_backends=pipeline_data.get('storage_backends', {}),
            export_configs=pipeline_data.get('export_configs', {}),
            dashboard_config=pipeline_data.get('dashboard_config')
        )

    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        return create_demo_config()


def create_demo_config() -> PipelineConfig:
    """Create a demo configuration for testing."""
    return PipelineConfig(
        name="Demo Analytics Pipeline",
        max_workers=4,
        batch_size=50,
        processing_timeout=15.0,
        enable_monitoring=True,
        enable_dashboard=True,
        auto_start=False,
        sources={
            'demo_rss': {
                'type': 'rss',
                'url': 'https://feeds.bbci.co.uk/news/rss.xml',
                'poll_interval': 60
            },
            'demo_api': {
                'type': 'api',
                'url': 'https://jsonplaceholder.typicode.com/posts',
                'method': 'GET',
                'poll_interval': 120
            }
        },
        processing_stages=[
            {
                'type': 'enrichment',
                'name': 'data_enrichment'
            },
            {
                'type': 'transformation',
                'name': 'data_transformation'
            },
            {
                'type': 'quality',
                'name': 'data_quality'
            }
        ],
        storage_backends={
            'local_sqlite': {
                'backend_type': 'sqlite',
                'connection_string': 'sqlite:///data/demo_pipeline.db'
            }
        },
        export_configs={
            'csv_export': {
                'format': 'csv',
                'output_path': './exports/demo_data.csv'
            },
            'json_export': {
                'format': 'json',
                'output_path': './exports/demo_data.json'
            }
        }
    )
