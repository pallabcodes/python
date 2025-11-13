"""Few-shot learning from examples."""

from typing import Any, Dict, List, Optional
import logging


class FewShotLearner:
    """Learn from few-shot examples."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize few-shot learner.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._examples: List[Dict[str, Any]] = []
        self._logger.info("Few-shot learner initialized")

    def add_example(self, example: Dict[str, Any]) -> None:
        """Add example to learning set.

        Args:
            example: Example dictionary with input and output
        """
        self._examples.append(example)
        self._logger.debug(f"Added example: {len(self._examples)} examples")

    def learn_from_examples(
        self,
        query: Dict[str, Any],
        k: int = 3
    ) -> Dict[str, Any]:
        """Learn from k similar examples.

        Args:
            query: Query dictionary
            k: Number of examples to use

        Returns:
            Learned result dictionary
        """
        try:
            similar = self._find_similar_examples(query, k)
            result = self._infer_from_examples(similar, query)
            self._logger.info(f"Learned from {len(similar)} examples")
            return result
        except Exception as e:
            self._logger.error(f"Few-shot learning failed: {e}")
            return {}

    def _find_similar_examples(
        self,
        query: Dict[str, Any],
        k: int
    ) -> List[Dict[str, Any]]:
        """Find k most similar examples.

        Args:
            query: Query dictionary
            k: Number of examples

        Returns:
            List of similar examples
        """
        return self._examples[:k]

    def _infer_from_examples(
        self,
        examples: List[Dict[str, Any]],
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Infer result from examples.

        Args:
            examples: Similar examples
            query: Query dictionary

        Returns:
            Inferred result dictionary
        """
        if not examples:
            return {}
        return {
            "inferred_strategy": examples[0].get("output", {}).get("strategy", "unknown"),
            "based_on_examples": len(examples)
        }

