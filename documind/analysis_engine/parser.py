"""Code parser using tree-sitter and language-specific parsing."""

import ast
import logging
import re
from typing import Dict, List, Optional, Tuple, Any

from app.core.exceptions import CodeAnalysisError

from .languages import LanguageSupport


class CodeParser:
    """Code parser for extracting entities from source code."""

    def __init__(self):
        """Initialize the code parser."""
        self.logger = logging.getLogger(__name__)
        self.language_support = LanguageSupport()

    async def parse_file(
        self,
        content: str,
        language: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Parse a file and extract code entities.

        Args:
            content: File content
            language: Programming language
            file_path: File path

        Returns:
            List of entity dictionaries
        """
        try:
            if language == 'python':
                return self._parse_python_file(content, file_path)
            elif language in ['javascript', 'typescript']:
                return self._parse_js_file(content, language, file_path)
            elif language == 'java':
                return self._parse_java_file(content, file_path)
            else:
                # Fallback to basic regex-based parsing
                return self._parse_generic_file(content, language, file_path)

        except Exception as e:
            self.logger.warning(f"Failed to parse {file_path}: {e}")
            raise CodeAnalysisError(f"Parsing failed: {e}", language=language, file_path=file_path)

    def _parse_python_file(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Python file using AST."""
        try:
            tree = ast.parse(content, filename=file_path)
            entities = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    entity = self._extract_python_function(node, content)
                    entities.append(entity)
                elif isinstance(node, ast.ClassDef):
                    entity = self._extract_python_class(node, content)
                    entities.append(entity)

            return entities

        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
            return []

    def _extract_python_function(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """Extract function information from AST node."""
        lines = content.split('\n')

        # Get function signature
        signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"

        # Get source code
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 1) - 1
        source_lines = lines[start_line:end_line + 1]
        source_code = '\n'.join(source_lines)

        # Get docstring
        docstring = None
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            docstring = node.body[0].value.s

        # Calculate complexity (simplified)
        complexity = self._calculate_python_complexity(node)

        return {
            'type': 'function',
            'name': node.name,
            'qualified_name': node.name,  # Could be improved with module path
            'signature': signature,
            'source_code': source_code,
            'docstring': docstring,
            'start_line': start_line + 1,
            'end_line': end_line + 1,
            'parameter_count': len(node.args.args),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'complexity': complexity,
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
        }

    def _extract_python_class(self, node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """Extract class information from AST node."""
        lines = content.split('\n')

        # Get class signature
        bases = [self._get_base_name(base) for base in node.bases]
        signature = f"class {node.name}"
        if bases:
            signature += f"({', '.join(bases)})"

        # Get source code
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', start_line + 1) - 1
        source_lines = lines[start_line:end_line + 1]
        source_code = '\n'.join(source_lines)

        # Get docstring
        docstring = None
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            docstring = node.body[0].value.s

        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        return {
            'type': 'class',
            'name': node.name,
            'qualified_name': node.name,
            'signature': signature,
            'source_code': source_code,
            'docstring': docstring,
            'start_line': start_line + 1,
            'end_line': end_line + 1,
            'inheritance': bases,
            'methods': methods,
        }

    def _calculate_python_complexity(self, node: ast.FunctionDef) -> float:
        """Calculate cyclomatic complexity for Python function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, (ast.And, ast.Or)):
                # Count boolean operations
                complexity += len(child.values) - 1

        return complexity

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)

    def _get_base_name(self, base) -> str:
        """Get base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}"
        return str(base)

    def _parse_js_file(self, content: str, language: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse JavaScript/TypeScript file."""
        entities = []

        # Function regex patterns
        function_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)',  # function foo()
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',  # const foo = () =>
            r'(\w+)\s*\([^)]*\)\s*{',  # foo() {
        ]

        # Class pattern
        class_pattern = r'class\s+(\w+)'

        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Check for functions
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    entity = self._extract_js_function(func_name, lines, i, language)
                    if entity:
                        entities.append(entity)
                    break

            # Check for classes
            class_match = re.search(class_pattern, line)
            if class_match:
                class_name = class_match.group(1)
                entity = self._extract_js_class(class_name, lines, i, language)
                if entity:
                    entities.append(entity)

        return entities

    def _extract_js_function(self, name: str, lines: List[str], start_idx: int, language: str) -> Optional[Dict[str, Any]]:
        """Extract JavaScript function information."""
        # Find function boundaries (simplified)
        brace_count = 0
        start_line = start_idx
        end_line = start_idx

        for i in range(start_idx, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')

            if brace_count == 0 and '{' in line:
                end_line = i
                break
            elif i == len(lines) - 1:
                end_line = i

        source_code = '\n'.join(lines[start_line:end_line + 1])

        return {
            'type': 'function',
            'name': name,
            'qualified_name': name,
            'source_code': source_code,
            'start_line': start_line + 1,
            'end_line': end_line + 1,
            'language': language,
        }

    def _extract_js_class(self, name: str, lines: List[str], start_idx: int, language: str) -> Optional[Dict[str, Any]]:
        """Extract JavaScript class information."""
        # Find class boundaries (simplified)
        brace_count = 0
        start_line = start_idx
        end_line = start_idx

        for i in range(start_idx, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')

            if brace_count == 0 and '{' in line:
                end_line = i
                break
            elif i == len(lines) - 1:
                end_line = i

        source_code = '\n'.join(lines[start_line:end_line + 1])

        return {
            'type': 'class',
            'name': name,
            'qualified_name': name,
            'source_code': source_code,
            'start_line': start_line + 1,
            'end_line': end_line + 1,
            'language': language,
        }

    def _parse_java_file(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse Java file."""
        entities = []

        # Class pattern
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?class\s+(\w+)'
        # Interface pattern
        interface_pattern = r'(?:public\s+|private\s+|protected\s+)?interface\s+(\w+)'
        # Method pattern
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:\w+\s+)+\s+(\w+)\s*\([^)]*\)'

        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Check for classes
            class_match = re.search(class_pattern, line)
            if class_match:
                class_name = class_match.group(1)
                entity = self._extract_java_class(class_name, lines, i)
                if entity:
                    entities.append(entity)

            # Check for interfaces
            interface_match = re.search(interface_pattern, line)
            if interface_match:
                interface_name = interface_match.group(1)
                entity = self._extract_java_interface(interface_name, lines, i)
                if entity:
                    entities.append(entity)

            # Check for methods (within classes)
            method_match = re.search(method_pattern, line)
            if method_match and not line.strip().endswith(';'):  # Not abstract method
                method_name = method_match.group(1)
                entity = self._extract_java_method(method_name, lines, i)
                if entity:
                    entities.append(entity)

        return entities

    def _extract_java_class(self, name: str, lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
        """Extract Java class information."""
        return {
            'type': 'class',
            'name': name,
            'qualified_name': name,
            'start_line': start_idx + 1,
            'language': 'java',
        }

    def _extract_java_interface(self, name: str, lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
        """Extract Java interface information."""
        return {
            'type': 'interface',
            'name': name,
            'qualified_name': name,
            'start_line': start_idx + 1,
            'language': 'java',
        }

    def _extract_java_method(self, name: str, lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
        """Extract Java method information."""
        return {
            'type': 'method',
            'name': name,
            'qualified_name': name,
            'start_line': start_idx + 1,
            'language': 'java',
        }

    def _parse_generic_file(self, content: str, language: str, file_path: str) -> List[Dict[str, Any]]:
        """Fallback parser for unsupported languages."""
        # Basic function detection using regex
        function_patterns = [
            r'(?:def|function|func|fn)\s+(\w+)\s*\(',
            r'(\w+)\s*\([^)]*\)\s*{',
        ]

        entities = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern in function_patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    entities.append({
                        'type': 'function',
                        'name': name,
                        'qualified_name': name,
                        'start_line': i + 1,
                        'language': language,
                    })
                    break

        return entities
