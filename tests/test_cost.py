"""Tests for AWS cost client."""

from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

from src.cost.aws_cost_client import AWSCostClient


class TestAWSCostClient:
    """Test AWS cost client functionality."""
    
    @patch('boto3.client')
    def test_cost_client_initialization(self, mock_boto):
        """Test cost client initialization."""
        client = AWSCostClient(region='eu-central-1')
        mock_boto.assert_called_with('ce', region_name='eu-central-1')
    
    @patch('boto3.client')
    def test_get_instance_costs(self, mock_boto):
        """Test getting instance costs."""
        # Mock CE client
        mock_ce = Mock()
        mock_boto.return_value = mock_ce
        
        # Mock response
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [{
                'TimePeriod': {'Start': '2024-01-01'},
                'Groups': [{
                    'Keys': ['t3.micro', 'tag$i-1234567890'],
                    'Metrics': {
                        'UnblendedCost': {'Amount': '1.50'},
                        'UsageQuantity': {'Amount': '24.0'}
                    }
                }]
            }]
        }
        
        # Test
        client = AWSCostClient()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        df = client.get_instance_costs(['i-1234567890'], start_date, end_date)
        
        assert not df.empty
        assert df.iloc[0]['cost'] == 1.50
        assert df.iloc[0]['usage_hours'] == 24.0
    
    def test_calculate_savings(self):
        """Test savings calculation."""
        client = AWSCostClient()
        
        # Create test data
        baseline = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=7),
            'cost': [10.0] * 7
        })
        
        optimized = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=7),
            'cost': [7.0] * 7
        })
        
        savings = client.calculate_savings(baseline, optimized)
        
        assert savings['total_baseline_cost'] == 70.0
        assert savings['total_optimized_cost'] == 49.0
        assert savings['absolute_savings'] == 21.0
        assert savings['percentage_savings'] == 30.0