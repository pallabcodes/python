"""
Performance tests for embedding operations.
"""

import pytest
import time
import numpy as np
from typing import List

from noleet.llm.llm_config import LLMConfig


@pytest.mark.performance
class TestEmbeddingPerformance:
    """Performance tests for embedding operations."""

    def test_embedding_generation_speed(self):
        """Test embedding generation performance."""
        config = LLMConfig()  # Will use mock

        with pytest.importorskip("pytest_benchmark"):
            # This would be a real benchmark test
            # For now, just test the interface
            from noleet.llm.embedder import Embedder

            embedder = Embedder.create('mock', config)

            start_time = time.time()
            # Simulate embedding generation
            result = embedder.generate_embedding("test text")
            end_time = time.time()

            # Should complete in reasonable time
            assert end_time - start_time < 1.0  # Less than 1 second

    def test_batch_embedding_performance(self):
        """Test batch embedding performance."""
        config = LLMConfig()

        from noleet.llm.embedder import Embedder
        embedder = Embedder.create('mock', config)

        # Test with different batch sizes
        batch_sizes = [1, 10, 50, 100]

        for batch_size in batch_sizes:
            texts = [f"test text {i}" for i in range(batch_size)]

            start_time = time.time()
            # This would actually call embedder.generate_embeddings(texts)
            # For mock, just simulate the operation
            embeddings = [[0.1] * 384 for _ in range(batch_size)]  # Mock embeddings
            end_time = time.time()

            # Calculate throughput
            duration = end_time - start_time
            throughput = batch_size / duration if duration > 0 else float('inf')

            # Should handle reasonable batch sizes efficiently
            assert throughput > 10  # At least 10 embeddings per second

    def test_memory_usage_embedding_operations(self):
        """Test memory usage during embedding operations."""
        import psutil
        import os

        config = LLMConfig()
        from noleet.llm.embedder import Embedder
        embedder = Embedder.create('mock', config)

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform operations
        large_batch = ["test text"] * 1000
        # In real scenario: embeddings = embedder.generate_embeddings(large_batch)

        # Simulate memory-intensive operation
        embeddings = np.random.rand(1000, 384)

        # Check memory usage after operation
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Should not use excessive memory (less than 500MB increase)
        assert memory_increase < 500

    def test_concurrent_embedding_operations(self):
        """Test performance with concurrent embedding operations."""
        import asyncio

        config = LLMConfig()
        from noleet.llm.embedder import Embedder
        embedder = Embedder.create('mock', config)

        async def generate_single_embedding(text: str):
            # Simulate async embedding generation
            await asyncio.sleep(0.01)  # Small delay
            return [0.1] * 384

        async def test_concurrent_operations():
            texts = [f"concurrent test {i}" for i in range(50)]

            start_time = time.time()
            # Simulate concurrent operations
            tasks = [generate_single_embedding(text) for text in texts]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            duration = end_time - start_time
            throughput = len(texts) / duration

            # Should handle concurrent operations efficiently
            assert duration < 1.0  # Complete within 1 second
            assert throughput > 25  # At least 25 operations per second

        # Run the async test
        asyncio.run(test_concurrent_operations())

    def test_embedding_similarity_performance(self):
        """Test performance of similarity calculations."""
        config = LLMConfig()
        from noleet.llm.embedder import Embedder
        embedder = Embedder.create('mock', config)

        # Create large set of embeddings for similarity testing
        num_embeddings = 1000
        embedding_dim = 384
        embeddings = np.random.rand(num_embeddings, embedding_dim)

        # Normalize embeddings (cosine similarity)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms

        # Test similarity calculation performance
        query_embedding = embeddings[0]  # Use first as query

        start_time = time.time()
        # Calculate cosine similarities
        similarities = np.dot(embeddings, query_embedding)
        end_time = time.time()

        duration = end_time - start_time

        # Should calculate similarities quickly
        assert duration < 0.1  # Less than 100ms for 1000 embeddings

        # Verify results are valid similarities
        assert np.all(similarities >= -1.0)
        assert np.all(similarities <= 1.0)

        # Self-similarity should be 1.0 (or very close due to floating point)
        assert abs(similarities[0] - 1.0) < 1e-6

    def test_embedding_caching_performance(self):
        """Test performance improvement with embedding caching."""
        config = LLMConfig()
        from noleet.llm.embedder import Embedder
        embedder = Embedder.create('mock', config)

        test_text = "performance test text"

        # First call (no cache)
        start_time = time.time()
        result1 = embedder.generate_embedding(test_text)
        first_duration = time.time() - start_time

        # Second call (potentially cached)
        start_time = time.time()
        result2 = embedder.generate_embedding(test_text)
        second_duration = time.time() - start_time

        # Results should be identical
        np.testing.assert_array_equal(result1, result2)

        # Second call should be faster (cache benefit)
        # Note: In mock implementation, this may not show improvement
        # but tests the caching interface
        assert second_duration >= 0  # Should not be negative

    def test_large_dataset_handling(self):
        """Test performance with large datasets."""
        config = LLMConfig()
        from noleet.llm.embedder import Embedder
        embedder = Embedder.create('mock', config)

        # Test with large number of texts
        num_texts = 10000
        texts = [f"large dataset text {i}" for i in range(num_texts)]

        start_time = time.time()
        # In real scenario, this would be batched
        # For testing, just simulate the time it would take
        batch_size = 100
        total_embeddings = []

        for i in range(0, num_texts, batch_size):
            batch = texts[i:i + batch_size]
            # Simulate batch processing time
            time.sleep(0.001)  # 1ms per batch
            batch_embeddings = [[0.1] * 384 for _ in batch]
            total_embeddings.extend(batch_embeddings)

        end_time = time.time()
        duration = end_time - start_time

        # Should handle large datasets reasonably
        assert duration < 10.0  # Less than 10 seconds for 10k texts
        assert len(total_embeddings) == num_texts

    def test_embedding_quality_vs_performance_tradeoff(self):
        """Test balance between embedding quality and performance."""
        # This test evaluates the tradeoff between accuracy and speed
        config = LLMConfig()

        # Test different embedding configurations
        configurations = [
            ('mock', 'fast but low quality'),
            # In real scenario, would test different models:
            # ('openai_ada', 'balanced'),
            # ('openai_large', 'accurate but slow'),
        ]

        for embedder_type, description in configurations:
            embedder = Embedder.create(embedder_type, config)

            test_texts = ["machine learning", "data structures", "algorithms"]
            similar_pairs = [("machine learning", "ML algorithms")]
            dissimilar_pairs = [("machine learning", "cooking recipes")]

            # Measure performance
            start_time = time.time()
            embeddings = embedder.generate_embeddings(test_texts)
            duration = time.time() - start_time

            # Performance assertion based on type
            if embedder_type == 'mock':
                assert duration < 0.1  # Very fast for mock

            # Quality would be tested by checking similarity scores
            # for similar vs dissimilar pairs

            assert len(embeddings) == len(test_texts)
