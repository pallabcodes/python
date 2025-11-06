"""
YAML configuration schema and validation.

This module defines the schema for YAML pipeline configurations
and provides validation logic to ensure configuration correctness.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class StageType(Enum):
    """Supported stage types in YAML configuration."""
    TRANSFORM = "transform"
    FILTER = "filter"
    SINK = "sink"
    CUSTOM = "custom"


class QueueType(Enum):
    """Supported queue types in YAML configuration."""
    MEMORY = "memory"


@dataclass
class StageConfig:
    """Configuration for a single pipeline stage."""
    name: str
    type: StageType
    module: str
    class_name: str
    parameters: Dict[str, Any]
    input_queue: Optional[str] = None
    output_queues: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.type.value,
            "module": self.module,
            "class_name": self.class_name,
            "parameters": self.parameters.copy(),
            "input_queue": self.input_queue,
            "output_queues": self.output_queues.copy() if self.output_queues else None
        }


@dataclass
class QueueConfig:
    """Configuration for a message queue."""
    name: str
    type: QueueType
    maxsize: int
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.type.value,
            "maxsize": self.maxsize,
            "parameters": self.parameters.copy()
        }


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    name: str
    description: Optional[str]
    version: str
    stages: List[StageConfig]
    queues: List[QueueConfig]
    global_settings: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "stages": [stage.to_dict() for stage in self.stages],
            "queues": [queue.to_dict() for queue in self.queues],
            "global_settings": self.global_settings.copy()
        }


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigValidator:
    """Validates YAML pipeline configurations."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.errors: List[str] = []

    def validate_config(self, config_dict: Dict[str, Any]) -> PipelineConfig:
        """Validate and parse configuration dictionary.

        Args:
            config_dict: Raw configuration dictionary from YAML.

        Returns:
            Validated PipelineConfig instance.

        Raises:
            ConfigValidationError: If validation fails.
        """
        self.errors = []

        try:
            # Validate top-level structure
            self._validate_top_level(config_dict)

            # Parse configuration
            config = self._parse_config(config_dict)

            # Validate cross-references
            self._validate_cross_references(config)

            if self.errors:
                raise ConfigValidationError(f"Configuration validation failed: {self.errors}")

            return config

        except Exception as e:
            self.errors.append(f"Configuration parsing failed: {e}")
            raise ConfigValidationError(f"Configuration validation failed: {self.errors}")

    def _validate_top_level(self, config: Dict[str, Any]) -> None:
        """Validate top-level configuration structure."""
        required_fields = ["name", "version", "stages"]
        for field in required_fields:
            if field not in config:
                self.errors.append(f"Missing required field: {field}")

        if "stages" in config and not isinstance(config["stages"], list):
            self.errors.append("stages must be a list")

        if "queues" in config and not isinstance(config["queues"], list):
            self.errors.append("queues must be a list")

    def _parse_config(self, config_dict: Dict[str, Any]) -> PipelineConfig:
        """Parse configuration dictionary into PipelineConfig."""
        # Parse stages
        stages = []
        for stage_dict in config_dict.get("stages", []):
            stage = self._parse_stage_config(stage_dict)
            stages.append(stage)

        # Parse queues
        queues = []
        for queue_dict in config_dict.get("queues", []):
            queue = self._parse_queue_config(queue_dict)
            queues.append(queue)

        return PipelineConfig(
            name=config_dict["name"],
            description=config_dict.get("description"),
            version=config_dict["version"],
            stages=stages,
            queues=queues,
            global_settings=config_dict.get("global_settings", {})
        )

    def _parse_stage_config(self, stage_dict: Dict[str, Any]) -> StageConfig:
        """Parse individual stage configuration."""
        # Validate required fields
        required = ["name", "type", "module", "class_name"]
        for field in required:
            if field not in stage_dict:
                self.errors.append(f"Stage missing required field: {field}")

        # Validate stage type
        try:
            stage_type = StageType(stage_dict["type"])
        except ValueError:
            self.errors.append(f"Invalid stage type: {stage_dict['type']}")

        # Validate parameters
        parameters = stage_dict.get("parameters", {})
        if not isinstance(parameters, dict):
            self.errors.append(f"Stage {stage_dict.get('name', 'unknown')} parameters must be a dict")

        return StageConfig(
            name=stage_dict["name"],
            type=stage_type,
            module=stage_dict["module"],
            class_name=stage_dict["class_name"],
            parameters=parameters,
            input_queue=stage_dict.get("input_queue"),
            output_queues=stage_dict.get("output_queues")
        )

    def _parse_queue_config(self, queue_dict: Dict[str, Any]) -> QueueConfig:
        """Parse individual queue configuration."""
        # Validate required fields
        required = ["name", "type"]
        for field in required:
            if field not in queue_dict:
                self.errors.append(f"Queue missing required field: {field}")

        # Validate queue type
        try:
            queue_type = QueueType(queue_dict["type"])
        except ValueError:
            self.errors.append(f"Invalid queue type: {queue_dict['type']}")

        # Validate maxsize
        maxsize = queue_dict.get("maxsize", 0)
        if not isinstance(maxsize, int) or maxsize < 0:
            self.errors.append(f"Queue maxsize must be non-negative integer, got: {maxsize}")

        return QueueConfig(
            name=queue_dict["name"],
            type=queue_type,
            maxsize=maxsize,
            parameters=queue_dict.get("parameters", {})
        )

    def _validate_cross_references(self, config: PipelineConfig) -> None:
        """Validate cross-references between stages and queues."""
        # Collect queue names
        queue_names = {queue.name for queue in config.queues}

        # Validate stage queue references
        for stage in config.stages:
            if stage.input_queue and stage.input_queue not in queue_names:
                self.errors.append(f"Stage {stage.name} references unknown input queue: {stage.input_queue}")

            if stage.output_queues:
                for queue_name in stage.output_queues:
                    if queue_name not in queue_names:
                        self.errors.append(f"Stage {stage.name} references unknown output queue: {queue_name}")

        # Check for duplicate stage names
        stage_names = [stage.name for stage in config.stages]
        if len(stage_names) != len(set(stage_names)):
            duplicates = [name for name in stage_names if stage_names.count(name) > 1]
            self.errors.append(f"Duplicate stage names found: {duplicates}")

        # Check for duplicate queue names
        queue_name_list = [queue.name for queue in config.queues]
        if len(queue_name_list) != len(set(queue_name_list)):
            duplicates = [name for name in queue_name_list if queue_name_list.count(name) > 1]
            self.errors.append(f"Duplicate queue names found: {duplicates}")


def validate_pipeline_config(config_dict: Dict[str, Any]) -> PipelineConfig:
    """Convenience function to validate pipeline configuration.

    Args:
        config_dict: Raw configuration dictionary.

    Returns:
        Validated PipelineConfig instance.

    Raises:
        ConfigValidationError: If validation fails.
    """
    validator = ConfigValidator()
    return validator.validate_config(config_dict)

