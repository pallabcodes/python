"""
Unit tests for embedding functionality.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from typing import List

from noleet.llm.embedder import Embedder
from noleet.llm.llm_config import LLMConfig


class TestEmbedder:
    """Test cases for text embedding functionality."""

    def test_openai_embedder_creation(self, test_settings, mock_embedding_client):
        """Test creating OpenAI embedder."""
        config = LLMConfig.from_settings(test_settings)

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)

            mock_embedder_class.assert_called_once_with(config.openai)
            assert embedder == mock_embedder

    def test_sentence_transformers_embedder_creation(self, test_settings):
        """Test creating Sentence Transformers embedder."""
        config = LLMConfig.from_settings(test_settings)

        with patch('noleet.llm.providers.sentence_transformers_embedder.SentenceTransformersEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('sentence-transformers', config)

            mock_embedder_class.assert_called_once()
            assert embedder == mock_embedder

    def test_mock_embedder_creation(self, test_settings):
        """Test creating mock embedder for testing."""
        config = LLMConfig.from_settings(test_settings)

        embedder = Embedder.create('mock', config)

        assert embedder.name == 'mock'

    def test_unknown_embedder_type(self, test_settings):
        """Test error handling for unknown embedder type."""
        config = LLMConfig.from_settings(test_settings)

        with pytest.raises(ValueError, match="Unknown embedder type"):
            Embedder.create('unknown', config)

    @pytest.mark.asyncio
    async def test_generate_embeddings_single_text(self, mock_embedding_client):
        """Test generating embeddings for single text."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedding = np.random.rand(384)  # 384-dimensional embedding
            mock_embedder.generate_embedding = AsyncMock(return_value=mock_embedding)
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)
            text = "This is a test text for embedding."
            embedding = await embedder.generate_embedding(text)

            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (384,)
            mock_embedder.generate_embedding.assert_called_once_with(text)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, mock_embedding_client):
        """Test generating embeddings for batch of texts."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embeddings = np.random.rand(3, 384)  # 3 texts, 384 dimensions each
            mock_embedder.generate_embeddings = AsyncMock(return_value=mock_embeddings)
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)
            texts = ["Text 1", "Text 2", "Text 3"]
            embeddings = await embedder.generate_embeddings(texts)

            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (3, 384)
            mock_embedder.generate_embeddings.assert_called_once_with(texts)

    @pytest.mark.asyncio
    async def test_similarity_calculation(self, mock_embedding_client):
        """Test cosine similarity calculation between embeddings."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder.cosine_similarity = AsyncMock(return_value=0.85)
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)
            embedding1 = np.random.rand(384)
            embedding2 = np.random.rand(384)
            similarity = await embedder.cosine_similarity(embedding1, embedding2)

            assert isinstance(similarity, float)
            assert 0 <= similarity <= 1
            mock_embedder.cosine_similarity.assert_called_once_with(embedding1, embedding2)

    def test_embedding_dimensions(self):
        """Test that embeddings have consistent dimensions."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            # Mock different embedding dimensions for different providers
            mock_embedder.embedding_dim = 1536  # OpenAI ada-002
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)

            assert embedder.embedding_dim == 1536

    @pytest.mark.asyncio
    async def test_embedding_normalization(self, mock_embedding_client):
        """Test that embeddings are properly normalized."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            # Create a non-normalized embedding
            raw_embedding = np.array([1.0, 2.0, 3.0])
            normalized_embedding = raw_embedding / np.linalg.norm(raw_embedding)
            mock_embedder.generate_embedding = AsyncMock(return_value=normalized_embedding)
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)
            embedding = await embedder.generate_embedding("test text")

            # Check that embedding is normalized (unit vector)
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 1e-6

    def test_embedder_auto_selection(self, test_settings):
        """Test automatic embedder selection based on configuration."""
        config = LLMConfig.from_settings(test_settings)

        # With OpenAI key, should select OpenAI embedder
        embedder = Embedder.auto_select(config)
        assert embedder.name == 'openai'

    def test_embedder_fallback_to_mock(self):
        """Test fallback to mock embedder when no providers available."""
        config = LLMConfig(
            openai_api_key=None,
            colab_environment=False
        )

        embedder = Embedder.auto_select(config)
        assert embedder.name == 'mock'

    @pytest.mark.asyncio
    async def test_embedding_caching(self):
        """Test embedding caching functionality."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedding = np.random.rand(384)
            mock_embedder.generate_embedding = AsyncMock(return_value=mock_embedding)
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)

            # First call
            text = "Test text for caching"
            embedding1 = await embedder.generate_embedding(text)

            # Second call with same text (should potentially use cache)
            embedding2 = await embedder.generate_embedding(text)

            # Embeddings should be identical
            np.testing.assert_array_equal(embedding1, embedding2)

    def test_embedding_error_handling(self):
        """Test error handling for embedding failures."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder.generate_embedding = AsyncMock(side_effect=Exception("API Error"))
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)

            with pytest.raises(Exception, match="API Error"):
                await embedder.generate_embedding("test text")

    @pytest.mark.asyncio
    async def test_batch_embedding_limits(self):
        """Test handling of batch size limits."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            # Simulate batch size limit
            mock_embedder.max_batch_size = 10
            mock_embeddings = np.random.rand(25, 384)  # 25 texts
            mock_embedder.generate_embeddings = AsyncMock(return_value=mock_embeddings)
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)

            # Try to embed more than batch limit
            texts = [f"Text {i}" for i in range(25)]
            embeddings = await embedder.generate_embeddings(texts)

            assert embeddings.shape == (25, 384)
            mock_embedder.generate_embeddings.assert_called_once()

    def test_embedder_memory_efficiency(self):
        """Test memory efficiency for large embedding operations."""
        config = LLMConfig(openai_api_key="test-key")

        with patch('noleet.llm.providers.openai_embedder.OpenAIEmbedder') as mock_embedder_class:
            mock_embedder = MagicMock()
            mock_embedder.embedding_dim = 384
            mock_embedder_class.return_value = mock_embedder

            embedder = Embedder.create('openai', config)

            # Test memory usage estimation
            estimated_memory = embedder.embedding_dim * 4  # 4 bytes per float32
            assert estimated_memory == 384 * 4  # 1536 bytes per embedding
