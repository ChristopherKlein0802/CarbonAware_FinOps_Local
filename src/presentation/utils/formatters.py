"""
Presentation Layer Utility Functions
Centralized formatting and helper functions for UI components
"""

from typing import Any, Optional


def get_period_label(period_days: int, format_type: str = "long") -> str:
    """
    Get standardized period label for UI display.

    Args:
        period_days: Analysis period in days (1, 7, or 30)
        format_type: "long" (e.g., "7-day"), "short" (e.g., "7d"), or "title" (e.g., "Monthly")

    Returns:
        Formatted period label

    Examples:
        >>> get_period_label(1, "long")
        "1-day"
        >>> get_period_label(7, "short")
        "7d"
        >>> get_period_label(30, "title")
        "Monthly"
    """
    if format_type == "short":
        return f"{period_days}d" if period_days < 30 else "30d"
    elif format_type == "title":
        if period_days == 1:
            return "24-Hour"
        elif period_days == 7:
            return "7-Day"
        else:
            return "Monthly"
    else:  # long
        return f"{period_days}-day" if period_days < 30 else "monthly"


def safe_getattr_with_fallback(
    obj: Any,
    primary_field: str,
    fallback_field: Optional[str] = None,
    default: Any = None
) -> Any:
    """
    Safely get attribute from object with optional fallback and default.

    Args:
        obj: Object to get attribute from
        primary_field: Primary field name to retrieve
        fallback_field: Optional fallback field name if primary is None/missing
        default: Default value if both primary and fallback are None/missing

    Returns:
        Field value, fallback value, or default

    Examples:
        >>> safe_getattr_with_fallback(instance, "co2_kg_average", "monthly_co2_kg", 0.0)
        42.5  # Returns co2_kg_average if available
    """
    # Try primary field
    value = getattr(obj, primary_field, None)
    if value is not None:
        return value

    # Try fallback field
    if fallback_field:
        value = getattr(obj, fallback_field, None)
        if value is not None:
            return value

    # Return default
    return default


def format_cost(value: Optional[float], currency: str = "€", precision: int = 2) -> str:
    """
    Format cost value with currency symbol.

    Args:
        value: Cost value in EUR
        currency: Currency symbol (default: "€")
        precision: Decimal precision (default: 2)

    Returns:
        Formatted cost string or "N/A" if value is None

    Examples:
        >>> format_cost(42.567)
        "€42.57"
        >>> format_cost(None)
        "N/A"
    """
    if value is None:
        return "N/A"
    return f"{currency}{value:.{precision}f}"


def format_co2(value: Optional[float], precision: int = 3, unit: str = "kg") -> str:
    """
    Format CO2 value with unit.

    Args:
        value: CO2 value in kg
        precision: Decimal precision (default: 3)
        unit: Unit label (default: "kg")

    Returns:
        Formatted CO2 string or "N/A" if value is None

    Examples:
        >>> format_co2(1.2345)
        "1.235 kg"
        >>> format_co2(None)
        "N/A"
    """
    if value is None:
        return "N/A"
    return f"{value:.{precision}f} {unit}"


def format_percentage(value: Optional[float], precision: int = 1, with_sign: bool = False) -> str:
    """
    Format percentage value.

    Args:
        value: Percentage value (0-100 or 0.0-1.0 depending on context)
        precision: Decimal precision (default: 1)
        with_sign: Include + sign for positive values (default: False)

    Returns:
        Formatted percentage string or "N/A" if value is None

    Examples:
        >>> format_percentage(42.567)
        "42.6%"
        >>> format_percentage(5.0, with_sign=True)
        "+5.0%"
    """
    if value is None:
        return "N/A"

    sign = "+" if with_sign and value > 0 else ""
    return f"{sign}{value:.{precision}f}%"


def format_hours(hours: Optional[float], precision: int = 1) -> str:
    """
    Format runtime hours.

    Args:
        hours: Runtime in hours
        precision: Decimal precision (default: 1)

    Returns:
        Formatted hours string or "N/A" if value is None

    Examples:
        >>> format_hours(24.5)
        "24.5h"
        >>> format_hours(None)
        "N/A"
    """
    if hours is None:
        return "N/A"
    return f"{hours:.{precision}f}h"


def get_calculation_method_label(method: str, format_type: str = "full") -> str:
    """
    Get standardized label for calculation method.

    Args:
        method: Calculation method ("hourly", "average", or other)
        format_type: "full" (detailed), "short" (abbreviated), or "badge" (emoji + short)

    Returns:
        Formatted method label

    Examples:
        >>> get_calculation_method_label("hourly", "full")
        "24h-Pattern Based"
        >>> get_calculation_method_label("average", "badge")
        "📊 Average"
    """
    if method == "hourly":
        if format_type == "full":
            return "24h-Pattern Based"
        elif format_type == "badge":
            return "🔍 Hourly"
        else:  # short
            return "Hourly"
    elif method == "average":
        if format_type == "full":
            return "Average Runtime Based"
        elif format_type == "badge":
            return "📊 Average"
        else:  # short
            return "Average"
    else:
        return method.title()


def validate_period_days(period_days: int, default: int = 30) -> int:
    """
    Validate and sanitize period_days value.

    Args:
        period_days: Period in days to validate
        default: Default value if invalid (default: 30)

    Returns:
        Valid period_days (1, 7, or 30)

    Examples:
        >>> validate_period_days(7)
        7
        >>> validate_period_days(15)  # invalid
        30  # returns default
    """
    VALID_PERIODS = {1, 7, 30}
    return period_days if period_days in VALID_PERIODS else default


# Convenience constants for UI consistency
PERIOD_LABELS = {
    1: {"long": "1-day", "short": "1d", "title": "24-Hour"},
    7: {"long": "7-day", "short": "7d", "title": "7-Day"},
    30: {"long": "monthly", "short": "30d", "title": "Monthly"},
}

CALCULATION_METHODS = {
    "hourly": {
        "full": "24h-Pattern Based",
        "short": "Hourly",
        "badge": "🔍 Hourly",
        "description": "Uses 24h carbon intensity patterns scaled to analysis period"
    },
    "average": {
        "full": "Average Runtime Based",
        "short": "Average",
        "badge": "📊 Average",
        "description": "Uses period-average carbon intensity × actual runtime hours"
    }
}
