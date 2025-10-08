"""
Carbon data aggregation and time-series services.

Following Clean Architecture, this service depends only on domain protocols,
not concrete infrastructure implementations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.domain.models import TimeSeriesPoint
from src.domain.constants import AcademicConstants
from src.domain.protocols import CacheRepository, InfrastructureGateway
from src.infrastructure.cache import JsonTimeSeriesStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CarbonServiceConfig:
    """Configuration for carbon data service operations."""

    region: str = "eu-central-1"
    timeseries_cache_key: str = "timeseries/cost_carbon"
    lookback_hours: int = 24  # Changed from 48h to match hourly costs window


class CarbonDataService:
    """
    Provide access to carbon data and derived time series.

    This service depends only on protocols (CacheRepository, InfrastructureGateway),
    following the Dependency Inversion Principle of Clean Architecture.
    """

    def __init__(
        self,
        config: CarbonServiceConfig | None = None,
        *,
        repository: CacheRepository,
        gateway: InfrastructureGateway,
        time_series_store: JsonTimeSeriesStore | None = None,
    ) -> None:
        self.config = config or CarbonServiceConfig()
        self._repository = repository
        self._gateway = gateway
        self._time_series_store = time_series_store or JsonTimeSeriesStore(repository, self.config.timeseries_cache_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_intensity(self, *, region: Optional[str] = None):
        region_code = region or self.config.region
        return self._gateway.get_current_carbon_intensity(region_code)

    def get_recent_history(self, *, region: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        region_code = region or self.config.region
        history = self._gateway.get_carbon_intensity_24h(region_code)
        if not history:
            history = self._gateway.get_self_collected_24h_data(region_code)
        return history

    def get_self_collected_history(self, *, region: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        region_code = region or self.config.region
        return self._gateway.get_self_collected_24h_data(region_code)

    def get_cached_time_series(self) -> List[TimeSeriesPoint]:
        raw_rows = self._time_series_store.load()
        points: List[TimeSeriesPoint] = []
        for entry in raw_rows:
            try:
                raw_timestamp = entry.get("timestamp")
                if not raw_timestamp:
                    continue
                timestamp = datetime.fromisoformat(str(raw_timestamp))
                points.append(
                    TimeSeriesPoint(
                        timestamp=timestamp,
                        cost_eur_per_hour=float(entry.get("cost_eur_per_hour", 0.0)),
                        co2_kg_per_hour=float(entry.get("co2_kg_per_hour", 0.0)),
                        carbon_intensity=entry.get("carbon_intensity"),
                    )
                )
            except (ValueError, TypeError) as error:
                logger.debug("⚠️ Skipping corrupt time series entry: %s", error)
        return sorted(points, key=lambda point: point.timestamp)

    def build_time_series(
        self,
        hourly_costs: List[Dict[str, Any]],
        carbon_history: Optional[List[Dict[str, Any]]],
        total_co2_kg: float,
    ) -> List[TimeSeriesPoint]:
        """
        Build time series points from hourly costs and carbon history.

        Note: TAC (Time Alignment Coverage) calculation was removed as it only
        measured ElectricityMaps API uptime, not synchronization quality.
        See docs/methodology/METRICS_REVISION.md for details.
        """
        if not hourly_costs:
            logger.debug("⚠️ No hourly costs provided, using cached time series")
            return self.get_cached_time_series()

        cost_map: Dict[datetime, float] = {}
        for entry in hourly_costs:
            timestamp_raw = entry.get("timestamp")
            cost_value = entry.get("cost_eur")
            if timestamp_raw is None or cost_value is None:
                continue
            try:
                ts = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            normalised = self._normalise_hour(ts)
            if normalised is None:
                continue
            cost_map[normalised] = float(cost_value)

        if not cost_map:
            logger.warning("⚠️ Cost map empty after processing, using cached time series")
            return self.get_cached_time_series()

        non_zero_costs = sum(1 for v in cost_map.values() if v > 0)
        logger.info(f"📊 Built cost map: {len(cost_map)} hours, {non_zero_costs} with non-zero costs")

        carbon_map: Dict[datetime, float] = {}
        for entry in carbon_history or []:
            ts_raw = entry.get("datetime") or entry.get("hour_key")
            value = entry.get("carbonIntensity") or entry.get("value")
            if ts_raw is None or value is None:
                continue
            try:
                ts_obj = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            normalised = self._normalise_hour(ts_obj)
            if normalised is None:
                continue
            try:
                carbon_map[normalised] = float(value)
            except (TypeError, ValueError):
                continue

        window_start = self._normalise_hour(datetime.now(timezone.utc) - timedelta(hours=self.config.lookback_hours))
        if window_start is None:
            window_start = datetime.now().replace(minute=0, second=0, microsecond=0)

        points: List[TimeSeriesPoint] = []
        sorted_hours = sorted(hour for hour in cost_map.keys() if hour >= window_start)
        if not sorted_hours:
            sorted_hours = sorted(cost_map.keys())

        base_hourly_co2 = None
        if total_co2_kg and len(sorted_hours) > 0:
            try:
                base_hourly_co2 = float(total_co2_kg) / AcademicConstants.HOURS_PER_MONTH
            except (TypeError, ValueError):
                base_hourly_co2 = None

        aligned_carbon_values = [carbon_map[hour] for hour in sorted_hours if hour in carbon_map]
        avg_carbon_intensity = (
            sum(aligned_carbon_values) / len(aligned_carbon_values) if aligned_carbon_values else None
        )

        for hour in sorted_hours:
            cost_value = cost_map.get(hour, 0.0)
            carbon_value = carbon_map.get(hour)
            if base_hourly_co2 is None:
                co2_value = 0.0
            elif carbon_value is not None and avg_carbon_intensity not in (None, 0.0):
                adjustment_factor = carbon_value / avg_carbon_intensity
                co2_value = round(base_hourly_co2 * adjustment_factor, 6)
            else:
                co2_value = round(base_hourly_co2, 6)

            points.append(
                TimeSeriesPoint(
                    timestamp=hour,
                    cost_eur_per_hour=round(float(cost_value), 6),
                    co2_kg_per_hour=co2_value,
                    carbon_intensity=carbon_value,
                )
            )

        serialised = [
            {
                "timestamp": point.timestamp.isoformat(),
                "cost_eur_per_hour": point.cost_eur_per_hour,
                "co2_kg_per_hour": point.co2_kg_per_hour,
                "carbon_intensity": point.carbon_intensity,
            }
            for point in points
        ]
        self._time_series_store.save(serialised)

        return points

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_hour(timestamp: datetime) -> Optional[datetime]:
        if timestamp is None:
            return None
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        localised = timestamp.astimezone().replace(minute=0, second=0, microsecond=0)
        return localised.replace(tzinfo=None)


__all__ = ["CarbonDataService", "CarbonServiceConfig"]
