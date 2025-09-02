import json
import os
import sys
import logging
import boto3
from datetime import datetime
from typing import Dict, Any

# Type annotations for boto3 resources (ignore missing stubs)

# Try importing directly first, then fall back to path manipulation if needed
try:
    from src.automation.shutdown_scheduler import ShutdownScheduler
except ImportError:
    # Lambda environment fallback
    sys.path.insert(0, "/opt/python")
    from src.automation.shutdown_scheduler import ShutdownScheduler

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

        # Initialize scheduler
        region = os.environ.get("AWS_REGION", "eu-central-1")
        scheduler = ShutdownScheduler(region=region)

        # Execute scheduling logic
        results = scheduler.execute_schedule()

        # Log results to CloudWatch
        logger.info(f"Execution results: {results}")

        # Store results in DynamoDB for tracking
        store_execution_results(results)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Scheduling executed successfully",
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error in Lambda execution: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()})}


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
