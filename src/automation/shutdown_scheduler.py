#!/usr/bin/env python3
"""
Carbon-aware shutdown scheduler for EC2 instances.
Implements off-hours automation with carbon intensity consideration.
"""

import boto3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
import yaml
from dataclasses import dataclass
import os

from ..carbon.carbon_api_client import CarbonIntensityClient
from ..cost.aws_cost_client import AWSCostClient

logger = logging.getLogger(__name__)

@dataclass
class ScheduleRule:
    """Represents a scheduling rule for instances."""
    name: str
    shutdown_time: Optional[str]
    startup_time: Optional[str]
    days: List[str]
    carbon_threshold: Optional[float] = None
    timezone: str = "Europe/Berlin"
    
class ShutdownScheduler:
    """Manages carbon-aware shutdown scheduling for EC2 instances."""
    
    def __init__(self, region: str = 'eu-central-1'):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.carbon_client = CarbonIntensityClient()
        self.cost_client = AWSCostClient(region)
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
    def get_tagged_instances(self, tag_key: str = 'Schedule') -> List[Dict]:
        """Get all instances with scheduling tags."""
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'tag-key', 'Values': [tag_key]},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'State': instance['State']['Name'],
                        'InstanceType': instance['InstanceType'],
                        'LaunchTime': instance.get('LaunchTime'),
                        'Tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            logger.info(f"Found {len(instances)} instances with scheduling tags")
            return instances
            
        except Exception as e:
            logger.error(f"Error fetching instances: {e}")
            return []
    
    def should_shutdown(self, instance: Dict, current_time: datetime) -> bool:
        """Determine if instance should be shut down based on schedule and carbon intensity."""
        schedule_tag = instance['Tags'].get('Schedule', 'always-on')
        
        # Special case: always-on instances
        if schedule_tag.lower() == 'always-on' or schedule_tag == '24/7 Always Running':
            return False
            
        # Load schedule rules
        schedule_rule = self._load_schedule_rule(schedule_tag)
        if not schedule_rule:
            logger.warning(f"No schedule rule found for tag: {schedule_tag}")
            return False
            
        # Check if shutdown time is defined
        if not schedule_rule.shutdown_time:
            # No specific shutdown time, check carbon threshold only
            if schedule_rule.carbon_threshold:
                current_carbon = self.carbon_client.get_current_intensity(self.region)
                if current_carbon > schedule_rule.carbon_threshold:
                    logger.info(f"Carbon intensity {current_carbon} above threshold {schedule_rule.carbon_threshold}")
                    return True
            return False
            
        # Check time-based rules
        if not self._is_within_shutdown_window(schedule_rule, current_time):
            return False
            
        # Additional carbon intensity check if threshold is set
        if schedule_rule.carbon_threshold:
            current_carbon = self.carbon_client.get_current_intensity(self.region)
            if current_carbon < schedule_rule.carbon_threshold:
                logger.info(f"Carbon intensity {current_carbon} below threshold {schedule_rule.carbon_threshold} - keeping instance running")
                return False
                
        return True
    
    def should_startup(self, instance: Dict, current_time: datetime) -> bool:
        """Determine if instance should be started up."""
        schedule_tag = instance['Tags'].get('Schedule', 'always-on')
        
        if schedule_tag.lower() == 'always-on' or schedule_tag == '24/7 Always Running':
            return False
            
        schedule_rule = self._load_schedule_rule(schedule_tag)
        if not schedule_rule:
            return False
            
        # Check if we're in startup window
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_day = current_time.strftime('%A').lower()
        
        # Check if today is a scheduled day
        if schedule_rule.days and current_day not in schedule_rule.days:
            return False
            
        if schedule_rule.startup_time:
            startup_hour, startup_minute = self._parse_time(schedule_rule.startup_time)
            
            # Start up 5 minutes before startup time
            if current_hour == startup_hour:
                if abs(current_minute - startup_minute) <= 5:
                    # Check carbon threshold if set
                    if schedule_rule.carbon_threshold:
                        current_carbon = self.carbon_client.get_current_intensity(self.region)
                        if current_carbon > schedule_rule.carbon_threshold:
                            logger.info(f"Carbon intensity {current_carbon} above threshold - delaying startup")
                            return False
                    return True
                
        return False
    
    def shutdown_instance(self, instance_id: str) -> bool:
        """Shutdown a specific instance."""
        try:
            # Record metrics before shutdown
            self._record_shutdown_metrics(instance_id)
            
            response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Successfully initiated shutdown for instance {instance_id}")
            
            # Log to DynamoDB
            self._log_action(instance_id, 'shutdown')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to shutdown instance {instance_id}: {e}")
            return False
    
    def startup_instance(self, instance_id: str) -> bool:
        """Start up a specific instance."""
        try:
            response = self.ec2_client.start_instances(InstanceIds=[instance_id])
            logger.info(f"Successfully started instance {instance_id}")
            
            # Record startup metrics
            self._record_startup_metrics(instance_id)
            
            # Log to DynamoDB
            self._log_action(instance_id, 'startup')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start instance {instance_id}: {e}")
            return False
    
    def execute_schedule(self) -> Dict:
        """Main execution method for scheduling logic."""
        current_time = datetime.now(timezone.utc)
        instances = self.get_tagged_instances()
        
        shutdown_count = 0
        startup_count = 0
        skipped_count = 0
        
        logger.info(f"Executing schedule at {current_time}")
        
        for instance in instances:
            instance_id = instance['InstanceId']
            current_state = instance['State']
            
            logger.debug(f"Processing instance {instance_id} (state: {current_state})")
            
            if current_state == 'running' and self.should_shutdown(instance, current_time):
                if self.shutdown_instance(instance_id):
                    shutdown_count += 1
                    
            elif current_state == 'stopped' and self.should_startup(instance, current_time):
                if self.startup_instance(instance_id):
                    startup_count += 1
            else:
                skipped_count += 1
        
        results = {
            'shutdowns': shutdown_count,
            'startups': startup_count,
            'skipped': skipped_count,
            'total_instances': len(instances),
            'execution_time': current_time.isoformat()
        }
        
        logger.info(f"Schedule execution complete: {results}")
        return results
    
    def _load_schedule_rule(self, schedule_name: str) -> Optional[ScheduleRule]:
        """Load schedule rule from configuration."""
        try:
            # Try to load from file
            config_file = os.path.join(os.path.dirname(__file__), '../../config/scheduling_rules.yaml')
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    rules = yaml.safe_load(f)
            else:
                # Use default rules if config file doesn't exist
                rules = self._get_default_rules()
            
            # Find matching rule
            for rule_key, rule_data in rules.items():
                if rule_data.get('name') == schedule_name:
                    return ScheduleRule(**rule_data)
                    
            # Check if schedule_name matches a rule key
            if schedule_name.replace(' ', '-').lower() in rules:
                rule_data = rules[schedule_name.replace(' ', '-').lower()]
                return ScheduleRule(**rule_data)
                
        except Exception as e:
            logger.error(f"Failed to load schedule rule {schedule_name}: {e}")
            
        return None
    
    def _get_default_rules(self) -> Dict:
        """Get default scheduling rules."""
        return {
            'always-on': {
                'name': '24/7 Always Running',
                'shutdown_time': None,
                'startup_time': None,
                'days': [],
                'carbon_threshold': None,
                'timezone': 'Europe/Berlin'
            },
            'office-hours-weekdays': {
                'name': 'Office Hours + Weekend Shutdown',
                'shutdown_time': '18:00',
                'startup_time': '08:00',
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                'carbon_threshold': None,
                'timezone': 'Europe/Berlin'
            },
            'development-extended': {
                'name': 'Extended Development Hours',
                'shutdown_time': '20:00',
                'startup_time': '07:00',
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                'carbon_threshold': 500,
                'timezone': 'Europe/Berlin'
            },
            'carbon-optimized': {
                'name': 'Carbon-Aware 24/7',
                'shutdown_time': None,
                'startup_time': None,
                'days': [],
                'carbon_threshold': 300,
                'timezone': 'Europe/Berlin'
            }
        }
    
    def _is_within_shutdown_window(self, schedule_rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current time is within shutdown window."""
        current_hour = current_time.hour
        current_day = current_time.strftime('%A').lower()
        
        # Check if today is a scheduled day
        if schedule_rule.days and current_day not in schedule_rule.days:
            logger.debug(f"Current day {current_day} not in scheduled days {schedule_rule.days}")
            return True  # Should be shut down on non-scheduled days
            
        # Parse shutdown and startup times
        if schedule_rule.shutdown_time and schedule_rule.startup_time:
            shutdown_hour, shutdown_minute = self._parse_time(schedule_rule.shutdown_time)
            startup_hour, startup_minute = self._parse_time(schedule_rule.startup_time)
            
            # Check if we're outside operating hours
            if shutdown_hour < startup_hour:
                # Shutdown and startup on same day
                if current_hour >= shutdown_hour or current_hour < startup_hour:
                    return True
            else:
                # Shutdown spans midnight
                if current_hour >= shutdown_hour and current_hour < startup_hour:
                    return True
                    
        return False
    
    def _parse_time(self, time_str: str) -> tuple:
        """Parse time string to hour and minute."""
        if ':' in time_str:
            parts = time_str.split(':')
            return int(parts[0]), int(parts[1])
        else:
            return int(time_str), 0
    
    def _record_shutdown_metrics(self, instance_id: str):
        """Record metrics when shutting down an instance."""
        try:
            # Would record to CloudWatch metrics
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            cloudwatch.put_metric_data(
                Namespace='CarbonAwareFinOps',
                MetricData=[
                    {
                        'MetricName': 'InstanceShutdown',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': instance_id}
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to record shutdown metrics: {e}")
    
    def _record_startup_metrics(self, instance_id: str):
        """Record metrics when starting up an instance."""
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            cloudwatch.put_metric_data(
                Namespace='CarbonAwareFinOps',
                MetricData=[
                    {
                        'MetricName': 'InstanceStartup',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': instance_id}
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to record startup metrics: {e}")
    
    def _log_action(self, instance_id: str, action: str):
        """Log action to DynamoDB."""
        try:
            table = self.dynamodb.Table('carbon-aware-finops-state')
            table.put_item(
                Item={
                    'instance_id': instance_id,
                    'timestamp': int(datetime.now().timestamp()),
                    'action': action,
                    'carbon_intensity': self.carbon_client.get_current_intensity(self.region),
                    'region': self.region
                }
            )
        except Exception as e:
            logger.error(f"Failed to log action to DynamoDB: {e}")

def main():
    """Main entry point for scheduler."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scheduler = ShutdownScheduler()
    results = scheduler.execute_schedule()
    print(f"Execution complete: {results}")

if __name__ == "__main__":
    main()