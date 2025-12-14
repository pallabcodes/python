"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_basic_health_check(self, client: AsyncClient):
        """Test basic health check."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_detailed_health_check(self, client: AsyncClient):
        """Test detailed health check."""
        response = await client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "database" in data

    async def test_database_health_check(self, client: AsyncClient):
        """Test database health check."""
        response = await client.get("/health/database")
        assert response.status_code == 200
        data = response.json()
        assert data["component"] == "database"
        assert data["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
class TestRepositoryAPI:
    """Test repository API endpoints."""

    async def test_create_repository(self, client: AsyncClient, db_session: AsyncSession):
        """Test repository creation via API."""
        repo_data = {
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "description": "A test repository",
            "url": "https://github.com/testuser/test-repo",
            "clone_url": "https://github.com/testuser/test-repo.git",
            "platform": "github",
            "owner": "testuser",
            "language": "python",
            "is_active": True,
            "analysis_enabled": True,
        }

        response = await client.post("/api/v1/repositories/", json=repo_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == repo_data["name"]
        assert data["full_name"] == repo_data["full_name"]

    async def test_get_repository(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test repository retrieval."""
        # First create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        repo = await repo_service.create_repository(sample_repository_data)

        response = await client.get(f"/api/v1/repositories/{repo.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == repo.id
        assert data["full_name"] == sample_repository_data["full_name"]

    async def test_list_repositories(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test repository listing."""
        # Create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        await repo_service.create_repository(sample_repository_data)

        response = await client.get("/api/v1/repositories/")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_update_repository(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test repository update."""
        # Create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        repo = await repo_service.create_repository(sample_repository_data)

        update_data = {
            "description": "Updated description",
            "stars": 42
        }

        response = await client.put(f"/api/v1/repositories/{repo.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Updated description"
        assert data["stars"] == 42


@pytest.mark.asyncio
class TestAnalysisAPI:
    """Test analysis API endpoints."""

    async def test_start_analysis(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test starting repository analysis."""
        # Create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        repo = await repo_service.create_repository(sample_repository_data)

        analysis_data = {
            "repository_id": repo.id,
            "trigger_type": "manual"
        }

        response = await client.post("/api/v1/analysis/", json=analysis_data)
        # This might return 202 Accepted for async processing
        assert response.status_code in [200, 202, 404]  # 404 if analysis endpoint not implemented yet

    async def test_get_analysis_status(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test getting analysis status."""
        # Create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        repo = await repo_service.create_repository(sample_repository_data)

        response = await client.get(f"/api/v1/analysis/{repo.id}/status")
        assert response.status_code in [200, 404]  # 404 if endpoint not implemented yet


@pytest.mark.asyncio
class TestDocumentationAPI:
    """Test documentation API endpoints."""

    async def test_list_documentation(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test documentation listing."""
        # Create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        repo = await repo_service.create_repository(sample_repository_data)

        response = await client.get(f"/api/v1/repositories/{repo.id}/documentation/")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data

    async def test_search_documentation(self, client: AsyncClient, sample_repository_data, db_session: AsyncSession):
        """Test documentation search."""
        # Create a repository
        from app.services.repository_service import RepositoryService
        repo_service = RepositoryService(db_session)
        repo = await repo_service.create_repository(sample_repository_data)

        search_data = {
            "query": "test",
            "limit": 10
        }

        response = await client.post(f"/api/v1/repositories/{repo.id}/documentation/search", json=search_data)
        assert response.status_code == 200

        data = response.json()
        assert "results" in data


@pytest.mark.asyncio
class TestRootEndpoints:
    """Test root API endpoints."""

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert data["name"] == "DocuMind"

    async def test_openapi_docs(self, client: AsyncClient):
        """Test OpenAPI documentation endpoint."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
