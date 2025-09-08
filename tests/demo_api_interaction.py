#!/usr/bin/env python3
"""
Demo: How ElectricityMap API and Power Consumption API work together
Shows the complete carbon footprint calculation process
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.power_consumption_service import PowerConsumptionService
from src.carbon.carbon_api_client import CarbonIntensityClient

def main():
    print("🌍 ElectricityMap API vs Power Consumption API Demo")
    print("=" * 55)
    
    # Initialize services
    power_service = PowerConsumptionService()
    carbon_client = CarbonIntensityClient()
    
    # Your optimized instance configuration
    instances = [
        {"name": "Baseline", "type": "t3.medium", "schedule": "24/7"},
        {"name": "Office Hours", "type": "t3.small", "schedule": "8h/day"},
        {"name": "Weekdays Only", "type": "t3.small", "schedule": "5 days/week"},
        {"name": "Carbon Aware", "type": "t3.micro", "schedule": "low carbon times"}
    ]
    
    print("\n🔌 Step 1: Get German Grid Carbon Intensity (ElectricityMap API)")
    try:
        carbon_intensity = carbon_client.get_current_intensity('eu-central-1')
        print(f"   Current German Grid: {carbon_intensity} gCO2/kWh")
        print(f"   Source: ElectricityMap API (Real-time)")
    except Exception as e:
        carbon_intensity = 400  # German average fallback
        print(f"   Using German Average: {carbon_intensity} gCO2/kWh")
        print(f"   Source: Fallback (ElectricityMap API unavailable)")
    
    print(f"\n⚡ Step 2: Get Hardware Power Consumption (Boavizta API + Fallback)")
    print("-" * 55)
    
    for instance in instances:
        print(f"\n🖥️  {instance['name']} ({instance['type']}):")
        
        # Get power consumption data
        power_data = power_service.get_instance_power_consumption(instance['type'])
        
        print(f"   Power Data Source: {power_data.data_source}")
        print(f"   Confidence Level:  {power_data.confidence_level}")
        print(f"   Average Power:     {power_data.avg_power_watts:.1f} W")
        
        # Calculate carbon emissions for 24h
        carbon_data = power_service.calculate_carbon_emissions(
            power_consumption=power_data,
            carbon_intensity_g_kwh=carbon_intensity,
            usage_hours=24.0,
            utilization_factor=0.5
        )
        
        print(f"   Daily Energy:      {carbon_data['energy_kwh']:.3f} kWh")
        print(f"   Daily CO2:         {carbon_data['carbon_emissions_kg']:.3f} kg")
        print(f"   Monthly CO2:       {carbon_data['carbon_emissions_kg'] * 30:.2f} kg")
    
    print(f"\n🧮 Step 3: Complete Carbon Footprint Calculation")
    print("-" * 55)
    print("Formula: Carbon Emissions = Power × Time × Grid Intensity")
    print("Example (t3.medium):")
    print("  Power: 21W (from Boavizta API)")
    print(f"  Grid:  {carbon_intensity}g CO2/kWh (from ElectricityMap API)")
    print("  Time:  24 hours")
    print("  Result: 21W × 24h × 420gCO2/kWh = 212g CO2/day")
    
    print(f"\n🎯 Why Both APIs Are Essential:")
    print("-" * 55)
    print("✅ ElectricityMap API:")
    print("   • Real-time grid carbon intensity")
    print("   • Regional specificity (German vs US grid)")
    print("   • Enables carbon-aware scheduling")
    print("   • Shows when electricity is 'cleanest'")
    
    print("\n✅ Power Consumption API (Boavizta):")
    print("   • Scientific hardware power consumption data")
    print("   • Instance-type specific accuracy")
    print("   • Confidence levels and data sources")
    print("   • Enables accurate carbon calculations")
    
    print(f"\n🚀 Combined Benefits:")
    print("-" * 55)
    print("• Complete carbon footprint analysis")
    print("• Real-time optimization potential calculations")
    print("• Scientific rigor with confidence tracking")
    print("• German grid focus for thesis accuracy")

if __name__ == "__main__":
    main()