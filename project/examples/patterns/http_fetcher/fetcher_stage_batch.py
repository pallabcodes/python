"""
Batch HTTP fetcher stage implementation.

This module contains the BatchHttpFetcherStage for concurrent
HTTP request processing with concurrency control.
"""

from typing import Any, Dict, Optional, List

from ..pipeline_core.stage_types import TransformStage


class BatchHttpFetcherStage(TransformStage):
    """Pipeline stage for batch HTTP fetching with concurrency control."""

    def __init__(
        self,
        name: str,
        max_concurrent: int = 5,
        **kwargs
    ):
        """Initialize batch HTTP fetcher stage.

        Args:
            name: Stage name
            max_concurrent: Maximum concurrent requests
            **kwargs: Arguments passed to HttpFetcherStage
        """
        super().__init__(name)
        self.max_concurrent = max_concurrent
        self.fetcher_kwargs = kwargs

        # Will be initialized in on_initialize
        self._fetcher_stage = None

    def on_initialize(self) -> None:
        """Initialize the underlying fetcher stage."""
        # Import here to avoid circular imports
        from .fetcher_stage_core import HttpFetcherStage

        self._fetcher_stage = HttpFetcherStage(
            name=f"{self.name}_worker",
            **self.fetcher_kwargs
        )
        self._fetcher_stage.initialize()

    def transform(self, data: Any) -> Any:
        """Process batch of HTTP requests.

        Args:
            data: List of request parameters or single request

        Returns:
            List of responses or single response
        """
        if not isinstance(data, list):
            # Single request
            return self._fetcher_stage.transform(data)

        # Batch requests with concurrency control
        results = []

        # Process in chunks to control concurrency
        for i in range(0, len(data), self.max_concurrent):
            chunk = data[i:i + self.max_concurrent]

            # For now, process sequentially (could be enhanced with ThreadPoolExecutor)
            chunk_results = []
            for request in chunk:
                result = self._fetcher_stage.transform(request)
                chunk_results.append(result)

            results.extend(chunk_results)

        return results

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._fetcher_stage:
            self._fetcher_stage.cleanup()
        super().cleanup()

    def get_stats(self) -> Dict[str, Any]:
        """Get batch fetcher statistics."""
        base_stats = {
            "stage_name": self.name,
            "max_concurrent": self.max_concurrent
        }

        if self._fetcher_stage:
            base_stats.update(self._fetcher_stage.get_stats())

        return base_stats

