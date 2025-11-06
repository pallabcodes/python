"""
Model server for production model serving.

Provides high-performance model inference with caching, batching,
and monitoring capabilities for both ML models and Gen AI models.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig


class InferenceRequest(BaseModel):
    """Model inference request."""
    model_name: str
    inputs: Union[List[Any], Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None


class InferenceResponse(BaseModel):
    """Model inference response."""
    outputs: Union[List[Any], Dict[str, Any]]
    model_name: str
    model_version: str
    processing_time: float
    metadata: Dict[str, Any] = {}


class BatchInferenceRequest(BaseModel):
    """Batch inference request."""
    model_name: str
    inputs: List[Union[List[Any], Dict[str, Any]]]
    parameters: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    version: str
    type: str
    framework: str
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None
    loaded_at: float
    last_used: float
    inference_count: int


class ModelServer:
    """
    Production model server with caching and batching.

    Features:
    - Model loading and caching
    - Batch inference processing
    - Performance monitoring
    - Resource management
    - Health checks and metrics
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize model server.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.ModelServer")

        # Model cache
        self._loaded_models: Dict[str, Any] = {}
        self._model_info: Dict[str, ModelInfo] = {}

        # Performance tracking
        self._inference_times: List[float] = []
        self._total_inferences = 0

        # Batch processing
        self._batch_queue: asyncio.Queue = asyncio.Queue()
        self._batch_processor_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize model server."""
        self.logger.info("Initializing model server...")

        # Start batch processor
        self._batch_processor_task = asyncio.create_task(self._batch_processor())

        self.logger.info("Model server initialized")

    async def load_model(self, model_name: str, model_version: Optional[str] = None) -> bool:
        """
        Load a model into memory.

        Args:
            model_name: Name of the model to load
            model_version: Specific version to load

        Returns:
            True if loaded successfully
        """
        try:
            # Get model metadata from registry
            # In a real implementation, this would load the actual model
            model_info = ModelInfo(
                name=model_name,
                version=model_version or "latest",
                type="unknown",
                framework="unknown",
                loaded_at=time.time(),
                last_used=time.time(),
                inference_count=0
            )

            # Simulate model loading
            self._loaded_models[model_name] = f"loaded_model_{model_name}"
            self._model_info[model_name] = model_info

            self.logger.info(f"Loaded model: {model_name} v{model_info.version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return False

    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.

        Args:
            model_name: Name of the model to unload

        Returns:
            True if unloaded successfully
        """
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            del self._model_info[model_name]
            self.logger.info(f"Unloaded model: {model_name}")
            return True

        return False

    async def predict(
        self,
        request: InferenceRequest
    ) -> InferenceResponse:
        """
        Perform single inference.

        Args:
            request: Inference request

        Returns:
            Inference response
        """
        start_time = time.time()

        try:
            # Check if model is loaded
            if request.model_name not in self._loaded_models:
                await self.load_model(request.model_name)

            if request.model_name not in self._loaded_models:
                raise ValueError(f"Model {request.model_name} not available")

            # Update usage stats
            self._model_info[request.model_name].last_used = start_time
            self._model_info[request.model_name].inference_count += 1

            # Perform inference (simulated)
            outputs = await self._perform_inference(
                request.model_name,
                request.inputs,
                request.parameters
            )

            processing_time = time.time() - start_time
            self._inference_times.append(processing_time)
            self._total_inferences += 1

            return InferenceResponse(
                outputs=outputs,
                model_name=request.model_name,
                model_version=self._model_info[request.model_name].version,
                processing_time=processing_time,
                metadata={"status": "success"}
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Inference failed for {request.model_name}: {e}")

            return InferenceResponse(
                outputs=[],
                model_name=request.model_name,
                model_version="unknown",
                processing_time=processing_time,
                metadata={"error": str(e)}
            )

    async def predict_batch(
        self,
        request: BatchInferenceRequest
    ) -> List[InferenceResponse]:
        """
        Perform batch inference.

        Args:
            request: Batch inference request

        Returns:
            List of inference responses
        """
        start_time = time.time()

        try:
            # Check if model is loaded
            if request.model_name not in self._loaded_models:
                await self.load_model(request.model_name)

            if request.model_name not in self._loaded_models:
                raise ValueError(f"Model {request.model_name} not available")

            # Process batch
            responses = []
            for inputs in request.inputs:
                single_request = InferenceRequest(
                    model_name=request.model_name,
                    inputs=inputs,
                    parameters=request.parameters
                )
                response = await self.predict(single_request)
                responses.append(response)

            batch_time = time.time() - start_time
            self.logger.info(f"Processed batch of {len(responses)} inferences in {batch_time:.3f}s")

            return responses

        except Exception as e:
            self.logger.error(f"Batch inference failed for {request.model_name}: {e}")
            return []

    async def _perform_inference(
        self,
        model_name: str,
        inputs: Union[List[Any], Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Union[List[Any], Dict[str, Any]]:
        """
        Perform actual model inference.

        Args:
            model_name: Name of the model
            inputs: Model inputs
            parameters: Inference parameters

        Returns:
            Model outputs
        """
        # This would implement actual model inference
        # For demo purposes, return mock results

        if isinstance(inputs, list):
            # Assume classification or regression
            if len(inputs) > 0 and isinstance(inputs[0], (int, float)):
                # Numerical inputs - mock regression
                return [sum(inputs) * 0.1 + 0.5]
            else:
                # Text inputs - mock classification
                return {"predictions": [0.8, 0.1, 0.1], "labels": ["positive", "neutral", "negative"]}

        elif isinstance(inputs, dict):
            # Structured inputs
            return {"result": "processed", "confidence": 0.85}

        else:
            return {"output": f"mock_inference_for_{model_name}"}

    async def _batch_processor(self) -> None:
        """Background batch processor."""
        while True:
            try:
                # Wait for batch requests
                await asyncio.sleep(1)  # Check every second

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Batch processor error: {e}")

    def get_model_info(self, model_name: Optional[str] = None) -> Union[ModelInfo, Dict[str, ModelInfo]]:
        """
        Get model information.

        Args:
            model_name: Specific model name, or None for all

        Returns:
            Model info or dict of all model infos
        """
        if model_name:
            return self._model_info.get(model_name)
        else:
            return self._model_info.copy()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self._inference_times:
            return {"total_inferences": 0}

        import statistics
        return {
            "total_inferences": self._total_inferences,
            "avg_inference_time": statistics.mean(self._inference_times),
            "median_inference_time": statistics.median(self._inference_times),
            "min_inference_time": min(self._inference_times),
            "max_inference_time": max(self._inference_times),
            "p95_inference_time": statistics.quantiles(self._inference_times, n=20)[18] if len(self._inference_times) >= 20 else max(self._inference_times),
            "models_loaded": len(self._loaded_models)
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        healthy = True
        issues = []

        # Check if server is responsive
        try:
            # Basic connectivity check
            pass
        except Exception as e:
            healthy = False
            issues.append(f"Server error: {e}")

        return {
            "healthy": healthy,
            "issues": issues,
            "models_loaded": len(self._loaded_models),
            "total_inferences": self._total_inferences
        }

    async def shutdown(self) -> None:
        """Shutdown model server."""
        self.logger.info("Shutting down model server...")

        # Cancel batch processor
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass

        # Unload all models
        for model_name in list(self._loaded_models.keys()):
            await self.unload_model(model_name)

        self.logger.info("Model server shutdown complete")
