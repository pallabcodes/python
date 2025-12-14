"""
Rate limiting and DDoS protection for security hardening.
OWASP compliant rate limiting implementation.
"""

import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from functools import wraps
import logging

from .validation import SecurityValidationError, SecurityAudit

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    requests: int  # Number of requests allowed
    window: int    # Time window in seconds
    burst: Optional[int] = None  # Burst allowance
    block_duration: Optional[int] = None  # Block duration after violation


class RateLimitViolation(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class SlidingWindowCounter:
    """Sliding window rate limiting using counter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key."""
        current_time = time.time()

        # Remove expired requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(current_time)
            return True

        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the key."""
        current_time = time.time()
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < self.window_seconds
        ]
        return max(0, self.max_requests - len(self.requests[key]))

    def get_reset_time(self, key: str) -> float:
        """Get time when the limit resets."""
        if not self.requests[key]:
            return time.time()
        return min(self.requests[key]) + self.window_seconds


class TokenBucket:
    """Token bucket algorithm for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens: Dict[str, float] = defaultdict(lambda: capacity)
        self.last_refill: Dict[str, float] = defaultdict(time.time)

    def is_allowed(self, key: str, tokens_needed: int = 1) -> bool:
        """Check if request is allowed and consume tokens."""
        current_time = time.time()

        # Refill tokens
        time_passed = current_time - self.last_refill[key]
        tokens_to_add = time_passed * self.refill_rate
        self.tokens[key] = min(self.capacity, self.tokens[key] + tokens_to_add)
        self.last_refill[key] = current_time

        # Check if we have enough tokens
        if self.tokens[key] >= tokens_needed:
            self.tokens[key] -= tokens_needed
            return True

        return False

    def get_available_tokens(self, key: str) -> float:
        """Get available tokens for the key."""
        current_time = time.time()
        time_passed = current_time - self.last_refill[key]
        tokens_to_add = time_passed * self.refill_rate
        available = min(self.capacity, self.tokens[key] + tokens_to_add)
        return available

    def get_reset_time(self, key: str) -> float:
        """Get time when tokens will be fully refilled."""
        available = self.get_available_tokens(key)
        if available >= self.capacity:
            return time.time()
        tokens_needed = self.capacity - available
        return time.time() + (tokens_needed / self.refill_rate)


class FixedWindowCounter:
    """Fixed window rate limiting."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, int] = defaultdict(int)
        self.window_start: Dict[str, float] = defaultdict(time.time)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        current_time = time.time()
        window_key = f"{key}:{int(current_time / self.window_seconds)}"

        # Reset counter for new window
        if current_time - self.window_start[key] >= self.window_seconds:
            self.requests[key] = 0
            self.window_start[key] = current_time

        # Check limit
        if self.requests[key] < self.max_requests:
            self.requests[key] += 1
            return True

        return False


class RateLimiter:
    """Main rate limiter with multiple algorithms."""

    def __init__(self):
        self.limiters: Dict[str, Any] = {}

    def add_rule(self, name: str, algorithm: str, **kwargs):
        """Add a rate limiting rule."""
        if algorithm == "sliding_window":
            self.limiters[name] = SlidingWindowCounter(**kwargs)
        elif algorithm == "token_bucket":
            self.limiters[name] = TokenBucket(**kwargs)
        elif algorithm == "fixed_window":
            self.limiters[name] = FixedWindowCounter(**kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def is_allowed(self, limiter_name: str, key: str) -> bool:
        """Check if request is allowed."""
        if limiter_name not in self.limiters:
            return True  # No limiter configured

        return self.limiters[limiter_name].is_allowed(key)

    def get_remaining_requests(self, limiter_name: str, key: str) -> int:
        """Get remaining requests."""
        if limiter_name not in self.limiters:
            return 999  # Unlimited

        limiter = self.limiters[limiter_name]
        if hasattr(limiter, 'get_remaining_requests'):
            return limiter.get_remaining_requests(key)
        elif hasattr(limiter, 'get_available_tokens'):
            return int(limiter.get_available_tokens(key))
        else:
            return 999  # Unknown limiter type

    def get_reset_time(self, limiter_name: str, key: str) -> float:
        """Get reset time."""
        if limiter_name not in self.limiters:
            return time.time()

        limiter = self.limiters[limiter_name]
        if hasattr(limiter, 'get_reset_time'):
            return limiter.get_reset_time(key)
        else:
            return time.time()


class DDoSProtection:
    """DDoS protection and anomaly detection."""

    def __init__(self, suspicion_threshold: int = 10):
        self.suspicion_threshold = suspicion_threshold
        self.ip_requests: Dict[str, List[float]] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}  # ip -> unblock_time
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)

    def analyze_request(self, ip_address: str, user_agent: str, request_data: Dict[str, Any]) -> bool:
        """Analyze request for DDoS patterns."""
        current_time = time.time()

        # Clean old data
        self._cleanup_old_data(current_time)

        # Track requests per IP
        self.ip_requests[ip_address].append(current_time)

        # Check for suspicious patterns
        is_suspicious = self._detect_suspicious_patterns(ip_address, user_agent, request_data)

        if is_suspicious:
            self.suspicious_patterns[ip_address] += 1

        # Check if IP should be blocked
        if self._should_block_ip(ip_address):
            self.blocked_ips[ip_address] = current_time + 3600  # Block for 1 hour
            SecurityAudit.log_security_event(
                "IP_BLOCKED",
                {"ip_address": ip_address, "reason": "DDoS_suspicion"},
                "WARNING"
            )
            return False

        return True

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked."""
        current_time = time.time()
        if ip_address in self.blocked_ips:
            if current_time < self.blocked_ips[ip_address]:
                return True
            else:
                # Unblock expired
                del self.blocked_ips[ip_address]
        return False

    def _cleanup_old_data(self, current_time: float):
        """Clean up old request data."""
        cutoff_time = current_time - 60  # 1 minute window

        for ip in list(self.ip_requests.keys()):
            self.ip_requests[ip] = [
                req_time for req_time in self.ip_requests[ip]
                if req_time > cutoff_time
            ]
            if not self.ip_requests[ip]:
                del self.ip_requests[ip]

    def _detect_suspicious_patterns(self, ip_address: str, user_agent: str, request_data: Dict[str, Any]) -> bool:
        """Detect suspicious patterns in requests."""
        suspicious = False

        # Check request frequency (more than 100 requests per minute)
        recent_requests = len([t for t in self.ip_requests[ip_address] if time.time() - t < 60])
        if recent_requests > 100:
            suspicious = True

        # Check for empty or suspicious user agent
        if not user_agent or len(user_agent) < 10:
            suspicious = True

        # Check for unusual request patterns
        if 'payload' in request_data:
            payload = str(request_data['payload'])
            if len(payload) > 10000:  # Very large payload
                suspicious = True

        return suspicious

    def _should_block_ip(self, ip_address: str) -> bool:
        """Determine if IP should be blocked."""
        # Block if too many suspicious patterns
        if self.suspicious_patterns[ip_address] > self.suspicion_threshold:
            return True

        # Block if extreme request frequency
        recent_requests = len([t for t in self.ip_requests[ip_address] if time.time() - t < 60])
        if recent_requests > 1000:  # More than 1000 requests per minute
            return True

        return False


class APIRateLimiter:
    """API rate limiter with multiple tiers."""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.ddos_protection = DDoSProtection()

        # Configure rate limiting rules
        self._setup_rate_limits()

    def _setup_rate_limits(self):
        """Set up rate limiting rules for different endpoints."""
        # General API limits
        self.rate_limiter.add_rule(
            "api_general",
            "sliding_window",
            max_requests=1000,  # 1000 requests
            window_seconds=3600  # per hour
        )

        # Authentication endpoints (stricter)
        self.rate_limiter.add_rule(
            "auth_login",
            "sliding_window",
            max_requests=5,  # 5 login attempts
            window_seconds=300  # per 5 minutes
        )

        # User registration
        self.rate_limiter.add_rule(
            "auth_register",
            "sliding_window",
            max_requests=3,  # 3 registration attempts
            window_seconds=3600  # per hour
        )

        # LLM API calls (expensive operations)
        self.rate_limiter.add_rule(
            "llm_calls",
            "token_bucket",
            capacity=100,  # 100 tokens
            refill_rate=10  # 10 tokens per second (600 per minute)
        )

        # File uploads
        self.rate_limiter.add_rule(
            "file_upload",
            "sliding_window",
            max_requests=10,  # 10 uploads
            window_seconds=3600  # per hour
        )

    def check_request(self, endpoint: str, client_ip: str, user_id: Optional[str] = None,
                     user_agent: str = "", request_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check if request should be allowed."""
        # DDoS protection check
        if not self.ddos_protection.analyze_request(client_ip, user_agent, request_data or {}):
            SecurityAudit.log_security_event(
                "REQUEST_BLOCKED",
                {"ip_address": client_ip, "reason": "DDoS_protection"},
                "WARNING"
            )
            return {
                "allowed": False,
                "reason": "Request blocked by DDoS protection",
                "retry_after": 3600
            }

        # Check if IP is blocked
        if self.ddos_protection.is_ip_blocked(client_ip):
            return {
                "allowed": False,
                "reason": "IP address temporarily blocked",
                "retry_after": 3600
            }

        # Determine rate limit key (user-specific or IP-based)
        rate_limit_key = user_id if user_id else client_ip

        # Select appropriate limiter based on endpoint
        limiter_name = self._get_limiter_for_endpoint(endpoint)

        # Check rate limit
        if not self.rate_limiter.is_allowed(limiter_name, rate_limit_key):
            reset_time = self.rate_limiter.get_reset_time(limiter_name, rate_limit_key)
            retry_after = max(1, int(reset_time - time.time()))

            SecurityAudit.log_security_event(
                "RATE_LIMIT_EXCEEDED",
                {
                    "endpoint": endpoint,
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "limiter": limiter_name
                },
                "WARNING"
            )

            return {
                "allowed": False,
                "reason": "Rate limit exceeded",
                "retry_after": retry_after,
                "remaining_requests": self.rate_limiter.get_remaining_requests(limiter_name, rate_limit_key)
            }

        return {
            "allowed": True,
            "remaining_requests": self.rate_limiter.get_remaining_requests(limiter_name, rate_limit_key)
        }

    def _get_limiter_for_endpoint(self, endpoint: str) -> str:
        """Get appropriate limiter for endpoint."""
        endpoint = endpoint.lower()

        if '/auth/login' in endpoint or '/login' in endpoint:
            return "auth_login"
        elif '/auth/register' in endpoint or '/register' in endpoint:
            return "auth_register"
        elif '/llm/' in endpoint or '/generate' in endpoint:
            return "llm_calls"
        elif '/upload' in endpoint or '/file' in endpoint:
            return "file_upload"
        else:
            return "api_general"

    def get_rate_limit_headers(self, endpoint: str, client_ip: str, user_id: Optional[str] = None) -> Dict[str, str]:
        """Get rate limit headers for response."""
        rate_limit_key = user_id if user_id else client_ip
        limiter_name = self._get_limiter_for_endpoint(endpoint)

        remaining = self.rate_limiter.get_remaining_requests(limiter_name, rate_limit_key)
        reset_time = self.rate_limiter.get_reset_time(limiter_name, rate_limit_key)

        return {
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_time)),
            "X-RateLimit-Limit": "1000",  # Default limit
        }


def rate_limit(endpoint_type: str = "api_general", key_func: Optional[Callable] = None):
    """Decorator for rate limiting endpoints."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get rate limiter from app context (would be injected in FastAPI)
            rate_limiter = kwargs.get('rate_limiter')
            if not rate_limiter:
                return await func(*args, **kwargs)

            # Determine key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default to IP address
                key = kwargs.get('client_ip', 'unknown')

            # Check rate limit
            if not rate_limiter.is_allowed(endpoint_type, key):
                reset_time = rate_limiter.get_reset_time(endpoint_type, key)
                retry_after = max(1, int(reset_time - time.time()))

                raise RateLimitViolation(f"Rate limit exceeded. Retry after {retry_after} seconds")

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Synchronous version
            rate_limiter = kwargs.get('rate_limiter')
            if not rate_limiter:
                return func(*args, **kwargs)

            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = kwargs.get('client_ip', 'unknown')

            if not rate_limiter.is_allowed(endpoint_type, key):
                reset_time = rate_limiter.get_reset_time(endpoint_type, key)
                retry_after = max(1, int(reset_time - time.time()))

                raise RateLimitViolation(f"Rate limit exceeded. Retry after {retry_after} seconds")

            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global instances (in production, use dependency injection)
rate_limiter = APIRateLimiter()
ddos_protection = DDoSProtection()

__all__ = [
    'RateLimiter',
    'APIRateLimiter',
    'DDoSProtection',
    'CircuitBreaker',
    'RateLimitViolation',
    'rate_limit',
    'rate_limiter',
    'ddos_protection'
]
