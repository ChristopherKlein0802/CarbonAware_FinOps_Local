"""Business and validation related services."""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from ..models.aws import EC2Instance, AWSCostData
from ..models.business import BusinessCase
from ..core.calculator import BusinessCaseCalculator

logger = logging.getLogger(__name__)


class BusinessInsightsService:
    """Encapsulates business-case calculations and validation logic."""

    def __init__(self, calculator: Optional[BusinessCaseCalculator] = None) -> None:
        self._calculator = calculator or BusinessCaseCalculator()

    def calculate_business_case(
        self,
        *,
        baseline_cost_eur: float,
        baseline_co2_kg: float,
        validation_factor: float,
    ) -> BusinessCase:
        return self._calculator.calculate_business_case(baseline_cost_eur, baseline_co2_kg, validation_factor)

    def validate_costs(
        self,
        instances: List[EC2Instance],
        calculated_cost_eur: float,
        cost_data: Optional[AWSCostData],
    ) -> Tuple[float, Optional[str]]:
        validation_factor = self._calculator.calculate_cloudtrail_enhanced_accuracy(
            instances,
            calculated_cost_eur,
            cost_data,
            original_instances=None,
        )
        accuracy_status = getattr(self._calculator, "_last_accuracy_status", None)
        logger.debug(
            "Business validation complete: factor=%.3f, status=%s",
            validation_factor,
            accuracy_status,
        )
        return validation_factor, accuracy_status
