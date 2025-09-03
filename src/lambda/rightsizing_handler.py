import json
import boto3
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Type annotations for boto3 resources (ignore missing stubs)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class RightSizingAnalyzer:
    """Analyzes EC2 instances for rightsizing opportunities."""

    def __init__(self, region="eu-central-1", aws_profile=None):
        self.aws_profile = aws_profile or os.getenv("AWS_PROFILE", "carbon-finops-sandbox")

        # Create session with SSO profile
        session = boto3.Session(profile_name=self.aws_profile)

        self.cloudwatch = session.client("cloudwatch", region_name=region)
        self.ec2 = session.client("ec2", region_name=region)
        self.ce = session.client("ce", region_name=region)

        # Instance family sizing map
        self.size_map = {
            "t3.micro": {"vcpu": 2, "memory": 1.0, "baseline_cpu": 10},
            "t3.small": {"vcpu": 2, "memory": 2.0, "baseline_cpu": 20},
            "t3.medium": {"vcpu": 2, "memory": 4.0, "baseline_cpu": 20},
            "t3.large": {"vcpu": 2, "memory": 8.0, "baseline_cpu": 30},
            "t3.xlarge": {"vcpu": 4, "memory": 16.0, "baseline_cpu": 40},
            "t3.2xlarge": {"vcpu": 8, "memory": 32.0, "baseline_cpu": 40},
        }

    def analyze_instance(self, instance_id: str, days: int = 14) -> Optional[Dict[str, Any]]:
        """Analyze a single instance for rightsizing."""

        # Get instance details
        instance = self.get_instance_details(instance_id)
        if not instance:
            return None

        # Get CPU utilization metrics
        cpu_stats = self.get_cpu_statistics(instance_id, days)

        # Get memory utilization (if CloudWatch agent installed)
        memory_stats = self.get_memory_statistics(instance_id, days)

        # Calculate recommendations
        recommendation = self.calculate_recommendation(instance["InstanceType"], cpu_stats, memory_stats)

        # Estimate savings
        if recommendation["recommended_type"] != instance["InstanceType"]:
            savings = self.estimate_savings(instance["InstanceType"], recommendation["recommended_type"])
            recommendation["estimated_monthly_savings"] = savings

        return {
            "instance_id": instance_id,
            "current_type": instance["InstanceType"],
            "analysis": cpu_stats,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat(),
        }

    def get_cpu_statistics(self, instance_id: str, days: int) -> Dict[str, float]:
        """Get CPU utilization statistics."""

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=["Average", "Maximum"],
        )

        if not response["Datapoints"]:
            return {"avg": 0, "max": 0, "p95": 0}

        datapoints = response["Datapoints"]
        avg_cpu = sum(dp["Average"] for dp in datapoints) / len(datapoints)
        max_cpu = max(dp["Maximum"] for dp in datapoints)

        # Calculate 95th percentile
        sorted_values = sorted([dp["Average"] for dp in datapoints])
        p95_index = int(len(sorted_values) * 0.95)
        p95_cpu = sorted_values[p95_index] if sorted_values else 0

        return {
            "avg": round(avg_cpu, 2),
            "max": round(max_cpu, 2),
            "p95": round(p95_cpu, 2),
            "datapoints": len(datapoints),
        }

    def calculate_recommendation(
        self, current_type: str, cpu_stats: Dict[str, float], _memory_stats: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate rightsizing recommendation."""

        reason_list: List[str] = []
        recommendation = {"action": "no_change", "recommended_type": current_type, "reason": reason_list}

        # Downsize if consistently low utilization
        if cpu_stats["p95"] < 40 and cpu_stats["max"] < 60:
            smaller_types = self.get_smaller_instances(current_type)
            if smaller_types:
                recommendation["action"] = "downsize"
                recommendation["recommended_type"] = smaller_types[0]
                reason_list.append(f"CPU P95 at {cpu_stats['p95']}% (threshold: 40%)")

        # Upsize if consistently high utilization
        elif cpu_stats["avg"] > 80 or cpu_stats["p95"] > 90:
            larger_types = self.get_larger_instances(current_type)
            if larger_types:
                recommendation["action"] = "upsize"
                recommendation["recommended_type"] = larger_types[0]
                reason_list.append(f"CPU P95 at {cpu_stats['p95']}% (threshold: 90%)")

        return recommendation

    def get_smaller_instances(self, current_type: str) -> List[str]:
        """Get list of smaller instance types in the same family."""
        sizes = ["micro", "small", "medium", "large", "xlarge", "2xlarge"]
        family = current_type.split(".")[0]
        current_size = current_type.split(".")[1]

        current_index = sizes.index(current_size) if current_size in sizes else -1
        if current_index > 0:
            return [f"{family}.{sizes[current_index-1]}"]
        return []

    def get_larger_instances(self, current_type: str) -> List[str]:
        """Get list of larger instance types in the same family."""
        sizes = ["micro", "small", "medium", "large", "xlarge", "2xlarge"]
        family = current_type.split(".")[0]
        current_size = current_type.split(".")[1]

        current_index = sizes.index(current_size) if current_size in sizes else -1
        if current_index < len(sizes) - 1 and current_index != -1:
            return [f"{family}.{sizes[current_index+1]}"]
        return []

    def get_instance_details(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get EC2 instance details."""
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            if response["Reservations"]:
                instance_data = response["Reservations"][0]["Instances"][0]
                return dict(instance_data) if instance_data else None
        except Exception as e:
            logger.error(f"Error getting instance details: {e}")
        return None

    def get_memory_statistics(self, _instance_id: str, _days: int) -> Dict[str, float]:
        """Get memory utilization if available."""
        # Placeholder - requires CloudWatch agent
        return {"avg": 0, "max": 0}

    def estimate_savings(self, current_type: str, recommended_type: str) -> float:
        """Estimate monthly cost savings."""
        # Simplified pricing (should use AWS Pricing API)
        pricing = {
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "t3.xlarge": 0.1664,
            "t3.2xlarge": 0.3328,
        }

        current_hourly = pricing.get(current_type, 0)
        recommended_hourly = pricing.get(recommended_type, 0)

        monthly_hours = 730
        monthly_savings = (current_hourly - recommended_hourly) * monthly_hours

        return round(monthly_savings, 2)


def lambda_handler(_event, _context):
    """Lambda handler for rightsizing analysis."""

    analyzer = RightSizingAnalyzer()

    # Get all tagged instances - use the analyzer's ec2 client with SSO
    ec2 = analyzer.ec2
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": ["carbon-aware-finops"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    results = []
    recommendations_count = 0

    # Initialize DynamoDB for storing results
    session = boto3.Session(profile_name=analyzer.aws_profile)
    dynamodb = session.resource("dynamodb", region_name="eu-central-1")  # type: ignore[misc]

    try:
        table = dynamodb.Table("carbon-aware-finops-rightsizing")  # type: ignore[misc]
    except Exception as e:
        logger.error(f"DynamoDB table not found, creating in-memory results only: {e}")
        table = None

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            analysis = analyzer.analyze_instance(instance_id)
            if analysis:
                results.append(analysis)

                # Store in DynamoDB if table exists
                if table:
                    try:
                        table.put_item(
                            Item={
                                "instance_id": instance_id,
                                "timestamp": int(datetime.now().timestamp()),
                                "current_type": analysis["current_type"],
                                "recommendation": analysis["recommendation"],
                                "analysis_timestamp": analysis["timestamp"],
                            }
                        )
                        logger.info(f"Stored recommendation for {instance_id} in DynamoDB")
                    except Exception as e:
                        logger.error(f"Failed to store recommendation in DynamoDB: {e}")

                # Log recommendations
                if analysis["recommendation"]["action"] != "no_change":
                    recommendations_count += 1
                    logger.info(f"Rightsizing recommendation for {instance_id}: {analysis['recommendation']}")

    logger.info(
        f"Analysis complete: {len(results)} instances analyzed, {recommendations_count} recommendations generated"
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "analyzed_instances": len(results),
                "recommendations": [r for r in results if r["recommendation"]["action"] != "no_change"],
                "recommendations_count": recommendations_count,
                "timestamp": datetime.now().isoformat(),
            }
        ),
    }


def main():
    """Main function for running as script."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    result = lambda_handler(None, None)
    print("Rightsizing Analysis Complete!")
    body = json.loads(result["body"])
    print(f"Analyzed {body['analyzed_instances']} instances")
    print(f"Generated {body['recommendations_count']} recommendations")

    if body["recommendations"]:
        print("\nRecommendations:")
        for i, rec in enumerate(body["recommendations"], 1):
            action = rec["recommendation"]["action"]
            current = rec["current_type"]
            recommended = rec["recommendation"]["recommended_type"]
            savings = rec["recommendation"].get("estimated_monthly_savings", "N/A")
            print(f"{i}. Instance {rec['instance_id']}: {action} from {current} to {recommended} (${savings}/month)")


if __name__ == "__main__":
    main()
