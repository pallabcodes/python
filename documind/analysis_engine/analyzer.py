"""Main code analyzer for DocuMind."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from app.core.exceptions import CodeAnalysisError
from app.models.code_entity import CodeEntity
from app.models.repository import Repository

from .languages import LanguageSupport
from .parser import CodeParser


class CodeAnalyzer:
    """Main code analyzer that orchestrates codebase analysis."""

    def __init__(self):
        """Initialize the code analyzer."""
        self.logger = logging.getLogger(__name__)
        self.language_support = LanguageSupport()
        self.parser = CodeParser()

        # Supported file extensions
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
        }

        # Files and patterns to ignore
        self.ignore_patterns = {
            '__pycache__',
            '.git',
            '.svn',
            '.hg',
            'node_modules',
            'venv',
            'env',
            '.env',
            'dist',
            'build',
            '*.pyc',
            '*.pyo',
            '*.min.js',
            '*.min.css',
        }

    async def analyze_repository(
        self,
        repo_path: str,
        repository: Repository,
        config: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Analyze an entire repository.

        Args:
            repo_path: Path to the repository
            repository: Repository model instance
            config: Analysis configuration

        Returns:
            Analysis results dictionary
        """
        try:
            self.logger.info(f"Starting analysis of repository: {repository.full_name}")

            config = config or {}
            repo_path = Path(repo_path)

            if not repo_path.exists():
                raise CodeAnalysisError(f"Repository path does not exist: {repo_path}")

            # Discover all source files
            source_files = await self._discover_source_files(repo_path, config.get('ignore_patterns', []))
            self.logger.info(f"Found {len(source_files)} source files to analyze")

            # Analyze each file
            all_entities = []
            file_results = []

            for file_path in source_files:
                try:
                    entities = await self._analyze_file(file_path, repo_path, repository)
                    all_entities.extend(entities)
                    file_results.append({
                        'file_path': str(file_path.relative_to(repo_path)),
                        'entities_found': len(entities),
                        'language': self._detect_language(file_path),
                        'status': 'success'
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")
                    file_results.append({
                        'file_path': str(file_path.relative_to(repo_path)),
                        'entities_found': 0,
                        'language': self._detect_language(file_path),
                        'status': 'error',
                        'error': str(e)
                    })

            # Generate analysis summary
            summary = await self._generate_analysis_summary(all_entities, source_files, repository)

            result = {
                'repository_id': repository.id,
                'files_analyzed': len(source_files),
                'entities_found': len(all_entities),
                'languages_detected': list(set(r['language'] for r in file_results if r['language'])),
                'file_results': file_results,
                'summary': summary,
                'entities': all_entities,
            }

            self.logger.info(f"Analysis completed: {len(all_entities)} entities found in {len(source_files)} files")
            return result

        except Exception as e:
            self.logger.error(f"Analysis failed for repository {repository.full_name}: {e}")
            raise CodeAnalysisError(f"Repository analysis failed: {e}")

    async def analyze_file(
        self,
        file_path: str,
        repository: Repository,
        config: Optional[Dict] = None
    ) -> List[CodeEntity]:
        """
        Analyze a single file.

        Args:
            file_path: Path to the file
            repository: Repository model instance
            config: Analysis configuration

        Returns:
            List of CodeEntity objects
        """
        file_path = Path(file_path)
        return await self._analyze_file(file_path, file_path.parent, repository)

    async def _analyze_file(
        self,
        file_path: Path,
        repo_root: Path,
        repository: Repository
    ) -> List[CodeEntity]:
        """Analyze a single file and return code entities."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                return []

            # Detect language
            language = self._detect_language(file_path)
            if not language:
                return []

            # Parse the file
            entities_data = await self.parser.parse_file(content, language, str(file_path))

            # Convert to CodeEntity objects
            entities = []
            for entity_data in entities_data:
                entity = CodeEntity(
                    repository_id=repository.id,
                    entity_type=entity_data.get('type', 'unknown'),
                    name=entity_data.get('name', ''),
                    qualified_name=entity_data.get('qualified_name', ''),
                    file_path=str(file_path.relative_to(repo_root)),
                    start_line=entity_data.get('start_line', 0),
                    end_line=entity_data.get('end_line'),
                    start_column=entity_data.get('start_column'),
                    end_column=entity_data.get('end_column'),
                    source_code=entity_data.get('source_code'),
                    signature=entity_data.get('signature'),
                    docstring=entity_data.get('docstring'),
                    language=language,
                    complexity_score=entity_data.get('complexity'),
                    parameter_count=entity_data.get('parameter_count'),
                    return_type=entity_data.get('return_type'),
                    is_async=entity_data.get('is_async'),
                    dependencies=entity_data.get('dependencies', []),
                    visibility=entity_data.get('visibility'),
                    decorators=entity_data.get('decorators', []),
                )
                entities.append(entity)

            return entities

        except Exception as e:
            self.logger.warning(f"Failed to analyze file {file_path}: {e}")
            raise CodeAnalysisError(f"File analysis failed: {e}", file_path=str(file_path))

    async def _discover_source_files(self, repo_path: Path, ignore_patterns: List[str] = None) -> List[Path]:
        """Discover all source files in the repository."""
        ignore_patterns = ignore_patterns or []
        all_ignore_patterns = self.ignore_patterns.union(set(ignore_patterns))

        source_files = []

        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d, all_ignore_patterns)]

            for file in files:
                file_path = Path(root) / file

                # Skip ignored files
                if self._should_ignore(file, all_ignore_patterns):
                    continue

                # Check if it's a supported source file
                if file_path.suffix.lower() in self.supported_extensions:
                    source_files.append(file_path)

        return source_files

    def _should_ignore(self, name: str, ignore_patterns: Set[str]) -> bool:
        """Check if a file or directory should be ignored."""
        for pattern in ignore_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in name:
                return True
        return False

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect the programming language of a file."""
        extension = file_path.suffix.lower()
        return self.supported_extensions.get(extension)

    async def _generate_analysis_summary(
        self,
        entities: List[CodeEntity],
        source_files: List[Path],
        repository: Repository
    ) -> Dict[str, any]:
        """Generate analysis summary statistics."""
        if not entities:
            return {
                'total_entities': 0,
                'entity_types': {},
                'languages': {},
                'complexity_stats': {},
                'documentation_stats': {},
            }

        # Count entity types
        entity_types = {}
        for entity in entities:
            entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1

        # Language distribution
        languages = {}
        for entity in entities:
            languages[entity.language] = languages.get(entity.language, 0) + 1

        # Complexity statistics
        complexities = [e.complexity_score for e in entities if e.complexity_score is not None]
        complexity_stats = {
            'average': sum(complexities) / len(complexities) if complexities else 0,
            'max': max(complexities) if complexities else 0,
            'min': min(complexities) if complexities else 0,
            'high_complexity_count': len([c for c in complexities if c and c > 10]),
        }

        # Documentation statistics
        documented = [e for e in entities if e.docstring and e.docstring.strip()]
        documentation_stats = {
            'documented_count': len(documented),
            'undocumented_count': len(entities) - len(documented),
            'documentation_coverage': len(documented) / len(entities) if entities else 0,
        }

        return {
            'total_entities': len(entities),
            'total_files': len(source_files),
            'entity_types': entity_types,
            'languages': languages,
            'complexity_stats': complexity_stats,
            'documentation_stats': documentation_stats,
        }
