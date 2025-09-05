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
        
        # Fallback power consumption data (watts) based on AWS instance families
        # Source: AWS documentation, Intel/AMD specs, and industry estimates
        self._fallback_power_data = {
            # General Purpose instances
            't3.nano': {'idle': 2.5, 'max': 5.0},
            't3.micro': {'idle': 3.5, 'max': 7.0},
            't3.small': {'idle': 7.0, 'max': 14.0},
            't3.medium': {'idle': 14.0, 'max': 28.0},
            't3.large': {'idle': 28.0, 'max': 56.0},
            't3.xlarge': {'idle': 56.0, 'max': 112.0},
            
            # Compute optimized
            'c5.large': {'idle': 25.0, 'max': 50.0},
            'c5.xlarge': {'idle': 50.0, 'max': 100.0},
            'c5.2xlarge': {'idle': 100.0, 'max': 200.0},
            
            # Memory optimized  
            'r5.large': {'idle': 30.0, 'max': 60.0},
            'r5.xlarge': {'idle': 60.0, 'max': 120.0},
            'r5.2xlarge': {'idle': 120.0, 'max': 240.0},
            
            # Storage optimized
            'i3.large': {'idle': 35.0, 'max': 70.0},
            'i3.xlarge': {'idle': 70.0, 'max': 140.0},
        }
    
    def get_instance_power_consumption(self, instance_type: str, region: str = "eu-central-1") -> PowerConsumption:
        """
        Get power consumption data for an EC2 instance type
        
        Args:
            instance_type: AWS EC2 instance type (e.g., "t3.micro")
            region: AWS region (used for data center efficiency factors)
            
        Returns:
            PowerConsumption object with power data and metadata
        """
        cache_key = f"{instance_type}_{region}"
        
        # Check cache first
        if cache_key in self._power_cache:
            logger.debug(f"Using cached power data for {instance_type}")
            return self._power_cache[cache_key]
        
        # Try Boavizta API first
        try:
            power_data = self._get_boavizta_power_data(instance_type, region)
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
    
    def _get_boavizta_power_data(self, instance_type: str, region: str) -> Optional[PowerConsumption]:
        """Get power consumption data from Boavizta API"""
        
        # Map AWS instance types to Boavizta format
        boavizta_config = self._map_aws_to_boavizta(instance_type)
        if not boavizta_config:
            logger.warning(f"Could not map {instance_type} to Boavizta format")
            return None
        
        try:
            # Boavizta cloud API endpoint for AWS instances
            endpoint = f"{self.boavizta_base_url}/cloud/instance"
            
            payload = {
                "instance_type": boavizta_config["instance_type"],
                "region": region,
                "usage": {
                    "hours_use_time": 8760,  # Full year for normalization
                    "hours_life_time": 35040,  # 4 years typical server life
                    "usage_location": "DEU"  # Germany for carbon intensity
                }
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
    
    def _map_aws_to_boavizta(self, instance_type: str) -> Optional[Dict]:
        """Map AWS instance types to Boavizta API format"""
        
        # Extract family and size from AWS instance type
        parts = instance_type.split('.')
        if len(parts) != 2:
            return None
            
        family, size = parts[0], parts[1]
        
        # Boavizta uses standardized instance configurations
        # This is a simplified mapping - in production, you'd have more comprehensive mapping
        size_mapping = {
            'nano': {'vcpu': 1, 'memory': 0.5},
            'micro': {'vcpu': 1, 'memory': 1.0},
            'small': {'vcpu': 1, 'memory': 2.0},
            'medium': {'vcpu': 2, 'memory': 4.0},
            'large': {'vcpu': 2, 'memory': 8.0},
            'xlarge': {'vcpu': 4, 'memory': 16.0},
            '2xlarge': {'vcpu': 8, 'memory': 32.0},
        }
        
        if size not in size_mapping:
            logger.warning(f"Unknown instance size: {size}")
            return None
        
        config = size_mapping[size]
        
        return {
            "instance_type": instance_type,
            "vcpu": config['vcpu'],
            "memory": config['memory']
        }
    
    def _parse_boavizta_response(self, data: Dict, instance_type: str) -> PowerConsumption:
        """Parse Boavizta API response to extract power consumption"""
        
        try:
            # Boavizta provides power consumption in the impacts section
            power_data = data.get('impacts', {}).get('pe', {})
            
            # Extract power consumption values (in watts)
            # Boavizta typically provides manufacturing + usage power
            usage_power = power_data.get('use', {}).get('value', 0)
            
            # Estimate idle vs max power (typical ratio is ~0.3-0.7)
            # This is a simplified approach - real implementation would use detailed Boavizta data
            idle_power = usage_power * 0.4  # 40% of usage power at idle
            max_power = usage_power * 1.2   # 120% of usage power at max
            avg_power = usage_power
            
            return PowerConsumption(
                idle_power_watts=idle_power,
                max_power_watts=max_power,
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
        """Estimate power consumption for unknown instance types based on patterns"""
        
        parts = instance_type.split('.')
        if len(parts) != 2:
            # Default for completely unknown instances
            return 20.0, 40.0
            
        family, size = parts[0], parts[1]
        
        # Base power estimates by family type
        family_base_power = {
            't2': 5.0,   # Burstable general purpose
            't3': 7.0,   # Burstable general purpose  
            't4g': 6.0,  # ARM-based burstable
            'm5': 25.0,  # General purpose
            'm6i': 28.0, # General purpose Intel
            'c5': 40.0,  # Compute optimized
            'c6i': 45.0, # Compute optimized Intel
            'r5': 35.0,  # Memory optimized
            'r6i': 40.0, # Memory optimized Intel
            'i3': 50.0,  # Storage optimized
        }
        
        # Size multipliers
        size_multipliers = {
            'nano': 0.5,
            'micro': 1.0,
            'small': 2.0,
            'medium': 4.0,
            'large': 8.0,
            'xlarge': 16.0,
            '2xlarge': 32.0,
            '4xlarge': 64.0,
            '8xlarge': 128.0,
        }
        
        # Get base power for family (default to general purpose if unknown)
        base_power = family_base_power.get(family, 25.0)
        
        # Get size multiplier (default to medium if unknown)
        size_mult = size_multipliers.get(size, 4.0)
        
        # Calculate power consumption
        idle_power = base_power * size_mult * 0.3  # 30% at idle
        max_power = base_power * size_mult
        
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
            'power_watts': actual_power_watts,
            'energy_kwh': energy_kwh,
            'carbon_emissions_g': carbon_emissions_g,
            'carbon_emissions_kg': carbon_emissions_g / 1000.0,
            'utilization_factor': utilization_factor,
            'confidence_level': power_consumption.confidence_level,
            'data_source': power_consumption.data_source
        }