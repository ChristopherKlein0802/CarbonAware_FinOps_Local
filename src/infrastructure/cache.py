"""
Infrastructure Cache - Filesystem-based caching and time-series persistence

This module consolidates all caching functionality:
- FileCacheRepository: JSON file caching with TTL validation (implements CacheRepository protocol)
- JsonTimeSeriesStore: Time-series data persistence
- CacheTTL: Standardized cache TTL values

Clean Architecture:
FileCacheRepository implements the src.domain.protocols.CacheRepository protocol,
allowing domain services to depend on abstractions rather than concrete implementations.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Iterable, List, Dict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheTTL:
    """Standard cache TTL values used across the application (minutes)."""

    CARBON_DATA: int = 60  # ElectricityMaps updates hourly
    CARBON_24H: int = 60  # Historical data synchronized with hourly updates (changed from 120)
    POWER_DATA: int = 10080  # Hardware specs rarely change (7 days)
    PRICING_DATA: int = 10080  # AWS pricing stable (7 days)
    COST_DATA: int = 1440  # Cost Explorer updates daily (24 hours)
    CPU_UTILIZATION: int = 60  # CloudWatch metrics aligned with grid data (1 hour)
    CLOUDTRAIL_EVENTS: int = 180  # Runtime events cache (3 hours, balanced refresh rate)
    INSTANCE_METADATA: int = 525600  # Launch time immutable (365 days)


class FileCacheRepository:
    """
    Filesystem-backed cache repository with JSON convenience helpers.

    Implements: src.domain.protocols.CacheRepository

    This concrete implementation satisfies the CacheRepository protocol through
    structural subtyping (duck typing). Domain services depend on the protocol,
    not this concrete class.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def path(self, *parts: str, extension: str = "json") -> Path:
        """Return a fully-qualified cache path within the repository root."""

        safe_parts = [segment.strip("/ ") for segment in parts if segment]
        if not safe_parts:
            raise ValueError("at least one cache path segment is required")
        filename = safe_parts[-1]
        directory = self._root.joinpath("api_data", *safe_parts[:-1])
        directory.mkdir(parents=True, exist_ok=True)
        if "." not in filename:
            filename = f"{filename}.{extension}"
        return directory / filename

    def is_valid(self, path: Path, max_age_minutes: int) -> bool:
        """Check whether the given cache file exists and is fresh enough."""

        if not path.exists():
            return False
        file_age = datetime.now().timestamp() - path.stat().st_mtime
        return file_age < (max_age_minutes * 60)

    def read_json(self, path: Path) -> Any:
        """Read a JSON payload from disk, returning ``None`` on errors."""

        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            logger.warning("⚠️ Failed to read cache %s: %s", path, error)
            return None

    def write_json(self, path: Path, payload: Any) -> None:
        """Persist a JSON payload to disk, best-effort."""

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except (OSError, TypeError, ValueError) as error:
            logger.warning("⚠️ Failed to write cache %s: %s", path, error)

    def info(self, path: Path) -> dict[str, Any]:
        """Return metadata about a cache file for debugging purposes."""

        if not path.exists():
            return {
                "exists": False,
                "path": str(path),
                "age_minutes": None,
                "size_bytes": None,
            }

        stat = path.stat()
        age_seconds = datetime.now().timestamp() - stat.st_mtime
        return {
            "exists": True,
            "path": str(path),
            "age_minutes": age_seconds / 60,
            "size_bytes": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    def clean_old(self, directory: Path, *, max_age_days: int = 7) -> int:
        """Remove cache files older than ``max_age_days`` from the directory."""

        if not directory.exists():
            return 0

        cutoff = datetime.now() - timedelta(days=max_age_days)
        cutoff_ts = cutoff.timestamp()
        deleted = 0

        for file in directory.iterdir():
            try:
                if file.is_file() and file.stat().st_mtime < cutoff_ts:
                    file.unlink()
                    deleted += 1
            except (OSError, FileNotFoundError) as error:
                logger.debug("Cache cleanup skipped %s: %s", file, error)

        if deleted:
            logger.info("🧹 Cache cleanup removed %d files from %s", deleted, directory)
        return deleted


class JsonTimeSeriesStore:
    """Lightweight JSON time-series storage backed by ``FileCacheRepository``."""

    def __init__(self, repository: FileCacheRepository, cache_key: str) -> None:
        self._repository = repository
        self._path = repository.path(*cache_key.split("/"))

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> List[Dict[str, Any]]:
        payload = self._repository.read_json(self._path)
        if isinstance(payload, list):
            return payload
        if payload is not None:
            logger.debug("Unexpected payload while loading time series: %s", type(payload))
        return []

    def save(self, rows: Iterable[Dict[str, Any]]) -> None:
        serialised = list(rows)
        self._repository.write_json(self._path, serialised)


__all__ = [
    "CacheTTL",
    "FileCacheRepository",
    "JsonTimeSeriesStore",
]
