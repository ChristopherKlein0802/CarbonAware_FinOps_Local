"""
ElectricityMaps API Integration
Carbon intensity data for carbon-aware optimization
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
import logging
from dotenv import load_dotenv

from ..constants import AWSConstants
from ..utils.cache import is_cache_valid, get_standard_cache_path, ensure_cache_dir, CacheTTL
from ..utils.errors import handle_api_requests, ErrorMessages
from ..utils.logging import get_performance_logger, log_api_operation, log_carbon_data
from ..models.carbon import CarbonIntensity

# Load environment variables
load_dotenv()

logger = get_performance_logger("electricity_api")


def parse_iso_datetime(datetime_str: str) -> datetime:
    """Parse ISO datetime string and ensure timezone awareness."""
    if not datetime_str:
        return datetime.now(timezone.utc)

    normalised = datetime_str.strip()
    if normalised.endswith("Z"):
        normalised = normalised[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(normalised)
    except ValueError:
        return datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class ElectricityMapsAPI:
    """ElectricityMaps API client for carbon intensity data"""

    def __init__(self):
        """Initialize ElectricityMaps API client"""
        self.api_key = os.getenv("ELECTRICITYMAP_API_KEY")
        self.base_url = "https://api-access.electricitymaps.com/v3"
        self.enable_hourly_collection = os.getenv(
            "ENABLE_HOURLY_CARBON_COLLECTION",
            "false",
        ).strip().lower() in {"1", "true", "yes", "on"}
        if self.enable_hourly_collection:
            logger.info("🟢 Hourly carbon fallback enabled via ENABLE_HOURLY_CARBON_COLLECTION")

    def get_current_carbon_intensity(self, region: str = "eu-central-1") -> Optional[CarbonIntensity]:
        """Get current carbon intensity from ElectricityMap with optimized 2-hour caching

        Scientific rationale: ElectricityMap updates every 15-60 minutes.
        2-hour cache reduces API costs while maintaining reasonable accuracy.
        """
        cache_path = get_standard_cache_path("carbon_intensity", region)
        ensure_cache_dir(cache_path)

        # Check cache first (2 hours - optimized for cost vs accuracy)
        if is_cache_valid(cache_path, CacheTTL.CARBON_DATA):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.debug(f"✅ Using cached carbon data for {region}")
                fetched_at_raw = cached_data.get("fetched_at_utc") or cached_data.get("fetched_at")
                if fetched_at_raw:
                    fetched_at_local = parse_iso_datetime(fetched_at_raw)
                    fetched_at = fetched_at_local.astimezone(timezone.utc)
                else:
                    fetched_at = datetime.fromtimestamp(os.path.getmtime(cache_path), tz=timezone.utc)
                timestamp_local = parse_iso_datetime(cached_data["timestamp"])
                return CarbonIntensity(
                    value=cached_data["value"],
                    timestamp=timestamp_local.astimezone(timezone.utc),
                    region=cached_data["region"],
                    source=cached_data["source"],
                    fetched_at=fetched_at
                )
            except (FileNotFoundError, PermissionError, OSError):
                pass  # Cache miss - use fresh API call
            except (ValueError, TypeError) as e:
                logger.warning(f"📄 Carbon cache corrupted: {e} - using fresh API call")

        # Fetch fresh data from ElectricityMap API
        if not self.api_key:
            logger.error("❌ ElectricityMap API key not available - NO FALLBACK used")
            return None

        headers = {"auth-token": self.api_key}
        zone = AWSConstants.REGION_MAPPINGS.get(region, "DE")

        try:
            logger.info(f"🌿 Fetching fresh carbon data for {zone}")
            response = requests.get(
                f"{self.base_url}/carbon-intensity/latest",
                headers=headers,
                params={"zone": zone},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if "carbonIntensity" not in data or "datetime" not in data:
                logger.error(f"❌ ElectricityMap API returned invalid data")
                return None

            fetched_at = datetime.now(timezone.utc)
            timestamp_utc = parse_iso_datetime(data["datetime"])
            carbon_data = CarbonIntensity(
                value=float(data["carbonIntensity"]),
                timestamp=timestamp_utc,
                region=region,
                source="electricitymap",
                fetched_at=fetched_at
            )

            # Cache the result with local and UTC timestamps
            try:
                local_timestamp = carbon_data.timestamp.astimezone()
                local_fetched = carbon_data.fetched_at.astimezone() if carbon_data.fetched_at else None
                cache_data = {
                    "value": carbon_data.value,
                    "timestamp": local_timestamp.isoformat(),
                    "timestamp_utc": carbon_data.timestamp.astimezone(timezone.utc).isoformat(),
                    "region": carbon_data.region,
                    "source": carbon_data.source,
                    "fetched_at": local_fetched.isoformat() if local_fetched else None,
                    "fetched_at_utc": carbon_data.fetched_at.astimezone(timezone.utc).isoformat() if carbon_data.fetched_at else None
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info(f"✅ Carbon intensity: {carbon_data.value}g CO2/kWh (cached 60min)")
            except (PermissionError, OSError):
                pass  # Cache write failed - data still available

            return carbon_data

        except requests.exceptions.Timeout:
            logger.error(f"⏱️ ElectricityMap API timeout - check network connection")
            return self._graceful_degradation_carbon(region, "API timeout")
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 ElectricityMap API connection failed - check internet connectivity")
            return self._graceful_degradation_carbon(region, "Connection error")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"🔐 ElectricityMap API authentication failed - check API key")
            elif e.response.status_code == 429:
                logger.warning(f"🚦 ElectricityMap API rate limited - reduce request frequency")
            else:
                logger.error(f"❌ ElectricityMap API HTTP error: {e.response.status_code}")
            return self._graceful_degradation_carbon(region, f"HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ElectricityMap API request failed: {type(e).__name__}: {e}")
            return self._graceful_degradation_carbon(region, str(e))

    def get_carbon_intensity_24h(self, region: str = "eu-central-1") -> Optional[List[Dict]]:
        """Get 24-hour historical carbon intensity from ElectricityMap with daily caching

        Scientific rationale: Historical data doesn't change, so daily caching is appropriate.
        Uses real API data instead of hard-coded patterns for academic integrity.

        Returns: List of hourly data points with timestamp and carbon intensity
        """
        # Use date-based cache key since historical data doesn't change
        today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
        cache_path = get_standard_cache_path("carbon_intensity_24h", f"{region}_{today}")
        ensure_cache_dir(cache_path)

        # Check cache first (24 hours - historical data doesn't change)
        if is_cache_valid(cache_path, CacheTTL.CARBON_24H):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                logger.debug(f"✅ Using cached 24h carbon data for {region}")
                return cached_data["history"]
            except (FileNotFoundError, PermissionError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ 24h carbon cache read failed: {e}")

        # Fetch fresh 24h historical data from ElectricityMap API (history endpoint → free tier)
        if not self.api_key:
            logger.error("❌ ElectricityMap API key not available for 24h data - NO FALLBACK used")
            return None

        headers = {"auth-token": self.api_key}
        zone = AWSConstants.REGION_MAPPINGS.get(region, "DE")

        try:
            logger.info(f"🌿 Fetching 24h carbon history for {zone}")

            history_url = f"{self.base_url}/carbon-intensity/history"
            request_params = {"zone": zone}
            response = requests.get(history_url, headers=headers, params=request_params, timeout=30)

            # Log response status before raising
            logger.info(f"📊 API Response status: {response.status_code}")

            response.raise_for_status()

            data = response.json()

            # Debug: Check what structure we actually get
            logger.info(f"📊 ElectricityMap 24h API response keys: {list(data.keys())}")

            # Show the actual error message for debugging
            if "error" in data and "message" in data:
                logger.info(f"📊 Full API error response: {data}")

            # Check for API error responses first
            if "error" in data and "message" in data:
                logger.error(f"❌ ElectricityMap 24h API error: {data['error']} - {data['message']}")
                logger.info("💡 Possible fixes: Check API key permissions, zone parameter, or time range")
                return None

            history_candidates: List[List[Dict]] = []
            if isinstance(data, dict):
                for key in ("history", "data", "points"):
                    value = data.get(key)
                    if isinstance(value, list):
                        history_candidates.append(value)
                # ElectricityMaps sometimes nests the list under "history" -> {"values": []}
                if "history" in data and isinstance(data["history"], dict):
                    nested_values = data["history"].get("values")
                    if isinstance(nested_values, list):
                        history_candidates.append(nested_values)
            elif isinstance(data, list):
                history_candidates.append(data)

            processed_history: List[Dict] = []

            def _normalise_entries(entries: List[Dict]) -> None:
                for raw_entry in entries:
                    if not isinstance(raw_entry, dict):
                        continue
                    intensity = raw_entry.get("carbonIntensity")
                    if intensity is None:
                        intensity = raw_entry.get("value")
                    timestamp = raw_entry.get("datetime") or raw_entry.get("time") or raw_entry.get("timestamp")
                    if intensity is None or timestamp is None:
                        continue
                    try:
                        intensity_value = float(intensity)
                    except (TypeError, ValueError):
                        continue
                    dt = parse_iso_datetime(str(timestamp))
                    local_dt = dt.astimezone()
                    processed_history.append({
                        "carbonIntensity": intensity_value,
                        "datetime": local_dt.isoformat(),
                        "datetime_utc": dt.astimezone(timezone.utc).isoformat(),
                        "hour": local_dt.hour,
                        "source": raw_entry.get("source", "electricitymap_24h_api")
                    })

            for candidate in history_candidates:
                _normalise_entries(candidate)

            if len(processed_history) < 12:  # Minimum reasonable data points
                logger.warning(f"⚠️ ElectricityMap returned insufficient 24h data: {len(processed_history)} points")
                return None

            # Remove duplicates and sort chronologically
            unique_history = {
                entry["datetime"]: entry for entry in processed_history
            }
            ordered_history = [unique_history[key] for key in sorted(unique_history.keys())]

            # Cache the result with daily expiration
            try:
                now_utc = datetime.now(timezone.utc)
                cache_data = {
                    "history": ordered_history,
                    "cached_at": now_utc.astimezone().isoformat(),
                    "cached_at_utc": now_utc.isoformat(),
                    "data_source": "electricitymap_24h_api",
                    "region": region,
                    "zone": zone
                }
                with open(cache_path, "w") as f:
                    json.dump(cache_data, f)
                logger.info(f"✅ 24h carbon history: {len(ordered_history)} data points (cached 24h)")
            except (OSError, PermissionError, json.JSONDecodeError) as e:
                logger.warning(f"⚠️ Failed to cache 24h carbon data: {e}")

            return ordered_history

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ElectricityMap 24h API failed: {e} - NO FALLBACK used")
            return None

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"❌ ElectricityMap 24h data processing failed: {e} - NO FALLBACK used")
            return None

    def get_self_collected_24h_data(self, region: str = "eu-central-1") -> Optional[List[Dict]]:
        """
        Get 24h carbon data from our own hourly collection system

        Scientific approach: Collect real API data every hour to build our own 24h dataset
        This maintains academic integrity - all data points are real ElectricityMaps data
        """
        collection_file = get_standard_cache_path("hourly_collection", region)

        if not self.enable_hourly_collection:
            if os.path.exists(collection_file):
                try:
                    os.remove(collection_file)
                    logger.debug("🧹 Removed hourly carbon fallback cache: %s", collection_file)
                except OSError as error:
                    logger.warning("⚠️ Failed to remove hourly fallback cache %s: %s", collection_file, error)
            logger.debug("Hourly carbon fallback disabled via configuration")
            return None

        ensure_cache_dir(collection_file)

        # Get current carbon data and store it
        self._store_hourly_carbon_data(region, collection_file)

        # Read and return available collected data
        return self._read_collected_hourly_data(collection_file)

    def _store_hourly_carbon_data(self, region: str, collection_file: str):
        """Store current carbon data with timestamp for hourly collection"""
        try:
            current_data = self.get_current_carbon_intensity(region)
            if not current_data:
                return

            current_time = datetime.now(timezone.utc).astimezone()
            current_hour = current_time.replace(minute=0, second=0, microsecond=0)

            # Load existing data
            collected_data = []
            if os.path.exists(collection_file):
                with open(collection_file, 'r') as f:
                    try:
                        collected_data = json.load(f)
                    except json.JSONDecodeError:
                        collected_data = []

            # Check if we already have data for this hour
            hour_key = current_hour.isoformat()
            existing_entry = next((entry for entry in collected_data if entry.get('hour_key') == hour_key), None)

            if not existing_entry:
                # Add new hourly data point with full timestamp
                new_entry = {
                    'hour_key': hour_key,
                    'carbonIntensity': current_data.value,
                    'datetime': current_hour.isoformat(),
                    'datetime_utc': current_hour.astimezone(timezone.utc).isoformat(),
                    'hour': current_hour.hour,
                    'collected_at': current_time.isoformat(),
                    'source': 'electricitymap_hourly_collection',
                    'full_date': current_hour.strftime('%d.%m.%Y'),
                    'display_time': current_hour.strftime('%d.%m.%Y %H:%M')
                }
                collected_data.append(new_entry)

                # Implement sliding 24h window: Keep only last 24 hours + current hour
                cutoff_time = datetime.now(timezone.utc).astimezone() - timedelta(hours=24)
                collected_data = [
                    entry for entry in collected_data
                    if parse_iso_datetime(entry['hour_key']).astimezone() > cutoff_time
                ]

                # If we have more than 24 hours of data, implement sliding window
                if len(collected_data) > 24:
                    # Sort by hour and keep only the most recent 24 entries
                    collected_data.sort(key=lambda x: x['hour_key'])
                    collected_data = collected_data[-24:]  # Keep last 24 hours

                # Sort by hour_key
                collected_data.sort(key=lambda x: x['hour_key'])

                # Save updated data
                with open(collection_file, 'w') as f:
                    json.dump(collected_data, f, indent=2)

                logger.info(f"📊 Stored hourly carbon data: {current_data.value}g CO₂/kWh for {current_hour.strftime('%H:00')}")

        except (OSError, PermissionError, json.JSONDecodeError) as e:
            logger.warning(f"⚠️ Failed to store hourly carbon data: {e}")

    def _graceful_degradation_carbon(self, region: str, error_msg: str) -> Optional[CarbonIntensity]:
        """Enhanced error recovery with cached fallback and regional averages

        Academic approach: Try cached data, then European grid average as last resort
        Maintains scientific transparency by logging all fallback decisions
        """
        # Try most recent cache (even if expired)
        cache_path = get_standard_cache_path("carbon_intensity", region)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                age_hours = (datetime.now().timestamp() - os.path.getmtime(cache_path)) / 3600
                logger.warning(f"⚠️ Using expired cache ({age_hours:.1f}h old) due to API failure: {error_msg}")
                return CarbonIntensity(
                    value=cached_data["value"],
                    timestamp=parse_iso_datetime(cached_data["timestamp"]),
                    region=cached_data["region"],
                    source=f"expired_cache_{cached_data['source']}"
                )
            except (FileNotFoundError, PermissionError, json.JSONDecodeError, KeyError) as cache_error:
                logger.warning(f"⚠️ Cache fallback also failed: {cache_error}")

        # NO-FALLBACK Policy: Academic integrity maintained
        if "Token has expired" in error_msg or "InvalidGrantException" in error_msg:
            logger.error("💡 API authentication failed - check credentials")

        # Academic NO-FALLBACK Policy: Return None instead of fake data
        logger.error("❌ Carbon intensity unavailable - NO-FALLBACK policy enforced")
        logger.info("🎓 Academic integrity: No synthetic data returned when real APIs fail")
        return None

    def _read_collected_hourly_data(self, collection_file: str) -> Optional[List[Dict]]:
        """Read and process collected hourly data for 24h visualization"""
        try:
            if not os.path.exists(collection_file):
                logger.debug("📊 No hourly collection data yet - building dataset over time")
                return None

            with open(collection_file, 'r') as f:
                collected_data = json.load(f)

            if not collected_data:
                return None

            # Filter for last 24 hours
            now = datetime.now(timezone.utc).astimezone()
            cutoff_time = now - timedelta(hours=24)

            recent_data = [
                entry for entry in collected_data
                if parse_iso_datetime(entry['hour_key']).astimezone() > cutoff_time
            ]

            if len(recent_data) >= 6:  # At least 6 hours of data to show meaningful trend
                logger.debug(f"📊 Retrieved {len(recent_data)} hours of self-collected carbon data")
                return recent_data
            else:
                logger.debug(f"📊 Self-collected dataset currently at {len(recent_data)} hour(s) - building towards 24h")
                return None

        except (FileNotFoundError, PermissionError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"⚠️ Failed to read collected hourly data: {e}")
            return None
