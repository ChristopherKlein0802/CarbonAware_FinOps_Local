"""
Carbon intensity API client for real-time carbon data.
Supports multiple providers: WattTime, electricityMap
"""

import os
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CarbonIntensity:
    """Carbon intensity data structure."""
    value: float  # gCO2/kWh
    timestamp: datetime
    region: str
    source: str
    
class CarbonAPIClient(ABC):
    """Abstract base class for carbon intensity API clients."""
    
    @abstractmethod
    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity for a region."""
        pass
    
    @abstractmethod
    def get_forecast(self, region: str, hours: int = 24) -> List[CarbonIntensity]:
        """Get carbon intensity forecast."""
        pass

class WattTimeClient(CarbonAPIClient):
    """WattTime API client implementation."""
    
    BASE_URL = "https://api2.watttime.org/v2"
    
    def __init__(self, username: str = None, password: str = None):
        self.username = username or os.getenv('WATTTIME_USERNAME')
        self.password = password or os.getenv('WATTTIME_PASSWORD')
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with WattTime API."""
        response = requests.get(
            f"{self.BASE_URL}/login",
            auth=(self.username, self.password)
        )
        response.raise_for_status()
        self.token = response.json()['token']
    
    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity from WattTime."""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Map AWS regions to WattTime balancing authorities
        region_mapping = {
            'us-east-1': 'PJM_NJ',
            'us-west-2': 'CAISO_NORTH',
            'eu-west-1': 'IE',
            'eu-north-1': 'SE'
        }
        
        ba = region_mapping.get(region, 'PJM_NJ')
        
        response = requests.get(
            f"{self.BASE_URL}/data",
            headers=headers,
            params={'ba': ba}
        )
        response.raise_for_status()
        
        data = response.json()
        return CarbonIntensity(
            value=data['value'],
            timestamp=datetime.fromisoformat(data['point_time']),
            region=region,
            source='watttime'
        )
    
    def get_forecast(self, region: str, hours: int = 24) -> List[CarbonIntensity]:
        """Get carbon intensity forecast from WattTime."""
        # Implementation for forecast
        pass

class ElectricityMapClient(CarbonAPIClient):
    """electricityMap API client implementation."""
    
    BASE_URL = "https://api.electricitymap.org/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ELECTRICITYMAP_API_KEY')
    
    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity from electricityMap."""
        headers = {'auth-token': self.api_key}
        
        # Map AWS regions to electricityMap zones
        zone_mapping = {
            'us-east-1': 'US-NJ',
            'us-west-2': 'US-CA',
            'eu-west-1': 'IE',
            'eu-north-1': 'SE'
        }
        
        zone = zone_mapping.get(region, 'US-NJ')
        
        response = requests.get(
            f"{self.BASE_URL}/carbon-intensity/latest",
            headers=headers,
            params={'zone': zone}
        )
        response.raise_for_status()
        
        data = response.json()
        return CarbonIntensity(
            value=data['carbonIntensity'],
            timestamp=datetime.fromisoformat(data['datetime']),
            region=region,
            source='electricitymap'
        )

class CarbonIntensityClient:
    """Main client that abstracts different providers."""
    
    def __init__(self, provider: str = None):
        provider = provider or os.getenv('CARBON_API_PROVIDER', 'watttime')
        
        if provider == 'watttime':
            self.client = WattTimeClient()
        elif provider == 'electricitymap':
            self.client = ElectricityMapClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def get_current_intensity(self, region: str) -> float:
        """Get current carbon intensity value."""
        try:
            intensity = self.client.get_current_intensity(region)
            logger.info(f"Current carbon intensity for {region}: {intensity.value} gCO2/kWh")
            return intensity.value
        except Exception as e:
            logger.error(f"Failed to get carbon intensity: {e}")
            # Return average grid intensity as fallback
            return 475.0