"""
Dashboard and application data models
Complete dashboard data structure and API health monitoring
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

# Import from other model modules to avoid circular imports
from .aws import EC2Instance
from .business import BusinessCase


@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    instances: List[EC2Instance]
    carbon_intensity: Optional[Any] = None  # CarbonIntensity from api.carbon
    total_cost_eur: float = 0.0
    total_co2_kg: float = 0.0
    business_case: Optional[BusinessCase] = None
    data_freshness: Optional[datetime] = None
    uncertainty_ranges: Dict[str, float] = None
    academic_disclaimers: List[str] = None
    api_health_status: Optional[Dict[str, 'APIHealthStatus']] = None
    validation_factor: Optional[float] = None
    accuracy_status: Optional[str] = None

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
