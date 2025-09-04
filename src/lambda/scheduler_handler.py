"""
Carbon-Aware Scheduler Lambda Function for Bachelor Thesis

This function demonstrates the cost and carbon savings potential of intelligent EC2 scheduling.
It combines real AWS Cost Explorer data with carbon intensity data from ElectricityMap/WattTime
to provide actionable insights for FinOps optimization.

Core thesis contribution: Quantifying both financial and environmental impact of cloud scheduling.
"""

import json
import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from decimal import Decimal
import logging

# Lightweight imports for Lambda
try:
    from src.carbon.carbon_api_client import CarbonIntensityClient
except ImportError:
    import sys
    sys.path.insert(0, "/opt/python")
    from src.carbon.carbon_api_client import CarbonIntensityClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
ec2 = boto3.client('ec2')
ce = boto3.client('ce')  # Cost Explorer
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


def lambda_handler(event, context):
    """
    Main Lambda handler for carbon-aware scheduling analysis.
    
    This function:
    1. Analyzes current EC2 instances and their costs
    2. Gets real-time carbon intensity data
    3. Applies scheduling logic based on carbon thresholds
    4. Calculates potential savings (cost + carbon)
    5. Stores results for dashboard visualization
    """
    try:
        logger.info("Starting Carbon-Aware Scheduler analysis")
        
        # Get environment variables
        project_name = os.environ.get('PROJECT_NAME', 'carbon-aware-finops')
        results_table_name = os.environ.get('DYNAMODB_RESULTS_TABLE')
        carbon_threshold = float(os.environ.get('CARBON_THRESHOLD', '400'))
        aws_region = os.environ.get('AWS_REGION', 'eu-central-1')
        
        if not results_table_name:
            raise ValueError("DYNAMODB_RESULTS_TABLE environment variable not set")
        
        results_table = dynamodb.Table(results_table_name)
        
        # 1. Get current test instances
        instances = get_test_instances(project_name)
        logger.info(f"Found {len(instances)} test instances")
        
        # 2. Get real cost data from Cost Explorer
        cost_data = get_ec2_costs(instances)
        logger.info(f"Retrieved cost data for {len(cost_data)} instances")
        
        # 3. Get current carbon intensity
        carbon_intensity = get_carbon_intensity(aws_region)
        logger.info(f"Current carbon intensity: {carbon_intensity} gCO2/kWh")
        
        # 4. Analyze each instance and calculate savings
        analysis_results = []
        total_cost_savings = 0
        total_carbon_savings = 0
        
        for instance in instances:
            instance_id = instance['InstanceId']
            schedule_type = get_instance_schedule(instance)
            
            # Calculate current costs and carbon
            current_cost = cost_data.get(instance_id, {}).get('daily_cost', 0)
            current_carbon = calculate_carbon_emissions(instance, carbon_intensity)
            
            # Calculate optimized costs and carbon based on schedule
            optimized_cost, optimized_carbon = calculate_optimized_values(
                current_cost, current_carbon, schedule_type, carbon_intensity, carbon_threshold
            )
            
            # Calculate savings
            cost_savings = current_cost - optimized_cost
            carbon_savings = current_carbon - optimized_carbon
            
            total_cost_savings += cost_savings
            total_carbon_savings += carbon_savings
            
            # Store individual instance analysis
            result = {
                'instance_id': instance_id,
                'timestamp': int(datetime.utcnow().timestamp()),
                'schedule_type': schedule_type,
                'current_cost_usd': float(current_cost),
                'optimized_cost_usd': float(optimized_cost),
                'cost_savings_usd': float(cost_savings),
                'current_carbon_kg': float(current_carbon),
                'optimized_carbon_kg': float(optimized_carbon),
                'carbon_savings_kg': float(carbon_savings),
                'carbon_intensity': carbon_intensity,
                'instance_type': instance.get('InstanceType'),
                'state': instance['State']['Name']
            }
            
            analysis_results.append(result)
            
            # Store in DynamoDB
            store_analysis_result(results_table, result)
            
            # Apply scheduling decision if needed
            apply_scheduling_decision(instance, schedule_type, carbon_intensity, carbon_threshold)
        
        # 5. Store aggregated results
        aggregated_result = {
            'instance_id': 'AGGREGATED_TOTALS',
            'timestamp': int(datetime.utcnow().timestamp()),
            'schedule_type': 'ALL',
            'total_instances': len(instances),
            'total_cost_savings_usd': float(total_cost_savings),
            'total_carbon_savings_kg': float(total_carbon_savings),
            'carbon_intensity': carbon_intensity,
            'analysis_date': datetime.utcnow().isoformat()
        }
        
        store_analysis_result(results_table, aggregated_result)
        
        # 6. Send CloudWatch metrics for monitoring
        send_cloudwatch_metrics(total_cost_savings, total_carbon_savings, len(instances))
        
        logger.info(f"Analysis complete. Cost savings: ${total_cost_savings:.2f}, Carbon savings: {total_carbon_savings:.2f} kg")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Carbon-aware analysis completed successfully',
                'instances_analyzed': len(instances),
                'total_cost_savings_usd': float(total_cost_savings),
                'total_carbon_savings_kg': float(total_carbon_savings),
                'carbon_intensity': carbon_intensity
            })
        }
        
    except Exception as e:
        logger.error(f"Error in carbon-aware scheduler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def get_test_instances(project_name: str) -> List[Dict]:
    """Get all test instances for the project."""
    try:
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': [project_name]},
                {'Name': 'tag:InstanceRole', 'Values': ['TestInstance']},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
            ]
        )
        
        instances = []
        for reservation in response['Reservations']:
            instances.extend(reservation['Instances'])
        
        return instances
    except Exception as e:
        logger.error(f"Error getting test instances: {str(e)}")
        return []


def get_ec2_costs(instances: List[Dict]) -> Dict[str, Dict]:
    """Get real cost data from Cost Explorer for EC2 instances."""
    try:
        # Get costs for the last 24 hours
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=1)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
            ],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Elastic Compute Cloud - Compute']
                }
            }
        )
        
        cost_data = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                # Estimate per-instance cost (simplified for thesis demonstration)
                avg_cost_per_instance = cost / max(len(instances), 1)
                
                for instance in instances:
                    instance_id = instance['InstanceId']
                    if instance_id not in cost_data:
                        cost_data[instance_id] = {'daily_cost': avg_cost_per_instance}
        
        return cost_data
    except Exception as e:
        logger.error(f"Error getting cost data: {str(e)}")
        # Return estimated costs if Cost Explorer fails
        estimated_costs = {}
        for instance in instances:
            instance_type = instance.get('InstanceType', 't3.micro')
            estimated_daily_cost = get_estimated_instance_cost(instance_type)
            estimated_costs[instance['InstanceId']] = {'daily_cost': estimated_daily_cost}
        return estimated_costs


def get_estimated_instance_cost(instance_type: str) -> float:
    """Get estimated daily cost for instance types (fallback if Cost Explorer fails)."""
    # Simplified cost estimates for thesis demonstration (USD per day)
    cost_estimates = {
        't3.micro': 0.50,
        't3.small': 1.00,
        't3.medium': 2.00,
        't3.large': 4.00,
        't3.xlarge': 8.00
    }
    return cost_estimates.get(instance_type, 1.00)


def get_carbon_intensity(aws_region: str) -> float:
    """Get current carbon intensity for the AWS region."""
    try:
        # Import carbon client (reusing existing code)
        carbon_client = CarbonIntensityClient()
        intensity = carbon_client.get_current_intensity(aws_region)
        return intensity
    except Exception as e:
        logger.error(f"Error getting carbon intensity: {str(e)}")
        # Fallback to regional averages
        fallback_intensities = {
            'eu-central-1': 380,  # Germany
            'eu-west-1': 300,     # Ireland  
            'eu-west-2': 250,     # UK
            'eu-west-3': 90,      # France
            'eu-north-1': 40,     # Sweden
            'us-east-1': 450,     # US East
            'us-west-2': 350      # US West
        }
        return fallback_intensities.get(aws_region, 350)


def calculate_carbon_emissions(instance: Dict, carbon_intensity: float) -> float:
    """Calculate carbon emissions for an instance in kg CO2."""
    try:
        # Simplified power consumption estimates (Watts) for thesis
        power_estimates = {
            't3.micro': 5,
            't3.small': 10, 
            't3.medium': 20,
            't3.large': 40,
            't3.xlarge': 80
        }
        
        instance_type = instance.get('InstanceType', 't3.micro')
        power_watts = power_estimates.get(instance_type, 10)
        
        # Daily energy consumption (kWh) = (Watts * 24 hours) / 1000
        daily_energy_kwh = (power_watts * 24) / 1000
        
        # Carbon emissions (kg CO2) = energy (kWh) * carbon intensity (gCO2/kWh) / 1000
        carbon_emissions_kg = (daily_energy_kwh * carbon_intensity) / 1000
        
        return carbon_emissions_kg
    except Exception as e:
        logger.error(f"Error calculating carbon emissions: {str(e)}")
        return 0.0


def get_instance_schedule(instance: Dict) -> str:
    """Get the scheduling type for an instance based on its tags."""
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    return tags.get('ScheduleType', 'unknown')


def calculate_optimized_values(current_cost: float, current_carbon: float, 
                             schedule_type: str, carbon_intensity: float, 
                             carbon_threshold: float) -> Tuple[float, float]:
    """Calculate optimized cost and carbon values based on scheduling strategy."""
    
    if schedule_type == 'baseline':
        # Baseline: no optimization (24/7 running)
        return current_cost, current_carbon
    
    elif schedule_type == 'office-hours':
        # Office hours: ~40 hours/week vs 168 hours/week = ~24% utilization
        utilization_factor = 40 / 168
        return current_cost * utilization_factor, current_carbon * utilization_factor
    
    elif schedule_type == 'weekdays-only':
        # Weekdays only: ~120 hours/week vs 168 hours/week = ~71% utilization  
        utilization_factor = 120 / 168
        return current_cost * utilization_factor, current_carbon * utilization_factor
    
    elif schedule_type == 'carbon-aware':
        # Carbon-aware: stops when carbon intensity > threshold
        if carbon_intensity > carbon_threshold:
            # High carbon intensity - instance would be stopped
            utilization_factor = 0.7  # Assume 70% uptime on average
        else:
            utilization_factor = 1.0  # Normal operation
        return current_cost * utilization_factor, current_carbon * utilization_factor
    
    else:
        # Unknown schedule type
        return current_cost, current_carbon


def apply_scheduling_decision(instance: Dict, schedule_type: str, 
                            carbon_intensity: float, carbon_threshold: float):
    """Apply actual scheduling decisions to instances (for thesis demonstration)."""
    try:
        instance_id = instance['InstanceId']
        current_state = instance['State']['Name']
        
        should_run = should_instance_run(schedule_type, carbon_intensity, carbon_threshold)
        
        if should_run and current_state == 'stopped':
            logger.info(f"Starting instance {instance_id} based on {schedule_type} schedule")
            ec2.start_instances(InstanceIds=[instance_id])
        elif not should_run and current_state == 'running':
            logger.info(f"Stopping instance {instance_id} based on {schedule_type} schedule")
            ec2.stop_instances(InstanceIds=[instance_id])
        else:
            logger.info(f"No action needed for instance {instance_id} (current: {current_state})")
    
    except Exception as e:
        logger.error(f"Error applying scheduling decision: {str(e)}")


def should_instance_run(schedule_type: str, carbon_intensity: float, carbon_threshold: float) -> bool:
    """Determine if an instance should be running based on its schedule type."""
    current_time = datetime.utcnow()
    weekday = current_time.weekday()  # 0=Monday, 6=Sunday
    hour = current_time.hour
    
    if schedule_type == 'baseline':
        return True  # Always running
    
    elif schedule_type == 'office-hours':
        # Monday-Friday, 8 AM - 6 PM UTC
        return weekday < 5 and 8 <= hour <= 18
    
    elif schedule_type == 'weekdays-only':
        # Monday-Friday, 24 hours
        return weekday < 5
    
    elif schedule_type == 'carbon-aware':
        # Stop if carbon intensity is above threshold
        return carbon_intensity <= carbon_threshold
    
    else:
        return True  # Default: keep running


def store_analysis_result(table, result: Dict):
    """Store analysis result in DynamoDB."""
    try:
        # Convert float values to Decimal for DynamoDB
        for key, value in result.items():
            if isinstance(value, float):
                result[key] = Decimal(str(value))
        
        table.put_item(Item=result)
    except Exception as e:
        logger.error(f"Error storing result in DynamoDB: {str(e)}")


def send_cloudwatch_metrics(cost_savings: float, carbon_savings: float, instance_count: int):
    """Send metrics to CloudWatch for monitoring."""
    try:
        cloudwatch.put_metric_data(
            Namespace='CarbonAwareFinOps',
            MetricData=[
                {
                    'MetricName': 'CostSavingsUSD',
                    'Value': cost_savings,
                    'Unit': 'None'
                },
                {
                    'MetricName': 'CarbonSavingsKg',
                    'Value': carbon_savings,
                    'Unit': 'None'
                },
                {
                    'MetricName': 'InstancesAnalyzed',
                    'Value': instance_count,
                    'Unit': 'Count'
                }
            ]
        )
    except Exception as e:
        logger.error(f"Error sending CloudWatch metrics: {str(e)}")