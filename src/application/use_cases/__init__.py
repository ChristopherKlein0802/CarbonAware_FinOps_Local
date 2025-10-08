"""
Application Use Cases

This package contains discrete use cases that implement specific business workflows.
Each use case is a single-responsibility class following Clean Architecture principles.
"""

from .enrich_instance import EnrichInstanceUseCase
from .fetch_infrastructure_data import FetchInfrastructureDataUseCase
from .build_api_health_status import BuildAPIHealthStatusUseCase
from .create_error_response import CreateErrorResponseUseCase

__all__ = [
    "EnrichInstanceUseCase",
    "FetchInfrastructureDataUseCase",
    "BuildAPIHealthStatusUseCase",
    "CreateErrorResponseUseCase",
]
