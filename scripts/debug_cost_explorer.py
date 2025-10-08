#!/usr/bin/env python3
"""
Debug Script for AWS Cost Explorer Region Filtering

This script helps identify the correct region dimension values
for Cost Explorer API filtering.

Usage:
    python scripts/debug_cost_explorer.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
import json
from datetime import datetime, timedelta
from src.config import settings

def debug_cost_explorer():
    """Debug AWS Cost Explorer to find correct region dimension values."""

    print("=" * 80)
    print("AWS COST EXPLORER DEBUG TOOL")
    print("=" * 80)
    print(f"\n🔍 Using AWS Profile: {settings.aws_profile}")
    print(f"🔍 Target Region: {settings.aws_region}")

    try:
        session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
        ce_client = session.client("ce", region_name="us-east-1")  # Cost Explorer is always us-east-1

        # Calculate time range (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        print(f"\n📅 Time Range: {start_date} to {end_date}")

        # -------------------------------------------------------------------
        # TEST 1: Get all available dimension values for REGION
        # -------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST 1: Available REGION Dimension Values")
        print("=" * 80)

        try:
            response = ce_client.get_dimension_values(
                TimePeriod={"Start": str(start_date), "End": str(end_date)},
                Dimension="REGION",
                Context="COST_AND_USAGE",
            )

            regions = [item["Value"] for item in response.get("DimensionValues", [])]
            print(f"\n✅ Found {len(regions)} regions with cost data:")
            for region in sorted(regions):
                print(f"   - {region}")

        except Exception as error:
            print(f"❌ Error getting REGION dimensions: {error}")

        # -------------------------------------------------------------------
        # TEST 2: Get all available SERVICE dimension values
        # -------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST 2: EC2-Related SERVICE Dimension Values")
        print("=" * 80)

        try:
            response = ce_client.get_dimension_values(
                TimePeriod={"Start": str(start_date), "End": str(end_date)},
                Dimension="SERVICE",
                Context="COST_AND_USAGE",
            )

            services = [item["Value"] for item in response.get("DimensionValues", [])]
            ec2_services = [s for s in services if "EC2" in s or "Elastic Compute" in s]

            print(f"\n✅ Found {len(ec2_services)} EC2-related services:")
            for service in sorted(ec2_services):
                print(f"   - {service}")

        except Exception as error:
            print(f"❌ Error getting SERVICE dimensions: {error}")

        # -------------------------------------------------------------------
        # TEST 3: Get costs WITHOUT region filter (baseline)
        # -------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST 3: Costs WITHOUT Region Filter (Baseline)")
        print("=" * 80)

        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={"Start": str(start_date), "End": str(end_date)},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                Filter={
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": ["Amazon Elastic Compute Cloud - Compute"]
                    }
                },
                GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
            )

            print("\n✅ Cost data by region (EC2 Compute only):")
            for result in response.get("ResultsByTime", []):
                period = result.get("TimePeriod", {})
                print(f"\n   Period: {period.get('Start')} to {period.get('End')}")

                groups = result.get("Groups", [])
                if not groups:
                    print("   ⚠️ No groups found!")
                    continue

                for group in groups:
                    region = group.get("Keys", ["Unknown"])[0]
                    cost = group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
                    cost_float = float(cost)
                    if cost_float > 0:
                        print(f"      {region}: ${cost_float:.2f}")

        except Exception as error:
            print(f"❌ Error getting costs without filter: {error}")

        # -------------------------------------------------------------------
        # TEST 4: Get costs WITH eu-central-1 filter (various formats)
        # -------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST 4: Costs WITH eu-central-1 Filter (Testing Formats)")
        print("=" * 80)

        test_formats = [
            "eu-central-1",
            "EU (Frankfurt)",
            "Europe (Frankfurt)",
            "eu_central_1",
        ]

        for region_format in test_formats:
            print(f"\n🔍 Testing region format: '{region_format}'")
            try:
                response = ce_client.get_cost_and_usage(
                    TimePeriod={"Start": str(start_date), "End": str(end_date)},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                    Filter={
                        "And": [
                            {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
                            {"Dimensions": {"Key": "REGION", "Values": [region_format]}},
                        ]
                    },
                )

                total_cost = 0.0
                for result in response.get("ResultsByTime", []):
                    cost = result.get("Total", {}).get("UnblendedCost", {}).get("Amount", "0")
                    total_cost += float(cost)

                if total_cost > 0:
                    print(f"   ✅ SUCCESS: ${total_cost:.2f}")
                else:
                    print(f"   ⚠️ No cost data returned (filter might be too restrictive)")

            except Exception as error:
                print(f"   ❌ Error: {error}")

        # -------------------------------------------------------------------
        # TEST 5: Detailed cost breakdown by service (all EC2)
        # -------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("TEST 5: Detailed EC2 Cost Breakdown (All Services)")
        print("=" * 80)

        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={"Start": str(start_date), "End": str(end_date)},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                Filter={
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": [
                            "Amazon Elastic Compute Cloud - Compute",
                            "EC2 - Other",
                            "Amazon Elastic Compute Cloud",
                        ]
                    }
                },
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            print("\n✅ EC2 cost breakdown by service:")
            total = 0.0
            for result in response.get("ResultsByTime", []):
                period = result.get("TimePeriod", {})
                print(f"\n   Period: {period.get('Start')} to {period.get('End')}")

                for group in result.get("Groups", []):
                    service = group.get("Keys", ["Unknown"])[0]
                    cost = group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0")
                    cost_float = float(cost)
                    if cost_float > 0:
                        print(f"      {service}: ${cost_float:.2f}")
                        total += cost_float

            print(f"\n   💰 Total EC2 Costs: ${total:.2f}")

        except Exception as error:
            print(f"❌ Error getting detailed breakdown: {error}")

        # -------------------------------------------------------------------
        # SUMMARY & RECOMMENDATIONS
        # -------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("SUMMARY & RECOMMENDATIONS")
        print("=" * 80)

        print("""
📊 ANALYSIS COMPLETE

🎯 Next Steps:
1. Check TEST 1 output for correct region string format
2. Compare TEST 3 (no filter) vs TEST 4 (with filter) results
3. If TEST 4 shows $0.00 for all formats, region filtering may not work as expected
4. Consider using region-agnostic approach and document as "Known AWS Limitation"

📝 Recommendations:
- If TEST 1 shows "eu-central-1" AND TEST 4 works with that format → Use it!
- If all TEST 4 attempts fail → Document as limitation, use aggregated costs
- Alternative: Use tags or resource-level cost allocation for better granularity

🔗 Documentation:
Update docs/methodology/cost-explorer-analysis.md with findings from this debug session.
        """)

    except Exception as error:
        print(f"\n❌ Fatal error: {error}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(debug_cost_explorer())
