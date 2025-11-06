"""
HTTP client requests library implementation.

This module contains the requests library implementation
for the HTTP client.
"""

from typing import Optional, Dict, Any, Union

from .http_client_core import HttpClient, HttpResponse, HttpError


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
    request_time = __import__('time').time()

    return HttpResponse(
        status_code=response.status_code,
        content=response.content,
        headers=dict(response.headers),
        url=response.url,
        elapsed=response.elapsed.total_seconds(),
        request_time=request_time
    )


# Monkey patch method onto HttpClient
HttpClient._make_requests_call = _make_requests_call

