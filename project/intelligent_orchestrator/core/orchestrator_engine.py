"""Main orchestrator engine."""

from typing import Any, Dict, Optional
import logging

from .orchestrator_config import OrchestratorConfig
from .orchestrator_logger import setup_logger
from ..intelligence.workload_analyzer_llm.workload_analyzer_llm import WorkloadAnalyzerLLM
from ..intelligence.strategy_selector_llm.strategy_selector_llm import StrategySelectorLLM
from ..intelligence.learning_system.learning_system import LearningSystem
from ..intelligence.explainability.decision_explainer import DecisionExplainer
from ..integration.concurrency_adapter.framework_adapter import FrameworkAdapter


class OrchestratorEngine:
    """Main orchestrator engine coordinating all components."""

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize orchestrator engine.

        Args:
            config: Orchestrator configuration
            logger: Optional logger instance
        """
        self._config = config or OrchestratorConfig.from_env()
        self._logger = logger or setup_logger(__name__, self._config.log_level)
        self._workload_analyzer = WorkloadAnalyzerLLM(logger=self._logger)
        self._strategy_selector = StrategySelectorLLM(logger=self._logger)
        self._learning_system = LearningSystem(logger=self._logger)
        self._explainer = DecisionExplainer(logger=self._logger)
        self._framework_adapter = FrameworkAdapter(logger=self._logger)
        self._logger.info("Orchestrator engine initialized")

    def optimize(self, workload: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workload using intelligent orchestration.

        Args:
            workload: Workload dictionary

        Returns:
            Optimization result dictionary
        """
        try:
            analysis = self._workload_analyzer.analyze(workload)
            strategies = self._get_available_strategies()
            selection = self._strategy_selector.select(analysis, strategies)
            result = self._execute_optimization(workload, selection)
            if self._config.enable_learning:
                self._learning_system.learn_from_results(result)
            explanation = None
            if self._config.enable_explanations:
                explanation = self._explainer.explain(selection)
            return {
                "analysis": analysis,
                "selection": selection,
                "result": result,
                "explanation": explanation
            }
        except Exception as e:
            self._logger.error(f"Optimization failed: {e}")
            return {"error": str(e)}

    def _get_available_strategies(self) -> list:
        """Get list of available strategies.

        Returns:
            List of strategy names
        """
        return ["threading", "multiprocessing", "asyncio", "hybrid"]

    def _execute_optimization(
        self,
        workload: Dict[str, Any],
        selection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute optimization using selected strategy.

        Args:
            workload: Workload dictionary
            selection: Strategy selection dictionary

        Returns:
            Optimization result dictionary
        """
        strategy = selection.get("selected_strategy", "unknown")
        return self._framework_adapter.optimize(workload, strategy)

