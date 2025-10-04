"""
Carbon and environmental data models
Carbon intensity, power consumption, and environmental metrics
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
