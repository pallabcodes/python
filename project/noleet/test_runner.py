#!/usr/bin/env python3
"""
Comprehensive test runner for NoLeet production readiness.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Comprehensive test runner for NoLeet."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}

    def run_command(self, cmd: List[str], cwd: Path = None) -> Dict[str, Any]:
        """Run a command and return results."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout after 300 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "returncode": -1,
                "stdout": "",
                "stderr": ""
            }

    def install_test_dependencies(self) -> bool:
        """Install test dependencies."""
        print("📦 Installing test dependencies...")
        cmd = [sys.executable, "-m", "pip", "install", "-q", "-r", "test-requirements.txt"]
        result = self.run_command(cmd)

        if result["success"]:
            print("✅ Test dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install test dependencies: {result['stderr']}")
            return False

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running unit tests...")

        # Check if pytest is available
        try:
            import pytest
        except ImportError:
            return {"success": False, "error": "pytest not available"}

        # Run unit tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "--cov=noleet",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=85"
        ]

        result = self.run_command(cmd)
        self.test_results["unit_tests"] = result

        if result["success"]:
            print("✅ Unit tests passed")
        else:
            print(f"❌ Unit tests failed: {result['stderr']}")

        return result

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running integration tests...")

        try:
            import pytest
        except ImportError:
            return {"success": False, "error": "pytest not available"}

        # Run integration tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "-x"  # Stop on first failure
        ]

        result = self.run_command(cmd)
        self.test_results["integration_tests"] = result

        if result["success"]:
            print("✅ Integration tests passed")
        else:
            print(f"❌ Integration tests failed: {result['stderr']}")

        return result

    def run_end_to_end_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests."""
        print("🌐 Running end-to-end tests...")

        try:
            import pytest
        except ImportError:
            return {"success": False, "error": "pytest not available"}

        # Run E2E tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/e2e/",
            "-v",
            "--tb=short",
            "-x"  # Stop on first failure
        ]

        result = self.run_command(cmd)
        self.test_results["e2e_tests"] = result

        if result["success"]:
            print("✅ End-to-end tests passed")
        else:
            print(f"❌ End-to-end tests failed: {result['stderr']}")

        return result

    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests."""
        print("🔒 Running security tests...")

        results = {}

        # Run bandit for security issues
        try:
            import bandit
            cmd = [sys.executable, "-m", "bandit", "-r", "noleet/", "-f", "json"]
            result = self.run_command(cmd)
            results["bandit"] = result

            if result["success"]:
                print("✅ Security scan passed")
            else:
                print(f"⚠️  Security issues found: {result['stderr']}")

        except ImportError:
            results["bandit"] = {"success": False, "error": "bandit not available"}

        # Run safety for dependency vulnerabilities
        try:
            cmd = [sys.executable, "-m", "safety", "check", "--json"]
            result = self.run_command(cmd)
            results["safety"] = result

            if result["success"]:
                print("✅ Dependency security check passed")
            else:
                print(f"⚠️  Dependency vulnerabilities found: {result['stderr']}")

        except ImportError:
            results["safety"] = {"success": False, "error": "safety not available"}

        self.test_results["security_tests"] = results
        return results

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        print("⚡ Running performance tests...")

        try:
            import pytest
        except ImportError:
            return {"success": False, "error": "pytest not available"}

        # Run performance tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "-v",
            "--tb=short",
            "--benchmark-only",
            "--benchmark-autosave"
        ]

        result = self.run_command(cmd)
        self.test_results["performance_tests"] = result

        if result["success"]:
            print("✅ Performance tests completed")
        else:
            print(f"⚠️  Performance tests had issues: {result['stderr']}")

        return result

    def run_code_quality_checks(self) -> Dict[str, Any]:
        """Run code quality checks."""
        print("🏗️  Running code quality checks...")

        results = {}

        # Run black for formatting check
        try:
            cmd = [sys.executable, "-m", "black", "--check", "--diff", "noleet/"]
            result = self.run_command(cmd)
            results["black"] = result

            if result["success"]:
                print("✅ Code formatting is correct")
            else:
                print(f"❌ Code formatting issues: {result['stdout']}")

        except ImportError:
            results["black"] = {"success": False, "error": "black not available"}

        # Run isort for import sorting
        try:
            cmd = [sys.executable, "-m", "isort", "--check-only", "--diff", "noleet/"]
            result = self.run_command(cmd)
            results["isort"] = result

            if result["success"]:
                print("✅ Import sorting is correct")
            else:
                print(f"❌ Import sorting issues: {result['stdout']}")

        except ImportError:
            results["isort"] = {"success": False, "error": "isort not available"}

        # Run flake8 for linting
        try:
            cmd = [sys.executable, "-m", "flake8", "noleet/"]
            result = self.run_command(cmd)
            results["flake8"] = result

            if result["success"]:
                print("✅ Linting passed")
            else:
                print(f"❌ Linting issues: {result['stdout']}")

        except ImportError:
            results["flake8"] = {"success": False, "error": "flake8 not available"}

        # Run mypy for type checking
        try:
            cmd = [sys.executable, "-m", "mypy", "noleet/"]
            result = self.run_command(cmd)
            results["mypy"] = result

            if result["success"]:
                print("✅ Type checking passed")
            else:
                print(f"⚠️  Type checking issues: {result['stdout']}")

        except ImportError:
            results["mypy"] = {"success": False, "error": "mypy not available"}

        self.test_results["code_quality"] = results
        return results

    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report."""
        print("📊 Generating coverage report...")

        try:
            import coverage

            cmd = [sys.executable, "-m", "coverage", "html"]
            result = self.run_command(cmd)

            if result["success"]:
                print("✅ Coverage report generated at htmlcov/index.html")
                return {"success": True, "report_path": "htmlcov/index.html"}
            else:
                print(f"❌ Failed to generate coverage report: {result['stderr']}")
                return {"success": False, "error": result['stderr']}

        except ImportError:
            print("⚠️  Coverage module not available")
            return {"success": False, "error": "coverage not available"}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        print("🚀 Starting comprehensive test suite...")
        print("=" * 60)

        # Install dependencies
        if not self.install_test_dependencies():
            return {"success": False, "error": "Failed to install dependencies"}

        # Run test suites
        test_suites = [
            ("unit_tests", self.run_unit_tests),
            ("integration_tests", self.run_integration_tests),
            ("e2e_tests", self.run_end_to_end_tests),
            ("security_tests", self.run_security_tests),
            ("performance_tests", self.run_performance_tests),
            ("code_quality", self.run_code_quality_checks)
        ]

        overall_success = True
        results_summary = {}

        for suite_name, test_function in test_suites:
            try:
                result = test_function()
                results_summary[suite_name] = result
                if not result.get("success", False):
                    overall_success = False
            except Exception as e:
                results_summary[suite_name] = {"success": False, "error": str(e)}
                overall_success = False

        # Generate coverage report
        coverage_result = self.generate_coverage_report()
        results_summary["coverage"] = coverage_result

        # Final summary
        print("\n" + "=" * 60)
        print("📋 TEST SUITE SUMMARY")
        print("=" * 60)

        for suite_name, result in results_summary.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            print("15")

        print("\n🏆 OVERALL RESULT:", "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED")

        return {
            "success": overall_success,
            "results": results_summary
        }

    def run_specific_test(self, test_type: str) -> Dict[str, Any]:
        """Run a specific test type."""
        test_functions = {
            "unit": self.run_unit_tests,
            "integration": self.run_integration_tests,
            "e2e": self.run_end_to_end_tests,
            "security": self.run_security_tests,
            "performance": self.run_performance_tests,
            "quality": self.run_code_quality_checks,
            "all": self.run_all_tests
        }

        if test_type not in test_functions:
            return {"success": False, "error": f"Unknown test type: {test_type}"}

        return test_functions[test_type]()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NoLeet Test Runner")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "e2e", "security", "performance", "quality", "all"],
        default="all",
        nargs="?",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="Skip dependency installation"
    )

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent

    # Initialize test runner
    runner = TestRunner(project_root)

    # Install dependencies unless skipped
    if not args.no_deps and args.test_type == "all":
        if not runner.install_test_dependencies():
            sys.exit(1)

    # Run tests
    result = runner.run_specific_test(args.test_type)

    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
