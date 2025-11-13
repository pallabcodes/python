"""Bridge between LLM and concurrency framework."""

from typing import Any, Dict, Optional
import logging

from .framework_adapter import FrameworkAdapter


class WorkloadBridge:
    """Bridge for converting between LLM and framework formats."""

    def __init__(
        self,
        framework_adapter: Optional[FrameworkAdapter] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize workload bridge.

        Args:
            framework_adapter: Framework adapter instance
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._adapter = framework_adapter or FrameworkAdapter(logger=logger)
        self._logger.info("Workload bridge initialized")

    def convert_llm_to_framework(
        self,
        llm_workload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert LLM workload format to framework format.

        Args:
            llm_workload: LLM workload dictionary

        Returns:
            Framework-compatible workload dictionary
        """
        try:
            framework_workload = {
                "code": llm_workload.get("code", ""),
                "description": llm_workload.get("description", ""),
                "metadata": llm_workload.get("metadata", {})
            }
            self._logger.debug("Converted LLM workload to framework format")
            return framework_workload
        except Exception as e:
            self._logger.error(f"Conversion failed: {e}")
            return {}

    def convert_framework_to_llm(
        self,
        framework_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert framework result format to LLM format.

        Args:
            framework_result: Framework result dictionary

        Returns:
            LLM-compatible result dictionary
        """
        try:
            llm_result = {
                "strategy": framework_result.get("strategy", "unknown"),
                "performance": framework_result.get("performance", {}),
                "metadata": framework_result.get("metadata", {})
            }
            self._logger.debug("Converted framework result to LLM format")
            return llm_result
        except Exception as e:
            self._logger.error(f"Conversion failed: {e}")
            return {}

