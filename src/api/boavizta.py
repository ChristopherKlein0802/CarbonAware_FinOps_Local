"""
Boavizta API Integration
Scientific power consumption data for AWS instances
"""

import json
import requests
from typing import Optional
import logging

from ..utils.cache import is_cache_valid, get_standard_cache_path, ensure_cache_dir, CacheTTL
from ..utils.errors import handle_api_requests
from ..utils.logging import get_performance_logger
from ..models.carbon import PowerConsumption

logger = get_performance_logger("boavizta_api")


class BoaviztaAPI:
    """Boavizta API client for scientific power consumption data"""

    def __init__(self):
        """Initialize Boavizta API client"""
        self.base_url = "https://api.boavizta.org/v1"

    def get_power_consumption(self, instance_type: str) -> Optional[PowerConsumption]:
        """Get power consumption from Boavizta API with 7-day caching"""
        if not instance_type:
            logger.error("❌ Invalid instance_type")
            return None

        cache_path = get_standard_cache_path("boavizta_power", instance_type)
        ensure_cache_dir(cache_path)

        # Check cache first (7 days - hardware specs don't change)
        if is_cache_valid(cache_path, CacheTTL.POWER_DATA):
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
            except (FileNotFoundError, PermissionError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Power cache read failed: {e}")

        # Fetch fresh data from Boavizta API
        try:
            logger.info(f"⚡ Fetching fresh power data for {instance_type}")
            url = f"{self.base_url}/cloud/instance"
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
                except (PermissionError, OSError):
                    pass  # Cache write failed - data still available

                return power_data
            else:
                logger.error(f"❌ Boavizta API: missing power data for {instance_type}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Boavizta API timeout for {instance_type} - check network connection")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Boavizta API connection failed for {instance_type} - check internet connectivity")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                logger.error(f"🏥 Boavizta API server error ({e.response.status_code}) for {instance_type} - try again later")
            else:
                logger.error(f"❌ Boavizta API HTTP error: {e.response.status_code} for {instance_type}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Boavizta API request failed for {instance_type}: {type(e).__name__}: {e}")
            return None