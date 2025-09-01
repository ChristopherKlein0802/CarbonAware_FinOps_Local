import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SpotInstanceManager:
    """Manages Spot Instance recommendations and migrations."""

    def __init__(self, region='eu-central-1'):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ce = boto3.client('ce', region_name=region)
        self.region = region

        # Workload suitability criteria
        self.suitability_criteria = {
            'stateless': True,
            'fault_tolerant': True,
            'flexible_timing': True,
            'checkpointing': False,
            'short_duration': True
        }

    def analyze_workload_suitability(self, instance_id: str) -> Dict:
        """Analyze if workload is suitable for Spot Instances."""

        instance = self.get_instance_details(instance_id)
        if not instance:
            return {'suitable': False, 'reason': 'Instance not found'}

        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}

        suitability_score = 0
        reasons = []

        # Check workload type from tags
        workload_type = tags.get('WorkloadType', 'unknown')

        # Batch processing is ideal for Spot
        if 'batch' in workload_type.lower():
            suitability_score += 30
            reasons.append("Batch processing workload")

        # Dev/Test environments are good candidates
        if tags.get('Environment', '').lower() in ['dev', 'test', 'development']:
            suitability_score += 25
            reasons.append("Non-production environment")

        # Check if instance has auto-scaling group
        if instance.get('AutoScalingGroup'):
            suitability_score += 20
            reasons.append("Part of Auto Scaling group")

        # Check schedule tag - flexible schedules are good for Spot
        schedule = tags.get('Schedule', '')
        if 'carbon-aware' in schedule.lower() or 'flexible' in schedule.lower():
            suitability_score += 25
            reasons.append("Flexible scheduling")

        # Determine suitability
        suitable = suitability_score >= 50

        return {
            'suitable': suitable,
            'score': suitability_score,
            'reasons': reasons,
            'instance_id': instance_id,
            'current_type': instance['InstanceType'],
            'recommendations': self.get_spot_recommendations(instance['InstanceType']) if suitable else []
        }

    def get_spot_recommendations(self, instance_type: str) -> List[Dict]:
        """Get Spot Instance recommendations for given instance type."""

        try:
            # Get Spot price history
            response = self.ec2.describe_spot_price_history(
                InstanceTypes=[instance_type],
                MaxResults=20,
                ProductDescriptions=['Linux/UNIX'],
                StartTime=datetime.now() - timedelta(days=7)
            )

            if not response['SpotPriceHistory']:
                return []

            # Calculate average spot price
            prices = [float(item['SpotPrice']) for item in response['SpotPriceHistory']]
            avg_spot_price = sum(prices) / len(prices)

            # Get on-demand price (simplified - should use Pricing API)
            on_demand_prices = {
                't3.micro': 0.0104,
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                't3.xlarge': 0.1664,
            }

            on_demand_price = on_demand_prices.get(instance_type, 0.05)

            # Calculate savings
            savings_percentage = ((on_demand_price - avg_spot_price) / on_demand_price) * 100

            return [{
                'instance_type': instance_type,
                'avg_spot_price': round(avg_spot_price, 4),
                'on_demand_price': on_demand_price,
                'savings_percentage': round(savings_percentage, 1),
                'availability_zones': self.get_best_availability_zones(instance_type),
                'interruption_rate': self.estimate_interruption_rate(instance_type)
            }]

        except Exception as e:
            logger.error(f"Error getting spot recommendations: {e}")
            return []

    def get_best_availability_zones(self, instance_type: str) -> List[str]:
        """Get AZs with best Spot availability."""

        try:
            response = self.ec2.describe_spot_price_history(
                InstanceTypes=[instance_type],
                MaxResults=100,
                ProductDescriptions=['Linux/UNIX'],
                StartTime=datetime.now() - timedelta(days=1)
            )

            # Count prices per AZ (more prices = more availability)
            az_counts = {}
            for item in response['SpotPriceHistory']:
                az = item['AvailabilityZone']
                az_counts[az] = az_counts.get(az, 0) + 1

            # Sort by frequency
            sorted_azs = sorted(az_counts.items(), key=lambda x: x[1], reverse=True)
            return [az for az, _ in sorted_azs[:3]]

        except Exception as e:
            logger.error(f"Error getting best AZs: {e}")
            return []

    def estimate_interruption_rate(self, instance_type: str) -> str:
        """Estimate Spot interruption rate based on instance type."""

        # Simplified estimation based on instance size
        # Smaller instances typically have lower interruption rates
        size_interruption_map = {
            'micro': 'Low (<5%)',
            'small': 'Low (<5%)',
            'medium': 'Medium (5-10%)',
            'large': 'Medium (5-10%)',
            'xlarge': 'High (10-20%)',
            '2xlarge': 'High (10-20%)',
        }

        size = instance_type.split('.')[1]
        return size_interruption_map.get(size, 'Unknown')

    def calculate_spot_savings(self, instance_ids: List[str], days: int = 30) -> Dict:
        """Calculate potential savings by switching to Spot Instances."""

        total_on_demand_cost = 0
        total_spot_cost = 0
        recommendations = []

        for instance_id in instance_ids:
            suitability = self.analyze_workload_suitability(instance_id)

            if suitability['suitable'] and suitability['recommendations']:
                rec = suitability['recommendations'][0]

                # Calculate monthly costs
                hours_per_month = days * 24
                on_demand_monthly = rec['on_demand_price'] * hours_per_month
                spot_monthly = rec['avg_spot_price'] * hours_per_month

                total_on_demand_cost += on_demand_monthly
                total_spot_cost += spot_monthly

                recommendations.append({
                    'instance_id': instance_id,
                    'instance_type': rec['instance_type'],
                    'monthly_on_demand': round(on_demand_monthly, 2),
                    'monthly_spot': round(spot_monthly, 2),
                    'monthly_savings': round(on_demand_monthly - spot_monthly, 2),
                    'savings_percentage': rec['savings_percentage']
                })

        return {
            'total_on_demand_cost': round(total_on_demand_cost, 2),
            'total_spot_cost': round(total_spot_cost, 2),
            'total_savings': round(total_on_demand_cost - total_spot_cost, 2),
            'savings_percentage': round(((total_on_demand_cost - total_spot_cost) / total_on_demand_cost * 100), 1) if total_on_demand_cost > 0 else 0,
            'recommendations': recommendations,
            'suitable_instances': len(recommendations),
            'analysis_date': datetime.now().isoformat()
        }

    def create_spot_fleet_request(self, config: Dict) -> str:
        """Create a Spot Fleet request for migrating instances."""

        # This would create actual Spot Fleet request
        # Simplified for demonstration

        spot_config = {
            'AllocationStrategy': 'lowest-price',
            'IamFleetRole': config['iam_fleet_role'],
            'SpotPrice': str(config['max_price']),
            'TargetCapacity': config['target_capacity'],
            'LaunchSpecifications': [
                {
                    'ImageId': config['ami_id'],
                    'InstanceType': config['instance_type'],
                    'KeyName': config.get('key_name'),
                    'SecurityGroups': config.get('security_groups', []),
                    'UserData': config.get('user_data', ''),
                    'TagSpecifications': [
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {'Key': 'Project', 'Value': 'carbon-aware-finops'},
                                {'Key': 'Type', 'Value': 'spot'},
                                {'Key': 'MigratedFrom', 'Value': config.get('source_instance', 'unknown')}
                            ]
                        }
                    ]
                }
            ]
        }

        try:
            response = self.ec2.request_spot_fleet(SpotFleetRequestConfig=spot_config)
            return response['SpotFleetRequestId']
        except Exception as e:
            logger.error(f"Error creating spot fleet: {e}")
            return None

    def get_instance_details(self, instance_id: str) -> Optional[Dict]:
        """Get EC2 instance details."""
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            if response['Reservations']:
                return response['Reservations'][0]['Instances'][0]
        except Exception as e:
            logger.error(f"Error getting instance details: {e}")
        return None