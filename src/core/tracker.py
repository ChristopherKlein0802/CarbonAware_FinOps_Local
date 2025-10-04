"""Backward compatible shim for the legacy RuntimeTracker import path."""

from ..services.runtime import RuntimeService as RuntimeTracker

__all__ = ['RuntimeTracker']
