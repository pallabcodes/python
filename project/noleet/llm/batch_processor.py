"""Batch processing system for efficient API usage during beta testing."""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum


class BatchStrategy(Enum):
    """Batching strategies for different use cases."""
    TIME_WINDOW = "time_window"      # Collect requests over time, batch when full or timeout
    COUNT_BASED = "count_based"      # Batch when reaching specific count
    HYBRID = "hybrid"               # Combine time and count limits
    IMMEDIATE = "immediate"         # No batching, process immediately


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    strategy: BatchStrategy = BatchStrategy.HYBRID
    max_batch_size: int = 5  # Maximum requests per batch
    max_wait_time: float = 30.0  # Maximum seconds to wait before processing
    min_batch_size: int = 1  # Minimum requests to form a batch
    enabled: bool = True  # Whether batching is enabled

    # Advanced settings
    priority_weighting: bool = True  # Prioritize high-quality requests
    adaptive_sizing: bool = True  # Adjust batch size based on API performance
    retry_on_failure: bool = True  # Retry failed batches


@dataclass
class BatchRequest:
    """Individual request in a batch."""
    request_id: str
    prompt: str
    quality_requirement: str
    timestamp: float = field(default_factory=time.time)
    priority: int = 1  # 1=low, 2=medium, 3=high
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Result for a batch request."""
    request_id: str
    response: str
    success: bool
    processing_time: float
    error_message: Optional[str] = None


class BatchProcessor:
    """Processes requests in batches for efficient API usage."""

    def __init__(
        self,
        config: BatchConfig,
        process_batch_func: Callable[[List[BatchRequest]], Awaitable[List[BatchResult]]],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize batch processor.

        Args:
            config: Batch processing configuration
            process_batch_func: Function to process a batch of requests
            logger: Optional logger
        """
        self._config = config
        self._process_batch = process_batch_func
        self._logger = logger or logging.getLogger(__name__)

        # Batch state
        self._pending_requests: List[BatchRequest] = []
        self._batch_start_time: Optional[float] = None
        self._processing_lock = asyncio.Lock()

        # Statistics
        self._stats = {
            "total_requests": 0,
            "batches_processed": 0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0,
            "success_rate": 1.0
        }

    async def submit_request(
        self,
        request_id: str,
        prompt: str,
        quality_requirement: str = "standard",
        priority: int = 1,
        **metadata
    ) -> str:
        """
        Submit a request for batch processing.

        Args:
            request_id: Unique identifier for the request
            prompt: The prompt to process
            quality_requirement: Quality level needed
            priority: Request priority (1-3)
            **metadata: Additional request metadata

        Returns:
            Request ID for tracking
        """
        if not self._config.enabled:
            # If batching disabled, process immediately
            return await self._process_single_request(
                BatchRequest(request_id, prompt, quality_requirement, priority=priority, metadata=metadata)
            )

        request = BatchRequest(
            request_id=request_id,
            prompt=prompt,
            quality_requirement=quality_requirement,
            priority=priority,
            metadata=metadata
        )

        async with self._processing_lock:
            self._pending_requests.append(request)
            self._stats["total_requests"] += 1

            # Initialize batch timing
            if self._batch_start_time is None:
                self._batch_start_time = time.time()

            # Check if we should process the batch
            should_process = self._should_process_batch()

            if should_process:
                await self._process_current_batch()
            else:
                # Schedule processing if we're approaching time limit
                time_remaining = self._config.max_wait_time - (time.time() - self._batch_start_time)
                if time_remaining < 5.0:  # Less than 5 seconds left
                    asyncio.create_task(self._delayed_process_batch(1.0))

        return request_id

    async def _process_single_request(self, request: BatchRequest) -> str:
        """Process a single request immediately (no batching)."""
        try:
            # Wrap single request in batch format
            batch_results = await self._process_batch([request])

            if batch_results and len(batch_results) > 0:
                result = batch_results[0]
                if result.success:
                    self._logger.info(f"Single request {request.request_id} processed successfully")
                    return result.response
                else:
                    self._logger.error(f"Single request {request.request_id} failed: {result.error_message}")
                    return f"Error: {result.error_message}"
            else:
                return "Error: No response generated"

        except Exception as e:
            self._logger.error(f"Single request processing failed: {e}")
            return f"Error: {str(e)}"

    def _should_process_batch(self) -> bool:
        """Determine if the current batch should be processed."""
        if not self._pending_requests:
            return False

        request_count = len(self._pending_requests)
        elapsed_time = time.time() - (self._batch_start_time or time.time())

        # Strategy-specific checks
        if self._config.strategy == BatchStrategy.COUNT_BASED:
            return request_count >= self._config.max_batch_size

        elif self._config.strategy == BatchStrategy.TIME_WINDOW:
            return elapsed_time >= self._config.max_wait_time

        elif self._config.strategy == BatchStrategy.HYBRID:
            # Process if we hit count limit OR time limit
            count_ready = request_count >= self._config.max_batch_size
            time_ready = elapsed_time >= self._config.max_wait_time
            return count_ready or time_ready

        elif self._config.strategy == BatchStrategy.IMMEDIATE:
            return True  # Process immediately

        return False

    async def _delayed_process_batch(self, delay_seconds: float):
        """Process batch after a delay."""
        await asyncio.sleep(delay_seconds)
        async with self._processing_lock:
            if self._pending_requests:  # Still have requests
                await self._process_current_batch()

    async def _process_current_batch(self):
        """Process the current batch of requests."""
        if not self._pending_requests:
            return

        batch_size = len(self._pending_requests)
        start_time = time.time()

        try:
            # Sort by priority if enabled
            if self._config.priority_weighting:
                self._pending_requests.sort(key=lambda r: r.priority, reverse=True)

            # Limit batch size if needed
            batch_requests = self._pending_requests[:self._config.max_batch_size]
            remaining_requests = self._pending_requests[self._config.max_batch_size:]

            self._logger.info(f"Processing batch of {len(batch_requests)} requests")

            # Process the batch
            batch_results = await self._process_batch(batch_requests)

            # Handle results
            await self._handle_batch_results(batch_results, batch_requests)

            # Keep remaining requests for next batch
            self._pending_requests = remaining_requests

            # Reset batch timing
            if self._pending_requests:
                self._batch_start_time = time.time()
            else:
                self._batch_start_time = None

            # Update statistics
            processing_time = time.time() - start_time
            self._update_batch_stats(batch_size, processing_time, batch_results)

        except Exception as e:
            self._logger.error(f"Batch processing failed: {e}")

            # On failure, try to process individual requests if retry enabled
            if self._config.retry_on_failure:
                await self._retry_individual_requests()

    async def _handle_batch_results(self, results: List[BatchResult], requests: List[BatchRequest]):
        """Handle the results of a batch processing operation."""
        result_map = {result.request_id: result for result in results}

        for request in requests:
            result = result_map.get(request.request_id)
            if result:
                if result.success:
                    self._logger.debug(f"Request {request.request_id} completed successfully")
                    # In real implementation, you'd store results for retrieval
                else:
                    self._logger.warning(f"Request {request.request_id} failed: {result.error_message}")
            else:
                self._logger.error(f"No result found for request {request.request_id}")

    async def _retry_individual_requests(self):
        """Retry failed batch by processing individual requests."""
        self._logger.info("Retrying failed batch with individual requests")

        requests_to_retry = self._pending_requests[:]
        self._pending_requests = []

        for request in requests_to_retry:
            try:
                await self._process_single_request(request)
            except Exception as e:
                self._logger.error(f"Individual retry failed for {request.request_id}: {e}")

    def _update_batch_stats(self, batch_size: int, processing_time: float, results: List[BatchResult]):
        """Update batch processing statistics."""
        self._stats["batches_processed"] += 1

        # Update average batch size
        total_batches = self._stats["batches_processed"]
        current_avg = self._stats["average_batch_size"]
        self._stats["average_batch_size"] = (current_avg * (total_batches - 1) + batch_size) / total_batches

        # Update average processing time
        current_time_avg = self._stats["average_processing_time"]
        self._stats["average_processing_time"] = (current_time_avg * (total_batches - 1) + processing_time) / total_batches

        # Update success rate
        successful_results = sum(1 for r in results if r.success)
        batch_success_rate = successful_results / len(results) if results else 1.0
        current_success_rate = self._stats["success_rate"]
        self._stats["success_rate"] = (current_success_rate * (total_batches - 1) + batch_success_rate) / total_batches

    async def flush_pending_requests(self):
        """Force process all pending requests."""
        async with self._processing_lock:
            while self._pending_requests:
                await self._process_current_batch()

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        return {
            **self._stats,
            "pending_requests": len(self._pending_requests),
            "current_batch_age": time.time() - (self._batch_start_time or time.time()),
            "config": {
                "strategy": self._config.strategy.value,
                "max_batch_size": self._config.max_batch_size,
                "max_wait_time": self._config.max_wait_time,
                "enabled": self._config.enabled
            }
        }

    def update_config(self, new_config: BatchConfig):
        """Update batch processing configuration."""
        self._config = new_config
        self._logger.info(f"Updated batch config: {new_config.strategy.value}, size={new_config.max_batch_size}")


class BetaBatchManager:
    """Manages batching specifically for beta testing scenarios."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._processors: Dict[str, BatchProcessor] = {}

        # Default beta configuration - conservative for testing
        self._beta_config = BatchConfig(
            strategy=BatchStrategy.HYBRID,
            max_batch_size=3,  # Small batches for beta
            max_wait_time=15.0,  # Quick processing for user experience
            min_batch_size=1,
            enabled=True
        )

    def create_beta_processor(
        self,
        name: str,
        process_function: Callable[[List[BatchRequest]], Awaitable[List[BatchResult]]]
    ) -> BatchProcessor:
        """
        Create a batch processor optimized for beta testing.

        Args:
            name: Processor name (e.g., 'recommendations', 'analysis')
            process_function: Function to process batches

        Returns:
            Configured batch processor
        """
        processor = BatchProcessor(self._beta_config, process_function, self._logger)
        self._processors[name] = processor
        self._logger.info(f"Created beta batch processor: {name}")
        return processor

    def get_processor(self, name: str) -> Optional[BatchProcessor]:
        """Get a batch processor by name."""
        return self._processors.get(name)

    def enable_aggressive_batching(self):
        """Enable aggressive batching for maximum API efficiency."""
        self._beta_config = BatchConfig(
            strategy=BatchStrategy.HYBRID,
            max_batch_size=10,  # Larger batches
            max_wait_time=60.0,  # Wait longer to fill batches
            min_batch_size=1,
            enabled=True
        )
        self._update_all_processors()

    def disable_batching(self):
        """Disable batching for immediate processing."""
        self._beta_config = BatchConfig(
            strategy=BatchStrategy.IMMEDIATE,
            max_batch_size=1,
            max_wait_time=0.0,
            enabled=False
        )
        self._update_all_processors()

    def _update_all_processors(self):
        """Update configuration for all processors."""
        for processor in self._processors.values():
            processor.update_config(self._beta_config)

    async def flush_all_processors(self):
        """Flush all pending requests across all processors."""
        for name, processor in self._processors.items():
            self._logger.info(f"Flushing processor: {name}")
            await processor.flush_pending_requests()

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all processors."""
        return {
            processor_name: processor.get_stats()
            for processor_name, processor in self._processors.items()
        }
