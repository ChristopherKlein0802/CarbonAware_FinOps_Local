"""
FetchInfrastructureDataUseCase - Main workflow for infrastructure data

Coordinates fetching and enriching infrastructure data.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.domain.models import EC2Instance, DashboardData, CarbonIntensity
from src.domain.services import RuntimeService, CarbonDataService
from src.application.calculator import BusinessCaseCalculator
from src.application.use_cases.enrich_instance import EnrichInstanceUseCase
from src.infrastructure.gateways import InfrastructureGateway
from src.infrastructure.cache import FileCacheRepository

logger = logging.getLogger(__name__)


class FetchInfrastructureDataUseCase:
    """
    Fetch EC2 instances and enrich with carbon/cost data.

    Handles main data fetching workflow:
    - Carbon intensity data
    - EC2 instances
    - Cost data
    - Instance enrichment
    - API call tracking
    - Business case calculations
    """

    def __init__(
        self,
        runtime_service: RuntimeService,
        carbon_service: CarbonDataService,
        calculator: BusinessCaseCalculator,
        gateway: InfrastructureGateway,
        repository: FileCacheRepository,
    ):
        """
        Initialize with required services.

        Args:
            runtime_service: EC2 instance data
            carbon_service: Carbon intensity data
            calculator: Business case calculator
            gateway: Cost data access
            repository: Cache and API tracking
        """
        self.runtime_service = runtime_service
        self.carbon_service = carbon_service
        self.calculator = calculator
        self.gateway = gateway
        self.repository = repository
        self.enrich_use_case = EnrichInstanceUseCase(runtime_service)

        # Track last API call timestamps for dashboard transparency
        self.api_last_calls: dict[str, Optional[datetime]] = {}

    def execute(self, *, force_refresh: bool = False, period_days: int = 30) -> DashboardData:
        """
        Execute infrastructure data fetching workflow.

        Args:
            force_refresh: Bypass cache and fetch fresh data
            period_days: Analysis period in days (1, 7, or 30)

        Returns:
            DashboardData with enriched instances and period-based metrics

        Raises:
            AWSAuthenticationError, ClientError, ValueError, TypeError
        """
        # Reset API call log for this processing cycle
        self.api_last_calls = {}

        logger.info(f"📊 Starting infrastructure analysis with {period_days}-day period")

        # Step 1: Get carbon intensity (1h cache)
        carbon_intensity = self.carbon_service.get_current_intensity(region="eu-central-1")
        if not carbon_intensity:
            raise ValueError("No carbon intensity data available")

        if carbon_intensity.fetched_at:
            self.api_last_calls["ElectricityMaps"] = carbon_intensity.fetched_at
        else:
            self.api_last_calls["ElectricityMaps"] = datetime.now(timezone.utc)

        # Step 2: Collect historical carbon data for visualizations
        carbon_history = self.carbon_service.get_recent_history(region="eu-central-1")
        self_collected_history = self.carbon_service.get_self_collected_history(region="eu-central-1")

        # Step 3: Get EC2 instances (live AWS data)
        instances = self.runtime_service.list_instances()
        if not instances:
            raise ValueError("No EC2 instances found")

        # Step 4: Get cost data for specified period (region-specific)
        cost_data = self.gateway.get_costs("eu-central-1", period_days)
        fetched_at = getattr(cost_data, "fetched_at", None) if cost_data else None
        if isinstance(fetched_at, datetime):
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            self.api_last_calls["AWS Cost Explorer"] = fetched_at

        # Step 5: Get hourly costs for last 24h (aligned with carbon data window)
        hourly_costs = self.gateway.get_hourly_costs(24, "eu-central-1") or []
        logger.info(f"📊 Retrieved {len(hourly_costs)} hourly cost entries from AWS Cost Explorer")

        # Step 6: Process each instance with API data and enhanced tracking
        processed_instances: List[EC2Instance] = []
        for instance in instances:
            enriched = self.enrich_use_case.execute(
                instance,
                carbon_intensity=carbon_intensity.value,
                carbon_history=carbon_history,  # NEW: Pass carbon history for hourly calculation
                force_refresh=force_refresh,
                period_days=period_days,  # Pass analysis period to enrichment
            )
            if enriched:
                processed_instances.append(enriched)

        if not processed_instances:
            raise ValueError("No instances could be processed")

        # Step 7: Track API call timestamps from cache metadata
        self._track_api_timestamps(processed_instances)

        # Step 8: Calculate totals with dual comparison
        # Separate instances by calculation method
        hourly_precise_instances = [i for i in processed_instances if i.co2_calculation_method == "hourly"]
        fallback_instances = [i for i in processed_instances if i.co2_calculation_method == "average"]

        # Aggregate totals for both calculation methods
        # Hourly-Precise totals (from instances with 24h carbon data)
        total_cost_hourly = sum(
            inst.cost_eur_hourly for inst in hourly_precise_instances
            if inst.cost_eur_hourly is not None
        )
        total_co2_hourly = sum(
            inst.co2_kg_hourly for inst in hourly_precise_instances
            if inst.co2_kg_hourly is not None
        )

        # Average-Based totals (from all instances)
        total_cost_average = sum(
            inst.cost_eur_average for inst in processed_instances
            if inst.cost_eur_average is not None
        )
        total_co2_average = sum(
            inst.co2_kg_average for inst in processed_instances
            if inst.co2_kg_average is not None
        )

        # DEPRECATED: Backward compatibility fields (use average-based totals)
        total_cost_eur = total_cost_average
        total_co2_kg = total_co2_average

        logger.info(
            f"📊 Aggregation: {len(hourly_precise_instances)} hourly-precise, {len(fallback_instances)} average-based | "
            f"CO2: {total_co2_hourly:.3f} kg (hourly) vs {total_co2_average:.3f} kg (average) | "
            f"Cost: €{total_cost_hourly:.2f} (hourly) vs €{total_cost_average:.2f} (average)"
        )

        # Step 9: Enhanced validation - compare calculated costs with actual AWS spending
        # NOTE: Use average-based costs for validation (factual runtime-based comparison)
        validation_factor = self.calculator.calculate_cloudtrail_enhanced_accuracy(
            processed_instances,
            total_cost_average,  # Average-based total for validation
            cost_data,
            original_instances=None,
        )
        accuracy_status = getattr(self.calculator, "_last_accuracy_status", None)

        # Step 10: Calculate CloudTrail Coverage for data quality validation
        cloudtrail_coverage, cloudtrail_tracked = self._calculate_cloudtrail_coverage(processed_instances)

        # Step 12: Calculate business case with validation factor awareness
        # NOTE: Using average-based totals as baseline (most conservative estimate)
        business_case = self.calculator.calculate_business_case(
            baseline_cost=total_cost_average,
            baseline_co2=total_co2_average,
            validation_factor=validation_factor,
        )

        # Step 13: Create complete dashboard data (health status will be added by orchestrator)
        dashboard_data = DashboardData(
            instances=processed_instances,
            carbon_intensity=carbon_intensity,
            analysis_period_days=period_days,
            # New field names (primary)
            total_cost_hourly=total_cost_hourly,
            total_co2_hourly=total_co2_hourly,
            total_cost_average=total_cost_average,
            total_co2_average=total_co2_average,
            hourly_precise_count=len(hourly_precise_instances),
            fallback_count=len(fallback_instances),
            # DEPRECATED: Backward compatibility fields
            total_cost_eur=total_cost_eur,
            total_co2_kg=total_co2_kg,
            business_case=business_case,
            data_freshness=datetime.now(),
            academic_disclaimers=[
                "All optimization calculations require empirical validation",
                "Conservative estimates with ±15% uncertainty range",
                "Theoretical scenarios for methodology demonstration",
            ],
            api_health_status={},  # Will be filled by orchestrator
            validation_factor=validation_factor,
            accuracy_status=accuracy_status,
            cloudtrail_coverage=cloudtrail_coverage,
            cloudtrail_tracked_instances=cloudtrail_tracked,
            carbon_history=carbon_history or [],
            self_collected_carbon_history=self_collected_history or [],
        )

        logger.info(
            f"✅ Infrastructure analysis complete: {len(processed_instances)} instances, "
            f"€{total_cost_average:.2f} ({period_days}d period)"
        )
        return dashboard_data

    def _track_api_timestamps(self, processed_instances: List[EC2Instance]) -> None:
        """Track API call timestamps from cache metadata"""

        def _cache_mtime(path: Optional[Path]) -> Optional[datetime]:
            if not path:
                return None
            try:
                return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except (FileNotFoundError, OSError):
                return None

        def _latest_for_source(marker: str, path_builder) -> Optional[datetime]:
            timestamps: list[datetime] = []
            for inst in processed_instances:
                if not (inst.data_sources and marker in inst.data_sources):
                    continue

                cache_path = path_builder(inst)
                cache_timestamp = _cache_mtime(cache_path)
                if cache_timestamp:
                    timestamps.append(cache_timestamp)
                    continue

                inst_updated = getattr(inst, "last_updated", None)
                if inst_updated:
                    if inst_updated.tzinfo is None:
                        inst_updated = inst_updated.replace(tzinfo=timezone.utc)
                    timestamps.append(inst_updated)

            return max(timestamps) if timestamps else None

        source_mapping = {
            "Boavizta": (
                "boavizta",
                lambda inst: self.repository.path("boavizta_power", inst.instance_type),
            ),
            "AWS Pricing": (
                "aws_pricing",
                lambda inst: self.repository.path("pricing", f"{inst.instance_type}_{inst.region}"),
            ),
            "AWS CloudWatch": (
                "cloudwatch",
                lambda inst: self.repository.path("cpu_utilization", inst.instance_id),
            ),
            "AWS CloudTrail": (
                "cloudtrail_audit",
                lambda inst: self.repository.path("cloudtrail_runtime", f"{inst.instance_id}_{inst.region}"),
            ),
        }

        for api_name, (marker, path_builder) in source_mapping.items():
            latest_ts = _latest_for_source(marker, path_builder)
            if latest_ts:
                self.api_last_calls[api_name] = latest_ts

        logger.debug("API last call timestamps: %s", self.api_last_calls)

    def _calculate_cloudtrail_coverage(self, instances: List[EC2Instance]) -> tuple[Optional[float], Optional[int]]:
        """
        Calculate CloudTrail Coverage: percentage of instances with runtime data.

        High coverage (≥90%) indicates reliable instance-specific cost calculations.
        Low coverage suggests CloudTrail retention or permission issues.

        Args:
            instances: List of EC2 instances

        Returns:
            Tuple of (coverage_ratio, tracked_count)
        """
        if not instances:
            return None, None

        total = len(instances)
        tracked = len([i for i in instances if getattr(i, "runtime_hours", None) and i.runtime_hours > 0])
        coverage = tracked / total if total > 0 else 0.0

        logger.info(f"📋 CloudTrail Coverage: {coverage * 100:.1f}% ({tracked}/{total} instances tracked)")
        return coverage, tracked
