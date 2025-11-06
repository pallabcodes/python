"""
Basic unit tests for HTTP fetcher components.

This module contains fundamental tests for rate limiting,
retry logic, and HTTP client functionality.
"""

import pytest
from unittest.mock import patch

from .rate_limiter import (
    RateLimiter, create_rate_limiter,
    TokenBucketLimiter, FixedWindowLimiter,
    RateLimitConfig, RateLimitAlgorithm
)
from .retry_logic import (
    RetryHandler, create_retry_handler,
    RetryConfig, RetryStrategy, RetryCondition
)
from .http_client import HttpClient, HttpResponse, HttpError


class TestRateLimiter:
    """Tests for rate limiting functionality."""

    def test_token_bucket_limiter(self):
        """Test token bucket rate limiter."""
        limiter = TokenBucketLimiter(requests_per_second=10.0, burst_size=20)

        # Should allow burst
        for i in range(20):
            delay = limiter.acquire()
            assert delay == 0.0

        # Should require delay after burst
        delay = limiter.acquire()
        assert delay > 0

    def test_fixed_window_limiter(self):
        """Test fixed window rate limiter."""
        limiter = FixedWindowLimiter(requests_per_window=5, window_size_seconds=1)

        # Should allow initial burst
        for i in range(5):
            delay = limiter.acquire()
            assert delay == 0.0

        # Should require delay after limit
        delay = limiter.acquire()
        assert delay > 0

    def test_rate_limiter_creation(self):
        """Test rate limiter factory function."""
        limiter = create_rate_limiter(
            algorithm="token_bucket",
            requests_per_second=5.0,
            burst_size=10
        )

        assert isinstance(limiter, RateLimiter)
        stats = limiter.get_stats()
        assert stats["requests_per_second"] == 5.0
        assert stats["burst_size"] == 10


class TestRetryLogic:
    """Tests for retry logic functionality."""

    def test_retry_config_validation(self):
        """Test retry configuration validation."""
        config = RetryConfig(max_attempts=3, base_delay=1.0)
        assert config.max_attempts == 3
        assert config.base_delay == 1.0

        # Test invalid values
        with pytest.raises(ValueError):
            RetryConfig(max_attempts=0)

        with pytest.raises(ValueError):
            RetryConfig(base_delay=0)

    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        handler = create_retry_handler(strategy="exponential_backoff", base_delay=1.0)

        # First retry: 1.0 * 2^0 = 1.0
        delay1 = handler.calculate_delay(1)
        assert delay1 == 1.0

        # Second retry: 1.0 * 2^1 = 2.0
        delay2 = handler.calculate_delay(2)
        assert delay2 == 2.0

    def test_retry_condition_checking(self):
        """Test retry condition evaluation."""
        handler = create_retry_handler()

        # Mock response for HTTP 500
        mock_response = type('MockResponse', (), {'status_code': 500})()

        assert handler.should_retry(ValueError("test"), mock_response)

        # Mock response for HTTP 429
        mock_response.status_code = 429
        assert handler.should_retry(ValueError("test"), mock_response)

    def test_retry_handler_creation(self):
        """Test retry handler factory function."""
        handler = create_retry_handler(
            max_attempts=5,
            strategy="fixed",
            base_delay=2.0
        )

        stats = handler.get_stats()
        assert stats["max_attempts"] == 5
        assert stats["strategy"] == "fixed"
        assert stats["base_delay"] == 2.0


class TestHttpClient:
    """Tests for HTTP client functionality."""

    @patch('requests.Session')
    def test_http_client_creation(self, mock_session):
        """Test HTTP client initialization."""
        client = HttpClient(timeout=10.0, user_agent="TestAgent")

        assert client.timeout == 10.0
        assert client.user_agent == "TestAgent"

    @patch('requests.Session')
    def test_http_client_with_rate_limiting(self, mock_session):
        """Test HTTP client with rate limiter."""
        rate_limiter = create_rate_limiter(requests_per_second=1.0)
        client = HttpClient(rate_limiter=rate_limiter)

        assert client.rate_limiter is rate_limiter

    @patch('requests.Session')
    def test_http_client_with_retries(self, mock_session):
        """Test HTTP client with retry handler."""
        retry_handler = create_retry_handler(max_attempts=3)
        client = HttpClient(retry_handler=retry_handler)

        assert client.retry_handler is retry_handler

    def test_http_response_properties(self):
        """Test HTTP response object properties."""
        import time
        response = HttpResponse(
            status_code=200,
            content=b'{"test": "data"}',
            headers={"content-type": "application/json"},
            url="https://example.com",
            elapsed=1.5,
            request_time=time.time()
        )

        assert response.status_code == 200
        assert response.content == b'{"test": "data"}'
        assert response.headers["content-type"] == "application/json"
        assert response.text == '{"test": "data"}'
        assert response.json() == {"test": "data"}


if __name__ == "__main__":
    """Run basic tests when executed directly."""
    pytest.main([__file__, "-v"])

