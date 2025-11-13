"""
ML Pipeline with GPU Acceleration Support.

Demonstrates:
- Machine learning model inference for real-time analytics
- GPU acceleration with PyTorch/TensorFlow
- Model loading and caching
- Batch processing for efficiency
- Graceful degradation when ML libraries unavailable
- Integration with multiprocessing for CPU-bound preprocessing
"""

import asyncio
import time
import logging
import json
import pickle
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path

# ML Framework imports (with fallbacks)
try:
    import torch
    import torch.nn as nn
    HAS_PYTORCH = True
except ImportError:
    HAS_PYTORCH = False
    torch = None
    nn = None

try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    tf = None

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

logger = logging.getLogger(__name__)


@dataclass
class MLModelConfig:
    """Configuration for ML model."""
    model_type: str  # "pytorch", "tensorflow", "sklearn"
    model_path: Optional[str] = None
    device: str = "auto"  # "cpu", "cuda", "auto"
    batch_size: int = 32
    max_batch_wait_ms: int = 100
    use_gpu: bool = True


@dataclass
class MLPrediction:
    """ML model prediction result."""
    prediction_id: str
    model_name: str
    predictions: List[Any]
    confidence_scores: Optional[List[float]] = None
    processing_time: float = 0.0
    used_gpu: bool = False
    batch_size: int = 1


@dataclass
class MLProcessorMetrics:
    """Metrics for ML processor performance."""
    total_predictions: int = 0
    total_batches: int = 0
    gpu_predictions: int = 0
    cpu_predictions: int = 0
    avg_processing_time: float = 0.0
    avg_batch_size: float = 0.0
    model_load_count: int = 0
    errors: int = 0


class BaseMLModel:
    """Base class for ML models."""
    
    def __init__(self, model_name: str, config: MLModelConfig):
        self.model_name = model_name
        self.config = config
        self.model = None
        self.device = self._determine_device()
        self.loaded = False
    
    def _determine_device(self) -> str:
        """Determine the device to use."""
        if self.config.device == "auto":
            if HAS_PYTORCH and torch.cuda.is_available() and self.config.use_gpu:
                return "cuda"
            elif HAS_TENSORFLOW and len(tf.config.list_physical_devices('GPU')) > 0 and self.config.use_gpu:
                return "gpu"
            else:
                return "cpu"
        return self.config.device
    
    def load(self):
        """Load the model."""
        raise NotImplementedError
    
    def predict(self, inputs: List[Any]) -> List[Any]:
        """Run prediction on inputs."""
        raise NotImplementedError
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.loaded


class PyTorchModel(BaseMLModel):
    """PyTorch model wrapper."""
    
    def load(self):
        """Load PyTorch model."""
        if not HAS_PYTORCH:
            logger.warning("PyTorch not available, using mock model")
            self.model = self._create_mock_model()
            self.loaded = True
            return
        
        try:
            if self.config.model_path and Path(self.config.model_path).exists():
                self.model = torch.load(self.config.model_path, map_location=self.device)
            else:
                # Create a simple mock model for demonstration
                self.model = self._create_mock_model()
            
            self.model.to(self.device)
            self.model.eval()
            self.loaded = True
            logger.info(f"PyTorch model loaded on device: {self.device}")
        except Exception as e:
            logger.error(f"Error loading PyTorch model: {e}")
            self.model = self._create_mock_model()
            self.loaded = True
    
    def _create_mock_model(self):
        """Create a mock PyTorch model for demonstration."""
        if HAS_PYTORCH:
            class MockModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.fc = nn.Linear(10, 1)
                
                def forward(self, x):
                    return torch.sigmoid(self.fc(x))
            return MockModel()
        return None
    
    def predict(self, inputs: List[Any]) -> List[Any]:
        """Run PyTorch prediction."""
        if not HAS_PYTORCH or not self.model:
            # Mock predictions
            return [0.5] * len(inputs)
        
        try:
            # Convert inputs to tensor
            if HAS_NUMPY:
                input_tensor = torch.tensor(np.array(inputs), dtype=torch.float32)
            else:
                input_tensor = torch.tensor(inputs, dtype=torch.float32)
            
            input_tensor = input_tensor.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(input_tensor)
                predictions = outputs.cpu().numpy().tolist()
            
            return predictions
        except Exception as e:
            logger.error(f"Error in PyTorch prediction: {e}")
            return [0.0] * len(inputs)


class TensorFlowModel(BaseMLModel):
    """TensorFlow model wrapper."""
    
    def load(self):
        """Load TensorFlow model."""
        if not HAS_TENSORFLOW:
            logger.warning("TensorFlow not available, using mock model")
            self.model = None
            self.loaded = True
            return
        
        try:
            if self.config.model_path and Path(self.config.model_path).exists():
                self.model = tf.keras.models.load_model(self.config.model_path)
            else:
                # Create a simple mock model
                self.model = self._create_mock_model()
            
            # Set device
            if self.device == "gpu":
                with tf.device('/GPU:0'):
                    pass
            
            self.loaded = True
            logger.info(f"TensorFlow model loaded on device: {self.device}")
        except Exception as e:
            logger.error(f"Error loading TensorFlow model: {e}")
            self.model = None
            self.loaded = True
    
    def _create_mock_model(self):
        """Create a mock TensorFlow model."""
        if HAS_TENSORFLOW:
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(10, activation='relu', input_shape=(10,)),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            return model
        return None
    
    def predict(self, inputs: List[Any]) -> List[Any]:
        """Run TensorFlow prediction."""
        if not HAS_TENSORFLOW or not self.model:
            return [0.5] * len(inputs)
        
        try:
            if HAS_NUMPY:
                input_array = np.array(inputs)
            else:
                input_array = inputs
            
            predictions = self.model.predict(input_array, verbose=0)
            return predictions.tolist()
        except Exception as e:
            logger.error(f"Error in TensorFlow prediction: {e}")
            return [0.0] * len(inputs)


class MLProcessor:
    """
    ML Processor for real-time analytics inference.
    
    Features:
    - Multiple model support (PyTorch, TensorFlow)
    - GPU acceleration
    - Batch processing
    - Model caching and lazy loading
    - Async inference pipeline
    """
    
    def __init__(self, config: Optional[MLModelConfig] = None):
        self.config = config or MLModelConfig(
            model_type="pytorch",
            device="auto",
            batch_size=32
        )
        
        # Model management
        self.models: Dict[str, BaseMLModel] = {}
        self.model_lock = asyncio.Lock()
        
        # Batch processing
        self.pending_inputs: Dict[str, List[Any]] = {}
        self.pending_callbacks: Dict[str, List[Callable]] = {}
        self.batch_tasks: Dict[str, asyncio.Task] = {}
        
        # Metrics
        self.metrics = MLProcessorMetrics()
        
        # Thread pool for CPU-bound preprocessing
        self.preprocess_executor = ThreadPoolExecutor(max_workers=4)
        
        self.running = False
    
    async def load_model(self, model_name: str, config: MLModelConfig) -> bool:
        """Load an ML model."""
        async with self.model_lock:
            if model_name in self.models:
                logger.info(f"Model {model_name} already loaded")
                return True
            
            try:
                if config.model_type == "pytorch":
                    model = PyTorchModel(model_name, config)
                elif config.model_type == "tensorflow":
                    model = TensorFlowModel(model_name, config)
                else:
                    logger.error(f"Unsupported model type: {config.model_type}")
                    return False
                
                # Load model (blocking operation in executor)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.preprocess_executor, model.load)
                
                self.models[model_name] = model
                self.metrics.model_load_count += 1
                
                logger.info(f"Model {model_name} loaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error loading model {model_name}: {e}")
                return False
    
    async def predict(
        self,
        model_name: str,
        inputs: Any,
        callback: Optional[Callable] = None
    ) -> Optional[MLPrediction]:
        """
        Run prediction (async, supports batching).
        
        Args:
            model_name: Name of the model to use
            inputs: Input data for prediction
            callback: Optional callback for async results
            
        Returns:
            Prediction result (if callback not provided)
        """
        if model_name not in self.models:
            logger.error(f"Model {model_name} not loaded")
            return None
        
        model = self.models[model_name]
        
        # Add to batch
        if model_name not in self.pending_inputs:
            self.pending_inputs[model_name] = []
            self.pending_callbacks[model_name] = []
            # Start batch processing task
            self.batch_tasks[model_name] = asyncio.create_task(
                self._batch_processor(model_name)
            )
        
        self.pending_inputs[model_name].append(inputs)
        if callback:
            self.pending_callbacks[model_name].append(callback)
        
        # If batch is full, trigger immediate processing
        if len(self.pending_inputs[model_name]) >= self.config.batch_size:
            # Signal batch processor
            pass
        
        # If callback provided, return None (async)
        if callback:
            return None
        
        # Otherwise, wait for batch and return result
        # (Simplified - in production would use futures)
        await asyncio.sleep(0.01)  # Brief wait for batching
        return await self._run_prediction(model_name, [inputs])
    
    async def _batch_processor(self, model_name: str):
        """Process batches for a model."""
        while self.running or model_name in self.pending_inputs:
            try:
                # Wait for batch to fill or timeout
                await asyncio.sleep(self.config.max_batch_wait_ms / 1000.0)
                
                if model_name not in self.pending_inputs:
                    break
                
                inputs = self.pending_inputs.get(model_name, [])
                callbacks = self.pending_callbacks.get(model_name, [])
                
                if not inputs:
                    continue
                
                # Process batch
                prediction = await self._run_prediction(model_name, inputs)
                
                # Call callbacks
                for callback in callbacks:
                    if callback:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(prediction)
                        else:
                            callback(prediction)
                
                # Clear batch
                self.pending_inputs[model_name] = []
                self.pending_callbacks[model_name] = []
                
            except Exception as e:
                logger.error(f"Error in batch processor for {model_name}: {e}")
                await asyncio.sleep(0.1)
    
    async def _run_prediction(self, model_name: str, inputs: List[Any]) -> MLPrediction:
        """Run prediction on a batch of inputs."""
        start_time = time.time()
        
        model = self.models[model_name]
        
        # Preprocess inputs (CPU-bound, in executor)
        loop = asyncio.get_event_loop()
        preprocessed = await loop.run_in_executor(
            self.preprocess_executor,
            self._preprocess_inputs,
            inputs
        )
        
        # Run inference (GPU if available, blocking)
        predictions = await loop.run_in_executor(
            None,  # Use default executor for GPU operations
            model.predict,
            preprocessed
        )
        
        processing_time = time.time() - start_time
        
        # Update metrics
        self.metrics.total_predictions += len(inputs)
        self.metrics.total_batches += 1
        if model.device in ["cuda", "gpu"]:
            self.metrics.gpu_predictions += len(inputs)
        else:
            self.metrics.cpu_predictions += len(inputs)
        
        # Update average processing time
        self.metrics.avg_processing_time = (
            (self.metrics.avg_processing_time * (self.metrics.total_batches - 1)) +
            processing_time
        ) / self.metrics.total_batches
        
        self.metrics.avg_batch_size = (
            (self.metrics.avg_batch_size * (self.metrics.total_batches - 1)) +
            len(inputs)
        ) / self.metrics.total_batches
        
        return MLPrediction(
            prediction_id=f"pred_{int(time.time()*1000)}",
            model_name=model_name,
            predictions=predictions,
            processing_time=processing_time,
            used_gpu=(model.device in ["cuda", "gpu"]),
            batch_size=len(inputs)
        )
    
    def _preprocess_inputs(self, inputs: List[Any]) -> List[Any]:
        """Preprocess inputs for model."""
        # Simple preprocessing - normalize, pad, etc.
        # In production, this would be more sophisticated
        if HAS_NUMPY:
            processed = []
            for inp in inputs:
                if isinstance(inp, (list, tuple)):
                    arr = np.array(inp, dtype=np.float32)
                    # Normalize
                    if arr.max() > 1.0:
                        arr = arr / arr.max()
                    # Pad or truncate to expected size (10 features)
                    if len(arr) < 10:
                        arr = np.pad(arr, (0, 10 - len(arr)), 'constant')
                    elif len(arr) > 10:
                        arr = arr[:10]
                    processed.append(arr.tolist())
                else:
                    processed.append([float(inp)] * 10)
            return processed
        return inputs
    
    async def start(self):
        """Start the ML processor."""
        self.running = True
        logger.info("ML Processor started")
    
    async def stop(self):
        """Stop the ML processor."""
        self.running = False
        
        # Cancel batch tasks
        for task in self.batch_tasks.values():
            task.cancel()
        
        if self.batch_tasks:
            await asyncio.gather(*self.batch_tasks.values(), return_exceptions=True)
        
        # Shutdown executor
        self.preprocess_executor.shutdown(wait=True)
        
        logger.info("ML Processor stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get ML processor metrics."""
        return {
            "total_predictions": self.metrics.total_predictions,
            "total_batches": self.metrics.total_batches,
            "gpu_predictions": self.metrics.gpu_predictions,
            "cpu_predictions": self.metrics.cpu_predictions,
            "avg_processing_time": self.metrics.avg_processing_time,
            "avg_batch_size": self.metrics.avg_batch_size,
            "model_load_count": self.metrics.model_load_count,
            "errors": self.metrics.errors,
            "loaded_models": list(self.models.keys())
        }


# Export processor
if not HAS_PYTORCH and not HAS_TENSORFLOW:
    logger.warning("ML frameworks not available. Install PyTorch or TensorFlow for GPU acceleration.")

