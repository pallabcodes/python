"""Bridge for optimization results."""

from typing import Any, Dict, Optional
import logging


class ResultBridge:
    """Bridge for processing and converting optimization results."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize result bridge.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info("Result bridge initialized")

    def process_result(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process optimization result with context.

        Args:
            result: Optimization result dictionary
            context: Context dictionary

        Returns:
            Processed result dictionary
        """
        try:
            processed = {
                **result,
                "context": context,
                "timestamp": self._get_timestamp(),
                "processed": True
            }
            self._logger.info("Result processing completed")
            return processed
        except Exception as e:
            self._logger.error(f"Result processing failed: {e}")
            return result

    def _get_timestamp(self) -> str:
        """Get current timestamp.

        Returns:
            ISO format timestamp string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()

