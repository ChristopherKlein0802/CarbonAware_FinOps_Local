"""
Parametric Sensitivity Analysis for SME Scaling
Bachelor Thesis: Carbon-Aware FinOps Tool

IMPORTANT METHODOLOGICAL DISCLAIMER:
This module performs PARAMETER EXPLORATION, not statistical prediction.
All input parameters are estimates for academic exploration only.
Results demonstrate methodology sensitivity, not validated performance.

Purpose: Explore how different parameter assumptions affect scaling projections
Method: Monte Carlo parameter sampling for sensitivity analysis
Academic Status: Educational simulation - not predictive modeling
"""

import random
import numpy as np
from typing import Dict, List, Tuple
import logging
from dataclasses import dataclass
from scipy import stats

logger = logging.getLogger(__name__)

@dataclass
class SimulationResult:
    """Results from Monte Carlo simulation run"""
    cost_savings_eur: float
    co2_savings_kg: float
    roi_months: float
    instances_count: int
    carbon_intensity: float
    optimization_efficiency: float

class MonteCarloSMEScaling:
    """
    Monte-Carlo simulation for SME scaling analysis
    
    ACADEMIC PURPOSE:
    - Addresses the limitation of our 4-instance test environment
    - Provides statistical projections for realistic SME scales (20-100 instances)
    - Quantifies uncertainty through probability distributions
    - Maintains scientific honesty by labeling as "simulated projections"
    """
    
    def __init__(self):
        """Initialize Monte-Carlo parameters based on realistic SME distributions"""
        
        # SME Infrastructure Size Distributions (based on SME surveys)
        self.sme_size_distribution = {
            'small_sme': {'min': 15, 'max': 30, 'mean': 22},      # Small SME
            'medium_sme': {'min': 30, 'max': 70, 'mean': 50},     # Medium SME  
            'large_sme': {'min': 70, 'max': 120, 'mean': 85}      # Large SME (thesis scope limit)
        }
        
        # Carbon Intensity Parameter Range (for sensitivity analysis)
        # NOTE: These are illustrative ranges for academic exploration
        # Real applications require validated historical data
        self.carbon_params = {
            'min': 250,        # Approximate clean periods (illustrative)
            'max': 550,        # Approximate peak periods (illustrative) 
            'mean': 380,       # Rough 2025 estimate (unvalidated)
            'std': 85          # Assumed variability (parameter exploration)
        }
        # DISCLAIMER: No validated German grid historical data source
        
        # Instance Type Parameters (for modeling purposes)
        # NOTE: These are approximations for academic simulation
        # Power values are rough estimates, not validated measurements
        self.instance_types = {
            't3.micro': {'probability': 0.15, 'hourly_cost_eur': 0.018, 'power_watts': 8.2},
            't3.small': {'probability': 0.35, 'hourly_cost_eur': 0.023, 'power_watts': 10.7}, 
            't3.medium': {'probability': 0.30, 'hourly_cost_eur': 0.032, 'power_watts': 11.5},
            't3.large': {'probability': 0.15, 'hourly_cost_eur': 0.055, 'power_watts': 18.4},
            't3.xlarge': {'probability': 0.05, 'hourly_cost_eur': 0.110, 'power_watts': 28.3}
        }
        # DISCLAIMER: Power values are estimates from various sources, not validated
        
        # Optimization Parameter Exploration Ranges
        # IMPORTANT: These are hypothetical ranges for sensitivity analysis
        # NOT validated from empirical studies
        self.optimization_params = {
            'office_hours_factor': {'mean': 0.65, 'std': 0.10, 'min': 0.45, 'max': 0.80},
            'carbon_reduction_factor': {'mean': 0.15, 'std': 0.08, 'min': 0.05, 'max': 0.30},
            'integration_efficiency': {'mean': 0.85, 'std': 0.10, 'min': 0.70, 'max': 0.95},
            'schedulable_workload_pct': {'mean': 0.50, 'std': 0.15, 'min': 0.20, 'max': 0.80}
        }
        # DISCLAIMER: All optimization factors are assumptions for academic modeling
        
        # Implementation Cost Parameter Range (illustrative)
        # NOTE: These are rough estimates for academic exploration
        # Real costs vary significantly based on specific requirements
        self.implementation_cost = {
            'mean': 12000,     # Illustrative mean for modeling
            'std': 5000,       # Assumed high variability
            'min': 5000,       # Theoretical minimum
            'max': 25000       # Theoretical maximum
        }
        # DISCLAIMER: No validated SME implementation cost data
        
        logger.info("✅ Monte-Carlo SME scaling simulation initialized")
    
    def generate_sme_infrastructure(self, sme_category: str) -> List[Dict]:
        """Generate realistic SME infrastructure mix"""
        
        size_params = self.sme_size_distribution[sme_category]
        instance_count = random.randint(size_params['min'], size_params['max'])
        
        infrastructure = []
        
        for i in range(instance_count):
            # Select instance type based on probability distribution
            instance_type = np.random.choice(
                list(self.instance_types.keys()),
                p=[self.instance_types[t]['probability'] for t in self.instance_types]
            )
            
            type_params = self.instance_types[instance_type]
            
            # Add realistic variation to costs and power
            cost_variation = random.uniform(0.90, 1.10)  # ±10% cost variation
            power_variation = random.uniform(0.85, 1.15)  # ±15% power variation
            
            infrastructure.append({
                'type': instance_type,
                'hourly_cost_eur': type_params['hourly_cost_eur'] * cost_variation,
                'power_watts': type_params['power_watts'] * power_variation,
                'monthly_hours': random.uniform(400, 720),  # Variable usage patterns
                'schedulable': random.random() < self.optimization_params['schedulable_workload_pct']['mean']
            })
        
        return infrastructure
    
    def simulate_carbon_intensity(self) -> float:
        """Simulate German grid carbon intensity with realistic distribution"""
        
        # Use truncated normal distribution to avoid unrealistic extremes
        carbon_intensity = stats.truncnorm.rvs(
            (self.carbon_params['min'] - self.carbon_params['mean']) / self.carbon_params['std'],
            (self.carbon_params['max'] - self.carbon_params['mean']) / self.carbon_params['std'],
            loc=self.carbon_params['mean'],
            scale=self.carbon_params['std']
        )
        
        return max(self.carbon_params['min'], min(carbon_intensity, self.carbon_params['max']))
    
    def simulate_optimization_factors(self) -> Dict:
        """Generate realistic optimization efficiency factors"""
        
        factors = {}
        
        for param_name, param_config in self.optimization_params.items():
            # Use truncated normal distribution
            factor = stats.truncnorm.rvs(
                (param_config['min'] - param_config['mean']) / param_config['std'],
                (param_config['max'] - param_config['mean']) / param_config['std'],
                loc=param_config['mean'],
                scale=param_config['std']
            )
            factors[param_name] = max(param_config['min'], min(factor, param_config['max']))
        
        return factors
    
    def calculate_baseline_metrics(self, infrastructure: List[Dict], carbon_intensity: float) -> Dict:
        """Calculate baseline cost and CO2 for infrastructure"""
        
        total_monthly_cost = 0
        total_monthly_power_kwh = 0
        
        for instance in infrastructure:
            monthly_cost = instance['hourly_cost_eur'] * instance['monthly_hours']
            monthly_power = (instance['power_watts'] * instance['monthly_hours']) / 1000
            
            total_monthly_cost += monthly_cost
            total_monthly_power_kwh += monthly_power
        
        total_monthly_co2_kg = (total_monthly_power_kwh * carbon_intensity) / 1000
        
        return {
            'monthly_cost_eur': total_monthly_cost,
            'monthly_power_kwh': total_monthly_power_kwh,
            'monthly_co2_kg': total_monthly_co2_kg
        }
    
    def calculate_optimization_savings(self, baseline: Dict, factors: Dict) -> Tuple[float, float]:
        """Calculate optimized savings based on factors"""
        
        # Office Hours optimization (cost focus)
        office_hours_cost_savings = baseline['monthly_cost_eur'] * factors['office_hours_factor'] * factors['schedulable_workload_pct']
        office_hours_co2_savings = baseline['monthly_co2_kg'] * factors['office_hours_factor'] * factors['schedulable_workload_pct']
        
        # Carbon-aware optimization (additional CO2 reduction)
        carbon_aware_co2_savings = baseline['monthly_co2_kg'] * factors['carbon_reduction_factor'] * factors['schedulable_workload_pct']
        
        # Integrated approach (combined with efficiency factor)
        integrated_cost_savings = office_hours_cost_savings * factors['integration_efficiency']
        integrated_co2_savings = (office_hours_co2_savings + carbon_aware_co2_savings) * factors['integration_efficiency']
        
        return integrated_cost_savings, integrated_co2_savings
    
    def simulate_implementation_cost(self) -> float:
        """Simulate realistic implementation cost for SME"""
        
        cost = stats.truncnorm.rvs(
            (self.implementation_cost['min'] - self.implementation_cost['mean']) / self.implementation_cost['std'],
            (self.implementation_cost['max'] - self.implementation_cost['mean']) / self.implementation_cost['std'],
            loc=self.implementation_cost['mean'],
            scale=self.implementation_cost['std']
        )
        
        return max(self.implementation_cost['min'], min(cost, self.implementation_cost['max']))
    
    def run_single_simulation(self, sme_category: str) -> SimulationResult:
        """Run single Monte-Carlo simulation"""
        
        # Generate infrastructure
        infrastructure = self.generate_sme_infrastructure(sme_category)
        
        # Simulate environmental conditions
        carbon_intensity = self.simulate_carbon_intensity()
        
        # Simulate optimization factors
        factors = self.simulate_optimization_factors()
        
        # Calculate baseline metrics
        baseline = self.calculate_baseline_metrics(infrastructure, carbon_intensity)
        
        # Calculate optimized savings
        cost_savings, co2_savings = self.calculate_optimization_savings(baseline, factors)
        
        # Calculate ROI
        implementation_cost = self.simulate_implementation_cost()
        roi_months = implementation_cost / cost_savings if cost_savings > 0 else 999
        
        # Overall optimization efficiency
        total_efficiency = factors['office_hours_factor'] * factors['integration_efficiency']
        
        return SimulationResult(
            cost_savings_eur=cost_savings,
            co2_savings_kg=co2_savings,
            roi_months=min(roi_months, 999),  # Cap at 999 months
            instances_count=len(infrastructure),
            carbon_intensity=carbon_intensity,
            optimization_efficiency=total_efficiency
        )
    
    def run_monte_carlo_analysis(self, sme_category: str, num_simulations: int = 10000) -> Dict:
        """
        Run comprehensive Monte-Carlo analysis for SME category
        
        Args:
            sme_category: 'small_sme', 'medium_sme', or 'large_sme'
            num_simulations: Number of simulation runs (default: 10,000)
        
        Returns:
            Statistical analysis of simulation results
        """
        
        logger.info(f"🎲 Starting Monte-Carlo analysis: {sme_category} ({num_simulations:,} simulations)")
        
        results = []
        
        # Run simulations
        for i in range(num_simulations):
            if i % 1000 == 0 and i > 0:
                logger.info(f"   Progress: {i:,}/{num_simulations:,} simulations complete")
            
            result = self.run_single_simulation(sme_category)
            results.append(result)
        
        # Statistical analysis
        cost_savings = [r.cost_savings_eur for r in results]
        co2_savings = [r.co2_savings_kg for r in results]
        roi_months = [r.roi_months for r in results]
        instances_counts = [r.instances_count for r in results]
        carbon_intensities = [r.carbon_intensity for r in results]
        
        # Calculate percentiles
        cost_percentiles = np.percentile(cost_savings, [5, 25, 50, 75, 95])
        co2_percentiles = np.percentile(co2_savings, [5, 25, 50, 75, 95])
        roi_percentiles = np.percentile(roi_months, [5, 25, 50, 75, 95])
        
        # Business viability analysis
        viable_simulations = sum(1 for r in roi_months if r <= 60)  # ≤5 years ROI
        viability_rate = viable_simulations / num_simulations * 100
        
        analysis = {
            'simulation_metadata': {
                'sme_category': sme_category,
                'num_simulations': num_simulations,
                'methodology': 'Monte-Carlo with realistic SME parameter distributions',
                'disclaimer': 'SIMULATED PROJECTIONS - Not validated results'
            },
            'infrastructure_analysis': {
                'instances_count': {
                    'mean': np.mean(instances_counts),
                    'median': np.median(instances_counts),
                    'std': np.std(instances_counts),
                    'range': [min(instances_counts), max(instances_counts)]
                },
                'carbon_intensity': {
                    'mean_g_co2_kwh': np.mean(carbon_intensities),
                    'median_g_co2_kwh': np.median(carbon_intensities),
                    'std_g_co2_kwh': np.std(carbon_intensities)
                }
            },
            'cost_savings_analysis': {
                'mean_monthly_eur': np.mean(cost_savings),
                'median_monthly_eur': np.median(cost_savings),
                'std_monthly_eur': np.std(cost_savings),
                'percentiles': {
                    '5th': cost_percentiles[0],
                    '25th': cost_percentiles[1], 
                    '50th': cost_percentiles[2],
                    '75th': cost_percentiles[3],
                    '95th': cost_percentiles[4]
                },
                'confidence_interval_95': [cost_percentiles[0], cost_percentiles[4]]
            },
            'co2_savings_analysis': {
                'mean_monthly_kg': np.mean(co2_savings),
                'median_monthly_kg': np.median(co2_savings),
                'std_monthly_kg': np.std(co2_savings),
                'percentiles': {
                    '5th': co2_percentiles[0],
                    '25th': co2_percentiles[1],
                    '50th': co2_percentiles[2], 
                    '75th': co2_percentiles[3],
                    '95th': co2_percentiles[4]
                },
                'confidence_interval_95': [co2_percentiles[0], co2_percentiles[4]]
            },
            'roi_analysis': {
                'mean_months': np.mean(roi_months),
                'median_months': np.median(roi_months),
                'std_months': np.std(roi_months),
                'percentiles': {
                    '5th': roi_percentiles[0],
                    '25th': roi_percentiles[1],
                    '50th': roi_percentiles[2],
                    '75th': roi_percentiles[3], 
                    '95th': roi_percentiles[4]
                },
                'business_viability': {
                    'viable_scenarios_pct': viability_rate,
                    'viable_threshold': '≤60 months ROI',
                    'viable_count': viable_simulations
                }
            },
            'academic_assessment': {
                'methodology_demonstration': f'n={num_simulations:,} parameter combinations explore sensitivity',
                'parameter_finding': f'{viability_rate:.1f}% of parameter combinations suggest viable scenarios',
                'thesis_contribution': 'Demonstrates framework for multi-parameter optimization analysis',
                'uncertainty_source': 'All parameters are estimates - real variability unknown',
                'empirical_requirement': 'ALL RESULTS require real-world validation with actual data',
                'predictive_disclaimer': 'NO PREDICTIVE VALUE - Academic methodology exploration only'
            }
        }
        
        logger.info(f"✅ Parameter sensitivity analysis complete: {sme_category}")
        logger.info(f"   Parameter-based median: €{analysis['cost_savings_analysis']['median_monthly_eur']:.2f}")
        logger.info(f"   Parameter-based ROI: {analysis['roi_analysis']['median_months']:.1f} months")
        logger.info(f"   Viable parameter combinations: {viability_rate:.1f}%")
        logger.info(f"   *** DISCLAIMER: All results are parameter exploration, not predictions ***")
        
        return analysis

# Create global instance for dashboard integration
# IMPORTANT: This performs parameter sensitivity analysis, not predictive modeling
parameter_sensitivity = MonteCarloSMEScaling()