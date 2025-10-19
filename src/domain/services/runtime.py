"""
Runtime-focused domain services.

Following Clean Architecture, this service depends only on domain protocols,
not concrete infrastructure implementations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from src.config import settings
from src.domain.constants import AcademicConstants
from src.domain.protocols import CacheRepository, InfrastructureGateway
from src.infrastructure.cache import CacheTTL
from src.domain.models import EC2Instance
from src.domain.errors import AWSAuthenticationError, ErrorMessages
from src.domain.calculations import (
    calculate_co2_emissions,
    calculate_co2_hourly_precise,
    calculate_simple_power_consumption,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeServiceConfig:
    """Configuration for runtime service operations."""

    region: str = settings.aws_region
    aws_profile: str = settings.aws_profile
    lookback_days: int = 30


class RuntimeService:
    """
    Service encapsulating runtime collection and enrichment logic.

    This service depends only on protocols (CacheRepository, InfrastructureGateway),
    following the Dependency Inversion Principle of Clean Architecture.
    """

    def __init__(
        self,
        config: RuntimeServiceConfig | None = None,
        *,
        repository: CacheRepository,
        gateway: InfrastructureGateway,
    ) -> None:
        self.config = config or RuntimeServiceConfig()
        self._repository = repository
        self._gateway = gateway
        logger.info("✅ RuntimeService initialised for region %s", self.config.region)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    @staticmethod
    def _align_carbon_history_to_hours(carbon_history: Optional[List[Dict]], num_hours: int = 24) -> List[float]:
        """
        Align ElectricityMaps history data to hourly slots.

        Extracts carbon intensity values from ElectricityMaps history and aligns
        them to the last N hours. Handles missing data with interpolation or average.

        Args:
            carbon_history: List from ElectricityMaps API with format:
                [{'datetime': '...', 'carbonIntensity': 280}, ...]
            num_hours: Number of hours to extract (default 24)

        Returns:
            List of carbon intensity values (g/kWh), one per hour.
            If data is missing, returns list filled with average or zeros.

        Example:
            Input: [{'datetime': '2025-10-18T10:00:00Z', 'carbonIntensity': 280}, ...]
            Output: [280.0, 290.0, 310.0, ...] (24 values)
        """
        if not carbon_history:
            logger.warning("No carbon history provided, returning zeros")
            return [0.0] * num_hours

        # Extract values and timestamps
        carbon_data = []
        for entry in carbon_history:
            try:
                dt_str = entry.get("datetime") or entry.get("hour_key")
                value = entry.get("carbonIntensity") or entry.get("value")

                if dt_str and value is not None:
                    # Parse datetime
                    if isinstance(dt_str, str):
                        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    else:
                        dt = dt_str

                    # Ensure timezone-aware
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)

                    carbon_data.append((dt, float(value)))
            except (ValueError, TypeError, KeyError) as e:
                logger.debug(f"Skipping invalid carbon entry: {entry}, error: {e}")
                continue

        if not carbon_data:
            logger.warning("No valid carbon data found, returning zeros")
            return [0.0] * num_hours

        # Sort by timestamp
        carbon_data.sort(key=lambda x: x[0])

        # Build hourly array for last N hours
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=num_hours)

        result = []
        for hour_offset in range(num_hours):
            hour_start = window_start + timedelta(hours=hour_offset)
            hour_end = hour_start + timedelta(hours=1)

            # Find value for this hour
            matching_value = None
            for dt, value in carbon_data:
                if hour_start <= dt < hour_end:
                    matching_value = value
                    break

            if matching_value is not None:
                result.append(matching_value)
            else:
                # No data for this hour - use average as fallback
                avg_value = sum(v for _, v in carbon_data) / len(carbon_data)
                result.append(avg_value)
                logger.debug(f"Missing carbon data for hour {hour_offset}, using average {avg_value:.1f}")

        logger.info(f"Aligned {len(result)} hours of carbon intensity data (avg: {sum(result)/len(result):.1f} g/kWh)")
        return result

    def list_instances(self) -> List[Dict]:
        """Return metadata for running/stopped EC2 instances in the configured region."""
        try:
            instances = self._gateway.list_instances(self.config.region)
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
        carbon_history: Optional[List[Dict]] = None,
        force_refresh: bool = False,
    ) -> Optional[EC2Instance]:
        """
        Return an enriched `EC2Instance` with runtime, power, cost, and CO2 metadata.

        Args:
            instance: Raw instance dict from AWS API
            carbon_intensity: Current carbon intensity (fallback value)
            carbon_history: Optional 24h carbon history for hourly calculation
            force_refresh: Force refresh all cached data

        Returns:
            Enriched EC2Instance with hourly-precise CO2 calculation if data available,
            otherwise falls back to monthly average calculation.
        """
        # Fetch basic data (unchanged)
        runtime_hours = self._get_precise_runtime_hours(instance, force_refresh=force_refresh)
        power_data = self._gateway.get_power_consumption(instance["instance_type"])
        hourly_price = self._gateway.get_instance_pricing(instance["instance_type"], instance["region"])

        # NEW: Try to get hourly CPU data (falls back to average if needed)
        cpu_hourly_data = self._get_cpu_utilisation_hourly(instance["instance_id"], force_refresh=force_refresh)

        # Fallback to old single-value CPU if hourly not available
        if cpu_hourly_data is None:
            cpu_utilisation = self._get_cpu_utilisation(instance["instance_id"], force_refresh=force_refresh)
        else:
            cpu_utilisation = cpu_hourly_data.get("average")

        if power_data is None and runtime_hours is None and hourly_price is None:
            logger.warning("Insufficient data to enrich instance %s", instance["instance_id"])

        # Initialize variables
        effective_power_watts = None
        hourly_co2_g = None
        monthly_co2_kg = None
        daily_co2_kg = None
        monthly_cost_usd = None
        monthly_cost_eur = None
        co2_method = "none"
        hourly_breakdown = None
        # NEW: Dual comparison variables
        monthly_co2_kg_projected = None
        monthly_co2_kg_30d = None
        monthly_cost_projected_eur = None
        daily_runtime_hours = None
        data_completeness_24h = None
        instance_age_days = None

        # NEW: Try hourly-precise CO2 calculation
        if power_data and cpu_hourly_data and carbon_history:
            try:
                logger.info(
                    f"Attempting hourly CO2 calculation for {instance['instance_id']} "
                    f"(CPU hours: {len(cpu_hourly_data['hourly_values'])}, "
                    f"Carbon history: {len(carbon_history)} entries)"
                )

                # Get CloudTrail events for runtime calculation
                end_time = datetime.now(timezone.utc)
                lookback_start = end_time - timedelta(days=self.config.lookback_days)
                events = self._gateway.lookup_instance_events(
                    instance_id=instance["instance_id"],
                    region=instance.get("region", self.config.region),
                    lookup_start=lookback_start,
                    lookup_end=end_time,
                )
                relevant_events = self._extract_relevant_events(events, instance["instance_id"])

                # Calculate runtime per hour for last 24h
                runtime_per_hour, hour_timestamps = self._calculate_runtime_per_hour_24h(
                    instance=instance, events=relevant_events, end_time=end_time
                )

                # Align carbon history to hourly slots
                carbon_hourly = self._align_carbon_history_to_hours(carbon_history, 24)

                # Perform hourly-precise calculation
                co2_result = calculate_co2_hourly_precise(
                    base_power_watts=power_data.avg_power_watts,
                    cpu_values_hourly=cpu_hourly_data["hourly_values"],
                    carbon_intensity_hourly=carbon_hourly,
                    runtime_hours_per_slot=runtime_per_hour,
                    timestamps=hour_timestamps,
                )

                daily_co2_kg = co2_result["total_co2_kg"]
                monthly_co2_kg_projected = daily_co2_kg * 30  # NEW: 24h projected
                monthly_co2_kg = monthly_co2_kg_projected  # Keep existing field for backward compatibility
                co2_method = "hourly_24h_precise"
                hourly_breakdown = co2_result["hourly_emissions"]
                data_completeness_24h = co2_result["coverage_hours"]

                # Calculate 24h runtime sum for projection
                daily_runtime_hours = sum(runtime_per_hour)

                # Calculate average power from hourly data
                power_values = [e["power_watts"] for e in hourly_breakdown if e.get("power_watts")]
                if power_values:
                    effective_power_watts = sum(power_values) / len(power_values)

                # Calculate hourly CO2 rate (for backward compatibility)
                if effective_power_watts:
                    hourly_co2_g = (effective_power_watts / 1000.0) * carbon_intensity

                logger.info(
                    f"✅ Hourly CO2 calculation successful: {daily_co2_kg:.6f} kg/day, "
                    f"{co2_result['coverage_hours']}/24 hours, quality={co2_result['data_quality']}"
                )

            except Exception as e:
                logger.warning(f"⚠️ Hourly CO2 calculation failed for {instance['instance_id']}: {e}", exc_info=True)
                # Fall through to legacy calculation

        # Calculate 30d actual CO2 (always, for comparison)
        monthly_co2_kg_30d = None
        if power_data and cpu_utilisation is not None and runtime_hours is not None:
            power_30d = calculate_simple_power_consumption(power_data.avg_power_watts, cpu_utilisation)
            if power_30d is not None:
                monthly_co2_kg_30d = calculate_co2_emissions(power_30d, carbon_intensity, runtime_hours)

        # FALLBACK: Use 30d actual if hourly-precise failed or data missing
        if monthly_co2_kg is None and monthly_co2_kg_30d is not None:
            monthly_co2_kg = monthly_co2_kg_30d
            monthly_co2_kg_projected = monthly_co2_kg_30d  # No projection, use actual
            if power_data and cpu_utilisation is not None:
                effective_power_watts = calculate_simple_power_consumption(power_data.avg_power_watts, cpu_utilisation)
                hourly_co2_g = (effective_power_watts / 1000.0) * carbon_intensity
            co2_method = "monthly_average"
            logger.info(
                f"Using legacy average CO2 calculation for {instance['instance_id']}: "
                f"{monthly_co2_kg:.3f} kg/month"
            )

        # Cost calculations
        monthly_cost_projected_eur = None
        if hourly_price is not None and runtime_hours is not None:
            # 30d actual cost (unchanged)
            monthly_cost_usd = hourly_price * runtime_hours
            monthly_cost_eur = monthly_cost_usd * AcademicConstants.get_eur_usd_rate()

            # NEW: 24h projected cost
            if daily_runtime_hours is not None:
                monthly_cost_projected_usd = hourly_price * (daily_runtime_hours * 30)
                monthly_cost_projected_eur = monthly_cost_projected_usd * AcademicConstants.get_eur_usd_rate()

        # Calculate instance age for validation
        instance_age_days = None
        launch_time = instance.get("launch_time")
        if launch_time:
            try:
                if isinstance(launch_time, str):
                    launch_dt = datetime.fromisoformat(launch_time.replace("Z", "+00:00"))
                else:
                    launch_dt = launch_time
                instance_age_days = (datetime.now(timezone.utc) - launch_dt).days
            except Exception as e:
                logger.debug(f"Could not calculate instance age: {e}")

        confidence_level, data_sources = self._determine_confidence_metadata(
            has_power=power_data is not None,
            has_pricing=hourly_price is not None,
            has_cpu=cpu_utilisation is not None,
            has_runtime=runtime_hours is not None,
        )

        data_quality = self._resolve_data_quality(
            runtime_hours, cpu_utilisation, effective_power_watts, monthly_cost_eur
        )

        return EC2Instance(
            instance_id=instance["instance_id"],
            instance_type=instance["instance_type"],
            state=instance.get("state", "unknown"),
            region=instance.get("region", self.config.region),
            instance_name=instance.get("instance_name", "Unnamed"),
            power_watts=self._safe_round(effective_power_watts, 1),
            hourly_co2_g=self._safe_round(hourly_co2_g, 2),
            monthly_co2_kg=self._safe_round(monthly_co2_kg, 3),
            daily_co2_kg=self._safe_round(daily_co2_kg, 6),
            co2_calculation_method=co2_method,
            hourly_co2_breakdown=hourly_breakdown,
            monthly_cost_usd=self._safe_round(monthly_cost_usd, 2),
            monthly_cost_eur=self._safe_round(monthly_cost_eur, 2),
            runtime_hours=self._safe_round(runtime_hours, 1),
            hourly_price_usd=self._safe_round(hourly_price, 4),
            cpu_utilization=self._safe_round(cpu_utilisation, 1),
            data_quality=data_quality,
            confidence_level=confidence_level,
            data_sources=data_sources,
            last_updated=datetime.now(timezone.utc),
            # NEW: Dual comparison fields
            daily_runtime_hours=self._safe_round(daily_runtime_hours, 2),
            monthly_co2_kg_projected=self._safe_round(monthly_co2_kg_projected, 3),
            monthly_co2_kg_30d=self._safe_round(monthly_co2_kg_30d, 3),
            monthly_cost_projected_eur=self._safe_round(monthly_cost_projected_eur, 2),
            instance_age_days=instance_age_days,
            data_completeness_24h=data_completeness_24h,
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

            # Try to get launch time from cache if not available from instance dict
            if not launch_time:
                launch_time = self._gateway.get_cached_launch_time(instance_id, region)
                if launch_time and launch_time.tzinfo is None:
                    launch_time = launch_time.replace(tzinfo=timezone.utc)
                if launch_time:
                    logger.debug(f"✅ Using cached launch time for {instance_id}: {launch_time}")

            lookback_start = end_time - timedelta(days=self.config.lookback_days)
            if launch_time:
                lookback_start = min(lookback_start, launch_time - timedelta(hours=1))

            events = self._gateway.lookup_instance_events(
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
                instance_id,
                runtime_hours,
                len(relevant_events),
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

    def _calculate_runtime_per_hour_24h(
        self, instance: Dict, events: List[Dict], end_time: datetime
    ) -> tuple[List[float], List[datetime]]:
        """
        Calculate runtime fraction (0.0-1.0) for each of the last 24 hours.

        This function builds running intervals from CloudTrail Start/Stop events
        and calculates what fraction of each hour the instance was running.

        Args:
            instance: Instance dict with state and launch_time
            events: Sorted CloudTrail events (already filtered, from _extract_relevant_events)
            end_time: Current time (usually datetime.now(UTC))

        Returns:
            Tuple of:
            - List of 24 floats (runtime fractions, 0.0-1.0)
            - List of 24 datetime objects (hour start times)

        Example:
            Instance started at 10:15, stopped at 12:45
            Hour 10:00-11:00 → 0.75 (ran 45 minutes)
            Hour 11:00-12:00 → 1.0  (ran full hour)
            Hour 12:00-13:00 → 0.75 (ran 45 minutes)
            Hour 13:00-14:00 → 0.0  (stopped)
        """
        runtime_per_hour = []
        timestamps = []

        start_events = {"RunInstances", "StartInstances"}
        stop_events = {"StopInstances", "TerminateInstances"}

        # Build running intervals from events
        running_intervals: List[tuple[datetime, datetime]] = []
        session_start: Optional[datetime] = None

        # Get instance state and launch time
        instance_state = instance.get("state", "").lower()
        launch_time = instance.get("launch_time")
        if launch_time and isinstance(launch_time, datetime) and launch_time.tzinfo is None:
            launch_time = launch_time.replace(tzinfo=timezone.utc)

        window_start = end_time - timedelta(hours=24)

        # Determine initial state at window_start
        # If instance was launched before our 24h window, check if it was running
        if launch_time and launch_time < window_start:
            # Instance existed before window - check for stop events before window
            has_early_stop = False
            last_event_before_window = None

            for event in events:
                event_time = event["time"]
                if event_time >= window_start:
                    break  # Events are sorted
                last_event_before_window = event

            # If last event before window was a start event (or no events), assume running
            if last_event_before_window is None:
                # No events before window, instance was launched earlier
                session_start = window_start
            elif last_event_before_window["name"] in start_events:
                # Last event was start, so instance was running at window start
                session_start = window_start
            elif last_event_before_window["name"] in stop_events:
                # Last event was stop, so instance was stopped at window start
                session_start = None

        # Process events within the 24h window
        for event in events:
            event_time = event["time"]
            event_name = event["name"]

            # Only consider events within our window
            if event_time < window_start:
                continue

            if event_name in start_events:
                if session_start is None:
                    session_start = event_time
                else:
                    logger.debug(f"Duplicate start event at {event_time}, ignoring")
            elif event_name in stop_events:
                if session_start is not None:
                    # Add interval
                    running_intervals.append((session_start, event_time))
                    session_start = None
                else:
                    logger.debug(f"Stop event without start at {event_time}, ignoring")

        # If still running at end_time, close the interval
        if session_start is not None:
            running_intervals.append((session_start, end_time))
        elif instance_state == "running" and not running_intervals:
            # No events but currently running - assume running entire window
            # This handles always-on instances
            logger.debug(f"Instance {instance.get('instance_id')} has no events but is running - assuming always-on")
            running_intervals.append((window_start, end_time))

        logger.debug(f"Built {len(running_intervals)} running intervals for last 24h")

        # Calculate runtime for each hour
        for hour_offset in range(24):
            hour_start = window_start + timedelta(hours=hour_offset)
            hour_end = hour_start + timedelta(hours=1)

            timestamps.append(hour_start)

            # Calculate overlap with running intervals
            total_seconds = 0.0

            for interval_start, interval_end in running_intervals:
                # Calculate overlap between this hour and the running interval
                overlap_start = max(hour_start, interval_start)
                overlap_end = min(hour_end, interval_end)

                if overlap_start < overlap_end:
                    overlap_seconds = (overlap_end - overlap_start).total_seconds()
                    total_seconds += overlap_seconds

            # Convert to fraction (0.0-1.0)
            runtime_fraction = min(total_seconds / 3600.0, 1.0)
            runtime_per_hour.append(runtime_fraction)

        logger.debug(
            f"Runtime per hour calculated: {sum(1 for r in runtime_per_hour if r > 0)} hours with runtime"
        )

        return runtime_per_hour, timestamps

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
            # Use UTC-aware datetime with stable hourly window
            # Always use data ending 1 hour ago to ensure CloudWatch completeness
            # This provides stable monthly projections (no intra-hour volatility)
            now = datetime.now(timezone.utc)
            end_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            start_time = end_time - timedelta(hours=24)

            results = self._gateway.fetch_cpu_metrics(
                instance_id=instance_id,
                region=self.config.region,
                start_time=start_time,
                end_time=end_time,
            )

            if not results:
                logger.error("❌ No CPU data available for %s - NO-FALLBACK policy enforced", instance_id)
                return None

            values = results[0].get("Values", [])
            if values:
                avg_cpu = sum(values) / len(values)
                payload = {
                    "cpu_utilization": avg_cpu,
                    "instance_id": instance_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "CloudWatch_get_metric_data",
                }
                self._repository.write_json(cache_path, payload)

                logger.info("✅ CPU Utilization %s: %.1f%% (cached)", instance_id, avg_cpu)
                return avg_cpu

            logger.error("❌ No CPU data available for %s - NO-FALLBACK policy enforced", instance_id)
            return None
        except Exception as error:  # pragma: no cover
            logger.warning("⚠️ CloudWatch CPU query error for %s: %s", instance_id, error)
            return None

    def _get_cpu_utilisation_hourly(self, instance_id: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Fetch hourly CPU utilization for last 24h (replaces single average).

        Returns hourly CPU values instead of a single average, enabling
        hourly-precise CO2 calculations.

        Args:
            instance_id: EC2 instance ID
            force_refresh: Force refresh from CloudWatch (ignore cache)

        Returns:
            Dictionary containing:
            - hourly_values: List of float (up to 24 values)
            - timestamps: List of datetime objects
            - average: float (backward compatibility)

            Returns None if no data available.

        Note:
            CloudWatch returns data with Period=3600 (1 hour), so we get
            individual values for each hour, not a single average.
        """
        cache_path = self._repository.path("cpu_utilization_hourly", instance_id)

        if not force_refresh and self._repository.is_valid(cache_path, CacheTTL.CPU_UTILIZATION):
            cached = self._repository.read_json(cache_path)
            if cached and "hourly_values" in cached:
                # Reconstruct datetime objects from ISO strings
                timestamps = [datetime.fromisoformat(ts) for ts in cached["timestamps"]]
                logger.debug(f"Using cached hourly CPU data for {instance_id}: {len(cached['hourly_values'])} hours")
                return {
                    "hourly_values": cached["hourly_values"],
                    "timestamps": timestamps,
                    "average": cached["average"],
                }

        try:
            # Use UTC-aware datetime with stable hourly window
            # Always use data ending 1 hour ago to ensure CloudWatch completeness
            # This provides stable monthly projections (no intra-hour volatility)
            now = datetime.now(timezone.utc)
            end_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            start_time = end_time - timedelta(hours=24)

            results = self._gateway.fetch_cpu_metrics(
                instance_id=instance_id,
                region=self.config.region,
                start_time=start_time,
                end_time=end_time,
            )

            if not results:
                logger.error("❌ No CPU data available for %s - NO-FALLBACK policy enforced", instance_id)
                return None

            # CloudWatch returns Values and Timestamps arrays
            values = results[0].get("Values", [])
            timestamps = results[0].get("Timestamps", [])

            if not values:
                logger.error("❌ No CPU values available for %s - NO-FALLBACK policy enforced", instance_id)
                return None

            avg_cpu = sum(values) / len(values)

            payload = {
                "hourly_values": values,
                "timestamps": [ts.isoformat() for ts in timestamps],
                "average": avg_cpu,
                "instance_id": instance_id,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "source": "CloudWatch_hourly_24h",
            }
            self._repository.write_json(cache_path, payload)

            logger.info(
                "✅ CPU Utilization Hourly %s: %d hours, avg %.1f%%, window=%s to %s",
                instance_id, len(values), avg_cpu,
                start_time.strftime("%Y-%m-%d %H:%M UTC"),
                end_time.strftime("%Y-%m-%d %H:%M UTC")
            )

            return {"hourly_values": values, "timestamps": timestamps, "average": avg_cpu}

        except Exception as error:  # pragma: no cover
            logger.warning("⚠️ CloudWatch CPU hourly query error for %s: %s", instance_id, error)
            return None

    # NOTE: Power and CO2 calculations consolidated in src.domain.calculations
    # to follow DRY principle. Functions removed from here:
    # - _calculate_effective_power() → calculate_simple_power_consumption()
    # - _calculate_monthly_co2() → calculate_co2_emissions()

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
        if all(
            value is not None for value in (runtime_hours, cpu_utilisation, effective_power_watts, monthly_cost_eur)
        ):
            return "measured"
        if any(
            value is not None for value in (runtime_hours, cpu_utilisation, effective_power_watts, monthly_cost_eur)
        ):
            return "partial"
        return "limited"
