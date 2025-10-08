"""
CreateErrorResponseUseCase - Error response factory (DRY principle)

Extracted from orchestrator.py (lines 400-480) - error response methods
This use case consolidates all error response creation logic in one place.
"""

import logging
from datetime import datetime
from typing import Optional

from src.domain.models import DashboardData, CarbonIntensity
from src.domain.services import CarbonDataService
from src.application.use_cases.build_api_health_status import BuildAPIHealthStatusUseCase
from src.domain.errors import ErrorMessages

logger = logging.getLogger(__name__)


class CreateErrorResponseUseCase:
    """
    Use Case: Error Response Factory (DRY Principle)

    Responsibilities:
    - Create consistent error responses for different failure scenarios
    - Preserve available data when possible (academic integrity)
    - Provide clear error messages and guidance
    - Build appropriate API health status

    Error Response Types:
    1. Empty Response: No data available at all
    2. Minimal Response: Carbon data only, no instances
    3. Auth Error Response: AWS authentication failed
    """

    def __init__(
        self,
        carbon_service: CarbonDataService,
        health_use_case: BuildAPIHealthStatusUseCase,
    ):
        """
        Initialize the use case with required services

        Args:
            carbon_service: Service for carbon data (used for cached time series)
            health_use_case: Use case for building API health status
        """
        self.carbon_service = carbon_service
        self.health_use_case = health_use_case

    def create_empty_response(self, error_message: str) -> DashboardData:
        """
        Create empty response structure for complete failure cases

        Used when:
        - No carbon data available
        - All APIs failed
        - Critical initialization errors

        Args:
            error_message: Description of what went wrong

        Returns:
            DashboardData with empty instances and fallback data
        """
        api_health_status = self.health_use_case.execute(
            carbon_available=False,
            cost_available=False,
            processed_instances=[],
            api_last_calls={},
            aws_auth_issue=False,
        )

        return DashboardData(
            instances=[],
            carbon_intensity=None,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=[error_message, "Academic integrity maintained - no fallback data used"],
            api_health_status=api_health_status,
            validation_factor=None,
            accuracy_status=None,
            cloudtrail_coverage=None,
            cloudtrail_tracked_instances=None,
        )

    def create_minimal_response(self, carbon_intensity: Optional[CarbonIntensity], error_message: str) -> DashboardData:
        """
        Create minimal response with available API data but no instances

        Used when:
        - Carbon data available but no EC2 instances found
        - Instance processing failed but APIs are working

        This preserves valuable API data for dashboard display.

        Args:
            carbon_intensity: Available carbon intensity data
            error_message: Description of what went wrong

        Returns:
            DashboardData with carbon data but empty instances
        """
        api_health_status = self.health_use_case.execute(
            carbon_available=carbon_intensity is not None,
            cost_available=False,
            processed_instances=[],
            api_last_calls={},
            aws_auth_issue=False,
        )

        return DashboardData(
            instances=[],
            carbon_intensity=carbon_intensity,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=[error_message, "Academic integrity maintained - preserving available API data"],
            api_health_status=api_health_status,
            validation_factor=None,
            accuracy_status=None,
            cloudtrail_coverage=None,
            cloudtrail_tracked_instances=None,
        )

    def create_auth_error_response(
        self, carbon_intensity: Optional[CarbonIntensity], error_message: str
    ) -> DashboardData:
        """
        Create response when AWS authentication is missing or expired

        Used when:
        - AWS SSO token expired
        - No AWS credentials configured
        - Insufficient AWS permissions

        Provides user guidance for fixing authentication issues.

        Args:
            carbon_intensity: Available carbon intensity data (if any)
            error_message: Authentication error description

        Returns:
            DashboardData with auth error and guidance
        """
        guidance = ErrorMessages.AWS_SSO_FIX

        api_health_status = self.health_use_case.execute(
            carbon_available=carbon_intensity is not None,
            cost_available=False,
            processed_instances=[],
            api_last_calls={},
            aws_auth_issue=True,
        )

        return DashboardData(
            instances=[],
            carbon_intensity=carbon_intensity,
            total_cost_eur=0.0,
            total_co2_kg=0.0,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=[error_message, guidance],
            api_health_status=api_health_status,
            validation_factor=None,
            accuracy_status=None,
            cloudtrail_coverage=None,
            cloudtrail_tracked_instances=None,
        )
