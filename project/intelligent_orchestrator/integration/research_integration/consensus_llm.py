"""Consensus for multi-LLM coordination."""

from typing import Any, Dict, List, Optional
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../adaptive_concurrency_framework"))

try:
    from adaptive_concurrency_framework.coordination.consensus import ConsensusProtocol
    HAS_RESEARCH = True
except ImportError:
    HAS_RESEARCH = False
    ConsensusProtocol = None


class ConsensusLLM:
    """Consensus protocol for coordinating multiple LLM agents."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize consensus protocol.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._consensus: Optional[Any] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize consensus protocol."""
        if HAS_RESEARCH and ConsensusProtocol:
            try:
                self._consensus = ConsensusProtocol()
                self._logger.info("Consensus protocol for LLM initialized")
            except Exception as e:
                self._logger.error(f"Failed to initialize consensus: {e}")

    def reach_consensus(
        self,
        proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Reach consensus among multiple LLM proposals.

        Args:
            proposals: List of proposal dictionaries

        Returns:
            Consensus result dictionary
        """
        if not self._consensus:
            return proposals[0] if proposals else {}
        try:
            consensus = self._consensus.reach_consensus(proposals)
            self._logger.info("Consensus reached among LLM agents")
            return consensus
        except Exception as e:
            self._logger.error(f"Consensus failed: {e}")
            return proposals[0] if proposals else {}

