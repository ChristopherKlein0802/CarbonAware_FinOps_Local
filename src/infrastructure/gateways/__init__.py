"""Convenience gateway aggregating infrastructure clients."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from src.config import settings
from src.infrastructure.cache import FileCacheRepository
from .aws import AWSClient
from .boavizta import BoaviztaClient
from .electricity import ElectricityClient

__all__ = [
    "InfrastructureGateway",
    "create_default_gateway",
]


class InfrastructureGateway:
    """Aggregates all external API clients used by the domain services."""

    def __init__(
        self,
        *,
        electricity_client: ElectricityClient,
        boavizta_client: BoaviztaClient,
        aws_client: AWSClient,
        region_zone_mapping: Dict[str, str],
    ) -> None:
        self._electricity = electricity_client
        self._boavizta = boavizta_client
        self._aws = aws_client
        self._region_zone_mapping = region_zone_mapping

    # ElectricityMaps -----------------------------------------------------

    def get_current_carbon_intensity(self, region: str) -> Optional[object]:
        return self._electricity.get_current_intensity(region, self._region_zone_mapping)

    def get_carbon_intensity_24h(self, region: str) -> Optional[list[dict]]:
        return self._electricity.get_carbon_intensity_history(region, self._region_zone_mapping)

    def get_self_collected_24h_data(self, region: str) -> Optional[list[dict]]:
        return self._electricity.get_self_collected_history(region)

    # Boavizta ------------------------------------------------------------

    def get_power_consumption(self, instance_type: str):
        return self._boavizta.get_power_consumption(instance_type)

    # AWS: Cost & Pricing -------------------------------------------------

    def get_instance_pricing(self, instance_type: str, region: str) -> Optional[float]:
        return self._aws.get_instance_pricing(instance_type, region)

    def get_costs(self, region: str, period_days: int = 30):
        return self._aws.get_costs(region, period_days)

    def get_hourly_costs(self, hours: int, region: str):
        return self._aws.get_hourly_costs(hours, region)

    # AWS: Runtime (EC2, CloudTrail, CloudWatch) --------------------------

    def list_instances(self, region: str) -> List[Dict]:
        return self._aws.list_instances(region)

    def lookup_instance_events(
        self,
        *,
        instance_id: str,
        region: str,
        lookup_start: datetime,
        lookup_end: datetime,
    ) -> List[Dict]:
        return self._aws.lookup_instance_events(
            instance_id=instance_id,
            region=region,
            lookup_start=lookup_start,
            lookup_end=lookup_end,
        )

    def fetch_cpu_metrics(
        self,
        *,
        instance_id: str,
        region: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        return self._aws.fetch_cpu_metrics(
            instance_id=instance_id,
            region=region,
            start_time=start_time,
            end_time=end_time,
        )

    def get_cached_launch_time(self, instance_id: str, region: str) -> Optional[datetime]:
        return self._aws.get_cached_launch_time(instance_id, region)


def create_default_gateway(repository: FileCacheRepository) -> InfrastructureGateway:
    electricity = ElectricityClient(repository=repository)
    boavizta = BoaviztaClient(repository=repository)
    aws = AWSClient(repository=repository)
    return InfrastructureGateway(
        electricity_client=electricity,
        boavizta_client=boavizta,
        aws_client=aws,
        region_zone_mapping=settings.aws_region_to_zone,
    )
