"""
Basic unit tests for YAML pipeline configuration.

This module contains fundamental tests for configuration schema,
safe loading, and basic pipeline building functionality.
"""

import pytest
from typing import Any

from .config_schema import (
    PipelineConfig, StageConfig, QueueConfig,
    ConfigValidationError, validate_pipeline_config
)
from .safe_loader import SafeStageLoader, StageLoadError


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
            module="nonexistent.module",
            class_name="NonExistentClass",
            parameters={}
        )

        with pytest.raises(StageLoadError):
            loader.load_stage(config)


if __name__ == "__main__":
    """Run basic tests when executed directly."""
    pytest.main([__file__, "-v"])

