"""ElectricityMaps API client implementation."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - fallback stub
    from ...vendor import httpx_stub as httpx

from src.config import settings
from src.infrastructure.cache import FileCacheRepository, CacheTTL
from src.domain.models import CarbonIntensity

logger = logging.getLogger(__name__)


def _parse_iso(dt: str) -> datetime:
    normalised = dt.strip()
    if normalised.endswith("Z"):
        normalised = normalised[:-1] + "+00:00"
    value = datetime.fromisoformat(normalised)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


class ElectricityClient:
    """Typed client for ElectricityMaps, with filesystem caching."""

    def __init__(
        self,
        *,
        repository: FileCacheRepository,
        base_url: str = str(settings.electricitymaps_base_url),
        api_key: Optional[str] = settings.electricitymaps_api_key,
        timeout_seconds: float = settings.http_timeout_seconds,
    ) -> None:
        self._repository = repository
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._enable_hourly_collection = settings.enable_hourly_carbon_collection

    async def _async_get(self, endpoint: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        timeout = httpx.Timeout(self._timeout)
        headers = {"auth-token": self._api_key or ""}
        async with httpx.AsyncClient(base_url=self._base_url, headers=headers, timeout=timeout) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()

    def _cache_path(self, category: str, identifier: str) -> Path:
        return self._repository.path(category, identifier)

    def get_current_intensity(self, region: str, zone_mapping: Dict[str, str]) -> Optional[CarbonIntensity]:
        cache_path = self._cache_path("carbon_intensity", region)
        if self._repository.is_valid(cache_path, CacheTTL.CARBON_DATA):
            cached = self._repository.read_json(cache_path)
            if cached:
                try:
                    timestamp = _parse_iso(cached["timestamp_utc"])
                    fetched = _parse_iso(cached["fetched_at_utc"])
                    return CarbonIntensity(
                        value=float(cached["value"]),
                        timestamp=timestamp,
                        region=cached["region"],
                        source=cached.get("source", "electricitymap"),
                        fetched_at=fetched,
                    )
                except (KeyError, ValueError, TypeError) as error:
                    logger.debug("Invalid cached carbon intensity for %s: %s", region, error)

        if not self._api_key:
            logger.error("❌ ElectricityMaps API key not configured")
            return None

        zone = zone_mapping.get(region, region)

        async def _fetch() -> Optional[CarbonIntensity]:
            data = await self._async_get("/carbon-intensity/latest", params={"zone": zone})
            if "carbonIntensity" not in data or "datetime" not in data:
                return None
            timestamp = _parse_iso(data["datetime"])
            fetched_at = datetime.now(timezone.utc)
            return CarbonIntensity(
                value=float(data["carbonIntensity"]),
                timestamp=timestamp,
                region=region,
                source="electricitymap",
                fetched_at=fetched_at,
            )

        try:
            result = asyncio.run(_fetch())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(_fetch())
        except httpx.TimeoutException:
            logger.error("⏱️ ElectricityMaps API timeout")
            return self._fallback_from_cache(cache_path)
        except httpx.HTTPStatusError as exc:
            logger.error("❌ ElectricityMaps HTTP error: %s", exc.response.status_code)
            return self._fallback_from_cache(cache_path)
        except httpx.RequestError as exc:
            logger.error("❌ ElectricityMaps request failed: %s", exc)
            return self._fallback_from_cache(cache_path)

        if result:
            payload = {
                "value": result.value,
                "timestamp": result.timestamp.astimezone().isoformat(),
                "timestamp_utc": result.timestamp.astimezone(timezone.utc).isoformat(),
                "region": result.region,
                "source": result.source,
                "fetched_at": result.fetched_at.astimezone().isoformat() if result.fetched_at else None,
                "fetched_at_utc": result.fetched_at.astimezone(timezone.utc).isoformat() if result.fetched_at else None,
            }
            self._repository.write_json(cache_path, payload)
        return result

    def get_carbon_intensity_history(self, region: str, zone_mapping: Dict[str, str]) -> Optional[List[Dict[str, Any]]]:
        cache_key = f"{region}_{datetime.now(timezone.utc).date().isoformat()}"
        cache_path = self._cache_path("carbon_intensity_24h", cache_key)
        if self._repository.is_valid(cache_path, CacheTTL.CARBON_24H):
            cached = self._repository.read_json(cache_path)
            if isinstance(cached, dict):
                return cached.get("history")

        if not self._api_key:
            logger.error("❌ ElectricityMaps API key not configured for history")
            return None

        zone = zone_mapping.get(region, region)

        async def _fetch() -> Optional[List[Dict[str, Any]]]:
            data = await self._async_get("/carbon-intensity/history", params={"zone": zone})
            history = data.get("history")
            return history

        try:
            history = asyncio.run(_fetch())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            history = loop.run_until_complete(_fetch())
        except httpx.TimeoutException:
            logger.error("⏱️ ElectricityMaps history timeout")
            return None
        except httpx.HTTPStatusError as exc:
            logger.error("❌ ElectricityMaps history error: %s", exc.response.status_code)
            return None
        except httpx.RequestError as exc:
            logger.error("❌ ElectricityMaps history request failed: %s", exc)
            return None

        if history:
            self._repository.write_json(cache_path, {"history": history, "fetched_at": datetime.now().isoformat()})
        return history

    def get_self_collected_history(self, region: str) -> Optional[List[Dict[str, Any]]]:
        if not self._enable_hourly_collection:
            return None
        collection_path = self._cache_path("carbon_collection", f"{region}_hourly.json")
        data = self._repository.read_json(collection_path)
        if not isinstance(data, list):
            return None
        cutoff = datetime.now(timezone.utc).astimezone() - timedelta(hours=24)
        filtered = [
            entry for entry in data if entry.get("hour_key") and _parse_iso(entry["hour_key"]).astimezone() > cutoff
        ]
        return filtered or None

    def store_hourly_snapshot(self, region: str, zone_mapping: Dict[str, str]) -> None:
        if not self._enable_hourly_collection:
            return
        current = self.get_current_intensity(region, zone_mapping)
        if current is None:
            return
        collection_path = self._cache_path("carbon_collection", f"{region}_hourly.json")
        now_local = datetime.now(timezone.utc).astimezone()
        hour_key = now_local.replace(minute=0, second=0, microsecond=0).isoformat()
        existing = self._repository.read_json(collection_path)
        rows: List[Dict[str, Any]] = []
        if isinstance(existing, list):
            rows = [entry for entry in existing if entry.get("hour_key") != hour_key]
        rows.append(
            {
                "hour_key": hour_key,
                "carbonIntensity": current.value,
                "datetime": now_local.isoformat(),
                "datetime_utc": now_local.astimezone(timezone.utc).isoformat(),
                "hour": now_local.hour,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "source": "electricitymap_hourly_collection",
            }
        )
        rows = [entry for entry in rows if _parse_iso(entry["hour_key"]).astimezone() > now_local - timedelta(hours=24)]
        rows.sort(key=lambda row: row["hour_key"])
        self._repository.write_json(collection_path, rows[-24:])

    def _fallback_from_cache(self, cache_path: Path) -> Optional[CarbonIntensity]:
        cached = self._repository.read_json(cache_path)
        if not cached:
            return None
        try:
            timestamp = _parse_iso(cached["timestamp_utc"])
            return CarbonIntensity(
                value=float(cached["value"]),
                timestamp=timestamp,
                region=cached["region"],
                source=f"expired_cache_{cached.get('source', 'electricitymap')}",
            )
        except (KeyError, ValueError, TypeError) as error:
            logger.debug("Expired cache unusable: %s", error)
            return None


__all__ = ["ElectricityClient"]
