#!/usr/bin/env python3
"""
Unit Tests for API Clients
Carbon-Aware FinOps Dashboard - Bachelor Thesis

Tests API client functionality:
- ElectricityMap API client
- Boavizta API client  
- AWS Cost Explorer client
- Unified API client integration
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.api_clients.unified_api_client import (
    UnifiedAPIClient,
    ElectricityMapClient,
    BoaviztalClient,
    AWSCostClient,
    CarbonIntensity,
    PowerConsumption,
    AWSCostData
)


class TestElectricityMapClient:
    """Test suite for ElectricityMap API client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = ElectricityMapClient(api_key="test_api_key")

    def test_initialization_with_api_key(self):
        """Test client initialization with API key."""
        assert self.client.api_key == "test_api_key"

    def test_initialization_without_api_key(self):
        """Test client initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            client = ElectricityMapClient()
            assert client.api_key is None

    @patch('requests.get')
    def test_get_carbon_intensity_success(self, mock_get):
        """Test successful carbon intensity retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'carbonIntensity': 350,
            'zone': 'DE',
            'datetime': '2025-01-01T12:00:00.000Z'
        }
        mock_get.return_value = mock_response

        result = self.client.get_carbon_intensity('DE')
        
        assert isinstance(result, CarbonIntensity)
        assert result.value == 350
        assert result.zone == 'DE'
        assert result.source == 'ElectricityMap API'

    @patch('requests.get')
    def test_get_carbon_intensity_api_error(self, mock_get):
        """Test carbon intensity retrieval with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        result = self.client.get_carbon_intensity('DE')
        assert result is None

    @patch('requests.get')
    def test_get_carbon_intensity_network_error(self, mock_get):
        """Test carbon intensity retrieval with network error."""
        mock_get.side_effect = requests.ConnectionError("Network error")
        
        result = self.client.get_carbon_intensity('DE')
        assert result is None

    def test_get_carbon_intensity_no_api_key(self):
        """Test carbon intensity retrieval without API key."""
        client = ElectricityMapClient(api_key=None)
        result = client.get_carbon_intensity('DE')
        assert result is None

    def test_cache_functionality(self):
        """Test carbon intensity caching."""
        with patch('requests.get') as mock_get, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getmtime', return_value=1640995200):  # Recent timestamp
            
            # Mock cached data
            mock_file = Mock()
            mock_file.read.return_value = json.dumps({
                'carbonIntensity': 350,
                'zone': 'DE',
                'cached_at': 1640995200
            })
            mock_open.return_value.__enter__.return_value = mock_file

            result = self.client.get_carbon_intensity('DE')
            
            # Should not call API if cache is fresh
            mock_get.assert_not_called()


class TestBoaviztalClient:
    """Test suite for Boavizta API client."""

    def setup_method(self):
        """Set up test fixtures.""" 
        self.client = BoaviztalClient()

    @patch('requests.post')
    def test_get_power_consumption_success(self, mock_post):
        """Test successful power consumption retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'verbose': {
                'avg_power': {'value': 10.5, 'unit': 'W'},
                'min_power': {'value': 8.0, 'unit': 'W'},
                'max_power': {'value': 13.0, 'unit': 'W'}
            }
        }
        mock_post.return_value = mock_response

        result = self.client.get_power_consumption('t3.small')
        
        assert isinstance(result, PowerConsumption)
        assert result.avg_power_watts == 10.5
        assert result.min_power_watts == 8.0
        assert result.max_power_watts == 13.0
        assert result.instance_type == 't3.small'

    @patch('requests.post')
    def test_get_power_consumption_api_error(self, mock_post):
        """Test power consumption retrieval with API error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Instance type not found"
        mock_post.return_value = mock_response

        result = self.client.get_power_consumption('invalid_type')
        assert result is None

    @patch('requests.post')
    def test_get_power_consumption_malformed_response(self, mock_post):
        """Test power consumption retrieval with malformed response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing expected fields
        mock_post.return_value = mock_response

        result = self.client.get_power_consumption('t3.small')
        assert result is None

    def test_supported_instance_types(self):
        """Test that common AWS instance types are supported."""
        common_types = ['t3.micro', 't3.small', 't3.medium', 'c5.large', 'm5.large']
        
        for instance_type in common_types:
            payload = self.client._build_request_payload(instance_type)
            assert payload is not None
            assert payload['instance_type'] == instance_type
            assert payload['provider'] == 'aws'


class TestAWSCostClient:
    """Test suite for AWS Cost Explorer client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = AWSCostClient(profile_name='test-profile')

    @patch('boto3.Session')
    def test_get_monthly_costs_success(self, mock_session):
        """Test successful monthly cost retrieval."""
        # Mock boto3 client and response
        mock_ce_client = Mock()
        mock_session.return_value.client.return_value = mock_ce_client
        
        mock_response = {
            'ResultsByTime': [
                {
                    'Total': {'UnblendedCost': {'Amount': '123.45', 'Unit': 'USD'}},
                    'Groups': [
                        {
                            'Keys': ['EC2-Instance'],
                            'Metrics': {'UnblendedCost': {'Amount': '100.00', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon S3'],
                            'Metrics': {'UnblendedCost': {'Amount': '23.45', 'Unit': 'USD'}}
                        }
                    ]
                }
            ]
        }
        mock_ce_client.get_cost_and_usage.return_value = mock_response

        result = self.client.get_monthly_costs()
        
        assert isinstance(result, AWSCostData)
        assert result.monthly_cost_usd == 123.45
        assert result.region == self.client.region
        assert len(result.service_costs) == 2
        assert 'EC2-Instance' in result.service_costs
        assert result.service_costs['EC2-Instance'] == 100.00

    @patch('boto3.Session')
    def test_get_monthly_costs_no_data(self, mock_session):
        """Test monthly cost retrieval with no data."""
        mock_ce_client = Mock()
        mock_session.return_value.client.return_value = mock_ce_client
        
        mock_response = {'ResultsByTime': []}
        mock_ce_client.get_cost_and_usage.return_value = mock_response

        result = self.client.get_monthly_costs()
        assert result is None

    @patch('boto3.Session')
    def test_get_monthly_costs_client_error(self, mock_session):
        """Test monthly cost retrieval with AWS client error."""
        from botocore.exceptions import ClientError
        
        mock_ce_client = Mock()
        mock_session.return_value.client.return_value = mock_ce_client
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_ce_client.get_cost_and_usage.side_effect = ClientError(error_response, 'GetCostAndUsage')

        result = self.client.get_monthly_costs()
        assert result is None

    def test_date_range_calculation(self):
        """Test proper date range calculation for monthly costs."""
        start_date, end_date = self.client._get_current_month_date_range()
        
        assert start_date is not None
        assert end_date is not None
        assert start_date < end_date
        assert len(start_date) == 10  # YYYY-MM-DD format
        assert len(end_date) == 10    # YYYY-MM-DD format


class TestUnifiedAPIClient:
    """Test suite for Unified API client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = UnifiedAPIClient(aws_profile='test-profile')

    def test_initialization(self):
        """Test unified client initialization."""
        assert self.client.electricitymap_client is not None
        assert self.client.boavizta_client is not None
        assert self.client.aws_client is not None

    @patch.object(ElectricityMapClient, 'get_carbon_intensity')
    def test_get_carbon_intensity(self, mock_get_carbon):
        """Test carbon intensity retrieval through unified client."""
        # Mock ElectricityMap client response
        mock_carbon = Mock()
        mock_carbon.value = 350
        mock_carbon.zone = 'DE'
        mock_get_carbon.return_value = mock_carbon

        result = self.client.get_carbon_intensity('eu-central-1')
        
        assert result == 350
        mock_get_carbon.assert_called_once_with('DE')

    @patch.object(BoaviztalClient, 'get_power_consumption')
    def test_get_power_consumption(self, mock_get_power):
        """Test power consumption retrieval through unified client."""
        # Mock Boavizta client response
        mock_power = Mock()
        mock_power.avg_power_watts = 10.5
        mock_get_power.return_value = mock_power

        result = self.client.get_power_consumption('t3.small')
        
        assert isinstance(result, PowerConsumption)
        assert result.avg_power_watts == 10.5

    @patch.object(AWSCostClient, 'get_monthly_costs')
    def test_get_aws_costs(self, mock_get_costs):
        """Test AWS cost retrieval through unified client."""
        # Mock AWS client response
        mock_costs = Mock()
        mock_costs.monthly_cost_usd = 123.45
        mock_get_costs.return_value = mock_costs

        result = self.client.get_aws_costs()
        
        assert isinstance(result, AWSCostData)
        assert result.monthly_cost_usd == 123.45

    def test_region_mapping(self):
        """Test AWS region to ElectricityMap zone mapping."""
        test_mappings = {
            'eu-central-1': 'DE',
            'us-east-1': 'US-VA',
            'eu-west-1': 'IE',
            'ap-southeast-1': 'SG'
        }
        
        for aws_region, expected_zone in test_mappings.items():
            zone = self.client._map_aws_region_to_zone(aws_region)
            assert zone == expected_zone

    def test_error_handling_isolation(self):
        """Test that errors in one API don't affect others."""
        with patch.object(ElectricityMapClient, 'get_carbon_intensity', side_effect=Exception("API Error")):
            # ElectricityMap error shouldn't prevent other API calls
            result = self.client.get_carbon_intensity('eu-central-1')
            assert result is None  # Should handle error gracefully


class TestAPIDataModels:
    """Test suite for API data models."""

    def test_carbon_intensity_model(self):
        """Test CarbonIntensity data model."""
        carbon = CarbonIntensity(
            value=350,
            zone='DE',
            timestamp='2025-01-01T12:00:00Z',
            source='ElectricityMap API'
        )
        
        assert carbon.value == 350
        assert carbon.zone == 'DE'
        assert carbon.source == 'ElectricityMap API'

    def test_power_consumption_model(self):
        """Test PowerConsumption data model."""
        power = PowerConsumption(
            instance_type='t3.small',
            avg_power_watts=10.5,
            min_power_watts=8.0,
            max_power_watts=13.0,
            source='Boavizta API',
            confidence_level='high'
        )
        
        assert power.instance_type == 't3.small'
        assert power.avg_power_watts == 10.5
        assert power.confidence_level == 'high'

    def test_aws_cost_data_model(self):
        """Test AWSCostData data model."""
        cost_data = AWSCostData(
            monthly_cost_usd=123.45,
            region='eu-central-1',
            service_costs={'EC2-Instance': 100.00, 'S3': 23.45},
            source='AWS Cost Explorer'
        )
        
        assert cost_data.monthly_cost_usd == 123.45
        assert cost_data.region == 'eu-central-1'
        assert len(cost_data.service_costs) == 2


if __name__ == "__main__":
    # Run tests with pytest if available
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Running basic test execution (pytest not available)")
        
        # Basic test runner
        print("✅ Testing ElectricityMap client...")
        test_em = TestElectricityMapClient()
        test_em.setup_method()
        test_em.test_initialization_with_api_key()
        
        print("✅ Testing Boavizta client...")
        test_boavizta = TestBoaviztalClient()
        test_boavizta.setup_method()
        test_boavizta.test_supported_instance_types()
        
        print("✅ Testing data models...")
        test_models = TestAPIDataModels()
        test_models.test_carbon_intensity_model()
        test_models.test_power_consumption_model()
        test_models.test_aws_cost_data_model()
        
        print("✅ All basic tests passed!")