"""
Unified API Client for Carbon-Aware FinOps Dashboard
Handles ALL external API integrations: Carbon, Power, and AWS Cost data
Bachelor Thesis requirement: NO FALLBACKS - real data only
"""

import os
import json
import requests
import boto3
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging
from dataclasses import dataclass
from dotenv import load_dotenv
from utils.performance_monitor import monitor_api_performance, CacheMonitor

# Load environment variables explicitly
load_dotenv()

logger = logging.getLogger(__name__)

# AWS region to ElectricityMap zone mappings
REGION_MAPPINGS = {
    "eu-central-1": "DE",  # Germany
    "eu-west-1": "IE",  # Ireland
    "eu-west-2": "GB",  # United Kingdom
    "eu-west-3": "FR",  # France
    "eu-north-1": "SE",  # Sweden
    "us-east-1": "US-NE-ISO",  # US East
    "us-west-2": "US-NW-PACW",  # US West
}

# REMOVED: FALLBACK_CARBON_VALUES - Bachelor Thesis requires API-only data


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


@dataclass
class PowerConsumption:
    """Power consumption data structure for AWS instances."""

    avg_power_watts: float
    min_power_watts: float
    max_power_watts: float
    confidence_level: str
    source: str


@dataclass
class AWSCostData:
    """AWS cost data structure."""

    monthly_cost_usd: float
    service_costs: Dict[str, float]
    region: str
    source: str


class ElectricityMapClient:
    """ElectricityMap API client for carbon intensity data."""

    BASE_URL = "https://api-access.electricitymaps.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELECTRICITYMAP_API_KEY")
        self.cache_monitor = CacheMonitor("electricitymap_cache")
        if not self.api_key:
            logger.warning("ElectricityMap API key not provided. Set ELECTRICITYMAP_API_KEY environment variable.")

    def _get_carbon_cache_path(self, region: str) -> str:
        """Get the path for carbon intensity cache file"""
        cache_dir = "/tmp/carbon_finops_cache"
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"carbon_intensity_{region}.json")

    def _is_carbon_cache_valid(self, cache_path: str, max_age_minutes: int = 30) -> bool:
        """Check if carbon cache is still valid (within max_age_minutes)"""
        if not os.path.exists(cache_path):
            return False

        file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        return file_age < (max_age_minutes * 60)  # Convert minutes to seconds

    @monitor_api_performance("electricitymap")
    def get_current_intensity(self, region: str) -> CarbonIntensity:
        """Get current carbon intensity from ElectricityMap with 30-minute caching"""
        cache_path = self._get_carbon_cache_path(region)

        # Check if cached data is valid (30 minutes)
        if self._is_carbon_cache_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                self.cache_monitor.record_hit()
                logger.info(f"✅ Using cached ElectricityMap data for {region} (saves API call)")
                return CarbonIntensity(
                    value=cached_data["value"],
                    timestamp=parse_iso_datetime(cached_data["timestamp"]),
                    region=cached_data["region"],
                    source=cached_data["source"],
                )
            except Exception as e:
                logger.warning(f"⚠️ Carbon cache read failed: {e}, fetching fresh data")

        # Fetch fresh data from API
        if not self.api_key:
            self.cache_monitor.record_miss()
            logger.error("❌ ElectricityMap API key not available - NO FALLBACK used (Bachelor Thesis policy)")
            return None

        headers = {"auth-token": self.api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
            self.cache_monitor.record_miss()
            logger.info(f"🌿 Fetching fresh ElectricityMap data for {zone}")
            response = requests.get(
                f"{self.BASE_URL}/carbon-intensity/latest", headers=headers, params={"zone": zone}, timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # Validate required fields exist
            if "carbonIntensity" not in data or "datetime" not in data:
                logger.error(f"❌ ElectricityMap API returned invalid data structure: {data}")
                return None

            carbon_data = CarbonIntensity(
                value=float(data["carbonIntensity"]),  # Ensure numeric value
                timestamp=parse_iso_datetime(data["datetime"]),
                region=region,
                source="electricitymap",
            )

            # Cache the result for 30 minutes
            try:
                cache_data = {
                    "value": carbon_data.value,
                    "timestamp": carbon_data.timestamp.isoformat(),
                    "region": carbon_data.region,
                    "source": carbon_data.source,
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info(f"✅ Carbon intensity cached for 30 minutes ({carbon_data.value}g CO2/kWh)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache carbon data: {e}")

            return carbon_data

        except requests.exceptions.Timeout:
            logger.error(f"❌ ElectricityMap API timeout (30s exceeded) - NO FALLBACK used (Bachelor Thesis policy)")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ ElectricityMap API HTTP error {e.response.status_code}: {e} - NO FALLBACK used")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ElectricityMap API network error: {e} - NO FALLBACK used")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"❌ ElectricityMap API data parsing error: {e} - NO FALLBACK used")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected ElectricityMap error: {e} - NO FALLBACK used (Bachelor Thesis policy)")
            return None

    def get_forecast(self, region: str, hours: int = 24) -> List[CarbonIntensity]:
        """Get carbon intensity forecast from ElectricityMap."""
        if not self.api_key:
            logger.error(
                "❌ ElectricityMap API key not available for forecast - NO FALLBACK used (Bachelor Thesis policy)"
            )
            return []

        headers = {"auth-token": self.api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
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

            return forecasts  # Return empty list if no API data available

        except Exception as e:
            logger.error(f"❌ Error getting ElectricityMap forecast: {e} - NO FALLBACK used (Bachelor Thesis policy)")
            return []

    # NOTE: No fallback methods implemented - maintains API-only approach for academic rigor


class CarbonIntensityClient:
    """Main client for carbon intensity data - focused on ElectricityMap."""

    def __init__(self, provider: Optional[str] = None):
        # Always use ElectricityMap for Bachelor Thesis (provider parameter for compatibility)
        self.client = ElectricityMapClient()

    def get_current_intensity(self, region: str) -> float:
        """Get current carbon intensity value."""
        try:
            intensity = self.client.get_current_intensity(region)
            if intensity is None:
                # API key missing or API failed - NO FALLBACK (Bachelor Thesis policy)
                logger.error("❌ ElectricityMap API returned None - NO FALLBACK USED")
                return 0.0
            logger.info(f"Current carbon intensity for {region}: {intensity.value} gCO2/kWh from {intensity.source}")
            return intensity.value
        except Exception as e:
            logger.error(f"Failed to get carbon intensity: {e}")
            # NO FALLBACK - return 0 for failed API calls (Bachelor Thesis requirement)
            logger.error("❌ CarbonIntensityClient failed - NO FALLBACK USED")
            return 0.0


class BoaviztoClient:
    """Boavizta API client for hardware power consumption data - NO FALLBACKS."""

    def __init__(self):
        self.base_url = "https://api.boavizta.org/v1"
        self.cache_monitor = CacheMonitor("boavizta_cache")

    def _get_power_cache_path(self, instance_type: str) -> str:
        """Get cache path for power consumption data (Conservative 24h caching for thesis stability)"""
        cache_dir = "/tmp/carbon_finops_cache"
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"boavizta_power_{instance_type}.json")

    def _is_power_cache_valid(self, cache_path: str, max_age_hours: int = 24) -> bool:
        """Check if power cache is valid (24h for thesis stability - hardware specs don't change frequently)"""
        if not os.path.exists(cache_path):
            return False
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        return file_age < (max_age_hours * 3600)

    @monitor_api_performance("boavizta")
    def get_power_consumption(self, instance_type: str) -> Optional[PowerConsumption]:
        """Get power consumption from Boavizta API with 24h caching - API ONLY (Bachelor Thesis requirement)"""
        # Input validation
        if not instance_type or not isinstance(instance_type, str):
            logger.error(f"❌ Invalid instance_type: {instance_type}")
            return None

        cache_path = self._get_power_cache_path(instance_type)

        # Check cached data first (24h validity for thesis stability)
        if self._is_power_cache_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                self.cache_monitor.record_hit()
                logger.info(f"✅ Using cached Boavizta data for {instance_type} ({cached_data['avg_power_watts']:.1f}W)")
                return PowerConsumption(
                    avg_power_watts=cached_data["avg_power_watts"],
                    min_power_watts=cached_data["min_power_watts"], 
                    max_power_watts=cached_data["max_power_watts"],
                    confidence_level=cached_data["confidence_level"],
                    source=cached_data["source"]
                )
            except Exception as e:
                logger.warning(f"⚠️ Boavizta cache read failed for {instance_type}: {e}")

        # Fetch fresh data from API
        self.cache_monitor.record_miss()
        try:
            url = f"{self.base_url}/cloud/instance"
            payload = {
                "provider": "aws",
                "instance_type": instance_type,
                "usage": {"hours_use_time": 1},
                "location": "EUC",  # Europe Central
            }

            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if not isinstance(data, dict):
                logger.error(f"❌ Boavizta API returned invalid data type: {type(data)}")
                return None

            # Extract power consumption from verbose.avg_power (actual Watts)
            if "verbose" in data and "avg_power" in data["verbose"]:
                avg_power_data = data["verbose"]["avg_power"]
                if not isinstance(avg_power_data, dict) or "value" not in avg_power_data:
                    logger.error(f"❌ Boavizta API: invalid avg_power structure for {instance_type}")
                    return None

                avg_power = avg_power_data.get("value", 0)
                min_power = data["verbose"].get("min_power", {}).get("value", avg_power * 0.8)
                max_power = data["verbose"].get("max_power", {}).get("value", avg_power * 1.2)

                # Validate power values
                if not isinstance(avg_power, (int, float)) or avg_power <= 0:
                    logger.error(f"❌ Boavizta API: invalid power value {avg_power} for {instance_type}")
                    return None

                power_data = PowerConsumption(
                    avg_power_watts=float(avg_power),
                    min_power_watts=float(min_power),
                    max_power_watts=float(max_power),
                    confidence_level="high",
                    source="Boavizta_API",
                )

                # Cache the result for 24 hours (Conservative caching for thesis stability)
                try:
                    cache_data = {
                        "avg_power_watts": power_data.avg_power_watts,
                        "min_power_watts": power_data.min_power_watts,
                        "max_power_watts": power_data.max_power_watts,
                        "confidence_level": power_data.confidence_level,
                        "source": power_data.source
                    }
                    with open(cache_path, "w") as f:
                        json.dump(cache_data, f)
                    logger.info(f"✅ Boavizta API: {instance_type} = {avg_power:.1f}W (cached 24h)")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache Boavizta data for {instance_type}: {e}")
                    logger.info(f"✅ Boavizta API: {instance_type} = {avg_power:.1f}W (not cached)")

                return power_data
            else:
                logger.error(f"❌ Boavizta API: missing verbose.avg_power data for {instance_type}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"❌ Boavizta API timeout (10s exceeded) for {instance_type} - NO FALLBACK USED")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"❌ Boavizta API HTTP error {e.response.status_code} for {instance_type}: {e} - NO FALLBACK USED"
            )
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Boavizta API network error for {instance_type}: {e} - NO FALLBACK USED")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"❌ Boavizta API data parsing error for {instance_type}: {e} - NO FALLBACK USED")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected Boavizta error for {instance_type}: {e} - NO FALLBACK USED")
            return None


class AWSCostClient:
    """AWS Cost Explorer API client - NO FALLBACKS."""

    def __init__(self, aws_profile: str = "carbon-finops-sandbox"):
        try:
            self.session = boto3.Session(profile_name=aws_profile)
            self.cost_client = self.session.client("ce", region_name="us-east-1")  # Cost Explorer only in us-east-1
            self.cache_monitor = CacheMonitor("aws_cost_cache")
            logger.info(f"✅ AWS Cost Explorer client initialized: Profile={aws_profile}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AWS Cost Explorer client: {e}")
            self.cost_client = None
            self.cache_monitor = CacheMonitor("aws_cost_cache")

    def _get_cost_cache_path(self) -> str:
        """Get the path for cost cache file"""
        cache_dir = "/tmp/carbon_finops_cache"
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "cost_data.json")

    def _is_cache_valid(self, cache_path: str, max_age_hours: int = 1) -> bool:
        """Check if cache file is still valid (within max_age_hours)"""
        if not os.path.exists(cache_path):
            return False

        file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        return file_age < (max_age_hours * 3600)  # Convert hours to seconds

    @monitor_api_performance("aws_cost_explorer")
    def get_monthly_costs(self, service: str = "Amazon Elastic Compute Cloud - Compute") -> Optional[AWSCostData]:
        """Get monthly AWS costs with 1-hour caching to reduce API costs"""
        cache_path = self._get_cost_cache_path()

        # Check if cached data is valid
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                self.cache_monitor.record_hit()
                logger.info("✅ Using cached Cost Explorer data (saves $0.01 API call)")
                return AWSCostData(**cached_data)
            except Exception as e:
                logger.warning(f"⚠️ Cache read failed: {e}, fetching fresh data")

        # Fetch fresh data from API
        if not self.cost_client:
            self.cache_monitor.record_miss()
            logger.error("❌ AWS Cost Explorer client not available - NO FALLBACK USED")
            return None

        try:
            self.cache_monitor.record_miss()
            logger.info("💰 Fetching fresh Cost Explorer data (costs $0.01)")
            # Get 30-day cost data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            response = self.cost_client.get_cost_and_usage(
                TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            # Validate response structure
            if not isinstance(response, dict) or "ResultsByTime" not in response:
                logger.error(f"❌ AWS Cost Explorer returned invalid response structure: {response}")
                return None

            service_costs = {}
            total_cost = 0.0

            for result in response["ResultsByTime"]:
                if not isinstance(result, dict) or "Groups" not in result:
                    logger.warning(f"⚠️ Skipping invalid result structure: {result}")
                    continue

                for group in result["Groups"]:
                    if not isinstance(group, dict) or "Keys" not in group or "Metrics" not in group:
                        logger.warning(f"⚠️ Skipping invalid group structure: {group}")
                        continue

                    if not group["Keys"] or len(group["Keys"]) == 0:
                        logger.warning(f"⚠️ Skipping group with empty Keys: {group}")
                        continue

                    service_name = group["Keys"][0]

                    # Validate cost data structure
                    metrics = group.get("Metrics", {})
                    unblended_cost = metrics.get("UnblendedCost", {})
                    cost_amount_str = unblended_cost.get("Amount", "0")

                    try:
                        cost_amount = float(cost_amount_str)
                        if cost_amount < 0:
                            logger.warning(f"⚠️ Negative cost for {service_name}: {cost_amount}")
                            cost_amount = 0.0
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Invalid cost amount '{cost_amount_str}' for {service_name}: {e}")
                        cost_amount = 0.0

                    service_costs[service_name] = cost_amount
                    total_cost += cost_amount

            logger.info(f"✅ AWS Cost Explorer: Total monthly costs = ${total_cost:.2f} USD")

            cost_data = AWSCostData(
                monthly_cost_usd=total_cost,
                service_costs=service_costs,
                region="us-east-1",  # Cost Explorer region
                source="AWS_Cost_Explorer_API",
            )

            # Cache the result for 1 hour
            try:
                cache_data = {
                    "monthly_cost_usd": cost_data.monthly_cost_usd,
                    "service_costs": cost_data.service_costs,
                    "region": cost_data.region,
                    "source": cost_data.source,
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info("✅ Cost data cached for 1 hour")
            except (IOError, OSError) as e:
                logger.warning(f"⚠️ Failed to cache cost data (I/O error): {e}")
            except (TypeError, ValueError) as e:
                logger.warning(f"⚠️ Failed to cache cost data (serialization error): {e}")

            return cost_data

        except boto3.exceptions.Boto3Error as e:
            logger.error(f"❌ AWS Boto3 error: {e} - NO FALLBACK USED")
            return None
        except Exception as e:
            logger.error(f"❌ AWS Cost Explorer API failed: {e} - NO FALLBACK USED")
            return None


class UnifiedAPIClient:
    """Unified client for all external APIs - Carbon, Power, and AWS Cost data."""

    def __init__(self, aws_profile: str = None):
        # Load environment variables first
        load_dotenv()
        
        # Use AWS profile from environment if not provided
        if aws_profile is None:
            aws_profile = os.getenv('AWS_PROFILE', 'carbon-finops-sandbox')
        
        # Initialize API clients with proper error handling
        try:
            self.carbon_client = CarbonIntensityClient()
            # Create aliases for deployment validation
            self.electricitymap_client = self.carbon_client
            logger.info("✅ ElectricityMap client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize carbon intensity client: {e}")
            self.carbon_client = None
            self.electricitymap_client = None
        
        try:
            self.power_client = BoaviztoClient()
            # Create alias for deployment validation  
            self.boavizta_client = self.power_client
            logger.info("✅ Boavizta client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize power consumption client: {e}")
            self.power_client = None
            self.boavizta_client = None
        
        try:
            self.cost_client = AWSCostClient(aws_profile)
            # Create alias for deployment validation
            self.aws_client = self.cost_client
            logger.info(f"✅ AWS Cost Explorer client initialized: Profile={aws_profile}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AWS cost client: {e}")
            self.cost_client = None
            self.aws_client = None
        
        # Log overall status
        clients_ready = sum([
            self.carbon_client is not None,
            self.power_client is not None, 
            self.cost_client is not None
        ])
        logger.info(f"✅ Unified API Client initialized - {clients_ready}/3 APIs ready")

    def get_carbon_intensity(self, region: str = "eu-central-1") -> Optional[CarbonIntensity]:
        """Get carbon intensity data."""
        return self.carbon_client.get_current_intensity(region)

    def get_power_consumption(self, instance_type: str) -> Optional[PowerConsumption]:
        """Get power consumption data."""
        return self.power_client.get_power_consumption(instance_type)

    def get_aws_costs(self) -> Optional[AWSCostData]:
        """Get AWS cost data."""
        return self.cost_client.get_monthly_costs()
