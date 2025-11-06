"""
HTTP Fetcher stage for pipeline processing.

Demonstrates:
- HTTP client with rate limiting
- Retry logic and error handling
- Response processing and validation
- Concurrent request management
"""

# Import main classes for easy access
from .rate_limiter import RateLimiter, create_rate_limiter
from .retry_logic import RetryHandler, create_retry_handler
from .http_client_core import HttpClient, HttpResponse, HttpError, create_http_client
from .fetcher_stage import HttpFetcherStage
from .fetcher_stage_batch import BatchHttpFetcherStage

# Convenience functions
def create_http_fetcher_stage(
    name: str,
    base_url: str = "",
    requests_per_second: float = 10.0,
    max_retries: int = 3,
    **kwargs
) -> HttpFetcherStage:
    """Create an HTTP fetcher stage with default configuration.

    Args:
        name: Stage name
        base_url: Base URL for requests
        requests_per_second: Rate limiting
        max_retries: Maximum retry attempts
        **kwargs: Additional HttpFetcherStage parameters

    Returns:
        Configured HttpFetcherStage instance
    """
    return HttpFetcherStage(
        name=name,
        base_url=base_url,
        requests_per_second=requests_per_second,
        max_retries=max_retries,
        **kwargs
    )

__all__ = [
    'RateLimiter', 'create_rate_limiter',
    'RetryHandler', 'create_retry_handler',
    'HttpClient', 'HttpResponse', 'HttpError', 'create_http_client',
    'HttpFetcherStage', 'BatchHttpFetcherStage',
    'create_http_fetcher_stage'
]

