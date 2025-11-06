"""
Integration tests for pipeline functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch

from output.orchestrator_core import PipelineConfig
from output.orchestrator import PipelineRunner


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for pipeline functionality."""

    @pytest.fixture
    def config(self):
        """Create integration test configuration."""
        return PipelineConfig(
            name="Integration Test Pipeline",
            max_workers=2,
            batch_size=10,
            enable_dashboard=False
        )

    @pytest.fixture
    def runner(self, config):
        """Create test pipeline runner."""
        return PipelineRunner(config)

    def test_full_pipeline_lifecycle(self, runner):
        """Test complete pipeline lifecycle."""
        # Initialize
        runner.initialize()

        # Verify initialization
        assert hasattr(runner, 'initializer')
        assert hasattr(runner, 'monitor')

        # Start pipeline
        with patch('time.sleep'):  # Prevent actual sleeping
            with patch.object(runner, '_run_main_loop'):
                with patch.object(runner, '_monitoring_loop'):
                    runner.start()
                    assert runner.running is True

        # Check status
        status = runner.get_status()
        assert status in ['running', 'stopped']

        # Get metrics
        metrics = runner.get_metrics()
        assert isinstance(metrics, dict)
        assert 'uptime' in metrics

        # Stop pipeline
        runner.stop()
        assert runner.running is False

    def test_metrics_collection(self, runner):
        """Test metrics collection during pipeline operation."""
        runner.initialize()

        # Simulate some activity
        runner.monitor.update_metrics(messages_processed=5, errors=1)
        runner.monitor.update_metrics(messages_processed=3)

        # Check metrics
        total_messages = runner.get_total_messages_processed()
        error_count = runner.get_error_count()

        assert total_messages == 8
        assert error_count == 1

    def test_stage_metrics(self, runner):
        """Test stage metrics collection."""
        runner.initialize()

        # Mock stage metrics
        mock_stage = Mock()
        mock_stage.get_stats.return_value = {
            'processed': 100,
            'errors': 2,
            'avg_processing_time': 0.5
        }

        runner.initializer.processing_stages['test_stage'] = mock_stage

        # Get stage metrics
        stage_metrics = runner.get_all_stage_metrics()

        assert 'test_stage' in stage_metrics
        assert stage_metrics['test_stage']['processed'] == 100
        assert stage_metrics['test_stage']['errors'] == 2

    @pytest.mark.network
    def test_demo_sources_integration(self, runner):
        """Test integration with demo sources (requires network)."""
        from sources.source_factory import create_demo_sources

        sources = create_demo_sources()

        # Verify sources were created
        assert isinstance(sources, dict)
        assert len(sources) > 0

        # Each source should have basic methods
        for name, source in sources.items():
            assert hasattr(source, 'get_messages')

    def test_storage_backend_integration(self, runner):
        """Test storage backend integration."""
        from storage.backend_factory import StorageBackendFactory

        # Create a SQLite backend
        config_dict = {
            'backend_type': 'sqlite',
            'connection_string': 'sqlite:///:memory:'
        }

        backend = StorageBackendFactory.create_backend_from_dict(config_dict)

        # Test basic operations
        record_id = backend.store('test_collection', {'test': 'data'})
        assert record_id is not None

        retrieved = backend.retrieve('test_collection', record_id)
        assert retrieved is not None
        assert retrieved['test'] == 'data'

    def test_error_handling_integration(self, runner):
        """Test error handling in integrated pipeline."""
        runner.initialize()

        # Test error metrics
        initial_errors = runner.get_error_count()

        # Simulate errors
        runner.monitor.update_metrics(errors=3)

        final_errors = runner.get_error_count()
        assert final_errors == initial_errors + 3

    def test_concurrent_operation_simulation(self, runner):
        """Test concurrent operation simulation."""
        import threading

        runner.initialize()

        results = []
        errors = []

        def worker(worker_id):
            try:
                # Simulate work
                runner.monitor.update_metrics(messages_processed=10)
                results.append(f"worker_{worker_id}_completed")
            except Exception as e:
                errors.append(str(e))

        # Start multiple worker threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify results
        assert len(results) == 3
        assert len(errors) == 0

        # Check total messages processed
        total_messages = runner.get_total_messages_processed()
        assert total_messages == 30
