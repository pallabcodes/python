"""Unit tests for orchestrator engine."""

import unittest
from intelligent_orchestrator.core.orchestrator_engine import OrchestratorEngine
from intelligent_orchestrator.core.orchestrator_config import OrchestratorConfig


class TestOrchestratorEngine(unittest.TestCase):
    """Test cases for orchestrator engine."""

    def setUp(self):
        """Set up test fixtures."""
        config = OrchestratorConfig(
            enable_learning=False,
            enable_explanations=False
        )
        self.engine = OrchestratorEngine(config=config)

    def test_optimize_workload(self):
        """Test workload optimization."""
        workload = {
            "code": "def process(data): return [x*2 for x in data]",
            "description": "Simple data processing"
        }
        result = self.engine.optimize(workload)
        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)
        self.assertIn("selection", result)

    def test_get_available_strategies(self):
        """Test getting available strategies."""
        strategies = self.engine._get_available_strategies()
        self.assertIsInstance(strategies, list)
        self.assertGreater(len(strategies), 0)

    def test_execute_optimization(self):
        """Test optimization execution."""
        workload = {"code": "pass"}
        selection = {"selected_strategy": "threading"}
        result = self.engine._execute_optimization(workload, selection)
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()

