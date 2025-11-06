"""
Unit tests for YAML pipeline configuration.

This module provides comprehensive tests for YAML configuration
loading, validation, and pipeline building.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from .config_schema import (
    PipelineConfig, StageConfig, QueueConfig,
    ConfigValidationError, validate_pipeline_config
)
from .safe_loader import SafeStageLoader, StageLoadError
from .pipeline_builder import YamlPipelineBuilder, PipelineBuildError
from .config_loader import SecureConfigLoader, ConfigLoadError, ConfigManager


class TestConfigSchema:
    """Tests for configuration schema validation."""

    def test_valid_pipeline_config(self):
        """Test validation of valid pipeline configuration."""
        config_dict = {
            "name": "test_pipeline",
            "version": "1.0.0",
            "stages": [
                {
                    "name": "test_stage",
                    "type": "transform",
                    "module": "test.module",
                    "class_name": "TestStage",
                    "parameters": {"key": "value"}
                }
            ]
        }

        config = validate_pipeline_config(config_dict)

        assert config.name == "test_pipeline"
        assert config.version == "1.0.0"
        assert len(config.stages) == 1
        assert config.stages[0].name == "test_stage"

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        config_dict = {
            "name": "test_pipeline"
            # Missing version and stages
        }

        with pytest.raises(ConfigValidationError):
            validate_pipeline_config(config_dict)

    def test_invalid_stage_type(self):
        """Test validation fails with invalid stage type."""
        config_dict = {
            "name": "test_pipeline",
            "version": "1.0.0",
            "stages": [
                {
                    "name": "test_stage",
                    "type": "invalid_type",  # Invalid type
                    "module": "test.module",
                    "class_name": "TestStage"
                }
            ]
        }

        with pytest.raises(ConfigValidationError):
            validate_pipeline_config(config_dict)

    def test_duplicate_stage_names(self):
        """Test validation fails with duplicate stage names."""
        config_dict = {
            "name": "test_pipeline",
            "version": "1.0.0",
            "stages": [
                {
                    "name": "duplicate_stage",
                    "type": "transform",
                    "module": "test.module",
                    "class_name": "TestStage1"
                },
                {
                    "name": "duplicate_stage",  # Duplicate
                    "type": "filter",
                    "module": "test.module",
                    "class_name": "TestStage2"
                }
            ]
        }

        with pytest.raises(ConfigValidationError):
            validate_pipeline_config(config_dict)


class TestSafeStageLoader:
    """Tests for safe stage loading."""

    def test_load_builtin_stage(self):
        """Test loading built-in stage."""
        loader = SafeStageLoader()

        config = StageConfig(
            name="test_transform",
            type="transform",
            module="pipeline_core.stage_types.TransformStage",
            class_name="TransformStage",
            parameters={}
        )

        # This should work for built-in stages
        stage_class = loader.load_stage(config)
        assert stage_class is not None

    def test_load_invalid_module(self):
        """Test loading from invalid module fails securely."""
        loader = SafeStageLoader(allowed_modules=["allowed.module"])

        config = StageConfig(
            name="test_stage",
            type="transform",
            module="disallowed.module",  # Not allowed
            class_name="TestStage",
            parameters={}
        )

        with pytest.raises(StageLoadError):
            loader.load_stage(config)

    @patch('importlib.import_module')
    def test_load_nonexistent_class(self, mock_import):
        """Test loading nonexistent class fails."""
        # Mock module with no class
        mock_module = type('MockModule', (), {})()
        mock_import.return_value = mock_module

        loader = SafeStageLoader()

        config = StageConfig(
            name="test_stage",
            type="transform",
            module="test.module",
            class_name="NonExistentClass",
            parameters={}
        )

        with pytest.raises(StageLoadError):
            loader.load_stage(config)


class TestPipelineBuilder:
    """Tests for pipeline builder."""

    def test_build_simple_pipeline(self):
        """Test building a simple pipeline."""
        config = PipelineConfig(
            name="test_pipeline",
            description="Test pipeline",
            version="1.0.0",
            stages=[
                StageConfig(
                    name="test_stage",
                    type="transform",
                    module="pipeline_core.stage_types.TransformStage",
                    class_name="TransformStage",
                    parameters={}
                )
            ],
            queues=[],
            global_settings={}
        )

        builder = YamlPipelineBuilder()
        runner = builder.build_pipeline(config)

        assert runner is not None
        assert len(runner._stages) == 1
        assert runner._stages[0].name == "test_stage"

    def test_build_pipeline_with_invalid_stage(self):
        """Test building pipeline with invalid stage fails."""
        config = PipelineConfig(
            name="test_pipeline",
            description="Test pipeline",
            version="1.0.0",
            stages=[
                StageConfig(
                    name="invalid_stage",
                    type="transform",
                    module="nonexistent.module",
                    class_name="NonExistentStage",
                    parameters={}
                )
            ],
            queues=[],
            global_settings={}
        )

        builder = YamlPipelineBuilder()
        with pytest.raises(PipelineBuildError):
            builder.build_pipeline(config)


class TestSecureConfigLoader:
    """Tests for secure configuration loading."""

    def test_load_valid_config_file(self):
        """Test loading valid configuration file."""
        config_content = """
name: "test_pipeline"
version: "1.0.0"
stages:
  - name: "test_stage"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
    parameters: {}
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            loader = SecureConfigLoader()
            config = loader.load_config(config_file)

            assert config.name == "test_pipeline"
            assert config.version == "1.0.0"
            assert len(config.stages) == 1

        finally:
            Path(config_file).unlink()

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML fails."""
        invalid_yaml = """
name: "test_pipeline"
version: "1.0.0"
stages:
  - name: "test_stage"
    type: "transform"
    module: "test.module"
    class_name: "TestStage"
  invalid_yaml_syntax: [
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            config_file = f.name

        try:
            loader = SecureConfigLoader()
            with pytest.raises(ConfigLoadError):
                loader.load_config(config_file)

        finally:
            Path(config_file).unlink()

    def test_environment_variable_substitution(self):
        """Test environment variable substitution."""
        import os
        os.environ["TEST_VAR"] = "substituted_value"

        try:
            config_content = """
name: "test_pipeline"
version: "1.0.0"
description: "${TEST_VAR}"
stages: []
"""

            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(config_content)
                config_file = f.name

            try:
                loader = SecureConfigLoader()
                config = loader.load_config(config_file)

                assert config.description == "substituted_value"

            finally:
                Path(config_file).unlink()

        finally:
            del os.environ["TEST_VAR"]

    def test_disallowed_path(self):
        """Test loading from disallowed path fails."""
        config_content = "name: test"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            # Restrict to /tmp only
            loader = SecureConfigLoader(allowed_paths=["/tmp"])
            config = loader.load_config(config_file)  # Should work if in /tmp

            # Now restrict to non-existent path
            loader_strict = SecureConfigLoader(allowed_paths=["/nonexistent"])
            with pytest.raises(ConfigLoadError):
                loader_strict.load_config(config_file)

        finally:
            Path(config_file).unlink()


class TestConfigManager:
    """Tests for configuration manager."""

    def test_config_manager_loading(self):
        """Test configuration manager loading."""
        config_content = """
name: "managed_pipeline"
version: "1.0.0"
stages:
  - name: "test_stage"
    type: "transform"
    module: "pipeline_core.stage_types"
    class_name: "TransformStage"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.yaml"
            config_file.write_text(config_content)

            manager = ConfigManager([temp_dir])

            # List configs
            configs = manager.list_configs()
            assert "test_config" in configs

            # Load config
            config = manager.load_config("test_config")
            assert config.name == "managed_pipeline"

            # Test caching
            config2 = manager.load_config("test_config")
            assert config is config2  # Should be cached

    def test_config_not_found(self):
        """Test loading non-existent config fails."""
        manager = ConfigManager(["/tmp"])

        with pytest.raises(ConfigLoadError):
            manager.load_config("nonexistent_config")


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])

