"""Boavizta API client implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover
    from ...vendor import httpx_stub as httpx

from ...config import settings
from ...infrastructure.cache import FileCacheRepository, CacheTTL
from ...models.carbon import PowerConsumption

logger = logging.getLogger(__name__)


class BoaviztaClient:
    """Boavizta cloud instance power consumption client."""

    def __init__(
        self,
        *,
        repository: FileCacheRepository,
        base_url: str = str(settings.boavizta_base_url),
        timeout_seconds: float = settings.http_timeout_seconds,
    ) -> None:
        self._repository = repository
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def _async_post(self, payload: Dict[str, object]) -> Dict[str, object]:
        timeout = httpx.Timeout(self._timeout)
        async with httpx.AsyncClient(base_url=self._base_url, timeout=timeout) as client:
            response = await client.post("/cloud/instance", json=payload, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json()

    def _cache_path(self, instance_type: str):
        return self._repository.path("boavizta_power", instance_type)

    def get_power_consumption(self, instance_type: str) -> Optional[PowerConsumption]:
        if not instance_type:
            logger.error("❌ Invalid instance_type provided to Boavizta client")
            return None

        cache_path = self._cache_path(instance_type)
        if self._repository.is_valid(cache_path, CacheTTL.POWER_DATA):
            cached = self._repository.read_json(cache_path)
            if cached:
                try:
                    return PowerConsumption(
                        avg_power_watts=float(cached["avg_power_watts"]),
                        min_power_watts=float(cached["min_power_watts"]),
                        max_power_watts=float(cached["max_power_watts"]),
                        confidence_level=str(cached.get("confidence_level", "high")),
                        source=str(cached.get("source", "Boavizta_API")),
                    )
                except (KeyError, ValueError, TypeError) as error:
                    logger.debug("Boavizta cache invalid for %s: %s", instance_type, error)

        payload = {
            "provider": "aws",
            "instance_type": instance_type,
            "usage": {"hours_use_time": 1},
            "location": "EUC",
        }

        async def _fetch() -> Optional[PowerConsumption]:
            data = await self._async_post(payload)
            verbose = data.get("verbose", {})
            avg_power = verbose.get("avg_power", {}).get("value")
            if avg_power is None or avg_power <= 0:
                return None
            min_power = verbose.get("min_power", {}).get("value", avg_power * 0.8)
            max_power = verbose.get("max_power", {}).get("value", avg_power * 1.2)
            return PowerConsumption(
                avg_power_watts=float(avg_power),
                min_power_watts=float(min_power),
                max_power_watts=float(max_power),
                confidence_level="high",
                source="Boavizta_API",
            )

        try:
            result = asyncio.run(_fetch())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(_fetch())
        except httpx.TimeoutException as exc:
            logger.error("⏱️ Boavizta API timeout for %s: %s", instance_type, exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.error("❌ Boavizta HTTP error %s for %s", exc.response.status_code, instance_type)
            return None
        except httpx.RequestError as exc:
            logger.error("❌ Boavizta request failed for %s: %s", instance_type, exc)
            return None

        if result:
            payload = {
                "avg_power_watts": result.avg_power_watts,
                "min_power_watts": result.min_power_watts,
                "max_power_watts": result.max_power_watts,
                "confidence_level": result.confidence_level,
                "source": result.source,
            }
            self._repository.write_json(cache_path, payload)
        return result


__all__ = ["BoaviztaClient"]
