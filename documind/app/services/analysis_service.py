"""Analysis service for orchestrating code analysis and documentation generation."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CodeAnalysisError
from app.models.analysis_run import AnalysisRun
from app.models.code_entity import CodeEntity
from app.models.documentation import Documentation
from app.models.repository import Repository

from analysis_engine import CodeAnalyzer
from doc_generator import DocGenerator


class AnalysisService:
    """Service for orchestrating code analysis and documentation generation."""

    def __init__(self, db: AsyncSession):
        """Initialize analysis service."""
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.analyzer = CodeAnalyzer()
        self.doc_generator = DocGenerator()

    async def analyze_repository(
        self,
        repo_id: int,
        repo_path: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Run complete analysis pipeline for a repository.

        Args:
            repo_id: Repository ID
            repo_path: Path to repository
            config: Analysis configuration

        Returns:
            Analysis results
        """
        try:
            # Get repository
            from app.services.repository_service import RepositoryService
            repo_service = RepositoryService(self.db)
            repository = await repo_service.get_repository(repo_id)

            self.logger.info(f"Starting analysis for repository: {repository.full_name}")

            # Create analysis run record
            analysis_run = AnalysisRun(
                repository_id=repo_id,
                trigger_type='manual',
                status='running',
            )
            self.db.add(analysis_run)
            await self.db.commit()
            await self.db.refresh(analysis_run)

            try:
                # Run code analysis
                analysis_results = await self.analyzer.analyze_repository(
                    repo_path, repository, config
                )

                # Store code entities
                entities_created = await self._store_code_entities(
                    repo_id, analysis_results['entities']
                )

                # Generate documentation for entities
                docs_created = await self._generate_documentation_for_entities(
                    analysis_results['entities']
                )

                # Update analysis run with results
                analysis_run.status = 'completed'
                analysis_run.entities_found = analysis_results['entities_found']
                analysis_run.entities_analyzed = entities_created
                analysis_run.docs_generated = docs_created
                analysis_run.duration_seconds = 0  # Would calculate actual duration

                await self.db.commit()

                # Update repository stats
                await repo_service.update_repository(repo_id, {
                    'last_analysis_at': analysis_run.completed_at,
                })

                result = {
                    'analysis_run_id': analysis_run.id,
                    'status': 'completed',
                    'entities_found': analysis_results['entities_found'],
                    'entities_created': entities_created,
                    'docs_generated': docs_created,
                    'files_processed': len(analysis_results['file_results']),
                    'languages': analysis_results['languages_detected'],
                    'summary': analysis_results['summary'],
                }

                self.logger.info(f"Analysis completed for {repository.full_name}: {entities_created} entities, {docs_created} docs")
                return result

            except Exception as e:
                # Update analysis run with error
                analysis_run.status = 'failed'
                analysis_run.error_message = str(e)
                await self.db.commit()

                raise CodeAnalysisError(f"Analysis failed: {e}")

        except Exception as e:
            self.logger.error(f"Analysis orchestration failed: {e}")
            raise

    async def analyze_single_file(
        self,
        repo_id: int,
        file_path: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """Analyze a single file."""
        try:
            from app.services.repository_service import RepositoryService
            repo_service = RepositoryService(self.db)
            repository = await repo_service.get_repository(repo_id)

            entities = await self.analyzer.analyze_file(file_path, repository, config)
            entities_created = await self._store_code_entities(repo_id, entities)
            docs_created = await self._generate_documentation_for_entities(entities)

            return {
                'status': 'completed',
                'entities_found': len(entities),
                'entities_created': entities_created,
                'docs_generated': docs_created,
            }

        except Exception as e:
            self.logger.error(f"Single file analysis failed: {e}")
            raise

    async def get_analysis_status(self, repo_id: int) -> Dict:
        """Get analysis status for a repository."""
        from sqlalchemy import select, desc

        query = select(AnalysisRun).where(
            AnalysisRun.repository_id == repo_id
        ).order_by(desc(AnalysisRun.created_at)).limit(1)

        result = await self.db.execute(query)
        latest_run = result.scalar_one_or_none()

        if not latest_run:
            return {
                'repository_id': repo_id,
                'status': 'never_analyzed',
                'last_analysis': None,
            }

        return {
            'repository_id': repo_id,
            'status': latest_run.status,
            'last_analysis': latest_run.created_at.isoformat(),
            'latest_run_id': latest_run.id,
            'entities_found': latest_run.entities_found,
            'docs_generated': latest_run.docs_generated,
            'duration_seconds': latest_run.duration_seconds,
            'error_message': latest_run.error_message,
        }

    async def get_analysis_history(self, repo_id: int, limit: int = 10) -> List[Dict]:
        """Get analysis history for a repository."""
        from sqlalchemy import select, desc

        query = select(AnalysisRun).where(
            AnalysisRun.repository_id == repo_id
        ).order_by(desc(AnalysisRun.created_at)).limit(limit)

        result = await self.db.execute(query)
        runs = result.scalars().all()

        return [
            {
                'run_id': run.id,
                'status': run.status,
                'created_at': run.created_at.isoformat(),
                'entities_found': run.entities_found,
                'docs_generated': run.docs_generated,
                'duration_seconds': run.duration_seconds,
                'error_message': run.error_message,
            }
            for run in runs
        ]

    async def _store_code_entities(self, repo_id: int, entities: List[CodeEntity]) -> int:
        """Store code entities in database."""
        if not entities:
            return 0

        # Check for existing entities to avoid duplicates
        existing_names = set()
        for entity in entities:
            # Simple duplicate check by qualified name
            if entity.qualified_name in existing_names:
                continue
            existing_names.add(entity.qualified_name)

            self.db.add(entity)

        await self.db.commit()

        # Refresh entities to get IDs
        for entity in entities:
            if hasattr(entity, 'id') and entity.id:
                await self.db.refresh(entity)

        return len(entities)

    async def _generate_documentation_for_entities(self, entities: List[CodeEntity]) -> int:
        """Generate documentation for code entities."""
        docs_created = 0

        for entity in entities:
            try:
                # Check if documentation already exists
                from sqlalchemy import select
                query = select(Documentation).where(Documentation.code_entity_id == entity.id)
                result = await self.db.execute(query)
                existing_doc = result.scalar_one_or_none()

                if existing_doc:
                    continue

                # Generate documentation
                documentation = await self.doc_generator.generate_documentation(entity)

                self.db.add(documentation)
                docs_created += 1

            except Exception as e:
                self.logger.warning(f"Failed to generate docs for {entity.qualified_name}: {e}")
                continue

        if docs_created > 0:
            await self.db.commit()

        return docs_created
