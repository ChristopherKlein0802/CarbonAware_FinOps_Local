"""
Power Consumption Service for Carbon-Aware FinOps

Integrates with Boavizta API to get real hardware power consumption data
with fallback to estimated values for comprehensive carbon footprint calculation.

Boavizta API Documentation: https://doc.api.boavizta.org/
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PowerConsumption:
    """Power consumption data for an EC2 instance"""
    idle_power_watts: float
    max_power_watts: float 
    avg_power_watts: float
    confidence_level: str  # "high", "medium", "low"
    data_source: str  # "boavizta", "fallback"
    
class PowerConsumptionService:
    """Service to get hardware power consumption data from Boavizta API"""
    
    def __init__(self):
        self.boavizta_base_url = "https://api.boavizta.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Cache for API responses to avoid repeated calls
        self._power_cache: Dict[str, PowerConsumption] = {}
        
        # Simplified fallback power consumption data for Bachelor Thesis
        self._fallback_power_data = {
            't3.micro': {'idle': 3.5, 'max': 7.0},
            't3.small': {'idle': 7.0, 'max': 14.0},
            't3.medium': {'idle': 14.0, 'max': 28.0},
            't3.large': {'idle': 28.0, 'max': 56.0},
            'c5.large': {'idle': 25.0, 'max': 50.0},
        }
    
    def get_instance_power_consumption(self, instance_type: str) -> PowerConsumption:
        """
        Get power consumption data for an EC2 instance type
        
        Args:
            instance_type: AWS EC2 instance type (e.g., "t3.micro")
            
        Returns:
            PowerConsumption object with power data and metadata
        """
        cache_key = instance_type
        
        # Check cache first
        if cache_key in self._power_cache:
            logger.debug(f"Using cached power data for {instance_type}")
            return self._power_cache[cache_key]
        
        # Try Boavizta API first
        try:
            power_data = self._get_boavizta_power_data(instance_type)
            if power_data:
                self._power_cache[cache_key] = power_data
                return power_data
        except Exception as e:
            logger.warning(f"Boavizta API failed for {instance_type}: {e}")
        
        # Fall back to estimated data
        logger.info(f"Using fallback power data for {instance_type}")
        fallback_data = self._get_fallback_power_data(instance_type)
        self._power_cache[cache_key] = fallback_data
        return fallback_data
    
    def _get_boavizta_power_data(self, instance_type: str) -> Optional[PowerConsumption]:
        """Get power consumption data from Boavizta API"""
        
        # Direct AWS instance type mapping - no conversion needed with new API format
        
        try:
            # Boavizta cloud API endpoint for AWS instances
            endpoint = f"{self.boavizta_base_url}/cloud/instance"
            
            # Use correct payload format based on working API test
            payload = {
                "provider": "aws",
                "instance_type": instance_type,  # Use AWS instance type directly
                "location": "FRA",  # Frankfurt for eu-central-1
                "verbose": True
            }
            
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_boavizta_response(data, instance_type)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Boavizta API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Boavizta response: {e}")
            return None
    
    
    def _parse_boavizta_response(self, data: Dict, instance_type: str) -> PowerConsumption:
        """Parse Boavizta API response to extract power consumption"""
        
        try:
            # Extract avg_power from verbose data (this is the key field we found in testing)
            verbose_data = data.get('verbose', {})
            avg_power_data = verbose_data.get('avg_power', {})
            
            # avg_power is a dict with 'value', 'min', 'max', 'unit'
            if isinstance(avg_power_data, dict) and 'value' in avg_power_data:
                avg_power = avg_power_data['value']
                min_power = avg_power_data.get('min', avg_power * 0.8)
                max_power = avg_power_data.get('max', avg_power * 1.2)
            else:
                # Fallback: try to extract from impacts section
                power_data = data.get('impacts', {}).get('pe', {})
                usage_power = power_data.get('use', {}).get('value', 0)
                avg_power = usage_power if usage_power > 0 else 20.0  # Default fallback
                min_power = avg_power * 0.8
                max_power = avg_power * 1.2
            
            # Use Boavizta's min as idle power if available, otherwise calculate
            idle_power = min_power if 'min_power' in locals() else avg_power * 0.9  # Boavizta min is close to idle
            # Use Boavizta's max power if available, otherwise calculate  
            max_power_final = max_power if 'max_power' in locals() else avg_power * 1.2
            
            return PowerConsumption(
                idle_power_watts=idle_power,
                max_power_watts=max_power_final,
                avg_power_watts=avg_power,
                confidence_level="high",
                data_source="boavizta"
            )
            
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error parsing Boavizta data for {instance_type}: {e}")
            raise
    
    def _get_fallback_power_data(self, instance_type: str) -> PowerConsumption:
        """Get fallback power consumption data for common instance types"""
        
        # Direct lookup for known instance types
        if instance_type in self._fallback_power_data:
            data = self._fallback_power_data[instance_type]
            idle_power = data['idle']
            max_power = data['max']
            avg_power = (idle_power + max_power) / 2
            confidence = "medium"
        else:
            # Estimate for unknown instance types based on family patterns
            idle_power, max_power = self._estimate_power_from_pattern(instance_type)
            avg_power = (idle_power + max_power) / 2
            confidence = "low"
        
        return PowerConsumption(
            idle_power_watts=idle_power,
            max_power_watts=max_power,
            avg_power_watts=avg_power,
            confidence_level=confidence,
            data_source="fallback"
        )
    
    def _estimate_power_from_pattern(self, instance_type: str) -> Tuple[float, float]:
        """Simplified power estimation for unknown instance types"""
        
        parts = instance_type.split('.')
        if len(parts) != 2:
            return 20.0, 40.0  # Default fallback
            
        size = parts[1]
        
        # Simple size-based estimation
        size_power = {
            'micro': 7.0, 'small': 14.0, 'medium': 28.0, 
            'large': 56.0, 'xlarge': 112.0
        }
        
        max_power = size_power.get(size, 28.0)  # Default to medium
        idle_power = max_power * 0.5  # 50% at idle
        
        return idle_power, max_power
    
    def calculate_carbon_emissions(self, power_consumption: PowerConsumption, 
                                 carbon_intensity_g_kwh: float, 
                                 usage_hours: float = 1.0,
                                 utilization_factor: float = 0.5) -> Dict[str, float]:
        """
        Calculate carbon emissions based on power consumption and grid carbon intensity
        
        Args:
            power_consumption: Power consumption data
            carbon_intensity_g_kwh: Grid carbon intensity in grams CO2 per kWh
            usage_hours: Number of hours of usage
            utilization_factor: CPU utilization factor (0.0 to 1.0)
            
        Returns:
            Dictionary with carbon emission calculations
        """
        
        # Calculate actual power based on utilization
        # Linear interpolation between idle and max power
        actual_power_watts = (
            power_consumption.idle_power_watts + 
            (power_consumption.max_power_watts - power_consumption.idle_power_watts) * utilization_factor
        )
        
        # Convert to kWh
        energy_kwh = (actual_power_watts / 1000.0) * usage_hours
        
        # Calculate carbon emissions in grams CO2
        carbon_emissions_g = energy_kwh * carbon_intensity_g_kwh
        
        return {
            'power_watts': float(actual_power_watts),
            'energy_kwh': float(energy_kwh),
            'carbon_emissions_g': float(carbon_emissions_g),
            'carbon_emissions_kg': float(carbon_emissions_g / 1000.0),
            'utilization_factor': float(utilization_factor)
        }