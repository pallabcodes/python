"""GPU utilization utilities for Google Colab."""

import logging
from typing import Optional, Dict, Any, Union


class ColabGPUUtilizer:
    """Handles GPU utilization in Google Colab environment."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize GPU utilizer.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._gpu_info = self._detect_gpu()
        self._frameworks = self._detect_frameworks()

    def is_gpu_available(self) -> bool:
        """
        Check if GPU is available.

        Returns:
            True if GPU is available
        """
        return self._gpu_info["available"]

    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get GPU information.

        Returns:
            Dictionary with GPU details
        """
        return self._gpu_info.copy()

    def get_frameworks_info(self) -> Dict[str, Any]:
        """
        Get information about available ML frameworks.

        Returns:
            Dictionary with framework availability
        """
        return self._frameworks.copy()

    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU availability and information."""
        gpu_info = {
            "available": False,
            "count": 0,
            "name": None,
            "memory_gb": 0,
            "driver_version": None,
            "cuda_version": None
        }

        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["available"] = True
                gpu_info["count"] = torch.cuda.device_count()

                if gpu_info["count"] > 0:
                    device = torch.cuda.get_device_properties(0)
                    gpu_info["name"] = device.name
                    gpu_info["memory_gb"] = round(device.total_memory / (1024**3), 2)

                    # Get CUDA version
                    try:
                        gpu_info["cuda_version"] = torch.version.cuda
                    except AttributeError:
                        pass

        except ImportError:
            pass

        # Fallback: try TensorFlow
        if not gpu_info["available"]:
            try:
                import tensorflow as tf
                gpus = tf.config.list_physical_devices("GPU")
                if gpus:
                    gpu_info["available"] = True
                    gpu_info["count"] = len(gpus)

                    # Try to get device details
                    try:
                        gpu_info["name"] = tf.config.experimental.get_device_details(gpus[0]).get("device_name")
                    except Exception:
                        gpu_info["name"] = "TensorFlow GPU"

            except ImportError:
                pass

        self._logger.info(f"GPU detection: {gpu_info}")
        return gpu_info

    def _detect_frameworks(self) -> Dict[str, Any]:
        """Detect available ML frameworks."""
        frameworks = {
            "torch": {"available": False, "version": None, "cuda_available": False},
            "tensorflow": {"available": False, "version": None, "gpu_available": False},
            "transformers": {"available": False, "version": None},
            "sentence_transformers": {"available": False, "version": None},
            "accelerate": {"available": False, "version": None}
        }

        # Check PyTorch
        try:
            import torch
            frameworks["torch"]["available"] = True
            frameworks["torch"]["version"] = torch.__version__
            frameworks["torch"]["cuda_available"] = torch.cuda.is_available()
        except ImportError:
            pass

        # Check TensorFlow
        try:
            import tensorflow as tf
            frameworks["tensorflow"]["available"] = True
            frameworks["tensorflow"]["version"] = tf.__version__
            frameworks["tensorflow"]["gpu_available"] = len(tf.config.list_physical_devices("GPU")) > 0
        except ImportError:
            pass

        # Check Transformers
        try:
            import transformers
            frameworks["transformers"]["available"] = True
            frameworks["transformers"]["version"] = transformers.__version__
        except ImportError:
            pass

        # Check Sentence Transformers
        try:
            import sentence_transformers
            frameworks["sentence_transformers"]["available"] = True
            frameworks["sentence_transformers"]["version"] = sentence_transformers.__version__
        except ImportError:
            pass

        # Check Accelerate
        try:
            import accelerate
            frameworks["accelerate"]["available"] = True
            frameworks["accelerate"]["version"] = accelerate.__version__
        except ImportError:
            pass

        return frameworks

    def optimize_for_gpu(self, framework: str = "auto") -> Dict[str, Any]:
        """
        Apply GPU optimizations for the specified framework.

        Args:
            framework: Framework to optimize ("torch", "tensorflow", or "auto")

        Returns:
            Dictionary with optimization results
        """
        results = {
            "optimizations_applied": [],
            "warnings": [],
            "performance_tips": []
        }

        if not self.is_gpu_available():
            results["warnings"].append("GPU not available, optimizations skipped")
            return results

        if framework == "auto":
            # Auto-detect based on available frameworks
            if self._frameworks["torch"]["available"]:
                framework = "torch"
            elif self._frameworks["tensorflow"]["available"]:
                framework = "tensorflow"
            else:
                results["warnings"].append("No supported ML framework detected")
                return results

        # Apply framework-specific optimizations
        if framework == "torch":
            results.update(self._optimize_pytorch())
        elif framework == "tensorflow":
            results.update(self._optimize_tensorflow())
        else:
            results["warnings"].append(f"Unsupported framework: {framework}")

        self._logger.info(f"Applied GPU optimizations for {framework}: {results['optimizations_applied']}")
        return results

    def _optimize_pytorch(self) -> Dict[str, Any]:
        """Apply PyTorch GPU optimizations."""
        results = {"optimizations_applied": [], "warnings": [], "performance_tips": []}

        try:
            import torch

            # Enable cuDNN optimizations
            torch.backends.cudnn.benchmark = True
            results["optimizations_applied"].append("cuDNN benchmark enabled")

            # Enable TF32 if available (A100/T4 GPUs)
            if torch.cuda.is_available():
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                results["optimizations_applied"].append("TF32 precision enabled")

            # Set memory allocator optimizations
            if hasattr(torch.cuda, "set_per_process_memory_fraction"):
                # Allow using more GPU memory
                torch.cuda.set_per_process_memory_fraction(0.95)
                results["optimizations_applied"].append("GPU memory fraction optimized")

            results["performance_tips"].extend([
                "Use torch.cuda.amp for mixed precision training",
                "Use DataParallel or DistributedDataParallel for multi-GPU",
                "Pin memory for faster data transfer: tensor.pin_memory()",
                "Use non-blocking data transfer: tensor.to(device, non_blocking=True)"
            ])

        except ImportError:
            results["warnings"].append("PyTorch not available")
        except Exception as e:
            results["warnings"].append(f"PyTorch optimization failed: {e}")

        return results

    def _optimize_tensorflow(self) -> Dict[str, Any]:
        """Apply TensorFlow GPU optimizations."""
        results = {"optimizations_applied": [], "warnings": [], "performance_tips": []}

        try:
            import tensorflow as tf

            # Enable mixed precision
            try:
                policy = tf.keras.mixed_precision.Policy("mixed_float16")
                tf.keras.mixed_precision.set_global_policy(policy)
                results["optimizations_applied"].append("Mixed precision enabled")
            except Exception:
                pass

            # Memory growth
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                try:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    results["optimizations_applied"].append("GPU memory growth enabled")
                except RuntimeError:
                    pass

            # XLA compilation
            tf.config.optimizer.set_jit(True)
            results["optimizations_applied"].append("XLA compilation enabled")

            results["performance_tips"].extend([
                "Use tf.function for graph compilation",
                "Use tf.data for efficient data pipelines",
                "Enable mixed precision training",
                "Use distribution strategies for multi-GPU"
            ])

        except ImportError:
            results["warnings"].append("TensorFlow not available")
        except Exception as e:
            results["warnings"].append(f"TensorFlow optimization failed: {e}")

        return results

    def monitor_gpu_usage(self) -> Dict[str, Any]:
        """
        Monitor current GPU usage.

        Returns:
            Dictionary with GPU usage statistics
        """
        usage = {
            "memory_used_gb": 0,
            "memory_free_gb": 0,
            "memory_total_gb": 0,
            "utilization_percent": 0,
            "temperature_celsius": None
        }

        if not self.is_gpu_available():
            return usage

        try:
            import torch

            if torch.cuda.is_available():
                device = torch.cuda.current_device()

                usage["memory_used_gb"] = round(torch.cuda.memory_allocated(device) / (1024**3), 2)
                usage["memory_reserved_gb"] = round(torch.cuda.memory_reserved(device) / (1024**3), 2)

                props = torch.cuda.get_device_properties(device)
                usage["memory_total_gb"] = round(props.total_memory / (1024**3), 2)
                usage["memory_free_gb"] = usage["memory_total_gb"] - usage["memory_used_gb"]

                # Get utilization (if available)
                try:
                    usage["utilization_percent"] = torch.cuda.utilization(device)
                except AttributeError:
                    pass

        except ImportError:
            pass

        return usage

    def get_memory_optimization_tips(self) -> list[str]:
        """
        Get memory optimization tips for Colab.

        Returns:
            List of optimization tips
        """
        tips = [
            "Use smaller batch sizes to fit in GPU memory",
            "Enable gradient checkpointing for large models",
            "Use model quantization (8-bit, 4-bit)",
            "Clear cache regularly: torch.cuda.empty_cache()",
            "Use torch.utils.checkpoint for memory-efficient backprop"
        ]

        if self._gpu_info.get("memory_gb", 0) < 8:
            tips.append("Consider using a smaller model or LoRA fine-tuning")
        elif self._gpu_info.get("memory_gb", 0) > 16:
            tips.append("You can use larger batch sizes or bigger models")

        return tips

    def setup_accelerated_inference(self, framework: str = "torch") -> Dict[str, Any]:
        """
        Setup accelerated inference optimizations.

        Args:
            framework: ML framework to optimize

        Returns:
            Dictionary with setup results
        """
        results = {
            "torch_compile": False,
            "flash_attention": False,
            "quantization": False,
            "optimizations_applied": []
        }

        if not self.is_gpu_available():
            return results

        if framework == "torch" and self._frameworks["torch"]["available"]:
            try:
                import torch

                # Check for torch.compile (PyTorch 2.0+)
                if hasattr(torch, "compile"):
                    results["torch_compile"] = True
                    results["optimizations_applied"].append("torch.compile available")

                # Check for flash attention
                try:
                    import flash_attn
                    results["flash_attention"] = True
                    results["optimizations_applied"].append("Flash attention available")
                except ImportError:
                    pass

                results["optimizations_applied"].append("GPU-accelerated inference ready")

            except Exception as e:
                self._logger.error(f"Torch inference setup failed: {e}")

        return results

    def get_colab_gpu_recommendations(self) -> Dict[str, Any]:
        """
        Get Colab-specific GPU recommendations.

        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "recommended_batch_size": 8,
            "use_mixed_precision": False,
            "recommended_framework": "torch",
            "memory_efficient_training": [],
            "performance_optimizations": []
        }

        gpu_name = self._gpu_info.get("name", "").lower()
        memory_gb = self._gpu_info.get("memory_gb", 0)

        # GPU-specific recommendations
        if "tesla t4" in gpu_name:
            recommendations["recommended_batch_size"] = 16
            recommendations["use_mixed_precision"] = True
            recommendations["performance_optimizations"].extend([
                "T4 excels at mixed precision training",
                "Use gradient accumulation for larger effective batch sizes"
            ])

        elif "tesla v100" in gpu_name:
            recommendations["recommended_batch_size"] = 32
            recommendations["use_mixed_precision"] = True

        elif "a100" in gpu_name:
            recommendations["recommended_batch_size"] = 64
            recommendations["use_mixed_precision"] = True
            recommendations["performance_optimizations"].extend([
                "A100 has exceptional memory bandwidth",
                "Consider using larger models"
            ])

        # Memory-based recommendations
        if memory_gb < 8:
            recommendations["memory_efficient_training"].extend([
                "Use gradient checkpointing",
                "Enable activation recomputation",
                "Consider model parallelism"
            ])
        elif memory_gb > 24:
            recommendations["memory_efficient_training"].append(
                "You have plenty of memory - focus on larger batch sizes"
            )

        return recommendations
