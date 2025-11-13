"""CRDTs for distributed LLM state."""

from typing import Any, Dict, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../adaptive_concurrency_framework"))

try:
    from adaptive_concurrency_framework.coordination.crdt_state import CRDTState
    HAS_RESEARCH = True
except ImportError:
    HAS_RESEARCH = False
    CRDTState = None


class CRDTLLMState:
    """CRDT-based state management for distributed LLM operations."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize CRDT state manager.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._crdt: Optional[Any] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize CRDT state."""
        if HAS_RESEARCH and CRDTState:
            try:
                self._crdt = CRDTState()
                self._logger.info("CRDT state for LLM initialized")
            except Exception as e:
                self._logger.error(f"Failed to initialize CRDT: {e}")

    def update_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Update distributed state using CRDT.

        Args:
            state: State dictionary

        Returns:
            Merged state dictionary
        """
        if not self._crdt:
            return state
        try:
            merged = self._crdt.merge(state)
            self._logger.info("State updated using CRDT")
            return merged
        except Exception as e:
            self._logger.error(f"State update failed: {e}")
            return state

