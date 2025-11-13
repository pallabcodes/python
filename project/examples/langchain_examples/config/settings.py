"""Configuration management using Pydantic Settings."""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from pydantic import BaseSettings, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    logger.warning("pydantic not installed, using basic configuration")


if HAS_PYDANTIC:
    class ProductionConfig(BaseSettings):
        """Production configuration with environment variable support."""
        
        # Service configuration
        service_name: str = Field(default="llm_service", env="SERVICE_NAME")
        log_level: str = Field(default="INFO", env="LOG_LEVEL")
        
        # Cache configuration
        cache_size: int = Field(default=1000, env="CACHE_SIZE")
        cache_ttl_seconds: float = Field(default=3600.0, env="CACHE_TTL_SECONDS")
        similarity_threshold: float = Field(default=0.95, env="SIMILARITY_THRESHOLD")
        enable_semantic_cache: bool = Field(default=True, env="ENABLE_SEMANTIC_CACHE")
        
        # Circuit breaker configuration
        enable_circuit_breaker: bool = Field(default=True, env="ENABLE_CIRCUIT_BREAKER")
        circuit_breaker_failure_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
        circuit_breaker_timeout_seconds: float = Field(default=60.0, env="CIRCUIT_BREAKER_TIMEOUT_SECONDS")
        circuit_breaker_success_threshold: int = Field(default=2, env="CIRCUIT_BREAKER_SUCCESS_THRESHOLD")
        
        # Rate limiting configuration
        rate_limit_per_second: float = Field(default=10.0, env="RATE_LIMIT_PER_SECOND")
        rate_limit_capacity: float = Field(default=20.0, env="RATE_LIMIT_CAPACITY")
        
        # Deduplication configuration
        enable_deduplication: bool = Field(default=True, env="ENABLE_DEDUPLICATION")
        deduplication_window_seconds: float = Field(default=60.0, env="DEDUPLICATION_WINDOW_SECONDS")
        
        # Tracing configuration
        enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
        trace_sample_rate: float = Field(default=1.0, env="TRACE_SAMPLE_RATE")
        
        # Batching configuration
        enable_batching: bool = Field(default=False, env="ENABLE_BATCHING")
        max_batch_size: int = Field(default=32, env="MAX_BATCH_SIZE")
        min_batch_size: int = Field(default=1, env="MIN_BATCH_SIZE")
        max_wait_seconds: float = Field(default=0.1, env="MAX_WAIT_SECONDS")
        
        # Connection pool configuration
        connection_pool_min_size: int = Field(default=2, env="CONNECTION_POOL_MIN_SIZE")
        connection_pool_max_size: int = Field(default=10, env="CONNECTION_POOL_MAX_SIZE")
        connection_pool_timeout: float = Field(default=5.0, env="CONNECTION_POOL_TIMEOUT")
        health_check_interval: float = Field(default=30.0, env="HEALTH_CHECK_INTERVAL")
        
        # Prometheus configuration
        enable_prometheus: bool = Field(default=False, env="ENABLE_PROMETHEUS")
        prometheus_port: int = Field(default=8000, env="PROMETHEUS_PORT")
        
        # Error recovery configuration
        enable_fallback_to_cache: bool = Field(default=True, env="ENABLE_FALLBACK_TO_CACHE")
        enable_request_queuing: bool = Field(default=True, env="ENABLE_REQUEST_QUEUING")
        
        # Retry configuration
        max_retries: int = Field(default=3, env="MAX_RETRIES")
        initial_retry_delay: float = Field(default=0.1, env="INITIAL_RETRY_DELAY")
        max_retry_delay: float = Field(default=10.0, env="MAX_RETRY_DELAY")
        retry_exponential_base: float = Field(default=2.0, env="RETRY_EXPONENTIAL_BASE")
        
        class Config:
            """Pydantic configuration."""
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            
            @classmethod
            def customise_sources(cls, init_settings, env_settings, file_secret_settings):
                """Customize settings sources."""
                return (
                    init_settings,
                    env_settings,
                    file_secret_settings,
                )
else:
    # Fallback configuration class without Pydantic
    class ProductionConfig:
        """Basic configuration without Pydantic."""
        
        def __init__(self, **kwargs):
            """Initialize configuration from kwargs or environment."""
            # Service configuration
            self.service_name = kwargs.get("service_name", os.getenv("SERVICE_NAME", "llm_service"))
            self.log_level = kwargs.get("log_level", os.getenv("LOG_LEVEL", "INFO"))
            
            # Cache configuration
            self.cache_size = int(kwargs.get("cache_size", os.getenv("CACHE_SIZE", "1000")))
            self.cache_ttl_seconds = float(kwargs.get("cache_ttl_seconds", os.getenv("CACHE_TTL_SECONDS", "3600.0")))
            self.similarity_threshold = float(kwargs.get("similarity_threshold", os.getenv("SIMILARITY_THRESHOLD", "0.95")))
            self.enable_semantic_cache = kwargs.get("enable_semantic_cache", os.getenv("ENABLE_SEMANTIC_CACHE", "true").lower() == "true")
            
            # Circuit breaker configuration
            self.enable_circuit_breaker = kwargs.get("enable_circuit_breaker", os.getenv("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true")
            self.circuit_breaker_failure_threshold = int(kwargs.get("circuit_breaker_failure_threshold", os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")))
            self.circuit_breaker_timeout_seconds = float(kwargs.get("circuit_breaker_timeout_seconds", os.getenv("CIRCUIT_BREAKER_TIMEOUT_SECONDS", "60.0")))
            self.circuit_breaker_success_threshold = int(kwargs.get("circuit_breaker_success_threshold", os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "2")))
            
            # Rate limiting configuration
            self.rate_limit_per_second = float(kwargs.get("rate_limit_per_second", os.getenv("RATE_LIMIT_PER_SECOND", "10.0")))
            self.rate_limit_capacity = float(kwargs.get("rate_limit_capacity", os.getenv("RATE_LIMIT_CAPACITY", "20.0")))
            
            # Deduplication configuration
            self.enable_deduplication = kwargs.get("enable_deduplication", os.getenv("ENABLE_DEDUPLICATION", "true").lower() == "true")
            self.deduplication_window_seconds = float(kwargs.get("deduplication_window_seconds", os.getenv("DEDUPLICATION_WINDOW_SECONDS", "60.0")))
            
            # Tracing configuration
            self.enable_tracing = kwargs.get("enable_tracing", os.getenv("ENABLE_TRACING", "true").lower() == "true")
            self.trace_sample_rate = float(kwargs.get("trace_sample_rate", os.getenv("TRACE_SAMPLE_RATE", "1.0")))
            
            # Batching configuration
            self.enable_batching = kwargs.get("enable_batching", os.getenv("ENABLE_BATCHING", "false").lower() == "true")
            self.max_batch_size = int(kwargs.get("max_batch_size", os.getenv("MAX_BATCH_SIZE", "32")))
            self.min_batch_size = int(kwargs.get("min_batch_size", os.getenv("MIN_BATCH_SIZE", "1")))
            self.max_wait_seconds = float(kwargs.get("max_wait_seconds", os.getenv("MAX_WAIT_SECONDS", "0.1")))
            
            # Connection pool configuration
            self.connection_pool_min_size = int(kwargs.get("connection_pool_min_size", os.getenv("CONNECTION_POOL_MIN_SIZE", "2")))
            self.connection_pool_max_size = int(kwargs.get("connection_pool_max_size", os.getenv("CONNECTION_POOL_MAX_SIZE", "10")))
            self.connection_pool_timeout = float(kwargs.get("connection_pool_timeout", os.getenv("CONNECTION_POOL_TIMEOUT", "5.0")))
            self.health_check_interval = float(kwargs.get("health_check_interval", os.getenv("HEALTH_CHECK_INTERVAL", "30.0")))
            
            # Prometheus configuration
            self.enable_prometheus = kwargs.get("enable_prometheus", os.getenv("ENABLE_PROMETHEUS", "false").lower() == "true")
            self.prometheus_port = int(kwargs.get("prometheus_port", os.getenv("PROMETHEUS_PORT", "8000")))
            
            # Error recovery configuration
            self.enable_fallback_to_cache = kwargs.get("enable_fallback_to_cache", os.getenv("ENABLE_FALLBACK_TO_CACHE", "true").lower() == "true")
            self.enable_request_queuing = kwargs.get("enable_request_queuing", os.getenv("ENABLE_REQUEST_QUEUING", "true").lower() == "true")
            
            # Retry configuration
            self.max_retries = int(kwargs.get("max_retries", os.getenv("MAX_RETRIES", "3")))
            self.initial_retry_delay = float(kwargs.get("initial_retry_delay", os.getenv("INITIAL_RETRY_DELAY", "0.1")))
            self.max_retry_delay = float(kwargs.get("max_retry_delay", os.getenv("MAX_RETRY_DELAY", "10.0")))
            self.retry_exponential_base = float(kwargs.get("retry_exponential_base", os.getenv("RETRY_EXPONENTIAL_BASE", "2.0")))


def get_config(config_file: Optional[str] = None) -> ProductionConfig:
    """
    Get configuration from environment variables or config file.
    
    Args:
        config_file: Optional path to config file (YAML/JSON)
        
    Returns:
        ProductionConfig instance
    """
    if config_file and Path(config_file).exists():
        # Load from file if provided
        if config_file.endswith(".yaml") or config_file.endswith(".yml"):
            import yaml
            with open(config_file) as f:
                config_dict = yaml.safe_load(f)
            return ProductionConfig(**config_dict)
        elif config_file.endswith(".json"):
            import json
            with open(config_file) as f:
                config_dict = json.load(f)
            return ProductionConfig(**config_dict)
    
    # Load from environment variables
    return ProductionConfig()

