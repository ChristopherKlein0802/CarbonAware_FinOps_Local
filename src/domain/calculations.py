"""
Domain Calculations - Core calculation logic for carbon and cost analysis

Scientific calculation functions for the Carbon-Aware FinOps dashboard.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def safe_round(value: Optional[float], decimals: int = 2) -> Optional[float]:
    """Safe rounding function that handles None values"""
    if value is None:
        return None
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return None


def calculate_simple_power_consumption(base_power_watts: float, cpu_utilization: float) -> float:
    """Calculate power consumption using linear scaling.

    Formula: Power = Base × (0.3 + 0.7 × CPU/100)

    Assumptions:
    - Idle power: 30% of peak power
    - Variable power: 70% of peak power (scales with CPU)
    - Linear relationship between CPU and power

    Args:
        base_power_watts: Base power consumption from Boavizta
        cpu_utilization: CPU utilization 0-100% from CloudWatch

    Returns:
        Effective power consumption in watts
    """
    # Input validation with safe defaults
    safe_base_power = max(base_power_watts, 0.1)  # Minimum 0.1W
    safe_cpu_utilization = min(max(cpu_utilization, 0), 100)  # Clamp 0-100%

    # Simple linear scaling - academically defensible
    # Formula: Power = Base × (0.3 + 0.7 × CPU/100)
    utilization_factor = 0.3 + 0.7 * (safe_cpu_utilization / 100.0)
    effective_power_watts = safe_base_power * utilization_factor

    logger.debug(f"Power calculation: {safe_base_power}W × {utilization_factor:.2f} = {effective_power_watts:.1f}W")

    return effective_power_watts


def calculate_co2_emissions(power_watts: float, carbon_intensity_g_per_kwh: float, runtime_hours: float) -> float:
    """Calculate CO2 emissions from power and grid intensity.

    Formula: CO2(kg) = Power(kW) × Grid_Intensity(g/kWh) × Runtime(h) / 1000

    Args:
        power_watts: Power consumption in watts
        carbon_intensity_g_per_kwh: Grid carbon intensity (g CO2/kWh)
        runtime_hours: Runtime in hours

    Returns:
        CO2 emissions in kg
    """
    if not all([power_watts, carbon_intensity_g_per_kwh, runtime_hours]):
        return 0.0

    power_kw = power_watts / 1000.0  # Convert W to kW
    co2_g = power_kw * carbon_intensity_g_per_kwh * runtime_hours
    co2_kg = co2_g / 1000.0  # Convert g to kg

    logger.debug(
        f"CO2 calculation: {power_kw:.3f}kW × {carbon_intensity_g_per_kwh:.0f}g/kWh × {runtime_hours:.1f}h = {co2_kg:.3f}kg"
    )

    return safe_round(co2_kg, 3)


__all__ = [
    "safe_round",
    "calculate_simple_power_consumption",
    "calculate_co2_emissions",
]
