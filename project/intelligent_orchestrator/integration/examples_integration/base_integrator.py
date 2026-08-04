"""
Base Abstract Integrator Interface for Intelligent Orchestrator.
Target: Google L6/L7 Systems Architecture Quality Bar.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseIntegrator(ABC):
    """Abstract Base Contract for all Execution Strategy Integrators.

    Enforces static interface contracts for dynamic strategy registration
    and technique introspection across Threading, Multiprocessing, AsyncIO,
    and Hybrid execution engines.
    """

    @abstractmethod
    def get_available_techniques(self) -> List[str]:
        """Get list of available concurrency/parallelism techniques.

        Returns:
            List of supported technique names.
        """
        pass

    @abstractmethod
    def create_strategy(
        self,
        technique: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an execution strategy dictionary from technique configuration.

        Args:
            technique: Target technique identifier name.
            config: Execution configuration dictionary.

        Returns:
            Strategy descriptor dictionary.

        Raises:
            ValueError: If technique is unsupported or config is invalid.
        """
        pass
