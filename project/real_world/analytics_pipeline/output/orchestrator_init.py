"""
Pipeline initialization components for the analytics pipeline.

This module contains the PipelineInitializer class which handles
component initialization and setup for the analytics pipeline.
"""

import time
import threading
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.orchestrator_core import PipelineOrchestrator as CoreOrchestrator
from ..sources.source_factory import create_demo_sources
from ..processing.stage_base import BaseProcessingStage
from ..storage.backend_factory import StorageBackendFactory
from .export_parquet import ExportManager
from .dashboard import MetricsDashboard, DashboardConfig
from .orchestrator_core import PipelineConfig


class PipelineInitializer:
    """Handles initialization of pipeline components."""

    def __init__(self, config: PipelineConfig):
        """Initialize the pipeline initializer.

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

    def initialize_components(self) -> None:
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

            print(f"Pipeline '{self.config.name}' components initialized successfully")

        except Exception as e:
            print(f"Failed to initialize pipeline components: {e}")
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

                if stage_class:
                    self.processing_stages[stage_name] = stage_class(
                        stage_name, stage_config.get('config', {})
                    )
                    print(f"Initialized processing stage: {stage_name}")

    def _initialize_storage_backends(self) -> None:
        """Initialize storage backends."""
        if not self.config.storage_backends:
            # Create default SQLite backend
            from ..storage.backend_factory import StorageBackendFactory
            sqlite_config = {
                'backend_type': 'sqlite',
                'connection_string': 'sqlite:///data/pipeline.db'
            }
            self.storage_backends['default'] = StorageBackendFactory.create_backend_from_dict(sqlite_config)
            print("Initialized default SQLite storage backend")
        else:
            # Initialize configured backends
            for backend_name, backend_config in self.config.storage_backends.items():
                self.storage_backends[backend_name] = StorageBackendFactory.create_backend_from_dict(backend_config)
                print(f"Initialized storage backend: {backend_name}")

    def _initialize_output_components(self) -> None:
        """Initialize output components."""
        if self.config.enable_dashboard:
            dashboard_config = self.config.dashboard_config or DashboardConfig()
            self.dashboard = MetricsDashboard(self, dashboard_config)
            print("Initialized dashboard component")

    def _connect_components(self) -> None:
        """Connect pipeline components."""
        # Connect sources to orchestrator
        for source_name, source in self.sources.items():
            self.core_orchestrator.add_source(source_name, source)

        # Add processing stages to orchestrator
        for stage_name, stage in self.processing_stages.items():
            self.core_orchestrator.add_stage(stage_name, stage)

        # Storage backends are handled by processing stages directly