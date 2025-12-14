"""
Unit tests for security rate limiting functionality.
"""

import pytest
import time
import asyncio
from unittest.mock import patch, AsyncMock

from noleet.app.core.security.rate_limiting import (
    SlidingWindowCounter,
    TokenBucket,
    FixedWindowCounter,
    RateLimiter,
    APIRateLimiter,
    DDoSProtection,
    CircuitBreaker,
    RateLimitViolation
)


class TestSlidingWindowCounter:
    """Test sliding window rate limiting."""

    def test_sliding_window_basic(self):
        """Test basic sliding window functionality."""
        limiter = SlidingWindowCounter(max_requests=3, window_seconds=10)

        # Should allow first 3 requests
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")

        # Fourth request should be denied
        assert not limiter.is_allowed("test_key")

    def test_sliding_window_expiration(self):
        """Test request expiration in sliding window."""
        limiter = SlidingWindowCounter(max_requests=2, window_seconds=1)

        # Use up requests
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")
        assert not limiter.is_allowed("test_key")

        # Wait for window to expire
        time.sleep(1.1)

        # Should allow requests again
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")
        assert not limiter.is_allowed("test_key")

    def test_sliding_window_remaining_requests(self):
        """Test remaining requests calculation."""
        limiter = SlidingWindowCounter(max_requests=5, window_seconds=10)

        # Use 2 requests
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")

        # Should have 3 remaining
        assert limiter.get_remaining_requests("test_key") == 3

    def test_sliding_window_reset_time(self):
        """Test reset time calculation."""
        limiter = SlidingWindowCounter(max_requests=2, window_seconds=10)

        # Use requests
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")

        reset_time = limiter.get_reset_time("test_key")
        current_time = time.time()

        # Reset time should be in the future
        assert reset_time > current_time
        assert reset_time <= current_time + 10


class TestTokenBucket:
    """Test token bucket rate limiting."""

    def test_token_bucket_basic(self):
        """Test basic token bucket functionality."""
        limiter = TokenBucket(capacity=5, refill_rate=1)

        # Should allow up to capacity
        for _ in range(5):
            assert limiter.is_allowed("test_key")

        # Should deny when empty
        assert not limiter.is_allowed("test_key")

    def test_token_bucket_refill(self):
        """Test token refill over time."""
        limiter = TokenBucket(capacity=3, refill_rate=1)  # 1 token per second

        # Use all tokens
        for _ in range(3):
            assert limiter.is_allowed("test_key")
        assert not limiter.is_allowed("test_key")

        # Wait for refill
        time.sleep(2.1)

        # Should have refilled
        assert limiter.is_allowed("test_key")

    def test_token_bucket_available_tokens(self):
        """Test available tokens calculation."""
        limiter = TokenBucket(capacity=10, refill_rate=2)

        # Initially full
        assert limiter.get_available_tokens("test_key") == 10

        # Use some tokens
        limiter.is_allowed("test_key", 3)
        assert limiter.get_available_tokens("test_key") == 7

    def test_token_bucket_reset_time(self):
        """Test reset time for full refill."""
        limiter = TokenBucket(capacity=5, refill_rate=1)

        # Empty bucket
        for _ in range(5):
            limiter.is_allowed("test_key")

        reset_time = limiter.get_reset_time("test_key")
        current_time = time.time()

        # Should take about 5 seconds to refill
        assert reset_time >= current_time + 4  # At least 4 seconds
        assert reset_time <= current_time + 6  # At most 6 seconds


class TestFixedWindowCounter:
    """Test fixed window rate limiting."""

    def test_fixed_window_basic(self):
        """Test basic fixed window functionality."""
        limiter = FixedWindowCounter(max_requests=3, window_seconds=5)

        # Should allow first 3 requests
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")

        # Fourth request should be denied
        assert not limiter.is_allowed("test_key")

    def test_fixed_window_boundary(self):
        """Test fixed window boundary conditions."""
        limiter = FixedWindowCounter(max_requests=2, window_seconds=1)

        # Use requests
        assert limiter.is_allowed("test_key")
        assert limiter.is_allowed("test_key")
        assert not limiter.is_allowed("test_key")

        # Wait for next window
        time.sleep(1.1)

        # Should reset
        assert limiter.is_allowed("test_key")


class TestRateLimiter:
    """Test main rate limiter."""

    def test_rate_limiter_rule_addition(self):
        """Test adding rate limiting rules."""
        limiter = RateLimiter()

        limiter.add_rule("test_rule", "sliding_window", max_requests=10, window_seconds=60)
        limiter.add_rule("token_rule", "token_bucket", capacity=5, refill_rate=1)

        assert "test_rule" in limiter.limiters
        assert "token_rule" in limiter.limiters

    def test_rate_limiter_is_allowed(self):
        """Test rate limiter allow/deny logic."""
        limiter = RateLimiter()
        limiter.add_rule("test_rule", "sliding_window", max_requests=2, window_seconds=10)

        # Should allow
        assert limiter.is_allowed("test_rule", "user1")
        assert limiter.is_allowed("test_rule", "user1")

        # Should deny
        assert not limiter.is_allowed("test_rule", "user1")

        # Different user should be allowed
        assert limiter.is_allowed("test_rule", "user2")

    def test_rate_limiter_unknown_rule(self):
        """Test handling of unknown rules."""
        limiter = RateLimiter()

        # Unknown rule should allow (no restriction)
        assert limiter.is_allowed("unknown_rule", "user1")
        assert limiter.get_remaining_requests("unknown_rule", "user1") == 999


class TestAPIRateLimiter:
    """Test API rate limiter."""

    def test_api_rate_limiter_initialization(self):
        """Test API rate limiter setup."""
        limiter = APIRateLimiter()

        # Should have predefined rules
        assert limiter.rate_limiter.is_allowed("api_general", "test_ip")
        assert limiter.rate_limiter.is_allowed("auth_login", "test_ip")

    def test_api_rate_limiter_endpoint_mapping(self):
        """Test endpoint to limiter mapping."""
        limiter = APIRateLimiter()

        # Test different endpoints map to different limiters
        assert limiter._get_limiter_for_endpoint("/api/projects") == "api_general"
        assert limiter._get_limiter_for_endpoint("/auth/login") == "auth_login"
        assert limiter._get_limiter_for_endpoint("/llm/generate") == "llm_calls"
        assert limiter._get_limiter_for_endpoint("/upload/file") == "file_upload"

    def test_api_rate_limiter_request_check(self):
        """Test full request checking."""
        limiter = APIRateLimiter()

        # Should allow initial request
        result = limiter.check_request("/api/test", "192.168.1.1")
        assert result["allowed"] is True
        assert "remaining_requests" in result

        # Should include rate limit headers
        headers = limiter.get_rate_limit_headers("/api/test", "192.168.1.1")
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    def test_api_rate_limiter_strict_auth_limits(self):
        """Test strict limits on auth endpoints."""
        limiter = APIRateLimiter()

        # Login should have very low limit
        for _ in range(5):
            result = limiter.check_request("/auth/login", "192.168.1.1")
            if not result["allowed"]:
                break

        # Should eventually deny
        assert result["allowed"] is False
        assert "Rate limit exceeded" in result["reason"]


class TestDDoSProtection:
    """Test DDoS protection functionality."""

    def test_ddos_normal_requests(self):
        """Test normal request handling."""
        protection = DDoSProtection()

        # Normal requests should be allowed
        assert protection.analyze_request("192.168.1.1", "Mozilla/5.0", {"action": "login"})
        assert protection.analyze_request("192.168.1.2", "Mozilla/5.0", {"action": "view"})

    def test_ddos_high_frequency_detection(self):
        """Test high frequency request detection."""
        protection = DDoSProtection(suspicion_threshold=3)

        ip = "192.168.1.100"

        # Send many requests quickly (simulate attack)
        for i in range(15):
            protection.analyze_request(ip, "Bot/1.0", {"action": f"request_{i}"})

        # IP should be blocked
        assert protection.is_ip_blocked(ip)

    def test_ddos_suspicious_patterns(self):
        """Test suspicious pattern detection."""
        protection = DDoSProtection()

        # Suspicious user agent
        assert protection.analyze_request("192.168.1.1", "", {"action": "login"})

        # Add more suspicious requests
        for _ in range(10):
            protection.analyze_request("192.168.1.1", "", {"action": "login"})

        # Should be flagged
        assert protection.suspicious_patterns["192.168.1.1"] > 0

    def test_ddos_data_cleanup(self):
        """Test old data cleanup."""
        protection = DDoSProtection()

        # Add some requests
        protection.ip_requests["192.168.1.1"].extend([time.time() - 120] * 5)  # Old requests

        # Run cleanup (happens automatically)
        protection._cleanup_old_data(time.time())

        # Old requests should be removed
        assert len(protection.ip_requests["192.168.1.1"]) == 0

    def test_ddos_block_expiration(self):
        """Test block expiration."""
        protection = DDoSProtection()

        ip = "192.168.1.1"

        # Block IP manually
        protection.blocked_ips[ip] = time.time() + 1  # Block for 1 second

        # Should be blocked
        assert protection.is_ip_blocked(ip)

        # Wait for expiration
        time.sleep(1.1)

        # Should be unblocked
        assert not protection.is_ip_blocked(ip)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker()

        # Successful calls should keep it closed
        def success_func():
            return "success"

        for _ in range(5):
            result = breaker.call(success_func)
            assert result == "success"
            assert breaker.state == "CLOSED"

    def test_circuit_breaker_open_state(self):
        """Test circuit breaker opening after failures."""
        breaker = CircuitBreaker(failure_threshold=3)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Service unavailable")

        # Should fail 3 times and open
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_func)

        assert breaker.state == "OPEN"
        assert call_count == 3

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery in half-open state."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Fail to open circuit
        def failing_func():
            raise Exception("Service unavailable")

        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_func)

        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should attempt recovery
        assert breaker.state == "HALF_OPEN"

        # Successful call should close circuit
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == "CLOSED"

    def test_circuit_breaker_failure_in_half_open(self):
        """Test circuit breaker reopening on failure in half-open state."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Open circuit
        def failing_func():
            raise Exception("Service unavailable")

        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_func)

        assert breaker.state == "OPEN"

        # Wait for recovery
        time.sleep(1.1)

        # Fail in half-open state - should reopen
        with pytest.raises(Exception):
            breaker.call(failing_func)

        assert breaker.state == "OPEN"


class TestRateLimitDecorator:
    """Test rate limiting decorator."""

    def test_rate_limit_decorator_sync(self):
        """Test rate limit decorator with sync functions."""
        from noleet.app.core.security.rate_limiting import rate_limit

        @rate_limit("api_general")
        def test_func():
            return "success"

        # Should work initially
        result = test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_async(self):
        """Test rate limit decorator with async functions."""
        from noleet.app.core.security.rate_limiting import rate_limit

        @rate_limit("api_general")
        async def async_test_func():
            return "async success"

        # Should work initially
        result = await async_test_func()
        assert result == "async success"

    def test_rate_limit_decorator_exceed_limit(self):
        """Test rate limit decorator when limit exceeded."""
        from noleet.app.core.security.rate_limiting import rate_limit, RateLimiter

        # Create a very restrictive limiter for testing
        test_limiter = RateLimiter()
        test_limiter.add_rule("test_limit", "sliding_window", max_requests=1, window_seconds=1)

        @rate_limit("test_limit")
        def limited_func():
            return "success"

        # First call should succeed
        result = limited_func()
        assert result == "success"

        # Second call should fail
        with pytest.raises(RateLimitViolation):
            limited_func()
