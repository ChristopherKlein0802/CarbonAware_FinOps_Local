"""
Statistical Analysis Module for Carbon-Aware FinOps

Adds academic rigor through statistical validation and confidence intervals
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class StatisticalAnalyzer:
    """Provides statistical analysis and confidence intervals for carbon calculations"""
    
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
        
        # Calculate confidence interval using normal distribution
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
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
    
    def optimization_significance_test(self, baseline_carbon: float, 
                                     optimized_carbon: float,
                                     baseline_source: str = 'fallback',
                                     optimized_source: str = 'fallback') -> Dict:
        """
        Statistical test to determine if optimization is statistically significant
        """
        # Calculate confidence intervals for both scenarios
        baseline_lower, baseline_upper = self.calculate_confidence_interval(
            baseline_carbon, baseline_source
        )
        optimized_lower, optimized_upper = self.calculate_confidence_interval(
            optimized_carbon, optimized_source
        )
        
        # Check if confidence intervals overlap
        intervals_overlap = baseline_lower <= optimized_upper and optimized_lower <= baseline_upper
        
        # Calculate effect size (Cohen's d equivalent for carbon reduction)
        reduction_percent = ((baseline_carbon - optimized_carbon) / baseline_carbon) * 100
        
        # Significance assessment
        if not intervals_overlap and reduction_percent > 10:
            significance = "statistically_significant"
        elif reduction_percent > 5:
            significance = "likely_significant"
        else:
            significance = "not_significant"
        
        return {
            'baseline_confidence': (baseline_lower, baseline_upper),
            'optimized_confidence': (optimized_lower, optimized_upper),
            'intervals_overlap': intervals_overlap,
            'reduction_percent': reduction_percent,
            'significance_assessment': significance,
            'minimum_detectable_reduction': self._minimum_detectable_effect(baseline_carbon, baseline_source)
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
    
    def _minimum_detectable_effect(self, baseline: float, source: str) -> float:
        """Calculate minimum carbon reduction that would be statistically detectable"""
        uncertainty = self.uncertainty_factors.get(source, 0.20)
        # Rule of thumb: need 2x the uncertainty to detect a significant change
        return baseline * uncertainty * 2
    
    def generate_statistical_summary(self, carbon_data: List[Dict]) -> Dict:
        """
        Generate comprehensive statistical summary for thesis documentation
        """
        if not carbon_data:
            return {}
        
        carbon_values = [item['carbon_kg'] for item in carbon_data]
        
        return {
            'sample_size': len(carbon_values),
            'mean_carbon_kg': np.mean(carbon_values),
            'std_deviation': np.std(carbon_values),
            'median_carbon_kg': np.median(carbon_values),
            'min_carbon_kg': np.min(carbon_values),
            'max_carbon_kg': np.max(carbon_values),
            'coefficient_of_variation': np.std(carbon_values) / np.mean(carbon_values),
            'statistical_power': self._calculate_statistical_power(carbon_values),
            'recommendations': self._generate_statistical_recommendations(carbon_values)
        }
    
    def _calculate_statistical_power(self, values: List[float]) -> float:
        """Calculate statistical power of the analysis"""
        if len(values) < 2:
            return 0.0
        
        # Simplified power calculation based on sample size and variance
        n = len(values)
        cv = np.std(values) / np.mean(values) if np.mean(values) > 0 else 1
        
        # Rule of thumb: power increases with sample size, decreases with variance
        power = min(0.95, (n * 0.1) / (1 + cv))
        return power
    
    def _generate_statistical_recommendations(self, values: List[float]) -> List[str]:
        """Generate recommendations for improving statistical analysis"""
        recommendations = []
        
        if len(values) < 10:
            recommendations.append("Increase sample size for more robust statistics")
        
        cv = np.std(values) / np.mean(values) if np.mean(values) > 0 else 1
        if cv > 0.5:
            recommendations.append("High variability detected - consider data quality improvements")
        
        if len(set(values)) == 1:
            recommendations.append("No variance in data - verify calculation methodology")
        
        return recommendations