"""
Cache Utilities Module
Centralized caching functionality to eliminate code duplication

This module provides reusable cache validation and management functions
used across the Carbon-Aware FinOps dashboard. Eliminates duplicate
cache validation code in api_client.py, data_processor.py, and cloudtrail_tracker.py.

Academic Benefits:
- DRY principle implementation
- Single source of truth for cache logic
- Easier testing and maintenance
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def is_cache_valid(cache_path: str, max_age_minutes: int) -> bool:
    """
    Check if cache file exists and is within max age

    Centralized cache validation function replacing duplicate implementations
    across multiple modules.

    Args:
        cache_path: Full path to cache file
        max_age_minutes: Maximum age in minutes for cache to be considered valid

    Returns:
        bool: True if cache exists and is within max age, False otherwise
    """
    if not os.path.exists(cache_path):
        return False

    file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
    return file_age < (max_age_minutes * 60)


def get_cache_path(cache_type: str, identifier: str, extension: str = "json") -> str:
    """
    Generate standardized cache file path

    Creates consistent cache file paths across the application
    following the pattern: .cache/api_data/{cache_type}_{identifier}.{extension}

    Args:
        cache_type: Type of cache (e.g., 'carbon', 'power', 'cpu')
        identifier: Unique identifier (e.g., instance_id, region)
        extension: File extension (default: 'json')

    Returns:
        str: Full path to cache file
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(project_root, ".cache", "api_data")
    cache_filename = f"{cache_type}_{identifier}.{extension}"

    return os.path.join(cache_dir, cache_filename)


def ensure_cache_dir(cache_path: str) -> None:
    """
    Ensure cache directory exists

    Creates cache directory structure if it doesn't exist.
    Used before writing cache files.

    Args:
        cache_path: Full path to cache file (directory will be extracted)
    """
    cache_dir = os.path.dirname(cache_path)
    os.makedirs(cache_dir, exist_ok=True)


def get_cache_info(cache_path: str) -> dict:
    """
    Get detailed cache file information

    Useful for debugging and cache management.

    Args:
        cache_path: Full path to cache file

    Returns:
        dict: Cache information including age, size, validity
    """
    if not os.path.exists(cache_path):
        return {
            "exists": False,
            "path": cache_path,
            "age_minutes": None,
            "size_bytes": None
        }

    stat = os.stat(cache_path)
    age_seconds = datetime.now().timestamp() - stat.st_mtime
    age_minutes = age_seconds / 60

    return {
        "exists": True,
        "path": cache_path,
        "age_minutes": age_minutes,
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def clean_old_cache_files(cache_dir: str, max_age_days: int = 7) -> int:
    """
    Clean old cache files to prevent disk space issues

    Removes cache files older than max_age_days from the specified directory.

    Args:
        cache_dir: Directory containing cache files
        max_age_days: Maximum age in days before files are deleted

    Returns:
        int: Number of files deleted
    """
    if not os.path.exists(cache_dir):
        return 0

    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    cutoff_timestamp = cutoff_time.timestamp()
    deleted_count = 0

    try:
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)

            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)

                if file_mtime < cutoff_timestamp:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.debug(f"🗑️ Cleaned old cache file: {filename}")

    except (OSError, PermissionError) as e:
        logger.warning(f"⚠️ Cache cleanup failed - file system error: {e}")
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ Cache cleanup failed - data validation error: {e}")

    if deleted_count > 0:
        logger.info(f"🧹 Cache cleanup: {deleted_count} old files removed from {cache_dir}")

    return deleted_count


# Constants for common cache TTLs (Time To Live in minutes)
class CacheTTL:
    """Standard cache TTL values used across the application"""
    CARBON_DATA = 30        # 30 minutes - ElectricityMaps updates
    CARBON_24H = 1440       # 24 hours - Historical data doesn't change
    POWER_DATA = 10080      # 7 days - Hardware specs don't change
    PRICING_DATA = 10080    # 7 days - AWS pricing relatively stable
    COST_DATA = 360         # 6 hours - Cost Explorer updates
    CPU_UTILIZATION = 180   # 3 hours - Performance metrics
    CLOUDTRAIL_EVENTS = 1440 # 24 hours - Audit events are immutable


def get_standard_cache_path(cache_type: str, identifier: str) -> str:
    """
    Get cache path using standardized project structure

    Convenience function that uses the standard .cache/api_data structure.

    Args:
        cache_type: Type of cache data
        identifier: Unique identifier for the cached item

    Returns:
        str: Standardized cache file path
    """
    return get_cache_path(cache_type, identifier)