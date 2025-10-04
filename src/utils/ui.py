"""
Utility functions for dashboard pages
Clean separation of calculations and data processing logic
"""

from typing import Dict, Any, Tuple
from src.constants import (
    AcademicConstants,
    CarbonConstants,
)

def determine_grid_status(grid_intensity: float) -> Tuple[str, str, str]:
    """Determine grid status and recommendations from carbon intensity"""
    if grid_intensity < CarbonConstants.OPTIMAL_THRESHOLD:
        return "🟢", "EXCELLENT (High Solar/Wind)", "⚡ OPTIMAL TIME: Run energy-intensive workloads NOW"
    elif grid_intensity < CarbonConstants.MODERATE_THRESHOLD:
        return "🟡", "MODERATE (Mixed Sources)", "⏱️ CONSIDER: Delay non-urgent workloads for 2-4 hours"
    else:
        return "🔴", "HIGH CARBON (Coal Peak)", "🚨 AVOID: Postpone batch jobs until grid improves"


def calculate_weighted_tradeoff(baseline_cost: float, baseline_co2: float, cost_weight: int) -> Dict[str, Any]:
    """Compute cost/CO₂ savings based on user-defined weighting."""

    clamped_weight = min(max(cost_weight, 0), 100)
    cost_priority = clamped_weight / 100.0
    carbon_priority = 1.0 - cost_priority

    aggressive_factor = AcademicConstants.MODERATE_SCENARIO_FACTOR  # 20%
    conservative_factor = AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR  # 10%

    cost_reduction_factor = (cost_priority * aggressive_factor) + (carbon_priority * conservative_factor)
    co2_reduction_factor = (carbon_priority * aggressive_factor) + (cost_priority * conservative_factor)

    cost_reduction = baseline_cost * cost_reduction_factor if baseline_cost else 0.0
    co2_reduction = baseline_co2 * co2_reduction_factor if baseline_co2 else 0.0

    summary = (
        f"{clamped_weight}% Kostenfokus → {cost_reduction_factor:.1%} Kostensenkung, "
        f"{co2_reduction_factor:.1%} CO₂-Reduktion"
    )

    return {
        "cost_reduction": cost_reduction,
        "co2_reduction": co2_reduction,
        "cost_factor": cost_reduction_factor,
        "co2_factor": co2_reduction_factor,
        "summary": summary,
    }
