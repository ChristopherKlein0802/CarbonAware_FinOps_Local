"""
Calculation Engine for Carbon-Aware FinOps Dashboard
CO2 and cost calculation logic
"""

import logging
from typing import Optional, List, Any
from datetime import datetime

from src.domain.models import EC2Instance, AWSCostData, BusinessCase
from src.domain.constants import AcademicConstants

logger = logging.getLogger(__name__)


class BusinessCaseCalculator:
    """Calculator for business case scenarios and savings"""

    def __init__(self):
        """Initialize business case calculator"""
        logger.info("✅ Business Case Calculator initialized")

    def calculate_business_case(
        self, baseline_cost: float, baseline_co2: float, validation_factor: float = 1.0
    ) -> BusinessCase:
        """Calculate business case scenarios with dynamic factors based on validation and data quality

        Args:
            baseline_cost: Current monthly cost in EUR
            baseline_co2: Current monthly CO2 emissions in kg
            validation_factor: Cost validation factor from AWS Cost Explorer comparison
        """

        # Normalise negative inputs (defensive programming for academic metrics)
        baseline_cost = max(baseline_cost, 0.0)
        baseline_co2 = max(baseline_co2, 0.0)

        # Base factors derived from literature (McKinsey [7]: 15–25% cost savings, MIT [20]: 15–25% CO₂)
        base_conservative = AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR  # 10%
        base_moderate = AcademicConstants.MODERATE_SCENARIO_FACTOR  # 20%

        if baseline_cost < 1.0:  # Development/Test-Szenario
            quality_modifier = 0.4
            logger.info("🧪 Development environment: Conservative optimization estimates")
        elif validation_factor <= 1.5:  # Gute Datenqualität (nahe Echtwert)
            quality_modifier = 0.8
        elif validation_factor <= 5.0:  # Aufbauende Datenlage
            quality_modifier = 0.6
        elif validation_factor <= 50.0:  # Stark eingeschränkte Daten
            quality_modifier = 0.45
        else:  # Kaum valide Datenpunkte
            quality_modifier = 0.3

        # Cost-based scaling: larger infrastructures have more optimization potential
        if baseline_cost > 500:  # Large infrastructure
            cost_scaling = 1.3
        elif baseline_cost > 100:  # Medium infrastructure
            cost_scaling = 1.1
        else:  # Small infrastructure
            cost_scaling = 0.8

        # Calculate dynamic factors (cap reflects conservative interpretation of literature ranges)
        scenario_a_factor = min(base_conservative * quality_modifier * cost_scaling, 0.15)
        scenario_b_factor = min(base_moderate * quality_modifier * cost_scaling, 0.25)

        # Apply factors to calculate actual savings
        scenario_a_cost_reduction = baseline_cost * scenario_a_factor
        scenario_a_co2_reduction = baseline_co2 * scenario_a_factor

        scenario_b_cost_reduction = baseline_cost * scenario_b_factor
        scenario_b_co2_reduction = baseline_co2 * scenario_b_factor

        # Use moderate scenario for integrated display
        integrated_cost_reduction = scenario_b_cost_reduction
        integrated_co2_reduction = scenario_b_co2_reduction

        logger.info(f"🎯 DYNAMIC Business Case Calculation:")
        logger.info(f"   💰 Baseline Cost: €{baseline_cost:.2f} → Scale Factor: {cost_scaling:.1f}")
        logger.info(
            f"   📊 Validation Factor: {validation_factor:.2f} → Quality Tier: {'Good' if validation_factor <= 1.5 else 'Moderate' if validation_factor <= 5.0 else 'Limited'}"
        )
        logger.info(
            f"   🎯 Conservative Scenario: {scenario_a_factor:.1%} reduction → €{scenario_a_cost_reduction:.2f}"
        )
        logger.info(f"   🚀 Moderate Scenario: {scenario_b_factor:.1%} reduction → €{scenario_b_cost_reduction:.2f}")

        return BusinessCase(
            baseline_cost_eur=baseline_cost,
            baseline_co2_kg=baseline_co2,
            office_hours_savings_eur=scenario_a_cost_reduction,
            carbon_aware_savings_eur=scenario_b_cost_reduction,
            integrated_savings_eur=integrated_cost_reduction,
            office_hours_co2_reduction_kg=scenario_a_co2_reduction,
            carbon_aware_co2_reduction_kg=scenario_b_co2_reduction,
            integrated_co2_reduction_kg=integrated_co2_reduction,
            confidence_interval=0.15,
            methodology="INTEGRATION_EXCELLENCE",
            validation_status=f"Cost validation factor: {validation_factor:.2f}",
            source_notes="Factors derived from McKinsey [7] cost studies and MIT carbon-aware scheduling [20]",
        )

    def calculate_cloudtrail_enhanced_accuracy(
        self,
        instances: List[EC2Instance],
        calculated_cost_eur: float,
        cost_data: Optional[AWSCostData],
        original_instances: Optional[List[Any]] = None,
    ) -> tuple[float, Optional[float]]:
        """Enhanced validation with state-awareness and runtime factors

        Returns:
            tuple: (validation_factor, actual_cost_eur)
                - validation_factor: Cost Explorer ÷ Calculated
                - actual_cost_eur: Actual Cost Explorer value in EUR (or None if unavailable)
        """
        if not cost_data or cost_data.monthly_cost_usd <= 0:
            logger.warning("⚠️ No Cost Explorer data for enhanced validation")
            return 1.0, None

        if calculated_cost_eur <= 0:
            logger.warning("⚠️ No calculated costs for validation")
            return 1.0, None

        # Convert actual AWS costs to EUR
        actual_cost_eur = cost_data.monthly_cost_usd * AcademicConstants.get_eur_usd_rate()

        # Calculate expected accuracy based on instance states
        running_instances = [i for i in instances if i.state == "running"]
        stopped_instances = [i for i in instances if i.state == "stopped"]
        total_instances = len(instances)

        if total_instances == 0:
            return 1.0

        # Calculate state-based expectations
        running_ratio = len(running_instances) / total_instances

        # Robust validation factor calculation with development scenario handling
        if calculated_cost_eur < 1.0:  # Less than €1 calculated (minimal runtime)
            # Development/test scenario - use conservative assessment
            validation_factor = min(actual_cost_eur / max(calculated_cost_eur, 0.10), 50.0)  # Cap at 50x
            logger.info("📊 Development scenario detected: minimal calculated runtime")
        else:
            validation_factor = actual_cost_eur / calculated_cost_eur

        # Enhanced logging with state analysis (removed problematic runtime estimation)
        logger.info(f"🎯 Enhanced Cost Validation:")
        logger.info(f"   📊 Calculated (Enhanced): €{calculated_cost_eur:.2f}")
        logger.info(f"   📊 Actual (Cost Explorer): €{actual_cost_eur:.2f}")
        logger.info(f"   📊 Validation Factor: {validation_factor:.2f}")
        logger.info(f"   🔄 Instance States: {len(running_instances)} running, {len(stopped_instances)} stopped")
        logger.info(f"   📈 Running Ratio: {running_ratio:.1%}")
        logger.info(f"   ⚡ Academic Note: Validation based on AWS Cost Explorer comparison")

        # Enhanced state-aware accuracy assessment with development scenario handling
        if calculated_cost_eur < 1.0:  # Development scenario
            logger.info("🧪 Development/Test Environment: Limited runtime data expected")
            accuracy_status = "DEVELOPMENT - Building runtime history"
        elif validation_factor > 50:  # Significantly underestimated
            logger.warning("⚠️ Runtime data insufficient - calculated hours too low")
            logger.info("💡 Recommendation: Allow more time for CloudTrail data collection")
            accuracy_status = "LIMITED - Runtime data incomplete"
        elif validation_factor > 10:  # Moderately underestimated
            logger.info("📈 Runtime data building - accuracy improving over time")
            accuracy_status = "BUILDING - Data collection in progress"
        elif running_ratio > 0.8:  # Mostly running instances
            if 0.7 <= validation_factor <= 1.3:
                logger.info("✅ Enhanced accuracy: EXCELLENT (±30% with mostly running instances)")
                accuracy_status = "EXCELLENT"
            elif 0.5 <= validation_factor <= 1.5:
                logger.info("✅ Enhanced accuracy: GOOD (±50% acceptable for mixed workloads)")
                accuracy_status = "GOOD"
            else:
                logger.warning("⚠️ Enhanced accuracy: MODERATE (consider runtime tracking)")
                accuracy_status = "MODERATE"
        elif running_ratio > 0.3:  # Mixed states
            if 0.4 <= validation_factor <= 1.6:
                logger.info("✅ Enhanced accuracy: GOOD (±60% expected for mixed instance states)")
                accuracy_status = "GOOD"
            else:
                logger.warning("⚠️ Enhanced accuracy: MODERATE (high variance expected)")
                accuracy_status = "MODERATE"
        else:  # Mostly stopped instances
            logger.info("📊 Enhanced accuracy: CONSERVATIVE (mostly stopped instances)")
            accuracy_status = "CONSERVATIVE"

        # Store accuracy assessment for dashboard display
        setattr(self, "_last_accuracy_status", accuracy_status)
        setattr(self, "_last_validation_factor", validation_factor)

        return validation_factor, actual_cost_eur
