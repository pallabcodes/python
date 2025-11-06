"""
Unit tests for pipeline core functionality.
"""

import pytest
from unittest.mock import Mock, patch

from output.orchestrator_core import PipelineConfig
from output.orchestrator import PipelineRunner


class TestPipelineConfig:
    """Test cases for PipelineConfig."""

    def test_default_config(self):
        """Test default pipeline configuration."""
        config = PipelineConfig()

        assert config.name == "Analytics Pipeline"
        assert config.max_workers == 10
        assert config.batch_size == 100
        assert config.processing_timeout == 30.0
        assert config.enable_monitoring is True
        assert config.enable_dashboard is True
        assert config.auto_start is False
        assert isinstance(config.sources, dict)
        assert isinstance(config.processing_stages, list)
        assert isinstance(config.storage_backends, dict)

    def test_custom_config(self):
        """Test custom pipeline configuration."""
        config = PipelineConfig(
            name="Custom Pipeline",
            max_workers=5,
            batch_size=50,
            enable_dashboard=False
        )

        assert config.name == "Custom Pipeline"
        assert config.max_workers == 5
        assert config.batch_size == 50
        assert config.enable_dashboard is False


class TestPipelineRunner:
    """Test cases for PipelineRunner."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PipelineConfig(name="Test Pipeline")

    @pytest.fixture
    def runner(self, config):
        """Create test pipeline runner."""
        return PipelineRunner(config)

    def test_runner_initialization(self, runner, config):
        """Test pipeline runner initialization."""
        assert runner.config == config
        assert hasattr(runner, 'initializer')
        assert hasattr(runner, 'monitor')
        assert runner.running is False

    @patch('output.orchestrator.PipelineRunner._run_main_loop')
    @patch('output.orchestrator.PipelineRunner._monitoring_loop')
    def test_start_pipeline(self, mock_monitoring, mock_main_loop, runner):
        """Test starting the pipeline."""
        with patch('time.sleep'):  # Prevent actual sleeping
            runner.start()

            assert runner.running is True
            # Verify monitoring was called
            mock_monitoring.assert_called_once()

    def test_stop_pipeline(self, runner):
        """Test stopping the pipeline."""
        runner.running = True
        runner.stop()

        assert runner.running is False

    def test_get_status_stopped(self, runner):
        """Test getting status when stopped."""
        runner.running = False
        status = runner.get_status()

        assert status == "stopped"

    def test_get_uptime(self, runner):
        """Test getting pipeline uptime."""
        runner.monitor.start_time = 1000.0

        with patch('time.time', return_value=1010.0):
            uptime = runner.get_uptime()

            assert uptime == 10.0

    def test_get_uptime_no_start_time(self, runner):
        """Test getting uptime when start time is not set."""
        runner.monitor.start_time = None

        uptime = runner.get_uptime()

        assert uptime == 0.0

    def test_is_running(self, runner):
        """Test checking if pipeline is running."""
        runner.running = True
        assert runner.is_running() is True

        runner.running = False
        assert runner.is_running() is False
