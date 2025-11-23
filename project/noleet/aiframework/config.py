"""
Configuration management for AI Framework

Handles all configuration needs:
- Development vs Production modes
- Provider settings
- Batching configuration
- Cost optimization
- Environment-specific overrides
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class Mode(Enum):
    """Framework operating modes."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class ProviderConfig:
    """Configuration for LLM providers."""
    name: str
    api_key_env: str
    base_url: Optional[str] = None
    models: List[str] = field(default_factory=list)
    rate_limit: int = 60  # requests per minute
    cost_per_token: float = 0.0
    quality_score: float = 0.8  # 0.0 to 1.0
    enabled: bool = True

    @property
    def is_available(self) -> bool:
        """Check if provider is available (has API key)."""
        return bool(os.getenv(self.api_key_env))

@dataclass
class BatchingConfig:
    """Configuration for request batching."""
    enabled: bool = True
    max_batch_size: int = 3
    max_wait_time: float = 15.0  # seconds
    strategy: str = "hybrid"  # count, time, or hybrid
    quality_preservation: bool = True
    cost_optimization: bool = True

@dataclass
class InterventionConfig:
    """Configuration for manual intervention."""
    enabled: bool = True
    quality_threshold: float = 0.7  # Trigger intervention below this
    auto_export: bool = True
    export_path: Path = field(default_factory=lambda: Path("./intervention_data"))
    expert_timeout: int = 3600  # 1 hour
    prompt_templates: Dict[str, str] = field(default_factory=dict)

@dataclass
class MonitoringConfig:
    """Configuration for monitoring and analytics."""
    enabled: bool = True
    metrics_retention: int = 30  # days
    cost_alert_threshold: float = 10.0  # dollars
    performance_tracking: bool = True
    log_requests: bool = False  # Set to False for privacy

@dataclass
class FrameworkConfig:
    """
    Main configuration class for AI Framework.

    Automatically adapts based on mode:
    - Development: Mock providers, unlimited usage
    - Production: Real APIs, cost optimization
    - Testing: Deterministic behavior, fast execution
    """

    mode: Mode = Mode.DEVELOPMENT

    # Provider configurations
    providers: Dict[str, ProviderConfig] = field(default_factory=lambda: {
        "gemini": ProviderConfig(
            name="gemini",
            api_key_env="GEMINI_API_KEY",
            models=["gemini-1.5-flash", "gemini-pro"],
            rate_limit=60,
            cost_per_token=0.0,  # Free tier
            quality_score=0.9
        ),
        "together": ProviderConfig(
            name="together",
            api_key_env="TOGETHER_API_KEY",
            models=["mistral-7b", "llama-2-70b"],
            rate_limit=1,  # Limited free tier
            cost_per_token=0.0,
            quality_score=0.85
        ),
        "openai": ProviderConfig(
            name="openai",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-4", "gpt-3.5-turbo"],
            rate_limit=60,
            cost_per_token=0.002,
            quality_score=0.95
        ),
        "ollama": ProviderConfig(
            name="ollama",
            api_key_env="",  # Local, no API key
            models=["llama2", "mistral"],
            rate_limit=1000,  # Local limits
            cost_per_token=0.0,
            quality_score=0.8
        ),
        "mock": ProviderConfig(
            name="mock",
            api_key_env="",  # Always available
            models=["mock-model"],
            rate_limit=1000,
            cost_per_token=0.0,
            quality_score=0.6,
            enabled=True
        )
    })

    # Component configurations
    batching: BatchingConfig = field(default_factory=BatchingConfig)
    intervention: InterventionConfig = field(default_factory=InterventionConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    def __post_init__(self):
        """Apply mode-specific configurations."""
        if self.mode == Mode.DEVELOPMENT:
            self._configure_development()
        elif self.mode == Mode.PRODUCTION:
            self._configure_production()
        elif self.mode == Mode.TESTING:
            self._configure_testing()

    def _configure_development(self):
        """Configure for development mode - unlimited, free, fast."""
        # Enable all providers (mock always available)
        for provider in self.providers.values():
            if provider.name == "mock":
                provider.enabled = True
            # Keep others as-is (will use mock if not available)

        # Optimize batching for development
        self.batching.max_batch_size = 5
        self.batching.max_wait_time = 5.0  # Faster for development

        # Enable monitoring but less strict
        self.monitoring.cost_alert_threshold = 100.0
        self.monitoring.log_requests = False

    def _configure_production(self):
        """Configure for production - cost-optimized, reliable."""
        # Prioritize free/reliable providers
        priority_order = ["gemini", "together", "ollama", "openai", "mock"]

        # Enable batching for cost optimization
        self.batching.enabled = True
        self.batching.max_batch_size = 3
        self.batching.cost_optimization = True

        # Stricter intervention thresholds
        self.intervention.quality_threshold = 0.8

        # Enable all monitoring
        self.monitoring.log_requests = False  # Privacy first
        self.monitoring.cost_alert_threshold = 50.0

    def _configure_testing(self):
        """Configure for testing - deterministic, fast."""
        # Only enable mock provider
        for provider in self.providers.values():
            provider.enabled = (provider.name == "mock")

        # Minimal batching
        self.batching.enabled = False

        # Disable intervention for tests
        self.intervention.enabled = False

        # Disable monitoring for tests
        self.monitoring.enabled = False

    def get_available_providers(self) -> List[ProviderConfig]:
        """Get list of currently available providers."""
        available = []
        for provider in self.providers.values():
            if provider.enabled and provider.is_available:
                available.append(provider)
        return available

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get provider configuration by name."""
        return self.providers.get(name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "mode": self.mode.value,
            "providers": {
                name: {
                    "name": p.name,
                    "available": p.is_available,
                    "rate_limit": p.rate_limit,
                    "cost_per_token": p.cost_per_token,
                    "quality_score": p.quality_score,
                    "enabled": p.enabled
                }
                for name, p in self.providers.items()
            },
            "batching": {
                "enabled": self.batching.enabled,
                "max_batch_size": self.batching.max_batch_size,
                "max_wait_time": self.batching.max_wait_time
            },
            "intervention": {
                "enabled": self.intervention.enabled,
                "quality_threshold": self.intervention.quality_threshold
            }
        }

    @classmethod
    def from_env(cls, mode: Optional[Mode] = None) -> "FrameworkConfig":
        """Create configuration from environment variables."""
        config = cls(mode=mode or Mode.DEVELOPMENT)

        # Override from environment
        if os.getenv("AI_FRAMEWORK_MODE"):
            config.mode = Mode(os.getenv("AI_FRAMEWORK_MODE"))

        # Provider-specific overrides
        for provider_name in config.providers:
            env_prefix = f"AI_{provider_name.upper()}_"
            provider = config.providers[provider_name]

            if os.getenv(f"{env_prefix}RATE_LIMIT"):
                provider.rate_limit = int(os.getenv(f"{env_prefix}RATE_LIMIT"))

            if os.getenv(f"{env_prefix}COST_PER_TOKEN"):
                provider.cost_per_token = float(os.getenv(f"{env_prefix}COST_PER_TOKEN"))

        # Batching overrides
        if os.getenv("AI_BATCH_ENABLED"):
            config.batching.enabled = os.getenv("AI_BATCH_ENABLED").lower() == "true"

        if os.getenv("AI_BATCH_SIZE"):
            config.batching.max_batch_size = int(os.getenv("AI_BATCH_SIZE"))

        return config

    def save_to_file(self, path: Path):
        """Save configuration to file."""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: Path) -> "FrameworkConfig":
        """Load configuration from file."""
        import json
        with open(path, 'r') as f:
            data = json.load(f)

        config = cls(mode=Mode(data["mode"]))

        # Override provider settings
        for provider_name, provider_data in data["providers"].items():
            if provider_name in config.providers:
                provider = config.providers[provider_name]
                for key, value in provider_data.items():
                    if hasattr(provider, key):
                        setattr(provider, key, value)

        return config
