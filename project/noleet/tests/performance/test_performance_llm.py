"""
Performance tests for LLM integration components.
Benchmarks LLM operations, embeddings, and API calls.
"""

import pytest
from unittest.mock import patch, MagicMock
import time

from benchmarks.benchmark_framework import BenchmarkSuite, PerformanceProfiler
from noleet.llm.llm_factory import LLMFactory
from noleet.llm.llm_config import LLMConfig
from noleet.llm.embedder import Embedder


class TestLLMPerformance(BenchmarkSuite):
    """Performance benchmarks for LLM operations."""

    def __init__(self):
        super().__init__("llm_performance", "LLM integration performance benchmarks")

        # Setup mock LLM for consistent testing
        self.mock_config = LLMConfig()
        self.mock_config.default_llm_provider = "mock"
        self.mock_config.default_embedder_provider = "mock"

    def setup_method(self):
        """Setup before each benchmark."""
        with patch('noleet.llm.providers.openai_llm.OpenAI') as mock_openai, \
             patch('noleet.llm.providers.ollama_llm.Client') as mock_ollama, \
             patch('noleet.llm.providers.sentence_transformers_embedder.SentenceTransformer') as mock_st:

            # Mock LLM responses
            mock_llm_instance = MagicMock()
            mock_llm_instance.generate_response.return_value = "This is a mock LLM response for benchmarking purposes."
            mock_openai.return_value = mock_llm_instance

            mock_ollama_instance = MagicMock()
            mock_ollama_instance.generate.return_value = "Mock Ollama response."
            mock_ollama.return_value = mock_ollama_instance

            # Mock embedder
            mock_embedder_instance = MagicMock()
            mock_embedder_instance.encode.return_value = [0.1, 0.2, 0.3] * 128  # 384-dimensional embedding
            mock_st.return_value = mock_embedder_instance

            self.factory = LLMFactory(self.mock_config)
            self.embedder = Embedder(self.mock_config)

    def test_llm_factory_creation(self):
        """Benchmark LLM factory creation time."""
        def benchmark():
            factory = LLMFactory(self.mock_config)
            return factory

        self.add_benchmark("llm_factory_creation", benchmark)

    def test_llm_response_generation(self):
        """Benchmark LLM response generation."""
        def benchmark():
            llm = self.factory.get_llm()
            response = llm.generate_response("What is the capital of France?")
            return len(response)

        self.add_benchmark("llm_response_generation", benchmark,
                          prompt_length=30, expected_tokens=50)

    def test_embedder_creation(self):
        """Benchmark embedder creation time."""
        def benchmark():
            embedder = Embedder(self.mock_config)
            return embedder

        self.add_benchmark("embedder_creation", benchmark)

    def test_text_embedding(self):
        """Benchmark text embedding generation."""
        def benchmark():
            embedding = self.embedder.embed_text("This is a test sentence for embedding.")
            return len(embedding)

        self.add_benchmark("text_embedding", benchmark,
                          text_length=50, embedding_dimension=384)

    def test_batch_text_embedding(self):
        """Benchmark batch text embedding."""
        test_texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence with more content.",
            "Fourth sentence for batch processing.",
            "Fifth and final test sentence."
        ]

        def benchmark():
            embeddings = self.embedder.embed_texts(test_texts)
            return len(embeddings), len(embeddings[0]) if embeddings else 0

        self.add_benchmark("batch_text_embedding", benchmark,
                          batch_size=len(test_texts), embedding_dimension=384)

    def test_llm_tokenization_estimate(self):
        """Benchmark token counting estimation."""
        long_text = "This is a very long text that would be tokenized by an LLM. " * 100

        def benchmark():
            # Simulate token counting (rough estimate: 1 token per 4 characters)
            token_count = len(long_text) // 4
            return token_count

        self.add_benchmark("tokenization_estimate", benchmark,
                          text_length=len(long_text), estimated_tokens=len(long_text)//4)


class TestLLMThroughput(BenchmarkSuite):
    """Throughput benchmarks for LLM operations."""

    def __init__(self):
        super().__init__("llm_throughput", "LLM throughput and concurrent operation benchmarks")

    def test_concurrent_llm_calls(self):
        """Benchmark concurrent LLM API calls."""
        import asyncio
        import concurrent.futures

        async def concurrent_benchmark():
            async def single_call(i):
                await asyncio.sleep(0.01)  # Simulate API call
                return f"Response {i}"

            # Simulate 10 concurrent calls
            tasks = [single_call(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return len(results)

        def benchmark():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(concurrent_benchmark())
                return result
            finally:
                loop.close()

        self.add_benchmark("concurrent_llm_calls", benchmark,
                          concurrent_requests=10, simulated_latency=0.01)

    def test_embedding_throughput(self):
        """Benchmark embedding throughput over time."""
        def benchmark():
            profiler = PerformanceProfiler()
            result = profiler.measure_throughput(
                lambda: self.embedder.embed_text("Test text for throughput measurement."),
                duration_seconds=2  # Short duration for testing
            )
            return result['total_operations']

        self.add_benchmark("embedding_throughput", benchmark,
                          duration_seconds=2)


class TestLLMMemoryUsage(BenchmarkSuite):
    """Memory usage benchmarks for LLM operations."""

    def __init__(self):
        super().__init__("llm_memory", "LLM memory usage and leak detection benchmarks")

    def test_llm_memory_usage(self):
        """Benchmark memory usage during LLM operations."""
        def benchmark():
            profiler = PerformanceProfiler()
            result = profiler.profile_memory_usage(
                lambda: self.factory.get_llm().generate_response("Generate a short response.")
            )
            return result['memory_delta']

        self.add_benchmark("llm_memory_usage", benchmark)

    def test_embedding_memory_usage(self):
        """Benchmark memory usage during embedding operations."""
        def benchmark():
            profiler = PerformanceProfiler()
            result = profiler.profile_memory_usage(
                lambda: self.embedder.embed_texts([
                    "First text to embed.",
                    "Second text to embed.",
                    "Third text to embed."
                ])
            )
            return result['memory_delta']

        self.add_benchmark("embedding_memory_usage", benchmark,
                          batch_size=3)

    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated LLM operations."""
        def benchmark():
            profiler = PerformanceProfiler()
            result = profiler.detect_memory_leaks(
                lambda: self.factory.get_llm().generate_response("Short response."),
                iterations=10  # Reduced for testing
            )
            return result['growth_rate_per_iteration']

        self.add_benchmark("memory_leak_detection", benchmark,
                          iterations=10)


# Performance test fixtures
@pytest.fixture
def llm_benchmark_suite():
    """Fixture for LLM performance benchmarks."""
    return TestLLMPerformance()


@pytest.fixture
def llm_throughput_suite():
    """Fixture for LLM throughput benchmarks."""
    return TestLLMThroughput()


@pytest.fixture
def llm_memory_suite():
    """Fixture for LLM memory benchmarks."""
    return TestLLMMemoryUsage()


# Performance test functions
def test_llm_performance_basic(llm_benchmark_suite):
    """Run basic LLM performance benchmarks."""
    results = llm_benchmark_suite.run_all(iterations=1, warmup_iterations=0)

    # Verify results were generated
    assert len(results) > 0
    for result in results:
        assert not result.error
        assert result.metrics.execution_time > 0


def test_llm_throughput(llm_throughput_suite):
    """Run LLM throughput benchmarks."""
    results = llm_throughput_suite.run_all(iterations=1, warmup_iterations=0)

    # Verify results were generated
    assert len(results) > 0
    for result in results:
        assert not result.error


def test_llm_memory_usage(llm_memory_suite):
    """Run LLM memory usage benchmarks."""
    results = llm_memory_suite.run_all(iterations=1, warmup_iterations=0)

    # Verify results were generated
    assert len(results) > 0
    for result in results:
        assert not result.error


# Performance profiling tests
def test_llm_detailed_profiling():
    """Detailed profiling of LLM operations."""
    profiler = PerformanceProfiler()

    # Profile LLM response generation
    with patch('noleet.llm.providers.openai_llm.OpenAI') as mock_openai:
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "Mock response"
        mock_openai.return_value = mock_llm

        config = LLMConfig()
        config.default_llm_provider = "openai"
        factory = LLMFactory(config)

        def llm_operation():
            llm = factory.get_llm()
            return llm.generate_response("Test prompt")

        result = profiler.profile_function(llm_operation)

        assert 'execution_time' in result
        assert 'peak_memory' in result
        assert result['execution_time'] > 0


def test_embedding_throughput_measurement():
    """Test embedding throughput measurement."""
    profiler = PerformanceProfiler()

    with patch('noleet.llm.providers.sentence_transformers_embedder.SentenceTransformer') as mock_st:
        mock_embedder = MagicMock()
        mock_embedder.encode.return_value = [0.1] * 384
        mock_st.return_value = mock_embedder

        config = LLMConfig()
        config.default_embedder_provider = "sentence-transformers"
        embedder = Embedder(config)

        result = profiler.measure_throughput(
            lambda: embedder.embed_text("Test text"),
            duration_seconds=1  # Short duration for testing
        )

        assert result['total_operations'] >= 0
        assert 'operations_per_second' in result
        assert 'average_latency' in result
