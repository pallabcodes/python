"""
Processing stages for the analytics pipeline.

This module contains the processing stages that transform and analyze
data in the analytics pipeline:
- Enrichment: Add metadata and context
- Transformation: Data cleansing and normalization
- Aggregation: Real-time aggregations
- Windowing: Sliding window analytics
- Quality: Data quality validation
"""

from .stage_base import BaseProcessingStage, ProcessingStats
from .enrichment import EnrichmentStage, EnrichmentRule
from .transformation import TransformationStage, TransformationRule
from .aggregation import AggregationStage, AggregationWindow, AggregationResult
from .windowing import WindowingStage, WindowConfig, WindowData
from .quality import QualityStage, QualityRule, QualityMetrics, QualityIssue

__all__ = [
    # Base classes
    'BaseProcessingStage', 'ProcessingStats',

    # Enrichment
    'EnrichmentStage', 'EnrichmentRule',

    # Transformation
    'TransformationStage', 'TransformationRule',

    # Aggregation
    'AggregationStage', 'AggregationWindow', 'AggregationResult',

    # Windowing
    'WindowingStage', 'WindowConfig', 'WindowData',

    # Quality
    'QualityStage', 'QualityRule', 'QualityMetrics', 'QualityIssue'
]
