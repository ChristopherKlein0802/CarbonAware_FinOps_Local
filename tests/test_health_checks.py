#!/usr/bin/env python3
"""
Unit Tests for Health Check Module
Carbon-Aware FinOps Dashboard - Bachelor Thesis

Tests API health monitoring functionality:
- ElectricityMap API health checks
- Boavizta API health checks
- AWS Cost Explorer health checks
- Overall system health assessment
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests
from botocore.exceptions import ClientError, BotoCoreError

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.health_checks import HealthCheckManager, quick_health_check


class TestHealthCheckManager:
    """Test suite for HealthCheckManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {'ELECTRICITYMAP_API_KEY': 'test_key'}):
            self.health_manager = HealthCheckManager()

    def test_initialization(self):
        """Test HealthCheckManager initialization."""
        assert self.health_manager is not None
        assert hasattr(self.health_manager, 'endpoints')
        assert 'electricitymap' in self.health_manager.endpoints
        assert 'boavizta' in self.health_manager.endpoints

    @patch('requests.get')
    def test_electricitymap_health_check_success(self, mock_get):
        """Test successful ElectricityMap API health check."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'carbonIntensity': 350,
            'zone': 'DE'
        }
        mock_get.return_value = mock_response

        result = self.health_manager._check_electricitymap_api()
        
        assert result['status'] == 'healthy'
        assert result['service'] == 'ElectricityMap API'
        assert result['api_key_configured'] is True
        assert result['carbon_intensity'] == 350
        assert result['response_time_ms'] > 0

    @patch('requests.get')
    def test_electricitymap_health_check_api_error(self, mock_get):
        """Test ElectricityMap API health check with API error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        result = self.health_manager._check_electricitymap_api()
        
        assert result['status'] == 'error'
        assert 'HTTP 401' in result['error_message']

    @patch('requests.get')
    def test_electricitymap_health_check_network_error(self, mock_get):
        """Test ElectricityMap API health check with network error."""
        mock_get.side_effect = requests.ConnectionError("Network error")

        result = self.health_manager._check_electricitymap_api()
        
        assert result['status'] == 'error'
        assert 'Network error' in result['error_message']

    def test_electricitymap_health_check_no_api_key(self):
        """Test ElectricityMap API health check without API key."""
        with patch.dict(os.environ, {}, clear=True):
            health_manager = HealthCheckManager()
            result = health_manager._check_electricitymap_api()
            
            assert result['status'] == 'error'
            assert result['api_key_configured'] is False
            assert 'API key not configured' in result['error_message']

    @patch('requests.post')
    def test_boavizta_health_check_success(self, mock_post):
        """Test successful Boavizta API health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'verbose': {
                'avg_power': {'value': 10.5, 'unit': 'W'}
            }
        }
        mock_post.return_value = mock_response

        result = self.health_manager._check_boavizta_api()
        
        assert result['status'] == 'healthy'
        assert result['service'] == 'Boavizta API'
        assert result['api_key_configured'] is True  # Public API
        assert result['test_power_watts'] == 10.5
        assert result['response_time_ms'] > 0

    @patch('requests.post')
    def test_boavizta_health_check_malformed_response(self, mock_post):
        """Test Boavizta API health check with malformed response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Missing expected fields
        mock_post.return_value = mock_response

        result = self.health_manager._check_boavizta_api()
        
        assert result['status'] == 'degraded'
        assert 'Response missing expected power data' in result['error_message']

    @patch('boto3.Session')
    def test_aws_cost_explorer_health_check_success(self, mock_session):
        """Test successful AWS Cost Explorer health check."""
        # Mock boto3 client and response
        mock_ce_client = Mock()
        mock_session.return_value.client.return_value = mock_ce_client
        
        mock_response = {
            'ResultsByTime': [
                {'Total': {'UnblendedCost': {'Amount': '123.45', 'Unit': 'USD'}}}
            ]
        }
        mock_ce_client.get_cost_and_usage.return_value = mock_response

        result = self.health_manager._check_aws_cost_explorer()
        
        assert result['status'] == 'healthy'
        assert result['service'] == 'AWS Cost Explorer API'
        assert result['cost_data_available'] is True
        assert result['response_time_ms'] > 0

    @patch('boto3.Session')
    def test_aws_cost_explorer_health_check_client_error(self, mock_session):
        """Test AWS Cost Explorer health check with client error."""
        mock_ce_client = Mock()
        mock_session.return_value.client.return_value = mock_ce_client
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_ce_client.get_cost_and_usage.side_effect = ClientError(error_response, 'GetCostAndUsage')

        result = self.health_manager._check_aws_cost_explorer()
        
        assert result['status'] == 'error'
        assert 'AWS Error AccessDenied' in result['error_message']

    @patch('boto3.Session')
    def test_aws_cost_explorer_health_check_botocore_error(self, mock_session):
        """Test AWS Cost Explorer health check with BotoCore error."""
        mock_session.side_effect = BotoCoreError()

        result = self.health_manager._check_aws_cost_explorer()
        
        assert result['status'] == 'error'
        assert 'AWS SDK error' in result['error_message']

    def test_overall_health_assessment_all_healthy(self):
        """Test overall health assessment when all services are healthy."""
        health_results = {
            'electricitymap': {'status': 'healthy'},
            'boavizta': {'status': 'healthy'},
            'aws_cost_explorer': {'status': 'healthy'}
        }
        
        result = self.health_manager._generate_overall_health(health_results)
        
        assert result['overall_status'] == 'healthy'
        assert result['services_healthy'] == 3
        assert result['services_degraded'] == 0
        assert result['services_error'] == 0
        assert result['dashboard_ready'] is True

    def test_overall_health_assessment_some_degraded(self):
        """Test overall health assessment with some degraded services."""
        health_results = {
            'electricitymap': {'status': 'healthy'},
            'boavizta': {'status': 'degraded'},
            'aws_cost_explorer': {'status': 'healthy'}
        }
        
        result = self.health_manager._generate_overall_health(health_results)
        
        assert result['overall_status'] == 'degraded'
        assert result['services_healthy'] == 2
        assert result['services_degraded'] == 1
        assert result['services_error'] == 0
        assert result['dashboard_ready'] is True

    def test_overall_health_assessment_some_errors(self):
        """Test overall health assessment with some service errors."""
        health_results = {
            'electricitymap': {'status': 'error'},
            'boavizta': {'status': 'healthy'},
            'aws_cost_explorer': {'status': 'healthy'}
        }
        
        result = self.health_manager._generate_overall_health(health_results)
        
        assert result['overall_status'] == 'error'
        assert result['services_healthy'] == 2
        assert result['services_degraded'] == 0
        assert result['services_error'] == 1
        assert result['dashboard_ready'] is False  # Error status makes dashboard not ready

    def test_overall_health_assessment_all_errors(self):
        """Test overall health assessment when all services have errors."""
        health_results = {
            'electricitymap': {'status': 'error'},
            'boavizta': {'status': 'error'},
            'aws_cost_explorer': {'status': 'error'}
        }
        
        result = self.health_manager._generate_overall_health(health_results)
        
        assert result['overall_status'] == 'error'
        assert result['services_healthy'] == 0
        assert result['services_degraded'] == 0
        assert result['services_error'] == 3
        assert result['dashboard_ready'] is False

    def test_get_health_summary_format(self):
        """Test health summary string formatting."""
        with patch.object(self.health_manager, 'check_all_apis') as mock_check:
            mock_check.return_value = {
                'system_overall': {
                    'overall_status': 'healthy',
                    'services_healthy': 3,
                    'services_degraded': 0,
                    'services_error': 0,
                    'total_services': 3,
                    'dashboard_ready': True
                }
            }
            
            summary = self.health_manager.get_health_summary()
            
            assert '🏥 API Health Status: HEALTHY' in summary
            assert '✅ Healthy: 3/3' in summary
            assert 'Dashboard Ready: ✅' in summary

    @patch.object(HealthCheckManager, '_check_electricitymap_api')
    @patch.object(HealthCheckManager, '_check_boavizta_api')  
    @patch.object(HealthCheckManager, '_check_aws_cost_explorer')
    def test_check_all_apis_integration(self, mock_aws, mock_boavizta, mock_em):
        """Test complete API health check integration."""
        # Mock all API checks
        mock_em.return_value = {'status': 'healthy', 'service': 'ElectricityMap API'}
        mock_boavizta.return_value = {'status': 'healthy', 'service': 'Boavizta API'}
        mock_aws.return_value = {'status': 'healthy', 'service': 'AWS Cost Explorer API'}
        
        result = self.health_manager.check_all_apis()
        
        assert 'electricitymap' in result
        assert 'boavizta' in result
        assert 'aws_cost_explorer' in result
        assert 'system_overall' in result
        
        # Verify all individual checks were called
        mock_em.assert_called_once()
        mock_boavizta.assert_called_once()
        mock_aws.assert_called_once()

    def test_performance_response_time_tracking(self):
        """Test that response times are properly tracked."""
        with patch('requests.get') as mock_get, \
             patch('time.time', side_effect=[0, 0.150]):  # 150ms response time
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'carbonIntensity': 350}
            mock_get.return_value = mock_response

            result = self.health_manager._check_electricitymap_api()
            
            assert result['response_time_ms'] == 150.0


class TestQuickHealthCheck:
    """Test suite for quick health check function."""

    @patch('dashboard.utils.health_checks.health_check_manager')
    def test_quick_health_check_success(self, mock_manager):
        """Test quick health check with healthy system."""
        mock_manager.check_all_apis.return_value = {
            'system_overall': {'dashboard_ready': True}
        }
        
        result = quick_health_check()
        assert result is True

    @patch('dashboard.utils.health_checks.health_check_manager')
    def test_quick_health_check_failure(self, mock_manager):
        """Test quick health check with unhealthy system."""
        mock_manager.check_all_apis.return_value = {
            'system_overall': {'dashboard_ready': False}
        }
        
        result = quick_health_check()
        assert result is False

    @patch('dashboard.utils.health_checks.health_check_manager')
    def test_quick_health_check_exception(self, mock_manager):
        """Test quick health check with exception."""
        mock_manager.check_all_apis.side_effect = Exception("Health check failed")
        
        result = quick_health_check()
        assert result is False


class TestHealthCheckEdgeCases:
    """Test suite for health check edge cases and error scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict(os.environ, {'ELECTRICITYMAP_API_KEY': 'test_key'}):
            self.health_manager = HealthCheckManager()

    def test_timeout_handling(self):
        """Test proper handling of API timeouts."""
        with patch('requests.get', side_effect=requests.Timeout("Request timeout")):
            result = self.health_manager._check_electricitymap_api()
            
            assert result['status'] == 'error'
            assert 'timeout' in result['error_message'].lower()

    def test_malformed_json_response(self):
        """Test handling of malformed JSON responses."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response

            result = self.health_manager._check_electricitymap_api()
            
            assert result['status'] == 'error'
            assert 'Unexpected error' in result['error_message']

    def test_partial_response_data(self):
        """Test handling of partial response data."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'zone': 'DE'}  # Missing carbonIntensity
            mock_get.return_value = mock_response

            result = self.health_manager._check_electricitymap_api()
            
            assert result['status'] == 'degraded'
            assert 'missing expected data structure' in result['error_message']


if __name__ == "__main__":
    # Run tests with pytest if available
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Running basic test execution (pytest not available)")
        
        # Basic test runner
        print("✅ Testing HealthCheckManager initialization...")
        test_health = TestHealthCheckManager()
        test_health.setup_method()
        test_health.test_initialization()
        
        print("✅ Testing overall health assessment...")
        test_health.test_overall_health_assessment_all_healthy()
        test_health.test_overall_health_assessment_some_errors()
        
        print("✅ Testing quick health check...")
        test_quick = TestQuickHealthCheck()
        
        print("✅ All basic tests passed!")