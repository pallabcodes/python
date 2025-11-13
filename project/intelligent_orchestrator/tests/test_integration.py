"""Integration tests for orchestrator."""

import unittest
from intelligent_orchestrator.core.orchestrator_factory import OrchestratorFactory


class TestIntegration(unittest.TestCase):
    """Integration test cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = OrchestratorFactory.create()

    def test_end_to_end_optimization(self):
        """Test end-to-end optimization flow."""
        workload = {
            "code": """
def process_items(items):
    results = []
    for item in items:
        result = expensive_operation(item)
        results.append(result)
    return results
""",
            "description": "CPU-bound batch processing"
        }
        result = self.orchestrator.optimize_workload(workload)
        self.assertIsInstance(result, dict)
        self.assertIn("analysis", result)
        self.assertIn("selection", result)
        self.assertIn("result", result)

    def test_multiple_workloads(self):
        """Test optimization of multiple workloads."""
        workloads = [
            {"code": "def cpu(): pass", "description": "CPU task"},
            {"code": "import requests", "description": "IO task"}
        ]
        for workload in workloads:
            result = self.orchestrator.optimize_workload(workload)
            self.assertIsInstance(result, dict)
            self.assertIn("selection", result)


if __name__ == "__main__":
    unittest.main()

