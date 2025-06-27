"""Tests for carbon API client."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.carbon.carbon_api_client import (
    CarbonIntensity, 
    ElectricityMapClient,
    CarbonIntensityClient
)

class TestCarbonAPIClient:
    """Test carbon API client functionality."""
    
    def test_carbon_intensity_dataclass(self):
        """Test CarbonIntensity dataclass."""
        intensity = CarbonIntensity(
            value=450.5,
            timestamp=datetime.now(),
            region='eu-central-1',
            source='electricitymap'
        )
        assert intensity.value == 450.5
        assert intensity.region == 'eu-central-1'
    
    @patch('requests.get')
    def test_electricitymap_client(self, mock_get):
        """Test ElectricityMap API client."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'carbonIntensity': 350.0,
            'datetime': '2024-01-01T12:00:00Z'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Test client
        client = ElectricityMapClient(api_key='test-key')
        intensity = client.get_current_intensity('eu-central-1')
        
        assert intensity.value == 350.0
        assert intensity.source == 'electricitymap'
    
    @patch.dict('os.environ', {'CARBON_API_PROVIDER': 'electricitymap'})
    @patch('src.carbon.carbon_api_client.ElectricityMapClient')
    def test_carbon_intensity_client(self, mock_client_class):
        """Test main carbon intensity client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        client = CarbonIntensityClient()
        assert client.client == mock_client