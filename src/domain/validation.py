"""
Domain Validation - Data quality and plausibility checks

This module provides validation functions for ensuring academic integrity
and data quality across the Carbon-Aware FinOps dashboard. All validation
rules are based on industry standards and conservative plausibility bounds.
"""

import logging
from typing import List, Dict, Any
from .models import EC2Instance

logger = logging.getLogger(__name__)


def validate_instance_data(instance: EC2Instance) -> Dict[str, Any]:
    """Validate instance data for plausibility and academic integrity

    Returns:
        Dict with validation results and warnings
    """
    warnings = []
    errors = []

    # Runtime validation
    if instance.runtime_hours is not None:
        if instance.runtime_hours > 744:  # Max hours in a month (31 days * 24h)
            warnings.append(f"Runtime {instance.runtime_hours:.1f}h exceeds monthly maximum (744h)")
        elif instance.runtime_hours <= 0:
            errors.append(f"Invalid runtime: {instance.runtime_hours:.1f}h")

    # Cost validation
    if instance.hourly_price_usd is not None:
        if instance.hourly_price_usd > 50.0:
            warnings.append(f"Hourly price ${instance.hourly_price_usd:.3f} seems unusually high")
        elif instance.hourly_price_usd < 0.001:
            warnings.append(f"Hourly price ${instance.hourly_price_usd:.3f} seems unusually low")

    # CO2 validation (use period-agnostic field with fallback)
    co2_value = getattr(instance, "co2_kg_average", None)
    if co2_value is None and hasattr(instance, "monthly_co2_kg"):
        co2_value = instance.monthly_co2_kg  # Fallback for backward compatibility

    if co2_value is not None:
        if co2_value > 1000:  # 1 tonne per instance per period
            warnings.append(f"CO₂ emissions {co2_value:.1f}kg seem very high for single instance")
        elif co2_value < 0:
            errors.append(f"Invalid CO₂ emissions: {co2_value:.1f}kg")

    # Power validation
    if instance.power_watts is not None:
        if instance.power_watts > 1000:  # 1kW for single instance
            warnings.append(f"Power consumption {instance.power_watts:.0f}W seems very high")
        elif instance.power_watts <= 0:
            errors.append(f"Invalid power consumption: {instance.power_watts:.0f}W")

    return {
        "instance_id": instance.instance_id,
        "warnings": warnings,
        "errors": errors,
        "is_valid": len(errors) == 0,
        "has_warnings": len(warnings) > 0,
    }


def validate_dashboard_data(instances: List[EC2Instance]) -> Dict[str, Any]:
    """Validate complete dashboard data set

    Returns:
        Summary of validation results across all instances
    """
    total_instances = len(instances)
    validation_results = [validate_instance_data(instance) for instance in instances]

    valid_instances = len([r for r in validation_results if r["is_valid"]])
    instances_with_warnings = len([r for r in validation_results if r["has_warnings"]])

    all_warnings = []
    all_errors = []

    for result in validation_results:
        all_warnings.extend(result["warnings"])
        all_errors.extend(result["errors"])

    return {
        "total_instances": total_instances,
        "valid_instances": valid_instances,
        "instances_with_warnings": instances_with_warnings,
        "total_warnings": len(all_warnings),
        "total_errors": len(all_errors),
        "validation_results": validation_results,
        "summary_warnings": all_warnings[:5],  # First 5 warnings for display
        "summary_errors": all_errors[:5],  # First 5 errors for display
    }


def get_data_quality_score(instances: List[EC2Instance]) -> float:
    """Calculate overall data quality score (0.0 to 1.0)

    Based on:
    - Presence of measured vs estimated data
    - Data completeness
    - Validation results
    """
    if not instances:
        return 0.0

    quality_points = 0
    max_points = 0

    for instance in instances:
        max_points += 5  # 5 points per instance

        # Runtime data quality
        if hasattr(instance, "runtime_hours") and instance.runtime_hours is not None:
            quality_points += 1
            if hasattr(instance, "data_quality") and instance.data_quality == "measured":
                quality_points += 1

        # Pricing data quality
        if hasattr(instance, "hourly_price_usd") and instance.hourly_price_usd is not None:
            quality_points += 1

        # CO2 calculation completeness (use period-agnostic field with fallback)
        co2_value = getattr(instance, "co2_kg_average", None)
        if co2_value is None and hasattr(instance, "monthly_co2_kg"):
            co2_value = instance.monthly_co2_kg  # Fallback for backward compatibility

        if co2_value is not None and co2_value > 0:
            quality_points += 1

        # Power calculation completeness
        if instance.power_watts is not None and instance.power_watts > 0:
            quality_points += 1

    return quality_points / max_points if max_points > 0 else 0.0


__all__ = [
    "validate_instance_data",
    "validate_dashboard_data",
    "get_data_quality_score",
]
