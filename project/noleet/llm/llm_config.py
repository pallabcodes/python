"""Configuration management for LLM integration."""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""

    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 1000
    openai_timeout: int = 30

    # Free API providers
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    together_api_key: Optional[str] = None
    together_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Future free providers
    huggingface_token: Optional[str] = None
    replicate_api_token: Optional[str] = None

    # Ollama (local models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    ollama_temperature: float = 0.1
    ollama_timeout: int = 60

    # Embeddings
    embedding_model: str = "text-embedding-ada-002"  # OpenAI
    embedding_provider: str = "openai"  # openai, local, sentence-transformers

    # Fallback and priorities
    primary_provider: str = "openai"  # openai, ollama, mock
    enable_fallback: bool = True
    fallback_provider: str = "mock"

    # Colab detection and settings
    is_colab: bool = field(init=False)
    colab_gpu_available: bool = field(init=False)

    # Logging
    enable_llm_logging: bool = False
    log_requests: bool = False
    log_responses: bool = False

    def __post_init__(self) -> None:
        """Initialize after dataclass creation."""
        self._detect_environment()
        self._load_credentials()

    def _detect_environment(self) -> None:
        """Detect environment (Colab vs local)."""
        try:
            from ..colab.colab_detector import ColabDetector
            detector = ColabDetector()
            self.is_colab = detector.is_colab()
            colab_info = detector.get_colab_info()
            self.colab_gpu_available = colab_info.get("gpu_available", False)

            # Apply Colab optimizations
            if self.is_colab:
                self._apply_colab_optimizations(colab_info)

        except ImportError:
            # Fallback to basic detection
            self.is_colab = False
            self.colab_gpu_available = False
            self._basic_colab_detection()

    def _basic_colab_detection(self) -> None:
        """Basic Colab detection without colab_detector."""
        try:
            import google.colab
            self.is_colab = True
            self._detect_colab_gpu()
        except ImportError:
            self.is_colab = False
            self.colab_gpu_available = False

    def _detect_colab_gpu(self) -> None:
        """Detect if GPU is available in Colab."""
        try:
            import torch
            self.colab_gpu_available = torch.cuda.is_available()
        except ImportError:
            self.colab_gpu_available = False

    def _apply_colab_optimizations(self, colab_info: Dict[str, Any]) -> None:
        """Apply Colab-specific optimizations based on detected environment."""
        try:
            from ..colab.colab_gpu_utilizer import ColabGPUUtilizer
            gpu_utilizer = ColabGPUUtilizer()

            # Adjust timeouts for Colab internet
            self.openai_timeout = 20
            self.ollama_timeout = 45

            # Set embedding provider based on Colab capabilities
            if gpu_utilizer.is_gpu_available():
                # Prefer local embeddings on GPU
                if colab_info.get("gpu_info", {}).get("memory_gb", 0) > 8:
                    self.embedding_provider = "sentence-transformers"
                else:
                    self.embedding_provider = "openai"  # Fallback to API
            else:
                self.embedding_provider = "openai"

        except ImportError:
            # Fallback to basic Colab config
            self._configure_for_colab()

    def _load_credentials(self) -> None:
        """Load credentials from environment variables."""
        # OpenAI API Key
        self.openai_api_key = (
            os.getenv("OPENAI_API_KEY") or
            self.openai_api_key
        )

        # Free API providers
        self.gemini_api_key = (
            os.getenv("GEMINI_API_KEY") or
            self.gemini_api_key
        )

        self.together_api_key = (
            os.getenv("TOGETHER_API_KEY") or
            self.together_api_key
        )

        self.huggingface_token = (
            os.getenv("HUGGINGFACE_TOKEN") or
            self.huggingface_token
        )

        self.replicate_api_token = (
            os.getenv("REPLICATE_API_TOKEN") or
            self.replicate_api_token
        )

        # Ollama settings
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.ollama_base_url)
        self.ollama_model = os.getenv("OLLAMA_MODEL", self.ollama_model)

        # Adjust settings for Colab
        if self.is_colab:
            self._configure_for_colab()

    def _configure_for_colab(self) -> None:
        """Configure settings for Google Colab environment."""
        # In Colab, prefer API over local models initially
        if not self.openai_api_key:
            self.primary_provider = "ollama" if self.colab_gpu_available else "mock"

        # Colab has good internet, so shorter timeouts are fine
        self.openai_timeout = 20
        self.ollama_timeout = 45

        # Use Colab-compatible embedding models
        if self.embedding_provider == "openai" and not self.openai_api_key:
            self.embedding_provider = "sentence-transformers"

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name (openai, ollama, etc.)

        Returns:
            Provider-specific configuration
        """
        if provider == "openai":
            return {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
                "timeout": self.openai_timeout,
                "request_timeout": self.openai_timeout
            }
        elif provider == "ollama":
            return {
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
                "temperature": self.ollama_temperature,
                "timeout": self.ollama_timeout
            }
        elif provider == "sentence-transformers":
            return {
                "model_name": "all-MiniLM-L6-v2",  # Good balance of speed/quality
                "device": "cuda" if self.colab_gpu_available else "cpu"
            }

        return {}

    def validate_config(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid
        """
        # Check if at least one provider is configured
        providers_available = []

        if self.openai_api_key:
            providers_available.append("openai")

        # Ollama might be available even without explicit config
        providers_available.append("ollama")  # We'll check at runtime

        if not providers_available:
            return False

        return True

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables only."""
        config = cls()
        config._load_credentials()
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (without sensitive data)."""
        return {
            "openai_model": self.openai_model,
            "ollama_model": self.ollama_model,
            "embedding_model": self.embedding_model,
            "embedding_provider": self.embedding_provider,
            "primary_provider": self.primary_provider,
            "enable_fallback": self.enable_fallback,
            "fallback_provider": self.fallback_provider,
            "is_colab": self.is_colab,
            "colab_gpu_available": self.colab_gpu_available,
            "enable_llm_logging": self.enable_llm_logging
        }

