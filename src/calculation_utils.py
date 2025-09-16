"""
Calculation Utilities Module
Academic-grade calculation functions for carbon and cost analysis

This module contains reusable calculation functions that support
the Carbon-Aware FinOps dashboard's business logic with transparent
academic methodology.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def safe_round(value, decimals=2):
    """Safe rounding function that handles None values"""
    if value is None:
        return None
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return None


def calculate_simple_power_consumption(base_power_watts: float, cpu_utilization: float) -> float:
    """Calculate power consumption using simple linear scaling

    Academic approach: Transparent linear model instead of complex formulas
    Formula: Power = Base × (1 + CPU/100)

    Args:
        base_power_watts: Base power consumption of the instance type
        cpu_utilization: CPU utilization percentage (0-100)

    Returns:
        Effective power consumption in watts
    """
    # Input validation with safe defaults
    safe_base_power = max(base_power_watts, 0.1)  # Minimum 0.1W
    safe_cpu_utilization = min(max(cpu_utilization, 0), 100)  # Clamp 0-100%

    # Simple linear scaling - academically defensible
    utilization_factor = 1.0 + (safe_cpu_utilization / 100.0)
    effective_power_watts = safe_base_power * utilization_factor

    logger.debug(f"Power calculation: {safe_base_power}W × {utilization_factor:.2f} = {effective_power_watts:.1f}W")

    return effective_power_watts


def calculate_co2_emissions(power_watts: float, carbon_intensity_g_per_kwh: float, runtime_hours: float) -> float:
    """Calculate CO2 emissions from power consumption and grid intensity

    Academic formula: CO2 = Power(kW) × Grid_Intensity(g/kWh) × Runtime(h) / 1000(g->kg)

    Args:
        power_watts: Power consumption in watts
        carbon_intensity_g_per_kwh: Grid carbon intensity in g CO2/kWh
        runtime_hours: Runtime in hours

    Returns:
        CO2 emissions in kg
    """
    if not all([power_watts, carbon_intensity_g_per_kwh, runtime_hours]):
        return 0.0

    power_kw = power_watts / 1000.0  # Convert W to kW
    co2_g = power_kw * carbon_intensity_g_per_kwh * runtime_hours
    co2_kg = co2_g / 1000.0  # Convert g to kg

    logger.debug(f"CO2 calculation: {power_kw:.3f}kW × {carbon_intensity_g_per_kwh:.0f}g/kWh × {runtime_hours:.1f}h = {co2_kg:.3f}kg")

    return safe_round(co2_kg, 3)


def calculate_monthly_cost(hourly_price_usd: float, runtime_hours: float, eur_usd_rate: float = 0.92) -> float:
    """Calculate monthly cost with currency conversion

    Academic transparency: Simple multiplication with clear currency conversion

    Args:
        hourly_price_usd: AWS pricing in USD per hour
        runtime_hours: Actual runtime in hours (from CloudTrail or estimates)
        eur_usd_rate: EUR/USD exchange rate

    Returns:
        Monthly cost in EUR
    """
    if not all([hourly_price_usd, runtime_hours]):
        return 0.0

    monthly_cost_usd = hourly_price_usd * runtime_hours
    monthly_cost_eur = monthly_cost_usd * eur_usd_rate

    logger.debug(f"Cost calculation: ${hourly_price_usd:.4f}/h × {runtime_hours:.1f}h × {eur_usd_rate} = €{monthly_cost_eur:.2f}")

    return safe_round(monthly_cost_eur, 2)


def calculate_scenario_savings(baseline_cost_eur: float, scenario_factor: float) -> float:
    """Calculate potential savings for optimization scenarios

    Academic approach: Simple percentage-based scenarios for sensitivity analysis

    Args:
        baseline_cost_eur: Baseline monthly cost in EUR
        scenario_factor: Optimization factor (e.g., 0.10 for 10% savings)

    Returns:
        Potential savings in EUR
    """
    if not baseline_cost_eur or scenario_factor <= 0:
        return 0.0

    savings_eur = baseline_cost_eur * scenario_factor

    logger.debug(f"Scenario calculation: €{baseline_cost_eur:.2f} × {scenario_factor:.1%} = €{savings_eur:.2f} savings")

    return safe_round(savings_eur, 2)


def calculate_confidence_score(*factors) -> float:
    """Calculate weighted confidence score from multiple factors

    Uses geometric mean to prevent any single factor from dominating

    Args:
        *factors: Individual confidence factors (0.0 to 1.0)

    Returns:
        Overall confidence score (0.0 to 1.0)
    """
    if not factors:
        return 0.0

    valid_factors = [f for f in factors if f > 0]
    if not valid_factors:
        return 0.0

    # Geometric mean for balanced confidence assessment
    product = 1.0
    for factor in valid_factors:
        product *= factor

    confidence = product ** (1.0 / len(valid_factors))

    logger.debug(f"Confidence calculation: Geometric mean of {len(valid_factors)} factors = {confidence:.1%}")

    return safe_round(confidence, 3)


def validate_calculation_inputs(**kwargs) -> bool:
    """Validate calculation inputs for academic integrity

    Returns False if any critical inputs are missing or invalid
    """
    required_numeric = ['power_watts', 'runtime_hours', 'carbon_intensity']

    for key, value in kwargs.items():
        if key in required_numeric:
            if value is None or value < 0:
                logger.warning(f"Invalid calculation input: {key}={value}")
                return False

    return True