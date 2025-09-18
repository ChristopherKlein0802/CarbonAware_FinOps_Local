"""
AWS-related data models
EC2 instances, cost data, and AWS service models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
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
    instance_name: Optional[str] = None  # NEW: Instance name from tags
    power_watts: Optional[float] = None
    hourly_co2_g: Optional[float] = None
    monthly_co2_kg: Optional[float] = None
    monthly_cost_usd: Optional[float] = None
    monthly_cost_eur: Optional[float] = None
    runtime_hours: Optional[float] = None  # NEW: Actual runtime hours (CloudTrail-enhanced)
    hourly_price_usd: Optional[float] = None  # NEW: AWS pricing per hour
    cpu_utilization: Optional[float] = None  # NEW: CPU utilization percentage
    data_quality: str = "estimated"  # NEW: "measured", "calculated", "estimated"
    confidence_level: str = "medium"  # "very_high" (CloudTrail), "high" (API), "medium" (estimates), "low" (fallback)
    data_sources: Optional[List[str]] = None  # Enhanced: includes "cloudtrail_audit" for precision tracking
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