"""
Base processing stage for the analytics pipeline.

This module defines the base class for all processing stages in the analytics
pipeline, providing common functionality for data processing, error handling,
and monitoring.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ..pipeline_core.stage_base import ProcessingStage


@dataclass
class ProcessingStats:
    """Statistics for processing stage operations."""

    messages_processed: int = 0
    messages_failed: int = 0
    processing_time_total: float = 0.0
    last_processing_time: float = 0.0
    errors_count: int = 0
    throughput_per_second: float = 0.0
    last_update_time: float = field(default_factory=time.time)


class BaseProcessingStage(ProcessingStage, ABC):
    """Base class for all processing stages.

    Provides common functionality for data processing stages including:
    - Message processing pipeline
    - Error handling and recovery
    - Statistics collection
    - Logging and monitoring
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the processing stage.

        Args:
            name: Stage name for identification
            config: Configuration dictionary for stage-specific settings
        """
        super().__init__(name)
        self._config = config or {}
        self._stats = ProcessingStats()
        self._logger = logging.getLogger(f"{__name__}.{name}")

        # Processing configuration
        self._max_processing_time = self._config.get('max_processing_time', 30.0)
        self._fail_on_error = self._config.get('fail_on_error', False)
        self._enable_stats = self._config.get('enable_stats', True)

        self._logger.info(f"Initialized processing stage '{name}'")

    @abstractmethod
    def _process_message(self, message: Any) -> Any:
        """Process a single message.

        Args:
            message: Input message to process

        Returns:
            Processed message or None if filtered out

        Raises:
            Exception: If processing fails and should be propagated
        """
        pass

    def process(self, message: Any) -> Optional[Any]:
        """Process a message through this stage.

        Args:
            message: Input message to process

        Returns:
            Processed message or None if message was filtered/processed
        """
        start_time = time.time()

        try:
            # Process the message
            result = self._process_message(message)

            # Update statistics
            if self._enable_stats:
                processing_time = time.time() - start_time
                self._update_stats(success=True, processing_time=processing_time)

            return result

        except Exception as e:
            # Update error statistics
            if self._enable_stats:
                processing_time = time.time() - start_time
                self._update_stats(success=False, processing_time=processing_time)

            # Log the error
            self._logger.error(f"Error processing message: {e}")

            # Handle error based on configuration
            if self._fail_on_error:
                raise
            else:
                return None

    def get_stats(self) -> ProcessingStats:
        """Get processing statistics.

        Returns:
            Current processing statistics
        """
        return ProcessingStats(
            messages_processed=self._stats.messages_processed,
            messages_failed=self._stats.messages_failed,
            processing_time_total=self._stats.processing_time_total,
            last_processing_time=self._stats.last_processing_time,
            errors_count=self._stats.errors_count,
            throughput_per_second=self._calculate_throughput(),
            last_update_time=self._stats.last_update_time
        )

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._stats = ProcessingStats()
        self._logger.info(f"Reset statistics for stage '{self.name}'")

    def _update_stats(self, success: bool, processing_time: float) -> None:
        """Update processing statistics.

        Args:
            success: Whether processing was successful
            processing_time: Time taken to process the message
        """
        self._stats.last_processing_time = processing_time
        self._stats.processing_time_total += processing_time
        self._stats.last_update_time = time.time()

        if success:
            self._stats.messages_processed += 1
        else:
            self._stats.messages_failed += 1
            self._stats.errors_count += 1

    def _calculate_throughput(self) -> float:
        """Calculate messages processed per second.

        Returns:
            Throughput rate in messages per second
        """
        if self._stats.processing_time_total == 0:
            return 0.0

        total_messages = self._stats.messages_processed + self._stats.messages_failed
        return total_messages / self._stats.processing_time_total

    def _validate_config(self, required_keys: List[str]) -> None:
        """Validate that required configuration keys are present.

        Args:
            required_keys: List of required configuration keys

        Raises:
            ValueError: If required configuration is missing
        """
        missing_keys = [key for key in required_keys if key not in self._config]
        if missing_keys:
            raise ValueError(f"Missing required configuration: {missing_keys}")

