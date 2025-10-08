"""
Domain Services - Business logic and orchestration

This package contains domain services that implement business rules
and coordinate between infrastructure and application layers.

Following Clean Architecture principles, domain services depend on
protocols (interfaces) rather than concrete infrastructure implementations.
"""

from pathlib import Path
from typing import Optional

from src.config import settings
from src.domain.protocols import CacheRepository, InfrastructureGateway

from .runtime import RuntimeService, RuntimeServiceConfig
from .carbon import CarbonDataService, CarbonServiceConfig


def _default_repository() -> CacheRepository:
    """
    Create default cache repository.

    Note: This factory imports concrete implementation here to keep
    domain services decoupled. Only the factory knows about infrastructure.
    """
    from src.infrastructure.cache import FileCacheRepository

    return FileCacheRepository(Path(settings.cache_root))


def _default_gateway(repository: CacheRepository) -> InfrastructureGateway:
    """
    Create default infrastructure gateway.

    Note: This factory imports concrete implementation here to keep
    domain services decoupled. Only the factory knows about infrastructure.
    """
    from src.infrastructure.gateways import create_default_gateway

    return create_default_gateway(repository)


def create_runtime_service(
    config: Optional[RuntimeServiceConfig] = None,
    *,
    repository: Optional[CacheRepository] = None,
    gateway: Optional[InfrastructureGateway] = None,
) -> RuntimeService:
    """
    Build a runtime service instance with optional configuration override.

    Args:
        config: Optional service configuration
        repository: Optional cache repository (defaults to FileCacheRepository)
        gateway: Optional infrastructure gateway (defaults to composite gateway)

    Returns:
        Configured RuntimeService instance
    """
    repository = repository or _default_repository()
    gateway = gateway or _default_gateway(repository)
    return RuntimeService(
        config=config,
        repository=repository,
        gateway=gateway,
    )


def create_carbon_data_service(
    config: Optional[CarbonServiceConfig] = None,
    *,
    repository: Optional[CacheRepository] = None,
    gateway: Optional[InfrastructureGateway] = None,
) -> CarbonDataService:
    """
    Build a carbon data service instance with optional configuration override.

    Args:
        config: Optional service configuration
        repository: Optional cache repository (defaults to FileCacheRepository)
        gateway: Optional infrastructure gateway (defaults to composite gateway)

    Returns:
        Configured CarbonDataService instance
    """
    repository = repository or _default_repository()
    gateway = gateway or _default_gateway(repository)
    return CarbonDataService(
        config=config,
        repository=repository,
        gateway=gateway,
    )


__all__ = [
    "RuntimeService",
    "RuntimeServiceConfig",
    "CarbonDataService",
    "CarbonServiceConfig",
    "create_runtime_service",
    "create_carbon_data_service",
]
