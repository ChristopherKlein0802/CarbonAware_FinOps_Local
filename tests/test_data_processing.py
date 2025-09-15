#!/usr/bin/env python3
"""
Unit Tests for Data Processing Module
Carbon-Aware FinOps Dashboard - Bachelor Thesis

Tests core data processing functionality:
- Infrastructure data aggregation
- Carbon calculation algorithms
- Cost optimization logic
- Academic validation methods
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.data_processing import DataProcessor


class TestDataProcessor:
    """Test suite for DataProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()

    def test_initialization(self):
        """Test DataProcessor initialization."""
        assert self.processor is not None
        assert hasattr(self.processor, 'ACADEMIC_CONSTANTS')
        assert 'EUR_USD_RATE' in self.processor.ACADEMIC_CONSTANTS
        assert 'EU_ETS_PRICE_PER_TONNE' in self.processor.ACADEMIC_CONSTANTS

    def test_academic_constants(self):
        """Test academic constants are reasonable."""
        constants = self.processor.ACADEMIC_CONSTANTS
        
        # EUR/USD rate should be reasonable
        assert 0.8 <= constants['EUR_USD_RATE'] <= 1.2
        
        # EU ETS price should be in reasonable range
        assert 30 <= constants['EU_ETS_PRICE_PER_TONNE'] <= 100

    @patch('dashboard.utils.data_processing.DataProcessor._fetch_from_unified_api')
    def test_get_infrastructure_data_success(self, mock_fetch):
        """Test successful infrastructure data retrieval."""
        # Mock API response
        mock_fetch.return_value = {
            'instances': [
                {
                    'instance_id': 'i-123456789',
                    'instance_type': 't3.small',
                    'state': 'running',
                    'monthly_cost': 15.50,
                    'power_watts': 10.5,
                    'carbon_intensity': 350
                }
            ],
            'carbon_intensity': 350,
            'total_cost': 15.50,
            'api_sources': {
                'electricitymap': 'success',
                'boavizta': 'success',
                'aws': 'success'
            }
        }
        
        result = self.processor.get_infrastructure_data()
        
        assert result is not None
        assert 'instances' in result
        assert 'carbon_intensity' in result
        assert len(result['instances']) == 1
        assert result['instances'][0]['instance_type'] == 't3.small'

    @patch('dashboard.utils.data_processing.DataProcessor._fetch_from_unified_api')
    def test_get_infrastructure_data_api_failure(self, mock_fetch):
        """Test infrastructure data retrieval when API fails."""
        mock_fetch.return_value = None
        
        result = self.processor.get_infrastructure_data()
        
        # Should return default structure with empty data
        assert result is not None
        assert result['instances'] == []
        assert result['carbon_intensity'] == 420  # Default fallback
        assert result['total_cost'] == 0

    def test_calculate_carbon_emissions(self):
        """Test carbon emissions calculation."""
        # Test data
        power_watts = 100
        carbon_intensity = 300  # g CO2/kWh
        hours_per_month = 730
        
        result = self.processor._calculate_carbon_emissions(
            power_watts, carbon_intensity, hours_per_month
        )
        
        # Expected: 100W * 0.001 kW * 730h * 300g/kWh = 21.9 kg CO2/month
        expected = 21.9
        assert abs(result - expected) < 0.1

    def test_calculate_carbon_emissions_edge_cases(self):
        """Test carbon emissions calculation edge cases."""
        # Zero power
        result = self.processor._calculate_carbon_emissions(0, 300, 730)
        assert result == 0.0
        
        # Zero carbon intensity
        result = self.processor._calculate_carbon_emissions(100, 0, 730)
        assert result == 0.0
        
        # Zero hours
        result = self.processor._calculate_carbon_emissions(100, 300, 0)
        assert result == 0.0

    def test_calculate_optimization_potential(self):
        """Test optimization potential calculation."""
        instance_data = {
            'instance_type': 't3.medium',
            'monthly_cost': 20.0,
            'power_watts': 15.0,
            'carbon_emissions_kg': 10.0,
            'carbon_intensity': 350
        }
        
        result = self.processor._calculate_optimization_potential(instance_data)
        
        assert result is not None
        assert 'cost_savings_percent' in result
        assert 'carbon_savings_percent' in result
        assert 'optimization_score' in result
        
        # Savings should be positive percentages
        assert 0 <= result['cost_savings_percent'] <= 50
        assert 0 <= result['carbon_savings_percent'] <= 50

    def test_generate_business_case_metrics(self):
        """Test business case metrics generation."""
        instances_data = [
            {
                'instance_type': 't3.small',
                'monthly_cost': 15.0,
                'carbon_emissions_kg': 8.0,
                'optimization': {
                    'cost_savings_percent': 20,
                    'carbon_savings_percent': 35
                }
            },
            {
                'instance_type': 't3.medium', 
                'monthly_cost': 25.0,
                'carbon_emissions_kg': 12.0,
                'optimization': {
                    'cost_savings_percent': 15,
                    'carbon_savings_percent': 30
                }
            }
        ]
        
        result = self.processor._generate_business_case_metrics(instances_data)
        
        assert result is not None
        assert 'monthly_cost_savings' in result
        assert 'monthly_carbon_savings_kg' in result
        assert 'annual_roi_percent' in result
        assert 'payback_months' in result
        
        # Check calculations make sense
        assert result['monthly_cost_savings'] > 0
        assert result['monthly_carbon_savings_kg'] > 0
        assert result['annual_roi_percent'] > 0

    def test_validate_api_response(self):
        """Test API response validation."""
        # Valid response
        valid_response = {
            'carbon_intensity': 350,
            'instances': [{'instance_id': 'i-123'}],
            'total_cost': 100.0
        }
        assert self.processor._validate_api_response(valid_response)
        
        # Invalid responses
        assert not self.processor._validate_api_response(None)
        assert not self.processor._validate_api_response({})
        assert not self.processor._validate_api_response({'carbon_intensity': 'invalid'})

    def test_confidence_intervals_calculation(self):
        """Test confidence intervals for academic rigor."""
        test_data = [100, 110, 95, 105, 120, 90, 115, 108, 102, 98]
        
        result = self.processor._calculate_confidence_intervals(test_data, confidence=0.95)
        
        assert result is not None
        assert 'mean' in result
        assert 'lower_bound' in result
        assert 'upper_bound' in result
        assert 'confidence_level' in result
        
        # Check bounds make sense
        assert result['lower_bound'] <= result['mean'] <= result['upper_bound']
        assert result['confidence_level'] == 0.95

    @patch('dashboard.utils.data_processing.DataProcessor._fetch_from_unified_api')
    def test_get_infrastructure_data_performance(self, mock_fetch):
        """Test infrastructure data retrieval performance."""
        # Mock fast API response
        mock_fetch.return_value = {
            'instances': [],
            'carbon_intensity': 350,
            'total_cost': 0,
            'api_sources': {}
        }
        
        start_time = datetime.now()
        result = self.processor.get_infrastructure_data()
        end_time = datetime.now()
        
        # Should complete quickly (< 1 second for mocked data)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0
        assert result is not None

    def test_error_handling_graceful_degradation(self):
        """Test graceful degradation when errors occur."""
        with patch('dashboard.utils.data_processing.logger') as mock_logger:
            # Simulate API client initialization failure
            with patch('dashboard.utils.data_processing.UnifiedAPIClient') as mock_client:
                mock_client.side_effect = Exception("API initialization failed")
                
                processor = DataProcessor()
                result = processor.get_infrastructure_data()
                
                # Should still return valid structure
                assert result is not None
                assert 'instances' in result
                assert result['instances'] == []


class TestDataProcessorIntegration:
    """Integration tests for DataProcessor with mocked external dependencies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()

    @patch('dashboard.utils.data_processing.UnifiedAPIClient')
    def test_full_data_processing_pipeline(self, mock_client_class):
        """Test complete data processing pipeline."""
        # Mock unified API client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock API responses
        mock_client.get_carbon_intensity.return_value = 350
        mock_client.get_aws_instances.return_value = [
            {
                'instance_id': 'i-123456789',
                'instance_type': 't3.small',
                'state': 'running',
                'monthly_cost': 15.50
            }
        ]
        mock_client.get_power_consumption.return_value = Mock(
            avg_power_watts=10.5,
            min_power_watts=8.0,
            max_power_watts=13.0,
            source='Boavizta API',
            confidence_level='high'
        )
        
        result = self.processor.get_infrastructure_data()
        
        # Verify complete pipeline execution
        assert result is not None
        assert len(result['instances']) > 0
        
        instance = result['instances'][0]
        assert 'carbon_emissions_kg' in instance
        assert 'optimization' in instance
        assert instance['carbon_emissions_kg'] > 0

    def test_academic_validation_requirements(self):
        """Test that all academic validation requirements are met."""
        # Verify academic constants are documented
        constants = self.processor.ACADEMIC_CONSTANTS
        assert isinstance(constants, dict)
        
        # Verify uncertainty handling
        test_data = [100, 105, 95, 110, 90]
        confidence_result = self.processor._calculate_confidence_intervals(test_data)
        assert confidence_result['confidence_level'] == 0.95
        
        # Verify no fallback dummy data policy
        with patch.object(self.processor, '_fetch_from_unified_api', return_value=None):
            result = self.processor.get_infrastructure_data()
            assert result['instances'] == []  # Empty, not dummy data


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise basic execution
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Running basic test execution (pytest not available)")
        
        # Basic test runner
        test_class = TestDataProcessor()
        test_class.setup_method()
        
        print("✅ Testing DataProcessor initialization...")
        test_class.test_initialization()
        
        print("✅ Testing academic constants...")
        test_class.test_academic_constants()
        
        print("✅ Testing carbon emissions calculation...")
        test_class.test_calculate_carbon_emissions()
        
        print("✅ All basic tests passed!")