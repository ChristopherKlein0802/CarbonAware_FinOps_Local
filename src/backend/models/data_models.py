"""
Data Models for Carbon-Aware FinOps Dashboard
Professional data structures with type hints and validation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class InstanceState(Enum):
    """AWS EC2 Instance states"""
    RUNNING = "running"
    STOPPED = "stopped"
    PENDING = "pending"
    TERMINATED = "terminated"


class APISource(Enum):
    """External API sources"""
    ELECTRICITY_MAPS = "electricitymap"
    BOAVIZTA = "boavizta"
    AWS_COST_EXPLORER = "aws_cost_explorer"


@dataclass
class CarbonIntensity:
    """Carbon intensity data from ElectricityMaps API"""
    value: float  # g CO2/kWh
    timestamp: datetime
    region: str  # AWS region
    zone: str    # ElectricityMaps zone (e.g., "DE")
    source: str


@dataclass
class PowerConsumption:
    """Hardware power consumption from Boavizta API"""
    avg_power_watts: float
    min_power_watts: float
    max_power_watts: float
    confidence_level: str
    source: str


@dataclass
class AWSCostData:
    """Cost data from AWS Cost Explorer API"""
    monthly_cost_usd: float
    monthly_cost_eur: float
    service_costs: Dict[str, float]
    region: str
    period_start: datetime
    period_end: datetime
    source: str


@dataclass
class EC2Instance:
    """AWS EC2 Instance with carbon and cost data"""
    instance_id: str
    instance_type: str
    state: InstanceState
    region: str

    # Power & Carbon Data
    power_watts: Optional[float] = None
    hourly_co2_g: Optional[float] = None
    monthly_co2_kg: Optional[float] = None

    # Cost Data
    hourly_cost_usd: Optional[float] = None
    monthly_cost_usd: Optional[float] = None
    monthly_cost_eur: Optional[float] = None

    # Academic Metadata
    confidence_level: str = "medium"
    data_sources: List[APISource] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class BusinessCase:
    """Business case calculations for thesis validation"""
    baseline_cost_eur: float
    baseline_co2_kg: float

    # Optimization scenarios
    office_hours_savings_eur: float
    carbon_aware_savings_eur: float
    integrated_savings_eur: float

    # Carbon reductions
    office_hours_co2_reduction_kg: float
    carbon_aware_co2_reduction_kg: float
    integrated_co2_reduction_kg: float

    # Academic validation
    confidence_interval: float = 0.15  # ±15% conservative
    methodology: str = "Theoretical framework for Bachelor thesis"
    validation_status: str = "Requires empirical validation"


@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    instances: List[EC2Instance]
    carbon_intensity: CarbonIntensity
    total_cost_eur: float
    total_co2_kg: float
    business_case: BusinessCase

    # API Health & Performance
    api_response_times: Dict[str, float]
    api_health_status: Dict[str, bool]
    cache_hit_rates: Dict[str, float]

    # Academic Metadata
    data_freshness: datetime
    uncertainty_ranges: Dict[str, float]
    academic_disclaimers: List[str]


@dataclass
class PerformanceMetrics:
    """API performance and caching metrics"""
    api_name: str
    response_time_ms: float
    cache_hit: bool
    error_count: int
    last_successful_call: datetime
    rate_limit_remaining: Optional[int] = None


@dataclass
class ValidationResult:
    """Thesis validation and competitive analysis results"""
    methodology_score: float  # 0-1
    data_quality_score: float  # 0-1
    academic_rigor_score: float  # 0-1

    # Competitive positioning
    novel_features: List[str]
    competitive_advantages: List[str]
    limitations: List[str]

    # Scientific validation
    uncertainty_documented: bool
    fallback_data_used: bool
    conservative_estimates: bool