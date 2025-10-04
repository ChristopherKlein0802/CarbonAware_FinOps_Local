"""AWS runtime data gateway (CloudTrail, CloudWatch, EC2 discovery)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Iterable, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, SSOError, TokenRetrievalError, UnauthorizedSSOTokenError

from ...config import settings
from ...utils.errors import AWSAuthenticationError, ErrorMessages

logger = logging.getLogger(__name__)

AWSAuthErrors = (UnauthorizedSSOTokenError, SSOError, NoCredentialsError, TokenRetrievalError)


class AWSRuntimeGateway:
    """Encapsulates AWS SDK calls used for runtime analysis."""

    def __init__(self, profile: Optional[str] = None) -> None:
        self._profile = profile or settings.aws_profile

    def _session(self, region: Optional[str] = None) -> boto3.Session:
        return boto3.Session(profile_name=self._profile, region_name=region or settings.aws_region)

    # EC2 -----------------------------------------------------------------

    def list_instances(self, region: str) -> List[Dict]:
        try:
            session = self._session(region)
            ec2_client = session.client("ec2", region_name=region)
            response = ec2_client.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}]
            )
        except AWSAuthErrors as auth_error:
            logger.error("🚫 AWS authentication required for EC2 discovery: %s", auth_error)
            raise AWSAuthenticationError(ErrorMessages.AWS_SSO_EXPIRED) from auth_error
        except ClientError as client_error:
            logger.error("❌ AWS EC2 client error: %s", client_error)
            raise
        instances: List[Dict] = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_name = next(
                    (tag["Value"] for tag in instance.get("Tags", []) if tag.get("Key") == "Name"),
                    "Unnamed",
                )
                instances.append(
                    {
                        "instance_id": instance["InstanceId"],
                        "instance_type": instance["InstanceType"],
                        "state": instance["State"]["Name"],
                        "region": region,
                        "instance_name": instance_name,
                        "launch_time": instance.get("LaunchTime"),
                        "state_transition_reason": instance.get("StateTransitionReason", ""),
                    }
                )
        return instances

    # CloudTrail ----------------------------------------------------------

    def lookup_instance_events(
        self,
        *,
        instance_id: str,
        region: str,
        lookup_start: datetime,
        lookup_end: datetime,
    ) -> List[Dict]:
        session = self._session(region)
        cloudtrail = session.client("cloudtrail", region_name=region)
        paginator = cloudtrail.get_paginator("lookup_events")
        events: List[Dict] = []
        lookup_params = {
            "LookupAttributes": [{"AttributeKey": "ResourceName", "AttributeValue": instance_id}],
            "StartTime": lookup_start,
            "EndTime": lookup_end,
        }
        for page in paginator.paginate(**lookup_params):
            events.extend(page.get("Events", []))
        return events

    # CloudWatch ---------------------------------------------------------

    def fetch_cpu_metrics(
        self,
        *,
        instance_id: str,
        region: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        session = self._session(region)
        cloudwatch = session.client("cloudwatch", region_name=region)
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "cpu_utilization",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": "AWS/EC2",
                            "MetricName": "CPUUtilization",
                            "Dimensions": [
                                {"Name": "InstanceId", "Value": instance_id}
                            ]
                        },
                        "Period": 3600,
                        "Stat": "Average"
                    },
                    "ReturnData": True
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )
        return response.get("MetricDataResults", [])


__all__ = ["AWSRuntimeGateway"]
