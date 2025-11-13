"""Unit tests for workload analyzer."""

import unittest
from intelligent_orchestrator.intelligence.workload_analyzer_llm.workload_analyzer_llm import WorkloadAnalyzerLLM


class TestWorkloadAnalyzer(unittest.TestCase):
    """Test cases for workload analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = WorkloadAnalyzerLLM()

    def test_analyze_cpu_workload(self):
        """Test analysis of CPU-bound workload."""
        workload = {
            "code": "def compute(n): return sum(i*i for i in range(n))",
            "description": "CPU-intensive computation"
        }
        result = self.analyzer.analyze(workload)
        self.assertIsInstance(result, dict)
        self.assertIn("bound_type", result)

    def test_analyze_io_workload(self):
        """Test analysis of I/O-bound workload."""
        workload = {
            "code": "import requests; requests.get('http://example.com')",
            "description": "I/O-bound HTTP request"
        }
        result = self.analyzer.analyze(workload)
        self.assertIsInstance(result, dict)
        self.assertIn("bound_type", result)

    def test_analyze_empty_workload(self):
        """Test analysis of empty workload."""
        workload = {}
        result = self.analyzer.analyze(workload)
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()

