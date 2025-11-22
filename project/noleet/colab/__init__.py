"""Google Colab compatibility layer for NoLeet."""

from .colab_detector import ColabDetector
from .colab_storage import ColabStorage
from .colab_gpu_utilizer import ColabGPUUtilizer

__all__ = ["ColabDetector", "ColabStorage", "ColabGPUUtilizer"]

