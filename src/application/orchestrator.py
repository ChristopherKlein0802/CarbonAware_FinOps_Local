"""
Dashboard Data Orchestrator

Main orchestrator for the Carbon-Aware FinOps Dashboard.
Acts as a coordinator that delegates business logic to specialized use cases.

Pattern: Dependency Inversion
- Orchestrator depends on domain protocols
- Use cases handle single-responsibility workflows
- Centralized error handling
"""

import logging
from typing import Optional
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    SSOError,
    TokenRetrievalError,
    UnauthorizedSSOTokenError,
)

from src.config import settings
from src.domain.errors import AWSAuthenticationError, ErrorMessages
from src.domain.models import DashboardData
from src.application.calculator import BusinessCaseCalculator
from src.domain.services import (
    RuntimeService,
    CarbonDataService,
    create_runtime_service,
    create_carbon_data_service,
)
from src.infrastructure.cache import FileCacheRepository
from src.infrastructure.gateways import InfrastructureGateway, create_default_gateway

# Import all use cases
from src.application.use_cases import (
    FetchInfrastructureDataUseCase,
    BuildAPIHealthStatusUseCase,
    CreateErrorResponseUseCase,
)

logger = logging.getLogger(__name__)


class DashboardDataOrchestrator:
    """
    Dashboard Data Orchestrator

    Coordinates data fetching workflow via use cases.
    Handles error scenarios and service initialization.
    """

    def __init__(
        self,
        *,
        runtime_service: Optional[RuntimeService] = None,
        carbon_service: Optional[CarbonDataService] = None,
        calculator: Optional[BusinessCaseCalculator] = None,
        repository: Optional[FileCacheRepository] = None,
        gateway: Optional[InfrastructureGateway] = None,
    ):
        """
        Initialize orchestrator with dependency injection.

        All dependencies are optional and auto-created with defaults.
        Accepts protocols for easy testing and flexibility.

        Args:
            runtime_service: EC2/CloudTrail operations
            carbon_service: Carbon intensity data
            calculator: Scenario calculations
            repository: Cache repository
            gateway: Infrastructure gateway
        """

        # Initialize infrastructure dependencies
        self.repository = repository or FileCacheRepository(settings.cache_root)
        self.gateway = gateway or create_default_gateway(self.repository)

        # Initialize domain services
        self.runtime_service = runtime_service or create_runtime_service(
            repository=self.repository,
            gateway=self.gateway,
        )
        self.carbon_service = carbon_service or create_carbon_data_service(
            repository=self.repository,
            gateway=self.gateway,
        )
        self.calculator = calculator or BusinessCaseCalculator()

        # Initialize use cases
        self.fetch_use_case = FetchInfrastructureDataUseCase(
            runtime_service=self.runtime_service,
            carbon_service=self.carbon_service,
            calculator=self.calculator,
            gateway=self.gateway,
            repository=self.repository,
        )

        self.health_use_case = BuildAPIHealthStatusUseCase()

        self.error_use_case = CreateErrorResponseUseCase(
            carbon_service=self.carbon_service,
            health_use_case=self.health_use_case,
        )

        logger.info("Dashboard Data Orchestrator initialized")

    def get_infrastructure_data(self, *, force_refresh: bool = False) -> Optional[DashboardData]:
        """
        Get infrastructure data - delegates to use cases.

        Coordinates happy path and error handling via specialized use cases.

        Args:
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            DashboardData with infrastructure metrics or error response
        """
        carbon_intensity = None

        try:
            # Happy path: delegate to fetch use case
            dashboard_data = self.fetch_use_case.execute(force_refresh=force_refresh)

            # Enrich with API health status
            api_health_status = self.health_use_case.execute(
                carbon_available=dashboard_data.carbon_intensity is not None,
                cost_available=dashboard_data.total_cost_eur > 0,
                processed_instances=dashboard_data.instances,
                api_last_calls=self.fetch_use_case.api_last_calls,
                aws_auth_issue=False,
            )
            dashboard_data.api_health_status = api_health_status

            logger.info(f"Infrastructure analysis complete: {len(dashboard_data.instances)} instances")
            return dashboard_data

        except ValueError as e:
            # Data validation errors or missing data
            error_message = str(e)
            logger.warning(f"Data validation error: {error_message}")

            # Try to preserve carbon intensity if available
            try:
                carbon_intensity = self.carbon_service.get_current_intensity(region="eu-central-1")
            except Exception:
                pass

            if carbon_intensity:
                return self.error_use_case.create_minimal_response(carbon_intensity, error_message)
            else:
                return self.error_use_case.create_empty_response(error_message)

        except (
            NoCredentialsError,
            SSOError,
            UnauthorizedSSOTokenError,
            TokenRetrievalError,
            AWSAuthenticationError,
        ) as auth_error:
            # AWS authentication errors
            logger.error("AWS authentication error: %s", auth_error)

            # Try to preserve carbon intensity
            try:
                carbon_intensity = self.carbon_service.get_current_intensity(region="eu-central-1")
            except Exception:
                pass

            return self.error_use_case.create_auth_error_response(carbon_intensity, ErrorMessages.AWS_SSO_EXPIRED)

        except ClientError as client_error:
            # AWS client errors
            logger.error("AWS client error: %s", client_error)
            message = (
                client_error.response.get("Error", {}).get("Message")
                if hasattr(client_error, "response")
                else str(client_error)
            )

            # Try to preserve carbon intensity
            try:
                carbon_intensity = self.carbon_service.get_current_intensity(region="eu-central-1")
            except Exception:
                pass

            return self.error_use_case.create_minimal_response(carbon_intensity, message or "AWS client error occurred")

        except (TypeError, KeyError) as e:
            # Data type/structure errors
            logger.error(f"Data type error: {e}")
            return self.error_use_case.create_empty_response(f"Data type error: {str(e)}")

        except (AttributeError, ImportError) as e:
            # Module/attribute errors
            logger.error(f"Module/attribute error: {e}", exc_info=True)
            return self.error_use_case.create_empty_response(f"Module error: {str(e)}")

        except (ConnectionError, TimeoutError) as e:
            # Network/API errors
            logger.error(f"Network/API error: {e}")
            return self.error_use_case.create_empty_response(f"Network error: {str(e)}")

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return self.error_use_case.create_empty_response(f"Unexpected error: {str(e)}")

    # All specialized functionality now properly delegated to use cases:
    # - FetchInfrastructureDataUseCase: Main workflow
    # - EnrichInstanceUseCase: Single instance enrichment
    # - BuildAPIHealthStatusUseCase: API health monitoring
    # - CreateErrorResponseUseCase: Error response factory
    # - BusinessCaseCalculator: Business case calculations
    # - RuntimeService: EC2 collection, runtime calculation, instance enrichment
    # - CarbonDataService: Carbon intensity queries and time-series management
