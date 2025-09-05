"""
Carbon intensity API client for real-time carbon data.
Supports multiple providers: WattTime, electricityMap
"""

import os
import requests
import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Union, Dict, Any, Tuple
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

# EC2 Instance Power Consumption Estimates (Watts)
# Based on research studies and CPU/memory specifications
EC2_POWER_CONSUMPTION = {
    # T3 instances (Burstable Performance)
    "t3.nano": 1.5,      # 2 vCPU, 0.5 GiB RAM
    "t3.micro": 2.5,     # 2 vCPU, 1 GiB RAM
    "t3.small": 5.0,     # 2 vCPU, 2 GiB RAM
    "t3.medium": 10.0,   # 2 vCPU, 4 GiB RAM
    "t3.large": 20.0,    # 2 vCPU, 8 GiB RAM
    "t3.xlarge": 40.0,   # 4 vCPU, 16 GiB RAM
    "t3.2xlarge": 80.0,  # 8 vCPU, 32 GiB RAM
    
    # M5 instances (General Purpose)
    "m5.large": 25.0,    # 2 vCPU, 8 GiB RAM
    "m5.xlarge": 50.0,   # 4 vCPU, 16 GiB RAM
    "m5.2xlarge": 100.0, # 8 vCPU, 32 GiB RAM
    "m5.4xlarge": 200.0, # 16 vCPU, 64 GiB RAM
    
    # C5 instances (Compute Optimized)
    "c5.large": 30.0,    # 2 vCPU, 4 GiB RAM
    "c5.xlarge": 60.0,   # 4 vCPU, 8 GiB RAM
    "c5.2xlarge": 120.0, # 8 vCPU, 16 GiB RAM
    "c5.4xlarge": 240.0, # 16 vCPU, 32 GiB RAM
    
    # R5 instances (Memory Optimized)
    "r5.large": 35.0,    # 2 vCPU, 16 GiB RAM
    "r5.xlarge": 70.0,   # 4 vCPU, 32 GiB RAM
    "r5.2xlarge": 140.0, # 8 vCPU, 64 GiB RAM
}

# CPU Utilization factors for realistic power consumption
# T3 instances have baseline performance levels
T3_CPU_BASELINE_UTILIZATION = {
    "t3.nano": 0.05,     # 5% baseline
    "t3.micro": 0.10,    # 10% baseline  
    "t3.small": 0.20,    # 20% baseline
    "t3.medium": 0.20,   # 20% baseline
    "t3.large": 0.30,    # 30% baseline
    "t3.xlarge": 0.40,   # 40% baseline
    "t3.2xlarge": 0.54,  # 54% baseline
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
        if username and password:
            self.username = username
            self.password = password
        else:
            # Try environment variables first, then secrets manager
            self.username = username or os.getenv("WATTTIME_USERNAME")
            self.password = password or os.getenv("WATTTIME_PASSWORD")
            
            # Simplified: just use environment variables
            if not self.username or not self.password:
                logger.warning("WattTime credentials not provided. Set WATTTIME_USERNAME and WATTTIME_PASSWORD environment variables.")
        
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
        if api_key:
            self.api_key = api_key
        else:
            # Try environment variable first, then secrets manager
            self.api_key = os.getenv("ELECTRICITYMAP_API_KEY")
            # Simplified: just use environment variable
            if not self.api_key:
                logger.warning("ElectricityMap API key not provided. Set ELECTRICITYMAP_API_KEY environment variable.")
                self.api_key = None

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


@dataclass
class InstanceEnergyData:
    """Complete energy and carbon data for an EC2 instance"""
    instance_id: str
    instance_type: str
    power_consumption_watts: float
    energy_consumption_kwh: float
    carbon_emissions_grams: float
    carbon_emissions_kg: float
    carbon_intensity_gco2_kwh: float
    runtime_hours: float
    cost_usd: float
    region: str
    timestamp: datetime


class EC2EnergyCalculator:
    """Calculate energy consumption and carbon emissions for EC2 instances"""
    
    def __init__(self, carbon_client: Optional[CarbonIntensityClient] = None):
        self.carbon_client = carbon_client or CarbonIntensityClient()
    
    def get_instance_power_consumption(self, instance_type: str, cpu_utilization: Optional[float] = None) -> float:
        """Get power consumption for instance type in watts"""
        
        base_power = EC2_POWER_CONSUMPTION.get(instance_type, 10.0)
        
        # Apply CPU utilization factor for T3 instances if provided
        if cpu_utilization is not None and instance_type.startswith('t3.'):
            baseline_utilization = T3_CPU_BASELINE_UTILIZATION.get(instance_type, 0.2)
            
            # Power scales with utilization above baseline
            if cpu_utilization > baseline_utilization:
                utilization_factor = 1.0 + (cpu_utilization - baseline_utilization) * 2
                return base_power * utilization_factor
            else:
                return base_power * 0.7  # Idle power is lower
        
        return base_power
    
    def calculate_energy_consumption(self, instance_type: str, runtime_hours: float, 
                                   cpu_utilization: Optional[float] = None) -> float:
        """Calculate energy consumption in kWh"""
        
        power_watts = self.get_instance_power_consumption(instance_type, cpu_utilization)
        energy_kwh = (power_watts * runtime_hours) / 1000  # Convert watts*hours to kWh
        
        return energy_kwh
    
    def calculate_carbon_emissions(self, energy_kwh: float, carbon_intensity: float) -> Tuple[float, float]:
        """Calculate carbon emissions in grams and kg"""
        
        emissions_grams = energy_kwh * carbon_intensity
        emissions_kg = emissions_grams / 1000
        
        return emissions_grams, emissions_kg
    
    def get_complete_instance_analysis(self, instance_id: str, instance_type: str, 
                                     runtime_hours: float, region: str,
                                     cost_usd: Optional[float] = None,
                                     cpu_utilization: Optional[float] = None) -> InstanceEnergyData:
        """Get complete energy and carbon analysis for an instance"""
        
        # Get current carbon intensity
        carbon_intensity = self.carbon_client.get_current_intensity(region)
        
        # Calculate power consumption
        power_watts = self.get_instance_power_consumption(instance_type, cpu_utilization)
        
        # Calculate energy consumption
        energy_kwh = self.calculate_energy_consumption(instance_type, runtime_hours, cpu_utilization)
        
        # Calculate carbon emissions
        emissions_grams, emissions_kg = self.calculate_carbon_emissions(energy_kwh, carbon_intensity)
        
        # Estimate cost if not provided
        if cost_usd is None:
            # Rough AWS pricing estimates per hour
            pricing = {
                't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
                't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328
            }
            hourly_rate = pricing.get(instance_type, 0.05)
            cost_usd = runtime_hours * hourly_rate
        
        return InstanceEnergyData(
            instance_id=instance_id,
            instance_type=instance_type,
            power_consumption_watts=power_watts,
            energy_consumption_kwh=energy_kwh,
            carbon_emissions_grams=emissions_grams,
            carbon_emissions_kg=emissions_kg,
            carbon_intensity_gco2_kwh=carbon_intensity,
            runtime_hours=runtime_hours,
            cost_usd=cost_usd,
            region=region,
            timestamp=datetime.now()
        )
    
    def compare_carbon_apis(self, region: str) -> Dict[str, Any]:
        """Compare carbon intensity from different APIs"""
        
        comparison = {
            'region': region,
            'timestamp': datetime.now().isoformat(),
            'apis': {}
        }
        
        # ElectricityMap
        try:
            electricitymap_intensity = self.carbon_client.get_current_intensity(region)
            comparison['apis']['electricitymap'] = {
                'intensity_gco2_kwh': electricitymap_intensity,
                'status': 'success',
                'source': 'electricitymap'
            }
        except Exception as e:
            comparison['apis']['electricitymap'] = {
                'intensity_gco2_kwh': None,
                'status': 'failed',
                'error': str(e)
            }
        
        # WattTime (if available)
        try:
            watttime_client = WattTimeClient()
            watttime_intensity = watttime_client.get_current_intensity(region)
            comparison['apis']['watttime'] = {
                'intensity_gco2_kwh': watttime_intensity.value,
                'status': 'success',
                'source': 'watttime'
            }
        except Exception as e:
            comparison['apis']['watttime'] = {
                'intensity_gco2_kwh': None,
                'status': 'failed', 
                'error': str(e)
            }
        
        # Fallback
        fallback_intensity = FALLBACK_CARBON_VALUES.get(region, 300)
        comparison['apis']['fallback'] = {
            'intensity_gco2_kwh': fallback_intensity,
            'status': 'success',
            'source': 'fallback'
        }
        
        # Calculate differences
        valid_values = [api['intensity_gco2_kwh'] for api in comparison['apis'].values() 
                       if api['intensity_gco2_kwh'] is not None]
        
        if len(valid_values) > 1:
            comparison['analysis'] = {
                'min_intensity': min(valid_values),
                'max_intensity': max(valid_values),
                'average_intensity': sum(valid_values) / len(valid_values),
                'variance': max(valid_values) - min(valid_values),
                'variance_percentage': ((max(valid_values) - min(valid_values)) / min(valid_values)) * 100
            }
        
        return comparison
    
    def calculate_optimization_savings(self, baseline_data: InstanceEnergyData, 
                                     optimized_data: InstanceEnergyData) -> Dict[str, Any]:
        """Calculate savings from optimization"""
        
        cost_savings = baseline_data.cost_usd - optimized_data.cost_usd
        carbon_savings = baseline_data.carbon_emissions_kg - optimized_data.carbon_emissions_kg
        energy_savings = baseline_data.energy_consumption_kwh - optimized_data.energy_consumption_kwh
        
        cost_savings_pct = (cost_savings / baseline_data.cost_usd) * 100 if baseline_data.cost_usd > 0 else 0
        carbon_savings_pct = (carbon_savings / baseline_data.carbon_emissions_kg) * 100 if baseline_data.carbon_emissions_kg > 0 else 0
        energy_savings_pct = (energy_savings / baseline_data.energy_consumption_kwh) * 100 if baseline_data.energy_consumption_kwh > 0 else 0
        
        return {
            'cost_savings_usd': round(cost_savings, 4),
            'carbon_savings_kg': round(carbon_savings, 4),
            'energy_savings_kwh': round(energy_savings, 4),
            'cost_savings_percentage': round(cost_savings_pct, 2),
            'carbon_savings_percentage': round(carbon_savings_pct, 2),
            'energy_savings_percentage': round(energy_savings_pct, 2),
            'baseline': {
                'cost_usd': baseline_data.cost_usd,
                'carbon_kg': baseline_data.carbon_emissions_kg,
                'energy_kwh': baseline_data.energy_consumption_kwh,
                'runtime_hours': baseline_data.runtime_hours
            },
            'optimized': {
                'cost_usd': optimized_data.cost_usd,
                'carbon_kg': optimized_data.carbon_emissions_kg,
                'energy_kwh': optimized_data.energy_consumption_kwh,
                'runtime_hours': optimized_data.runtime_hours
            }
        }
