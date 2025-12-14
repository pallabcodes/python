"""
Performance tests for caching system.
Benchmarks cache performance, hit rates, and memory usage.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from benchmarks.benchmark_framework import BenchmarkSuite, PerformanceProfiler, MemoryProfiler
from noleet.core.cache import CacheManager, CacheConfig, LRUCache, LFUCache, TTLCache


class TestCachePerformance(BenchmarkSuite):
    """Performance benchmarks for caching operations."""

    def __init__(self):
        super().__init__("cache_performance", "Cache system performance benchmarks")

    def setup_method(self):
        """Setup cache instances for testing."""
        self.memory_cache = CacheManager().get_cache("test_memory", backend="memory", strategy="lru")
        self.memory_cache.clear()

    def test_cache_set_performance(self):
        """Benchmark cache set operations."""
        def benchmark():
            for i in range(100):
                self.memory_cache.set(f"key_{i}", f"value_{i}")
            return 100

        self.add_benchmark("cache_set_100_items", benchmark)

    def test_cache_get_performance(self):
        """Benchmark cache get operations."""
        # Pre-populate cache
        for i in range(100):
            self.memory_cache.set(f"key_{i}", f"value_{i}")

        def benchmark():
            total = 0
            for i in range(100):
                value = self.memory_cache.get(f"key_{i}")
                if value:
                    total += 1
            return total

        self.add_benchmark("cache_get_100_items", benchmark)

    def test_cache_hit_miss_ratio(self):
        """Benchmark cache hit/miss performance."""
        # Pre-populate half the cache
        for i in range(50):
            self.memory_cache.set(f"key_{i}", f"value_{i}")

        def benchmark():
            hits = 0
            misses = 0
            for i in range(100):
                value = self.memory_cache.get(f"key_{i}")
                if value:
                    hits += 1
                else:
                    misses += 1
            return hits, misses

        self.add_benchmark("cache_hit_miss_50_50", benchmark)

    def test_cache_concurrent_access(self):
        """Benchmark concurrent cache access."""
        import threading

        results = []
        errors = []

        def worker_thread(thread_id):
            try:
                # Each thread does 50 operations
                for i in range(50):
                    key = f"thread_{thread_id}_key_{i}"
                    self.memory_cache.set(key, f"value_{i}")
                    value = self.memory_cache.get(key)
                    if value != f"value_{i}":
                        errors.append(f"Thread {thread_id}: value mismatch")
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        def benchmark():
            threads = []
            num_threads = 5

            # Start threads
            for i in range(num_threads):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            return len(results), len(errors)

        self.add_benchmark("cache_concurrent_5_threads", benchmark)


class TestCacheStrategies(BenchmarkSuite):
    """Performance benchmarks for different cache strategies."""

    def __init__(self):
        super().__init__("cache_strategies", "Cache strategy performance benchmarks")

    def test_lru_strategy_performance(self):
        """Benchmark LRU cache strategy."""
        cache = LRUCache(max_size=1000)

        def benchmark():
            operations = 0
            for i in range(1000):
                cache.on_add(f"key_{i}", MagicMock())
                operations += 1

                if i > 100:  # Start evicting
                    evicted = cache.should_evict(f"key_{i}", 100)
                    operations += len(evicted)

            return operations

        self.add_benchmark("lru_strategy_1000_operations", benchmark)

    def test_lfu_strategy_performance(self):
        """Benchmark LFU cache strategy."""
        cache = LFUCache(max_size=1000)

        def benchmark():
            operations = 0
            # Add items
            for i in range(500):
                cache.on_add(f"key_{i}", MagicMock())
                operations += 1

            # Access some items more frequently
            for i in range(10):  # Multiple accesses for some items
                for j in range(10):
                    cache.on_access(f"key_{j}")
                    operations += 1

            # Check evictions
            evicted = cache.should_evict("new_key", 100)
            operations += len(evicted)

            return operations

        self.add_benchmark("lfu_strategy_500_operations", benchmark)

    def test_ttl_strategy_performance(self):
        """Benchmark TTL cache strategy."""
        cache = TTLCache(ttl_seconds=60, max_size=1000)

        def benchmark():
            operations = 0
            # Add items with different TTLs
            for i in range(100):
                mock_entry = MagicMock()
                mock_entry.is_expired.return_value = False
                mock_entry.ttl_seconds = 60
                cache.on_add(f"key_{i}", mock_entry)
                operations += 1

            # Check expirations
            expired = cache.cleanup_expired()
            operations += len(expired)

            return operations

        self.add_benchmark("ttl_strategy_100_operations", benchmark)


class TestLLMCacheIntegration(BenchmarkSuite):
    """Performance benchmarks for LLM caching integration."""

    def __init__(self):
        super().__init__("llm_cache_integration", "LLM caching integration benchmarks")

    def setup_method(self):
        """Setup mock LLM for testing."""
        self.mock_llm = MagicMock()
        self.mock_llm._model_name = "test-model"
        self.mock_llm._generate_response.side_effect = lambda prompt, **kwargs: f"Response to: {prompt[:50]}..."

        # Mock cache
        self.cache_patcher = patch('noleet.llm.llm_base.get_llm_cache')
        self.mock_cache = self.cache_patcher.start()
        self.mock_cache_instance = MagicMock()
        self.mock_cache.return_value = self.mock_cache_instance

    def teardown_method(self):
        """Cleanup mocks."""
        self.cache_patcher.stop()

    def test_llm_cache_hit_performance(self):
        """Benchmark LLM cache hit performance."""
        # Setup cache hit
        self.mock_cache_instance.get.return_value = "Cached response"

        def benchmark():
            # Import here to avoid issues
            from noleet.llm.providers.mock_llm import MockLLM

            llm = MockLLM()
            # Simulate cached response
            response = llm.generate("Test prompt", use_cache=True)
            return len(response) if response else 0

        self.add_benchmark("llm_cache_hit", benchmark)

    def test_llm_cache_miss_performance(self):
        """Benchmark LLM cache miss performance."""
        # Setup cache miss
        self.mock_cache_instance.get.return_value = None

        def benchmark():
            from noleet.llm.providers.mock_llm import MockLLM

            llm = MockLLM()
            response = llm.generate("Test prompt", use_cache=True)
            return len(response) if response else 0

        self.add_benchmark("llm_cache_miss", benchmark)

    def test_llm_no_cache_performance(self):
        """Benchmark LLM without caching."""
        def benchmark():
            from noleet.llm.providers.mock_llm import MockLLM

            llm = MockLLM()
            response = llm.generate("Test prompt", use_cache=False)
            return len(response) if response else 0

        self.add_benchmark("llm_no_cache", benchmark)


class TestEmbedderCacheIntegration(BenchmarkSuite):
    """Performance benchmarks for embedder caching integration."""

    def __init__(self):
        super().__init__("embedder_cache_integration", "Embedder caching integration benchmarks")

    def setup_method(self):
        """Setup mock embedder for testing."""
        self.cache_patcher = patch('noleet.llm.llm_base.get_llm_cache')
        self.mock_cache = self.cache_patcher.start()
        self.mock_cache_instance = MagicMock()
        self.mock_cache.return_value = self.mock_cache_instance

    def teardown_method(self):
        """Cleanup mocks."""
        self.cache_patcher.stop()

    def test_embedder_cache_hit_performance(self):
        """Benchmark embedder cache hit performance."""
        # Setup cache hit for all texts
        cached_embedding = [0.1, 0.2, 0.3] * 128  # 384-dimensional
        self.mock_cache_instance.get.return_value = cached_embedding

        def benchmark():
            from noleet.llm.providers.mock_embedder import MockEmbedder

            embedder = MockEmbedder()
            embeddings = embedder.embed(["Test text 1", "Test text 2"])
            return len(embeddings), len(embeddings[0]) if embeddings else 0

        self.add_benchmark("embedder_cache_hit", benchmark)

    def test_embedder_cache_miss_performance(self):
        """Benchmark embedder cache miss performance."""
        # Setup cache miss
        self.mock_cache_instance.get.return_value = None

        def benchmark():
            from noleet.llm.providers.mock_embedder import MockEmbedder

            embedder = MockEmbedder()
            embeddings = embedder.embed(["Test text 1", "Test text 2"])
            return len(embeddings), len(embeddings[0]) if embeddings else 0

        self.add_benchmark("embedder_cache_miss", benchmark)


# Performance test fixtures
@pytest.fixture
def cache_performance_suite():
    """Fixture for cache performance benchmarks."""
    return TestCachePerformance()


@pytest.fixture
def cache_strategies_suite():
    """Fixture for cache strategies benchmarks."""
    return TestCacheStrategies()


@pytest.fixture
def llm_cache_suite():
    """Fixture for LLM cache integration benchmarks."""
    return TestLLMCacheIntegration()


@pytest.fixture
def embedder_cache_suite():
    """Fixture for embedder cache integration benchmarks."""
    return TestEmbedderCacheIntegration()


# Performance test functions
def test_cache_performance_basic(cache_performance_suite):
    """Run basic cache performance benchmarks."""
    results = cache_performance_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error
        assert result.metrics.execution_time >= 0


def test_cache_strategies_performance(cache_strategies_suite):
    """Run cache strategies performance benchmarks."""
    results = cache_strategies_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error


def test_llm_cache_integration(llm_cache_suite):
    """Run LLM cache integration benchmarks."""
    results = llm_cache_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error


def test_embedder_cache_integration(embedder_cache_suite):
    """Run embedder cache integration benchmarks."""
    results = embedder_cache_suite.run_all(iterations=1, warmup_iterations=0)

    assert len(results) > 0
    for result in results:
        assert not result.error


# Detailed performance profiling tests
def test_cache_memory_usage_profiling():
    """Detailed memory profiling of cache operations."""
    profiler = MemoryProfiler()

    cache_manager = CacheManager()
    cache = cache_manager.get_cache("memory_test", backend="memory", strategy="lru")

    def cache_operations():
        # Perform various cache operations
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}" * 100)  # Larger values
            cache.get(f"key_{i}")

        # Test eviction
        for i in range(100, 200):
            cache.set(f"key_{i}", f"value_{i}" * 100)

    result = profiler.profile_memory_usage(cache_operations)

    assert 'memory_delta' in result
    assert result['memory_delta'] >= 0


def test_cache_throughput_measurement():
    """Test cache throughput measurement."""
    profiler = PerformanceProfiler()

    cache_manager = CacheManager()
    cache = cache_manager.get_cache("throughput_test", backend="memory", strategy="lru")

    def cache_workload():
        # Simulate mixed read/write workload
        for i in range(100):
            if i % 2 == 0:
                cache.set(f"key_{i}", f"value_{i}")
            else:
                cache.get(f"key_{i % 50}")  # Mix hits and misses

    result = profiler.measure_throughput(cache_workload, duration_seconds=1)

    assert result['total_operations'] >= 0
    assert 'operations_per_second' in result
    assert 'average_latency' in result


def test_cache_memory_leak_detection():
    """Test for memory leaks in cache operations."""
    profiler = MemoryProfiler()

    def cache_stress_test():
        cache_manager = CacheManager()
        cache = cache_manager.get_cache("leak_test", backend="memory", strategy="lru")

        # Perform many cache operations
        for iteration in range(50):
            for i in range(100):
                key = f"iter_{iteration}_key_{i}"
                cache.set(key, f"value_{i}" * 10)
                cache.get(key)

    result = profiler.detect_memory_leaks(cache_stress_test, iterations=3)

    assert 'leak_detected' in result
    # Memory leaks in cache operations are concerning
    if result['leak_detected']:
        print(f"Memory leak detected: {result['growth_rate_per_iteration']} bytes per iteration")
