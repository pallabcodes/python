"""
Integration Tests for C++ Bindings Performance Module.

Tests the integration between Python and C++ implementations,
including fallback mechanisms and performance validation.
"""

import asyncio
import time
from typing import List
import pytest

# Import the performance module
try:
    from examples.performance.cpp_bindings import (
        CppPerformanceModule,
        VectorOperations,
        TokenizationEngine
    )
except ImportError:
    pytest.skip("C++ bindings module not available", allow_module_level=True)


class TestCppBindingsIntegration:
    """Integration tests for C++ bindings."""

    @pytest.fixture
    def performance_module(self):
        """Fixture for C++ performance module."""
        return CppPerformanceModule()

    @pytest.fixture
    def vector_ops(self):
        """Fixture for vector operations."""
        return VectorOperations()

    @pytest.fixture
    def tokenizer(self):
        """Fixture for tokenization engine."""
        return TokenizationEngine()

    def test_module_initialization(self, performance_module):
        """Test that the module initializes correctly."""
        assert performance_module is not None
        assert hasattr(performance_module, 'vector_ops')
        assert hasattr(performance_module, 'tokenizer')
        assert hasattr(performance_module, 'is_cpp_available')

    def test_vector_operations_integration(self, vector_ops):
        """Test vector operations work correctly."""
        vec_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        vec_b = [2.0, 3.0, 4.0, 5.0, 6.0]

        # Test dot product
        dot_result = vector_ops.dot_product(vec_a, vec_b)
        assert isinstance(dot_result, float)
        assert dot_result > 0

        # Test cosine similarity
        cos_result = vector_ops.cosine_similarity(vec_a, vec_b)
        assert isinstance(cos_result, float)
        assert -1 <= cos_result <= 1

        # Test normalization
        normalized = vector_ops.normalize(vec_a)
        assert len(normalized) == len(vec_a)
        assert all(isinstance(x, float) for x in normalized)

        # Verify normalization (approximately unit length)
        import math
        magnitude = math.sqrt(sum(x * x for x in normalized))
        assert abs(magnitude - 1.0) < 0.01

    def test_tokenization_integration(self, tokenizer):
        """Test tokenization engine works correctly."""
        text = "Hello world this is a test"
        tokens = tokenizer.tokenize(text)
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, int) for t in tokens)

        # Test detokenization
        detokenized = tokenizer.detokenize(tokens)
        assert isinstance(detokenized, str)
        assert len(detokenized) > 0

        # Test with max tokens
        limited_tokens = tokenizer.tokenize(text, max_tokens=3)
        assert len(limited_tokens) <= 3

    def test_fallback_mechanisms(self, vector_ops):
        """Test that fallback to Python/NumPy works when C++ is unavailable."""
        # This should work regardless of C++ availability
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [4.0, 5.0, 6.0]

        result = vector_ops.dot_product(vec_a, vec_b)
        assert isinstance(result, float)

        # Test with larger vectors for performance
        large_vec_a = [float(i) for i in range(1000)]
        large_vec_b = [float(i * 2) for i in range(1000)]

        start_time = time.time()
        large_result = vector_ops.dot_product(large_vec_a, large_vec_b)
        end_time = time.time()

        assert isinstance(large_result, float)
        assert large_result > 0

        # Should complete in reasonable time
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should be fast even with Python fallback

    def test_performance_module_benchmarking(self, performance_module):
        """Test that benchmarking works correctly."""
        results = performance_module.benchmark(iterations=10)
        assert isinstance(results, dict)
        assert len(results) > 0

        # Check that all expected operations are benchmarked
        expected_ops = ['dot_product', 'cosine_similarity', 'tokenization']
        for op in expected_ops:
            assert op in results
            assert isinstance(results[op], float)
            assert results[op] > 0

    def test_error_handling(self, vector_ops):
        """Test error handling for invalid inputs."""
        # Test mismatched vector lengths
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [1.0, 2.0]  # Different length

        with pytest.raises(ValueError):
            vector_ops.dot_product(vec_a, vec_b)

        with pytest.raises(ValueError):
            vector_ops.cosine_similarity(vec_a, vec_b)

    def test_memory_efficiency(self, vector_ops):
        """Test memory efficiency with large vectors."""
        # Test with reasonably large vectors
        size = 10000
        large_vec_a = [float(i % 100) for i in range(size)]
        large_vec_b = [float((i + 1) % 100) for i in range(size)]

        # Should not crash or take excessive memory
        result = vector_ops.dot_product(large_vec_a, large_vec_b)
        assert isinstance(result, float)

        # Test normalization on large vector
        normalized = vector_ops.normalize(large_vec_a)
        assert len(normalized) == size
        assert all(isinstance(x, float) for x in normalized)

    @pytest.mark.asyncio
    async def test_async_compatibility(self, performance_module):
        """Test that the module works in async contexts."""
        # This should work fine in async functions
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [4.0, 5.0, 6.0]

        result = performance_module.vector_ops.dot_product(vec_a, vec_b)
        assert isinstance(result, float)

        # Test tokenization in async context
        text = "async test text"
        tokens = performance_module.tokenizer.tokenize(text)
        assert isinstance(tokens, list)


class TestCppBindingsStress:
    """Stress tests for C++ bindings."""

    def test_high_frequency_operations(self, vector_ops):
        """Test high-frequency vector operations."""
        vec_a = [1.0, 2.0, 3.0, 4.0, 5.0]
        vec_b = [2.0, 3.0, 4.0, 5.0, 6.0]

        # Perform many operations quickly
        for i in range(1000):
            result = vector_ops.dot_product(vec_a, vec_b)
            assert isinstance(result, float)

            # Modify vectors slightly for variation
            vec_a[0] = float(i % 10 + 1)

    def test_large_scale_tokenization(self, tokenizer):
        """Test tokenization with large texts."""
        # Create large text
        words = ["word"] * 1000
        large_text = " ".join(words)

        start_time = time.time()
        tokens = tokenizer.tokenize(large_text)
        end_time = time.time()

        assert isinstance(tokens, list)
        assert len(tokens) > 0

        # Should complete reasonably quickly
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should be fast even with large text

    def test_concurrent_operations(self, vector_ops):
        """Test concurrent vector operations."""
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def worker(worker_id):
            try:
                vec_a = [float(i + worker_id) for i in range(10)]
                vec_b = [float(i * 2) for i in range(10)]

                result = vector_ops.dot_product(vec_a, vec_b)
                results.put((worker_id, result))
            except Exception as e:
                errors.put((worker_id, str(e)))

        # Start multiple threads
        threads = []
        num_threads = 10

        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check results
        assert results.qsize() == num_threads
        assert errors.qsize() == 0

        # Verify all results are valid
        while not results.empty():
            worker_id, result = results.get()
            assert isinstance(result, float)
            assert result >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])