"""Tests for carbon API client (ElectricityMap only)."""

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
        assert intensity.source == 'electricitymap'
    
    @patch('requests.get')
    def test_electricitymap_client(self, mock_get):
        """Test ElectricityMap API client."""
        # Mock response for current intensity
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
        assert intensity.region == 'eu-central-1'
        
        # Verify API was called correctly
        mock_get.assert_called_with(
            'https://api.electricitymap.org/v3/carbon-intensity/latest',
            headers={'auth-token': 'test-key'},
            params={'zone': 'DE'},
            timeout=30
        )
    
    def test_electricitymap_fallback(self):
        """Test ElectricityMap fallback when no API key."""
        client = ElectricityMapClient(api_key=None)
        
        # Should use fallback
        intensity = client.get_current_intensity('eu-central-1')
        assert intensity.value == 358  # Germany fallback (current ElectricityMap)
        assert intensity.source == 'fallback'
    
    @patch.dict('os.environ', {'CARBON_API_PROVIDER': 'electricitymap'})
    @patch('src.carbon.carbon_api_client.ElectricityMapClient')
    def test_carbon_intensity_client(self, mock_client_class):
        """Test main carbon intensity client."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock the get_current_intensity method
        mock_intensity = CarbonIntensity(
            value=350.0,
            timestamp=datetime.now(),
            region='eu-central-1',
            source='electricitymap'
        )
        mock_client.get_current_intensity.return_value = mock_intensity
        
        client = CarbonIntensityClient()
        assert client.client == mock_client
        
        # Test get_current_intensity
        value = client.get_current_intensity('eu-central-1')
        assert value == 350.0
    
    def test_region_mappings(self):
        """Test that region mappings work."""
        client = ElectricityMapClient(api_key='test')
        
        # Test common AWS regions have mappings
        test_regions = ['eu-central-1', 'eu-west-1', 'us-east-1']
        
        for region in test_regions:
            # Should return fallback (not raise exception)
            intensity = client._get_fallback_intensity(region)
            assert intensity.value > 0
            assert intensity.region == region
    
    def test_error_handling(self):
        """Test error handling and fallbacks."""
        # Test with no API keys
        client = CarbonIntensityClient(provider='electricitymap')
        
        # Should not raise exception, should use fallback
        value = client.get_current_intensity('eu-central-1')
        assert value > 0  # Should return fallback value