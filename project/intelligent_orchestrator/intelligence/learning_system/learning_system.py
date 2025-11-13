"""Main adaptive learning system."""

from typing import Any, Dict, Optional
import logging

from .pattern_learner import PatternLearner
from .feedback_processor import FeedbackProcessor
from .few_shot_learner import FewShotLearner


class LearningSystem:
    """Main learning system combining multiple learning methods."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize learning system.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._pattern_learner = PatternLearner(logger=logger)
        self._feedback_processor = FeedbackProcessor(logger=logger)
        self._few_shot_learner = FewShotLearner(logger=logger)
        self._logger.info("Learning system initialized")

    def learn_from_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from optimization results.

        Args:
            results: Optimization results dictionary

        Returns:
            Learning insights dictionary
        """
        try:
            patterns = self._pattern_learner.learn(results)
            feedback = self._feedback_processor.process(results)
            combined = self._combine_learning(patterns, feedback)
            self._logger.info("Learning from results completed")
            return combined
        except Exception as e:
            self._logger.error(f"Learning failed: {e}")
            return {}

    def _combine_learning(
        self,
        patterns: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine learning from multiple sources.

        Args:
            patterns: Pattern learning results
            feedback: Feedback processing results

        Returns:
            Combined learning dictionary
        """
        return {
            "patterns": patterns,
            "feedback": feedback,
            "insights": []
        }

