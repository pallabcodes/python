"""Repository service for managing repositories and integrations."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundError, ValidationError
from app.models.repository import Repository
from app.models.integration import Integration


class RepositoryService:
    """Service for managing repositories and their integrations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository service."""
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def create_repository(self, repo_data: Dict) -> Repository:
        """Create a new repository."""
        try:
            # Validate required fields
            required_fields = ['name', 'full_name', 'url', 'clone_url', 'platform']
            for field in required_fields:
                if field not in repo_data:
                    raise ValidationError(f"Missing required field: {field}")

            repository = Repository(**repo_data)
            self.db.add(repository)
            await self.db.commit()
            await self.db.refresh(repository)

            self.logger.info(f"Created repository: {repository.full_name}")
            return repository

        except Exception as e:
            self.logger.error(f"Failed to create repository: {e}")
            raise

    async def get_repository(self, repo_id: int) -> Repository:
        """Get repository by ID."""
        query = select(Repository).where(Repository.id == repo_id)
        result = await self.db.execute(query)
        repository = result.scalar_one_or_none()

        if not repository:
            raise NotFoundError("Repository", repo_id)

        return repository

    async def get_repository_by_full_name(self, full_name: str) -> Optional[Repository]:
        """Get repository by full name (owner/repo)."""
        query = select(Repository).where(Repository.full_name == full_name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_repositories(self, active_only: bool = True) -> List[Repository]:
        """List all repositories."""
        query = select(Repository)
        if active_only:
            query = query.where(Repository.is_active == True)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_repository(self, repo_id: int, updates: Dict) -> Repository:
        """Update repository information."""
        repository = await self.get_repository(repo_id)

        # Update allowed fields
        allowed_fields = [
            'description', 'language', 'languages', 'topics',
            'stars', 'forks', 'watchers', 'size_kb',
            'is_active', 'analysis_enabled', 'last_commit_sha',
            'analysis_config', 'ignore_patterns'
        ]

        for field in allowed_fields:
            if field in updates:
                setattr(repository, field, updates[field])

        await self.db.commit()
        await self.db.refresh(repository)

        self.logger.info(f"Updated repository: {repository.full_name}")
        return repository

    async def delete_repository(self, repo_id: int) -> None:
        """Delete a repository."""
        repository = await self.get_repository(repo_id)

        await self.db.delete(repository)
        await self.db.commit()

        self.logger.info(f"Deleted repository: {repository.full_name}")

    async def create_integration(self, integration_data: Dict) -> Integration:
        """Create a new integration for a repository."""
        try:
            # Validate required fields
            required_fields = ['service_type', 'service_name', 'auth_type']
            for field in required_fields:
                if field not in integration_data:
                    raise ValidationError(f"Missing required field: {field}")

            integration = Integration(**integration_data)
            self.db.add(integration)
            await self.db.commit()
            await self.db.refresh(integration)

            self.logger.info(f"Created integration: {integration.service_type} for {integration.repository_id or 'org'}")
            return integration

        except Exception as e:
            self.logger.error(f"Failed to create integration: {e}")
            raise

    async def get_repository_integrations(self, repo_id: int) -> List[Integration]:
        """Get all integrations for a repository."""
        query = select(Integration).where(Integration.repository_id == repo_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_integration_status(self, integration_id: int, is_active: bool, error_message: Optional[str] = None) -> Integration:
        """Update integration status."""
        query = select(Integration).where(Integration.id == integration_id)
        result = await self.db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise NotFoundError("Integration", integration_id)

        integration.is_active = is_active
        if error_message:
            integration.last_error_message = error_message

        await self.db.commit()
        await self.db.refresh(integration)

        self.logger.info(f"Updated integration {integration_id} status: {is_active}")
        return integration

    async def sync_repository_data(self, repo_id: int) -> Dict:
        """Sync repository data from external sources (GitHub, GitLab, etc.)."""
        repository = await self.get_repository(repo_id)

        # This would integrate with GitHub/GitLab APIs to get latest data
        # For now, return current data
        sync_result = {
            'repository_id': repo_id,
            'sync_status': 'completed',
            'updated_fields': [],
            'last_sync': repository.updated_at.isoformat() if repository.updated_at else None,
        }

        self.logger.info(f"Synced repository data for: {repository.full_name}")
        return sync_result

    async def get_repository_stats(self, repo_id: int) -> Dict:
        """Get comprehensive statistics for a repository."""
        repository = await self.get_repository(repo_id)

        # Get code entity counts
        from sqlalchemy import func
        from app.models.code_entity import CodeEntity
        from app.models.documentation import Documentation
        from app.models.analysis_run import AnalysisRun

        # Code entities by type
        query = select(
            CodeEntity.entity_type,
            func.count(CodeEntity.id)
        ).where(CodeEntity.repository_id == repo_id).group_by(CodeEntity.entity_type)
        result = await self.db.execute(query)
        entity_counts = dict(result.all())

        # Documentation stats
        query = select(func.count(Documentation.id)).where(Documentation.repository_id == repo_id)
        result = await self.db.execute(query)
        docs_count = result.scalar()

        # Analysis runs
        query = select(func.count(AnalysisRun.id)).where(AnalysisRun.repository_id == repo_id)
        result = await self.db.execute(query)
        analysis_count = result.scalar()

        # Documentation coverage
        query = select(
            func.count(CodeEntity.id)
        ).where(
            CodeEntity.repository_id == repo_id,
            CodeEntity.documentation.isnot(None)
        )
        result = await self.db.execute(query)
        documented_entities = result.scalar()

        total_entities = sum(entity_counts.values())
        coverage = (documented_entities / total_entities * 100) if total_entities > 0 else 0

        return {
            'repository_id': repo_id,
            'total_entities': total_entities,
            'entities_by_type': entity_counts,
            'documented_entities': documented_entities,
            'documentation_coverage': round(coverage, 1),
            'total_documentations': docs_count,
            'analysis_runs': analysis_count,
            'last_analysis': repository.last_analysis_at.isoformat() if repository.last_analysis_at else None,
            'language': repository.language,
            'size_kb': repository.size_kb,
        }
