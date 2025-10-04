"""
Dashboard and application data models
Complete dashboard data structure and API health monitoring
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

# Import from other model modules to avoid circular imports
from .aws import EC2Instance
from .business import BusinessCase
from .carbon import CarbonIntensity


@dataclass
class TimeSeriesPoint:
    """Hourly aligned snapshot for time alignment coverage."""

    timestamp: datetime
    cost_eur_per_hour: float
    co2_kg_per_hour: float
    carbon_intensity: Optional[float] = None


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
        time_series: Hourly cost/carbon alignment points
        tac_score: Time Alignment Coverage score (0.0-1.0)
        tac_aligned_hours: Number of aligned hours in time series
        cost_mape: Cost Mean Absolute Percentage Error vs AWS
        carbon_history: Historical carbon intensity data from ElectricityMaps
        self_collected_carbon_history: Self-collected carbon intensity snapshots
    """
    instances: List[EC2Instance]
    carbon_intensity: Optional[CarbonIntensity] = None
    total_cost_eur: float = 0.0
    total_co2_kg: float = 0.0
    business_case: Optional[BusinessCase] = None
    data_freshness: Optional[datetime] = None
    academic_disclaimers: Optional[List[str]] = None
    api_health_status: Optional[Dict[str, 'APIHealthStatus']] = None
    validation_factor: Optional[float] = None
    accuracy_status: Optional[str] = None
    time_series: List[TimeSeriesPoint] = field(default_factory=list)
    tac_score: Optional[float] = None
    tac_aligned_hours: Optional[int] = None
    cost_mape: Optional[float] = None
    carbon_history: List[Dict[str, Any]] = field(default_factory=list)
    self_collected_carbon_history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.academic_disclaimers is None:
            self.academic_disclaimers = []


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
