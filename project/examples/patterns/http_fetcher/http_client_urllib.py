"""
HTTP client urllib fallback implementation.

This module contains the urllib fallback implementation
for the HTTP client when requests is not available.
"""

from typing import Optional, Dict, Any, Union

from .http_client_core import HttpClient, HttpResponse, HttpError


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

    request_start = __import__('time').time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read()
            elapsed = __import__('time').time() - request_start

            return HttpResponse(
                status_code=response.getcode(),
                content=content,
                headers=dict(response.headers),
                url=url,
                elapsed=elapsed,
                request_time=__import__('time').time()
            )
    except urllib.error.HTTPError as e:
        # Convert to HttpResponse for consistency
        elapsed = __import__('time').time() - request_start
        raise HttpError(f"HTTP {e.code}: {e.reason}", HttpResponse(
            status_code=e.code,
            content=e.read() if hasattr(e, 'read') else b'',
            headers=dict(e.headers) if e.headers else {},
            url=url,
            elapsed=elapsed,
            request_time=__import__('time').time()
        ))
    except urllib.error.URLError as e:
        elapsed = __import__('time').time() - request_start
        raise HttpError(f"URL Error: {e.reason}", None)


# Monkey patch method onto HttpClient
HttpClient._make_urllib_call = _make_urllib_call

