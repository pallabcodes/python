"""Unit tests for RepositoryService."""

import pytest
from unittest.mock import Mock, patch

from app.core.exceptions import NotFoundError, ValidationError
from app.models.repository import Repository
from app.services.repository_service import RepositoryService


class TestRepositoryService:
    """Test cases for RepositoryService."""

    @pytest.fixture
    def service(self, db_session):
        """Create repository service instance."""
        return RepositoryService(db_session)

    @pytest.mark.asyncio
    async def test_create_repository_success(self, service, sample_repository_data):
        """Test successful repository creation."""
        repository = await service.create_repository(sample_repository_data)

        assert repository.name == sample_repository_data["name"]
        assert repository.full_name == sample_repository_data["full_name"]
        assert repository.platform == sample_repository_data["platform"]
        assert repository.language == sample_repository_data["language"]
        assert repository.is_active == sample_repository_data["is_active"]

    @pytest.mark.asyncio
    async def test_create_repository_validation_error(self, service):
        """Test repository creation with missing required fields."""
        invalid_data = {
            "name": "test-repo",
            # Missing required fields
        }

        with pytest.raises(ValidationError):
            await service.create_repository(invalid_data)

    @pytest.mark.asyncio
    async def test_get_repository_success(self, service, sample_repository_data):
        """Test successful repository retrieval."""
        # Create repository first
        created_repo = await service.create_repository(sample_repository_data)

        # Retrieve it
        retrieved_repo = await service.get_repository(created_repo.id)

        assert retrieved_repo.id == created_repo.id
        assert retrieved_repo.full_name == sample_repository_data["full_name"]

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self, service):
        """Test repository retrieval with invalid ID."""
        with pytest.raises(NotFoundError):
            await service.get_repository(99999)

    @pytest.mark.asyncio
    async def test_get_repository_by_full_name(self, service, sample_repository_data):
        """Test repository retrieval by full name."""
        # Create repository first
        await service.create_repository(sample_repository_data)

        # Retrieve by full name
        retrieved_repo = await service.get_repository_by_full_name(
            sample_repository_data["full_name"]
        )

        assert retrieved_repo is not None
        assert retrieved_repo.full_name == sample_repository_data["full_name"]

    @pytest.mark.asyncio
    async def test_update_repository(self, service, sample_repository_data):
        """Test repository update."""
        # Create repository first
        repository = await service.create_repository(sample_repository_data)

        # Update it
        updates = {
            "description": "Updated description",
            "stars": 42,
            "language": "javascript",
        }

        updated_repo = await service.update_repository(repository.id, updates)

        assert updated_repo.description == "Updated description"
        assert updated_repo.stars == 42
        assert updated_repo.language == "javascript"

    @pytest.mark.asyncio
    async def test_list_repositories(self, service, sample_repository_data):
        """Test repository listing."""
        # Create multiple repositories
        repo_data1 = sample_repository_data.copy()
        repo_data2 = sample_repository_data.copy()
        repo_data2["name"] = "test-repo-2"
        repo_data2["full_name"] = "testuser/test-repo-2"

        await service.create_repository(repo_data1)
        await service.create_repository(repo_data2)

        # List all repositories
        repositories = await service.list_repositories()

        assert len(repositories) == 2
        assert all(repo.is_active for repo in repositories)

    @pytest.mark.asyncio
    async def test_list_repositories_inactive_only(self, service, sample_repository_data):
        """Test listing only inactive repositories."""
        repo_data = sample_repository_data.copy()
        repo_data["is_active"] = False

        await service.create_repository(repo_data)

        # List active only (should be empty)
        active_repos = await service.list_repositories(active_only=True)
        assert len(active_repos) == 0

        # List all (should include inactive)
        all_repos = await service.list_repositories(active_only=False)
        assert len(all_repos) == 1

    @pytest.mark.asyncio
    async def test_delete_repository(self, service, sample_repository_data):
        """Test repository deletion."""
        # Create repository first
        repository = await service.create_repository(sample_repository_data)

        # Delete it
        await service.delete_repository(repository.id)

        # Verify it's gone
        with pytest.raises(NotFoundError):
            await service.get_repository(repository.id)

    @pytest.mark.asyncio
    async def test_get_repository_stats(self, service, sample_repository_data):
        """Test repository statistics retrieval."""
        # Create repository
        repository = await service.create_repository(sample_repository_data)

        # Get stats
        stats = await service.get_repository_stats(repository.id)

        assert stats["repository_id"] == repository.id
        assert "total_entities" in stats
        assert "documentation_coverage" in stats
        assert "entities_by_type" in stats

    @pytest.mark.asyncio
    async def test_sync_repository_data(self, service, sample_repository_data):
        """Test repository data synchronization."""
        # Create repository
        repository = await service.create_repository(sample_repository_data)

        # Mock external API calls would happen here
        # For now, just test the method exists and returns expected structure
        result = await service.sync_repository_data(repository.id)

        assert result["repository_id"] == repository.id
        assert "sync_status" in result
        assert "updated_fields" in result
        assert "last_sync" in result
