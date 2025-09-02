#!/usr/bin/env python3
"""
Collect baseline data for cost and carbon analysis.
"""

import click
import boto3
from datetime import datetime, timedelta
import pandas as pd
import json
from loguru import logger
import sys

# Add project root to path
sys.path.append('.')

from src.carbon.carbon_api_client import CarbonIntensityClient
from src.cost.aws_cost_client import AWSCostClient

@click.command()
@click.option('--days', default=7, help='Number of days to collect baseline data')
@click.option('--region', default='eu-central-1', help='AWS region')
@click.option('--output', default='data/baseline/baseline_data.csv', help='Output file path')
@click.option('--profile', default='carbon-finops-sandbox', help='AWS SSO profile name')
def collect_baseline(days: int, region: str, output: str, profile: str):
    """Collect baseline data for specified number of days."""
    
    logger.info(f"Starting baseline data collection for {days} days in {region}")
    logger.info(f"Using AWS profile: {profile}")
    
    try:
        # Initialize clients with SSO profile
        session = boto3.Session(profile_name=profile)
        ec2 = session.client('ec2', region_name=region)
        carbon_client = CarbonIntensityClient()
        cost_client = AWSCostClient(region)
        
        logger.info("AWS clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients with profile '{profile}': {e}")
        logger.info(f"Please run: aws sso login --profile {profile}")
        return
    
    # Get all instances
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']},
            {'Name': 'tag:Project', 'Values': ['carbon-aware-finops']}
        ]
    )
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append({
                'instance_id': instance['InstanceId'],
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'launch_time': instance.get('LaunchTime'),
                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
            })
    
    logger.info(f"Found {len(instances)} instances to monitor")
    
    # Collect data for each day
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get cost data
    instance_ids = [i['instance_id'] for i in instances]
    cost_data = cost_client.get_instance_costs(instance_ids, start_date, end_date)
    
    # Collect carbon intensity data
    carbon_data = []
    current_date = start_date
    
    while current_date <= end_date:
        try:
            intensity = carbon_client.get_current_intensity(region)
            carbon_data.append({
                'timestamp': current_date,
                'region': region,
                'carbon_intensity': intensity
            })
        except Exception as e:
            logger.error(f"Failed to get carbon data for {current_date}: {e}")
        
        current_date += timedelta(hours=1)
    
    # Combine data
    carbon_df = pd.DataFrame(carbon_data)
    
    # Save baseline data
    baseline_data = {
        'metadata': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'region': region,
            'instance_count': len(instances),
            'total_days': days
        },
        'instances': instances,
        'cost_summary': {
            'total_cost': cost_data['cost'].sum() if not cost_data.empty else 0,
            'average_daily_cost': cost_data.groupby('date')['cost'].sum().mean() if not cost_data.empty else 0
        },
        'carbon_summary': {
            'average_intensity': carbon_df['carbon_intensity'].mean() if not carbon_df.empty else 0,
            'min_intensity': carbon_df['carbon_intensity'].min() if not carbon_df.empty else 0,
            'max_intensity': carbon_df['carbon_intensity'].max() if not carbon_df.empty else 0
        }
    }
    
    # Save detailed data
    if not cost_data.empty:
        cost_data.to_csv(output.replace('.csv', '_costs.csv'), index=False)
    
    carbon_df.to_csv(output.replace('.csv', '_carbon.csv'), index=False)
    
    # Save summary
    with open(output.replace('.csv', '_summary.json'), 'w') as f:
        json.dump(baseline_data, f, indent=2, default=str)
    
    logger.success(f"Baseline data collection complete. Files saved to {output}")
    
    # Print summary
    click.echo("\n📊 Baseline Summary:")
    click.echo(f"  • Instances monitored: {len(instances)}")
    click.echo(f"  • Total baseline cost: ${baseline_data['cost_summary']['total_cost']:.2f}")
    click.echo(f"  • Average daily cost: ${baseline_data['cost_summary']['average_daily_cost']:.2f}")
    click.echo(f"  • Average carbon intensity: {baseline_data['carbon_summary']['average_intensity']:.1f} gCO2/kWh")

if __name__ == '__main__':
    collect_baseline()