import os
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict

import boto3

try:
    from src.carbon.carbon_api_client import EC2EnergyCalculator, CarbonIntensityClient
    from src.config.settings import get_instance_pricing
except Exception:
    # Lambda layer path
    import sys
    sys.path.insert(0, "/opt/python")
    from src.carbon.carbon_api_client import EC2EnergyCalculator, CarbonIntensityClient
    from src.config.settings import get_instance_pricing


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def to_decimal(val: float) -> Decimal:
    try:
        return Decimal(str(round(float(val), 6)))
    except Exception:
        return Decimal("0")


def lambda_handler(_event: Dict[str, Any], _context: Any):
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"))
    project_name = os.environ.get("PROJECT_NAME", "carbon-aware-finops")
    hourly_table_name = os.environ.get("HOURLY_TABLE_NAME", f"{project_name}-hourly")

    ec2 = boto3.client("ec2", region_name=region)
    dynamodb = boto3.resource("dynamodb", region_name=region)
    hourly_table = dynamodb.Table(hourly_table_name)

    # Previous hour window and timestamp (top of previous hour)
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    ts = int(start.timestamp())

    # Prepare helpers
    energy_calc = EC2EnergyCalculator()
    carbon_client = CarbonIntensityClient(provider=os.getenv("CARBON_API_PROVIDER", "electricitymap"))

    # List managed instances
    resp = ec2.describe_instances(
        Filters=[{"Name": "tag:Project", "Values": [project_name]}]
    )

    total = 0
    for reservation in resp.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            instance_id = inst.get("InstanceId")
            instance_type = inst.get("InstanceType", "t3.medium")
            state = inst.get("State", {}).get("Name", "unknown")

            is_running = state == "running"

            # Cost (per hour)
            try:
                hourly_rate = float(get_instance_pricing(instance_type))
            except Exception:
                hourly_rate = 0.05
            cost = hourly_rate if is_running else 0.0

            # Energy and carbon
            try:
                power_watts = energy_calc.get_instance_power_consumption(instance_type, cpu_utilization=0.20)
            except Exception:
                power_watts = 100.0
            energy_kwh = (power_watts / 1000.0) * (1.0 if is_running else 0.0)

            try:
                intensity = float(carbon_client.get_current_intensity(region))
            except Exception:
                intensity = 400.0
            carbon_kg = (energy_kwh * intensity) / 1000.0  # gCO2 -> kg

            item = {
                "instance_id": instance_id,
                "timestamp": ts,
                "cost": to_decimal(cost),
                "energy_kwh": to_decimal(energy_kwh),
                "carbon_kg": to_decimal(carbon_kg),
                "state": state,
                "instance_type": instance_type,
            }

            try:
                hourly_table.put_item(Item=item)
                total += 1
            except Exception as e:
                logger.error(f"Failed to write hourly metrics for {instance_id}: {e}")

    logger.info(f"Hourly aggregation complete: {total} instance-hours recorded at {ts}")
    return {"statusCode": 200, "body": f"Recorded {total} items"}

