"""Domain services and factory helpers for the Carbon-Aware FinOps dashboard."""

from pathlib import Path
from typing import Optional

from ..config import settings
from ..core.calculator import BusinessCaseCalculator
from ..infrastructure.cache import FileCacheRepository
from ..infrastructure.clients import InfrastructureGateway, create_default_gateway
from ..infrastructure.clients.aws_runtime import AWSRuntimeGateway
from .business import BusinessInsightsService
from .carbon import CarbonDataService, CarbonServiceConfig
from .runtime import RuntimeService, RuntimeServiceConfig


def _default_repository() -> FileCacheRepository:
    return FileCacheRepository(Path(settings.cache_root))


def _default_gateway(repository: FileCacheRepository) -> InfrastructureGateway:
    return create_default_gateway(repository)


def _default_runtime_gateway() -> AWSRuntimeGateway:
    return AWSRuntimeGateway(profile=settings.aws_profile)


def create_runtime_service(
    config: Optional[RuntimeServiceConfig] = None,
    *,
    repository: Optional[FileCacheRepository] = None,
    gateway: Optional[InfrastructureGateway] = None,
    runtime_gateway: Optional[AWSRuntimeGateway] = None,
) -> RuntimeService:
    """Build a runtime service instance with optional configuration override."""

    repository = repository or _default_repository()
    gateway = gateway or _default_gateway(repository)
    runtime_gateway = runtime_gateway or _default_runtime_gateway()
    return RuntimeService(
        config=config,
        repository=repository,
        infrastructure_gateway=gateway,
        runtime_gateway=runtime_gateway,
    )


def create_carbon_data_service(
    config: Optional[CarbonServiceConfig] = None,
    *,
    repository: Optional[FileCacheRepository] = None,
    gateway: Optional[InfrastructureGateway] = None,
) -> CarbonDataService:
    """Build a carbon data service instance with optional configuration override."""

    repository = repository or _default_repository()
    gateway = gateway or _default_gateway(repository)
    return CarbonDataService(
        config=config,
        repository=repository,
        gateway=gateway,
    )


def create_business_insights_service(
    calculator: Optional[BusinessCaseCalculator] = None,
) -> BusinessInsightsService:
    """Build a business insights service with an optional calculator instance."""

    return BusinessInsightsService(calculator=calculator)


__all__ = [
    "RuntimeService",
    "RuntimeServiceConfig",
    "CarbonDataService",
    "CarbonServiceConfig",
    "BusinessInsightsService",
    "create_runtime_service",
    "create_carbon_data_service",
    "create_business_insights_service",
]
