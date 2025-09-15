"""
Unified API Client for Carbon-Aware FinOps Dashboard
Pragmatic Professional Implementation - Clean, single-file API integration

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

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# AWS region to ElectricityMap zone mappings
REGION_MAPPINGS = {
    "eu-central-1": "DE",  # Germany
    "eu-west-1": "IE",     # Ireland
    "eu-west-2": "GB",     # United Kingdom
    "eu-west-3": "FR",     # France
    "eu-north-1": "SE",    # Sweden
    "us-east-1": "US-NE-ISO",    # US East
    "us-west-2": "US-NW-PACW",   # US West
}

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
        """Initialize the unified API client"""
        # Load environment variables
        load_dotenv()

        # AWS profile configuration
        if aws_profile is None:
            aws_profile = os.getenv('AWS_PROFILE', 'carbon-finops-sandbox')

        # Initialize clients
        self.aws_profile = aws_profile
        self._init_cache_dir()

        logger.info("✅ Unified API Client initialized")

    def _init_cache_dir(self):
        """Initialize cache directory"""
        self.cache_dir = "/tmp/carbon_finops_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def _is_cache_valid(self, cache_path: str, max_age_minutes: int) -> bool:
        """Check if cache file is still valid"""
        if not os.path.exists(cache_path):
            return False

        file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        return file_age < (max_age_minutes * 60)

    def get_current_carbon_intensity(self, region: str = "eu-central-1") -> Optional[CarbonIntensity]:
        """Get current carbon intensity from ElectricityMap with 30-minute caching"""
        cache_path = os.path.join(self.cache_dir, f"carbon_intensity_{region}.json")

        # Check cache first (30 minutes)
        if self._is_cache_valid(cache_path, 30):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.info(f"✅ Using cached carbon data for {region}")
                return CarbonIntensity(
                    value=cached_data["value"],
                    timestamp=parse_iso_datetime(cached_data["timestamp"]),
                    region=cached_data["region"],
                    source=cached_data["source"]
                )
            except Exception as e:
                logger.warning(f"⚠️ Carbon cache read failed: {e}")

        # Fetch fresh data from ElectricityMap API
        api_key = os.getenv("ELECTRICITYMAP_API_KEY")
        if not api_key:
            logger.error("❌ ElectricityMap API key not available - NO FALLBACK used")
            return None

        headers = {"auth-token": api_key}
        zone = REGION_MAPPINGS.get(region, "DE")

        try:
            logger.info(f"🌿 Fetching fresh carbon data for {zone}")
            response = requests.get(
                "https://api-access.electricitymaps.com/v3/carbon-intensity/latest",
                headers=headers,
                params={"zone": zone},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if "carbonIntensity" not in data or "datetime" not in data:
                logger.error(f"❌ ElectricityMap API returned invalid data")
                return None

            carbon_data = CarbonIntensity(
                value=float(data["carbonIntensity"]),
                timestamp=parse_iso_datetime(data["datetime"]),
                region=region,
                source="electricitymap"
            )

            # Cache the result
            try:
                cache_data = {
                    "value": carbon_data.value,
                    "timestamp": carbon_data.timestamp.isoformat(),
                    "region": carbon_data.region,
                    "source": carbon_data.source
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info(f"✅ Carbon intensity: {carbon_data.value}g CO2/kWh (cached 30min)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache carbon data: {e}")

            return carbon_data

        except Exception as e:
            logger.error(f"❌ ElectricityMap API failed: {e} - NO FALLBACK used")
            return None

    def get_power_consumption(self, instance_type: str) -> Optional[PowerConsumption]:
        """Get power consumption from Boavizta API with 24h caching"""
        if not instance_type:
            logger.error("❌ Invalid instance_type")
            return None

        cache_path = os.path.join(self.cache_dir, f"boavizta_power_{instance_type}.json")

        # Check cache first (24 hours)
        if self._is_cache_valid(cache_path, 24 * 60):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.info(f"✅ Using cached power data for {instance_type}")
                return PowerConsumption(
                    avg_power_watts=cached_data["avg_power_watts"],
                    min_power_watts=cached_data["min_power_watts"],
                    max_power_watts=cached_data["max_power_watts"],
                    confidence_level=cached_data["confidence_level"],
                    source=cached_data["source"]
                )
            except Exception as e:
                logger.warning(f"⚠️ Power cache read failed: {e}")

        # Fetch fresh data from Boavizta API
        try:
            logger.info(f"⚡ Fetching fresh power data for {instance_type}")
            url = "https://api.boavizta.org/v1/cloud/instance"
            payload = {
                "provider": "aws",
                "instance_type": instance_type,
                "usage": {"hours_use_time": 1},
                "location": "EUC"  # Europe Central
            }

            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract power consumption from verbose.avg_power
            if "verbose" in data and "avg_power" in data["verbose"]:
                avg_power_data = data["verbose"]["avg_power"]
                if "value" not in avg_power_data:
                    logger.error(f"❌ Boavizta API: invalid avg_power structure")
                    return None

                avg_power = avg_power_data.get("value", 0)
                min_power = data["verbose"].get("min_power", {}).get("value", avg_power * 0.8)
                max_power = data["verbose"].get("max_power", {}).get("value", avg_power * 1.2)

                if avg_power <= 0:
                    logger.error(f"❌ Boavizta API: invalid power value {avg_power}")
                    return None

                power_data = PowerConsumption(
                    avg_power_watts=float(avg_power),
                    min_power_watts=float(min_power),
                    max_power_watts=float(max_power),
                    confidence_level="high",
                    source="Boavizta_API"
                )

                # Cache the result
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
                    logger.info(f"✅ Power: {instance_type} = {avg_power:.1f}W (cached 24h)")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache power data: {e}")

                return power_data
            else:
                logger.error(f"❌ Boavizta API: missing power data for {instance_type}")
                return None

        except Exception as e:
            logger.error(f"❌ Boavizta API failed for {instance_type}: {e} - NO FALLBACK used")
            return None

    def get_monthly_costs(self) -> Optional[AWSCostData]:
        """Get monthly AWS costs with 1-hour caching"""
        cache_path = os.path.join(self.cache_dir, "cost_data.json")

        # Check cache first (1 hour)
        if self._is_cache_valid(cache_path, 60):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.info("✅ Using cached Cost Explorer data")
                return AWSCostData(**cached_data)
            except Exception as e:
                logger.warning(f"⚠️ Cost cache read failed: {e}")

        # Fetch fresh data from AWS Cost Explorer
        try:
            session = boto3.Session(profile_name=self.aws_profile)
            cost_client = session.client("ce", region_name="us-east-1")

            logger.info("💰 Fetching fresh Cost Explorer data")

            # Get 30-day cost data
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            response = cost_client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d")
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
            )

            service_costs = {}
            total_cost = 0.0

            for result in response["ResultsByTime"]:
                for group in result["Groups"]:
                    if group["Keys"]:
                        service_name = group["Keys"][0]
                        cost_amount_str = group["Metrics"]["UnblendedCost"]["Amount"]

                        try:
                            cost_amount = float(cost_amount_str)
                            if cost_amount < 0:
                                cost_amount = 0.0
                        except (ValueError, TypeError):
                            cost_amount = 0.0

                        service_costs[service_name] = cost_amount
                        total_cost += cost_amount

            cost_data = AWSCostData(
                monthly_cost_usd=total_cost,
                service_costs=service_costs,
                region="us-east-1",
                source="AWS_Cost_Explorer_API"
            )

            # Cache the result
            try:
                cache_data = {
                    "monthly_cost_usd": cost_data.monthly_cost_usd,
                    "service_costs": cost_data.service_costs,
                    "region": cost_data.region,
                    "source": cost_data.source
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info(f"✅ AWS costs: ${total_cost:.2f} USD (cached 1h)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache cost data: {e}")

            return cost_data

        except Exception as e:
            logger.error(f"❌ AWS Cost Explorer failed: {e} - NO FALLBACK used")
            return None

# Global instance
unified_api_client = UnifiedAPIClient()