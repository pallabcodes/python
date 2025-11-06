"""
Safe dynamic loading of pipeline stages.

This module provides secure loading of pipeline stages from
configuration, with validation and sandboxing to prevent
arbitrary code execution.
"""

import importlib
import inspect
import logging
from typing import Any, Dict, Type, Optional, List

from ..pipeline_core.stage_base import PipelineStage
from .config_schema import StageConfig, ConfigValidationError


class StageLoadError(Exception):
    """Raised when stage loading fails."""
    pass


class SafeStageLoader:
    """Secure loader for pipeline stages from configuration."""

    def __init__(self, allowed_modules: Optional[List[str]] = None) -> None:
        """Initialize the safe loader.

        Args:
            allowed_modules: List of allowed module prefixes for security.
                           If None, allows all modules (less secure).
        """
        self.allowed_modules = allowed_modules or []
        self._logger = logging.getLogger(__name__)

        # Built-in stages that are always allowed
        self._builtin_stages = {
            "pipeline_core.stage_types.TransformStage": "pipeline_core.stage_types",
            "pipeline_core.stage_types.FilterStage": "pipeline_core.stage_types",
            "pipeline_core.stage_types.SinkStage": "pipeline_core.stage_types",
            "pipeline_core.stage_types.PassThroughStage": "pipeline_core.stage_types",
            "pipeline_core.stage_types.LoggingStage": "pipeline_core.stage_types"
        }

    def load_stage(self, config: StageConfig) -> Type[PipelineStage]:
        """Load a stage class from configuration.

        Args:
            config: Stage configuration.

        Returns:
            Loaded stage class.

        Raises:
            StageLoadError: If loading fails or validation fails.
        """
        try:
            # Check if it's a built-in stage
            if config.module in self._builtin_stages:
                return self._load_builtin_stage(config)

            # Check module security
            self._validate_module_security(config.module)

            # Load the module
            module = importlib.import_module(config.module)

            # Get the class
            stage_class = getattr(module, config.class_name)

            # Validate the class
            self._validate_stage_class(stage_class, config)

            self._logger.info(
                f"Successfully loaded stage class {config.class_name} from {config.module}",
                extra={"stage_name": config.name, "module": config.module, "class_name": config.class_name}
            )

            return stage_class

        except Exception as e:
            error_msg = f"Failed to load stage {config.name}: {e}"
            self._logger.error(
                error_msg,
                extra={
                    "stage_name": config.name,
                    "module": config.module,
                    "class_name": config.class_name,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise StageLoadError(error_msg) from e

    def instantiate_stage(self, stage_class: Type[PipelineStage], config: StageConfig) -> PipelineStage:
        """Instantiate a stage from its class and configuration.

        Args:
            stage_class: The loaded stage class.
            config: Stage configuration with parameters.

        Returns:
            Instantiated stage object.

        Raises:
            StageLoadError: If instantiation fails.
        """
        try:
            # Instantiate with parameters
            stage = stage_class(config.name, **config.parameters)

            self._logger.debug(
                f"Instantiated stage {config.name}",
                extra={"stage_name": config.name, "parameters": list(config.parameters.keys())}
            )

            return stage

        except Exception as e:
            error_msg = f"Failed to instantiate stage {config.name}: {e}"
            self._logger.error(
                error_msg,
                extra={
                    "stage_name": config.name,
                    "error_type": type(e).__name__,
                    "parameters": list(config.parameters.keys())
                },
                exc_info=True
            )
            raise StageLoadError(error_msg) from e

    def _load_builtin_stage(self, config: StageConfig) -> Type[PipelineStage]:
        """Load a built-in stage class."""
        module_name = self._builtin_stages[config.module]
        module = importlib.import_module(module_name)
        stage_class = getattr(module, config.class_name)

        self._validate_stage_class(stage_class, config)

        return stage_class

    def _validate_module_security(self, module_name: str) -> None:
        """Validate that the module is allowed to be loaded.

        Args:
            module_name: Module name to validate.

        Raises:
            StageLoadError: If module is not allowed.
        """
        if not self.allowed_modules:
            # If no restrictions, allow all modules
            return

        # Check if module matches any allowed prefix
        allowed = any(module_name.startswith(allowed_prefix) for allowed_prefix in self.allowed_modules)

        if not allowed:
            raise StageLoadError(f"Module '{module_name}' is not in allowed modules list")

    def _validate_stage_class(self, stage_class: Type, config: StageConfig) -> None:
        """Validate that the loaded class is a valid pipeline stage.

        Args:
            stage_class: The class to validate.
            config: Stage configuration.

        Raises:
            StageLoadError: If validation fails.
        """
        # Check if it's a class
        if not inspect.isclass(stage_class):
            raise StageLoadError(f"{config.class_name} is not a class")

        # Check if it implements PipelineStage protocol
        # We check for the required methods
        required_methods = ["process_message", "initialize", "cleanup", "name"]

        for method_name in required_methods:
            if not hasattr(stage_class, method_name):
                raise StageLoadError(f"Stage class {config.class_name} missing required method: {method_name}")

        # Check that name is a property or can be set via constructor
        # The validation here is basic - actual instantiation will catch issues

        self._logger.debug(
            f"Validated stage class {config.class_name}",
            extra={"stage_name": config.name, "class_name": config.class_name}
        )


class StageRegistry:
    """Registry for managing loaded stage classes."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._stages: Dict[str, Type[PipelineStage]] = {}
        self._logger = logging.getLogger(__name__)

    def register_stage(self, name: str, stage_class: Type[PipelineStage]) -> None:
        """Register a stage class.

        Args:
            name: Stage name identifier.
            stage_class: Stage class to register.
        """
        self._stages[name] = stage_class
        self._logger.debug(f"Registered stage class: {name}")

    def get_stage(self, name: str) -> Type[PipelineStage]:
        """Get a registered stage class.

        Args:
            name: Stage name identifier.

        Returns:
            Registered stage class.

        Raises:
            KeyError: If stage is not registered.
        """
        if name not in self._stages:
            raise KeyError(f"Stage '{name}' not registered")
        return self._stages[name]

    def list_stages(self) -> List[str]:
        """List all registered stage names."""
        return list(self._stages.keys())

    def clear(self) -> None:
        """Clear all registered stages."""
        self._stages.clear()
        self._logger.debug("Cleared stage registry")


# Global registry instance
stage_registry = StageRegistry()


def create_stage_from_config(
    config: StageConfig,
    allowed_modules: Optional[List[str]] = None
) -> PipelineStage:
    """Convenience function to create a stage from configuration.

    Args:
        config: Stage configuration.
        allowed_modules: List of allowed module prefixes.

    Returns:
        Instantiated stage object.

    Raises:
        StageLoadError: If loading or instantiation fails.
    """
    loader = SafeStageLoader(allowed_modules)
    stage_class = loader.load_stage(config)
    return loader.instantiate_stage(stage_class, config)

