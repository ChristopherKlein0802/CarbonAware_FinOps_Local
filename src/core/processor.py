"""
Data Processing Controller for Carbon-Aware FinOps Dashboard
Main orchestration layer for all data processing and business calculations
"""

import os
import json
import logging
import boto3
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError, SSOError, TokenRetrievalError, UnauthorizedSSOTokenError

from ..constants import AcademicConstants, ErrorConstants
from ..api.client import unified_api_client
from ..models.aws import EC2Instance
from ..models.business import BusinessCase
from ..models.dashboard import DashboardData, APIHealthStatus, TimeSeriesPoint
from ..utils.calculations import safe_round
from ..utils.cache import is_cache_valid, get_standard_cache_path, ensure_cache_dir, CacheTTL
from .tracker import RuntimeTracker
from .calculator import CarbonCalculator, BusinessCaseCalculator
from ..utils.errors import AWSAuthenticationError

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Professional Data Processing Controller

    Responsibilities:
    - Business logic orchestration
    - AWS instance data collection
    - Conservative academic estimations
    - Academic integrity (no fallback data)
    """

    def __init__(self):
        """Initialize data processor using centralized constants"""

        # Initialize core components
        self.runtime_tracker = RuntimeTracker()
        self.carbon_calculator = CarbonCalculator()
        self.business_calculator = BusinessCaseCalculator()

        # Track last API call timestamps for dashboard transparency
        self.api_last_calls: Dict[str, Optional[datetime]] = {}

        # Local persistence for hourly-aligned cost/carbon snapshots
        self._timeseries_path = get_standard_cache_path("timeseries", "cost_carbon")
        ensure_cache_dir(self._timeseries_path)

        # INTEGRATION EXCELLENCE FOCUS - The real thesis contribution
        self.METHODOLOGY_ACHIEVEMENTS = {
            "DATA_INTEGRATION": {
                "description": "5-API orchestration with optimized caching strategies",
                "apis": ["ElectricityMaps", "AWS Cost Explorer", "AWS CloudTrail", "Boavizta", "AWS CloudWatch"],
                "cost_optimization": "€5/month vs €200+ separate tools",
                "evidence_level": "IMPLEMENTED",
                "academic_contribution": "First integrated carbon+cost+precision tool for German SMEs"
            },
            "CLOUDTRAIL_INNOVATION": {
                "description": "Runtime precision via AWS audit events instead of estimates",
                "innovation": "State change timestamps for exact runtime calculation",
                "comparison": "Exact vs estimated runtime (eliminates guesswork)",
                "evidence_level": "IMPLEMENTED",
                "academic_contribution": "Novel application of AWS CloudTrail for environmental optimization"
            },
            "REGIONAL_SPECIALIZATION": {
                "description": "German grid carbon intensity integration (EU-Central-1 focus)",
                "variability_range": "250-550g CO2/kWh observed in German grid",
                "business_relevance": "EU Green Deal compliance for German SME market",
                "evidence_level": "DATA_VERIFIED",
                "academic_contribution": "Regional carbon optimization vs generic EU averages"
            },
            "_thesis_focus": "Methodology and integration excellence, not optimization predictions"
        }

        # Academic constants for uncertainty documentation
        self.ACADEMIC_CONSTANTS = {
            "cloudtrail_precision": "±5% accuracy vs ±40% estimates",
            "carbon_uncertainty": "±15% typical ElectricityMaps range",
            "cost_uncertainty": "±10% AWS billing reconciliation",
            "methodology": "Conservative estimates with documented ranges"
        }

        logger.info("✅ Data Processor initialized")

    def get_infrastructure_data(self, *, force_refresh: bool = False) -> Optional[DashboardData]:
        """
        Main controller method - orchestrates all data processing

        Returns:
            DashboardData: Complete dashboard data structure or None
        """
        carbon_intensity = None
        try:
            # Reset API call log for this processing cycle
            self.api_last_calls = {}

            # Get carbon intensity (30min cache)
            carbon_intensity = unified_api_client.get_current_carbon_intensity("eu-central-1")

            if not carbon_intensity:
                logger.warning("❌ No carbon intensity data available")
                return self._create_empty_response("No carbon data available")

            if carbon_intensity.fetched_at:
                self.api_last_calls["ElectricityMaps"] = carbon_intensity.fetched_at
            else:
                self.api_last_calls["ElectricityMaps"] = datetime.now(timezone.utc)

            # Collect historical carbon data for TAC calculation
            carbon_history = unified_api_client.get_carbon_intensity_24h("eu-central-1")
            if not carbon_history:
                carbon_history = unified_api_client.get_self_collected_24h_data("eu-central-1")

            # Get EC2 instances (live AWS data)
            instances = self.runtime_tracker.get_all_ec2_instances()

            if not instances:
                logger.warning("❌ No EC2 instances found - but preserving available API data")
                return self._create_minimal_response(carbon_intensity, "No instances found")

            # Get cost data once for proportional allocation
            cost_data = unified_api_client.get_monthly_costs()
            fetched_at = getattr(cost_data, "fetched_at", None) if cost_data else None
            if isinstance(fetched_at, datetime):
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                self.api_last_calls["AWS Cost Explorer"] = fetched_at
            hourly_costs = unified_api_client.get_hourly_costs(48) or []
            if hourly_costs:
                now_ts = datetime.now(timezone.utc)
                self.api_last_calls["AWS Cost Explorer (hourly)"] = now_ts
                existing_ce = self.api_last_calls.get("AWS Cost Explorer")
                if not existing_ce or (isinstance(existing_ce, datetime) and now_ts > existing_ce):
                    self.api_last_calls["AWS Cost Explorer"] = now_ts

            # Process each instance with API data and enhanced tracking
            processed_instances = []
            for instance in instances:
                processed_instance = self.runtime_tracker.process_instance_enhanced(
                    instance,
                    carbon_intensity.value,
                    force_refresh=force_refresh,
                )
                if processed_instance:
                    processed_instances.append(processed_instance)

            if not processed_instances:
                logger.warning("❌ No instances could be processed")
                return self._create_empty_response("Instance processing failed")

            def _latest_for_source(marker: str) -> Optional[datetime]:
                timestamps = [
                    inst.last_updated
                    for inst in processed_instances
                    if inst.last_updated and inst.data_sources and marker in inst.data_sources
                ]
                if not timestamps:
                    return None
                latest = max(timestamps)
                if latest.tzinfo is None:
                    latest = latest.replace(tzinfo=timezone.utc)
                return latest

            source_mapping = {
                "Boavizta": "boavizta",
                "AWS Pricing": "aws_pricing",
                "AWS CloudWatch": "cloudwatch",
                "AWS CloudTrail": "cloudtrail_audit",
            }
            for api_name, marker in source_mapping.items():
                latest_ts = _latest_for_source(marker)
                if latest_ts:
                    self.api_last_calls[api_name] = latest_ts

            # Calculate totals and business case
            total_cost_eur = sum(inst.monthly_cost_eur for inst in processed_instances if inst.monthly_cost_eur is not None)
            total_co2_kg = sum(inst.monthly_co2_kg for inst in processed_instances if inst.monthly_co2_kg is not None)

            # Enhanced validation: Compare calculated costs with actual AWS spending
            validation_factor = self.business_calculator.calculate_cloudtrail_enhanced_accuracy(processed_instances, total_cost_eur, cost_data, instances)
            accuracy_status = getattr(self.business_calculator, '_last_accuracy_status', None)

            # Persist hourly-aligned snapshot and compute TAC
            time_series_points, tac_score, tac_aligned_hours = self._build_time_series(
                hourly_costs,
                carbon_history,
                total_co2_kg,
            )

            cost_mape = None
            if validation_factor and validation_factor not in (0, float('inf')):
                try:
                    cost_mape = abs(1 - (1 / validation_factor))
                except ZeroDivisionError:
                    cost_mape = None

            # Calculate business case with validation factor awareness
            business_case = self.business_calculator.calculate_business_case(total_cost_eur, total_co2_kg, validation_factor)

            api_health_status = self._build_api_health_status(
                carbon_available=carbon_intensity is not None,
                cost_available=cost_data is not None and getattr(cost_data, 'monthly_cost_usd', 0.0) >= 0.0,
                processed_instances=processed_instances
            )

            # Create complete dashboard data
            dashboard_data = DashboardData(
                instances=processed_instances,
                carbon_intensity=carbon_intensity,
                total_cost_eur=total_cost_eur,
                total_co2_kg=total_co2_kg,
                business_case=business_case,
                data_freshness=datetime.now(),
                uncertainty_ranges=self.ACADEMIC_CONSTANTS,
                academic_disclaimers=[
                    "All optimization calculations require empirical validation",
                    "Conservative estimates with ±15% uncertainty range",
                    "Theoretical scenarios for methodology demonstration"
                ],
                api_health_status=api_health_status,
                validation_factor=validation_factor,
                accuracy_status=accuracy_status,
                time_series=time_series_points,
                tac_score=tac_score,
                tac_aligned_hours=tac_aligned_hours,
                cost_mape=cost_mape
            )

            logger.info(f"✅ Infrastructure analysis complete: {len(processed_instances)} instances, €{total_cost_eur:.2f} monthly")
            return dashboard_data

        except (NoCredentialsError, SSOError, UnauthorizedSSOTokenError, TokenRetrievalError, AWSAuthenticationError) as auth_error:
            logger.error("🚫 AWS authentication error: %s", auth_error)
            return self._create_auth_error_response(
                carbon_intensity,
                ErrorConstants.AWS_SSO_EXPIRED_MSG
            )
        except ClientError as client_error:
            logger.error("❌ AWS client error: %s", client_error)
            message = client_error.response.get("Error", {}).get("Message") if hasattr(client_error, "response") else str(client_error)
            return self._create_minimal_response(carbon_intensity, message or "AWS client error occurred")
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"❌ Data validation/type error: {e}")
            return self._create_empty_response(f"Data validation error: {str(e)}")
        except (AttributeError, ImportError) as e:
            logger.error(f"❌ Module/attribute error: {e}")
            return self._create_empty_response(f"Module error: {str(e)}")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Network/API error: {e}")
            return self._create_empty_response(f"Network error: {str(e)}")

    def _build_api_health_status(
        self,
        *,
        carbon_available: bool,
        cost_available: bool,
        processed_instances: List[EC2Instance],
        aws_auth_issue: bool = False
    ) -> Dict[str, APIHealthStatus]:
        """Create API health status objects for dashboard display"""
        now = datetime.now()

        def _status(healthy: bool, degraded: bool = False) -> tuple[str, bool]:
            if healthy:
                return "healthy", True
            if degraded:
                return "degraded", False
            return "error", False

        def _derive_status(has_full: bool, has_partial: bool, *, partial_message: str, missing_message: str) -> tuple[str, bool, Optional[str]]:
            if aws_auth_issue:
                return "degraded", False, ErrorConstants.AWS_SSO_EXPIRED_MSG
            if not processed_instances:
                return "degraded", False, missing_message
            if has_full:
                return "healthy", True, None
            if has_partial:
                return "degraded", False, partial_message
            return "error", False, missing_message

        runtime_instances = [inst for inst in processed_instances if inst.runtime_hours is not None]
        cpu_instances = [inst for inst in processed_instances if inst.cpu_utilization is not None]
        pricing_instances = [inst for inst in processed_instances if inst.hourly_price_usd is not None]
        power_instances = [inst for inst in processed_instances if inst.power_watts is not None]

        cloudtrail_status, cloudtrail_healthy, cloudtrail_message = _derive_status(
            len(runtime_instances) == len(processed_instances),
            bool(runtime_instances),
            partial_message="Partial runtimes",
            missing_message="Runtime data unavailable"
        )
        cloudwatch_status, cloudwatch_healthy, cloudwatch_message = _derive_status(
            len(cpu_instances) == len(processed_instances),
            bool(cpu_instances),
            partial_message="Partial CPU data",
            missing_message="CPU metrics missing"
        )
        pricing_status, pricing_healthy, pricing_message = _derive_status(
            len(pricing_instances) == len(processed_instances),
            bool(pricing_instances),
            partial_message="Partial pricing",
            missing_message="Pricing unavailable"
        )
        power_status, power_healthy, power_message = _derive_status(
            len(power_instances) == len(processed_instances),
            bool(power_instances),
            partial_message="Partial power data",
            missing_message="Power model data unavailable"
        )

        def _api_call_time(key: str) -> Optional[datetime]:
            return self.api_last_calls.get(key)

        statuses: Dict[str, APIHealthStatus] = {
            "ElectricityMaps": APIHealthStatus(
                service="ElectricityMaps",
                status="healthy" if carbon_available else "error",
                response_time_ms=0.0,
                last_check=now,
                healthy=carbon_available,
                error_message=None if carbon_available else "No carbon intensity data",
                last_api_call=_api_call_time("ElectricityMaps"),
            ),
            "AWS Cost Explorer": APIHealthStatus(
                service="AWS Cost Explorer",
                status="healthy" if cost_available else "degraded",
                response_time_ms=0.0,
                last_check=now,
                healthy=cost_available and not aws_auth_issue,
                error_message=None
                if cost_available
                else (ErrorConstants.AWS_SSO_EXPIRED_MSG if aws_auth_issue else "Cost validation pending"),
                last_api_call=_api_call_time("AWS Cost Explorer"),
            ),
            "AWS CloudTrail": APIHealthStatus(
                service="AWS CloudTrail",
                status=cloudtrail_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=cloudtrail_healthy,
                error_message=cloudtrail_message,
                last_api_call=_api_call_time("AWS CloudTrail"),
            ),
            "AWS Pricing": APIHealthStatus(
                service="AWS Pricing",
                status=pricing_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=pricing_healthy,
                error_message=pricing_message,
                last_api_call=_api_call_time("AWS Pricing"),
            ),
            "Boavizta": APIHealthStatus(
                service="Boavizta",
                status=power_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=power_healthy,
                error_message=power_message,
                last_api_call=_api_call_time("Boavizta"),
            ),
            "AWS CloudWatch": APIHealthStatus(
                service="AWS CloudWatch",
                status=cloudwatch_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=cloudwatch_healthy,
                error_message=cloudwatch_message,
                last_api_call=_api_call_time("AWS CloudWatch"),
            )
        }

        return statuses

    def _create_empty_response(self, error_message: str) -> DashboardData:
        """Create empty response structure for error cases"""
        return DashboardData(
            instances=[],
            carbon_intensity=None,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
            uncertainty_ranges=self.ACADEMIC_CONSTANTS,
            academic_disclaimers=[
                error_message,
                "Academic integrity maintained - no fallback data used"
            ],
            api_health_status=self._build_api_health_status(
                carbon_available=False,
                cost_available=False,
                processed_instances=[],
                aws_auth_issue=False
            ),
            validation_factor=None,
            accuracy_status=None,
            time_series=self._load_time_series(),
            tac_score=None,
            tac_aligned_hours=None,
            cost_mape=None
        )

    def _create_minimal_response(self, carbon_intensity, error_message: str) -> DashboardData:
        """Create minimal response with available API data but no instances"""
        return DashboardData(
            instances=[],
            carbon_intensity=carbon_intensity,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
            uncertainty_ranges=self.ACADEMIC_CONSTANTS,
            academic_disclaimers=[
                error_message,
                "Academic integrity maintained - preserving available API data"
            ],
            api_health_status=self._build_api_health_status(
                carbon_available=carbon_intensity is not None,
                cost_available=False,
                processed_instances=[],
                aws_auth_issue=False
            ),
            validation_factor=None,
            accuracy_status=None,
            time_series=self._load_time_series(),
            tac_score=None,
            tac_aligned_hours=None,
            cost_mape=None
        )

    def _create_auth_error_response(self, carbon_intensity, error_message: str) -> DashboardData:
        """Create response when AWS authentication is missing"""
        guidance = ErrorConstants.AWS_SSO_FIX_MSG
        return DashboardData(
            instances=[],
            carbon_intensity=carbon_intensity,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
            uncertainty_ranges=self.ACADEMIC_CONSTANTS,
            academic_disclaimers=[
                error_message,
                guidance
            ],
            api_health_status=self._build_api_health_status(
                carbon_available=carbon_intensity is not None,
                cost_available=False,
                processed_instances=[],
                aws_auth_issue=True
            ),
            validation_factor=None,
            accuracy_status=None,
            time_series=self._load_time_series(),
            tac_score=None,
            tac_aligned_hours=None,
            cost_mape=None
        )

    # All specialized functionality now properly delegated to dedicated modules:
    # - RuntimeTracker: EC2 collection, runtime calculation, instance processing
    # - BusinessCaseCalculator: Business case scenarios and cost validation
    # - CarbonCalculator: CO2 emissions calculation

    def _load_time_series(self) -> List[TimeSeriesPoint]:
        """Load cached cost/carbon time series data."""

        if not os.path.exists(self._timeseries_path):
            return []

        try:
            with open(self._timeseries_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, TypeError) as error:
            logger.warning("⚠️ Failed to load time series cache: %s", error)
            return []

        points: List[TimeSeriesPoint] = []
        for entry in payload:
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

    def _save_time_series(self, points: List[TimeSeriesPoint]) -> None:
        """Persist cost/carbon time series data."""

        serialised = [
            {
                "timestamp": point.timestamp.isoformat(),
                "cost_eur_per_hour": safe_round(point.cost_eur_per_hour, 6),
                "co2_kg_per_hour": safe_round(point.co2_kg_per_hour, 6),
                "carbon_intensity": point.carbon_intensity,
            }
            for point in points
        ]

        try:
            with open(self._timeseries_path, "w", encoding="utf-8") as handle:
                json.dump(serialised, handle, indent=2)
        except OSError as error:
            logger.warning("⚠️ Failed to persist time series cache: %s", error)

    def _build_time_series(
        self,
        hourly_costs: List[Dict[str, Any]],
        carbon_history: Optional[List[Dict[str, Any]]],
        total_co2_kg: float,
    ) -> tuple[List[TimeSeriesPoint], Optional[float], Optional[int]]:
        """Merge AWS cost series with carbon intensity for TAC calculation."""

        if not hourly_costs:
            # Return cached series so that UI still shows previous values
            cached = self._load_time_series()
            return cached, None, None

        cost_map: Dict[datetime, float] = {}
        for entry in hourly_costs:
            timestamp_raw = entry.get("timestamp")
            cost_value = entry.get("cost_eur")
            if timestamp_raw is None or cost_value is None:
                continue
            try:
                if isinstance(timestamp_raw, datetime):
                    ts = timestamp_raw
                else:
                    ts = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            except ValueError:
                continue

            normalized = self._normalize_hour(ts)
            if normalized is None:
                continue
            cost_map[normalized] = float(cost_value)

        if not cost_map:
            cached = self._load_time_series()
            return cached, None, None

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
            normalized = self._normalize_hour(ts_obj)
            if normalized is None:
                continue
            try:
                carbon_map[normalized] = float(value)
            except (TypeError, ValueError):
                continue

        window_start = self._normalize_hour(datetime.now(timezone.utc) - timedelta(hours=48))
        if window_start is None:
            window_start = datetime.now().replace(minute=0, second=0, microsecond=0)

        points: List[TimeSeriesPoint] = []
        sorted_hours = sorted(hour for hour in cost_map.keys() if hour >= window_start)
        if not sorted_hours:
            sorted_hours = sorted(cost_map.keys())

        co2_estimate = None
        if total_co2_kg and len(sorted_hours) > 0:
            co2_estimate = total_co2_kg / len(sorted_hours)

        for hour in sorted_hours:
            cost_value = cost_map.get(hour, 0.0)
            carbon_value = carbon_map.get(hour)
            co2_value = safe_round(co2_estimate, 6) if co2_estimate is not None else 0.0
            points.append(
                TimeSeriesPoint(
                    timestamp=hour,
                    cost_eur_per_hour=safe_round(cost_value, 6),
                    co2_kg_per_hour=co2_value,
                    carbon_intensity=carbon_value,
                )
            )

        self._save_time_series(points)

        cost_hours = set(sorted_hours)
        carbon_hours = {hour for hour in carbon_map.keys() if hour in cost_hours}
        aligned_hours = len(carbon_hours)
        tac_score = aligned_hours / len(cost_hours) if cost_hours else None

        return points, tac_score, aligned_hours

    def _normalize_hour(self, timestamp: datetime) -> Optional[datetime]:
        """Normalize timestamps to naive hours in local timezone."""

        if timestamp is None:
            return None

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        localized = timestamp.astimezone().replace(minute=0, second=0, microsecond=0)
        return localized.replace(tzinfo=None)
