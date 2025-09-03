"""Tests for carbon API client."""

from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.carbon.carbon_api_client import (
    CarbonIntensity, 
    ElectricityMapClient,
    WattTimeClient,
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
    
    @patch('requests.get')
    def test_electricitymap_forecast(self, mock_get):
        """Test ElectricityMap forecast functionality."""
        # Mock response for forecast
        mock_response = Mock()
        mock_response.json.return_value = {
            'forecast': [
                {'carbonIntensity': 300.0, 'datetime': '2024-01-01T12:00:00Z'},
                {'carbonIntensity': 320.0, 'datetime': '2024-01-01T13:00:00Z'},
                {'carbonIntensity': 310.0, 'datetime': '2024-01-01T14:00:00Z'},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ElectricityMapClient(api_key='test-key')
        forecasts = client.get_forecast('eu-central-1', hours=3)
        
        assert len(forecasts) == 3
        assert forecasts[0].value == 300.0
        assert forecasts[1].value == 320.0
        assert forecasts[2].value == 310.0
        assert all(f.source == 'electricitymap' for f in forecasts)
    
    def test_electricitymap_fallback(self):
        """Test ElectricityMap fallback when no API key."""
        client = ElectricityMapClient(api_key=None)
        
        # Should use fallback
        intensity = client.get_current_intensity('eu-central-1')
        assert intensity.value == 380  # Germany fallback
        assert intensity.source == 'fallback'
        
        # Test forecast fallback
        forecasts = client.get_forecast('eu-central-1', hours=24)
        assert len(forecasts) == 24
        assert all(f.source == 'fallback_forecast' for f in forecasts)
    
    @patch('requests.get')
    def test_watttime_client(self, mock_get):
        """Test WattTime API client."""
        # Mock authentication
        auth_response = Mock()
        auth_response.json.return_value = {'token': 'test-token'}
        auth_response.raise_for_status = Mock()
        
        # Mock data response
        data_response = Mock()
        data_response.json.return_value = {
            'value': 400.0,
            'point_time': '2024-01-01T12:00:00Z'
        }
        data_response.raise_for_status = Mock()
        
        # Setup mock to return different responses
        mock_get.side_effect = [auth_response, data_response]
        
        # Test client
        client = WattTimeClient(username='test', password='pass')
        assert client.token == 'test-token'
        
        intensity = client.get_current_intensity('eu-central-1')
        assert intensity.value == 400.0
        assert intensity.source == 'watttime'
    
    @patch('requests.get')
    def test_watttime_forecast(self, mock_get):
        """Test WattTime forecast functionality."""
        # Mock authentication
        auth_response = Mock()
        auth_response.json.return_value = {'token': 'test-token'}
        auth_response.raise_for_status = Mock()
        
        # Mock forecast response
        forecast_response = Mock()
        forecast_response.json.return_value = {
            'data': [
                {'value': 380.0, 'point_time': '2024-01-01T12:00:00Z'},
                {'value': 390.0, 'point_time': '2024-01-01T13:00:00Z'},
            ]
        }
        forecast_response.raise_for_status = Mock()
        
        mock_get.side_effect = [auth_response, forecast_response]
        
        client = WattTimeClient(username='test', password='pass')
        forecasts = client.get_forecast('eu-central-1', hours=2)
        
        assert len(forecasts) == 2
        assert forecasts[0].value == 380.0
        assert forecasts[1].value == 390.0
    
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
    
    @patch.dict('os.environ', {'CARBON_API_PROVIDER': 'electricitymap'})
    def test_carbon_client_best_hours(self):
        """Test getting best hours for running workloads."""
        with patch('src.carbon.carbon_api_client.ElectricityMapClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Create mock forecast data
            mock_forecasts = [
                CarbonIntensity(value=400, timestamp=datetime.now(), region='eu-central-1', source='mock'),
                CarbonIntensity(value=200, timestamp=datetime.now() + timedelta(hours=1), region='eu-central-1', source='mock'),
                CarbonIntensity(value=500, timestamp=datetime.now() + timedelta(hours=2), region='eu-central-1', source='mock'),
                CarbonIntensity(value=150, timestamp=datetime.now() + timedelta(hours=3), region='eu-central-1', source='mock'),
            ]
            mock_client.get_forecast.return_value = mock_forecasts
            
            client = CarbonIntensityClient()
            best_hours = client.get_best_hours('eu-central-1', hours_needed=2, forecast_hours=4)
            
            # Should return hours 3 and 1 (lowest values: 150 and 200)
            assert best_hours == [1, 3]
    
    @patch.dict('os.environ', {'CARBON_API_PROVIDER': 'electricitymap'})
    def test_carbon_client_should_run(self):
        """Test checking if should run based on threshold."""
        with patch('src.carbon.carbon_api_client.ElectricityMapClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Test below threshold
            mock_client.get_current_intensity.return_value = CarbonIntensity(
                value=350, timestamp=datetime.now(), region='eu-central-1', source='mock'
            )
            
            client = CarbonIntensityClient()
            assert client.should_run_now('eu-central-1', threshold=400) == True
            
            # Test above threshold
            mock_client.get_current_intensity.return_value = CarbonIntensity(
                value=450, timestamp=datetime.now(), region='eu-central-1', source='mock'
            )
            assert client.should_run_now('eu-central-1', threshold=400) == False
    
    def test_region_mappings(self):
        """Test that region mappings are consistent."""
        # Check ElectricityMap mappings
        em_client = ElectricityMapClient(api_key='test')
        
        # Test common AWS regions have mappings
        test_regions = ['eu-central-1', 'eu-west-1', 'us-east-1', 'us-west-2']
        
        for region in test_regions:
            # Should return fallback (not raise exception)
            intensity = em_client._get_fallback_intensity(region)
            assert intensity.value > 0
            assert intensity.region == region
    
    def test_error_handling(self):
        """Test error handling and fallbacks."""
        # Test with no API keys
        client = CarbonIntensityClient(provider='electricitymap')
        
        # Should not raise exception, should use fallback
        value = client.get_current_intensity('eu-central-1')
        assert value > 0  # Should return fallback value
        
        # Test forecast fallback
        forecast = client.get_forecast('eu-central-1', hours=24)
        assert len(forecast) == 24
        assert all(v > 0 for v in forecast)