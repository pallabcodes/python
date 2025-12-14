"""
Unit tests for configuration management.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from noleet.app.core.config import Settings, get_settings
from noleet.llm.llm_config import LLMConfig


class TestSettings:
    """Test cases for application settings."""

    def test_default_settings_creation(self):
        """Test creating settings with default values."""
        settings = Settings()

        assert settings.debug is False
        assert settings.environment == "production"
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0

    def test_settings_with_env_vars(self):
        """Test settings with environment variables."""
        env_vars = {
            "DEBUG": "True",
            "ENVIRONMENT": "testing",
            "SECRET_KEY": "test-secret-key",
            "DATABASE_URL": "postgresql://test:test@localhost/testdb",
            "OPENAI_API_KEY": "test-openai-key",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "JWT_SECRET_KEY": "test-jwt-secret"
        }

        with patch.dict(os.environ, env_vars):
            settings = Settings()

            assert settings.debug is True
            assert settings.environment == "testing"
            assert settings.secret_key == "test-secret-key"
            assert settings.database_url == "postgresql://test:test@localhost/testdb"
            assert settings.openai_api_key == "test-openai-key"
            assert settings.ollama_base_url == "http://localhost:11434"
            assert settings.jwt_secret_key == "test-jwt-secret"

    def test_database_url_validation(self):
        """Test database URL validation."""
        # Valid URLs
        valid_urls = [
            "postgresql://user:pass@localhost/db",
            "mysql://user:pass@localhost/db",
            "sqlite:///app.db",
            "sqlite:///:memory:"
        ]

        for url in valid_urls:
            with patch.dict(os.environ, {"DATABASE_URL": url}):
                settings = Settings()
                assert settings.database_url == url

    def test_jwt_secret_validation(self):
        """Test JWT secret key validation."""
        # Should generate a secret if not provided
        settings = Settings()
        assert settings.jwt_secret_key is not None
        assert len(settings.jwt_secret_key) >= 32  # Should be sufficiently long

        # Should use provided secret
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "custom-jwt-secret"}):
            settings = Settings()
            assert settings.jwt_secret_key == "custom-jwt-secret"

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from environment."""
        # Single origin
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000"}):
            settings = Settings()
            assert settings.cors_origins == ["http://localhost:3000"]

        # Multiple origins
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,https://app.example.com"}):
            settings = Settings()
            expected = ["http://localhost:3000", "https://app.example.com"]
            assert settings.cors_origins == expected

    def test_environment_validation(self):
        """Test environment validation."""
        valid_environments = ["development", "testing", "staging", "production"]

        for env in valid_environments:
            with patch.dict(os.environ, {"ENVIRONMENT": env}):
                settings = Settings()
                assert settings.environment == env

        # Invalid environment should raise error
        with patch.dict(os.environ, {"ENVIRONMENT": "invalid"}):
            with pytest.raises(ValueError):
                Settings()

    def test_api_key_validation(self):
        """Test API key presence validation."""
        # Should work without API keys (fallback to mock)
        settings = Settings()
        assert settings.openai_api_key is None  # Can be None, will use mock

        # Should accept provided keys
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            settings = Settings()
            assert settings.openai_api_key == "sk-test-key"

    def test_settings_immutability(self):
        """Test that settings are immutable after creation."""
        settings = Settings()

        # Should not be able to modify settings
        with pytest.raises(Exception):  # pydantic.BaseModel prevents modification
            settings.debug = True

    def test_settings_singleton_pattern(self):
        """Test settings singleton behavior."""
        # Test get_settings function
        with patch('noleet.app.core.config.settings', None):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should return the same instance
            assert settings1 is settings2


class TestLLMConfig:
    """Test cases for LLM configuration."""

    def test_llm_config_from_settings(self, test_settings):
        """Test creating LLM config from settings."""
        llm_config = LLMConfig.from_settings(test_settings)

        assert llm_config.openai_api_key == test_settings.openai_api_key
        assert llm_config.ollama_base_url == test_settings.ollama_base_url
        assert llm_config.colab_environment == test_settings.colab_environment

    def test_llm_config_validation(self):
        """Test LLM configuration validation."""
        # Valid config
        config = LLMConfig(
            openai_api_key="sk-test",
            ollama_base_url="http://localhost:11434",
            colab_environment=False
        )
        assert config.openai_api_key == "sk-test"

        # Config without API keys (should work with mock fallback)
        config_minimal = LLMConfig()
        assert config_minimal.openai_api_key is None

    def test_llm_config_colab_detection(self):
        """Test Colab environment detection in LLM config."""
        with patch('noleet.llm.llm_config.is_running_in_colab', return_value=True):
            config = LLMConfig(colab_environment=True)
            assert config.colab_environment is True

        with patch('noleet.llm.llm_config.is_running_in_colab', return_value=False):
            config = LLMConfig(colab_environment=False)
            assert config.colab_environment is False

    def test_llm_config_provider_availability(self):
        """Test provider availability checking."""
        # Config with OpenAI
        config_with_openai = LLMConfig(openai_api_key="sk-test")
        assert config_with_openai.has_openai

        # Config without OpenAI
        config_without_openai = LLMConfig()
        assert not config_without_openai.has_openai

    def test_llm_config_model_selection(self):
        """Test model selection logic."""
        config = LLMConfig(
            openai_api_key="sk-test",
            openai_model="gpt-4-turbo"
        )

        assert config.openai_model == "gpt-4-turbo"

        # Default model
        config_default = LLMConfig(openai_api_key="sk-test")
        assert config_default.openai_model == "gpt-4"  # Default

    def test_llm_config_timeout_settings(self):
        """Test timeout configuration."""
        config = LLMConfig(
            openai_timeout=30.0,
            ollama_timeout=60.0
        )

        assert config.openai_timeout == 30.0
        assert config.ollama_timeout == 60.0

    def test_llm_config_rate_limits(self):
        """Test rate limiting configuration."""
        config = LLMConfig(
            openai_rpm=100,
            openai_tpm=10000
        )

        assert config.openai_rpm == 100
        assert config.openai_tpm == 10000

    def test_llm_config_serialization(self):
        """Test config serialization for logging/debugging."""
        config = LLMConfig(
            openai_api_key="sk-test-key",
            ollama_base_url="http://localhost:11434"
        )

        # Should be serializable (for logging)
        config_dict = config.dict()
        assert "openai_api_key" in config_dict

        # API keys should be masked in serialization
        assert config_dict["openai_api_key"] != "sk-test-key"  # Should be masked

    def test_llm_config_environment_integration(self):
        """Test LLM config with environment variables."""
        env_vars = {
            "OPENAI_API_KEY": "sk-env-key",
            "OLLAMA_BASE_URL": "http://env-host:11434",
            "OPENAI_MODEL": "gpt-4-turbo",
            "OLLAMA_MODEL": "llama2:13b"
        }

        with patch.dict(os.environ, env_vars):
            config = LLMConfig()

            assert config.openai_api_key == "sk-env-key"
            assert config.ollama_base_url == "http://env-host:11434"
            assert config.openai_model == "gpt-4-turbo"
            assert config.ollama_model == "llama2:13b"

    def test_llm_config_fallback_behavior(self):
        """Test fallback behavior when primary providers unavailable."""
        # Config with no providers
        config = LLMConfig()

        # Should still be valid (will use mock provider)
        assert config is not None

        # Should indicate no providers available
        assert not config.has_openai
        assert not config.has_ollama
        assert not config.has_gemini

    def test_llm_config_validation_errors(self):
        """Test configuration validation errors."""
        # Invalid URL
        with pytest.raises(ValueError):
            LLMConfig(ollama_base_url="not-a-url")

        # Invalid timeout
        with pytest.raises(ValueError):
            LLMConfig(openai_timeout=-1)

        # Invalid rate limit
        with pytest.raises(ValueError):
            LLMConfig(openai_rpm=0)

    def test_llm_config_provider_priorities(self):
        """Test provider priority selection."""
        # OpenAI should be preferred when available
        config_with_openai = LLMConfig(openai_api_key="sk-test")
        assert config_with_openai.preferred_provider == "openai"

        # Ollama fallback
        config_with_ollama = LLMConfig(ollama_base_url="http://localhost:11434")
        assert config_with_ollama.preferred_provider == "ollama"

        # Mock as last resort
        config_empty = LLMConfig()
        assert config_empty.preferred_provider == "mock"
