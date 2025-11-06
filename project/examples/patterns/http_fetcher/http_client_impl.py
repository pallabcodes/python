"""
HTTP client implementation details.

This module contains the actual HTTP request implementation
using requests library and urllib fallback.
"""

import time
import logging
from typing import Optional, Dict, Any, Union

from .http_client_core import HttpClient, HttpResponse, HttpError


def _make_single_request(
    self: HttpClient,
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
    self: HttpClient,
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
    self: HttpClient,
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


# Monkey patch methods onto HttpClient
HttpClient._make_single_request = _make_single_request
HttpClient._make_requests_call = _make_requests_call
HttpClient._make_urllib_call = _make_urllib_call


# Additional HttpClient methods
def get(self: HttpClient, url: str, **kwargs) -> HttpResponse:
    """Make a GET request."""
    return self.request('GET', url, **kwargs)


def post(self: HttpClient, url: str, **kwargs) -> HttpResponse:
    """Make a POST request."""
    return self.request('POST', url, **kwargs)


def put(self: HttpClient, url: str, **kwargs) -> HttpResponse:
    """Make a PUT request."""
    return self.request('PUT', url, **kwargs)


def delete(self: HttpClient, url: str, **kwargs) -> HttpResponse:
    """Make a DELETE request."""
    return self.request('DELETE', url, **kwargs)


def close(self: HttpClient) -> None:
    """Close the HTTP client and cleanup resources."""
    if self._session:
        self._session.close()


def __enter__(self: HttpClient):
    """Context manager entry."""
    return self


def __exit__(self: HttpClient, exc_type, exc_val, exc_tb):
    """Context manager exit."""
    self.close()


def get_stats(self: HttpClient) -> Dict[str, Any]:
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


# Add methods to HttpClient class
HttpClient.get = get
HttpClient.post = post
HttpClient.put = put
HttpClient.delete = delete
HttpClient.close = close
HttpClient.__enter__ = __enter__
HttpClient.__exit__ = __exit__
HttpClient.get_stats = get_stats

