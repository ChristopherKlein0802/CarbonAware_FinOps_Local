"""
Carbon intensity API client for real-time carbon data.
Supports multiple providers: WattTime, electricityMap
"""

import os
import requests
import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Union
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# AWS region to API provider zone mappings
REGION_MAPPINGS = {
    "eu-central-1": "DE",       # Germany
    "eu-west-1": "IE",         # Ireland
    "eu-west-2": "GB",         # United Kingdom
    "eu-west-3": "FR",         # France
    "eu-north-1": "SE",        # Sweden
    "us-east-1": "US-NE-ISO",  # US East (ElectricityMap) / PJM_NJ (WattTime)
    "us-west-2": "US-NW-PACW"  # US West (ElectricityMap) / CAISO (WattTime)
}

# WattTime specific mappings (override for different balancing authorities)
WATTTIME_REGION_MAPPINGS = {
    "eu-central-1": "DE",
    "eu-west-1": "IE",
    "eu-west-2": "GB",
    "eu-west-3": "FR",
    "eu-north-1": "SE",
    "us-east-1": "PJM_NJ",
    "us-west-2": "CAISO"
}

# Average carbon intensities by region (gCO2/kWh)
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
        return parse_iso_datetime(datetime_str)


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

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or os.getenv("WATTTIME_USERNAME")
        self.password = password or os.getenv("WATTTIME_PASSWORD")
        self.token = None
        if self.username and self.password:
            self._authenticate()

    def _authenticate(self):
        """Authenticate with WattTime API."""
        if not self.username or not self.password:
            logger.error("WattTime username or password not provided")
            self.token = None
            return

        try:
            response = requests.get(f"{self.BASE_URL}/login", auth=(self.username, self.password), timeout=30)
            response.raise_for_status()
            self.token = response.json()["token"]
        except Exception as e:
            logger.error(f"WattTime authentication failed: {e}")
            self.token = None

    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity from WattTime."""
        if not self.token:
            logger.warning("WattTime token not available, using fallback")
            return self._get_fallback_intensity(region)

        headers = {"Authorization": f"Bearer {self.token}"}
        ba = WATTTIME_REGION_MAPPINGS.get(region, "DE")

        try:
            response = requests.get(f"{self.BASE_URL}/data", headers=headers, params={"ba": ba}, timeout=30)
            response.raise_for_status()

            data = response.json()
            return CarbonIntensity(
                value=data["value"], timestamp=parse_iso_datetime(data["point_time"]), region=region, source="watttime"
            )
        except Exception as e:
            logger.error(f"Error getting WattTime data: {e}")
            return self._get_fallback_intensity(region)

    def get_forecast(self, region: str, hours: int = 24) -> List[CarbonIntensity]:
        """Get carbon intensity forecast from WattTime."""
        if not self.token:
            logger.warning("WattTime token not available, using fallback forecast")
            return self._get_fallback_forecast(region, hours)

        headers = {"Authorization": f"Bearer {self.token}"}
        ba = WATTTIME_REGION_MAPPINGS.get(region, "DE")

        try:
            response = requests.get(
                f"{self.BASE_URL}/forecast", headers=headers, params={"ba": ba, "horizon_hours": hours}, timeout=30
            )
            response.raise_for_status()

            data = response.json()
            forecasts = []

            for item in data.get("data", []):
                forecasts.append(
                    CarbonIntensity(
                        value=item["value"],
                        timestamp=parse_iso_datetime(item["point_time"]),
                        region=region,
                        source="watttime",
                    )
                )

            return forecasts
        except Exception as e:
            logger.error(f"Error getting WattTime forecast: {e}")
            return self._get_fallback_forecast(region, hours)

    def _get_fallback_intensity(self, region: str) -> CarbonIntensity:
        """Get fallback intensity when API fails."""
        return CarbonIntensity(
            value=FALLBACK_CARBON_VALUES.get(region, 475), timestamp=datetime.now(), region=region, source="fallback"
        )

    def _get_fallback_forecast(self, region: str, hours: int) -> List[CarbonIntensity]:
        """Generate fallback forecast when API fails."""
        base_value = self._get_fallback_intensity(region).value
        forecasts = []

        for hour in range(hours):
            # Simple sine wave pattern to simulate daily variation
            variation = math.sin((hour / 24) * 2 * math.pi) * 50

            forecasts.append(
                CarbonIntensity(
                    value=base_value + variation,
                    timestamp=datetime.now() + timedelta(hours=hour),
                    region=region,
                    source="fallback_forecast",
                )
            )

        return forecasts


class ElectricityMapClient(CarbonAPIClient):
    """electricityMap API client implementation."""

    BASE_URL = "https://api.electricitymap.org/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELECTRICITYMAP_API_KEY")

    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity from electricityMap."""
        if not self.api_key:
            logger.warning("ElectricityMap API key not available, using fallback")
            return self._get_fallback_intensity(region)

        headers = {"auth-token": self.api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
            response = requests.get(
                f"{self.BASE_URL}/carbon-intensity/latest", headers=headers, params={"zone": zone}, timeout=30
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
        """Get carbon intensity forecast from electricityMap."""
        if not self.api_key:
            logger.warning("ElectricityMap API key not available, using fallback forecast")
            return self._get_fallback_forecast(region, hours)

        headers = {"auth-token": self.api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
            # ElectricityMap forecast endpoint
            params = {"zone": zone, "hours": str(hours)}
            response = requests.get(
                f"{self.BASE_URL}/carbon-intensity/forecast", headers=headers, params=params, timeout=30
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
            value=FALLBACK_CARBON_VALUES.get(region, 475), timestamp=datetime.now(), region=region, source="fallback"
        )

    def _get_fallback_forecast(self, region: str, hours: int) -> List[CarbonIntensity]:
        """Generate fallback forecast when API fails."""
        base_value = self._get_fallback_intensity(region).value
        forecasts = []

        for hour in range(hours):
            # Simple sine wave pattern to simulate daily variation
            # Peak during day (hour 12), low at night (hour 0 and 24)
            variation = math.sin((hour - 6) / 24 * 2 * math.pi) * 50

            forecasts.append(
                CarbonIntensity(
                    value=max(0, base_value + variation),  # Ensure non-negative
                    timestamp=datetime.now() + timedelta(hours=hour),
                    region=region,
                    source="fallback_forecast",
                )
            )

        return forecasts


class CarbonIntensityClient:
    """Main client that abstracts different providers."""

    def __init__(self, provider: Optional[str] = None):
        provider = provider or os.getenv("CARBON_API_PROVIDER", "electricitymap")

        self.client: Union[WattTimeClient, ElectricityMapClient]

        if provider == "watttime":
            self.client = WattTimeClient()
        elif provider == "electricitymap":
            self.client = ElectricityMapClient()
        else:
            # Default to ElectricityMap
            logger.warning(f"Unknown provider: {provider}, defaulting to ElectricityMap")
            self.client = ElectricityMapClient()

    def get_current_intensity(self, region: str) -> float:
        """Get current carbon intensity value."""
        try:
            intensity = self.client.get_current_intensity(region)
            logger.info(f"Current carbon intensity for {region}: {intensity.value} gCO2/kWh from {intensity.source}")
            return intensity.value
        except Exception as e:
            logger.error(f"Failed to get carbon intensity: {e}")
            # Return average EU grid intensity as fallback
            return 475.0

    def get_forecast(self, region: str, hours: int = 24) -> List[float]:
        """Get carbon intensity forecast values."""
        try:
            forecasts = self.client.get_forecast(region, hours)
            values = [f.value for f in forecasts]
            logger.info(f"Got {len(values)} hour forecast for {region}")
            return values
        except Exception as e:
            logger.error(f"Failed to get carbon forecast: {e}")
            # Return flat forecast as fallback
            return [475.0] * hours

    def get_best_hours(self, region: str, hours_needed: int = 8, forecast_hours: int = 24) -> List[int]:
        """Get the best hours (lowest carbon intensity) within the forecast period."""
        try:
            forecasts = self.client.get_forecast(region, forecast_hours)

            # Sort by carbon intensity value
            sorted_forecasts = sorted(enumerate(forecasts), key=lambda x: x[1].value)

            # Get the hours with lowest intensity
            best_hours = [hour for hour, _ in sorted_forecasts[:hours_needed]]
            best_hours.sort()  # Return in chronological order

            logger.info(f"Best {hours_needed} hours for {region}: {best_hours}")
            return best_hours

        except Exception as e:
            logger.error(f"Failed to get best hours: {e}")
            # Return first hours as fallback
            return list(range(hours_needed))

    def should_run_now(self, region: str, threshold: float = 400) -> bool:
        """Check if current carbon intensity is below threshold."""
        try:
            current_intensity = self.get_current_intensity(region)
            should_run = current_intensity < threshold

            logger.info(
                f"Should run now in {region}? {should_run} (current: {current_intensity}, threshold: {threshold})"
            )
            return should_run

        except Exception as e:
            logger.error(f"Failed to check if should run: {e}")
            # Default to running if we can't determine
            return True
