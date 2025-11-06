"""
Core configuration loading functionality.

This module contains the main configuration loading classes
and interfaces for YAML pipeline configurations.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config_schema import validate_pipeline_config, PipelineConfig, ConfigValidationError


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""
    pass


class SecureConfigLoader:
    """Secure loader for YAML pipeline configurations."""

    def __init__(
        self,
        allowed_paths: Optional[List[str]] = None,
        allowed_env_vars: Optional[List[str]] = None
    ) -> None:
        """Initialize the secure config loader.

        Args:
            allowed_paths: List of allowed directory paths for config files.
                         If None, allows all paths (less secure).
            allowed_env_vars: List of allowed environment variable prefixes.
                            If None, allows all env vars (less secure).
        """
        self.allowed_paths = [Path(p).resolve() for p in (allowed_paths or [])]
        self.allowed_env_vars = allowed_env_vars or []
        self._logger = logging.getLogger(__name__)

    def load_config(self, config_path: str) -> PipelineConfig:
        """Load and validate pipeline configuration from file.

        Args:
            config_path: Path to YAML configuration file.

        Returns:
            Validated PipelineConfig instance.

        Raises:
            ConfigLoadError: If loading or validation fails.
        """
        try:
            # Validate file path security
            self._validate_file_path(config_path)

            # Load YAML content
            yaml_content = self._load_yaml_file(config_path)

            # Parse and validate configuration
            config_dict = self._parse_yaml_content(yaml_content)
            config = validate_pipeline_config(config_dict)

            self._logger.info(
                f"Successfully loaded pipeline config '{config.name}' from {config_path}",
                extra={"pipeline_name": config.name, "config_path": config_path}
            )

            return config

        except Exception as e:
            error_msg = f"Failed to load config from {config_path}: {e}"
            self._logger.error(
                error_msg,
                extra={"config_path": config_path, "error_type": type(e).__name__},
                exc_info=True
            )
            raise ConfigLoadError(error_msg) from e

    def _validate_file_path(self, config_path: str) -> None:
        """Validate that the config file path is allowed.

        Args:
            config_path: Path to validate.

        Raises:
            ConfigLoadError: If path is not allowed.
        """
        if not self.allowed_paths:
            # If no path restrictions, allow all paths
            return

        config_file = Path(config_path).resolve()

        # Check if file is within allowed directories
        allowed = any(
            config_file.is_relative_to(allowed_path) or allowed_path in config_file.parents
            for allowed_path in self.allowed_paths
        )

        if not allowed:
            raise ConfigLoadError(f"Config file path not allowed: {config_path}")

        # Additional security checks
        if not config_file.exists():
            raise ConfigLoadError(f"Config file does not exist: {config_path}")

        if not config_file.is_file():
            raise ConfigLoadError(f"Path is not a file: {config_path}")

        # Check file extension
        if config_file.suffix.lower() not in ['.yaml', '.yml']:
            raise ConfigLoadError(f"Invalid file extension: {config_file.suffix}")

    def _load_yaml_file(self, config_path: str) -> str:
        """Load YAML file content.

        Args:
            config_path: Path to YAML file.

        Returns:
            File content as string.

        Raises:
            ConfigLoadError: If file cannot be read.
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError as e:
            raise ConfigLoadError(f"Invalid file encoding: {e}") from e
        except IOError as e:
            raise ConfigLoadError(f"Failed to read file: {e}") from e

    def _parse_yaml_content(self, yaml_content: str) -> Dict[str, Any]:
        """Parse YAML content into dictionary.

        Args:
            yaml_content: YAML content as string.

        Returns:
            Parsed configuration dictionary.

        Raises:
            ConfigLoadError: If YAML parsing fails.
        """
        try:
            import yaml
        except ImportError:
            raise ConfigLoadError("PyYAML is required for YAML configuration loading")

        try:
            config_dict = yaml.safe_load(yaml_content)
            if not isinstance(config_dict, dict):
                raise ConfigLoadError("YAML root must be a dictionary")

            return config_dict

        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML syntax: {e}") from e


class ConfigManager:
    """Manager for loading and caching pipeline configurations."""

    def __init__(
        self,
        config_dirs: Optional[List[str]] = None,
        allowed_modules: Optional[List[str]] = None,
        cache_configs: bool = True
    ) -> None:
        """Initialize the configuration manager.

        Args:
            config_dirs: List of directories to search for configs.
            allowed_modules: List of allowed module prefixes.
            cache_configs: Whether to cache loaded configurations.
        """
        self.config_dirs = config_dirs or []
        self.allowed_modules = allowed_modules or []
        self.cache_configs = cache_configs
        self._config_cache: Dict[str, PipelineConfig] = {}
        self._loader = SecureConfigLoader(self.config_dirs, self.allowed_modules)
        self._logger = logging.getLogger(__name__)

    def load_config(self, config_name: str) -> PipelineConfig:
        """Load a configuration by name.

        Args:
            config_name: Configuration name (with or without .yaml extension).

        Returns:
            Loaded and validated configuration.

        Raises:
            ConfigLoadError: If loading fails.
        """
        # Check cache first
        if self.cache_configs and config_name in self._config_cache:
            return self._config_cache[config_name]

        # Find config file
        config_path = self._find_config_file(config_name)
        if not config_path:
            raise ConfigLoadError(f"Configuration not found: {config_name}")

        # Load configuration
        config = self._loader.load_config(config_path)

        # Cache if enabled
        if self.cache_configs:
            self._config_cache[config_name] = config

        return config

    def _find_config_file(self, config_name: str) -> Optional[str]:
        """Find configuration file by name.

        Args:
            config_name: Configuration name.

        Returns:
            Full path to config file or None if not found.
        """
        # Add .yaml extension if not present
        if not config_name.endswith(('.yaml', '.yml')):
            config_name += '.yaml'

        # Search in config directories
        for config_dir in self.config_dirs:
            config_path = Path(config_dir) / config_name
            if config_path.exists():
                return str(config_path)

        return None

    def list_configs(self) -> List[str]:
        """List all available configurations.

        Returns:
            List of configuration names.
        """
        configs = set()

        for config_dir in self.config_dirs:
            try:
                available = self._loader.list_available_configs(config_dir)
                for config_path in available:
                    config_name = Path(config_path).stem  # Remove extension
                    configs.add(config_name)
            except ConfigLoadError:
                # Skip directories that can't be accessed
                continue

        return sorted(configs)

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
        self._logger.debug("Cleared configuration cache")


# Convenience functions
def load_pipeline_config(config_path: str) -> PipelineConfig:
    """Load pipeline configuration from file.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        Validated PipelineConfig instance.
    """
    loader = SecureConfigLoader()
    return loader.load_config(config_path)


def create_config_manager(
    config_dirs: List[str],
    allowed_modules: Optional[List[str]] = None
) -> ConfigManager:
    """Create a configuration manager.

    Args:
        config_dirs: List of directories to search for configs.
        allowed_modules: List of allowed module prefixes.

    Returns:
        ConfigManager instance.
    """
    return ConfigManager(config_dirs, allowed_modules)

