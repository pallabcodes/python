"""
Core HTTP fetcher stage implementation.

This module contains the main HttpFetcherStage class with
full functionality for HTTP fetching in pipelines.
"""

from typing import Any, Dict, Optional, List

from ..pipeline_core.stage_types import TransformStage
from .http_client_core import HttpClient, create_http_client


class HttpFetcherStage(TransformStage):
    """Pipeline stage for fetching data from HTTP endpoints."""

    def __init__(
        self,
        name: str,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        requests_per_second: float = 10.0,
        max_retries: int = 3
    ):
        """Initialize HTTP fetcher stage.

        Args:
            name: Stage name for identification
            base_url: Base URL for requests
            headers: Default headers for all requests
            timeout: Request timeout in seconds
            requests_per_second: Rate limiting for requests
            max_retries: Maximum retry attempts for failed requests
        """
        super().__init__(name)
        self.base_url = base_url.rstrip('/')
        self.default_headers = headers or {}
        self.timeout = timeout
        self.requests_per_second = requests_per_second
        self.max_retries = max_retries

        # Initialize HTTP client
        self._http_client = create_http_client(
            requests_per_second=requests_per_second,
            max_retries=max_retries,
            timeout=timeout
        )

        # Statistics
        self._requests_made = 0
        self._requests_successful = 0
        self._requests_failed = 0

    def transform(self, data: Any) -> Any:
        """Fetch data from HTTP endpoint.

        Args:
            data: Input data containing URL and request parameters

        Returns:
            Fetched data with response information
        """
        self._requests_made += 1

        try:
            # Extract request parameters from input data
            request_params = self._extract_request_params(data)

            # Make HTTP request
            response = self._make_request(request_params)

            # Process response
            result = self._process_response(response, request_params)

            self._requests_successful += 1

            self._logger.info(
                f"HTTP fetch successful: {response.status_code} from {response.url}",
                extra={
                    "stage_name": self.name,
                    "url": response.url,
                    "status_code": response.status_code,
                    "elapsed": response.elapsed,
                    "content_length": len(response.content)
                }
            )

            return result

        except Exception as e:
            self._requests_failed += 1

            self._logger.error(
                f"HTTP fetch failed: {e}",
                extra={
                    "stage_name": self.name,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )

            # Return error information instead of raising
            return {
                "error": True,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "original_request": data
            }

    def cleanup(self) -> None:
        """Clean up HTTP client resources."""
        if self._http_client:
            self._http_client.close()
        super().cleanup()

    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher stage statistics."""
        return {
            "stage_name": self.name,
            "requests_made": self._requests_made,
            "requests_successful": self._requests_successful,
            "requests_failed": self._requests_failed,
            "success_rate": (self._requests_successful / self._requests_made * 100) if self._requests_made > 0 else 0,
            "http_client": self._http_client.get_stats() if self._http_client else None
        }


# Import utility functions and monkey patch them
from .fetcher_stage_utils import (
    _extract_request_params,
    _make_request,
    _process_response
)
