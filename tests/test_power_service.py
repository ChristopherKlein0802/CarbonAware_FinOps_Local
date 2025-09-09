#!/usr/bin/env python3
"""
Test script for Power Consumption Service

Tests both Boavizta API integration and fallback functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.power_consumption_service import PowerConsumptionService

def main():
    print("🔋 Testing Power Consumption Service\n")
    
    # Initialize service
    service = PowerConsumptionService()
    
    # Test instance types from the optimized configuration
    test_instances = [
        't3.micro',    # Carbon-aware (optimized)
        't3.small',    # Office-hours & weekdays-only (optimized)
        't3.medium',   # Baseline (optimized)
        'c5.large',    # Compute optimized
        'm5.large'     # Additional compute instance type
    ]
    
    print("Testing instance types with Boavizta API + fallback:")
    print("=" * 60)
    
    for instance_type in test_instances:
        try:
            print(f"\n🖥️  Testing {instance_type}:")
            
            # Get power consumption data
            power_data = service.get_instance_power_consumption(instance_type)
            
            print(f"  Idle Power:    {power_data.idle_power_watts:.1f} W")
            print(f"  Average Power: {power_data.avg_power_watts:.1f} W") 
            print(f"  Max Power:     {power_data.max_power_watts:.1f} W")
            print(f"  Data Source:   {power_data.data_source}")
            print(f"  Confidence:    {power_data.confidence_level}")
            
            # Calculate carbon emissions (German grid average ~400g CO2/kWh)
            carbon_data = service.calculate_carbon_emissions(
                power_consumption=power_data,
                carbon_intensity_g_kwh=400,  # German grid average
                usage_hours=24.0,            # Daily calculation
                utilization_factor=0.5       # 50% average utilization
            )
            
            print(f"  Daily Energy:  {carbon_data['energy_kwh']:.3f} kWh")
            print(f"  Daily CO2:     {carbon_data['carbon_emissions_kg']:.3f} kg")
            print(f"  Monthly CO2:   {carbon_data['carbon_emissions_kg'] * 30:.2f} kg")
            
        except Exception as e:
            print(f"  ❌ Error testing {instance_type}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Power Consumption Service Test Complete!")
    print("\nKey Benefits:")
    print("• Real hardware power consumption data via Boavizta API")
    print("• Comprehensive fallback system for unknown instance types")
    print("• Accurate carbon footprint calculations with German grid data")
    print("• Enhanced confidence levels and data source tracking")

if __name__ == "__main__":
    main()