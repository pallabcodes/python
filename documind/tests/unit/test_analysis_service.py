"""Unit tests for AnalysisService."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.models.repository import Repository
from app.services.analysis_service import AnalysisService


class TestAnalysisService:
    """Test cases for AnalysisService."""

    @pytest.fixture
    def service(self, db_session):
        """Create analysis service instance."""
        return AnalysisService(db_session)

    @pytest.fixture
    def mock_analyzer(self):
        """Mock code analyzer."""
        analyzer = Mock()
        analyzer.analyze_repository = AsyncMock()
        return analyzer

    @pytest.fixture
    def mock_doc_generator(self):
        """Mock documentation generator."""
        generator = Mock()
        generator.generate_documentation = AsyncMock()
        return generator

    @pytest.mark.asyncio
    async def test_analyze_repository_success(self, service, db_session, sample_repository_data, mock_analyzer, mock_doc_generator):
        """Test successful repository analysis."""
        # Create repository in DB
        repository = Repository(**sample_repository_data)
        db_session.add(repository)
        await db_session.commit()
        await db_session.refresh(repository)

        # Mock analysis results
        mock_analysis_result = {
            'files_analyzed': 5,
            'entities_found': 10,
            'entities_created': 10,
            'docs_generated': 8,
            'files_processed': 5,
            'languages_detected': ['python'],
            'summary': {
                'total_entities': 10,
                'documentation_coverage': 80.0,
            }
        }

        with patch.object(service, 'analyzer', mock_analyzer), \
             patch.object(service, 'doc_generator', mock_doc_generator):

            mock_analyzer.analyze_repository.return_value = mock_analysis_result

            result = await service.analyze_repository(repository.id, "/fake/path")

            assert result['status'] == 'completed'
            assert result['entities_found'] == 10
            assert result['docs_generated'] == 8
            assert result['files_processed'] == 5

    @pytest.mark.asyncio
    async def test_analyze_repository_invalid_repo_id(self, service):
        """Test analysis with invalid repository ID."""
        with pytest.raises(Exception):  # Should raise repository not found
            await service.analyze_repository(99999, "/fake/path")

    @pytest.mark.asyncio
    async def test_analyze_repository_path_not_exists(self, service, db_session, sample_repository_data):
        """Test analysis with non-existent repository path."""
        # Create repository in DB
        repository = Repository(**sample_repository_data)
        db_session.add(repository)
        await db_session.commit()

        with pytest.raises(Exception):  # Should raise path not found error
            await service.analyze_repository(repository.id, "/nonexistent/path")

    @pytest.mark.asyncio
    async def test_get_analysis_status_success(self, service, db_session, sample_repository_data):
        """Test getting analysis status for repository."""
        # Create repository
        repository = Repository(**sample_repository_data)
        db_session.add(repository)
        await db_session.commit()

        status = await service.get_analysis_status(repository.id)

        assert status['repository_id'] == repository.id
        assert status['status'] == 'never_analyzed'
        assert status['last_analysis'] is None

    @pytest.mark.asyncio
    async def test_get_analysis_history(self, service, db_session, sample_repository_data):
        """Test getting analysis history."""
        # Create repository
        repository = Repository(**sample_repository_data)
        db_session.add(repository)
        await db_session.commit()

        history = await service.get_analysis_history(repository.id)

        assert isinstance(history, list)
        assert len(history) == 0  # No analysis runs yet

    @pytest.mark.asyncio
    async def test_analyze_single_file(self, service, db_session, sample_repository_data):
        """Test single file analysis."""
        # Create repository
        repository = Repository(**sample_repository_data)
        db_session.add(repository)
        await db_session.commit()

        with patch.object(service, 'analyzer') as mock_analyzer, \
             patch.object(service, 'doc_generator') as mock_doc_generator:

            mock_analyzer.analyze_file.return_value = [
                Mock(id=1, qualified_name="test_function")
            ]

            result = await service.analyze_single_file(repository.id, "/fake/file.py")

            assert result['status'] == 'completed'
            assert 'entities_found' in result
            assert 'docs_generated' in result
