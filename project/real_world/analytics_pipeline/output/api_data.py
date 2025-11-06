"""
Data API endpoints for the analytics pipeline.

This module contains the DataAPI and APIEndpoints classes which provide
REST API endpoints for data access, queries, and API coordination.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ..storage.storage_base import QueryFilter, QueryOptions
from .api_core import APIResponse
from .api_metrics import MetricsAPI

# Import CRUD and metadata operations
from .api_crud import query_data, store_data, retrieve_data, delete_data
from .api_metadata import get_collections, get_collection_stats


class DataAPI:
    """API endpoints for data access and queries."""

    def __init__(self, storage_backends: Dict[str, Any]):
        """Initialize data API.

        Args:
            storage_backends: Dictionary of storage backend instances
        """
        self.storage_backends = storage_backends


class APIEndpoints:
    """Main API endpoints coordinator."""

    def __init__(self, pipeline_orchestrator, storage_backends: Dict[str, Any]):
        """Initialize API endpoints.

        Args:
            pipeline_orchestrator: Pipeline orchestrator instance
            storage_backends: Dictionary of storage backend instances
        """
        self.metrics_api = MetricsAPI(pipeline_orchestrator)
        self.data_api = DataAPI(storage_backends)

    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get all available API endpoints.

        Returns:
            Dictionary of endpoint definitions
        """
        return {
            # Health and status endpoints
            'GET /health': {
                'handler': self.metrics_api.get_system_health,
                'description': 'Get system health status'
            },
            'GET /status': {
                'handler': self.metrics_api.get_pipeline_status,
                'description': 'Get pipeline status'
            },

            # Metrics endpoints
            'GET /metrics': {
                'handler': lambda: self.metrics_api.get_stage_metrics(),
                'description': 'Get all stage metrics'
            },
            'GET /metrics/{stage_name}': {
                'handler': self.metrics_api.get_stage_metrics,
                'description': 'Get metrics for specific stage'
            },
            'GET /storage/metrics': {
                'handler': lambda: self.metrics_api.get_storage_metrics(),
                'description': 'Get all storage metrics'
            },
            'GET /storage/metrics/{backend_name}': {
                'handler': self.metrics_api.get_storage_metrics,
                'description': 'Get metrics for specific storage backend'
            },

            # Data endpoints
            'GET /data/{backend_name}/{collection}': {
                'handler': lambda backend_name, collection, filters=None, options=None: 
                    self.data_api.query_data(backend_name, collection, filters, options),
                'description': 'Query data from collection'
            },
            'POST /data/{backend_name}/{collection}': {
                'handler': self.data_api.store_data,
                'description': 'Store data in collection'
            },
            'GET /data/{backend_name}/{collection}/{record_id}': {
                'handler': self.data_api.retrieve_data,
                'description': 'Retrieve specific record'
            },
            'DELETE /data/{backend_name}/{collection}/{record_id}': {
                'handler': self.data_api.delete_data,
                'description': 'Delete specific record'
            },
            'GET /collections/{backend_name}': {
                'handler': self.data_api.get_collections,
                'description': 'Get list of collections in backend'
            },
            'GET /collections/{backend_name}/{collection}/stats': {
                'handler': self.data_api.get_collection_stats,
                'description': 'Get collection statistics'
            }
        }
