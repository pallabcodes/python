"""Google Colab environment detection."""

import os
import sys
import logging
from typing import Optional, Dict, Any


class ColabDetector:
    """Detects and provides information about Google Colab environment."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize Colab detector.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._is_colab = self._detect_colab()
        self._colab_info = self._get_colab_info() if self._is_colab else {}

    def is_colab(self) -> bool:
        """
        Check if running in Google Colab.

        Returns:
            True if running in Colab
        """
        return self._is_colab

    def get_colab_info(self) -> Dict[str, Any]:
        """
        Get Colab environment information.

        Returns:
            Dictionary with Colab environment details
        """
        return self._colab_info.copy()

    def _detect_colab(self) -> bool:
        """Detect if running in Google Colab."""
        try:
            # Method 1: Check for colab module
            import google.colab
            return True
        except ImportError:
            pass

        # Method 2: Check for Colab-specific environment variables
        if os.getenv("COLAB_GPU") is not None:
            return True

        # Method 3: Check for Colab-specific paths
        if "/content" in sys.path or os.path.exists("/content"):
            return True

        # Method 4: Check user agent or other Colab indicators
        if os.getenv("GOOGLE_COLAB") == "1":
            return True

        return False

    def _get_colab_info(self) -> Dict[str, Any]:
        """Get detailed Colab environment information."""
        info = {
            "is_colab": True,
            "runtime_type": self._get_runtime_type(),
            "gpu_available": self._check_gpu_availability(),
            "gpu_info": self._get_gpu_info(),
            "memory_info": self._get_memory_info(),
            "storage_info": self._get_storage_info(),
            "environment_vars": self._get_relevant_env_vars()
        }

        self._logger.info(f"Detected Colab environment: {info}")
        return info

    def _get_runtime_type(self) -> str:
        """Get Colab runtime type (CPU/GPU/TPU)."""
        try:
            # Check for TPU
            import tensorflow as tf
            tpu_devices = tf.config.list_logical_devices("TPU")
            if tpu_devices:
                return "TPU"
        except ImportError:
            pass

        # Check for GPU
        if self._check_gpu_availability():
            return "GPU"

        return "CPU"

    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available in Colab."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            try:
                import tensorflow as tf
                return len(tf.config.list_physical_devices("GPU")) > 0
            except ImportError:
                pass

        return False

    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information."""
        gpu_info = {
            "available": False,
            "count": 0,
            "name": None,
            "memory": None
        }

        try:
            import torch
            if torch.cuda.is_available():
                gpu_info["available"] = True
                gpu_info["count"] = torch.cuda.device_count()
                if gpu_info["count"] > 0:
                    gpu_info["name"] = torch.cuda.get_device_name(0)
                    gpu_info["memory"] = torch.cuda.get_device_properties(0).total_memory
        except ImportError:
            pass

        return gpu_info

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get system memory information."""
        memory_info = {
            "total_gb": None,
            "available_gb": None,
            "used_gb": None
        }

        try:
            import psutil
            mem = psutil.virtual_memory()
            memory_info["total_gb"] = round(mem.total / (1024**3), 2)
            memory_info["available_gb"] = round(mem.available / (1024**3), 2)
            memory_info["used_gb"] = round(mem.used / (1024**3), 2)
        except ImportError:
            # Fallback: try to read from /proc/meminfo (Linux)
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            total_kb = int(line.split()[1])
                            memory_info["total_gb"] = round(total_kb / (1024**2), 2)
                        elif line.startswith("MemAvailable:"):
                            avail_kb = int(line.split()[1])
                            memory_info["available_gb"] = round(avail_kb / (1024**2), 2)
                            break
            except (FileNotFoundError, OSError):
                pass

        return memory_info

    def _get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        storage_info = {
            "content_dir_exists": False,
            "drive_mounted": False,
            "available_space_gb": None
        }

        # Check if /content directory exists
        import os
        storage_info["content_dir_exists"] = os.path.exists("/content")

        # Check if Google Drive is mounted
        storage_info["drive_mounted"] = os.path.exists("/content/drive")

        # Get available space
        try:
            stat = os.statvfs("/content" if storage_info["content_dir_exists"] else "/")
            available_bytes = stat.f_bavail * stat.f_frsize
            storage_info["available_space_gb"] = round(available_bytes / (1024**3), 2)
        except (OSError, AttributeError):
            pass

        return storage_info

    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get relevant environment variables."""
        relevant_vars = [
            "COLAB_GPU",
            "COLAB_TPU_ADDR",
            "COLAB_BACKEND_VERSION",
            "PYTHONPATH"
        ]

        env_vars = {}
        for var in relevant_vars:
            value = os.getenv(var)
            if value is not None:
                env_vars[var] = value

        return env_vars

    def get_optimization_suggestions(self) -> Dict[str, Any]:
        """
        Get optimization suggestions based on Colab environment.

        Returns:
            Dictionary with optimization suggestions
        """
        suggestions = {
            "use_gpu": False,
            "batch_size_multiplier": 1.0,
            "memory_optimization": [],
            "performance_tips": []
        }

        if not self._is_colab:
            return suggestions

        info = self._colab_info

        # GPU suggestions
        if info.get("gpu_available"):
            suggestions["use_gpu"] = True
            gpu_info = info.get("gpu_info", {})
            gpu_name = gpu_info.get("name", "").lower()

            if "tesla" in gpu_name or "t4" in gpu_name:
                suggestions["batch_size_multiplier"] = 4.0
                suggestions["performance_tips"].append("Use mixed precision training")
            elif "a100" in gpu_name:
                suggestions["batch_size_multiplier"] = 8.0
                suggestions["performance_tips"].append("Leverage A100's high memory bandwidth")

        # Memory suggestions
        memory_info = info.get("memory_info", {})
        total_gb = memory_info.get("total_gb", 0)

        if total_gb < 13:  # Standard Colab CPU runtime
            suggestions["memory_optimization"].append("Use smaller batch sizes")
            suggestions["memory_optimization"].append("Enable gradient checkpointing")
        elif total_gb > 25:  # High-RAM runtime
            suggestions["batch_size_multiplier"] = 2.0
            suggestions["performance_tips"].append("Take advantage of extra RAM for larger models")

        # Storage suggestions
        storage_info = info.get("storage_info", {})
        if storage_info.get("drive_mounted"):
            suggestions["performance_tips"].append("Use Google Drive for persistent storage")
        else:
            suggestions["performance_tips"].append("Mount Google Drive for larger datasets")

        return suggestions

    def setup_colab_environment(self) -> Dict[str, Any]:
        """
        Setup Colab-specific environment optimizations.

        Returns:
            Dictionary with setup results
        """
        setup_results = {
            "gpu_setup": False,
            "memory_setup": False,
            "drive_setup": False,
            "warnings": [],
            "optimizations_applied": []
        }

        if not self._is_colab:
            setup_results["warnings"].append("Not running in Colab environment")
            return setup_results

        # GPU setup
        if self._colab_info.get("gpu_available"):
            try:
                import torch
                torch.backends.cudnn.benchmark = True
                setup_results["gpu_setup"] = True
                setup_results["optimizations_applied"].append("GPU optimizations enabled")
            except ImportError:
                setup_results["warnings"].append("PyTorch not available for GPU setup")

        # Memory setup
        try:
            import gc
            gc.collect()
            setup_results["memory_setup"] = True
            setup_results["optimizations_applied"].append("Garbage collection performed")
        except Exception as e:
            setup_results["warnings"].append(f"Memory setup failed: {e}")

        # Drive mount reminder
        if not self._colab_info.get("storage_info", {}).get("drive_mounted"):
            setup_results["warnings"].append("Google Drive not mounted - consider mounting for persistent storage")

        return setup_results
