"""
TorchServe Integration for Model Serving.

TorchServe is PyTorch's model serving framework for production deployment.
This module integrates TorchServe with the MLOps platform.

Key Features:
- Model packaging and archiving
- Model serving endpoints
- Model versioning and management
- Batch inference support
- Integration with FastAPI

Production Considerations:
- Model versioning and rollback
- Health checks and monitoring
- Resource management
- Error handling and retries
"""

import logging
import subprocess
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time


class TorchServeManager:
    """
    Manager for TorchServe model serving.
    
    Handles model packaging, deployment, and serving lifecycle.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize TorchServe manager.
        
        Args:
            base_url: TorchServe server base URL
        """
        self._base_url = base_url.rstrip("/")
        self._logger = logging.getLogger(f"{__name__}.TorchServeManager")
        self._is_available = self._check_torchserve_available()
    
    def _check_torchserve_available(self) -> bool:
        """Check if TorchServe is available."""
        try:
            import torchserve
            return True
        except ImportError:
            try:
                # Check if torch-model-archiver is available
                result = subprocess.run(
                    ["torch-model-archiver", "--version"],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
            except Exception:
                self._logger.warning("TorchServe not available")
                return False
    
    def package_model(
        self,
        model_path: str,
        model_name: str,
        handler_path: Optional[str] = None,
        extra_files: Optional[List[str]] = None,
        requirements_file: Optional[str] = None,
        version: str = "1.0"
    ) -> Optional[Path]:
        """
        Package model for TorchServe deployment.
        
        Args:
            model_path: Path to model file (.pth, .pt, etc.)
            model_name: Name for the model
            handler_path: Path to custom handler script
            extra_files: Additional files to include
            requirements_file: Path to requirements.txt
            version: Model version
            
        Returns:
            Path to created .mar file, or None if failed
        """
        if not self._is_available:
            self._logger.warning("TorchServe not available, cannot package model")
            return None
        
        try:
            output_dir = Path("/tmp/torchserve_models")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            mar_file = output_dir / f"{model_name}.mar"
            
            cmd = [
                "torch-model-archiver",
                "--model-name", model_name,
                "--version", version,
                "--model-file", model_path,
                "--serialized-file", model_path,
                "--export-path", str(output_dir),
                "--force"
            ]
            
            if handler_path:
                cmd.extend(["--handler", handler_path])
            
            if extra_files:
                cmd.extend(["--extra-files", ",".join(extra_files)])
            
            if requirements_file:
                cmd.extend(["--requirements-file", requirements_file])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and mar_file.exists():
                self._logger.info(f"Model packaged successfully: {mar_file}")
                return mar_file
            else:
                self._logger.error(f"Model packaging failed: {result.stderr}")
                return None
                
        except Exception as e:
            self._logger.error(f"Error packaging model: {e}")
            return None
    
    def register_model(
        self,
        mar_file_path: str,
        model_name: Optional[str] = None,
        initial_workers: int = 1,
        batch_size: int = 1,
        max_batch_delay: int = 100
    ) -> bool:
        """
        Register model with TorchServe.
        
        Args:
            mar_file_path: Path to .mar file
            model_name: Model name (extracted from mar if None)
            initial_workers: Number of initial worker processes
            batch_size: Batch size for inference
            max_batch_delay: Maximum batch delay in ms
            
        Returns:
            True if registration successful
        """
        if not self._is_available:
            self._logger.warning("TorchServe not available, cannot register model")
            return False
        
        try:
            import requests
            
            if model_name is None:
                model_name = Path(mar_file_path).stem
            
            url = f"{self._base_url}/models"
            
            params = {
                "model_name": model_name,
                "url": mar_file_path,
                "initial_workers": initial_workers,
                "batch_size": batch_size,
                "max_batch_delay": max_batch_delay
            }
            
            response = requests.post(url, params=params, timeout=60)
            
            if response.status_code == 200:
                self._logger.info(f"Model registered successfully: {model_name}")
                return True
            else:
                self._logger.error(f"Model registration failed: {response.text}")
                return False
                
        except Exception as e:
            self._logger.error(f"Error registering model: {e}")
            return False
    
    def predict(
        self,
        model_name: str,
        data: Any,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Make prediction using TorchServe model.
        
        Args:
            model_name: Name of registered model
            data: Input data for prediction
            timeout: Request timeout in seconds
            
        Returns:
            Prediction result or None if failed
        """
        if not self._is_available:
            self._logger.warning("TorchServe not available, cannot make prediction")
            return None
        
        try:
            import requests
            
            url = f"{self._base_url}/predictions/{model_name}"
            
            if isinstance(data, dict):
                response = requests.post(url, json=data, timeout=timeout)
            else:
                response = requests.post(url, data=data, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                self._logger.error(f"Prediction failed: {response.text}")
                return None
                
        except Exception as e:
            self._logger.error(f"Error making prediction: {e}")
            return None
    
    def get_model_status(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get model status from TorchServe.
        
        Args:
            model_name: Name of model
            
        Returns:
            Model status information or None
        """
        if not self._is_available:
            return None
        
        try:
            import requests
            
            url = f"{self._base_url}/models/{model_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            self._logger.error(f"Error getting model status: {e}")
            return None
    
    def unregister_model(self, model_name: str) -> bool:
        """
        Unregister model from TorchServe.
        
        Args:
            model_name: Name of model to unregister
            
        Returns:
            True if unregistration successful
        """
        if not self._is_available:
            self._logger.warning("TorchServe not available, cannot unregister model")
            return False
        
        try:
            import requests
            
            url = f"{self._base_url}/models/{model_name}"
            response = requests.delete(url, timeout=30)
            
            if response.status_code == 200:
                self._logger.info(f"Model unregistered: {model_name}")
                return True
            else:
                self._logger.error(f"Model unregistration failed: {response.text}")
                return False
                
        except Exception as e:
            self._logger.error(f"Error unregistering model: {e}")
            return False
    
    def scale_workers(self, model_name: str, min_workers: int, max_workers: int) -> bool:
        """
        Scale model workers.
        
        Args:
            model_name: Name of model
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers
            
        Returns:
            True if scaling successful
        """
        if not self._is_available:
            return False
        
        try:
            import requests
            
            url = f"{self._base_url}/models/{model_name}"
            
            params = {
                "min_workers": min_workers,
                "max_workers": max_workers
            }
            
            response = requests.put(url, params=params, timeout=30)
            
            if response.status_code == 200:
                self._logger.info(f"Workers scaled for {model_name}: {min_workers}-{max_workers}")
                return True
            else:
                return False
                
        except Exception as e:
            self._logger.error(f"Error scaling workers: {e}")
            return False


class TorchServeHandler:
    """
    Base handler for TorchServe model inference.
    
    Custom handlers should inherit from this class.
    """
    
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.TorchServeHandler")
    
    def initialize(self, context: Any) -> None:
        """
        Initialize handler with model context.
        
        Args:
            context: TorchServe model context
        """
        self._context = context
        self._model = context.model
        self._logger.info("Handler initialized")
    
    def preprocess(self, data: Any) -> Any:
        """
        Preprocess input data.
        
        Args:
            data: Raw input data
            
        Returns:
            Preprocessed data
        """
        return data
    
    def inference(self, data: Any) -> Any:
        """
        Run model inference.
        
        Args:
            data: Preprocessed data
            
        Returns:
            Model predictions
        """
        return self._model(data)
    
    def postprocess(self, data: Any) -> Any:
        """
        Postprocess model output.
        
        Args:
            data: Model predictions
            
        Returns:
            Final output
        """
        return data
    
    def handle(self, data: Any, context: Any) -> Any:
        """
        Handle inference request.
        
        Args:
            data: Input data
            context: Model context
            
        Returns:
            Inference result
        """
        preprocessed = self.preprocess(data)
        inference_result = self.inference(preprocessed)
        return self.postprocess(inference_result)


class TorchServeIntegration:
    """
    Integration class for TorchServe with MLOps platform.
    
    Provides unified interface for model serving.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize TorchServe integration.
        
        Args:
            base_url: TorchServe server base URL
        """
        self._manager = TorchServeManager(base_url)
        self._logger = logging.getLogger(f"{__name__}.TorchServeIntegration")
        self._registered_models: Dict[str, Dict[str, Any]] = {}
    
    def deploy_model(
        self,
        model_path: str,
        model_name: str,
        handler_path: Optional[str] = None,
        version: str = "1.0"
    ) -> bool:
        """
        Deploy model to TorchServe.
        
        Args:
            model_path: Path to model file
            model_name: Model name
            handler_path: Path to custom handler
            version: Model version
            
        Returns:
            True if deployment successful
        """
        # Package model
        mar_file = self._manager.package_model(
            model_path=model_path,
            model_name=model_name,
            handler_path=handler_path,
            version=version
        )
        
        if not mar_file:
            return False
        
        # Register model
        success = self._manager.register_model(str(mar_file), model_name)
        
        if success:
            self._registered_models[model_name] = {
                "mar_file": str(mar_file),
                "version": version,
                "deployed_at": datetime.now().isoformat()
            }
        
        return success
    
    def predict(self, model_name: str, data: Any) -> Optional[Dict[str, Any]]:
        """
        Make prediction using deployed model.
        
        Args:
            model_name: Name of deployed model
            data: Input data
            
        Returns:
            Prediction result
        """
        return self._manager.predict(model_name, data)
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about deployed model.
        
        Args:
            model_name: Name of model
            
        Returns:
            Model information
        """
        status = self._manager.get_model_status(model_name)
        if status and model_name in self._registered_models:
            return {
                **status,
                **self._registered_models[model_name]
            }
        return status
    
    def is_available(self) -> bool:
        """Check if TorchServe is available."""
        return self._manager._is_available


if __name__ == "__main__":
    """Demo TorchServe integration."""
    import asyncio
    
    async def demo():
        logging.basicConfig(level=logging.INFO)
        
        integration = TorchServeIntegration()
        
        print(f"TorchServe Available: {integration.is_available()}")
        print()
        
        if integration.is_available():
            # Example: Deploy a model
            # model_path = "/path/to/model.pth"
            # success = integration.deploy_model(model_path, "my_model")
            # print(f"Model deployed: {success}")
            
            # Example: Make prediction
            # result = integration.predict("my_model", {"input": "data"})
            # print(f"Prediction: {result}")
            
            print("TorchServe integration ready")
        else:
            print("TorchServe not available - install torchserve package")
    
    asyncio.run(demo())