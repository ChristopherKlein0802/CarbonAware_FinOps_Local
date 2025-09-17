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

def calculate_cloudtrail_precision_metrics(instances: List[Any]) -> Tuple[int, int, float]:
    """Calculate CloudTrail precision metrics from instance list"""
    if not instances:
        return 0, 0, 0

    total_instances = len(instances)
    cloudtrail_instances = len([i for i in instances if "cloudtrail_audit" in (i.data_sources or [])])
    precision_ratio = (cloudtrail_instances / total_instances * 100) if total_instances > 0 else 0

    return total_instances, cloudtrail_instances, precision_ratio

def calculate_baseline_metrics(dashboard_data: Any) -> Tuple[float, float]:
    """Calculate baseline cost and CO2 metrics per instance"""
    if not dashboard_data or not dashboard_data.instances:
        return AcademicConstants.DEFAULT_COST_PER_INSTANCE_EUR, AcademicConstants.DEFAULT_CO2_PER_INSTANCE_KG

    total_instances = len(dashboard_data.instances)
    baseline_cost_per_instance = dashboard_data.total_cost_eur / total_instances if total_instances > 0 else 5.20
    baseline_co2_per_instance = dashboard_data.total_co2_kg / total_instances if total_instances > 0 else 0.093

    return baseline_cost_per_instance, baseline_co2_per_instance

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

def create_instance_data_row(instance: Any) -> Dict[str, Any]:
    """Create standardized instance data row for tables"""
    is_cloudtrail = "cloudtrail_audit" in (instance.data_sources or [])
    precision_badge = "🎯 Audit" if is_cloudtrail else "📋 Estimate"
    accuracy = "±5%" if is_cloudtrail else "±40%"

    return {
        "Instance ID": instance.instance_id[:10] + "...",
        "Type": instance.instance_type,
        "State": instance.state,
        "Runtime Source": precision_badge,
        "Accuracy": accuracy,
        "Confidence": instance.confidence_level,
        "Power (W)": instance.power_watts or 0,
        "Cost (€/month)": instance.monthly_cost_eur or 0,
        "CO₂ (kg/month)": instance.monthly_co2_kg or 0
    }

def calculate_roi_metrics(projected_cost: float, implementation_cost: float = 5000) -> Tuple[float, float, float, float, float]:
    """Calculate ROI metrics with demonstrative scenarios"""
    scenario_a_savings, scenario_b_savings, integrated_savings = calculate_scenario_savings(projected_cost)

    monthly_roi = integrated_savings
    payback_months = implementation_cost / monthly_roi if monthly_roi > 0 else 999

    return scenario_a_savings, scenario_b_savings, integrated_savings, payback_months, implementation_cost

def create_precision_data_row(instance: Any) -> Dict[str, Any]:
    """Create precision analysis data row"""
    is_cloudtrail = "cloudtrail_audit" in (instance.data_sources or [])
    return {
        "Instance": instance.instance_id[:8],
        "Type": instance.instance_type,
        "State": instance.state,
        "Runtime Source": "CloudTrail Audit" if is_cloudtrail else "Conservative Estimate",
        "Confidence": instance.confidence_level,
        "Accuracy": "±5%" if is_cloudtrail else "±40%",
        "Cost (EUR)": f"€{instance.monthly_cost_eur:.2f}" if instance.monthly_cost_eur else "N/A"
    }