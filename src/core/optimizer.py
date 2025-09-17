"""
Carbon-Aware Optimization Engine
Optimization strategies and scheduling logic
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..models.aws import EC2Instance
from ..utils.calculations import safe_round

logger = logging.getLogger(__name__)


class CarbonOptimizer:
    """Optimizer for carbon-aware scheduling and instance management"""

    def __init__(self):
        """Initialize carbon optimizer"""
        logger.info("✅ Carbon Optimizer initialized")

    def analyze_optimization_opportunities(self, instances: List[EC2Instance]) -> Dict:
        """Analyze potential optimization opportunities based on instance usage patterns"""
        if not instances:
            logger.warning("⚠️ No instances provided for optimization analysis")
            return {
                "office_hours_potential": 0.0,
                "carbon_aware_potential": 0.0,
                "integrated_potential": 0.0,
                "analysis_quality": "insufficient_data"
            }

        # Calculate total baseline metrics
        total_cost_eur = sum(inst.monthly_cost_eur for inst in instances if inst.monthly_cost_eur)
        total_co2_kg = sum(inst.monthly_co2_kg for inst in instances if inst.monthly_co2_kg)

        # DEMONSTRATIVE OPTIMIZATION SCENARIOS
        # Conservative round numbers for academic methodology demonstration

        # Scenario A: Office hours scheduling (10% conservative estimate)
        office_hours_factor = 0.10  # Conservative demonstrative scenario
        office_hours_cost_potential = total_cost_eur * office_hours_factor
        office_hours_co2_potential = total_co2_kg * office_hours_factor

        # Scenario B: Carbon-aware scheduling (20% moderate estimate)
        carbon_aware_factor = 0.20  # Moderate demonstrative scenario
        carbon_aware_cost_potential = total_cost_eur * carbon_aware_factor
        carbon_aware_co2_potential = total_co2_kg * carbon_aware_factor

        # Integrated approach (using scenario B as primary)
        integrated_cost_potential = carbon_aware_cost_potential
        integrated_co2_potential = carbon_aware_co2_potential

        logger.info(f"🔍 Optimization analysis: {len(instances)} instances, €{total_cost_eur:.2f} baseline")
        logger.info(f"   📅 Office hours potential: €{office_hours_cost_potential:.2f} ({office_hours_factor:.0%})")
        logger.info(f"   🌱 Carbon-aware potential: €{carbon_aware_cost_potential:.2f} ({carbon_aware_factor:.0%})")

        return {
            "office_hours_potential": safe_round(office_hours_cost_potential, 2),
            "carbon_aware_potential": safe_round(carbon_aware_cost_potential, 2),
            "integrated_potential": safe_round(integrated_cost_potential, 2),
            "office_hours_co2_potential": safe_round(office_hours_co2_potential, 3),
            "carbon_aware_co2_potential": safe_round(carbon_aware_co2_potential, 3),
            "integrated_co2_potential": safe_round(integrated_co2_potential, 3),
            "baseline_cost_eur": safe_round(total_cost_eur, 2),
            "baseline_co2_kg": safe_round(total_co2_kg, 3),
            "analysis_quality": "demonstrative_scenarios",
            "methodology_note": "Conservative estimates for capability demonstration"
        }

    def calculate_carbon_aware_scheduling(self, carbon_history: List[Dict]) -> Dict:
        """Calculate optimal scheduling based on carbon intensity patterns

        Args:
            carbon_history: List of carbon intensity measurements with timestamps

        Returns:
            Dict: Scheduling recommendations with optimal and peak hours
        """
        if not carbon_history:
            logger.warning("⚠️ No carbon history provided for scheduling analysis")
            return {
                "optimal_hours": [],
                "peak_hours": [],
                "savings_potential": 0.0,
                "analysis_quality": "insufficient_data"
            }

        # Sort by carbon intensity to identify patterns
        sorted_by_intensity = sorted(carbon_history, key=lambda x: x.get('intensity', 999))

        # Calculate quartiles for categorization
        n = len(sorted_by_intensity)
        if n < 4:
            logger.warning("⚠️ Insufficient carbon data for quartile analysis")
            return {
                "optimal_hours": [],
                "peak_hours": [],
                "savings_potential": 0.0,
                "analysis_quality": "insufficient_data_points"
            }

        # Define optimal hours (lowest 25% carbon intensity)
        optimal_count = max(1, n // 4)
        optimal_data = sorted_by_intensity[:optimal_count]
        optimal_hours = [item.get('hour', 0) for item in optimal_data]

        # Define peak hours (highest 25% carbon intensity)
        peak_data = sorted_by_intensity[-optimal_count:]
        peak_hours = [item.get('hour', 0) for item in peak_data]

        # Calculate potential savings (demonstrative)
        if len(sorted_by_intensity) >= 2:
            min_intensity = sorted_by_intensity[0].get('intensity', 0)
            max_intensity = sorted_by_intensity[-1].get('intensity', 0)
            intensity_variance = max_intensity - min_intensity

            # Conservative savings estimate based on intensity variance
            if max_intensity > 0:
                variance_ratio = intensity_variance / max_intensity
                savings_potential = min(0.15, variance_ratio * 0.5)  # Cap at 15%
            else:
                savings_potential = 0.0
        else:
            savings_potential = 0.0

        logger.info(f"📅 Carbon-aware scheduling analysis: {n} data points")
        logger.info(f"   🌱 Optimal hours: {sorted(optimal_hours)} (low carbon)")
        logger.info(f"   🔥 Peak hours: {sorted(peak_hours)} (high carbon)")
        logger.info(f"   💡 Potential savings: {savings_potential:.1%}")

        return {
            "optimal_hours": sorted(optimal_hours),
            "peak_hours": sorted(peak_hours),
            "savings_potential": safe_round(savings_potential, 3),
            "analysis_quality": "pattern_based",
            "min_intensity": min_intensity if 'min_intensity' in locals() else None,
            "max_intensity": max_intensity if 'max_intensity' in locals() else None,
            "intensity_variance": intensity_variance if 'intensity_variance' in locals() else None,
            "methodology_note": "Demonstrative analysis based on carbon intensity patterns"
        }

    def suggest_instance_rightsizing(self, instances: List[EC2Instance]) -> List[Dict]:
        """Suggest instance type optimizations based on usage patterns

        Args:
            instances: List of EC2 instances with utilization data

        Returns:
            List[Dict]: Rightsizing recommendations
        """
        if not instances:
            logger.warning("⚠️ No instances provided for rightsizing analysis")
            return []

        recommendations = []

        for instance in instances:
            # Skip instances without sufficient data
            if not hasattr(instance, 'power_watts') or not instance.power_watts:
                continue

            # Basic rightsizing logic based on power consumption patterns
            current_type = instance.instance_type
            current_power = instance.power_watts

            # Categorize instance utilization (demonstrative logic)
            if current_power < 10:  # Very low power usage
                utilization_category = "underutilized"
                recommendation_type = "Consider downsizing to smaller instance type"
                potential_savings = "15-30%"
            elif current_power < 50:  # Moderate power usage
                utilization_category = "moderate"
                recommendation_type = "Current sizing appears appropriate"
                potential_savings = "0-5%"
            else:  # High power usage
                utilization_category = "high"
                recommendation_type = "Monitor for potential upsizing needs"
                potential_savings = "Performance optimization"

            recommendation = {
                "instance_id": instance.instance_id,
                "current_type": current_type,
                "current_power_watts": current_power,
                "utilization_category": utilization_category,
                "recommendation": recommendation_type,
                "potential_savings": potential_savings,
                "confidence": "demonstrative",
                "methodology_note": "Based on power consumption patterns - requires detailed utilization analysis"
            }

            recommendations.append(recommendation)

        logger.info(f"📏 Rightsizing analysis: {len(recommendations)} recommendations generated")
        if recommendations:
            underutilized = len([r for r in recommendations if r["utilization_category"] == "underutilized"])
            logger.info(f"   📉 Potentially underutilized: {underutilized} instances")

        return recommendations