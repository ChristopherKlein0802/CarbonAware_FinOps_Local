"""
BuildAPIHealthStatusUseCase - API health status monitoring

Extracted from orchestrator.py (lines 277-398) - _build_api_health_status()
This use case creates API health status objects for dashboard transparency.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

from src.domain.models import EC2Instance, APIHealthStatus
from src.domain.errors import ErrorMessages

logger = logging.getLogger(__name__)


class BuildAPIHealthStatusUseCase:
    """
    Use Case: Build API health status for dashboard monitoring

    Responsibilities:
    - Assess health of all external APIs
    - Track API call timestamps
    - Provide detailed status and error messages
    - Support degraded states (partial data availability)

    Monitored APIs:
    - ElectricityMaps (carbon intensity)
    - AWS Cost Explorer (cost data)
    - AWS CloudTrail (runtime hours)
    - AWS CloudWatch (CPU metrics)
    - AWS Pricing (instance pricing)
    - Boavizta (power consumption models)
    """

    def execute(
        self,
        *,
        carbon_available: bool,
        cost_available: bool,
        processed_instances: List[EC2Instance],
        api_last_calls: Dict[str, Optional[datetime]],
        aws_auth_issue: bool = False,
    ) -> Dict[str, APIHealthStatus]:
        """
        Build API health status objects for dashboard display

        Args:
            carbon_available: Whether carbon intensity data is available
            cost_available: Whether cost data is available
            processed_instances: List of processed EC2 instances
            api_last_calls: Dictionary of last API call timestamps
            aws_auth_issue: Whether AWS authentication is failing

        Returns:
            Dictionary mapping API names to their health status
        """
        now = datetime.now(timezone.utc)

        # Analyze instance data sources
        runtime_instances = [inst for inst in processed_instances if inst.runtime_hours is not None]
        cpu_instances = [inst for inst in processed_instances if inst.cpu_utilization is not None]
        pricing_instances = [inst for inst in processed_instances if inst.hourly_price_usd is not None]
        power_instances = [inst for inst in processed_instances if inst.power_watts is not None]

        # Derive status for AWS services
        cloudtrail_status, cloudtrail_healthy, cloudtrail_message = self._derive_status(
            has_full=len(runtime_instances) == len(processed_instances),
            has_partial=bool(runtime_instances),
            partial_message="Partial runtimes",
            missing_message="Runtime data unavailable",
            aws_auth_issue=aws_auth_issue,
            processed_instances=processed_instances,
        )

        cloudwatch_status, cloudwatch_healthy, cloudwatch_message = self._derive_status(
            has_full=len(cpu_instances) == len(processed_instances),
            has_partial=bool(cpu_instances),
            partial_message="Partial CPU data",
            missing_message="CPU metrics missing",
            aws_auth_issue=aws_auth_issue,
            processed_instances=processed_instances,
        )

        pricing_status, pricing_healthy, pricing_message = self._derive_status(
            has_full=len(pricing_instances) == len(processed_instances),
            has_partial=bool(pricing_instances),
            partial_message="Partial pricing",
            missing_message="Pricing unavailable",
            aws_auth_issue=aws_auth_issue,
            processed_instances=processed_instances,
        )

        power_status, power_healthy, power_message = self._derive_status(
            has_full=len(power_instances) == len(processed_instances),
            has_partial=bool(power_instances),
            partial_message="Partial power data",
            missing_message="Power model data unavailable",
            aws_auth_issue=aws_auth_issue,
            processed_instances=processed_instances,
        )

        # Build complete status dictionary
        statuses: Dict[str, APIHealthStatus] = {
            "ElectricityMaps": APIHealthStatus(
                service="ElectricityMaps",
                status="healthy" if carbon_available else "error",
                response_time_ms=0.0,
                last_check=now,
                healthy=carbon_available,
                error_message=None if carbon_available else "No carbon intensity data",
                last_api_call=api_last_calls.get("ElectricityMaps"),
            ),
            "AWS Cost Explorer": APIHealthStatus(
                service="AWS Cost Explorer",
                status="healthy" if cost_available else "degraded",
                response_time_ms=0.0,
                last_check=now,
                healthy=cost_available and not aws_auth_issue,
                error_message=(
                    None
                    if cost_available
                    else (ErrorMessages.AWS_SSO_EXPIRED if aws_auth_issue else "Cost validation pending")
                ),
                last_api_call=api_last_calls.get("AWS Cost Explorer"),
            ),
            "AWS CloudTrail": APIHealthStatus(
                service="AWS CloudTrail",
                status=cloudtrail_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=cloudtrail_healthy,
                error_message=cloudtrail_message,
                last_api_call=api_last_calls.get("AWS CloudTrail"),
            ),
            "AWS Pricing": APIHealthStatus(
                service="AWS Pricing",
                status=pricing_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=pricing_healthy,
                error_message=pricing_message,
                last_api_call=api_last_calls.get("AWS Pricing"),
            ),
            "Boavizta": APIHealthStatus(
                service="Boavizta",
                status=power_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=power_healthy,
                error_message=power_message,
                last_api_call=api_last_calls.get("Boavizta"),
            ),
            "AWS CloudWatch": APIHealthStatus(
                service="AWS CloudWatch",
                status=cloudwatch_status,
                response_time_ms=0.0,
                last_check=now,
                healthy=cloudwatch_healthy,
                error_message=cloudwatch_message,
                last_api_call=api_last_calls.get("AWS CloudWatch"),
            ),
        }

        return statuses

    def _derive_status(
        self,
        *,
        has_full: bool,
        has_partial: bool,
        partial_message: str,
        missing_message: str,
        aws_auth_issue: bool,
        processed_instances: List[EC2Instance],
    ) -> tuple[str, bool, Optional[str]]:
        """
        Derive health status based on data availability

        Returns:
            Tuple of (status_string, is_healthy, error_message)
        """
        if aws_auth_issue:
            return "degraded", False, ErrorMessages.AWS_SSO_EXPIRED

        if not processed_instances:
            return "degraded", False, missing_message

        if has_full:
            return "healthy", True, None

        if has_partial:
            return "degraded", False, partial_message

        return "error", False, missing_message
