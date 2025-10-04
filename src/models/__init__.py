"""
Data Models for Carbon-Aware FinOps Dashboard
Type-safe data structures organized by domain
"""

from .aws import EC2Instance, AWSCostData
from .carbon import CarbonIntensity, PowerConsumption
from .business import BusinessCase
from .dashboard import DashboardData, APIHealthStatus

__all__ = [
    # AWS models
    'EC2Instance',
    'AWSCostData',

    # Carbon models
    'CarbonIntensity',
    'PowerConsumption',

    # Business models
    'BusinessCase',

    # Dashboard models
    'DashboardData',
    'APIHealthStatus'
]
