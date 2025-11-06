"""
YAML-driven pipeline builder.

This module provides functionality to build complete pipelines
from YAML configurations, including stage instantiation and
queue setup.
"""

import logging
from typing import Dict, Any, Optional, List

from ..pipeline_core.runner import PipelineRunner
from ..pipeline_core.stage_base import PipelineStage
from ..pipeline_core.queue import create_message_queue
from .config_schema import PipelineConfig, QueueConfig
from .safe_loader import create_stage_from_config, SafeStageLoader


class PipelineBuildError(Exception):
    """Raised when pipeline building fails."""
    pass


class YamlPipelineBuilder:
    """Builds pipelines from YAML configurations."""

    def __init__(
        self,
        allowed_modules: Optional[List[str]] = None,
        stage_registry: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize the pipeline builder.

        Args:
            allowed_modules: List of allowed module prefixes for stage loading.
            stage_registry: Optional pre-registered stages.
        """
        self.allowed_modules = allowed_modules
        self.stage_registry = stage_registry or {}
        self._logger = logging.getLogger(__name__)

        # Initialize stage loader
        self._loader = SafeStageLoader(allowed_modules)

    def build_pipeline(self, config: PipelineConfig) -> PipelineRunner:
        """Build a complete pipeline from configuration.

        Args:
            config: Validated pipeline configuration.

        Returns:
            Configured PipelineRunner instance.

        Raises:
            PipelineBuildError: If building fails.
        """
        try:
            self._logger.info(
                f"Building pipeline '{config.name}' with {len(config.stages)} stages",
                extra={"pipeline_name": config.name, "stage_count": len(config.stages)}
            )

            # Build stages
            stages = self._build_stages(config)

            # Create custom queue factory
            queue_factory = self._create_queue_factory(config)

            # Get max workers from global settings
            max_workers = config.global_settings.get("max_workers")

            # Create pipeline runner
            runner = PipelineRunner(
                stages=stages,
                queue_factory=queue_factory,
                max_workers=max_workers
            )

            self._logger.info(
                f"Successfully built pipeline '{config.name}'",
                extra={"pipeline_name": config.name}
            )

            return runner

        except Exception as e:
            error_msg = f"Failed to build pipeline '{config.name}': {e}"
            self._logger.error(
                error_msg,
                extra={"pipeline_name": config.name, "error_type": type(e).__name__},
                exc_info=True
            )
            raise PipelineBuildError(error_msg) from e

    def _build_stages(self, config: PipelineConfig) -> List[PipelineStage]:
        """Build stage instances from configuration.

        Args:
            config: Pipeline configuration.

        Returns:
            List of instantiated stage objects.
        """
        stages = []

        for stage_config in config.stages:
            try:
                # Create stage from configuration
                stage = create_stage_from_config(stage_config, self.allowed_modules)
                stages.append(stage)

                self._logger.debug(
                    f"Built stage '{stage_config.name}' of type {stage_config.type.value}",
                    extra={
                        "stage_name": stage_config.name,
                        "stage_type": stage_config.type.value,
                        "module": stage_config.module
                    }
                )

            except Exception as e:
                raise PipelineBuildError(f"Failed to build stage '{stage_config.name}': {e}") from e

        return stages

    def _create_queue_factory(self, config: PipelineConfig):
        """Create a queue factory function from configuration.

        Args:
            config: Pipeline configuration.

        Returns:
            Queue factory function.
        """
        # Create queue configuration map
        queue_configs = {queue.name: queue for queue in config.queues}

        def queue_factory(name: str, maxsize: int = 0, **kwargs):
            """Factory function for creating queues."""
            if name in queue_configs:
                queue_config = queue_configs[name]
                # Use configured maxsize if not overridden
                actual_maxsize = kwargs.get('maxsize', queue_config.maxsize)
                queue_params = {**queue_config.parameters, **kwargs}

                return create_message_queue(
                    queue_type=queue_config.type.value,
                    maxsize=actual_maxsize,
                    name=name,
                    **queue_params
                )
            else:
                # Fallback to default queue creation
                return create_message_queue(
                    queue_type="memory",
                    maxsize=maxsize,
                    name=name,
                    **kwargs
                )

        return queue_factory

    def validate_configuration(self, config: PipelineConfig) -> List[str]:
        """Validate that a pipeline configuration can be built.

        Args:
            config: Pipeline configuration to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        try:
            # Try to build stages (without actually instantiating)
            for stage_config in config.stages:
                try:
                    # Just validate that the stage can be loaded
                    stage_class = self._loader.load_stage(stage_config)
                    # Basic validation
                    if not hasattr(stage_class, '__init__'):
                        errors.append(f"Stage {stage_config.name}: Invalid class {stage_class}")
                except Exception as e:
                    errors.append(f"Stage {stage_config.name}: {e}")

            # Validate queues
            queue_names = {queue.name for queue in config.queues}
            for stage in config.stages:
                if stage.input_queue and stage.input_queue not in queue_names:
                    errors.append(f"Stage {stage.name}: Input queue '{stage.input_queue}' not defined")

                if stage.output_queues:
                    for queue_name in stage.output_queues:
                        if queue_name not in queue_names:
                            errors.append(f"Stage {stage.name}: Output queue '{queue_name}' not defined")

        except Exception as e:
            errors.append(f"Configuration validation failed: {e}")

        return errors


def build_pipeline_from_yaml(
    yaml_content: str,
    allowed_modules: Optional[List[str]] = None
) -> PipelineRunner:
    """Convenience function to build pipeline from YAML string.

    Args:
        yaml_content: YAML configuration as string.
        allowed_modules: List of allowed module prefixes.

    Returns:
        Configured PipelineRunner instance.

    Raises:
        PipelineBuildError: If building fails.
    """
    try:
        import yaml
    except ImportError:
        raise PipelineBuildError("PyYAML is required for YAML pipeline configuration")

    try:
        # Parse YAML
        config_dict = yaml.safe_load(yaml_content)

        # Validate configuration
        from .config_schema import validate_pipeline_config
        config = validate_pipeline_config(config_dict)

        # Build pipeline
        builder = YamlPipelineBuilder(allowed_modules)
        return builder.build_pipeline(config)

    except yaml.YAMLError as e:
        raise PipelineBuildError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        raise PipelineBuildError(f"Failed to build pipeline from YAML: {e}") from e


def build_pipeline_from_file(
    yaml_file_path: str,
    allowed_modules: Optional[List[str]] = None
) -> PipelineRunner:
    """Convenience function to build pipeline from YAML file.

    Args:
        yaml_file_path: Path to YAML configuration file.
        allowed_modules: List of allowed module prefixes.

    Returns:
        Configured PipelineRunner instance.

    Raises:
        PipelineBuildError: If building fails.
    """
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()

        return build_pipeline_from_yaml(yaml_content, allowed_modules)

    except FileNotFoundError:
        raise PipelineBuildError(f"YAML file not found: {yaml_file_path}")
    except IOError as e:
        raise PipelineBuildError(f"Failed to read YAML file {yaml_file_path}: {e}")

