"""Unit tests for strategy selector."""

import unittest
from intelligent_orchestrator.intelligence.strategy_selector_llm.strategy_selector_llm import StrategySelectorLLM


class TestStrategySelector(unittest.TestCase):
    """Test cases for strategy selector."""

    def setUp(self):
        """Set up test fixtures."""
        self.selector = StrategySelectorLLM()

    def test_select_strategy(self):
        """Test strategy selection."""
        analysis = {
            "bound_type": "io_bound",
            "has_async": True
        }
        strategies = ["threading", "asyncio", "multiprocessing"]
        result = self.selector.select(analysis, strategies)
        self.assertIsInstance(result, dict)
        self.assertIn("selected_strategy", result)

    def test_select_with_empty_strategies(self):
        """Test selection with empty strategies list."""
        analysis = {"bound_type": "unknown"}
        strategies = []
        result = self.selector.select(analysis, strategies)
        self.assertIsInstance(result, dict)

    def test_select_with_tradeoffs(self):
        """Test selection with trade-off analysis."""
        analysis = {
            "bound_type": "cpu_bound",
            "cpu_intensive": True
        }
        strategies = ["multiprocessing", "threading"]
        result = self.selector.select(analysis, strategies)
        self.assertIsInstance(result, dict)
        self.assertIn("tradeoffs", result)


if __name__ == "__main__":
    unittest.main()

