"""
Core HTTP client implementation.

This module contains the main HttpClient class with rate limiting
and retry logic for reliable HTTP requests.
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

from .rate_limiter import RateLimiter
from .retry_logic import RetryHandler


@dataclass
class HttpResponse:
    """HTTP response wrapper with metadata."""
    status_code: int
    content: bytes
    headers: Dict[str, str]
    url: str
    elapsed: float
    request_time: float

    @property
    def text(self) -> str:
        """Get response content as text."""
        return self.content.decode('utf-8', errors='replace')

    @property
    def json(self) -> Any:
        """Parse response content as JSON."""
        import json
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        """Raise an exception for bad status codes."""
        if 400 <= self.status_code < 600:
            raise HttpError(f"HTTP {self.status_code}: {self.text}", self)


class HttpError(Exception):
    """HTTP-related exception."""

    def __init__(self, message: str, response: Optional[HttpResponse] = None):
        """Initialize HTTP error.

        Args:
            message: Error message
            response: Optional HTTP response that caused the error
        """
        super().__init__(message)
        self.response = response


class HttpClient:
    """Production HTTP client with rate limiting and retries."""

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        retry_handler: Optional[RetryHandler] = None,
        timeout: float = 30.0,
        user_agent: str = "HttpFetcher/1.0"
    ):
        """Initialize HTTP client.

        Args:
            rate_limiter: Optional rate limiter for requests
            retry_handler: Optional retry handler for failed requests
            timeout: Default request timeout in seconds
            user_agent: User-Agent header for requests
        """
        self.rate_limiter = rate_limiter
        self.retry_handler = retry_handler
        self.timeout = timeout
        self.user_agent = user_agent
        self._logger = logging.getLogger(__name__)

        # Initialize HTTP session if available
        self._session = None
        try:
            import requests
            self._session = requests.Session()
            self._session.headers.update({'User-Agent': user_agent})
        except ImportError:
            self._logger.warning("requests library not available, using urllib")
            import urllib.request
            import urllib.error
            self._urllib_available = True

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[bytes, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> HttpResponse:
        """Make an HTTP request with rate limiting and retries.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            headers: Optional headers to include
            data: Optional request body
            params: Optional query parameters
            timeout: Optional request timeout
            **kwargs: Additional arguments

        Returns:
            HttpResponse object

        Raises:
            HttpError: For HTTP errors
            Exception: For network or other errors
        """
        request_timeout = timeout or self.timeout
        all_headers = {'User-Agent': self.user_agent}
        if headers:
            all_headers.update(headers)

        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        # Define the request function for retry logic
        def make_request():
            return self._make_single_request(
                method, url, all_headers, data, params, request_timeout
            )

        # Execute with retries if configured
        if self.retry_handler:
            return self.retry_handler.execute_with_retry(make_request)
        else:
            return make_request()

