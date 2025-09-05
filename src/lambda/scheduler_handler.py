"""
Infrastructure Analysis Lambda Function for Bachelor Thesis

This function analyzes AWS infrastructure to calculate cost and carbon consumption,
then determines optimization potential through various scheduling strategies.
It combines real AWS Cost Explorer data with German grid carbon intensity data.

Core thesis contribution: Quantifying optimization potential for both cost AND carbon reduction.
Focus: Analysis and recommendations, NOT automatic infrastructure changes.
"""

import json
import os
import boto3
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from decimal import Decimal
import logging

# Lightweight imports for Lambda
try:
    from src.carbon.carbon_api_client import CarbonIntensityClient
    from src.services.power_consumption_service import PowerConsumptionService
except ImportError:
    import sys
    sys.path.insert(0, "/opt/python")
    from src.carbon.carbon_api_client import CarbonIntensityClient
    from src.services.power_consumption_service import PowerConsumptionService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
ec2 = boto3.client('ec2')
ce = boto3.client('ce')  # Cost Explorer
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


def lambda_handler(_event, _context):
    """
    Main Lambda handler for infrastructure analysis and optimization potential calculation.
    
    This function:
    1. Analyzes current EC2 instances and their real costs (AWS Cost Explorer)
    2. Gets real-time German grid carbon intensity data (ElectricityMap)
    3. Calculates current cost and carbon consumption
    4. Determines optimization potential for different scheduling strategies
    5. Stores analysis results for dashboard visualization
    
    NOTE: This function does NOT modify instances - it only analyzes and calculates potential.
    """
    try:
        logger.info("Starting Infrastructure Analysis and Optimization Potential Calculation")
        
        # Get environment variables
        project_name = os.environ.get('PROJECT_NAME', 'carbon-aware-finops')
        results_table_name = os.environ.get('DYNAMODB_RESULTS_TABLE')
        carbon_threshold = float(os.environ.get('CARBON_THRESHOLD', '400'))
        aws_region = os.environ.get('AWS_REGION', 'eu-central-1')
        analysis_mode = os.environ.get('DEPLOYMENT_MODE', 'universal')
        
        if not results_table_name:
            raise ValueError("DYNAMODB_RESULTS_TABLE environment variable not set")
        
        results_table = dynamodb.Table(results_table_name)  # type: ignore
        
        # 1. Get current test instances
        instances = get_test_instances(project_name)
        logger.info(f"Found {len(instances)} test instances")
        
        # 2. Get real cost data from Cost Explorer
        cost_data = get_ec2_costs(instances)
        logger.info(f"Retrieved cost data for {len(cost_data)} instances")
        
        # 3. Get current carbon intensity
        carbon_intensity = get_carbon_intensity(aws_region)
        logger.info(f"Current carbon intensity: {carbon_intensity} gCO2/kWh")
        
        # 4. Analyze each instance and calculate optimization potential
        analysis_results = []
        total_current_costs = 0
        total_current_carbon = 0
        optimization_scenarios = ['office_hours', 'weekdays_only', 'carbon_aware']
        
        for instance in instances:
            instance_id = instance['InstanceId']
            instance_name = get_instance_name(instance)
            
            # Calculate current costs and carbon
            current_cost = cost_data.get(instance_id, {}).get('daily_cost', 0)
            current_carbon = calculate_carbon_emissions(instance, carbon_intensity)
            
            total_current_costs += current_cost
            total_current_carbon += current_carbon
            
            # Calculate optimization potential for each scenario
            optimization_potential = {}
            for scenario in optimization_scenarios:
                optimized_cost, optimized_carbon = calculate_optimized_values(
                    current_cost, current_carbon, scenario, carbon_intensity, carbon_threshold
                )
                
                optimization_potential[scenario] = {
                    'cost_savings': float(current_cost - optimized_cost),
                    'carbon_savings': float(current_carbon - optimized_carbon),
                    'optimized_cost': float(optimized_cost),
                    'optimized_carbon': float(optimized_carbon),
                    'runtime_hours_month': get_scenario_runtime_hours(scenario)
                }
            
            # Store individual instance analysis with optimization potential
            result = {
                'instance_id': instance_id,
                'instance_name': instance_name,
                'timestamp': int(datetime.now(timezone.utc).timestamp()),
                'analysis_mode': analysis_mode,
                'current_cost_usd': float(current_cost),
                'current_carbon_kg': float(current_carbon),
                'carbon_intensity': carbon_intensity,
                'instance_type': instance.get('InstanceType'),
                'state': instance['State']['Name'],
                'region': aws_region,
                'optimization_potential': optimization_potential
            }
            
            analysis_results.append(result)
            
            # Store in DynamoDB
            store_analysis_result(results_table, result)
            
            logger.info(f"Analyzed {instance_id}: €{current_cost:.2f}/month, {current_carbon:.2f}kg CO2/month")
        
        # 5. Calculate aggregated optimization potential
        total_optimization_potential = {}
        for scenario in optimization_scenarios:
            total_cost_savings = sum(
                result['optimization_potential'][scenario]['cost_savings'] 
                for result in analysis_results
            )
            total_carbon_savings = sum(
                result['optimization_potential'][scenario]['carbon_savings'] 
                for result in analysis_results
            )
            total_optimization_potential[scenario] = {
                'total_cost_savings': total_cost_savings,
                'total_carbon_savings': total_carbon_savings
            }
        
        # Store aggregated analysis summary
        aggregated_result = {
            'instance_id': 'INFRASTRUCTURE_SUMMARY',
            'timestamp': int(datetime.now(timezone.utc).timestamp()),
            'analysis_mode': analysis_mode,
            'total_instances': len(instances),
            'total_current_cost_usd': float(total_current_costs),
            'total_current_carbon_kg': float(total_current_carbon),
            'carbon_intensity': carbon_intensity,
            'region': aws_region,
            'optimization_potential_summary': total_optimization_potential,
            'analysis_date': datetime.now(timezone.utc).isoformat()
        }
        
        store_analysis_result(results_table, aggregated_result)
        
        # 6. Send CloudWatch metrics for monitoring
        best_scenario = max(optimization_scenarios, key=lambda s: total_optimization_potential[s]['total_cost_savings'])
        best_cost_savings = total_optimization_potential[best_scenario]['total_cost_savings']
        best_carbon_savings = total_optimization_potential[best_scenario]['total_carbon_savings']
        
        send_cloudwatch_metrics(best_cost_savings, best_carbon_savings, len(instances))
        
        logger.info(f"Infrastructure analysis complete. Analyzed {len(instances)} instances.")
        logger.info(f"Current: €{total_current_costs:.2f}/month, {total_current_carbon:.1f} kg CO2/month")
        logger.info(f"Best optimization potential ({best_scenario}): €{best_cost_savings:.2f} savings, {best_carbon_savings:.1f} kg CO2 savings")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Infrastructure analysis completed successfully',
                'analysis_mode': analysis_mode,
                'instances_analyzed': len(instances),
                'total_current_cost_usd': float(total_current_costs),
                'total_current_carbon_kg': float(total_current_carbon),
                'optimization_potential': total_optimization_potential,
                'carbon_intensity': carbon_intensity,
                'region': aws_region
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
    """Get instances for analysis - ALL instances in universal mode, or tagged instances in testing mode."""
    try:
        # Check if we're in universal mode (analyze ALL instances in account)
        analyze_all = os.environ.get('ANALYZE_ALL_INSTANCES', 'true').lower() == 'true'
        deployment_mode = os.environ.get('DEPLOYMENT_MODE', 'universal')
        
        if deployment_mode == 'universal' or analyze_all:
            # Universal mode: Analyze ALL EC2 instances in the account
            logger.info("Universal mode: Analyzing ALL instances in account")
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )
        else:
            # Testing mode: Only analyze tagged test instances
            logger.info(f"Testing mode: Analyzing only tagged instances for project {project_name}")
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
        
        logger.info(f"Found {len(instances)} instances for analysis (mode: {deployment_mode})")
        return instances
        
    except Exception as e:
        logger.error(f"Error getting instances: {str(e)}")
        return []


def get_ec2_costs(instances: List[Dict]) -> Dict[str, Dict]:
    """Get real cost data from Cost Explorer for EC2 instances."""
    try:
        # Get costs for the last 24 hours
        end_date = datetime.now(timezone.utc).date()
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
        total_cost = 0
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                total_cost += cost
        
        # Always use actual Cost Explorer data (even if $0) - no fallbacks for thesis research
        avg_cost_per_instance = total_cost / max(len(instances), 1)
        for instance in instances:
            instance_id = instance['InstanceId']
            cost_data[instance_id] = {'daily_cost': avg_cost_per_instance}
        
        logger.info(f"Real AWS Cost Explorer data: ${total_cost:.4f} total, ${avg_cost_per_instance:.4f} per instance")
        return cost_data
    except Exception as e:
        logger.error(f"Error getting cost data from Cost Explorer: {str(e)}")
        # Return empty/zero costs when Cost Explorer API fails - no fallbacks for thesis research
        cost_data = {}
        for instance in instances:
            instance_id = instance['InstanceId']
            cost_data[instance_id] = {'daily_cost': 0.0}
        logger.warning("Using $0.00 costs due to Cost Explorer API error - no fallback data for thesis accuracy")
        return cost_data




def get_carbon_intensity(aws_region: str) -> float:
    """Get current carbon intensity for the AWS region, focused on German grid data."""
    try:
        # Import carbon client (reusing existing code)
        carbon_client = CarbonIntensityClient()
        
        # For German regions, always use German grid data (zone=DE)
        if aws_region in ['eu-central-1', 'eu-central-2']:
            # Force German grid data for thesis research accuracy
            intensity = carbon_client.get_current_intensity('eu-central-1')
            logger.info(f"Using German grid intensity for region {aws_region}: {intensity} gCO2/kWh")
        else:
            intensity = carbon_client.get_current_intensity(aws_region)
            logger.info(f"Using regional grid intensity for {aws_region}: {intensity} gCO2/kWh")
        
        return intensity
    except Exception as e:
        logger.error(f"Error getting carbon intensity: {str(e)}")
        # German-focused fallback values (more accurate for thesis)
        german_focused_fallbacks = {
            'eu-central-1': 420,  # Germany (higher during coal periods)
            'eu-central-2': 380,  # Zurich/Switzerland (close to Germany)
            'eu-west-1': 320,     # Ireland  
            'eu-west-2': 280,     # UK
            'eu-west-3': 100,     # France (nuclear heavy)
            'eu-north-1': 50,     # Sweden (hydro/nuclear)
            'us-east-1': 450,     # US East
            'us-west-2': 350      # US West
        }
        fallback_value = german_focused_fallbacks.get(aws_region, 400)
        logger.warning(f"Using fallback carbon intensity for {aws_region}: {fallback_value} gCO2/kWh")
        return fallback_value


def calculate_carbon_emissions(instance: Dict, carbon_intensity: float) -> float:
    """
    Calculate carbon emissions for an instance using real power consumption data.
    
    Enhanced with Boavizta API integration for accurate hardware power consumption.
    Falls back to comprehensive estimates if API is unavailable.
    """
    try:
        power_service = PowerConsumptionService()
        instance_type = instance.get('InstanceType', 'unknown')
        
        # Get real power consumption data (Boavizta API + fallback)
        power_data = power_service.get_instance_power_consumption(instance_type)
        
        # Calculate emissions using comprehensive power data and carbon intensity
        # Assume typical 50% utilization for running instances
        emissions_data = power_service.calculate_carbon_emissions(
            power_consumption=power_data,
            carbon_intensity_g_kwh=carbon_intensity,
            usage_hours=24.0,  # Daily emissions
            utilization_factor=0.5  # 50% average utilization
        )
        
        # Return daily carbon emissions in kg CO2
        daily_carbon_kg = emissions_data['carbon_emissions_kg']
        
        logger.info(f"Carbon calculation for {instance_type}: "
                   f"{daily_carbon_kg:.4f} kg CO2/day "
                   f"(Power: {emissions_data['power_watts']:.1f}W, "
                   f"Source: {power_data.data_source}, "
                   f"Confidence: {power_data.confidence_level})")
        
        return daily_carbon_kg
        
    except Exception as e:
        logger.error(f"Error calculating carbon emissions for {instance.get('InstanceType', 'unknown')}: {e}")
        
        # Fallback to simple estimates if service fails
        simplified_estimates = {
            't3.micro': 5,
            't3.small': 10, 
            't3.medium': 20,
            't3.large': 40,
            't3.xlarge': 80
        }
        
        instance_type = instance.get('InstanceType', 't3.micro')
        power_watts = simplified_estimates.get(instance_type, 10)
        
        # Daily energy consumption (kWh) = (Watts * 24 hours) / 1000
        daily_energy_kwh = (power_watts * 24) / 1000
        
        # Carbon emissions (kg CO2) = energy (kWh) * carbon intensity (gCO2/kWh) / 1000
        carbon_emissions_kg = (daily_energy_kwh * carbon_intensity) / 1000
        
        logger.warning(f"Using fallback carbon calculation for {instance_type}: {carbon_emissions_kg:.4f} kg CO2/day")
        return carbon_emissions_kg


def get_instance_name(instance: Dict) -> str:
    """Get a human-readable name for the instance."""
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    
    # Try different name tag variations
    for name_key in ['Name', 'name', 'InstanceName', 'instance-name']:
        if name_key in tags:
            return tags[name_key]
    
    # Fallback to instance ID
    return instance['InstanceId']

def get_scenario_runtime_hours(scenario: str) -> int:
    """Get the runtime hours per month for each optimization scenario."""
    scenario_hours = {
        'office_hours': 200,    # 8h × 5days × 4weeks = 160h, rounded up to 200h
        'weekdays_only': 520,   # 24h × 5days × 4weeks = 480h, rounded up to 520h  
        'carbon_aware': 612,    # ~85% uptime (avoiding peak carbon hours)
        'baseline': 720         # 24h × 30days = 720h
    }
    return scenario_hours.get(scenario, 720)

def get_instance_schedule(instance: Dict) -> str:
    """Get the scheduling type for an instance based on its tags."""
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    
    # Check for explicit ScheduleType tag first
    if 'ScheduleType' in tags:
        return tags['ScheduleType']
    
    # For universal deployment: infer schedule type or default to baseline
    deployment_mode = os.environ.get('DEPLOYMENT_MODE', 'universal')
    if deployment_mode == 'universal':
        # In universal mode, treat all instances as baseline (no scheduling) by default
        # Users can manually tag instances with ScheduleType for optimization
        return 'baseline'
    
    # Testing mode fallback
    return 'unknown'


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


# =============================================================================
# AUTOMATIC SCHEDULING FUNCTIONS REMOVED FOR ANALYSIS-FOCUSED APPROACH
# =============================================================================
# 
# This tool focuses on ANALYSIS and OPTIMIZATION POTENTIAL calculation only.
# It does NOT automatically modify infrastructure - this ensures:
# 
# 1. Customer Safety: No unexpected downtime in production environments
# 2. Business Acceptance: Shows value before requiring trust in automation
# 3. Thesis Validity: Demonstrates potential rather than disruptive implementation
# 4. Practical Deployment: Can be safely deployed in any AWS environment
#
# For customers wanting to implement the scheduling recommendations:
# - Export the optimization analysis results
# - Use external automation tools (Terraform, AWS Lambda, etc.)
# - Implement gradual rollout based on the calculated potential
# - Monitor actual vs. predicted savings
# 
# This approach provides the scientific foundation for optimization decisions
# while leaving implementation control with the customer.


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