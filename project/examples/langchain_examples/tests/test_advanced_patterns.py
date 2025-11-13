"""Unit tests for advanced patterns."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from advanced_patterns import (
    AdaptiveCircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    SemanticCache,
    TokenBucketRateLimiter,
    RequestDeduplicator,
    ConnectionPool,
    ConnectionPoolExhaustedError,
    IntelligentBatcher,
    DistributedTracer
)


class TestAdaptiveCircuitBreaker:
    """Tests for AdaptiveCircuitBreaker."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in CLOSED state."""
        breaker = AdaptiveCircuitBreaker("test_breaker")
        
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        
        metrics = await breaker.get_metrics()
        assert metrics["state"] == "closed"
        assert metrics["total_requests"] == 1
        assert metrics["total_failures"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout_seconds=1.0)
        breaker = AdaptiveCircuitBreaker("test_breaker", config)
        
        async def failing_func():
            raise ValueError("Test error")
        
        # Trigger failures
        for _ in range(3):
            try:
                await breaker.call(failing_func)
            except ValueError:
                pass
        
        # Circuit should be open
        metrics = await breaker.get_metrics()
        assert metrics["state"] == "open"
        assert metrics["total_failures"] == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_raises_when_open(self):
        """Test circuit breaker raises when open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=1.0)
        breaker = AdaptiveCircuitBreaker("test_breaker", config)
        
        async def failing_func():
            raise ValueError("Test error")
        
        # Trigger failure
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass
        
        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_thread_safety(self):
        """Test circuit breaker thread safety with concurrent calls."""
        breaker = AdaptiveCircuitBreaker("test_breaker")
        
        async def success_func():
            await asyncio.sleep(0.01)
            return "success"
        
        # Concurrent calls
        tasks = [breaker.call(success_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert all(r == "success" for r in results)
        metrics = await breaker.get_metrics()
        assert metrics["total_requests"] == 10


class TestSemanticCache:
    """Tests for SemanticCache."""
    
    def test_cache_put_and_get(self):
        """Test basic cache put and get."""
        cache = SemanticCache(max_size=10, ttl_seconds=3600.0)
        
        cache.put("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        cache = SemanticCache(max_size=10, ttl_seconds=0.1)
        
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("key1") is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = SemanticCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.put("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
    
    def test_semantic_similarity_matching(self):
        """Test semantic similarity matching."""
        cache = SemanticCache(max_size=10, similarity_threshold=0.8)
        
        cache.put("What is Python?", "Python is a programming language")
        
        # Similar query should match
        result = cache.get("Tell me about Python")
        assert result is not None
    
    def test_embeddings_memory_bounded(self):
        """Test that embeddings dictionary is bounded."""
        cache = SemanticCache(max_size=3)
        
        # Fill cache beyond max_size
        for i in range(10):
            cache.put(f"key{i}", f"value{i}")
        
        # Embeddings should be bounded
        assert len(cache._embeddings) <= 3


class TestTokenBucketRateLimiter:
    """Tests for TokenBucketRateLimiter."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting."""
        limiter = TokenBucketRateLimiter(rate=2.0, capacity=2.0)
        
        # First 2 should succeed
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        
        # Third should be rate limited
        assert await limiter.acquire() is False
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test token refill over time."""
        limiter = TokenBucketRateLimiter(rate=2.0, capacity=2.0)
        
        # Consume all tokens
        await limiter.acquire()
        await limiter.acquire()
        
        # Wait for refill
        await asyncio.sleep(0.6)  # Should refill 1 token
        
        assert await limiter.acquire() is True


class TestRequestDeduplicator:
    """Tests for RequestDeduplicator."""
    
    @pytest.mark.asyncio
    async def test_deduplication(self):
        """Test request deduplication."""
        deduplicator = RequestDeduplicator(deduplication_window_seconds=60.0)
        
        call_count = 0
        
        async def expensive_func(x: int):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return x * 2
        
        # Concurrent calls with same args
        tasks = [
            deduplicator.execute(expensive_func, 5)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        # Should only call once
        assert call_count == 1
        assert all(r == 10 for r in results)
    
    @pytest.mark.asyncio
    async def test_deduplication_window(self):
        """Test deduplication window expiration."""
        deduplicator = RequestDeduplicator(deduplication_window_seconds=0.1)
        
        call_count = 0
        
        async def func(x: int):
            nonlocal call_count
            call_count += 1
            return x
        
        # First call
        await deduplicator.execute(func, 1)
        assert call_count == 1
        
        # Second call within window (should deduplicate)
        await deduplicator.execute(func, 1)
        assert call_count == 1
        
        # Wait for window to expire
        await asyncio.sleep(0.2)
        
        # Third call after window (should not deduplicate)
        await deduplicator.execute(func, 1)
        assert call_count == 2


class TestConnectionPool:
    """Tests for ConnectionPool."""
    
    @pytest.mark.asyncio
    async def test_connection_acquisition(self):
        """Test connection acquisition."""
        pool = ConnectionPool(factory=lambda: Mock(), min_size=1, max_size=3)
        
        conn1 = await pool.acquire()
        assert conn1 is not None
        
        await pool.release(conn1)
    
    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self):
        """Test connection pool exhaustion with timeout."""
        pool = ConnectionPool(
            factory=lambda: Mock(),
            min_size=1,
            max_size=2,
            acquire_timeout=0.5
        )
        
        # Acquire all connections
        conn1 = await pool.acquire()
        conn2 = await pool.acquire()
        
        # Next acquisition should timeout
        with pytest.raises(ConnectionPoolExhaustedError):
            await pool.acquire(timeout=0.1)
        
        await pool.release(conn1)
        await pool.release(conn2)
    
    @pytest.mark.asyncio
    async def test_connection_pool_waiters(self):
        """Test connection pool waiters."""
        pool = ConnectionPool(factory=lambda: Mock(), min_size=1, max_size=2)
        
        # Acquire all connections
        conn1 = await pool.acquire()
        conn2 = await pool.acquire()
        
        # Start waiter task
        async def waiter():
            return await pool.acquire()
        
        waiter_task = asyncio.create_task(waiter())
        
        # Release connection
        await asyncio.sleep(0.1)
        await pool.release(conn1)
        
        # Waiter should get connection
        conn3 = await waiter_task
        assert conn3 is not None
        
        await pool.release(conn2)
        await pool.release(conn3)


class TestIntelligentBatcher:
    """Tests for IntelligentBatcher."""
    
    @pytest.mark.asyncio
    async def test_batching(self):
        """Test intelligent batching."""
        batcher = IntelligentBatcher(max_batch_size=5, min_batch_size=2, max_wait_seconds=0.1)
        
        async def process_batch(items):
            return [f"result_{item}" for item in items]
        
        # Submit items
        futures = []
        for i in range(3):
            future = await batcher.submit(i, process_batch)
            futures.append(future)
        
        # Wait for results
        results = await asyncio.gather(*futures)
        assert len(results) == 3


class TestDistributedTracer:
    """Tests for DistributedTracer."""
    
    def test_trace_creation(self):
        """Test trace creation."""
        tracer = DistributedTracer("test_service")
        
        trace_id = tracer.start_trace("test_operation")
        assert trace_id is not None
        
        span_id = tracer.start_span(trace_id, "test_span")
        assert span_id is not None
    
    def test_span_logging(self):
        """Test span logging."""
        tracer = DistributedTracer("test_service")
        
        trace_id = tracer.start_trace("test_operation")
        span_id = tracer.start_span(trace_id, "test_span")
        
        tracer.log_span(trace_id, span_id, "test_event", {"key": "value"})
        
        spans = tracer.get_trace(trace_id)
        assert len(spans) > 0

