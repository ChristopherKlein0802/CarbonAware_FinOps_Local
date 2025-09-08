"""
Carbon intensity API client for real-time carbon data.
Focuses on ElectricityMap integration for Bachelor Thesis analysis.
"""

import os
import requests
import math
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# AWS region to ElectricityMap zone mappings
REGION_MAPPINGS = {
    "eu-central-1": "DE",       # Germany
    "eu-west-1": "IE",         # Ireland
    "eu-west-2": "GB",         # United Kingdom
    "eu-west-3": "FR",         # France
    "eu-north-1": "SE",        # Sweden
    "us-east-1": "US-NE-ISO",  # US East
    "us-west-2": "US-NW-PACW"  # US West
}

# Fallback carbon intensities by region (gCO2/kWh)
FALLBACK_CARBON_VALUES = {
    "eu-central-1": 380,    # Germany
    "eu-west-1": 300,      # Ireland
    "eu-west-2": 250,      # UK
    "eu-west-3": 90,       # France (nuclear)
    "eu-north-1": 40,      # Sweden (hydro)
    "us-east-1": 450,      # US East
    "us-west-2": 350,      # US West
}

def parse_iso_datetime(datetime_str: str) -> datetime:
    """Parse ISO datetime string, handling 'Z' timezone indicator."""
    if datetime_str.endswith("Z"):
        datetime_str = datetime_str[:-1]

    if "+" in datetime_str:
        datetime_str = datetime_str.split("+")[0]
    elif datetime_str.count("-") > 2:
        for i in range(len(datetime_str) - 1, -1, -1):
            if datetime_str[i] in ["-", "+"] and i > 10:
                datetime_str = datetime_str[:i]
                break

    try:
        if "." in datetime_str:
            return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return datetime.now()

@dataclass
class CarbonIntensity:
    """Carbon intensity data structure."""
    value: float  # gCO2/kWh
    timestamp: datetime
    region: str
    source: str

class ElectricityMapClient:
    """ElectricityMap API client for carbon intensity data."""

    BASE_URL = "https://api.electricitymap.org/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELECTRICITYMAP_API_KEY")
        if not self.api_key:
            logger.warning("ElectricityMap API key not provided. Set ELECTRICITYMAP_API_KEY environment variable.")

    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity from ElectricityMap."""
        if not self.api_key:
            logger.warning("ElectricityMap API key not available, using fallback")
            return self._get_fallback_intensity(region)

        headers = {"auth-token": self.api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
            response = requests.get(
                f"{self.BASE_URL}/carbon-intensity/latest", 
                headers=headers, 
                params={"zone": zone}, 
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return CarbonIntensity(
                value=data["carbonIntensity"],
                timestamp=parse_iso_datetime(data["datetime"]),
                region=region,
                source="electricitymap",
            )
        except Exception as e:
            logger.error(f"Error getting ElectricityMap data: {e}")
            return self._get_fallback_intensity(region)

    def get_forecast(self, region: str, hours: int = 24) -> List[CarbonIntensity]:
        """Get carbon intensity forecast from ElectricityMap."""
        if not self.api_key:
            logger.warning("ElectricityMap API key not available, using fallback forecast")
            return self._get_fallback_forecast(region, hours)

        headers = {"auth-token": self.api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
            params = {"zone": zone, "hours": str(hours)}
            response = requests.get(
                f"{self.BASE_URL}/carbon-intensity/forecast", 
                headers=headers, 
                params=params, 
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            forecasts = []

            for item in data.get("forecast", []):
                forecasts.append(
                    CarbonIntensity(
                        value=item["carbonIntensity"],
                        timestamp=parse_iso_datetime(item["datetime"]),
                        region=region,
                        source="electricitymap",
                    )
                )

            return forecasts if forecasts else self._get_fallback_forecast(region, hours)

        except Exception as e:
            logger.error(f"Error getting ElectricityMap forecast: {e}")
            return self._get_fallback_forecast(region, hours)

    def _get_fallback_intensity(self, region: str) -> CarbonIntensity:
        """Get fallback intensity when API fails."""
        return CarbonIntensity(
            value=FALLBACK_CARBON_VALUES.get(region, 380), 
            timestamp=datetime.now(), 
            region=region, 
            source="fallback"
        )

    def _get_fallback_forecast(self, region: str, hours: int) -> List[CarbonIntensity]:
        """Generate fallback forecast when API fails."""
        base_value = self._get_fallback_intensity(region).value
        forecasts = []

        for hour in range(hours):
            # Simple sine wave pattern to simulate daily variation
            variation = math.sin((hour - 6) / 24 * 2 * math.pi) * 50

            forecasts.append(
                CarbonIntensity(
                    value=max(0, base_value + variation),
                    timestamp=datetime.now() + timedelta(hours=hour),
                    region=region,
                    source="fallback_forecast",
                )
            )

        return forecasts

class CarbonIntensityClient:
    """Main client for carbon intensity data - focused on ElectricityMap."""

    def __init__(self, provider: Optional[str] = None):
        # Always use ElectricityMap for Bachelor Thesis (provider parameter for compatibility)
        self.client = ElectricityMapClient()

    def get_current_intensity(self, region: str) -> float:
        """Get current carbon intensity value."""
        try:
            intensity = self.client.get_current_intensity(region)
            logger.info(f"Current carbon intensity for {region}: {intensity.value} gCO2/kWh from {intensity.source}")
            return intensity.value
        except Exception as e:
            logger.error(f"Failed to get carbon intensity: {e}")
            # Return German fallback as default
            return 380.0