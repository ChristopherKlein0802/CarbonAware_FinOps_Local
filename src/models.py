"""
Data Models for Carbon-Aware FinOps Dashboard
Pragmatic Professional Implementation - Type-safe data structures

All data models with proper typing and validation
Clean dataclass implementation without overengineering
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class InstanceState(Enum):
    """AWS instance states"""
    RUNNING = "running"
    STOPPED = "stopped"
    STOPPING = "stopping"
    STARTING = "starting"
    TERMINATED = "terminated"

@dataclass
class EC2Instance:
    """EC2 instance with carbon and cost data"""
    instance_id: str
    instance_type: str
    state: str
    region: str
    power_watts: Optional[float] = None
    hourly_co2_g: Optional[float] = None
    monthly_co2_kg: Optional[float] = None
    monthly_cost_usd: Optional[float] = None
    monthly_cost_eur: Optional[float] = None
    confidence_level: str = "medium"
    data_sources: List[str] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []

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

@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    instances: List[EC2Instance]
    carbon_intensity: Optional[Any] = None  # CarbonIntensity from api_client
    total_cost_eur: float = 0.0
    total_co2_kg: float = 0.0
    business_case: Optional[BusinessCase] = None
    data_freshness: Optional[datetime] = None
    uncertainty_ranges: Dict[str, float] = None
    academic_disclaimers: List[str] = None
    api_health_status: Optional[Dict[str, 'APIHealthStatus']] = None

    def __post_init__(self):
        if self.uncertainty_ranges is None:
            self.uncertainty_ranges = {}
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