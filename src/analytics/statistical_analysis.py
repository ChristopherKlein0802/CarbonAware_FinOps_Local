"""
Statistical Analysis Module for Carbon-Aware FinOps

Provides confidence intervals for carbon calculations in the Bachelor Thesis
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class StatisticalAnalyzer:
    """Provides statistical confidence intervals for carbon calculations"""
    
    def __init__(self):
        # Uncertainty factors for different data sources
        self.uncertainty_factors = {
            'boavizta': 0.05,    # 5% uncertainty for scientific data
            'fallback': 0.15,    # 15% uncertainty for estimates
            'electricitymap': 0.08,  # 8% uncertainty for grid data
            'aws_costs': 0.02    # 2% uncertainty for billing data
        }
    
    def calculate_confidence_interval(self, value: float, data_source: str, 
                                    confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for carbon/cost calculations
        
        Args:
            value: The calculated value (CO2 or cost)
            data_source: Source of the data (boavizta, fallback, etc.)
            confidence_level: Statistical confidence level (default 95%)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        uncertainty = self.uncertainty_factors.get(data_source, 0.20)  # 20% default
        margin_of_error = value * uncertainty
        
        # Simple confidence interval calculation (95% ≈ ±1.96σ, simplified to ±2σ)
        z_score = 2.0 if confidence_level >= 0.95 else 1.64  # 95% or 90%
        interval_width = z_score * margin_of_error
        
        lower_bound = max(0, value - interval_width)  # Can't be negative
        upper_bound = value + interval_width
        
        return lower_bound, upper_bound
    
    def carbon_calculation_with_confidence(self, power_watts: float, 
                                         carbon_intensity: float,
                                         hours: float,
                                         power_source: str = 'fallback',
                                         grid_source: str = 'electricitymap') -> Dict:
        """
        Calculate carbon emissions with statistical confidence intervals
        
        Returns comprehensive statistical analysis of carbon calculation
        """
        # Base calculation
        energy_kwh = (power_watts * hours) / 1000
        carbon_kg = (energy_kwh * carbon_intensity) / 1000
        
        # Power consumption confidence interval
        power_lower, power_upper = self.calculate_confidence_interval(
            power_watts, power_source
        )
        
        # Grid intensity confidence interval  
        grid_lower, grid_upper = self.calculate_confidence_interval(
            carbon_intensity, grid_source
        )
        
        # Combined uncertainty for carbon calculation
        # Worst case: high power + high grid intensity
        carbon_upper = ((power_upper * hours) / 1000 * grid_upper) / 1000
        # Best case: low power + low grid intensity
        carbon_lower = ((power_lower * hours) / 1000 * grid_lower) / 1000
        
        return {
            'carbon_kg_estimate': carbon_kg,
            'carbon_kg_lower_95': carbon_lower,
            'carbon_kg_upper_95': carbon_upper,
            'confidence_interval_width': carbon_upper - carbon_lower,
            'relative_uncertainty_percent': ((carbon_upper - carbon_lower) / carbon_kg) * 50,
            'power_confidence': (power_lower, power_upper),
            'grid_confidence': (grid_lower, grid_upper),
            'data_quality_score': self._calculate_data_quality_score(power_source, grid_source)
        }
    
    def _calculate_data_quality_score(self, power_source: str, grid_source: str) -> float:
        """Calculate overall data quality score (0-100)"""
        power_quality = {
            'boavizta': 90,
            'fallback': 60,
            'estimated': 40
        }.get(power_source, 40)
        
        grid_quality = {
            'electricitymap': 85,
            'fallback': 55,
            'estimated': 35
        }.get(grid_source, 35)
        
        return (power_quality + grid_quality) / 2