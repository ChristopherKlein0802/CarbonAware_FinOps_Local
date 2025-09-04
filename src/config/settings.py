"""
Centralized configuration settings for Carbon-Aware FinOps.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AWSConfig:
    """AWS-specific configuration."""

    region: str = "eu-central-1"
    profile: str = "carbon-finops-sandbox"

    # Single DynamoDB table for results
    results_table: str = "carbon-aware-finops-results"

    # CloudWatch settings
    cloudwatch_namespace: str = "CarbonAwareFinOps"
    log_group: str = "/aws/carbon-aware-finops"


@dataclass
class CarbonConfig:
    """Carbon intensity configuration."""

    # Carbon thresholds by region (gCO2/kWh)
    thresholds: Optional[Dict[str, float]] = None

    # API providers
    primary_provider: str = "electricitymap"  # 'electricitymap' or 'watttime'
    fallback_provider: str = "watttime"

    # API keys will be loaded via properties from secrets manager

    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {
                "eu-central-1": 300,  # Germany
                "eu-west-1": 250,  # Ireland
                "eu-west-2": 200,  # UK
                "eu-west-3": 90,  # France (nuclear)
                "eu-north-1": 40,  # Sweden (hydro)
                "us-east-1": 450,  # US East
                "us-west-2": 350,  # US West
            }

        # Load API keys from secrets manager (lazy loading)
        self._electricitymap_api_key: Optional[str] = None
        self._watttime_username: Optional[str] = None
        self._watttime_password: Optional[str] = None

    @property
    def electricitymap_api_key(self) -> Optional[str]:
        """Get ElectricityMap API key from environment variable."""
        if self._electricitymap_api_key is None:
            self._electricitymap_api_key = os.getenv("ELECTRICITYMAP_API_KEY")
        return self._electricitymap_api_key

    @property
    def watttime_username(self) -> Optional[str]:
        """Get WattTime username from environment variable."""
        if self._watttime_username is None:
            self._watttime_username = os.getenv("WATTTIME_USERNAME")
        return self._watttime_username

    @property
    def watttime_password(self) -> Optional[str]:
        """Get WattTime password from environment variable."""
        if self._watttime_password is None:
            self._watttime_password = os.getenv("WATTTIME_PASSWORD")
        return self._watttime_password


@dataclass
class SchedulingConfig:
    """Instance scheduling configuration."""

    # Default schedules
    always_on_schedule: str = "24/7 Always Running"
    office_hours_schedule: str = "Office Hours + Weekend Shutdown"
    extended_hours_schedule: str = "Extended Development Hours"
    carbon_aware_schedule: str = "Carbon-Aware 24/7"

    # Timing settings
    default_timezone: str = "Europe/Berlin"
    startup_buffer_minutes: int = 5  # Start instances 5 min before needed

    # Cost estimation (hourly rates in USD)
    instance_pricing: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.instance_pricing is None:
            self.instance_pricing = {
                "t3.micro": 0.0104,
                "t3.small": 0.0208,
                "t3.medium": 0.0416,
                "t3.large": 0.0832,
                "t3.xlarge": 0.1664,
                "t3.2xlarge": 0.3328,
            }




@dataclass
class DashboardConfig:
    """Dashboard configuration."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8050
    debug: bool = True

    # Update intervals (milliseconds)
    refresh_interval: int = 60 * 1000  # 1 minute

    # Chart settings
    chart_days_back: int = 30
    max_chart_points: int = 1000


@dataclass
class Settings:
    """Main settings container."""

    aws: Optional[AWSConfig] = None
    carbon: Optional[CarbonConfig] = None
    scheduling: Optional[SchedulingConfig] = None
    dashboard: Optional[DashboardConfig] = None

    # Environment
    environment: str = "development"
    project_name: str = "carbon-aware-finops"

    def __post_init__(self):
        # Initialize sub-configs if not provided
        if self.aws is None:
            self.aws = AWSConfig()
        if self.carbon is None:
            self.carbon = CarbonConfig()
        if self.scheduling is None:
            self.scheduling = SchedulingConfig()
        if self.dashboard is None:
            self.dashboard = DashboardConfig()

        # Override from environment variables
        self.environment = os.getenv("ENVIRONMENT", self.environment)
        self.project_name = os.getenv("PROJECT_NAME", self.project_name)
        self.aws.region = os.getenv("AWS_REGION", self.aws.region)
        self.aws.profile = os.getenv("AWS_PROFILE", self.aws.profile)


# Global settings instance
settings = Settings()


def get_carbon_threshold(region: str) -> float:
    """Get carbon threshold for a specific region."""
    if settings.carbon and settings.carbon.thresholds:
        return settings.carbon.thresholds.get(region, 400.0)
    return 400.0  # Default fallback


def get_instance_pricing(instance_type: str) -> float:
    """Get hourly pricing for an instance type."""
    if settings.scheduling and settings.scheduling.instance_pricing:
        return settings.scheduling.instance_pricing.get(instance_type, 0.05)
    return 0.05  # Default fallback


