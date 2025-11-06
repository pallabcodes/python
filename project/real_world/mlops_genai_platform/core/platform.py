"""
Main platform orchestrator for MLOps + Gen AI Platform.

Provides unified interface to MLOps and Gen AI capabilities with enterprise-grade
orchestration, monitoring, and deployment management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI
from pydantic import BaseModel

from .config import PlatformConfig


class PlatformStatus(BaseModel):
    """Platform status information."""

    status: str
    version: str
    environment: str
    components: Dict[str, str]
    uptime_seconds: Optional[float] = None


class MLOpsPlatform:
    """
    Main platform orchestrator for MLOps + Gen AI capabilities.

    Features:
    - Unified MLOps infrastructure (training, registry, monitoring)
    - Gen AI capabilities (LLM, RAG, agents)
    - Enterprise orchestration and lifecycle management
    - Production-ready serving and deployment
    """

    def __init__(self, config: Optional[PlatformConfig] = None):
        """
        Initialize the MLOps platform.

        Args:
            config: Platform configuration. If None, uses default config.
        """
        self.config = config or PlatformConfig()
        self.logger = self._setup_logging()

        # Component references (lazy loaded)
        self._mlops_components: Dict[str, Any] = {}
        self._genai_components: Dict[str, Any] = {}
        self._serving_components: Dict[str, Any] = {}
        self._monitoring_components: Dict[str, Any] = {}

        # Platform state
        self._initialized = False
        self._start_time: Optional[float] = None

        self.logger.info(f"Initialized {self.config.project_name} v{self.config.version}")

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging."""
        logger = logging.getLogger(self.config.project_name)
        logger.setLevel(getattr(logging, self.config.monitoring.log_level))

        # Remove existing handlers
        logger.handlers.clear()

        # Console handler with structured format
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # File handler for persistent logs
        log_file = self.config.logs_dir / "platform.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    async def initialize(self) -> None:
        """
        Initialize all platform components.

        This method sets up MLOps infrastructure, Gen AI components,
        monitoring, and serving capabilities.
        """
        if self._initialized:
            self.logger.warning("Platform already initialized")
            return

        self.logger.info("Initializing MLOps + Gen AI Platform...")

        try:
            # Initialize MLOps components
            if self.config.enable_mlops:
                await self._init_mlops_components()

            # Initialize Gen AI components
            if self.config.enable_genai:
                await self._init_genai_components()

            # Initialize monitoring (Phase 3 - coming soon)
            if self.config.enable_monitoring:
                self.logger.info("Monitoring components not yet implemented (Phase 3)")
                # await self._init_monitoring_components()

            # Initialize serving (Phase 3 - coming soon)
            self.logger.info("Serving components not yet implemented (Phase 3)")
            # await self._init_serving_components()

            self._initialized = True
            self._start_time = asyncio.get_event_loop().time()

            self.logger.info("Platform initialization complete")

        except Exception as e:
            self.logger.error(f"Platform initialization failed: {e}")
            raise

    async def _init_mlops_components(self) -> None:
        """Initialize MLOps infrastructure components."""
        self.logger.info("Initializing MLOps components...")

        # Import here to avoid circular dependencies
        try:
            from ..mlops import (
                ExperimentTracker,
                ModelRegistry,
                FeatureStore,
                ModelMonitor,
            )
        except ImportError:
            # Fallback for script execution
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from mlops import (
                ExperimentTracker,
                ModelRegistry,
                FeatureStore,
                ModelMonitor,
            )

        # Initialize experiment tracking
        self._mlops_components["experiment_tracker"] = ExperimentTracker(self.config)
        await self._mlops_components["experiment_tracker"].initialize()

        # Initialize model registry
        self._mlops_components["model_registry"] = ModelRegistry(self.config)
        await self._mlops_components["model_registry"].initialize()

        # Initialize feature store
        self._mlops_components["feature_store"] = FeatureStore(self.config)
        await self._mlops_components["feature_store"].initialize()

        # Initialize model monitoring
        self._mlops_components["model_monitor"] = ModelMonitor(self.config)
        await self._mlops_components["model_monitor"].initialize()

        self.logger.info("MLOps components initialized")

    async def _init_genai_components(self) -> None:
        """Initialize Gen AI components."""
        self.logger.info("Initializing Gen AI components...")

        # Import here to avoid circular dependencies
        try:
            from ..genai import (
                LLMManager,
                FineTuningPipeline,
                RAGSystem,
                AIAgentFramework,
                MultiModalProcessor,
            )
        except ImportError:
            # Fallback for script execution
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from genai import (
                LLMManager,
                FineTuningPipeline,
                RAGSystem,
                AIAgentFramework,
                MultiModalProcessor,
            )

        # Initialize LLM manager
        self._genai_components["llm_manager"] = LLMManager(self.config)
        await self._genai_components["llm_manager"].initialize()

        # Initialize fine-tuning pipeline
        self._genai_components["finetuning_pipeline"] = FineTuningPipeline(self.config)
        await self._genai_components["finetuning_pipeline"].initialize()

        # Initialize RAG system
        if self.config.enable_rag:
            self._genai_components["rag_system"] = RAGSystem(self.config)
            await self._genai_components["rag_system"].initialize()

        # Initialize AI agent framework
        if self.config.enable_agents:
            self._genai_components["agent_framework"] = AIAgentFramework(self.config)
            await self._genai_components["agent_framework"].initialize()

        # Initialize multi-modal processor
        self._genai_components["multimodal_processor"] = MultiModalProcessor(self.config)
        await self._genai_components["multimodal_processor"].initialize()

        self.logger.info("Gen AI components initialized")

    async def _init_monitoring_components(self) -> None:
        """Initialize monitoring and observability."""
        self.logger.info("Initializing monitoring components...")

        # Import here to avoid circular dependencies
        try:
            from ..monitoring import MetricsCollector, TracingManager
        except ImportError:
            # Fallback for script execution
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from monitoring import MetricsCollector, TracingManager

        # Initialize metrics collection
        self._monitoring_components["metrics_collector"] = MetricsCollector(self.config)
        await self._monitoring_components["metrics_collector"].initialize()

        # Initialize tracing
        if self.config.monitoring.enable_tracing:
            self._monitoring_components["tracing_manager"] = TracingManager(self.config)
            await self._monitoring_components["tracing_manager"].initialize()

        self.logger.info("Monitoring components initialized")

    async def _init_serving_components(self) -> None:
        """Initialize serving infrastructure."""
        self.logger.info("Initializing serving components...")

        # Import here to avoid circular dependencies
        try:
            from ..serving import ModelServer, APIManager
        except ImportError:
            # Fallback for script execution
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from serving import ModelServer, APIManager

        # Initialize model server
        self._serving_components["model_server"] = ModelServer(self.config)
        await self._serving_components["model_server"].initialize()

        # Initialize API manager
        self._serving_components["api_manager"] = APIManager(self.config)
        await self._serving_components["api_manager"].initialize()

        self.logger.info("Serving components initialized")

    async def shutdown(self) -> None:
        """Shutdown all platform components gracefully."""
        self.logger.info("Shutting down platform...")

        # Shutdown in reverse order
        components_to_shutdown = [
            self._serving_components,
            self._monitoring_components,
            self._genai_components,
            self._mlops_components,
        ]

        for component_group in components_to_shutdown:
            for component in component_group.values():
                if hasattr(component, "shutdown"):
                    await component.shutdown()

        self._initialized = False
        self.logger.info("Platform shutdown complete")

    def get_status(self) -> PlatformStatus:
        """Get platform status information."""
        uptime = None
        if self._start_time:
            uptime = asyncio.get_event_loop().time() - self._start_time

        components = {}

        # Check MLOps components
        for name, component in self._mlops_components.items():
            components[f"mlops_{name}"] = "initialized" if component else "not_initialized"

        # Check Gen AI components
        for name, component in self._genai_components.items():
            components[f"genai_{name}"] = "initialized" if component else "not_initialized"

        # Check monitoring components
        for name, component in self._monitoring_components.items():
            components[f"monitoring_{name}"] = "initialized" if component else "not_initialized"

        # Check serving components
        for name, component in self._serving_components.items():
            components[f"serving_{name}"] = "initialized" if component else "not_initialized"

        return PlatformStatus(
            status="healthy" if self._initialized else "initializing",
            version=self.config.version,
            environment=self.config.environment,
            components=components,
            uptime_seconds=uptime,
        )

    # MLOps Interface
    async def train_model(
        self,
        model_type: str,
        dataset: Any,
        hyperparameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Train a model using MLOps infrastructure."""
        if not self._initialized or "experiment_tracker" not in self._mlops_components:
            raise RuntimeError("Platform not initialized or MLOps components not available")

        return await self._mlops_components["experiment_tracker"].train_model(
            model_type, dataset, hyperparameters, **kwargs
        )

    async def deploy_model(self, model_id: str, **kwargs) -> str:
        """Deploy a model to production."""
        if not self._initialized or "model_registry" not in self._mlops_components:
            raise RuntimeError("Platform not initialized or MLOps components not available")

        return await self._mlops_components["model_registry"].deploy_model(model_id, **kwargs)

    # Gen AI Interface
    async def generate_text(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Generate text using LLM with optional RAG context."""
        if not self._initialized or "llm_manager" not in self._genai_components:
            raise RuntimeError("Platform not initialized or Gen AI components not available")

        # Use RAG if context provided and RAG system available
        if context and "rag_system" in self._genai_components:
            enhanced_context = await self._genai_components["rag_system"].retrieve_context(
                prompt, context
            )
            kwargs["context"] = enhanced_context

        response = await self._genai_components["llm_manager"].generate_text(prompt, **kwargs)
        return response.content if hasattr(response, 'content') else str(response)

    async def finetune_model(
        self,
        model_name: str,
        dataset_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Fine-tune a model using the fine-tuning pipeline."""
        if not self._initialized or "finetuning_pipeline" not in self._genai_components:
            raise RuntimeError("Platform not initialized or Gen AI components not available")

        # Create fine-tuning job
        job_id = await self._genai_components["finetuning_pipeline"].create_finetuning_job(
            name=model_name,
            config=kwargs.get("config", {}),
            dataset_config={"path": dataset_path}
        )

        # Start fine-tuning
        result = await self._genai_components["finetuning_pipeline"].start_finetuning(job_id)
        return result

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using RAG."""
        if not self._initialized or "rag_system" not in self._genai_components:
            raise RuntimeError("Platform not initialized or Gen AI components not available")

        results = await self._genai_components["rag_system"].search(query, top_k=top_k, **kwargs)
        return [{"content": r.document.content, "score": r.score} for r in results]

    async def create_agent(
        self,
        agent_type: str,
        tools: List[str],
        **kwargs
    ) -> Any:
        """Create an AI agent with specified tools."""
        if not self._initialized or "agent_framework" not in self._genai_components:
            raise RuntimeError("Platform not initialized or Gen AI components not available")

        return await self._genai_components["agent_framework"].create_agent(
            agent_type, tools, **kwargs
        )

    async def process_multimodal(
        self,
        content: Any,
        content_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process multi-modal content."""
        if not self._initialized or "multimodal_processor" not in self._genai_components:
            raise RuntimeError("Platform not initialized or Gen AI components not available")

        result = await self._genai_components["multimodal_processor"].process_content(
            content, content_type, **kwargs
        )
        return {
            "content_type": result.content_type,
            "analysis_results": result.analysis_results,
            "has_embeddings": result.embeddings is not None,
        }

    # FastAPI Integration
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """FastAPI lifespan context manager."""
        await self.initialize()
        yield
        await self.shutdown()


# Global platform instance
platform = MLOpsPlatform()
