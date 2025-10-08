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
    monthly_co2_kg: Optional[float] = None
    monthly_cost_usd: Optional[float] = None
    monthly_cost_eur: Optional[float] = None
    runtime_hours: Optional[float] = None
    hourly_price_usd: Optional[float] = None
    cpu_utilization: Optional[float] = None
    data_quality: str = "estimated"
    confidence_level: str = "medium"
    data_sources: Optional[List[str]] = None
    last_updated: Optional[datetime] = None

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
    Complete dashboard data structure.

    Attributes:
        instances: List of EC2 instances with enriched data
        carbon_intensity: Current carbon intensity from ElectricityMaps
        total_cost_eur: Total monthly costs in EUR
        total_co2_kg: Total monthly CO₂ emissions in kg
        business_case: Business case calculations and scenarios
        data_freshness: Timestamp of last data update
        academic_disclaimers: List of academic integrity notes
        api_health_status: Health status of all API integrations
        validation_factor: Cost validation factor (calculated vs. AWS)
        accuracy_status: Human-readable accuracy status
        cloudtrail_coverage: Percentage of instances with CloudTrail runtime data (0.0-1.0)
        cloudtrail_tracked_instances: Number of instances with runtime data
        carbon_history: Historical carbon intensity data from ElectricityMaps
        self_collected_carbon_history: Self-collected carbon intensity snapshots
    """

    instances: List[EC2Instance]
    carbon_intensity: Optional[CarbonIntensity] = None
    total_cost_eur: float = 0.0
    total_co2_kg: float = 0.0
    business_case: Optional[BusinessCase] = None
    data_freshness: Optional[datetime] = None
    academic_disclaimers: List[str] = field(default_factory=list)
    api_health_status: Optional[Dict[str, APIHealthStatus]] = None
    validation_factor: Optional[float] = None
    accuracy_status: Optional[str] = None
    cloudtrail_coverage: Optional[float] = None
    cloudtrail_tracked_instances: Optional[int] = None
    carbon_history: List[Dict[str, Any]] = field(default_factory=list)
    self_collected_carbon_history: List[Dict[str, Any]] = field(default_factory=list)


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
