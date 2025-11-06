"""
Pipeline orchestrator for the analytics pipeline.

This module provides the main pipeline orchestrator that coordinates data sources,
processing stages, storage backends, and output components.
"""

import time
import threading
import signal
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.orchestrator_core import PipelineOrchestrator as CoreOrchestrator
from ..sources.source_factory import create_demo_sources
from ..processing.stage_base import BaseProcessingStage
from ..storage.backend_factory import StorageBackendFactory
from .export_parquet import ExportManager
from .dashboard import MetricsDashboard, DashboardConfig


@dataclass
class PipelineConfig:
    """Configuration for the analytics pipeline."""

    name: str = "Analytics Pipeline"
    max_workers: int = 10
    batch_size: int = 100
    processing_timeout: float = 30.0
    enable_monitoring: bool = True
    enable_dashboard: bool = True
    auto_start: bool = False

    # Component configurations
    sources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    processing_stages: List[Dict[str, Any]] = field(default_factory=list)
    storage_backends: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Output configurations
    export_configs: Dict[str, Any] = field(default_factory=dict)
    dashboard_config: Optional[DashboardConfig] = None


class PipelineRunner:
    """Main pipeline runner that coordinates all components."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline runner.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.core_orchestrator = CoreOrchestrator(config.name)

        # Component storage
        self.sources: Dict[str, Any] = {}
        self.processing_stages: Dict[str, BaseProcessingStage] = {}
        self.storage_backends: Dict[str, Any] = {}

        # Output components
        self.export_manager = ExportManager()
        self.dashboard: Optional[MetricsDashboard] = None

        # Control
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.shutdown_event = threading.Event()

        # Metrics
        self.start_time: Optional[float] = None
        self.total_messages_processed = 0
        self.error_count = 0

        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def initialize(self) -> None:
        """Initialize all pipeline components."""
        try:
            # Initialize sources
            self._initialize_sources()

            # Initialize processing stages
            self._initialize_processing_stages()

            # Initialize storage backends
            self._initialize_storage_backends()

            # Initialize output components
            self._initialize_output_components()

            # Connect components
            self._connect_components()

            print(f"Pipeline '{self.config.name}' initialized successfully")

        except Exception as e:
            print(f"Failed to initialize pipeline: {e}")
            raise

    def _initialize_sources(self) -> None:
        """Initialize data sources."""
        if not self.config.sources:
            # Use demo sources if none configured
            demo_sources = create_demo_sources()
            for name, source in demo_sources.items():
                self.sources[name] = source
                print(f"Initialized demo source: {name}")
        else:
            # Initialize configured sources
            for source_name, source_config in self.config.sources.items():
                # This would create actual source instances based on config
                # For now, using demo sources as placeholder
                demo_sources = create_demo_sources()
                if source_name in demo_sources:
                    self.sources[source_name] = demo_sources[source_name]
                    print(f"Initialized source: {source_name}")

    def _initialize_processing_stages(self) -> None:
        """Initialize processing stages."""
        # Import processing stages
        from ..processing import (
            EnrichmentStage, TransformationStage, AggregationStage,
            WindowingStage, QualityStage
        )

        stage_classes = {
            'enrichment': EnrichmentStage,
            'transformation': TransformationStage,
            'aggregation': AggregationStage,
            'windowing': WindowingStage,
            'quality': QualityStage
        }

        if not self.config.processing_stages:
            # Create default processing pipeline
            self.processing_stages['enrichment'] = EnrichmentStage('enrichment')
            self.processing_stages['transformation'] = TransformationStage('transformation')
            self.processing_stages['quality'] = QualityStage('quality')
            print("Initialized default processing stages")
        else:
            # Initialize configured stages
            for stage_config in self.config.processing_stages:
                stage_type = stage_config.get('type')
                stage_name = stage_config.get('name', stage_type)
                stage_class = stage_classes.get(stage_type)
