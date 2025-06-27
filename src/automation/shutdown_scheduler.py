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

from ..carbon.carbon_api_client import CarbonIntensityClient
from ..cost.aws_cost_client import AWSCostClient

logger = logging.getLogger(__name__)

@dataclass
class ScheduleRule:
    """Represents a scheduling rule for instances."""
    name: str
    shutdown_time: str
    startup_time: str
    days: List[str]
    carbon_threshold: Optional[float] = None
    
class ShutdownScheduler:
    """Manages carbon-aware shutdown scheduling for EC2 instances."""
    
    def __init__(self, region: str = 'us-east-1'):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.carbon_client = CarbonIntensityClient()
        self.cost_client = AWSCostClient(region)
        self.region = region
        
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
        
        if schedule_tag == 'always-on':
            return False
            
        # Load schedule rules
        schedule_rule = self._load_schedule_rule(schedule_tag)
        if not schedule_rule:
            return False
            
        # Check time-based rules
        if not self._is_within_shutdown_window(schedule_rule, current_time):
            return False
            
        # Check carbon intensity if threshold is set
        if schedule_rule.carbon_threshold:
            current_carbon = self.carbon_client.get_current_intensity(self.region)
            if current_carbon < schedule_rule.carbon_threshold:
                logger.info(f"Carbon intensity {current_carbon} below threshold {schedule_rule.carbon_threshold}")
                return False
                
        return True
    
    def shutdown_instance(self, instance_id: str) -> bool:
        """Shutdown a specific instance."""
        try:
            # Record metrics before shutdown
            self._record_shutdown_metrics(instance_id)
            
            response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Successfully initiated shutdown for instance {instance_id}")
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
            return True
            
        except Exception as e:
            logger.error(f"Failed to start instance {instance_id}: {e}")
            return False
    
    def execute_schedule(self):
        """Main execution method for scheduling logic."""
        current_time = datetime.now(timezone.utc)
        instances = self.get_tagged_instances()
        
        shutdown_count = 0
        startup_count = 0
        
        for instance in instances:
            instance_id = instance['InstanceId']
            current_state = instance['State']
            
            if current_state == 'running' and self.should_shutdown(instance, current_time):
                if self.shutdown_instance(instance_id):
                    shutdown_count += 1
                    
            elif current_state == 'stopped' and self.should_startup(instance, current_time):
                if self.startup_instance(instance_id):
                    startup_count += 1
        
        logger.info(f"Schedule execution complete: {shutdown_count} shutdowns, {startup_count} startups")
        return {'shutdowns': shutdown_count, 'startups': startup_count}
    
    def _load_schedule_rule(self, schedule_name: str) -> Optional[ScheduleRule]:
        """Load schedule rule from configuration."""
        try:
            with open('config/scheduling_rules.yaml', 'r') as f:
                rules = yaml.safe_load(f)
                rule_data = rules.get(schedule_name)
                if rule_data:
                    return ScheduleRule(**rule_data)
        except Exception as e:
            logger.error(f"Failed to load schedule rule {schedule_name}: {e}")
        return None
    
    def _is_within_shutdown_window(self, rule: ScheduleRule, current_time: datetime) -> bool:
        """Check if current time is within shutdown window."""
        # Implementation for time window checking
        current_hour = current_time.hour
        current_day = current_time.strftime('%A').lower()
        
        if current_day not in rule.days:
            return False
            
        shutdown_hour = int(rule.shutdown_time.split(':')[0])
        startup_hour = int(rule.startup_time.split(':')[0])
        
        if shutdown_hour <= current_hour or current_hour < startup_hour:
            return True
            
        return False
    
    def should_startup(self, instance: Dict, current_time: datetime) -> bool:
        """Determine if instance should be started up."""
        schedule_tag = instance['Tags'].get('Schedule', 'always-on')
        
        if schedule_tag == 'always-on':
            return False
            
        schedule_rule = self._load_schedule_rule(schedule_tag)
        if not schedule_rule:
            return False
            
        # Check if we're in startup window
        current_hour = current_time.hour
        current_day = current_time.strftime('%A').lower()
        
        if current_day not in rule.days:
            return False
            
        startup_hour = int(schedule_rule.startup_time.split(':')[0])
        
        # Start up 15 minutes before startup time
        if current_hour == startup_hour - 1 and current_time.minute >= 45:
            return True
        elif current_hour == startup_hour and current_time.minute < 15:
            return True
            
        return False
    
    def _record_shutdown_metrics(self, instance_id: str):
        """Record metrics when shutting down an instance."""
        # Implementation for metrics recording
        pass
    
    def _record_startup_metrics(self, instance_id: str):
        """Record metrics when starting up an instance."""
        # Implementation for metrics recording
        pass

def main():
    """Main entry point for scheduler."""
    logging.basicConfig(level=logging.INFO)
    scheduler = ShutdownScheduler()
    results = scheduler.execute_schedule()
    print(f"Execution complete: {results}")

if __name__ == "__main__":
    main()