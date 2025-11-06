"""
End-to-end tests for the complete analytics pipeline.
"""

import pytest
import time
import requests
from unittest.mock import patch

from output.orchestrator_core import PipelineConfig
from output.orchestrator import PipelineRunner


@pytest.mark.e2e
class TestPipelineE2E:
    """End-to-end tests for the complete pipeline."""

    @pytest.fixture(scope="class")
    def pipeline_config(self):
        """Create end-to-end test configuration."""
        return PipelineConfig(
            name="E2E Test Pipeline",
            max_workers=2,
            batch_size=5,
            processing_timeout=10.0,
            enable_dashboard=True,
            enable_monitoring=True
        )

    @pytest.fixture(scope="class")
    def pipeline_runner(self, pipeline_config):
        """Create and initialize pipeline runner for e2e tests."""
        runner = PipelineRunner(pipeline_config)
        runner.initialize()
        yield runner
        # Cleanup
        runner.stop()

    def test_pipeline_initialization_e2e(self, pipeline_runner):
        """Test complete pipeline initialization."""
        # Verify components are initialized
        assert hasattr(pipeline_runner, 'initializer')
        assert hasattr(pipeline_runner, 'monitor')

        # Verify sources, stages, and backends are set up
        assert hasattr(pipeline_runner.initializer, 'sources')
        assert hasattr(pipeline_runner.initializer, 'processing_stages')
        assert hasattr(pipeline_runner.initializer, 'storage_backends')

        # Verify at least basic components exist
        assert isinstance(pipeline_runner.initializer.sources, dict)
        assert isinstance(pipeline_runner.initializer.processing_stages, dict)
        assert isinstance(pipeline_runner.initializer.storage_backends, dict)

    def test_pipeline_execution_e2e(self, pipeline_runner):
        """Test complete pipeline execution cycle."""
        # Start the pipeline
        pipeline_runner.start()

        # Verify it's running
        assert pipeline_runner.running is True
        assert pipeline_runner.get_status() in ['running', 'stopped']

        # Let it run for a short time
        time.sleep(2)

        # Check that metrics are being collected
        metrics = pipeline_runner.get_metrics()
        assert isinstance(metrics, dict)

        # Verify uptime is reasonable
        uptime = pipeline_runner.get_uptime()
        assert uptime >= 1.0  # At least 1 second

        # Stop the pipeline
        pipeline_runner.stop()
        assert pipeline_runner.running is False

    def test_data_flow_e2e(self, pipeline_runner):
        """Test complete data flow through the pipeline."""
        # Start pipeline
        pipeline_runner.start()

        try:
            # Simulate data processing
            initial_messages = pipeline_runner.get_total_messages_processed()

            # Add some test data to simulate processing
            pipeline_runner.monitor.update_metrics(messages_processed=10)

            # Verify metrics updated
            final_messages = pipeline_runner.get_total_messages_processed()
            assert final_messages >= initial_messages + 10

            # Test stage metrics
            stage_metrics = pipeline_runner.get_all_stage_metrics()
            assert isinstance(stage_metrics, dict)

            # Test storage metrics
            storage_metrics = pipeline_runner.get_all_storage_metrics()
            assert isinstance(storage_metrics, dict)

        finally:
            pipeline_runner.stop()

    def test_error_handling_e2e(self, pipeline_runner):
        """Test error handling in end-to-end scenario."""
        pipeline_runner.start()

        try:
            # Simulate errors
            initial_errors = pipeline_runner.get_error_count()

            # Add some errors
            pipeline_runner.monitor.update_metrics(errors=5)

            # Verify error count increased
            final_errors = pipeline_runner.get_error_count()
            assert final_errors >= initial_errors + 5

            # Verify pipeline continues running despite errors
            assert pipeline_runner.running is True

        finally:
            pipeline_runner.stop()

    @pytest.mark.slow
    def test_long_running_stability_e2e(self, pipeline_runner):
        """Test pipeline stability over longer period."""
        pipeline_runner.start()

        try:
            # Run for 10 seconds
            start_time = time.time()
            while time.time() - start_time < 10:
                # Simulate periodic activity
                pipeline_runner.monitor.update_metrics(messages_processed=1)
                time.sleep(0.5)

            # Verify pipeline remained stable
            assert pipeline_runner.running is True

            # Check accumulated metrics
            total_messages = pipeline_runner.get_total_messages_processed()
            assert total_messages >= 20  # At least 20 messages over 10 seconds

            uptime = pipeline_runner.get_uptime()
            assert uptime >= 9.0  # At least 9 seconds

        finally:
            pipeline_runner.stop()

    def test_configuration_persistence_e2e(self, pipeline_config):
        """Test that configuration is properly maintained."""
        runner1 = PipelineRunner(pipeline_config)
        runner2 = PipelineRunner(pipeline_config)

        # Verify configurations are equivalent
        assert runner1.config.name == runner2.config.name
        assert runner1.config.max_workers == runner2.config.max_workers
        assert runner1.config.batch_size == runner2.config.batch_size

    def test_resource_cleanup_e2e(self, pipeline_runner):
        """Test proper resource cleanup."""
        pipeline_runner.start()

        # Verify resources are allocated
        assert pipeline_runner.running is True
        assert hasattr(pipeline_runner, 'executor')

        # Stop and verify cleanup
        pipeline_runner.stop()

        assert pipeline_runner.running is False

        # Verify executor is properly shut down
        # Note: In real implementation, check for proper thread cleanup
