"""AST-based code analysis for workload characterization."""

import ast
from typing import Any, Dict, List, Optional
import logging


class CodeAnalyzer:
    """Analyze code using AST parsing to determine workload characteristics."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize code analyzer.

        Args:
            logger: Optional logger instance
        """
        self._logger = logger or logging.getLogger(__name__)
        self._logger.info("Code analyzer initialized")

    def analyze(self, code: str) -> Dict[str, Any]:
        """Analyze code to extract workload characteristics.

        Args:
            code: Python code string

        Returns:
            Analysis dictionary with characteristics
        """
        try:
            tree = ast.parse(code)
            characteristics = self._extract_characteristics(tree)
            self._logger.info("Code analysis completed")
            return characteristics
        except SyntaxError as e:
            self._logger.error(f"Syntax error in code: {e}")
            return self._default_characteristics()
        except Exception as e:
            self._logger.error(f"Code analysis failed: {e}")
            return self._default_characteristics()

    def _extract_characteristics(self, tree: ast.AST) -> Dict[str, Any]:
        """Extract characteristics from AST.

        Args:
            tree: Parsed AST

        Returns:
            Characteristics dictionary
        """
        visitor = WorkloadCharacteristicVisitor()
        visitor.visit(tree)
        return visitor.get_characteristics()

    def _default_characteristics(self) -> Dict[str, Any]:
        """Return default characteristics when analysis fails.

        Returns:
            Default characteristics dictionary
        """
        return {
            "bound_type": "unknown",
            "io_operations": False,
            "cpu_intensive": False,
            "has_loops": False,
            "has_async": False
        }


class WorkloadCharacteristicVisitor(ast.NodeVisitor):
    """AST visitor for extracting workload characteristics."""

    def __init__(self):
        """Initialize visitor."""
        self.io_operations = False
        self.cpu_intensive = False
        self.has_loops = False
        self.has_async = False
        self.function_calls = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.function_calls.append(func_name)
            if func_name in ["open", "read", "write", "request", "fetch"]:
                self.io_operations = True
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Visit for loop nodes."""
        self.has_loops = True
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Visit while loop nodes."""
        self.has_loops = True
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes."""
        self.has_async = True
        self.generic_visit(node)

    def visit_Await(self, node: ast.Await) -> None:
        """Visit await nodes."""
        self.has_async = True
        self.generic_visit(node)

    def get_characteristics(self) -> Dict[str, Any]:
        """Get extracted characteristics.

        Returns:
            Characteristics dictionary
        """
        bound_type = "io_bound" if self.io_operations else "cpu_bound"
        if self.has_async:
            bound_type = "io_bound"
        return {
            "bound_type": bound_type,
            "io_operations": self.io_operations,
            "cpu_intensive": not self.io_operations and self.has_loops,
            "has_loops": self.has_loops,
            "has_async": self.has_async,
            "function_calls": self.function_calls
        }

