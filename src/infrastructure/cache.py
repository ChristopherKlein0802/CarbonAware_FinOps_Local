"""Filesystem-based cache utilities for the infrastructure layer."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheTTL:
    """Standard cache TTL values used across the application (minutes)."""

    CARBON_DATA: int = 60         # ElectricityMaps updates roughly every hour
    CARBON_24H: int = 120         # Historical data can be cached longer
    POWER_DATA: int = 10080       # Hardware specs rarely change
    PRICING_DATA: int = 10080     # AWS pricing is stable
    COST_DATA: int = 360          # Cost Explorer updates several times per day
    CPU_UTILIZATION: int = 180    # Performance metrics refresh every few hours
    CLOUDTRAIL_EVENTS: int = 1440 # CloudTrail events immutable


class FileCacheRepository:
    """Filesystem-backed cache repository with JSON convenience helpers."""

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


__all__ = ["FileCacheRepository", "CacheTTL"]
