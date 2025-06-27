"""
Metrics collector for gathering cost and carbon data.
"""

import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import logging

from ..carbon.carbon_api_client import CarbonIntensityClient
from ..cost.aws_cost_client import AWSCostClient

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and processes metrics for reporting."""
    
    def __init__(self, region: str = 'eu-central-1'):
        self.region = region
        self.carbon_client = CarbonIntensityClient()
        self.cost_client = AWSCostClient(region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    def collect_instance_metrics(self, 
                               instance_id: str, 
                               start_time: datetime, 
                               end_time: datetime) -> pd.DataFrame:
        """Collect CloudWatch metrics for an instance."""
        
        metrics = []
        
        # CPU Utilization
        cpu_data = self._get_cloudwatch_metric(
            instance_id, 'CPUUtilization', start_time, end_time
        )
        
        # Network In/Out
        network_in = self._get_cloudwatch_metric(
            instance_id, 'NetworkIn', start_time, end_time
        )
        network_out = self._get_cloudwatch_metric(
            instance_id, 'NetworkOut', start_time, end_time
        )
        
        # Combine metrics
        for i, timestamp in enumerate(cpu_data['timestamps']):
            metrics.append({
                'timestamp': timestamp,
                'instance_id': instance_id,
                'cpu_utilization': cpu_data['values'][i],
                'network_in': network_in['values'][i] if i < len(network_in['values']) else 0,
                'network_out': network_out['values'][i] if i < len(network_out['values']) else 0
            })
        
        return pd.DataFrame(metrics)
    
    def _get_cloudwatch_metric(self, 
                             instance_id: str, 
                             metric_name: str, 
                             start_time: datetime, 
                             end_time: datetime) -> Dict:
        """Get specific CloudWatch metric."""
        
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            # Sort by timestamp
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            
            return {
                'timestamps': [dp['Timestamp'] for dp in datapoints],
                'values': [dp['Average'] for dp in datapoints]
            }
            
        except Exception as e:
            logger.error(f"Error getting CloudWatch metric {metric_name}: {e}")
            return {'timestamps': [], 'values': []}
    
    def calculate_carbon_emissions(self, 
                                 usage_hours: float, 
                                 instance_type: str, 
                                 carbon_intensity: float) -> float:
        """Calculate carbon emissions for instance usage."""
        
        # Instance power consumption (kW) - simplified estimates NOCH ANPASSEN
        # These values are rough estimates and should be adjusted based on actual data
        power_consumption = {
            't3.micro': 0.01,
            't3.small': 0.02,
            't3.medium': 0.04,
            't3.large': 0.08,
            't3.xlarge': 0.16
        }
        
        instance_power = power_consumption.get(instance_type, 0.05)
        
        # Calculate emissions: Power (kW) × Time (h) × Carbon Intensity (gCO2/kWh)
        emissions_g = instance_power * usage_hours * carbon_intensity
        
        # Convert to kg
        return emissions_g / 1000