"""
Application Configuration

Configure your AI Framework settings here.
"""

from aiframework import FrameworkConfig, Mode

# Development configuration
def get_development_config() -> FrameworkConfig:
    """Get configuration for development environment."""
    return FrameworkConfig(
        mode=Mode.DEVELOPMENT
        # Add custom settings here
    )

# Production configuration
def get_production_config() -> FrameworkConfig:
    """Get configuration for production environment."""
    return FrameworkConfig(
        mode=Mode.PRODUCTION
        # Add production settings here
    )

# Get appropriate configuration based on environment
def get_config():
    """Get configuration based on current environment."""
    import os
    if os.getenv("ENVIRONMENT") == "production":
        return get_production_config()
    else:
        return get_development_config()
