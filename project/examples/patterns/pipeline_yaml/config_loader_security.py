"""
Security features for configuration loading.

This module contains security-related functionality for
safe configuration loading including environment variable
processing and path validation.
"""

import os
import re
from typing import List, Optional
from pathlib import Path

from .config_loader_core import SecureConfigLoader, ConfigLoadError


def _process_env_vars_secure(
    self: SecureConfigLoader,
    yaml_content: str
) -> str:
    """Process environment variable substitution in YAML content.

    Args:
        yaml_content: Raw YAML content.

    Returns:
        Processed YAML content with env vars substituted.

    Raises:
        ConfigLoadError: If env var processing fails.
    """
    def replace_env_var(match):
        var_name = match.group(1)

        # Validate env var access
        if self.allowed_env_vars:
            allowed = any(var_name.startswith(prefix) for prefix in self.allowed_env_vars)
            if not allowed:
                raise ConfigLoadError(f"Environment variable not allowed: {var_name}")

        # Get environment variable
        var_value = os.getenv(var_name)
        if var_value is None:
            raise ConfigLoadError(f"Environment variable not set: {var_name}")

        return var_value

    # Pattern for ${VAR_NAME} or $VAR_NAME
    pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
    try:
        return re.sub(pattern, replace_env_var, yaml_content)
    except Exception as e:
        raise ConfigLoadError(f"Environment variable processing failed: {e}") from e


def _list_available_configs_secure(
    self: SecureConfigLoader,
    config_dir: str
) -> List[str]:
    """List available configuration files in a directory.

    Args:
        config_dir: Directory to scan for config files.

    Returns:
        List of configuration file paths.

    Raises:
        ConfigLoadError: If directory scan fails.
    """
    try:
        config_path = Path(config_dir)

        if not self.allowed_paths:
            pass  # Allow all if no restrictions
        elif not any(config_path.is_relative_to(allowed) for allowed in self.allowed_paths):
            raise ConfigLoadError(f"Config directory not allowed: {config_dir}")

        if not config_path.exists() or not config_path.is_dir():
            raise ConfigLoadError(f"Config directory does not exist: {config_dir}")

        # Find YAML files
        yaml_files = []
        for yaml_file in config_path.glob("**/*.yaml"):
            yaml_files.append(str(yaml_file))
        for yml_file in config_path.glob("**/*.yml"):
            yaml_files.append(str(yml_file))

        return yaml_files

    except Exception as e:
        raise ConfigLoadError(f"Failed to list config files: {e}") from e


# Monkey patch the secure methods onto SecureConfigLoader
SecureConfigLoader._process_env_vars = _process_env_vars_secure
SecureConfigLoader.list_available_configs = _list_available_configs_secure


# Update the main SecureConfigLoader to use secure env var processing
original_load_config = SecureConfigLoader.load_config

def load_config_with_env_processing(self, config_path: str):
    """Load config with environment variable processing."""
    try:
        # Validate file path security
        self._validate_file_path(config_path)

        # Load YAML content
        yaml_content = self._load_yaml_file(config_path)

        # Process environment variables
        processed_content = self._process_env_vars(yaml_content)

        # Parse and validate configuration
        config_dict = self._parse_yaml_content(processed_content)
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

SecureConfigLoader.load_config = load_config_with_env_processing

