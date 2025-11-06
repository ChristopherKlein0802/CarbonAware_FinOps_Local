"""
Presentation Layer Utilities
"""

from .formatters import (
    get_period_label,
    safe_getattr_with_fallback,
    format_cost,
    format_co2,
    format_percentage,
    format_hours,
    get_calculation_method_label,
    validate_period_days,
    PERIOD_LABELS,
    CALCULATION_METHODS,
)

__all__ = [
    "get_period_label",
    "safe_getattr_with_fallback",
    "format_cost",
    "format_co2",
    "format_percentage",
    "format_hours",
    "get_calculation_method_label",
    "validate_period_days",
    "PERIOD_LABELS",
    "CALCULATION_METHODS",
]
