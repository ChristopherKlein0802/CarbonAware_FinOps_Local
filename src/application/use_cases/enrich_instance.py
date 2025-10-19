"""
EnrichInstanceUseCase - Instance enrichment with runtime and emissions data

Enriches EC2 instances with runtime, pricing, power, and emissions data.
"""

import logging
from typing import Dict, List, Optional

from src.domain.models import EC2Instance
from src.domain.services import RuntimeService

logger = logging.getLogger(__name__)


class EnrichInstanceUseCase:
    """
    Enrich EC2 instance with runtime, pricing, power, and emissions.

    Delegates to RuntimeService and handles failures gracefully.
    """

    def __init__(self, runtime_service: RuntimeService):
        """
        Initialize with runtime service.

        Args:
            runtime_service: Runtime data and instance enrichment
        """
        self.runtime_service = runtime_service

    def execute(
        self,
        instance: EC2Instance,
        carbon_intensity: float,
        *,
        carbon_history: Optional[List[Dict]] = None,
        force_refresh: bool = False,
    ) -> Optional[EC2Instance]:
        """
        Enrich EC2 instance with runtime, pricing, power, and emissions.

        Args:
            instance: EC2 instance to enrich
            carbon_intensity: Current carbon intensity (gCO2/kWh) - used as fallback
            carbon_history: Optional 24h carbon history for hourly-precise calculation
            force_refresh: Bypass cache

        Returns:
            Enriched EC2Instance or None if failed
        """
        try:
            enriched = self.runtime_service.enrich_instance(
                instance,
                carbon_intensity=carbon_intensity,
                carbon_history=carbon_history,
                force_refresh=force_refresh,
            )

            if enriched:
                logger.debug(f"Enriched instance {instance['instance_id']} (method: {enriched.co2_calculation_method})")
                return enriched
            else:
                logger.warning(f"Failed to enrich instance {instance['instance_id']}")
                return None

        except Exception as e:
            logger.error(f"Error enriching instance {instance['instance_id']}: {e}")
            return None
