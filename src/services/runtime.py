"""Runtime-focused domain services."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..config import settings
from ..constants import AcademicConstants
from ..infrastructure.cache import CacheTTL, FileCacheRepository
from ..infrastructure.clients import InfrastructureGateway
from ..infrastructure.clients.aws_runtime import AWSRuntimeGateway
from ..models.aws import EC2Instance
from ..utils.errors import AWSAuthenticationError, ErrorMessages

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeServiceConfig:
    region: str = settings.aws_region
    aws_profile: str = settings.aws_profile
    lookback_days: int = 30


class RuntimeService:
    """Service encapsulating runtime collection and enrichment logic."""

    def __init__(
        self,
        config: RuntimeServiceConfig | None = None,
        *,
        repository: FileCacheRepository,
        infrastructure_gateway: InfrastructureGateway,
        runtime_gateway: AWSRuntimeGateway,
    ) -> None:
        self.config = config or RuntimeServiceConfig()
        self._repository = repository
        self._gateway = infrastructure_gateway
        self._runtime_gateway = runtime_gateway
        logger.info("✅ RuntimeService initialised for region %s", self.config.region)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def list_instances(self) -> List[Dict]:
        """Return metadata for running/stopped EC2 instances in the configured region."""
        try:
            instances = self._runtime_gateway.list_instances(self.config.region)
        except AWSAuthenticationError:
            raise
        except Exception as error:  # pragma: no cover - defensive safeguard
            logger.error("❌ Unexpected EC2 discovery error: %s", error)
            return []

        logger.info("✅ RuntimeService discovered %d instances", len(instances))
        return instances

    def enrich_instance(
        self,
        instance: Dict,
        *,
        carbon_intensity: float,
        force_refresh: bool = False,
    ) -> Optional[EC2Instance]:
        """Return an enriched `EC2Instance` with runtime, power, cost, and confidence metadata."""
        runtime_hours = self._get_precise_runtime_hours(instance, force_refresh=force_refresh)
        power_data = self._gateway.get_power_consumption(instance["instance_type"])
        hourly_price = self._gateway.get_instance_pricing(instance["instance_type"], instance["region"])
        cpu_utilisation = self._get_cpu_utilisation(instance["instance_id"], force_refresh=force_refresh)

        if power_data is None and runtime_hours is None and hourly_price is None:
            logger.warning("Insufficient data to enrich instance %s", instance["instance_id"])

        effective_power_watts = None
        hourly_co2_g = None
        monthly_co2_kg = None
        monthly_cost_usd = None
        monthly_cost_eur = None

        if power_data and cpu_utilisation is not None:
            effective_power_watts = self._calculate_effective_power(power_data.avg_power_watts, cpu_utilisation)

        if effective_power_watts is not None and runtime_hours is not None:
            monthly_co2_kg = self._calculate_monthly_co2(effective_power_watts, carbon_intensity, runtime_hours)
            hourly_co2_g = (effective_power_watts / 1000.0) * carbon_intensity

        if hourly_price is not None and runtime_hours is not None:
            monthly_cost_usd = hourly_price * runtime_hours
            monthly_cost_eur = monthly_cost_usd * AcademicConstants.EUR_USD_RATE

        confidence_level, data_sources = self._determine_confidence_metadata(
            has_power=power_data is not None,
            has_pricing=hourly_price is not None,
            has_cpu=cpu_utilisation is not None,
            has_runtime=runtime_hours is not None,
        )

        data_quality = self._resolve_data_quality(runtime_hours, cpu_utilisation, effective_power_watts, monthly_cost_eur)

        return EC2Instance(
            instance_id=instance["instance_id"],
            instance_type=instance["instance_type"],
            state=instance.get("state", "unknown"),
            region=instance.get("region", self.config.region),
            instance_name=instance.get("instance_name", "Unnamed"),
            power_watts=self._safe_round(effective_power_watts, 1),
            hourly_co2_g=self._safe_round(hourly_co2_g, 2),
            monthly_co2_kg=self._safe_round(monthly_co2_kg, 3),
            monthly_cost_usd=self._safe_round(monthly_cost_usd, 2),
            monthly_cost_eur=self._safe_round(monthly_cost_eur, 2),
            runtime_hours=self._safe_round(runtime_hours, 1),
            hourly_price_usd=self._safe_round(hourly_price, 4),
            cpu_utilization=self._safe_round(cpu_utilisation, 1),
            data_quality=data_quality,
            confidence_level=confidence_level,
            data_sources=data_sources,
            last_updated=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_precise_runtime_hours(self, instance: Dict, *, force_refresh: bool = False) -> Optional[float]:
        instance_id = instance["instance_id"]
        region = instance.get("region", self.config.region)
        cache_identifier = f"{instance_id}_{region}"
        cache_path = self._repository.path("cloudtrail_runtime", cache_identifier)

        if not force_refresh and self._repository.is_valid(cache_path, CacheTTL.CLOUDTRAIL_EVENTS):
            cached_payload = self._repository.read_json(cache_path)
            if isinstance(cached_payload, dict):
                runtime_hours = cached_payload.get("runtime_hours")
                if runtime_hours is not None:
                    logger.debug("Using cached CloudTrail runtime for %s (%.2f h)", instance_id, runtime_hours)
                    return runtime_hours

        try:
            end_time = datetime.now(timezone.utc)
            launch_time = instance.get("launch_time")
            if isinstance(launch_time, datetime) and launch_time.tzinfo is None:
                launch_time = launch_time.replace(tzinfo=timezone.utc)

            lookback_start = end_time - timedelta(days=self.config.lookback_days)
            if launch_time:
                lookback_start = min(lookback_start, launch_time - timedelta(hours=1))

            events = self._runtime_gateway.lookup_instance_events(
                instance_id=instance_id,
                region=region,
                lookup_start=lookback_start,
                lookup_end=end_time,
            )

            relevant_events = self._extract_relevant_events(events, instance_id)

            if not relevant_events:
                state = (instance.get("state") or "").lower()
                if launch_time and state == "running":
                    runtime_hours = (end_time - launch_time).total_seconds() / 3600.0
                    logger.warning(
                        "Fallback runtime estimation for %s using launch time (no CloudTrail events)",
                        instance_id,
                    )
                else:
                    logger.warning("No CloudTrail state change events for %s within lookback window", instance_id)
                    return None
            else:
                runtime_hours = self._calculate_runtime_from_events(
                    relevant_events,
                    end_time,
                    lookback_start,
                    launch_time,
                    instance.get("state"),
                )

            payload = {
                "runtime_hours": runtime_hours,
                "event_count": len(relevant_events),
                "lookback_start": lookback_start.isoformat() if lookback_start else None,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }
            self._repository.write_json(cache_path, payload)

            logger.info(
                "CloudTrail runtime for %s: %.2f h from %d events (start/stop only, not continuous runtime)",
                instance_id, runtime_hours, len(relevant_events)
            )
            return runtime_hours
        except Exception as error:  # pragma: no cover
            logger.error("Runtime calculation error for %s: %s", instance_id, error)
            return None

    def _extract_relevant_events(self, events: List[Dict], instance_id: str) -> List[Dict]:
        start_events = {"RunInstances", "StartInstances"}
        stop_events = {"StopInstances", "TerminateInstances"}
        relevant: List[Dict] = []

        for event in events:
            event_name = event.get("EventName")
            event_time = event.get("EventTime")
            if event_name not in start_events | stop_events or event_time is None:
                continue

            resources = event.get("Resources", []) or []
            if not any(r.get("ResourceName") == instance_id for r in resources):
                continue

            relevant.append({"name": event_name, "time": event_time})

        relevant.sort(key=lambda entry: entry["time"])
        return relevant

    def _calculate_runtime_from_events(
        self,
        events: List[Dict],
        end_time: datetime,
        lookback_start: Optional[datetime],
        launch_time: Optional[datetime] = None,
        instance_state: Optional[str] = None,
    ) -> float:
        session_start: Optional[datetime] = None
        runtime_hours = 0.0
        start_events = {"RunInstances", "StartInstances"}
        stop_events = {"StopInstances", "TerminateInstances"}

        fallback_start: Optional[datetime] = launch_time or lookback_start

        if events:
            first_event_name = events[0].get("name")
            if first_event_name in stop_events and fallback_start is not None:
                session_start = fallback_start

        instance_state_lower = (instance_state or "").lower()

        for event in events:
            event_time = event["time"]
            event_name = event["name"]

            if event_name in start_events:
                session_start = event_time
            elif event_name in stop_events and session_start is not None:
                runtime_hours += (event_time - session_start).total_seconds() / 3600.0
                session_start = None
            elif event_name in stop_events and session_start is None and fallback_start is not None:
                runtime_hours += (event_time - fallback_start).total_seconds() / 3600.0
                fallback_start = None

        if session_start is not None:
            runtime_hours += (end_time - session_start).total_seconds() / 3600.0
        elif instance_state_lower == "running" and fallback_start is not None:
            runtime_hours += max((end_time - fallback_start).total_seconds() / 3600.0, 0.0)

        return round(runtime_hours, 2)

    # ------------------------------------------------------------------
    # Auxiliary helpers for enrichment
    # ------------------------------------------------------------------

    def _get_cpu_utilisation(self, instance_id: str, force_refresh: bool = False) -> Optional[float]:
        cache_path = self._repository.path("cpu_utilization", instance_id)

        if not force_refresh and self._repository.is_valid(cache_path, CacheTTL.CPU_UTILIZATION):
            cached = self._repository.read_json(cache_path)
            if isinstance(cached, dict) and "cpu_utilization" in cached:
                return cached["cpu_utilization"]

        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            results = self._runtime_gateway.fetch_cpu_metrics(
                instance_id=instance_id,
                region=self.config.region,
                start_time=start_time,
                end_time=end_time,
            )

            if not results:
                logger.error("❌ No CPU data available for %s - NO-FALLBACK policy enforced", instance_id)
                return None

            values = results[0].get('Values', [])
            if values:
                avg_cpu = sum(values) / len(values)
                payload = {
                    "cpu_utilization": avg_cpu,
                    "instance_id": instance_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "CloudWatch_get_metric_data"
                }
                self._repository.write_json(cache_path, payload)

                logger.info("✅ CPU Utilization %s: %.1f%% (cached)", instance_id, avg_cpu)
                return avg_cpu

            logger.error("❌ No CPU data available for %s - NO-FALLBACK policy enforced", instance_id)
            return None
        except Exception as error:  # pragma: no cover
            logger.warning("⚠️ CloudWatch CPU query error for %s: %s", instance_id, error)
            return None

    @staticmethod
    def _calculate_effective_power(avg_power_watts: float, cpu_utilisation: float) -> float:
        utilisation_factor = 0.3 + 0.7 * (cpu_utilisation / 100.0)
        return avg_power_watts * utilisation_factor

    @staticmethod
    def _calculate_monthly_co2(power_watts: float, carbon_intensity: float, runtime_hours: float) -> float:
        power_kw = power_watts / 1000.0
        co2_g = power_kw * carbon_intensity * runtime_hours
        return round(co2_g / 1000.0, 3)

    @staticmethod
    def _safe_round(value: Optional[float], decimals: int) -> Optional[float]:
        if value is None:
            return None
        return round(float(value), decimals)

    @staticmethod
    def _determine_confidence_metadata(
        *,
        has_power: bool,
        has_pricing: bool,
        has_cpu: bool,
        has_runtime: bool,
    ) -> tuple[str, List[str]]:
        data_sources: List[str] = ["aws_api"]
        if has_power:
            data_sources.append("boavizta")
        if has_pricing:
            data_sources.append("aws_pricing")
        if has_cpu:
            data_sources.append("cloudwatch")
        if has_runtime:
            data_sources.append("cloudtrail_audit")

        if len(data_sources) >= 4:
            confidence_level = "high"
        elif len(data_sources) >= 3:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return confidence_level, data_sources

    @staticmethod
    def _resolve_data_quality(
        runtime_hours: Optional[float],
        cpu_utilisation: Optional[float],
        effective_power_watts: Optional[float],
        monthly_cost_eur: Optional[float],
    ) -> str:
        if all(value is not None for value in (runtime_hours, cpu_utilisation, effective_power_watts, monthly_cost_eur)):
            return "measured"
        if any(value is not None for value in (runtime_hours, cpu_utilisation, effective_power_watts, monthly_cost_eur)):
            return "partial"
        return "limited"
