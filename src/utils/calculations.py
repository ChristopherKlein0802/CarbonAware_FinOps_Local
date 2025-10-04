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


def safe_round(value: Optional[float], decimals: int = 2) -> Optional[float]:
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
    Formula: Power = Base × (0.3 + 0.7 × CPU/100)

    **BACHELOR THESIS DOCUMENTATION:**
    This simplified linear power model is based on literature showing that server power consumption
    scales approximately linearly with CPU utilization between idle and peak states.

    **ACADEMIC JUSTIFICATION:**
    - Idle power consumption: ~30% of peak power (industry standard)
    - Variable power consumption: ~70% of peak power (scales with CPU)
    - Sources: Barroso & Hölzle (2007), Koomey et al. (2011), SPECpower benchmarks

    **MODEL LIMITATIONS:**
    - Simplified linear model (actual relationship may be slightly non-linear)
    - Does not account for memory, disk, or network utilization
    - Conservative approach for thesis methodology demonstration

    **FORMULA VALIDATION:**
    - At 0% CPU: Power = Base × 0.3 (30% idle power)
    - At 50% CPU: Power = Base × 0.65 (65% of peak power)
    - At 100% CPU: Power = Base × 1.0 (100% peak power)

    Args:
        base_power_watts: Base power consumption of the instance type (from Boavizta)
        cpu_utilization: CPU utilization percentage 0-100 (from CloudWatch)

    Returns:
        Effective power consumption in watts (utilization-adjusted)
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
    """Calculate CO2 emissions from power consumption and grid intensity

    Academic formula: CO2 = Power(kW) × Grid_Intensity(g/kWh) × Runtime(h) / 1000(g->kg)

    **BACHELOR THESIS DOCUMENTATION:**
    This calculation follows the internationally accepted standard for computing carbon emissions
    from electricity consumption. The formula is based on the IEA methodology and is consistent
    with academic literature on carbon accounting (e.g., Carbonfund.org, EPA guidelines).

    **UNIT ANALYSIS:**
    - Input: power_watts [W], carbon_intensity [g CO2/kWh], runtime_hours [h]
    - Step 1: power_watts / 1000 = power_kw [kW]
    - Step 2: power_kw × carbon_intensity = co2_g [g CO2]
    - Step 3: co2_g / 1000 = co2_kg [kg CO2]
    - Result: co2_kg [kg CO2]

    **VALIDATION:**
    - Example: 100W × 300g/kWh × 730h = 0.1kW × 300g/kWh × 730h = 21,900g = 21.9kg CO2
    - This matches expected industrial calculations for server carbon footprints

    Args:
        power_watts: Power consumption in watts (from Boavizta API)
        carbon_intensity_g_per_kwh: Grid carbon intensity in g CO2/kWh (from ElectricityMaps)
        runtime_hours: Runtime in hours (from CloudTrail precision tracking)

    Returns:
        CO2 emissions in kg (monthly footprint)
    """
    if not all([power_watts, carbon_intensity_g_per_kwh, runtime_hours]):
        return 0.0

    power_kw = power_watts / 1000.0  # Convert W to kW
    co2_g = power_kw * carbon_intensity_g_per_kwh * runtime_hours
    co2_kg = co2_g / 1000.0  # Convert g to kg

    logger.debug(f"CO2 calculation: {power_kw:.3f}kW × {carbon_intensity_g_per_kwh:.0f}g/kWh × {runtime_hours:.1f}h = {co2_kg:.3f}kg")

    return safe_round(co2_kg, 3)


__all__ = [
    "safe_round",
    "calculate_simple_power_consumption",
    "calculate_co2_emissions",
]
