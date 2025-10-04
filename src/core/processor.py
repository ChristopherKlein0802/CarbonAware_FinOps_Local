"""
Data Processing Controller for Carbon-Aware FinOps Dashboard
Main orchestration layer for all data processing and business calculations
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError, SSOError, TokenRetrievalError, UnauthorizedSSOTokenError

from ..constants import AcademicConstants
from ..config import settings
from ..utils.errors import AWSAuthenticationError, ErrorMessages
from ..models.aws import EC2Instance
from ..models.business import BusinessCase
from ..models.dashboard import DashboardData, APIHealthStatus, TimeSeriesPoint
from ..utils.calculations import safe_round
from ..services import (
    RuntimeService,
    CarbonDataService,
    BusinessInsightsService,
    create_runtime_service,
    create_carbon_data_service,
    create_business_insights_service,
)
from ..infrastructure.cache import FileCacheRepository
from ..infrastructure.clients import InfrastructureGateway, create_default_gateway
from ..infrastructure.clients.aws_runtime import AWSRuntimeGateway

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

    def __init__(
        self,
        *,
        runtime_service: Optional[RuntimeService] = None,
        carbon_service: Optional[CarbonDataService] = None,
        business_service: Optional[BusinessInsightsService] = None,
        repository: Optional[FileCacheRepository] = None,
        gateway: Optional[InfrastructureGateway] = None,
        runtime_gateway: Optional[AWSRuntimeGateway] = None,
    ):
        """Initialize data processor with optional service overrides."""

        self.repository = repository or FileCacheRepository(settings.cache_root)
        self.gateway = gateway or create_default_gateway(self.repository)
        self.runtime_gateway = runtime_gateway or AWSRuntimeGateway(profile=settings.aws_profile)

        self.runtime_service = runtime_service or create_runtime_service(
            repository=self.repository,
            gateway=self.gateway,
            runtime_gateway=self.runtime_gateway,
        )
        self.carbon_service = carbon_service or create_carbon_data_service(
            repository=self.repository,
            gateway=self.gateway,
        )
        self.business_service = business_service or create_business_insights_service()

        # Track last API call timestamps for dashboard transparency
        self.api_last_calls: Dict[str, Optional[datetime]] = {}

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

            # Get carbon intensity (1h cache)
            carbon_intensity = self.carbon_service.get_current_intensity(region="eu-central-1")

            if not carbon_intensity:
                logger.warning("❌ No carbon intensity data available")
                return self._create_empty_response("No carbon data available")

            if carbon_intensity.fetched_at:
                self.api_last_calls["ElectricityMaps"] = carbon_intensity.fetched_at
            else:
                self.api_last_calls["ElectricityMaps"] = datetime.now(timezone.utc)

            # Collect historical carbon data for TAC calculation
            carbon_history = self.carbon_service.get_recent_history(region="eu-central-1")
            self_collected_history = self.carbon_service.get_self_collected_history(region="eu-central-1")
            history_for_alignment = carbon_history or self_collected_history

            # Get EC2 instances (live AWS data)
            instances = self.runtime_service.list_instances()

            if not instances:
                logger.warning("❌ No EC2 instances found - but preserving available API data")
                return self._create_minimal_response(carbon_intensity, "No instances found")

            # Get cost data once for proportional allocation (region-specific)
            cost_data = self.gateway.get_monthly_costs("eu-central-1")
            fetched_at = getattr(cost_data, "fetched_at", None) if cost_data else None
            if isinstance(fetched_at, datetime):
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                self.api_last_calls["AWS Cost Explorer"] = fetched_at

            # Get hourly costs for last 24h (aligned with carbon data window)
            hourly_costs = self.gateway.get_hourly_costs(24, "eu-central-1") or []
            logger.info(f"📊 Retrieved {len(hourly_costs)} hourly cost entries from AWS Cost Explorer")

            # Process each instance with API data and enhanced tracking
            processed_instances: List[EC2Instance] = []
            for instance in instances:
                enriched = self.runtime_service.enrich_instance(
                    instance,
                    carbon_intensity=carbon_intensity.value,
                    force_refresh=force_refresh,
                )
                if enriched:
                    processed_instances.append(enriched)

            if not processed_instances:
                logger.warning("❌ No instances could be processed")
                return self._create_empty_response("Instance processing failed")

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

            # Calculate totals and business case
            total_cost_eur = sum(inst.monthly_cost_eur for inst in processed_instances if inst.monthly_cost_eur is not None)
            total_co2_kg = sum(inst.monthly_co2_kg for inst in processed_instances if inst.monthly_co2_kg is not None)

            # Enhanced validation: Compare calculated costs with actual AWS spending
            validation_factor, accuracy_status = self.business_service.validate_costs(
                processed_instances,
                total_cost_eur,
                cost_data,
            )

            # Persist hourly-aligned snapshot and compute TAC
            time_series_points, tac_score, tac_aligned_hours = self.carbon_service.build_time_series(
                hourly_costs,
                history_for_alignment,
                total_co2_kg,
            )

            cost_mape = None
            if validation_factor and validation_factor not in (0, float('inf')):
                try:
                    cost_mape = abs(1 - (1 / validation_factor))
                    logger.info(f"📊 Cost MAPE calculated: {cost_mape * 100:.1f}% (validation_factor={validation_factor:.2f})")
                except ZeroDivisionError:
                    cost_mape = None
            else:
                logger.warning(f"⚠️ Cost MAPE not calculated: validation_factor={validation_factor}")

            # Calculate business case with validation factor awareness
            business_case = self.business_service.calculate_business_case(
                baseline_cost_eur=total_cost_eur,
                baseline_co2_kg=total_co2_kg,
                validation_factor=validation_factor,
            )

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
                cost_mape=cost_mape,
                carbon_history=carbon_history or [],
                self_collected_carbon_history=self_collected_history or [],
            )

            logger.info(f"✅ Infrastructure analysis complete: {len(processed_instances)} instances, €{total_cost_eur:.2f} monthly")
            return dashboard_data

        except (NoCredentialsError, SSOError, UnauthorizedSSOTokenError, TokenRetrievalError, AWSAuthenticationError) as auth_error:
            logger.error("🚫 AWS authentication error: %s", auth_error)
            return self._create_auth_error_response(
                carbon_intensity,
                ErrorMessages.AWS_SSO_EXPIRED
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
        now = datetime.now(timezone.utc)

        def _status(healthy: bool, degraded: bool = False) -> tuple[str, bool]:
            if healthy:
                return "healthy", True
            if degraded:
                return "degraded", False
            return "error", False

        def _derive_status(has_full: bool, has_partial: bool, *, partial_message: str, missing_message: str) -> tuple[str, bool, Optional[str]]:
            if aws_auth_issue:
                return "degraded", False, ErrorMessages.AWS_SSO_EXPIRED
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
                else (ErrorMessages.AWS_SSO_EXPIRED if aws_auth_issue else "Cost validation pending"),
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
            time_series=self.carbon_service.get_cached_time_series(),
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
            time_series=self.carbon_service.get_cached_time_series(),
            tac_score=None,
            tac_aligned_hours=None,
            cost_mape=None
        )

    def _create_auth_error_response(self, carbon_intensity, error_message: str) -> DashboardData:
        """Create response when AWS authentication is missing"""
        guidance = ErrorMessages.AWS_SSO_FIX
        return DashboardData(
            instances=[],
            carbon_intensity=carbon_intensity,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
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
            time_series=self.carbon_service.get_cached_time_series(),
            tac_score=None,
            tac_aligned_hours=None,
            cost_mape=None
        )

    # All specialized functionality now properly delegated to dedicated modules:
    # - RuntimeService: EC2 collection, runtime calculation, instance enrichment
    # - BusinessInsightsService: Business case scenarios and cost validation
    # - CarbonDataService: Carbon intensity queries and time-series management
