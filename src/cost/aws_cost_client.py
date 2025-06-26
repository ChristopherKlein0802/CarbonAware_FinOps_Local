"""
AWS Cost Explorer client for cost analysis.
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class AWSCostClient:
    """Client for AWS Cost Explorer API."""
    
    def __init__(self, region: str = 'us-east-1'):
        self.ce_client = boto3.client('ce', region_name=region)
        self.region = region
    
    def get_instance_costs(self, 
                          instance_ids: List[str], 
                          start_date: datetime, 
                          end_date: datetime) -> pd.DataFrame:
        """Get cost data for specific instances."""
        
        # Format dates for Cost Explorer
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start,
                    'End': end
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'},
                    {'Type': 'TAG', 'Key': 'InstanceId'}
                ],
                Filter={
                    'And': [
                        {
                            'Dimensions': {
                                'Key': 'SERVICE',
                                'Values': ['Amazon Elastic Compute Cloud - Compute']
                            }
                        },
                        {
                            'Tags': {
                                'Key': 'InstanceId',
                                'Values': instance_ids
                            }
                        }
                    ]
                }
            )
            
            # Convert to DataFrame
            data = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                for group in result['Groups']:
                    instance_type = group['Keys'][0]
                    instance_id = group['Keys'][1].split('$')[1] if '$' in group['Keys'][1] else 'Unknown'
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    data.append({
                        'date': date,
                        'instance_id': instance_id,
                        'instance_type': instance_type,
                        'cost': cost,
                        'usage_hours': usage
                    })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            logger.info(f"Retrieved cost data for {len(instance_ids)} instances")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get cost data: {e}")
            return pd.DataFrame()
    
    def calculate_savings(self, 
                         baseline_costs: pd.DataFrame, 
                         optimized_costs: pd.DataFrame) -> Dict:
        """Calculate cost savings from optimization."""
        
        total_baseline = baseline_costs['cost'].sum()
        total_optimized = optimized_costs['cost'].sum()
        
        savings = {
            'total_baseline_cost': total_baseline,
            'total_optimized_cost': total_optimized,
            'absolute_savings': total_baseline - total_optimized,
            'percentage_savings': ((total_baseline - total_optimized) / total_baseline) * 100,
            'daily_average_savings': (total_baseline - total_optimized) / len(baseline_costs['date'].unique())
        }
        
        logger.info(f"Calculated savings: ${savings['absolute_savings']:.2f} ({savings['percentage_savings']:.1f}%)")
        return savings