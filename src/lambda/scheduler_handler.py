import json
import os
import sys
import logging
import boto3
from datetime import datetime
from typing import Dict, Any

# Type annotations for boto3 resources (ignore missing stubs)

# Lightweight imports for Lambda
try:
    from src.carbon.carbon_api_client import CarbonIntensityClient
except ImportError:
    sys.path.insert(0, "/opt/python")
    from src.carbon.carbon_api_client import CarbonIntensityClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(_event, _context):
    """
    Main Lambda handler for carbon-aware scheduling.
    Triggered every 15 minutes by EventBridge.
    """
    try:
        # Log execution start
        logger.info(f"Starting execution at {datetime.now()}")

        # Initialize carbon client
        carbon_client = CarbonIntensityClient()
        
        # Get AWS region
        region = os.environ.get("AWS_REGION", "eu-central-1")
        
        # Get current carbon intensity
        current_intensity = carbon_client.get_current_intensity(region)
        threshold = int(os.environ.get("CARBON_THRESHOLD", "400"))
        
        logger.info(f"Current carbon intensity: {current_intensity} gCO2/kWh (threshold: {threshold})")
        
        # Get instances to manage
        ec2 = boto3.client("ec2")  # type: ignore[misc]
        project_name = os.environ.get("PROJECT_NAME", "carbon-aware-finops")
        
        # Find instances with carbon-aware schedules
        response = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Project", "Values": [project_name]},
                {"Name": "instance-state-name", "Values": ["running", "stopped"]},
            ]
        )
        
        managed_instances = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                managed_instances.append({
                    "instance_id": instance["InstanceId"],
                    "state": instance["State"]["Name"],
                    "tags": {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
                })
        
        logger.info(f"Found {len(managed_instances)} managed instances")
        
        # Execute carbon-aware decisions
        results = execute_carbon_aware_scheduling(ec2, managed_instances, current_intensity, threshold)
        
        # Store results in DynamoDB for tracking
        store_execution_results(results)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Scheduling executed successfully",
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                    "carbon_intensity": current_intensity,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error in Lambda execution: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()})}


def execute_carbon_aware_scheduling(ec2_client, instances: list, current_intensity: float, threshold: float) -> Dict[str, Any]:
    """Execute carbon-aware scheduling decisions."""
    results = {
        "shutdowns": 0,
        "startups": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    for instance in instances:
        instance_id = instance["instance_id"]
        current_state = instance["state"]
        tags = instance["tags"]
        
        try:
            # Check if instance has carbon-aware schedule
            schedule = tags.get("Schedule", "")
            if "Carbon-Aware" not in schedule:
                logger.debug(f"Instance {instance_id} not carbon-aware scheduled")
                results["skipped"] += 1
                continue
            
            # Make carbon-aware decision
            if current_intensity > threshold:
                # High carbon intensity - shut down if running
                if current_state == "running":
                    logger.info(f"Stopping instance {instance_id} (carbon intensity: {current_intensity})")
                    ec2_client.stop_instances(InstanceIds=[instance_id])
                    results["shutdowns"] += 1
                else:
                    logger.debug(f"Instance {instance_id} already stopped")
                    results["skipped"] += 1
            else:
                # Low carbon intensity - start if stopped
                if current_state == "stopped":
                    logger.info(f"Starting instance {instance_id} (carbon intensity: {current_intensity})")
                    ec2_client.start_instances(InstanceIds=[instance_id])
                    results["startups"] += 1
                else:
                    logger.debug(f"Instance {instance_id} already running")
                    results["skipped"] += 1
                    
        except Exception as e:
            logger.error(f"Error processing instance {instance_id}: {e}")
            results["errors"] += 1
    
    return results


def store_execution_results(results: Dict[str, Any]) -> None:
    """Store execution results in DynamoDB for tracking."""
    dynamodb = boto3.resource("dynamodb")  # type: ignore[misc]
    table = dynamodb.Table("carbon-aware-finops-state")  # type: ignore[misc]

    table.put_item(
        Item={
            "instance_id": "scheduler-execution",
            "timestamp": int(datetime.now().timestamp()),
            "shutdowns": results.get("shutdowns", 0),
            "startups": results.get("startups", 0),
            "execution_date": datetime.now().isoformat(),
        }
    )
