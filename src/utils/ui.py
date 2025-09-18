"""
Utility functions for dashboard pages
Clean separation of calculations and data processing logic
"""

from typing import Dict, Any, Tuple, List
from src.constants import (
    AcademicConstants,
    CarbonConstants,
    UIConstants
)



def calculate_scenario_savings(projected_cost: float) -> Tuple[float, float, float]:
    """Calculate demonstrative scenario savings"""
    scenario_a_savings = projected_cost * AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR
    scenario_b_savings = projected_cost * AcademicConstants.MODERATE_SCENARIO_FACTOR
    integrated_savings = scenario_b_savings  # Using scenario B

    return scenario_a_savings, scenario_b_savings, integrated_savings

def determine_grid_status(grid_intensity: float) -> Tuple[str, str, str]:
    """Determine grid status and recommendations from carbon intensity"""
    if grid_intensity < CarbonConstants.OPTIMAL_THRESHOLD:
        return "🟢", "EXCELLENT (High Solar/Wind)", "⚡ OPTIMAL TIME: Run energy-intensive workloads NOW"
    elif grid_intensity < CarbonConstants.MODERATE_THRESHOLD:
        return "🟡", "MODERATE (Mixed Sources)", "⏱️ CONSIDER: Delay non-urgent workloads for 2-4 hours"
    else:
        return "🔴", "HIGH CARBON (Coal Peak)", "🚨 AVOID: Postpone batch jobs until grid improves"


def calculate_roi_metrics(projected_cost: float, implementation_cost: float = 5000) -> Tuple[float, float, float, float, float]:
    """Calculate ROI metrics with demonstrative scenarios"""
    scenario_a_savings, scenario_b_savings, integrated_savings = calculate_scenario_savings(projected_cost)

    monthly_roi = integrated_savings
    payback_months = implementation_cost / monthly_roi if monthly_roi > 0 else 999

    return scenario_a_savings, scenario_b_savings, integrated_savings, payback_months, implementation_cost

