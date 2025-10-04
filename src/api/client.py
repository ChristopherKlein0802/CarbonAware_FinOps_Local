"""
Unified API Client for Carbon-Aware FinOps Dashboard
Facade pattern for all external API integrations
"""

from typing import Optional, Dict, List

from .electricity import ElectricityMapsAPI
from .aws import AWSAPIClient
from .boavizta import BoaviztaAPI
from ..models.carbon import CarbonIntensity, PowerConsumption
from ..models.aws import AWSCostData
from ..utils.logging import get_performance_logger

logger = get_performance_logger("unified_api_client")


class UnifiedAPIClient:
    """
    Unified client for all external APIs - Clean, professional implementation

    Features:
    - ElectricityMap for carbon intensity (30min cache)
    - Boavizta for power consumption (24h cache)
    - AWS Cost Explorer for billing (1h cache)
    - NO FALLBACKS - Academic integrity maintained
    """

    def __init__(self, aws_profile: str = None):
        """Initialize with optional AWS profile"""
        self.electricity_api = ElectricityMapsAPI()
        self.aws_api = AWSAPIClient(aws_profile)
        self.boavizta_api = BoaviztaAPI()

    def get_current_carbon_intensity(self, region: str = "eu-central-1") -> Optional[CarbonIntensity]:
        """Get current carbon intensity from ElectricityMap with optimized 2-hour caching

        Scientific rationale: ElectricityMap updates every 15-60 minutes.
        2-hour cache reduces API costs while maintaining reasonable accuracy.
        """
        return self.electricity_api.get_current_carbon_intensity(region)

    def get_carbon_intensity_24h(self, region: str = "eu-central-1") -> Optional[List[Dict]]:
        """Get 24-hour historical carbon intensity from ElectricityMap with daily caching

        Scientific rationale: Historical data doesn't change, so daily caching is appropriate.
        Uses real API data instead of hard-coded patterns for academic integrity.

        Returns: List of hourly data points with timestamp and carbon intensity
        """
        return self.electricity_api.get_carbon_intensity_24h(region)

    def get_self_collected_24h_data(self, region: str = "eu-central-1") -> Optional[List[Dict]]:
        """Optional hourly fallback controlled via `ENABLE_HOURLY_CARBON_COLLECTION`."""
        return self.electricity_api.get_self_collected_24h_data(region)

    def get_power_consumption(self, instance_type: str) -> Optional[PowerConsumption]:
        """Get power consumption from Boavizta API with 7-day caching"""
        return self.boavizta_api.get_power_consumption(instance_type)

    def get_instance_pricing(self, instance_type: str, region: str = "eu-central-1") -> Optional[float]:
        """Get AWS EC2 instance pricing from AWS Pricing API with 7-day caching"""
        return self.aws_api.get_instance_pricing(instance_type, region)

    def get_monthly_costs(self) -> Optional[AWSCostData]:
        """Get monthly AWS costs for validation with 6-hour caching"""
        return self.aws_api.get_monthly_costs()

    def get_hourly_costs(self, hours: int = 48) -> Optional[list[dict]]:
        """Get recent hourly EC2 costs from AWS Cost Explorer."""
        return self.aws_api.get_hourly_costs(hours)


# Global instance
unified_api_client = UnifiedAPIClient()
