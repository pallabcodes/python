"""
Unit tests for LLM factory functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from noleet.llm.llm_factory import LLMFactory
from noleet.llm.llm_config import LLMConfig
from noleet.llm.providers.mock_llm import MockLLMProvider


class TestLLMFactory:
    """Test cases for LLM factory."""

    def test_create_openai_provider(self, test_settings):
        """Test creating OpenAI provider."""
        config = LLMConfig.from_settings(test_settings)

        with patch('noleet.llm.providers.openai_llm.OpenAILLMProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            provider = LLMFactory.create_provider('openai', config)

            mock_provider_class.assert_called_once_with(config.openai)
            assert provider == mock_provider

    def test_create_ollama_provider(self, test_settings):
        """Test creating Ollama provider."""
        config = LLMConfig.from_settings(test_settings)

        with patch('noleet.llm.providers.ollama_provider.OllamaLLMProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            provider = LLMFactory.create_provider('ollama', config)

            mock_provider_class.assert_called_once_with(config.ollama)
            assert provider == mock_provider

    def test_create_gemini_provider(self, test_settings):
        """Test creating Gemini provider."""
        config = LLMConfig.from_settings(test_settings)

        with patch('noleet.llm.providers.gemini_provider.GeminiLLMProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            provider = LLMFactory.create_provider('gemini', config)

            mock_provider_class.assert_called_once_with(config.gemini)
            assert provider == mock_provider

    def test_create_mock_provider(self, test_settings):
        """Test creating mock provider for testing."""
        config = LLMConfig.from_settings(test_settings)

        provider = LLMFactory.create_provider('mock', config)

        assert isinstance(provider, MockLLMProvider)

    def test_create_unknown_provider(self, test_settings):
        """Test error handling for unknown provider."""
        config = LLMConfig.from_settings(test_settings)

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMFactory.create_provider('unknown', config)

    def test_get_available_providers(self, test_settings):
        """Test getting list of available providers."""
        config = LLMConfig.from_settings(test_settings)

        providers = LLMFactory.get_available_providers(config)

        expected_providers = ['openai', 'ollama', 'gemini', 'together', 'mock']
        assert set(providers) == set(expected_providers)

    def test_auto_select_provider_with_openai(self, test_settings):
        """Test auto-selection with OpenAI available."""
        config = LLMConfig.from_settings(test_settings)

        provider = LLMFactory.auto_select_provider(config)

        assert provider.name == 'openai'

    def test_auto_select_provider_fallback_to_mock(self):
        """Test auto-selection fallback to mock when no providers available."""
        # Create config with no API keys
        config = LLMConfig(
            openai_api_key=None,
            ollama_base_url=None,
            gemini_api_key=None,
            together_api_key=None,
            colab_environment=False
        )

        provider = LLMFactory.auto_select_provider(config)

        assert provider.name == 'mock'

    @pytest.mark.asyncio
    async def test_provider_health_check(self, mock_llm_client):
        """Test provider health check functionality."""
        config = LLMConfig.from_settings(test_settings)

        with patch('noleet.llm.providers.openai_llm.OpenAILLMProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.health_check = AsyncMock(return_value=True)
            mock_provider_class.return_value = mock_provider

            provider = LLMFactory.create_provider('openai', config)
            health = await provider.health_check()

            assert health is True
            mock_provider.health_check.assert_called_once()

    def test_provider_creation_with_colab_detection(self):
        """Test provider creation considers Colab environment."""
        # Mock Colab environment
        with patch('noleet.llm.llm_config.is_running_in_colab', return_value=True):
            config = LLMConfig(
                openai_api_key="test-key",
                colab_environment=True
            )

            provider = LLMFactory.auto_select_provider(config)

            # Should still prefer OpenAI even in Colab
            assert provider.name == 'openai'

    def test_provider_fallback_chain(self):
        """Test provider fallback chain when primary fails."""
        config = LLMConfig(
            openai_api_key=None,  # No OpenAI
            ollama_base_url="http://localhost:11434",  # Has Ollama
            gemini_api_key=None,
            together_api_key=None,
            colab_environment=False
        )

        provider = LLMFactory.auto_select_provider(config)

        assert provider.name == 'ollama'
