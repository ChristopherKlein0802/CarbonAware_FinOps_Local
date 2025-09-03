"""
AWS Cost Explorer client for cost analysis.
"""

import boto3
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AWSCostClient:
    """Client for AWS Cost Explorer API."""

    def __init__(self, region: str = "eu-central-1", session: Optional[boto3.Session] = None):
        # Cost Explorer API is only available in us-east-1
        if session:
            self.ce_client = session.client("ce", region_name="us-east-1")
        else:
            self.ce_client = boto3.client("ce", region_name="us-east-1")
        self.region = region

    def get_instance_costs(self, instance_ids: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get cost data for EC2 instances."""

        # Format dates for Cost Explorer
        start = start_date.strftime("%Y-%m-%d")
        end = end_date.strftime("%Y-%m-%d")

        try:
            # Simplified query - get all EC2 costs by instance type
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity="DAILY",
                Metrics=["UnblendedCost", "UsageQuantity"],
                GroupBy=[{"Type": "DIMENSION", "Key": "INSTANCE_TYPE"}],
                Filter={
                    "Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}
                },
            )

            # Convert to DataFrame
            data = []
            for result in response["ResultsByTime"]:
                date = result["TimePeriod"]["Start"]
                
                # If there are groups (by instance type)
                if result["Groups"]:
                    for group in result["Groups"]:
                        instance_type = group["Keys"][0] if group["Keys"] else "Unknown"
                        cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                        usage = float(group["Metrics"]["UsageQuantity"]["Amount"])

                        data.append(
                            {
                                "date": date,
                                "instance_type": instance_type,
                                "cost": cost,
                                "usage_hours": usage,
                            }
                        )
                else:
                    # If no groups, use total cost
                    total_cost = float(result["Total"]["UnblendedCost"]["Amount"]) if "UnblendedCost" in result["Total"] else 0.0
                    if total_cost > 0:
                        data.append(
                            {
                                "date": date,
                                "instance_type": "All",
                                "cost": total_cost,
                                "usage_hours": 0.0,
                            }
                        )

            if data:
                df = pd.DataFrame(data)
                df["date"] = pd.to_datetime(df["date"])
                logger.info(f"Retrieved cost data for {len(data)} daily records")
                return df
            else:
                logger.info("No cost data found for the specified period")
                return pd.DataFrame(columns=["date", "instance_type", "cost", "usage_hours"])

        except Exception as e:
            error_msg = str(e)
            if "UnrecognizedClientException" in error_msg or "security token" in error_msg.lower():
                logger.warning(f"AWS Cost Explorer API access denied. This may be due to:")
                logger.warning("1. Account not having Cost Explorer enabled")
                logger.warning("2. Insufficient billing permissions") 
                logger.warning("3. Using a sandbox/educational account")
                logger.warning("Cost data will be unavailable but system will continue functioning.")
            else:
                logger.error(f"Failed to get cost data: {e}")
            return pd.DataFrame()

    def calculate_savings(self, baseline_costs: pd.DataFrame, optimized_costs: pd.DataFrame) -> Dict:
        """Calculate cost savings from optimization."""

        total_baseline = baseline_costs["cost"].sum()
        total_optimized = optimized_costs["cost"].sum()

        savings = {
            "total_baseline_cost": total_baseline,
            "total_optimized_cost": total_optimized,
            "absolute_savings": total_baseline - total_optimized,
            "percentage_savings": ((total_baseline - total_optimized) / total_baseline) * 100,
            "daily_average_savings": (total_baseline - total_optimized) / len(baseline_costs["date"].unique()),
        }

        logger.info(f"Calculated savings: ${savings['absolute_savings']:.2f} ({savings['percentage_savings']:.1f}%)")
        return savings
