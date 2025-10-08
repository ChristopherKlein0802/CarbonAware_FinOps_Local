"""
Configuration Package

This package manages all application configuration including environment-specific settings.

Modules:
    settings: Main Pydantic settings (environment variables, API keys)
"""

# Re-export for convenient access
from .settings import settings, Settings

__all__ = ["settings", "Settings"]
