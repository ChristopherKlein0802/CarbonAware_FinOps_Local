"""
API Layer for Carbon-Aware FinOps Dashboard
Modular API integration for maintainability and testing
"""

from .client import UnifiedAPIClient, unified_api_client
from .electricity import ElectricityMapsAPI
from .aws import AWSAPIClient
from .boavizta import BoaviztaAPI

__all__ = [
    'UnifiedAPIClient',
    'unified_api_client',
    'ElectricityMapsAPI',
    'AWSAPIClient',
    'BoaviztaAPI'
]