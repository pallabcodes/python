"""
HTTP client with rate limiting and retry logic.

This module provides a production-ready HTTP client that integrates
rate limiting, retry logic, and comprehensive error handling for
reliable web requests.
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

from .rate_limiter import RateLimiter, create_rate_limiter
from .retry_logic import RetryHandler, create_retry_handler


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

    def get(self, url: str, **kwargs) -> HttpResponse:
        """Make a GET request."""
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> HttpResponse:
        """Make a POST request."""
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> HttpResponse:
        """Make a PUT request."""
        return self.request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> HttpResponse:
        """Make a DELETE request."""
        return self.request('DELETE', url, **kwargs)

    def _make_single_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Union[bytes, str]],
        params: Optional[Dict[str, Any]],
        timeout: float
    ) -> HttpResponse:
        """Make a single HTTP request without retries."""
        request_start = time.time()

        try:
            if self._session:
                # Use requests library
                response = self._make_requests_call(
                    method, url, headers, data, params, timeout
                )
            else:
                # Fallback to urllib
                response = self._make_urllib_call(
                    method, url, headers, data, params, timeout
                )

            elapsed = time.time() - request_start

            self._logger.debug(
                f"HTTP {method} {url} -> {response.status_code} ({elapsed:.2f}s)",
                extra={
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "elapsed": elapsed
                }
            )

            return response

        except Exception as e:
            elapsed = time.time() - request_start
            self._logger.error(
                f"HTTP {method} {url} failed after {elapsed:.2f}s: {e}",
                extra={
                    "method": method,
                    "url": url,
                    "elapsed": elapsed,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    def _make_requests_call(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Union[bytes, str]],
        params: Optional[Dict[str, Any]],
        timeout: float
    ) -> HttpResponse:
        """Make request using requests library."""
        import requests

        # Prepare request
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': timeout
        }

        if data is not None:
            if isinstance(data, str):
                request_kwargs['data'] = data.encode('utf-8')
            else:
                request_kwargs['data'] = data

        if params:
            request_kwargs['params'] = params

        # Make request
        response = self._session.request(**request_kwargs)
        request_time = time.time()

        return HttpResponse(
            status_code=response.status_code,
            content=response.content,
            headers=dict(response.headers),
            url=response.url,
            elapsed=response.elapsed.total_seconds(),
            request_time=request_time
        )

    def _make_urllib_call(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Union[bytes, str]],
        params: Optional[Dict[str, Any]],
        timeout: float
    ) -> HttpResponse:
        """Make request using urllib (fallback)."""
        import urllib.request
        import urllib.parse
        import urllib.error

        # Build URL with params
        if params:
            url_parts = list(urllib.parse.urlparse(url))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urllib.parse.urlencode(query)
            url = urllib.parse.urlunparse(url_parts)

        # Prepare request
        if data is not None and isinstance(data, str):
            data = data.encode('utf-8')

        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        request_start = time.time()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read()
                elapsed = time.time() - request_start

                return HttpResponse(
                    status_code=response.getcode(),
                    content=content,
                    headers=dict(response.headers),
                    url=url,
                    elapsed=elapsed,
                    request_time=time.time()
                )
        except urllib.error.HTTPError as e:
            # Convert to HttpResponse for consistency
            elapsed = time.time() - request_start
            raise HttpError(f"HTTP {e.code}: {e.reason}", HttpResponse(
                status_code=e.code,
                content=e.read() if hasattr(e, 'read') else b'',
                headers=dict(e.headers) if e.headers else {},
                url=url,
                elapsed=elapsed,
                request_time=time.time()
            ))
        except urllib.error.URLError as e:
            elapsed = time.time() - request_start
            raise HttpError(f"URL Error: {e.reason}", None)

    def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._session:
            self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP client statistics."""
        stats = {
            "timeout": self.timeout,
            "user_agent": self.user_agent,
            "has_session": self._session is not None
        }

        if self.rate_limiter:
            stats["rate_limiter"] = self.rate_limiter.get_stats()

        if self.retry_handler:
            stats["retry_handler"] = self.retry_handler.get_stats()

        return stats


def create_http_client(
    requests_per_second: float = 10.0,
    max_retries: int = 3,
    timeout: float = 30.0
) -> HttpClient:
    """Create an HTTP client with default rate limiting and retries.

    Args:
        requests_per_second: Rate limit for requests
        max_retries: Maximum retry attempts
        timeout: Request timeout in seconds

    Returns:
        Configured HttpClient instance
    """
    rate_limiter = create_rate_limiter(requests_per_second=requests_per_second)
    retry_handler = create_retry_handler(max_attempts=max_retries)

    return HttpClient(
        rate_limiter=rate_limiter,
        retry_handler=retry_handler,
        timeout=timeout
    )

