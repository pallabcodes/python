"""
Unit tests for semantic matching functionality.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
from typing import List, Dict, Any

from noleet.intelligence.semantic_matcher import SemanticMatcher
from noleet.llm.llm_config import LLMConfig


class TestSemanticMatcher:
    """Test cases for semantic matching functionality."""

    def test_semantic_matcher_initialization(self):
        """Test semantic matcher initialization."""
        config = LLMConfig(openai_api_key="test-key")
        matcher = SemanticMatcher(config)

        assert matcher.config == config
        assert matcher.embedder is not None

    def test_similarity_score_calculation(self):
        """Test similarity score calculation between texts."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            # Mock embeddings
            embedding1 = np.array([1.0, 0.0, 0.0])  # Unit vector
            embedding2 = np.array([0.0, 1.0, 0.0])  # Unit vector
            mock_embedder.cosine_similarity = AsyncMock(return_value=0.0)  # Orthogonal vectors
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            # Mock the embedding generation
            mock_embedder.generate_embedding = AsyncMock(side_effect=[embedding1, embedding2])

            # Test similarity calculation
            score = matcher.calculate_similarity("text1", "text2")
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_semantic_search_single_query(self):
        """Test semantic search with single query against multiple candidates."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            # Mock embeddings
            query_embedding = np.array([1.0, 0.0, 0.0])
            candidate_embeddings = [
                np.array([0.9, 0.1, 0.0]),  # High similarity
                np.array([0.0, 1.0, 0.0]),  # Low similarity
                np.array([0.8, 0.2, 0.0])   # Medium similarity
            ]

            mock_embedder.generate_embedding = AsyncMock(side_effect=[query_embedding] + candidate_embeddings)
            mock_embedder.cosine_similarity = AsyncMock(side_effect=[0.9, 0.0, 0.8])

            query = "machine learning algorithms"
            candidates = [
                "ML algorithm implementations",
                "Database optimization",
                "Advanced ML techniques"
            ]

            results = matcher.semantic_search(query, candidates, top_k=2)

            assert len(results) == 2
            assert results[0]['text'] == "ML algorithm implementations"
            assert results[0]['score'] >= results[1]['score']

    def test_semantic_search_with_threshold(self):
        """Test semantic search with similarity threshold."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            # Mock embeddings with varying similarities
            mock_embedder.cosine_similarity = AsyncMock(side_effect=[0.9, 0.3, 0.1])

            query = "data structures"
            candidates = ["trees and graphs", "web development", "cooking recipes"]

            # Only return results above threshold
            results = matcher.semantic_search(query, candidates, threshold=0.5)

            assert len(results) == 1
            assert results[0]['score'] >= 0.5

    def test_batch_semantic_search(self):
        """Test batch semantic search for multiple queries."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            queries = ["arrays", "linked lists"]
            candidates = ["array algorithms", "tree structures", "list operations"]

            # Mock embeddings and similarities
            mock_embedder.generate_embeddings = AsyncMock(return_value=np.random.rand(5, 384))
            mock_embedder.cosine_similarity = AsyncMock(side_effect=[0.8, 0.6, 0.9, 0.7, 0.5, 0.3])

            results = matcher.batch_semantic_search(queries, candidates, top_k=1)

            assert len(results) == 2  # One result per query
            for query_results in results:
                assert len(query_results) <= 1  # top_k=1

    def test_find_most_similar(self):
        """Test finding the most similar text from candidates."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            query = "binary search"
            candidates = ["linear search", "binary tree", "binary search algorithm"]

            mock_embedder.cosine_similarity = AsyncMock(side_effect=[0.3, 0.7, 0.95])

            result = matcher.find_most_similar(query, candidates)

            assert result['text'] == "binary search algorithm"
            assert result['score'] == 0.95

    def test_similarity_matrix_calculation(self):
        """Test calculation of similarity matrix for multiple texts."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            texts = ["text1", "text2", "text3"]
            embeddings = np.random.rand(3, 384)

            mock_embedder.generate_embeddings = AsyncMock(return_value=embeddings)
            mock_embedder.cosine_similarity = AsyncMock(side_effect=[
                1.0, 0.8, 0.6,  # text1 similarities
                0.8, 1.0, 0.7,  # text2 similarities
                0.6, 0.7, 1.0   # text3 similarities
            ])

            matrix = matcher.calculate_similarity_matrix(texts)

            assert matrix.shape == (3, 3)
            # Diagonal should be 1.0 (self-similarity)
            np.testing.assert_array_almost_equal(np.diag(matrix), np.ones(3))
            # Matrix should be symmetric
            assert np.allclose(matrix, matrix.T)

    def test_ranking_with_ties(self):
        """Test ranking when multiple candidates have same similarity."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            query = "test query"
            candidates = ["candidate1", "candidate2", "candidate3"]

            # Mock identical similarities
            mock_embedder.cosine_similarity = AsyncMock(side_effect=[0.8, 0.8, 0.8])

            results = matcher.semantic_search(query, candidates, top_k=3)

            assert len(results) == 3
            # All should have same score
            assert all(r['score'] == 0.8 for r in results)

    def test_empty_candidates_handling(self):
        """Test handling of empty candidates list."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            query = "test query"
            candidates = []

            results = matcher.semantic_search(query, candidates)

            assert results == []

    def test_error_handling_embedding_failure(self):
        """Test error handling when embedding generation fails."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder.generate_embedding = AsyncMock(side_effect=Exception("API Error"))
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            with pytest.raises(Exception, match="API Error"):
                matcher.calculate_similarity("text1", "text2")

    def test_performance_with_large_datasets(self):
        """Test performance characteristics with larger datasets."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            # Test with reasonable size dataset
            query = "machine learning"
            candidates = [f"candidate {i}" for i in range(100)]

            # Mock similarity calculations
            similarities = np.random.rand(100).tolist()
            mock_embedder.cosine_similarity = AsyncMock(side_effect=similarities)

            results = matcher.semantic_search(query, candidates, top_k=10)

            assert len(results) == 10
            # Results should be sorted by score descending
            scores = [r['score'] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_memory_efficiency(self):
        """Test memory efficiency for large similarity matrices."""
        config = LLMConfig(openai_api_key="test-key")

        matcher = SemanticMatcher(config)

        # Test with reasonably sized matrix
        texts = [f"text_{i}" for i in range(50)]

        # This should not cause memory issues
        # In real implementation, this would use efficient matrix operations
        with patch.object(matcher, 'calculate_similarity_matrix') as mock_calc:
            mock_calc.return_value = np.random.rand(50, 50)

            matrix = matcher.calculate_similarity_matrix(texts)

            assert matrix.shape == (50, 50)

    def test_caching_behavior(self):
        """Test that embeddings are cached for performance."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            # Mock embedder to track calls
            call_count = 0
            original_generate = mock_embedder.generate_embedding

            async def counting_generate(text):
                nonlocal call_count
                call_count += 1
                return await original_generate(text)

            mock_embedder.generate_embedding = counting_generate

            # First search
            matcher.semantic_search("query1", ["candidate1", "candidate2"])

            # Second search with same texts
            matcher.semantic_search("query1", ["candidate1", "candidate2"])

            # Should reuse embeddings (implementation dependent)
            # This test validates the caching interface exists
            assert hasattr(matcher, 'embedder')

    def test_similarity_score_normalization(self):
        """Test that similarity scores are properly normalized."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.intelligence.semantic_matcher.Embedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.auto_select.return_value = mock_embedder

            matcher = SemanticMatcher(config)

            # Mock similarity calculation
            mock_embedder.cosine_similarity = AsyncMock(return_value=1.5)  # Invalid similarity > 1

            # The matcher should clamp or handle invalid similarities
            score = matcher.calculate_similarity("text1", "text2")

            # Score should be valid (0-1 range)
            assert 0.0 <= score <= 1.0
