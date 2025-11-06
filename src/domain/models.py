"""
Domain Models - Complete data model definitions for Carbon-Aware FinOps Dashboard

This module consolidates all domain entities:
- AWS models (EC2 instances, cost data)
- Carbon models (intensity, power consumption)
- Business models (optimization scenarios)
- Dashboard models (UI data structures, API health)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


# ============================================================================
# AWS MODELS
# ============================================================================


@dataclass
class EC2Instance:
    """EC2 instance with carbon and cost data"""

    instance_id: str
    instance_type: str
    state: str
    region: str
    instance_name: Optional[str] = None
    power_watts: Optional[float] = None
    hourly_co2_g: Optional[float] = None
    runtime_hours: Optional[float] = None
    hourly_price_usd: Optional[float] = None
    cpu_utilization: Optional[float] = None
    data_quality: str = "estimated"
    confidence_level: str = "medium"
    data_sources: Optional[List[str]] = None
    last_updated: Optional[datetime] = None

    # ========================================================================
    # PERIOD-BASED CALCULATIONS (New flexible time window approach)
    # ========================================================================

    period_days: int = 30
    """Analysis window in days (1, 7, or 30). Determines timeframe for all calculations."""

    # Hourly-Precise Method (24h real-time data scaled to period)
    co2_kg_hourly: Optional[float] = None
    """CO2 emissions using Hourly-Precise method: daily_co2_kg × period_days"""

    cost_eur_hourly: Optional[float] = None
    """Cost using Hourly-Precise method: daily_cost × period_days"""

    # Average-Based Method (full period runtime)
    co2_kg_average: Optional[float] = None
    """CO2 emissions using Average-Based method: power × carbon × runtime_period"""

    cost_eur_average: Optional[float] = None
    """Cost using Average-Based method: price × runtime_period"""

    # ========================================================================
    # HOURLY-PRECISE CALCULATION METADATA
    # ========================================================================

    daily_co2_kg: Optional[float] = None
    """Daily CO2 emissions calculated with hourly precision (24h window)"""

    daily_runtime_hours: Optional[float] = None
    """Runtime hours from last 24h window (sum of hourly fractions)"""

    co2_calculation_method: str = "average"
    """
    Method used for CO2 calculation:
    - 'hourly': Hourly-Precise calculation with 24h data
    - 'average': Average-Based calculation (fallback)
    - 'none': No CO2 data available
    """

    hourly_co2_breakdown: Optional[List[Dict]] = None
    """
    Hourly breakdown of CO2 emissions (only available for hourly method).
    Format: List of dicts with keys: timestamp, co2_g, power_watts, cpu_percent, carbon_intensity, runtime_fraction, running
    """

    instance_age_days: Optional[int] = None
    """Days since instance launch (for data completeness validation)"""

    data_completeness_24h: Optional[int] = None
    """Number of hours with valid data in 24h window (0-24)"""

    # ========================================================================
    # DEPRECATED FIELDS (Kept for backward compatibility, will be removed in v2.0.0)
    # Migration Guide: docs/migration/field-deprecation.md
    # ========================================================================

    monthly_co2_kg: Optional[float] = None
    """DEPRECATED: Use co2_kg_average instead. Maps to period-based calculation."""

    monthly_cost_usd: Optional[float] = None
    """DEPRECATED: Use cost_eur_hourly or cost_eur_average instead."""

    monthly_cost_eur: Optional[float] = None
    """DEPRECATED: Use cost_eur_average instead. Maps to period-based calculation."""

    monthly_co2_kg_projected: Optional[float] = None
    """DEPRECATED: Use co2_kg_hourly instead. Was: daily_co2_kg × 30"""

    monthly_co2_kg_30d: Optional[float] = None
    """DEPRECATED: Use co2_kg_average instead. Was: 30d actual runtime calculation."""

    monthly_cost_projected_eur: Optional[float] = None
    """DEPRECATED: Use cost_eur_hourly instead. Was: 24h projected to 30d"""

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []


@dataclass
class AWSCostData:
    """AWS cost data structure."""

    monthly_cost_usd: float
    service_costs: Dict[str, float]
    region: str
    source: str
    fetched_at: Optional[datetime] = None


# ============================================================================
# CARBON MODELS
# ============================================================================


@dataclass
class CarbonIntensity:
    """Carbon intensity data structure."""

    value: float  # gCO2/kWh
    timestamp: datetime
    region: str
    source: str
    fetched_at: Optional[datetime] = None


@dataclass
class PowerConsumption:
    """Power consumption data structure for AWS instances."""

    avg_power_watts: float
    min_power_watts: float
    max_power_watts: float
    confidence_level: str
    source: str


# ============================================================================
# BUSINESS MODELS
# ============================================================================


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
    analysis_period_days: int = 30
    """Analysis period for which savings are calculated (1, 7, or 30 days)"""


# ============================================================================
# DASHBOARD MODELS
# ============================================================================


@dataclass
class TimeSeriesPoint:
    """Hourly aligned snapshot for time alignment coverage."""

    timestamp: datetime
    cost_eur_per_hour: float
    co2_kg_per_hour: float
    carbon_intensity: Optional[float] = None


@dataclass
class APIHealthStatus:
    """API health monitoring data"""

    service: str
    status: str  # "healthy", "degraded", "error"
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    healthy: bool = False
    last_api_call: Optional[datetime] = None


@dataclass
class DashboardData:
    """
    Complete dashboard data structure with period-based analysis.

    Key Attributes:
        instances: List of EC2 instances with enriched data
        analysis_period_days: Analysis time window (1, 7, or 30 days)
        total_co2_hourly: Total CO2 using Hourly-Precise method
        total_co2_average: Total CO2 using Average-Based method
        total_cost_hourly: Total costs using Hourly-Precise method
        total_cost_average: Total costs using Average-Based method
        carbon_intensity: Current carbon intensity from ElectricityMaps
        business_case: Business case calculations for selected period
        validation_factor: Cost validation factor (calculated vs. AWS)
        cloudtrail_coverage: Percentage of instances with CloudTrail data
        hourly_precise_count: Instances using Hourly-Precise method
        fallback_count: Instances using Average-Based method
    """

    instances: List[EC2Instance]

    # ========================================================================
    # PERIOD-BASED ANALYSIS CONFIGURATION
    # ========================================================================

    analysis_period_days: int = 30
    """Current analysis time window in days (1, 7, or 30)"""

    # ========================================================================
    # PERIOD TOTALS - HOURLY-PRECISE METHOD
    # ========================================================================

    total_co2_hourly: float = 0.0
    """Total CO2 emissions using Hourly-Precise method (24h scaled to period)"""

    total_cost_hourly: float = 0.0
    """Total costs using Hourly-Precise method (24h scaled to period)"""

    # ========================================================================
    # PERIOD TOTALS - AVERAGE-BASED METHOD
    # ========================================================================

    total_co2_average: float = 0.0
    """Total CO2 emissions using Average-Based method (full period runtime)"""

    total_cost_average: float = 0.0
    """Total costs using Average-Based method (full period runtime)"""

    # ========================================================================
    # METHOD STATISTICS
    # ========================================================================

    hourly_precise_count: int = 0
    """Number of instances successfully using Hourly-Precise calculation"""

    fallback_count: int = 0
    """Number of instances falling back to Average-Based calculation"""

    # ========================================================================
    # CARBON & VALIDATION DATA
    # ========================================================================

    carbon_intensity: Optional[CarbonIntensity] = None
    carbon_history: List[Dict[str, Any]] = field(default_factory=list)
    self_collected_carbon_history: List[Dict[str, Any]] = field(default_factory=list)

    validation_factor: Optional[float] = None
    """Cost validation: Cost Explorer ÷ Calculated (aligned period windows)"""

    cost_explorer_eur: Optional[float] = None
    """Actual AWS Cost Explorer value in EUR for the analysis period"""

    accuracy_status: Optional[str] = None
    cloudtrail_coverage: Optional[float] = None
    cloudtrail_tracked_instances: Optional[int] = None

    # ========================================================================
    # DASHBOARD METADATA
    # ========================================================================

    business_case: Optional[BusinessCase] = None
    data_freshness: Optional[datetime] = None
    academic_disclaimers: List[str] = field(default_factory=list)
    api_health_status: Optional[Dict[str, APIHealthStatus]] = None

    # ========================================================================
    # DEPRECATED FIELDS (Backward compatibility, will be removed in v2.0.0)
    # Migration Guide: docs/migration/field-deprecation.md
    # ========================================================================

    total_cost_eur: float = 0.0
    """DEPRECATED: Use total_cost_average instead. Mapped for backward compatibility."""

    total_co2_kg: float = 0.0
    """DEPRECATED: Use total_co2_average instead. Mapped for backward compatibility."""

    total_cost_projected_eur: float = 0.0
    """DEPRECATED: Use total_cost_hourly instead. Was: 24h projected to 30d"""

    total_co2_projected_kg: float = 0.0
    """DEPRECATED: Use total_co2_hourly instead. Was: 24h projected to 30d"""

    total_cost_30d_eur: float = 0.0
    """DEPRECATED: Use total_cost_average instead. Was: 30d actual costs"""

    total_co2_30d_kg: float = 0.0
    """DEPRECATED: Use total_co2_average instead. Was: 30d actual CO2"""


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # AWS Models
    "EC2Instance",
    "AWSCostData",
    # Carbon Models
    "CarbonIntensity",
    "PowerConsumption",
    # Business Models
    "BusinessCase",
    # Dashboard Models
    "TimeSeriesPoint",
    "APIHealthStatus",
    "DashboardData",
]
