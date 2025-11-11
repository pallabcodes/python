"""
Platform configuration management.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PlatformConfig:
    """Platform configuration."""
    concurrency: Any  # ConcurrencyConfig
    ingestion_port: int = 8080
    enable_distributed: bool = False
    alert_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "error_rate": 0.05,
                "latency_p95": 1.0,
                "throughput_drop": 0.5
            }
