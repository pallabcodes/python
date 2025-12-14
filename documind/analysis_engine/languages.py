"""Language support for DocuMind code analysis."""

import logging
from typing import Dict, List, Optional, Set

from tree_sitter import Language, Parser


class LanguageSupport:
    """Language support utilities for code analysis."""

    def __init__(self):
        """Initialize language support."""
        self.logger = logging.getLogger(__name__)

        # Supported languages
        self.supported_languages = {
            'python': {
                'extensions': ['.py'],
                'entity_types': ['function', 'class', 'method', 'module'],
                'comment_styles': ['#', '"""', "'''"],
            },
            'javascript': {
                'extensions': ['.js', '.jsx'],
                'entity_types': ['function', 'class', 'method', 'arrow_function'],
                'comment_styles': ['//', '/* */'],
            },
            'typescript': {
                'extensions': ['.ts', '.tsx'],
                'entity_types': ['function', 'class', 'method', 'interface', 'type'],
                'comment_styles': ['//', '/* */'],
            },
            'java': {
                'extensions': ['.java'],
                'entity_types': ['class', 'interface', 'method', 'constructor'],
                'comment_styles': ['//', '/* */'],
            },
            'go': {
                'extensions': ['.go'],
                'entity_types': ['function', 'struct', 'interface', 'method'],
                'comment_styles': ['//', '/* */'],
            },
            'rust': {
                'extensions': ['.rs'],
                'entity_types': ['function', 'struct', 'enum', 'trait', 'impl'],
                'comment_styles': ['//', '/* */'],
            },
            'cpp': {
                'extensions': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
                'entity_types': ['function', 'class', 'method', 'struct'],
                'comment_styles': ['//', '/* */'],
            },
        }

        # Tree-sitter parsers (loaded on demand)
        self.parsers = {}

    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.supported_languages.keys())

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in self.supported_languages

    def get_language_extensions(self, language: str) -> List[str]:
        """Get file extensions for a language."""
        if language not in self.supported_languages:
            return []
        return self.supported_languages[language]['extensions']

    def get_entity_types(self, language: str) -> List[str]:
        """Get supported entity types for a language."""
        if language not in self.supported_languages:
            return []
        return self.supported_languages[language]['entity_types']

    def get_comment_styles(self, language: str) -> List[str]:
        """Get comment styles for a language."""
        if language not in self.supported_languages:
            return []
        return self.supported_languages[language]['comment_styles']

    def get_parser(self, language: str) -> Optional[Parser]:
        """Get tree-sitter parser for a language."""
        if language not in self.parsers:
            try:
                # Load tree-sitter language
                lang = self._load_tree_sitter_language(language)
                if lang:
                    parser = Parser()
                    parser.set_language(lang)
                    self.parsers[language] = parser
                    return parser
            except Exception as e:
                self.logger.warning(f"Failed to load parser for {language}: {e}")
                return None

        return self.parsers.get(language)

    def _load_tree_sitter_language(self, language: str) -> Optional[Language]:
        """Load tree-sitter language library."""
        try:
            # Import language-specific modules
            if language == 'python':
                from tree_sitter_python import language
                return language()
            elif language in ['javascript', 'typescript']:
                from tree_sitter_javascript import language as js_lang
                return js_lang()
            elif language == 'java':
                from tree_sitter_java import language
                return language()
            elif language == 'go':
                from tree_sitter_go import language
                return language()
            elif language == 'rust':
                from tree_sitter_rust import language
                return language()
            else:
                self.logger.warning(f"No tree-sitter support for {language}")
                return None
        except ImportError:
            self.logger.warning(f"Tree-sitter language not installed for {language}")
            return None

    def detect_language_from_content(self, content: str, filename: str = "") -> Optional[str]:
        """
        Detect programming language from file content and filename.

        Args:
            content: File content
            filename: Filename (optional)

        Returns:
            Detected language or None
        """
        # First try filename extension
        if filename:
            for lang, config in self.supported_languages.items():
                for ext in config['extensions']:
                    if filename.endswith(ext):
                        return lang

        # Try content-based detection
        content_lower = content.lower().strip()

        # Python indicators
        if any(indicator in content_lower for indicator in ['def ', 'class ', 'import ', 'from ', 'if __name__']):
            return 'python'

        # JavaScript/TypeScript indicators
        if any(indicator in content_lower for indicator in ['function ', 'const ', 'let ', 'var ', '=>', 'console.log']):
            # Check for TypeScript-specific features
            if any(ts_indicator in content_lower for ts_indicator in ['interface ', 'type ', ': string', ': number']):
                return 'typescript'
            return 'javascript'

        # Java indicators
        if any(indicator in content_lower for indicator in ['public class', 'public static void main', 'import java.']):
            return 'java'

        # Go indicators
        if any(indicator in content_lower for indicator in ['func ', 'package main', 'import (']):
            return 'go'

        # Rust indicators
        if any(indicator in content_lower for indicator in ['fn ', 'let mut', 'println!']):
            return 'rust'

        return None

    def extract_docstring(self, content: str, language: str, start_line: int, end_line: int) -> Optional[str]:
        """
        Extract docstring/comment from code entity.

        Args:
            content: Full file content
            language: Programming language
            start_line: Start line of entity
            end_line: End line of entity

        Returns:
            Extracted docstring or None
        """
        lines = content.split('\n')
        comment_styles = self.get_comment_styles(language)

        # Look for docstrings/comments before the entity
        for i in range(max(0, start_line - 10), start_line):
            line = lines[i].strip()

            # Check for docstring starts
            if language == 'python':
                if line.startswith('"""') or line.startswith("'''"):
                    return self._extract_python_docstring(lines, i)
            elif language in ['javascript', 'typescript']:
                if line.startswith('/**') or line.startswith('*'):
                    return self._extract_js_docstring(lines, i)
            elif language == 'java':
                if line.startswith('/**') or line.startswith('*'):
                    return self._extract_java_docstring(lines, i)

        return None

    def _extract_python_docstring(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract Python docstring."""
        start_line = lines[start_idx]
        quote_type = '"""' if start_line.startswith('"""') else "'''"

        docstring_lines = []
        i = start_idx

        # Find closing quote
        while i < len(lines):
            line = lines[i]
            docstring_lines.append(line)

            if line.strip().endswith(quote_type) and len(line.strip()) > len(quote_type):
                break
            elif line.strip() == quote_type and i > start_idx:
                break

            i += 1

        return '\n'.join(docstring_lines).strip()

    def _extract_js_docstring(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract JavaScript/TypeScript JSDoc."""
        if not lines[start_idx].strip().startswith('/**'):
            return None

        docstring_lines = []
        i = start_idx

        while i < len(lines):
            line = lines[i]
            docstring_lines.append(line)

            if line.strip().endswith('*/'):
                break

            i += 1

        return '\n'.join(docstring_lines).strip()

    def _extract_java_docstring(self, lines: List[str], start_idx: int) -> Optional[str]:
        """Extract JavaDoc."""
        return self._extract_js_docstring(lines, start_idx)  # Same format as JSDoc
