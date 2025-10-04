"""Time-series persistence helpers used by domain services."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, List, Dict, Any

from .cache import FileCacheRepository

logger = logging.getLogger(__name__)


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


__all__ = ["JsonTimeSeriesStore"]
