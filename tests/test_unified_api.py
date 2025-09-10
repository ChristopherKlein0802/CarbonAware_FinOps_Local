#!/usr/bin/env python3
"""
Test script for Unified API Client
Tests all three APIs: Carbon, Power, and AWS Cost data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.api_clients.unified_api_client import (
    UnifiedAPIClient,
    CarbonIntensity,
    PowerConsumption,
    AWSCostData
)

def main():
    print("🔋 Testing Unified API Client\n")
    
    # Initialize unified client
    client = UnifiedAPIClient(aws_profile='carbon-finops-sandbox')
    
    # Test instance types
    test_instances = [
        't3.micro',    # Carbon-aware optimized
        't3.small',    # Office-hours & weekdays optimized  
        't3.medium',   # Baseline optimized
        'c5.large',    # Compute optimized
        'm5.large'     # Additional compute instance
    ]
    
    print("Testing Unified API Client (Carbon + Power + AWS Cost):")
    print("=" * 65)
    
    # Test 1: Carbon intensity
    print("\n🌍 Carbon Intensity (ElectricityMap API):")
    try:
        carbon_intensity = client.get_carbon_intensity('eu-central-1')
        if carbon_intensity:
            print(f"   Current German Grid: {carbon_intensity} gCO2/kWh")
            print(f"   Source: ElectricityMap API (Real-time)")
        else:
            print("   ❌ ElectricityMap API unavailable - NO FALLBACK (as designed)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Power consumption for each instance
    print(f"\n⚡ Power Consumption (Boavizta API):")
    for instance_type in test_instances:
        try:
            power_data = client.get_power_consumption(instance_type)
            
            if power_data:
                print(f"\n🖥️  {instance_type}:")
                print(f"   Average Power: {power_data.avg_power_watts:.1f} W")
                print(f"   Min Power:     {power_data.min_power_watts:.1f} W") 
                print(f"   Max Power:     {power_data.max_power_watts:.1f} W")
                print(f"   Source:        {power_data.source}")
                print(f"   Confidence:    {power_data.confidence_level}")
            else:
                print(f"\n🖥️  {instance_type}: ❌ Boavizta API unavailable - NO FALLBACK (as designed)")
                
        except Exception as e:
            print(f"\n🖥️  {instance_type}: ❌ Error: {e}")
    
    # Test 3: AWS costs
    print(f"\n💰 AWS Costs (Cost Explorer API):")
    try:
        cost_data = client.get_aws_costs()
        
        if cost_data:
            print(f"   Monthly Total: ${cost_data.monthly_cost_usd:.2f} USD")
            print(f"   Region:        {cost_data.region}")
            print(f"   Source:        {cost_data.source}")
            print(f"   Services:      {len(cost_data.service_costs)} different services")
        else:
            print("   ❌ AWS Cost Explorer API unavailable - NO FALLBACK (as designed)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 65)
    print("✅ Unified API Client Test Complete!")
    print("\nArchitecture Benefits:")
    print("• Single client handles ALL external APIs")
    print("• Consistent error handling across all APIs")
    print("• No fallbacks = Pure scientific approach")
    print("• 0 values when APIs unavailable (Bachelor thesis requirement)")

if __name__ == "__main__":
    main()