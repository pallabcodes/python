"""Factory for creating LLM instances with multi-provider support."""

import logging
from typing import Optional, Any, Dict
from .llm_base import LLMBase, EmbedderBase
from .llm_config import LLMConfig
from .provider_router import ProviderRouter, QualityRequirement


class LLMFactory:
    """Factory for creating LLM and embedder instances."""

    def __init__(
        self,
        config: LLMConfig,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize LLM factory.

        Args:
            config: LLM configuration
            logger: Optional logger instance
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._llm_cache: Dict[str, LLMBase] = {}
        self._embedder_cache: Optional[EmbedderBase] = None
        self._router: Optional[ProviderRouter] = None
        self._providers: Dict[str, LLMBase] = {}

        # Initialize multi-provider support
        self._initialize_multi_provider_support()

    def _initialize_multi_provider_support(self):
        """Initialize multi-provider support with free API providers."""
        # Always initialize basic providers first
        self._initialize_basic_providers()

        # Initialize free API providers if keys are available
        self._initialize_free_providers()

        # Create router if we have multiple providers
        if len(self._providers) > 1:
            self._router = ProviderRouter(self._providers, self._logger)
            self._logger.info(f"Multi-provider routing enabled with {len(self._providers)} providers")
        else:
            self._logger.info("Single provider mode (upgrade to multi-provider by adding more API keys)")

    def _initialize_basic_providers(self):
        """Initialize basic providers (OpenAI, Ollama, Mock)."""
        # OpenAI
        if self._config.openai_api_key:
            try:
                llm = self._create_openai_llm()
                if llm.is_available():
                    self._providers["openai"] = llm
                    self._logger.info("✅ OpenAI provider available")
                else:
                    self._logger.warning("❌ OpenAI provider configured but not available")
            except Exception as e:
                self._logger.warning(f"Failed to initialize OpenAI: {e}")

        # Ollama
        try:
            llm = self._create_ollama_llm()
            if llm.is_available():
                self._providers["ollama"] = llm
                self._logger.info("✅ Ollama provider available")
            else:
                self._logger.info("ℹ️ Ollama provider not available (start Ollama service)")
        except Exception as e:
            self._logger.warning(f"Failed to initialize Ollama: {e}")

        # Mock (always available)
        try:
            llm = self._create_mock_llm()
            self._providers["mock"] = llm
            self._logger.info("✅ Mock provider available")
        except Exception as e:
            self._logger.warning(f"Failed to initialize Mock: {e}")

    def _initialize_free_providers(self):
        """Initialize free API providers."""
        # Google Gemini
        gemini_key = getattr(self._config, 'gemini_api_key', None)
        if gemini_key:
            try:
                from .providers.gemini_provider import GeminiProvider
                gemini_llm = GeminiProvider(
                    api_key=gemini_key,
                    model=getattr(self._config, 'gemini_model', 'gemini-1.5-flash'),
                    logger=self._logger
                )
                if gemini_llm.is_available():
                    self._providers["gemini"] = gemini_llm
                    self._logger.info("✅ Gemini provider available (FREE: 60 RPM)")
                else:
                    self._logger.warning("❌ Gemini provider configured but not available")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Gemini: {e}")

        # Together AI
        together_key = getattr(self._config, 'together_api_key', None)
        if together_key:
            try:
                from .providers.together_provider import TogetherProvider
                together_llm = TogetherProvider(
                    api_key=together_key,
                    model=getattr(self._config, 'together_model', 'mistralai/Mixtral-8x7B-Instruct-v0.1'),
                    logger=self._logger
                )
                if together_llm.is_available():
                    self._providers["together"] = together_llm
                    self._logger.info("✅ Together AI provider available (FREE: 1 RPM)")
                else:
                    self._logger.warning("❌ Together AI provider configured but not available")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Together AI: {e}")

        # Future: Hugging Face, Replicate, etc.
        # These can be added as more free providers become available

    def create_llm(
        self,
        provider: Optional[str] = None,
        quality_requirement: QualityRequirement = QualityRequirement.STANDARD
    ) -> LLMBase:
        """
        Create LLM instance with intelligent multi-provider routing.

        Args:
            provider: Specific provider to use (optional, overrides routing)
            quality_requirement: Quality level for intelligent routing

        Returns:
            LLM instance
        """
        # If specific provider requested, use it
        if provider:
            # Check cache first
            if provider in self._llm_cache:
                llm = self._llm_cache[provider]
                if llm.is_available():
                    return llm

            # Create new instance
            llm = self._create_llm_instance(provider)

            # Test availability
            if llm.is_available():
                self._llm_cache[provider] = llm
                return llm

            # Try fallback if enabled
            if self._config.enable_fallback and provider != self._config.fallback_provider:
                self._logger.warning(
                    f"LLM provider {provider} not available, trying fallback"
                )
                return self.create_llm(self._config.fallback_provider)

            # Return the instance anyway (might be mock)
            return llm

        # Use intelligent multi-provider routing
        if self._router and len(self._providers) > 1:
            return MultiProviderLLM(self._router, quality_requirement, self._logger)

        # Single provider mode - use primary provider
        primary_provider = self._config.primary_provider
        if primary_provider in self._providers:
            return self._providers[primary_provider]

        # Fallback to first available provider
        if self._providers:
            first_provider = list(self._providers.keys())[0]
            return self._providers[first_provider]

        # Last resort: mock provider
        return self._create_mock_llm()

    def _create_llm_instance(self, provider: str) -> LLMBase:
        """Create LLM instance for specific provider."""
        try:
            if provider == "openai":
                return self._create_openai_llm()
            elif provider == "ollama":
                return self._create_ollama_llm()
            elif provider == "mock":
                return self._create_mock_llm()
            else:
                raise ValueError(f"Unknown LLM provider: {provider}")
        except Exception as e:
            self._logger.error(f"Failed to create LLM for {provider}: {e}")
            return self._create_mock_llm()

    def _create_openai_llm(self) -> LLMBase:
        """Create OpenAI LLM instance."""
        from .providers.openai_llm import OpenAILLM
        config = self._config.get_provider_config("openai")
        return OpenAILLM(
            api_key=config.get("api_key"),
            model=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.1),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 30),
            logger=self._logger
        )

    def _create_ollama_llm(self) -> LLMBase:
        """Create Ollama LLM instance."""
        from .providers.ollama_llm import OllamaLLM
        config = self._config.get_provider_config("ollama")
        return OllamaLLM(
            base_url=config.get("base_url", "http://localhost:11434"),
            model=config.get("model", "llama2"),
            temperature=config.get("temperature", 0.1),
            timeout=config.get("timeout", 60),
            logger=self._logger
        )

    def _create_mock_llm(self) -> LLMBase:
        """Create mock LLM instance for testing."""
        from .providers.mock_llm import MockLLM
        return MockLLM(
            model_name="mock-llm",
            logger=self._logger
        )

    def create_embedder(self, provider: Optional[str] = None) -> EmbedderBase:
        """
        Create embedder instance.

        Args:
            provider: Specific embedder provider to use

        Returns:
            Embedder instance
        """
        provider = provider or self._config.embedding_provider

        # Check cache first
        if self._embedder_cache and self._embedder_cache.is_available():
            return self._embedder_cache

        # Create new instance
        embedder = self._create_embedder_instance(provider)

        if embedder.is_available():
            self._embedder_cache = embedder
            return embedder

        # Fallback to mock
        return self._create_mock_embedder()

    def _create_embedder_instance(self, provider: str) -> EmbedderBase:
        """Create embedder instance for specific provider."""
        try:
            if provider == "openai":
                return self._create_openai_embedder()
            elif provider == "sentence-transformers":
                return self._create_sentence_transformers_embedder()
            elif provider == "mock":
                return self._create_mock_embedder()
            else:
                raise ValueError(f"Unknown embedder provider: {provider}")
        except Exception as e:
            self._logger.error(f"Failed to create embedder for {provider}: {e}")
            return self._create_mock_embedder()

    def _create_openai_embedder(self) -> EmbedderBase:
        """Create OpenAI embedder instance."""
        from .providers.openai_embedder import OpenAIEmbedder
        config = self._config.get_provider_config("openai")
        return OpenAIEmbedder(
            api_key=config.get("api_key"),
            model=self._config.embedding_model,
            logger=self._logger
        )

    def _create_sentence_transformers_embedder(self) -> EmbedderBase:
        """Create sentence-transformers embedder instance."""
        from .providers.sentence_transformers_embedder import SentenceTransformersEmbedder
        config = self._config.get_provider_config("sentence-transformers")
        return SentenceTransformersEmbedder(
            model_name=config.get("model_name", "all-MiniLM-L6-v2"),
            device=config.get("device", "cpu"),
            logger=self._logger
        )

    def _create_mock_embedder(self) -> EmbedderBase:
        """Create mock embedder instance."""
        from .providers.mock_embedder import MockEmbedder
        return MockEmbedder(
            model_name="mock-embedder",
            logger=self._logger
        )

    def get_available_providers(self) -> Dict[str, Any]:
        """
        Check which providers are available with detailed information.

        Returns:
            Dictionary with provider availability and routing information
        """
        providers = {}

        # Check all initialized providers
        for name, provider in self._providers.items():
            try:
                info = provider.get_provider_info() if hasattr(provider, 'get_provider_info') else {}
                providers[name] = {
                    "available": provider.is_available(),
                    "info": info
                }
            except Exception as e:
                providers[name] = {
                    "available": False,
                    "error": str(e)
                }

        # Add routing information
        result = {
            "providers": providers,
            "multi_provider_enabled": self._router is not None,
            "total_available": sum(1 for p in providers.values() if p["available"]),
            "routing_stats": self._router.get_routing_statistics() if self._router else None,
            "routing_recommendations": {}
        }

        # Add routing recommendations
        if self._router:
            for quality in QualityRequirement:
                recommended = self._router.get_provider_recommendation(quality)
                result["routing_recommendations"][quality.name] = recommended

        return result

    def _test_ollama_availability(self) -> bool:
        """Test if Ollama is available."""
        try:
            import requests
            response = requests.get(
                f"{self._config.ollama_base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False


class MultiProviderLLM(LLMBase):
    """LLM wrapper that uses provider router for intelligent selection."""

    def __init__(
        self,
        router: ProviderRouter,
        quality_requirement: QualityRequirement,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize multi-provider LLM.

        Args:
            router: Provider router instance
            quality_requirement: Quality requirement for routing
            logger: Optional logger
        """
        self._router = router
        self._quality_requirement = quality_requirement
        self._logger = logger or logging.getLogger(__name__)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using intelligent provider selection.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        try:
            response, provider_used = self._router.generate_with_fallback(
                prompt=prompt,
                quality_requirement=self._quality_requirement,
                **kwargs
            )

            self._logger.info(f"Generated response using {provider_used} (quality: {self._quality_requirement.name})")
            return response

        except Exception as e:
            self._logger.error(f"All providers failed: {e}")
            # Return a helpful error message
            return f"I apologize, but I'm currently unable to generate a response due to service limitations. Please try again later or consider using manual expert review for this request."

    def is_available(self) -> bool:
        """Check if any provider is available."""
        return len(self._router.get_available_providers()) > 0

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the multi-provider setup."""
        return {
            "type": "multi_provider",
            "quality_requirement": self._quality_requirement.name,
            "available_providers": self._router.get_available_providers(),
            "routing_stats": self._router.get_routing_statistics()
        }

