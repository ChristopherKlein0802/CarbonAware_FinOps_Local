"""
Simplified DynamoDB Service for Carbon-Aware FinOps Data Persistence
Stores API data for historical analysis in the Bachelor Thesis dashboard
"""

import boto3
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DynamoDBService:
    """Simplified service for persisting dashboard data to DynamoDB."""
    
    def __init__(self, aws_profile='carbon-finops-sandbox', project_name='carbon-aware-finops'):
        self.aws_profile = aws_profile
        self.project_name = project_name
        self.table = None
        
        try:
            boto3.setup_default_session(profile_name=aws_profile)
            self.dynamodb = boto3.resource('dynamodb')
            self.table_name = f"{project_name}-analysis-data"
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"DynamoDB service initialized with table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB service: {e}")

    def _convert_floats_to_decimal(self, data):
        """Convert floats to Decimal for DynamoDB compatibility."""
        if isinstance(data, float):
            return Decimal(str(data))
        elif isinstance(data, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_floats_to_decimal(item) for item in data]
        return data

    def store_carbon_intensity(self, region: str, carbon_intensity: float) -> bool:
        """Store ElectricityMap carbon intensity data."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f'CARBON#{region}',
                'SK': timestamp,
                'DataType': 'CARBON_INTENSITY',
                'Timestamp': timestamp,
                'Region': region,
                'CarbonIntensity': Decimal(str(carbon_intensity)),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (30 * 24 * 3600))  # 30 days
            }
                
            self.table.put_item(Item=item)
            logger.info(f"Stored carbon intensity for {region}: {carbon_intensity} gCO2/kWh")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store carbon intensity data: {e}")
            return False

    def store_power_data(self, instance_type: str, power_data: Dict) -> bool:
        """Store Boavizta power consumption data."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f'POWER#{instance_type}',
                'SK': timestamp,
                'DataType': 'POWER_CONSUMPTION',
                'Timestamp': timestamp,
                'InstanceType': instance_type,
                'IdlePower': Decimal(str(power_data.get('idle_power_watts', 0))),
                'AvgPower': Decimal(str(power_data.get('avg_power_watts', 0))),
                'MaxPower': Decimal(str(power_data.get('max_power_watts', 0))),
                'DataSource': power_data.get('data_source', 'unknown'),
                'Confidence': power_data.get('confidence_level', 'low'),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (7 * 24 * 3600))  # 7 days
            }
                
            self.table.put_item(Item=item)
            logger.info(f"Stored power data for {instance_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store power data: {e}")
            return False

    def store_cost_data(self, instance_data: List[Dict]) -> bool:
        """Store instance cost analysis data."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Store aggregated cost data
            total_monthly_cost = sum(float(instance.get('monthly_cost_usd', 0)) for instance in instance_data)
            total_monthly_co2 = sum(float(instance.get('monthly_co2_kg', 0)) for instance in instance_data)
            
            item = {
                'PK': 'COST#ANALYSIS',
                'SK': timestamp,
                'DataType': 'COST_ANALYSIS',
                'Timestamp': timestamp,
                'TotalMonthlyCostUSD': Decimal(str(total_monthly_cost)),
                'TotalMonthlyCO2Kg': Decimal(str(total_monthly_co2)),
                'InstanceCount': len(instance_data),
                'InstanceData': self._convert_floats_to_decimal(instance_data),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (90 * 24 * 3600))  # 90 days
            }
                
            self.table.put_item(Item=item)
            logger.info(f"Stored cost analysis for {len(instance_data)} instances")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store cost data: {e}")
            return False

    def get_historical_carbon_data(self, region: str, days: int = 7) -> List[Dict]:
        """Get historical carbon intensity data for region."""
        if not self.table:
            return []
            
        try:
            # Calculate timestamp threshold
            threshold = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
            threshold_iso = datetime.fromtimestamp(threshold, timezone.utc).isoformat()
            
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND SK > :threshold',
                ExpressionAttributeValues={
                    ':pk': f'CARBON#{region}',
                    ':threshold': threshold_iso
                },
                ScanIndexForward=False  # Latest first
            )
            
            # Convert Decimal back to float for JSON serialization
            items = []
            for item in response.get('Items', []):
                items.append({
                    'timestamp': item['Timestamp'],
                    'carbon_intensity': float(item['CarbonIntensity']),
                    'region': item['Region']
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get historical carbon data: {e}")
            return []

    def get_historical_cost_data(self, days: int = 30) -> List[Dict]:
        """Get historical cost analysis data."""
        if not self.table:
            return []
            
        try:
            threshold = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
            threshold_iso = datetime.fromtimestamp(threshold, timezone.utc).isoformat()
            
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND SK > :threshold',
                ExpressionAttributeValues={
                    ':pk': 'COST#ANALYSIS',
                    ':threshold': threshold_iso
                },
                ScanIndexForward=False
            )
            
            items = []
            for item in response.get('Items', []):
                items.append({
                    'timestamp': item['Timestamp'],
                    'total_monthly_cost': float(item['TotalMonthlyCostUSD']),
                    'total_monthly_co2': float(item['TotalMonthlyCO2Kg']),
                    'instance_count': item['InstanceCount']
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get historical cost data: {e}")
            return []

    def get_data_summary(self) -> Dict:
        """Get summary of stored data points."""
        if not self.table:
            return {'carbon_points': 0, 'cost_points': 0, 'power_points': 0}
            
        try:
            summary = {'carbon_points': 0, 'cost_points': 0, 'power_points': 0}
            
            # Count different data types using GSI
            for data_type, key in [('CARBON_INTENSITY', 'carbon_points'), 
                                  ('COST_ANALYSIS', 'cost_points'),
                                  ('POWER_CONSUMPTION', 'power_points')]:
                try:
                    response = self.table.query(
                        IndexName='DataTypeIndex',
                        KeyConditionExpression='DataType = :dt',
                        ExpressionAttributeValues={':dt': data_type},
                        Select='COUNT'
                    )
                    summary[key] = response['Count']
                except Exception:
                    continue
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {'carbon_points': 0, 'cost_points': 0, 'power_points': 0}