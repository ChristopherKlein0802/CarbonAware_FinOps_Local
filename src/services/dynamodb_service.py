"""
DynamoDB Service for API Data Persistence and Analysis Storage

This service handles:
1. Storing API data from ElectricityMap, Boavizta, AWS Cost Explorer
2. Caching analysis results for dashboard performance
3. Historical data tracking for trend analysis
4. Data retrieval for dashboard components

Data Model:
- PK: Data source (e.g., "ELECTRICITYMAP", "BOAVIZTA", "COST_EXPLORER", "ANALYSIS")  
- SK: Timestamp or specific identifier
- GSI: DataType + Timestamp for querying
"""

import boto3
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class DynamoDBService:
    """Service for persisting API data and analysis results."""
    
    def __init__(self, aws_profile='carbon-finops-sandbox', project_name='carbon-aware-finops'):
        self.aws_profile = aws_profile
        self.project_name = project_name
        
        try:
            boto3.setup_default_session(profile_name=aws_profile)
            self.dynamodb = boto3.resource('dynamodb')
            self.table_name = f"{project_name}-analysis-data"
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"DynamoDB service initialized with table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB service: {e}")
            self.dynamodb = None
            self.table = None

    def _convert_floats_to_decimal(self, data: Any) -> Any:
        """Convert floats to Decimal for DynamoDB compatibility."""
        if isinstance(data, float):
            return Decimal(str(data))
        elif isinstance(data, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_floats_to_decimal(item) for item in data]
        return data

    def store_electricity_map_data(self, region: str, carbon_intensity: float, metadata: Dict = None) -> bool:
        """Store ElectricityMap carbon intensity data."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f'ELECTRICITYMAP#{region}',
                'SK': timestamp,
                'DataType': 'CARBON_INTENSITY',
                'Timestamp': timestamp,
                'Region': region,
                'CarbonIntensity': Decimal(str(carbon_intensity)),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (7 * 24 * 3600))  # 7 days
            }
            
            if metadata:
                item.update(self._convert_floats_to_decimal(metadata))
                
            self.table.put_item(Item=item)
            logger.info(f"Stored ElectricityMap data for {region}: {carbon_intensity} gCO2/kWh")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store ElectricityMap data: {e}")
            return False

    def store_boavizta_data(self, instance_type: str, power_data: Dict) -> bool:
        """Store Boavizta hardware power consumption data."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f'BOAVIZTA#{instance_type}',
                'SK': timestamp,
                'DataType': 'POWER_CONSUMPTION',
                'Timestamp': timestamp,
                'InstanceType': instance_type,
                'IdlePower': Decimal(str(power_data.get('idle_power', 0))),
                'AvgPower': Decimal(str(power_data.get('avg_power', 0))),
                'MaxPower': Decimal(str(power_data.get('max_power', 0))),
                'DataSource': power_data.get('data_source', 'unknown'),
                'Confidence': power_data.get('confidence', 'low'),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (24 * 3600))  # 1 day
            }
                
            self.table.put_item(Item=item)
            logger.info(f"Stored Boavizta data for {instance_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Boavizta data: {e}")
            return False

    def store_cost_explorer_data(self, account_id: str, cost_data: Dict) -> bool:
        """Store AWS Cost Explorer data."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f'COST_EXPLORER#{account_id}',
                'SK': timestamp,
                'DataType': 'COST_DATA',
                'Timestamp': timestamp,
                'AccountId': account_id,
                'CostData': self._convert_floats_to_decimal(cost_data),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (30 * 24 * 3600))  # 30 days
            }
                
            self.table.put_item(Item=item)
            logger.info(f"Stored Cost Explorer data for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Cost Explorer data: {e}")
            return False

    def store_analysis_results(self, analysis_id: str, results: Dict) -> bool:
        """Store dashboard analysis results."""
        if not self.table:
            return False
            
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f'ANALYSIS#{analysis_id}',
                'SK': timestamp,
                'DataType': 'ANALYSIS_RESULTS',
                'Timestamp': timestamp,
                'AnalysisId': analysis_id,
                'Results': self._convert_floats_to_decimal(results),
                'TTL': int((datetime.now(timezone.utc).timestamp()) + (7 * 24 * 3600))  # 7 days
            }
                
            self.table.put_item(Item=item)
            logger.info(f"Stored analysis results for {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis results: {e}")
            return False

    def get_latest_carbon_intensity(self, region: str) -> Optional[Dict]:
        """Get latest carbon intensity data for region."""
        if not self.table:
            return None
            
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'ELECTRICITYMAP#{region}'
                },
                ScanIndexForward=False,  # Latest first
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                return {
                    'carbon_intensity': float(item['CarbonIntensity']),
                    'timestamp': item['Timestamp'],
                    'region': item['Region']
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get carbon intensity data: {e}")
            return None

    def get_latest_power_data(self, instance_type: str) -> Optional[Dict]:
        """Get latest power consumption data for instance type."""
        if not self.table:
            return None
            
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'BOAVIZTA#{instance_type}'
                },
                ScanIndexForward=False,  # Latest first
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                return {
                    'instance_type': item['InstanceType'],
                    'idle_power': float(item['IdlePower']),
                    'avg_power': float(item['AvgPower']),
                    'max_power': float(item['MaxPower']),
                    'data_source': item['DataSource'],
                    'confidence': item['Confidence'],
                    'timestamp': item['Timestamp']
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get power data: {e}")
            return None

    def get_historical_data(self, data_type: str, hours: int = 24) -> List[Dict]:
        """Get historical data for trend analysis."""
        if not self.table:
            return []
            
        try:
            # Calculate timestamp threshold
            threshold = datetime.now(timezone.utc).timestamp() - (hours * 3600)
            threshold_iso = datetime.fromtimestamp(threshold, timezone.utc).isoformat()
            
            response = self.table.query(
                IndexName='DataTypeIndex',
                KeyConditionExpression='DataType = :dt AND #ts > :threshold',
                ExpressionAttributeNames={
                    '#ts': 'Timestamp'
                },
                ExpressionAttributeValues={
                    ':dt': data_type,
                    ':threshold': threshold_iso
                },
                ScanIndexForward=False  # Latest first
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return []

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of stored data for dashboard status."""
        if not self.table:
            return {}
            
        try:
            summary = {
                'carbon_intensity_points': 0,
                'power_data_points': 0,
                'cost_data_points': 0,
                'analysis_results': 0,
                'last_update': None
            }
            
            # Count different data types
            for data_type in ['CARBON_INTENSITY', 'POWER_CONSUMPTION', 'COST_DATA', 'ANALYSIS_RESULTS']:
                try:
                    response = self.table.query(
                        IndexName='DataTypeIndex',
                        KeyConditionExpression='DataType = :dt',
                        ExpressionAttributeValues={
                            ':dt': data_type
                        },
                        Select='COUNT'
                    )
                    
                    if data_type == 'CARBON_INTENSITY':
                        summary['carbon_intensity_points'] = response['Count']
                    elif data_type == 'POWER_CONSUMPTION':
                        summary['power_data_points'] = response['Count']
                    elif data_type == 'COST_DATA':
                        summary['cost_data_points'] = response['Count']
                    elif data_type == 'ANALYSIS_RESULTS':
                        summary['analysis_results'] = response['Count']
                        
                except Exception:
                    continue
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get analysis summary: {e}")
            return {}