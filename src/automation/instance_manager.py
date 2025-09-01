"""
Instance manager for starting and stopping EC2 instances.
"""

import boto3
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class InstanceManager:
    """Manages EC2 instance lifecycle operations."""

    def __init__(self, region: str = 'eu-central-1'):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.region = region

    def get_instances_by_tag(self, tag_key: str, tag_value: str) -> List[Dict]:
        """Get instances filtered by tag."""
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )

            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'instance_id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'type': instance['InstanceType'],
                        'launch_time': instance.get('LaunchTime'),
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })

            return instances
        except Exception as e:
            logger.error(f"Error getting instances: {e}")
            return []

    def stop_instances(self, instance_ids: List[str]) -> Dict[str, bool]:
        """Stop multiple instances."""
        results = {}

        for instance_id in instance_ids:
            try:
                self.ec2_client.stop_instances(InstanceIds=[instance_id])
                results[instance_id] = True
                logger.info(f"Successfully stopped instance {instance_id}")
            except Exception as e:
                results[instance_id] = False
                logger.error(f"Failed to stop instance {instance_id}: {e}")

        return results

    def start_instances(self, instance_ids: List[str]) -> Dict[str, bool]:
        """Start multiple instances."""
        results = {}

        for instance_id in instance_ids:
            try:
                self.ec2_client.start_instances(InstanceIds=[instance_id])
                results[instance_id] = True
                logger.info(f"Successfully started instance {instance_id}")
            except Exception as e:
                results[instance_id] = False
                logger.error(f"Failed to start instance {instance_id}: {e}")

        return results

    def get_instance_state(self, instance_id: str) -> Optional[str]:
        """Get current state of an instance."""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            if response['Reservations']:
                instance = response['Reservations'][0]['Instances'][0]
                return instance['State']['Name']
        except Exception as e:
            logger.error(f"Error getting instance state: {e}")
        return None
