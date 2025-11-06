"""
HTTP fetcher stage utilities.

This module contains utility functions and helper methods
for HTTP fetcher stage implementations.
"""

from typing import Any, Dict, Optional, List

from .fetcher_stage_core import HttpFetcherStage


def _extract_request_params(stage: HttpFetcherStage, data: Any) -> Dict[str, Any]:
    """Extract HTTP request parameters from input data.

    Args:
        stage: The HttpFetcherStage instance
        data: Input data (dict with URL and params, or just URL string)

    Returns:
        Dictionary with request parameters
    """
    if isinstance(data, str):
        # Simple URL string
        return {"url": data, "method": "GET"}

    elif isinstance(data, dict):
        # Dictionary with request parameters
        params = dict(data)  # Copy to avoid modifying original

        # Ensure method defaults to GET
        params.setdefault("method", "GET")

        # Build full URL if relative
        if "url" in params and not params["url"].startswith("http"):
            params["url"] = f"{stage.base_url}/{params['url'].lstrip('/')}"

        # Merge default headers
        if "headers" in params:
            merged_headers = stage.default_headers.copy()
            merged_headers.update(params["headers"])
            params["headers"] = merged_headers
        else:
            params["headers"] = stage.default_headers.copy()

        return params

    else:
        raise ValueError(f"Unsupported input data type: {type(data)}")


def _make_request(stage: HttpFetcherStage, params: Dict[str, Any]) -> Any:
    """Make HTTP request using the configured client.

    Args:
        stage: The HttpFetcherStage instance
        params: Request parameters

    Returns:
        HTTP response object
    """
    method = params.get("method", "GET").upper()
    url = params["url"]
    headers = params.get("headers", {})
    data = params.get("data")
    request_params = params.get("params")

    return stage._http_client.request(
        method=method,
        url=url,
        headers=headers,
        data=data,
        params=request_params,
        timeout=params.get("timeout", stage.timeout)
    )


def _process_response(stage: HttpFetcherStage, response: Any, request_params: Dict[str, Any]) -> Dict[str, Any]:
    """Process HTTP response into standardized format.

    Args:
        stage: The HttpFetcherStage instance
        response: HTTP response object
        request_params: Original request parameters

    Returns:
        Processed response data
    """
    # Basic response structure
    result = {
        "url": response.url,
        "status_code": response.status_code,
        "headers": response.headers,
        "elapsed": response.elapsed,
        "request_time": response.request_time,
        "content_length": len(response.content),
        "request_params": request_params
    }

    # Add content based on content type
    content_type = response.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        try:
            result["data"] = response.json()
            result["content_type"] = "json"
        except Exception:
            # Fallback to text if JSON parsing fails
            result["data"] = response.text
            result["content_type"] = "text"
    elif "text/" in content_type or "xml" in content_type:
        result["data"] = response.text
        result["content_type"] = "text"
    else:
        result["data"] = response.content
        result["content_type"] = "binary"

    return result


# Monkey patch utility methods onto HttpFetcherStage
HttpFetcherStage._extract_request_params = _extract_request_params
HttpFetcherStage._make_request = _make_request
HttpFetcherStage._process_response = _process_response

