"""
Centralized configuration settings for Carbon-Aware FinOps.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AWSConfig:
    """AWS-specific configuration."""
    region: str = 'eu-central-1'
    profile: str = 'carbon-finops-sandbox'
    
    # DynamoDB table names
    state_table: str = 'carbon-aware-finops-state'
    rightsizing_table: str = 'carbon-aware-finops-rightsizing'
    costs_table: str = 'carbon-aware-finops-costs'
    
    # CloudWatch settings
    cloudwatch_namespace: str = 'CarbonAwareFinOps'
    log_group: str = '/aws/carbon-aware-finops'


@dataclass
class CarbonConfig:
    """Carbon intensity configuration."""
    
    # Carbon thresholds by region (gCO2/kWh)
    thresholds: Dict[str, float] = None
    
    # API providers
    primary_provider: str = 'electricitymap'  # 'electricitymap' or 'watttime'
    fallback_provider: str = 'watttime'
    
    # API keys (loaded from environment)
    electricitymap_api_key: Optional[str] = None
    watttime_username: Optional[str] = None
    watttime_password: Optional[str] = None
    
    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {
                'eu-central-1': 300,    # Germany
                'eu-west-1': 250,       # Ireland  
                'eu-west-2': 200,       # UK
                'eu-west-3': 90,        # France (nuclear)
                'eu-north-1': 40,       # Sweden (hydro)
                'us-east-1': 450,       # US East
                'us-west-2': 350,       # US West
            }
        
        # Load API keys from secrets manager (lazy loading)
        self._electricitymap_api_key = None
        self._watttime_username = None
        self._watttime_password = None
    
    @property
    def electricitymap_api_key(self) -> Optional[str]:
        """Get ElectricityMap API key from secrets manager."""
        if self._electricitymap_api_key is None:
            from src.utils.secrets_manager import get_secret
            self._electricitymap_api_key = get_secret('electricitymap_api_key')
        return self._electricitymap_api_key
    
    @property
    def watttime_username(self) -> Optional[str]:
        """Get WattTime username from secrets manager."""
        if self._watttime_username is None:
            from src.utils.secrets_manager import get_secret
            self._watttime_username = get_secret('watttime_username')
        return self._watttime_username
    
    @property
    def watttime_password(self) -> Optional[str]:
        """Get WattTime password from secrets manager."""
        if self._watttime_password is None:
            from src.utils.secrets_manager import get_secret
            self._watttime_password = get_secret('watttime_password')
        return self._watttime_password


@dataclass
class SchedulingConfig:
    """Instance scheduling configuration."""
    
    # Default schedules
    always_on_schedule: str = '24/7 Always Running'
    office_hours_schedule: str = 'Office Hours + Weekend Shutdown'
    extended_hours_schedule: str = 'Extended Development Hours'
    carbon_aware_schedule: str = 'Carbon-Aware 24/7'
    
    # Timing settings
    default_timezone: str = 'Europe/Berlin'
    startup_buffer_minutes: int = 5  # Start instances 5 min before needed
    
    # Cost estimation (hourly rates in USD)
    instance_pricing: Dict[str, float] = None
    
    def __post_init__(self):
        if self.instance_pricing is None:
            self.instance_pricing = {
                't3.micro': 0.0104,
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                't3.xlarge': 0.1664,
                't3.2xlarge': 0.3328,
            }


@dataclass
class RightsizingConfig:
    """Rightsizing analysis configuration."""
    
    # CPU utilization thresholds (%)
    downsize_cpu_p95_threshold: float = 40.0
    downsize_cpu_max_threshold: float = 60.0
    upsize_cpu_avg_threshold: float = 80.0
    upsize_cpu_p95_threshold: float = 90.0
    
    # Analysis periods
    default_analysis_days: int = 14
    minimum_datapoints: int = 24  # Minimum hours of data needed
    
    # Power consumption estimates (kW) for carbon calculations
    power_consumption: Dict[str, float] = None
    
    def __post_init__(self):
        if self.power_consumption is None:
            self.power_consumption = {
                't3.micro': 0.01,
                't3.small': 0.02,
                't3.medium': 0.04,
                't3.large': 0.08,
                't3.xlarge': 0.16,
                't3.2xlarge': 0.32,
            }


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    
    # Server settings
    host: str = '127.0.0.1'
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
    
    aws: AWSConfig = None
    carbon: CarbonConfig = None
    scheduling: SchedulingConfig = None  
    rightsizing: RightsizingConfig = None
    dashboard: DashboardConfig = None
    
    # Environment
    environment: str = 'development'
    project_name: str = 'carbon-aware-finops'
    
    def __post_init__(self):
        # Initialize sub-configs if not provided
        if self.aws is None:
            self.aws = AWSConfig()
        if self.carbon is None:
            self.carbon = CarbonConfig()
        if self.scheduling is None:
            self.scheduling = SchedulingConfig()
        if self.rightsizing is None:
            self.rightsizing = RightsizingConfig()
        if self.dashboard is None:
            self.dashboard = DashboardConfig()
        
        # Override from environment variables
        self.environment = os.getenv('ENVIRONMENT', self.environment)
        self.project_name = os.getenv('PROJECT_NAME', self.project_name)
        self.aws.region = os.getenv('AWS_REGION', self.aws.region)
        self.aws.profile = os.getenv('AWS_PROFILE', self.aws.profile)


# Global settings instance
settings = Settings()


def get_carbon_threshold(region: str) -> float:
    """Get carbon threshold for a specific region."""
    return settings.carbon.thresholds.get(region, 400.0)  # Default fallback


def get_instance_pricing(instance_type: str) -> float:
    """Get hourly pricing for an instance type."""
    return settings.scheduling.instance_pricing.get(instance_type, 0.05)  # Default fallback


def get_power_consumption(instance_type: str) -> float:
    """Get power consumption estimate for an instance type."""
    return settings.rightsizing.power_consumption.get(instance_type, 0.05)  # Default fallback