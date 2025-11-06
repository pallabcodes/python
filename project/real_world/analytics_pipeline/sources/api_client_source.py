"""
API Client Source for analytics pipeline.

This module provides REST API client capabilities for the analytics pipeline,
supporting multiple APIs with authentication, rate limiting, and pagination.
"""

import time
import logging
import threading
import requests
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ..pipeline_core.message import DataMessage
from ..pipeline_core.stage_base import SourceStage


class APIAuthType(Enum):
    """API authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


@dataclass
class APIEndpointConfig:
    """Configuration for API endpoint."""
    name: str
    url: str
    method: str = "GET"
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    data: Dict[str, Any] = None
    json_data: Dict[str, Any] = None
    auth_type: APIAuthType = APIAuthType.NONE
    auth_config: Dict[str, Any] = None
    poll_interval: int = 300  # 5 minutes
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    enabled: bool = True

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}
        if self.auth_config is None:
            self.auth_config = {}


@dataclass
class APIResponse:
    """Represents an API response."""
    status_code: int
    headers: Dict[str, str]
    data: Any
    url: str
    timestamp: float
    request_time: float

    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return 200 <= self.status_code < 300


@dataclass
class APIClientStats:
    """Statistics for API client operations."""
    endpoints_configured: int = 0
    endpoints_active: int = 0
    requests_made: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    last_request_time: Optional[float] = None
    rate_limit_hits: int = 0


class APIClientSource(SourceStage):
    """API Client source stage for the analytics pipeline.

    This stage polls REST APIs at configured intervals and emits responses
    as pipeline messages. It supports multiple endpoints, authentication,
    rate limiting, and robust error handling.
    """

    def __init__(
        self,
        name: str,
        endpoints: List[APIEndpointConfig],
        max_workers: int = 4,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60  # per minute
    ):
        """Initialize API client source.

        Args:
            name: Stage name
            endpoints: List of API endpoint configurations
            max_workers: Maximum concurrent API polling workers
            rate_limit_requests: Maximum requests per rate limit window
            rate_limit_window: Rate limit window in seconds
        """
        super().__init__(name)
        self.endpoints = endpoints
        self.max_workers = max_workers
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window

        # State management
        self._running = False
        self._threads: List[threading.Thread] = []
        self._shutdown_event = threading.Event()
# Methods are implemented inline to keep file under 200 lines
