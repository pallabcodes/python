"""Configuration management for orchestrator."""

from typing import Any, Dict, Optional
import logging
import os
from dataclasses import dataclass


@dataclass
class OrchestratorConfig:
    """Configuration for intelligent orchestrator."""

    llm_model: str = "gpt-4"
    enable_learning: bool = True
    enable_explanations: bool = True
    max_workers: int = 4
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Create config from environment variables.

        Returns:
            OrchestratorConfig instance
        """
        return cls(
            llm_model=os.getenv("LLM_MODEL", "gpt-4"),
            enable_learning=os.getenv("ENABLE_LEARNING", "true").lower() == "true",
            enable_explanations=os.getenv("ENABLE_EXPLANATIONS", "true").lower() == "true",
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

