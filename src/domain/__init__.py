"""
Domain Layer - Business logic, models, and domain services

This package contains all domain-specific code:
- models: Domain entities (EC2Instance, CarbonIntensity, BusinessCase, etc.)
- calculations: Core mathematical functions (power, CO2, costs)
- validation: Data quality and plausibility checks
- errors: Domain-specific exceptions
- constants: Academic and business constants
- services: Domain services (runtime, carbon analysis)
"""

# Core domain models
from .models import (
    EC2Instance,
    AWSCostData,
    CarbonIntensity,
    PowerConsumption,
    BusinessCase,
    TimeSeriesPoint,
    APIHealthStatus,
    DashboardData,
)

# Domain calculations
from .calculations import (
    safe_round,
    calculate_simple_power_consumption,
    calculate_co2_emissions,
)

# Domain validation
from .validation import (
    validate_instance_data,
    validate_dashboard_data,
    get_data_quality_score,
)

# Domain errors
from .errors import (
    ErrorMessages,
    AWSAuthenticationError,
)

# Domain constants
from .constants import (
    AcademicConstants,
    CarbonConstants,
    UIConstants,
)

__all__ = [
    # Models
    "EC2Instance",
    "AWSCostData",
    "CarbonIntensity",
    "PowerConsumption",
    "BusinessCase",
    "TimeSeriesPoint",
    "APIHealthStatus",
    "DashboardData",
    # Calculations
    "safe_round",
    "calculate_simple_power_consumption",
    "calculate_co2_emissions",
    # Validation
    "validate_instance_data",
    "validate_dashboard_data",
    "get_data_quality_score",
    # Errors
    "ErrorMessages",
    "AWSAuthenticationError",
    # Constants
    "AcademicConstants",
    "CarbonConstants",
    "UIConstants",
]
