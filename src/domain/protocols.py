"""
Domain Layer Protocols (Interfaces) for Clean Architecture

Following the Dependency Inversion Principle, the domain layer defines
interfaces that infrastructure must implement. This ensures domain logic
remains independent of external concerns.

References:
- Clean Architecture (Robert C. Martin)
- Dependency Inversion Principle (SOLID)
"""

from __future__ import annotations
from typing import Protocol, Optional, List, Any
from datetime import datetime, timedelta
from pathlib import Path


class CacheRepository(Protocol):
    """
    Protocol for cache storage operations.

    The domain layer defines what caching operations it needs,
    but doesn't know HOW they're implemented (file system, Redis, etc.)

    This follows the Dependency Inversion Principle:
    - High-level modules (domain) define the interface
    - Low-level modules (infrastructure) implement it
    """

    def get(
        self,
        category: str,
        key: str,
        *,
        max_age: Optional[timedelta] = None,
        parser: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Retrieve cached data if available and fresh.

        Args:
            category: Cache category (e.g., "carbon_intensity", "runtime")
            key: Unique identifier within category
            max_age: Maximum age for cache validity (None = no expiry)
            parser: Optional function to parse cached data

        Returns:
            Cached data if found and valid, None otherwise
        """
        ...

    def set(
        self,
        category: str,
        key: str,
        value: Any,
        *,
        serializer: Optional[Any] = None,
    ) -> bool:
        """
        Store data in cache.

        Args:
            category: Cache category
            key: Unique identifier
            value: Data to cache
            serializer: Optional function to serialize data

        Returns:
            True if successful, False otherwise
        """
        ...

    def path(self, category: str, key: str) -> Optional[Path]:
        """
        Get file system path for cached item (if applicable).

        Args:
            category: Cache category
            key: Unique identifier

        Returns:
            Path to cached file, or None if cache type doesn't use files
        """
        ...

    def clear_category(self, category: str) -> bool:
        """
        Clear all cached items in a category.

        Args:
            category: Cache category to clear

        Returns:
            True if successful
        """
        ...


class AWSGateway(Protocol):
    """
    Protocol for AWS service operations.

    Defines AWS operations needed by domain services without
    coupling to boto3 implementation details.
    """

    def list_ec2_instances(self, region: str) -> List[Any]:
        """
        List all EC2 instances in a region.

        Args:
            region: AWS region code (e.g., "eu-central-1")

        Returns:
            List of EC2 instance data
        """
        ...

    def get_cloudtrail_events(
        self,
        instance_id: str,
        region: str,
        *,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Any]:
        """
        Get CloudTrail events for an instance.

        Args:
            instance_id: EC2 instance ID
            region: AWS region
            start_time: Event window start
            end_time: Event window end

        Returns:
            List of CloudTrail events
        """
        ...

    def get_cpu_utilization(
        self,
        instance_id: str,
        region: str,
        *,
        hours: int,
    ) -> Optional[float]:
        """
        Get average CPU utilization for an instance.

        Args:
            instance_id: EC2 instance ID
            region: AWS region
            hours: Lookback period in hours

        Returns:
            Average CPU percentage, or None if unavailable
        """
        ...

    def get_instance_pricing(
        self,
        instance_type: str,
        region: str,
    ) -> Optional[float]:
        """
        Get hourly on-demand pricing for instance type.

        Args:
            instance_type: EC2 instance type (e.g., "t3.medium")
            region: AWS region

        Returns:
            Hourly price in USD, or None if unavailable
        """
        ...

    def get_monthly_costs(
        self,
        region: str,
    ) -> Optional[Any]:
        """
        Get monthly cost data from Cost Explorer.

        Args:
            region: AWS region

        Returns:
            Cost data object, or None if unavailable
        """
        ...

    def get_hourly_costs(
        self,
        hours: int,
        region: str,
    ) -> List[Any]:
        """
        Get hourly cost breakdown from Cost Explorer.

        Args:
            hours: Lookback period in hours
            region: AWS region

        Returns:
            List of hourly cost data points
        """
        ...


class CarbonDataGateway(Protocol):
    """
    Protocol for carbon intensity data operations.

    Defines operations for fetching carbon intensity from external APIs
    (ElectricityMaps, etc.) without coupling to HTTP client details.
    """

    def get_current_intensity(
        self,
        region: str,
        zone: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Get current carbon intensity for a region.

        Args:
            region: Geographic region
            zone: Optional grid zone identifier

        Returns:
            CarbonIntensity object, or None if unavailable
        """
        ...

    def get_intensity_history(
        self,
        region: str,
        *,
        hours: int,
        zone: Optional[str] = None,
    ) -> List[Any]:
        """
        Get historical carbon intensity data.

        Args:
            region: Geographic region
            hours: Lookback period in hours
            zone: Optional grid zone identifier

        Returns:
            List of historical CarbonIntensity objects
        """
        ...


class PowerModelGateway(Protocol):
    """
    Protocol for power consumption model operations.

    Defines operations for fetching hardware power models from
    external APIs (Boavizta, etc.)
    """

    def get_power_consumption(
        self,
        instance_type: str,
        *,
        cpu_utilization: Optional[float] = None,
    ) -> Optional[Any]:
        """
        Get power consumption estimate for instance type.

        Args:
            instance_type: Cloud instance type (e.g., "t3.medium")
            cpu_utilization: Optional CPU utilization percentage

        Returns:
            PowerConsumption object, or None if unavailable
        """
        ...


class InfrastructureGateway(Protocol):
    """
    Composite protocol combining all infrastructure operations.

    This is the main gateway interface used by domain services.
    Concrete implementations can delegate to specialized clients.
    """

    # AWS Operations
    def list_ec2_instances(self, region: str) -> List[Any]:
        """List EC2 instances."""
        ...

    def get_cloudtrail_events(
        self,
        instance_id: str,
        region: str,
        *,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Any]:
        """Get CloudTrail events."""
        ...

    def get_cpu_utilization(
        self,
        instance_id: str,
        region: str,
        *,
        hours: int,
    ) -> Optional[float]:
        """Get CPU utilization."""
        ...

    def get_instance_pricing(
        self,
        instance_type: str,
        region: str,
    ) -> Optional[float]:
        """Get instance pricing."""
        ...

    def get_monthly_costs(self, region: str) -> Optional[Any]:
        """Get monthly costs."""
        ...

    def get_hourly_costs(self, hours: int, region: str) -> List[Any]:
        """Get hourly costs."""
        ...

    def get_cached_launch_time(
        self,
        instance_id: str,
        region: str,
    ) -> Optional[datetime]:
        """Get cached launch time for instance."""
        ...

    # Carbon Data Operations
    def get_carbon_intensity(
        self,
        region: str,
        zone: Optional[str] = None,
    ) -> Optional[Any]:
        """Get current carbon intensity."""
        ...

    def get_carbon_history(
        self,
        region: str,
        *,
        hours: int,
        zone: Optional[str] = None,
    ) -> List[Any]:
        """Get carbon intensity history."""
        ...

    # Power Model Operations
    def get_power_model(
        self,
        instance_type: str,
        *,
        cpu_utilization: Optional[float] = None,
    ) -> Optional[Any]:
        """Get power consumption model."""
        ...
