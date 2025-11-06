"""
Platform configuration for MLOps + Gen AI Platform.

Provides centralized configuration management with Pydantic validation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration for metadata and features."""

    type: str = Field(default="sqlite", description="Database type (sqlite, postgres)")
    connection_string: str = Field(default="sqlite:///mlops_platform.db")
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)


class MLflowConfig(BaseModel):
    """MLflow configuration for experiment tracking."""

    tracking_uri: str = Field(default="./mlruns")
    artifact_uri: Optional[str] = None
    registry_uri: Optional[str] = None


class WandbConfig(BaseModel):
    """Weights & Biases configuration."""

    project: str = Field(default="mlops-genai-platform")
    entity: Optional[str] = None
    api_key: Optional[str] = None


class VectorDBConfig(BaseModel):
    """Vector database configuration for RAG."""

    type: str = Field(default="chroma", description="Vector DB type (chroma, pinecone, weaviate)")
    collection: str = Field(default="mlops_genai_kb")
    dimension: int = Field(default=1536, description="Embedding dimension")
    chroma_path: Optional[str] = Field(default="./chroma_db")
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    weaviate_url: Optional[str] = None


class LLMConfig(BaseModel):
    """Large Language Model configuration."""

    model_name: str = Field(default="gpt-3.5-turbo")
    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, huggingface)")
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4096)
    huggingface_model: Optional[str] = Field(default="microsoft/DialoGPT-medium")


class TrainingConfig(BaseModel):
    """Model training configuration."""

    batch_size: int = Field(default=16, ge=1)
    learning_rate: float = Field(default=2e-5, gt=0)
    epochs: int = Field(default=3, ge=1)
    max_seq_length: int = Field(default=512, ge=1)
    save_steps: int = Field(default=500, ge=1)
    eval_steps: int = Field(default=500, ge=1)
    gradient_accumulation_steps: int = Field(default=1, ge=1)


class ServingConfig(BaseModel):
    """Model serving configuration."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)
    gpu_memory_utilization: float = Field(default=0.9, ge=0.1, le=1.0)


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""

    prometheus_port: int = Field(default=9090, ge=1, le=65535)
    enable_tracing: bool = Field(default=True)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    metrics_interval: int = Field(default=30, ge=1, description="Metrics collection interval in seconds")


class PlatformConfig(BaseSettings):
    """Main platform configuration."""

    # Core settings
    project_name: str = Field(default="mlops-genai-platform")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path.cwd())
    models_dir: Path = Field(default_factory=lambda: Path.cwd() / "models")
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
    logs_dir: Path = Field(default_factory=lambda: Path.cwd() / "logs")

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mlflow: MLflowConfig = Field(default_factory=MLflowConfig)
    wandb: WandbConfig = Field(default_factory=WandbConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    serving: ServingConfig = Field(default_factory=ServingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Feature flags
    enable_mlops: bool = Field(default=True)
    enable_genai: bool = Field(default=True)
    enable_rag: bool = Field(default=True)
    enable_agents: bool = Field(default=True)
    enable_monitoring: bool = Field(default=True)

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "MLOPS_"
        case_sensitive = False

    @validator("models_dir", "data_dir", "logs_dir", pre=True, always=True)
    def resolve_paths(cls, v, values):
        """Resolve paths relative to base directory."""
        if isinstance(v, str):
            v = Path(v)
        if not v.is_absolute() and "base_dir" in values:
            v = values["base_dir"] / v
        return v

    @validator("models_dir", "data_dir", "logs_dir")
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    def dict(self, **kwargs):
        """Convert to dictionary with path resolution."""
        d = super().dict(**kwargs)
        # Convert Path objects to strings for serialization
        for key, value in d.items():
            if isinstance(value, Path):
                d[key] = str(value)
        return d


# Global configuration instance
config = PlatformConfig()
