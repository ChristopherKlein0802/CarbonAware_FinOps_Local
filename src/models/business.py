"""
Business case and financial data models
Cost optimization, savings calculations, and business metrics
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BusinessCase:
    """Business case calculations for cost and carbon optimization"""
    baseline_cost_eur: float
    baseline_co2_kg: float
    office_hours_savings_eur: Optional[float] = None
    carbon_aware_savings_eur: Optional[float] = None
    integrated_savings_eur: Optional[float] = None
    office_hours_co2_reduction_kg: Optional[float] = None
    carbon_aware_co2_reduction_kg: Optional[float] = None
    integrated_co2_reduction_kg: Optional[float] = None
    confidence_interval: float = 0.15
    methodology: str = "Theoretical framework"
    validation_status: str = "Requires validation"
    source_notes: Optional[str] = None
