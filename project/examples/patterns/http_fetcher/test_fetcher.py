"""
Unit tests for HTTP fetcher functionality.

This module provides comprehensive tests for the HTTP fetcher
components including rate limiting, retries, and pipeline integration.
"""

import time
import pytest
from unittest.mock import Mock, patch
from typing import Any

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
from .fetcher_stage import HttpFetcherStage, BatchHttpFetcherStage


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
        mock_response = Mock()
        mock_response.status_code = 500

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


class TestHttpFetcherStage:
    """Tests for HTTP fetcher pipeline stage."""

    def test_fetcher_stage_initialization(self):
        """Test fetcher stage initialization."""
        stage = HttpFetcherStage(
            name="TestFetcher",
            base_url="https://api.example.com",
            requests_per_second=5.0,
            max_retries=2
        )

        assert stage.name == "TestFetcher"
        assert stage.base_url == "https://api.example.com"
        assert stage.requests_per_second == 5.0
        assert stage.max_retries == 2

    def test_request_params_extraction(self):
        """Test extraction of request parameters."""
        stage = HttpFetcherStage(name="TestFetcher")

        # Test string URL
        params = stage._extract_request_params("https://example.com")
        assert params["url"] == "https://example.com"
        assert params["method"] == "GET"

        # Test dict with parameters
        request_dict = {
            "url": "/api/data",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "data": '{"key": "value"}'
        }
        params = stage._extract_request_params(request_dict)
        assert params["url"] == "/api/data"
        assert params["method"] == "POST"
        assert params["headers"]["Content-Type"] == "application/json"

    @patch('http_fetcher.http_client.HttpClient.request')
    def test_successful_fetch(self, mock_request):
        """Test successful HTTP fetch."""
        # Mock successful response
        mock_response = HttpResponse(
            status_code=200,
            content=b'{"result": "success"}',
            headers={"content-type": "application/json"},
            url="https://api.example.com/data",
            elapsed=0.5,
            request_time=time.time()
        )
        mock_request.return_value = mock_response

        stage = HttpFetcherStage(name="TestFetcher")
        input_data = {"url": "https://api.example.com/data"}

        result = stage.transform(input_data)

        assert result["status_code"] == 200
        assert result["data"] == {"result": "success"}
        assert result["content_type"] == "json"
        assert "elapsed" in result

    @patch('http_fetcher.http_client.HttpClient.request')
    def test_fetch_error_handling(self, mock_request):
        """Test error handling in fetch operations."""
        mock_request.side_effect = HttpError("Connection failed")

        stage = HttpFetcherStage(name="TestFetcher")
        input_data = {"url": "https://api.example.com/data"}

        result = stage.transform(input_data)

        assert result["error"] is True
        assert "Connection failed" in result["error_message"]
        assert result["original_request"] == input_data

    def test_fetcher_stats(self):
        """Test fetcher statistics reporting."""
        stage = HttpFetcherStage(name="TestFetcher")

        stats = stage.get_stats()
        assert stats["stage_name"] == "TestFetcher"
        assert stats["requests_made"] == 0
        assert stats["requests_successful"] == 0
        assert stats["requests_failed"] == 0


class TestBatchHttpFetcherStage:
    """Tests for batch HTTP fetcher stage."""

    def test_batch_fetcher_initialization(self):
        """Test batch fetcher initialization."""
        stage = BatchHttpFetcherStage(
            name="BatchFetcher",
            max_concurrent=5,
            requests_per_second=10.0
        )

        assert stage.name == "BatchFetcher"
        assert stage.max_concurrent == 5

    def test_batch_processing(self):
        """Test batch request processing."""
        stage = BatchHttpFetcherStage(name="BatchFetcher", max_concurrent=2)

        # Mock the underlying fetcher
        mock_fetcher = Mock()
        mock_fetcher.transform.side_effect = [
            {"status_code": 200, "data": "result1"},
            {"status_code": 200, "data": "result2"},
            {"status_code": 200, "data": "result3"}
        ]
        stage._fetcher_stage = mock_fetcher

        batch_data = [
            {"url": "https://api.example.com/1"},
            {"url": "https://api.example.com/2"},
            {"url": "https://api.example.com/3"}
        ]

        result = stage.transform(batch_data)

        assert len(result) == 3
        assert result[0]["data"] == "result1"
        assert result[1]["data"] == "result2"
        assert result[2]["data"] == "result3"

        # Verify calls were made
        assert mock_fetcher.transform.call_count == 3


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])

