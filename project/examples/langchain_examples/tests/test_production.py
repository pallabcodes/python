"""Unit tests for production patterns."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from production import (
    ProductionLLMWrapper,
    ProductionMetrics,
    ExponentialBackoffRetry
)


class TestProductionMetrics:
    """Tests for ProductionMetrics."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = ProductionMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert len(metrics._latencies) == 0
    
    def test_record_latency(self):
        """Test latency recording."""
        metrics = ProductionMetrics()
        
        metrics.record_latency(0.1)
        metrics.record_latency(0.2)
        metrics.record_latency(0.3)
        
        assert len(metrics._latencies) == 3
    
    def test_latency_bounded(self):
        """Test that latency storage is bounded."""
        metrics = ProductionMetrics()
        
        # Record more than maxlen
        for i in range(1500):
            metrics.record_latency(float(i))
        
        # Should be bounded to maxlen (1000)
        assert len(metrics._latencies) == 1000
    
    def test_get_percentiles(self):
        """Test percentile calculation."""
        metrics = ProductionMetrics()
        
        # Record latencies
        for i in range(100):
            metrics.record_latency(float(i))
        
        percentiles = metrics.get_percentiles()
        
        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        assert "p99.9" in percentiles


class TestExponentialBackoffRetry:
    """Tests for ExponentialBackoffRetry."""
    
    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test retry on success."""
        retry = ExponentialBackoffRetry(max_retries=3, initial_delay=0.1)
        
        call_count = 0
        
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await retry.execute(success_func)
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry on transient failure."""
        retry = ExponentialBackoffRetry(max_retries=3, initial_delay=0.01)
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"
        
        result = await retry.execute(failing_func)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry exhaustion."""
        retry = ExponentialBackoffRetry(max_retries=2, initial_delay=0.01)
        
        async def always_failing_func():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError):
            await retry.execute(always_failing_func)


class TestProductionLLMWrapper:
    """Tests for ProductionLLMWrapper."""
    
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_llm_factory):
        """Test successful generation."""
        wrapper = ProductionLLMWrapper(
            llm_factory=mock_llm_factory,
            enable_semantic_cache=False,
            enable_circuit_breaker=False,
            enable_deduplication=False
        )
        
        result = await wrapper.generate("Test prompt")
        
        assert "result" in result
        assert wrapper.metrics.total_requests == 1
        assert wrapper.metrics.successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_semantic_cache(self, mock_llm_factory):
        """Test semantic caching."""
        wrapper = ProductionLLMWrapper(
            llm_factory=mock_llm_factory,
            enable_semantic_cache=True,
            enable_circuit_breaker=False,
            enable_deduplication=False
        )
        
        # First call
        result1 = await wrapper.generate("What is Python?")
        assert wrapper.metrics.cache_misses == 1
        
        # Second call (should hit cache)
        result2 = await wrapper.generate("Tell me about Python")
        assert wrapper.metrics.semantic_cache_hits >= 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, mock_llm_factory):
        """Test circuit breaker integration."""
        wrapper = ProductionLLMWrapper(
            llm_factory=mock_llm_factory,
            enable_semantic_cache=False,
            enable_circuit_breaker=True,
            enable_deduplication=False
        )
        
        # Normal operation
        result = await wrapper.generate("Test prompt")
        assert result is not None
        
        # Check metrics
        metrics = await wrapper.get_metrics()
        assert "circuit_breaker" in metrics
    
    @pytest.mark.asyncio
    async def test_deduplication_integration(self, mock_llm_factory):
        """Test deduplication integration."""
        wrapper = ProductionLLMWrapper(
            llm_factory=mock_llm_factory,
            enable_semantic_cache=False,
            enable_circuit_breaker=False,
            enable_deduplication=True
        )
        
        # Concurrent calls with same prompt
        tasks = [
            wrapper.generate("Test prompt", use_deduplication=True)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        assert wrapper.metrics.deduplicated_requests >= 4  # At least 4 deduplicated
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, mock_llm_factory):
        """Test metrics retrieval."""
        wrapper = ProductionLLMWrapper(
            llm_factory=mock_llm_factory,
            enable_semantic_cache=False,
            enable_circuit_breaker=False,
            enable_deduplication=False
        )
        
        await wrapper.generate("Test prompt")
        
        metrics = await wrapper.get_metrics()
        
        assert "total_requests" in metrics
        assert "success_rate" in metrics
        assert "cache_hit_rate" in metrics

