"""
Domain Calculations - Core calculation logic for carbon and cost analysis

Scientific calculation functions for the Carbon-Aware FinOps dashboard.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

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


def calculate_co2_hourly_precise(
    base_power_watts: float,
    cpu_values_hourly: List[float],
    carbon_intensity_hourly: List[float],
    runtime_hours_per_slot: List[float],
    timestamps: List[datetime],
    hourly_price_usd: Optional[float] = None,
    eur_usd_rate: float = 0.92,
) -> Dict[str, Any]:
    """
    Calculate CO2 emissions and costs with hourly precision for 24h window.

    This function calculates CO2 emissions and costs with hourly granularity by using:
    - Hourly CPU utilization data from CloudWatch
    - Hourly carbon intensity data from ElectricityMaps
    - Hourly runtime fractions from CloudTrail events
    - Hourly pricing from AWS Pricing API

    Formula for each hour h:
        Power_h = Base × (0.3 + 0.7 × CPU_h/100)
        CO2_h = (Power_h / 1000) × Carbon_h × Runtime_h
        Cost_h = HourlyPrice_USD × Runtime_h × EUR_USD_Rate

    Total: Sum over all hours

    Args:
        base_power_watts: Base power consumption from Boavizta (constant)
        cpu_values_hourly: List of CPU % values (one per hour, up to 24)
        carbon_intensity_hourly: List of carbon intensity g/kWh (one per hour)
        runtime_hours_per_slot: List of runtime fractions (0.0-1.0) per hour
        timestamps: List of datetime objects for each hour
        hourly_price_usd: Optional hourly price in USD (for cost calculation)
        eur_usd_rate: EUR/USD exchange rate (default: 0.92)

    Returns:
        Dictionary containing (NOTE: These are dict keys, not model field names):
        - total_co2_kg: Total CO2 emissions in kg (sum of all hours)
        - total_cost_eur: Total cost in EUR (sum of all hours, if price provided)
        - hourly_emissions: List of detailed hourly breakdowns (includes cost_eur if price provided)
        - data_quality: 'high' (≥20h), 'medium' (≥12h), or 'low' (<12h)
        - coverage_hours: Number of hours with valid data
        - method: Always 'hourly_24h_precise'

        Note: Dictionary keys differ from DashboardData model fields. Model uses:
        total_co2_average, total_cost_average, total_co2_hourly, total_cost_hourly

    Example:
        Hour 0 (23h ago): CPU=35%, Carbon=280g/kWh, Runtime=1.0h, Price=$0.042/h
            Power = 15W × (0.3 + 0.7×0.35) = 8.175W
            CO2 = 0.008175kW × 280g × 1.0h = 2.289g
            Cost = $0.042 × 1.0h × 0.92 = €0.0386

        Hour 1 (22h ago): CPU=45%, Carbon=320g/kWh, Runtime=1.0h
            Power = 15W × (0.3 + 0.7×0.45) = 9.225W
            CO2 = 0.009225kW × 320g × 1.0h = 2.952g
            Cost = $0.042 × 1.0h × 0.92 = €0.0386

        Total: Sum of all 24 hours
    """
    hourly_emissions = []
    total_co2_g = 0.0
    total_cost_eur = 0.0
    hours_with_data = 0

    # Ensure all lists have compatible lengths
    num_hours = min(
        len(cpu_values_hourly),
        len(carbon_intensity_hourly),
        len(runtime_hours_per_slot),
        len(timestamps),
    )

    if num_hours == 0:
        logger.warning("No hourly data available for CO2 calculation")
        return {
            "total_co2_kg": 0.0,
            "total_cost_eur": 0.0,
            "hourly_emissions": [],
            "data_quality": "low",
            "coverage_hours": 0,
            "method": "hourly",
        }

    logger.info(f"Calculating hourly CO2 for {num_hours} hours")

    for i in range(num_hours):
        cpu = cpu_values_hourly[i]
        carbon = carbon_intensity_hourly[i]
        runtime = runtime_hours_per_slot[i]
        timestamp = timestamps[i]

        # Skip if instance wasn't running this hour
        if runtime == 0.0:
            emission_data = {
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                "co2_g": 0.0,
                "running": False,
            }
            # Add cost if pricing available
            if hourly_price_usd is not None:
                emission_data["cost_eur"] = 0.0
            hourly_emissions.append(emission_data)
            continue

        # Calculate effective power for this hour
        power_watts = calculate_simple_power_consumption(base_power_watts, cpu)

        # Calculate CO2 for this hour
        # Formula: CO2(g) = Power(kW) × Carbon(g/kWh) × Runtime(h)
        power_kw = power_watts / 1000.0
        co2_g = power_kw * carbon * runtime

        # Calculate cost for this hour (if pricing available)
        # Formula: Cost(EUR) = HourlyPrice(USD) × Runtime(h) × EUR_USD_Rate
        cost_eur = 0.0
        if hourly_price_usd is not None:
            cost_eur = hourly_price_usd * runtime * eur_usd_rate
            total_cost_eur += cost_eur

        total_co2_g += co2_g
        hours_with_data += 1

        emission_data = {
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "co2_g": round(co2_g, 3),
            "power_watts": round(power_watts, 2),
            "cpu_percent": round(cpu, 1),
            "carbon_intensity": round(carbon, 1),
            "runtime_fraction": round(runtime, 2),
            "running": True,
        }

        # Add cost if pricing available
        if hourly_price_usd is not None:
            emission_data["cost_eur"] = round(cost_eur, 4)

        hourly_emissions.append(emission_data)

        logger.debug(
            f"Hour {i}: {power_kw:.4f}kW × {carbon:.0f}g/kWh × {runtime:.2f}h = {co2_g:.3f}g "
            f"(CPU={cpu:.1f}%, Power={power_watts:.1f}W)"
        )

    # Calculate data quality based on coverage
    if hours_with_data >= 20:
        data_quality = "high"
    elif hours_with_data >= 12:
        data_quality = "medium"
    else:
        data_quality = "low"

    total_co2_kg = total_co2_g / 1000.0

    if hourly_price_usd is not None:
        logger.info(
            f"✅ Hourly CO2 & Cost calculation complete: {total_co2_kg:.6f} kg, €{total_cost_eur:.4f} "
            f"({hours_with_data}/{num_hours} hours, quality={data_quality})"
        )
    else:
        logger.info(
            f"✅ Hourly CO2 calculation complete: {total_co2_kg:.6f} kg "
            f"({hours_with_data}/{num_hours} hours, quality={data_quality})"
        )

    return {
        "total_co2_kg": round(total_co2_kg, 6),
        "total_cost_eur": round(total_cost_eur, 4),
        "hourly_emissions": hourly_emissions,
        "data_quality": data_quality,
        "coverage_hours": hours_with_data,
        "method": "hourly",
    }


__all__ = [
    "safe_round",
    "calculate_simple_power_consumption",
    "calculate_co2_emissions",
    "calculate_co2_hourly_precise",
]
