"""
Tests for src.core.processor module
Testing DataProcessor integration and orchestration functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.core.processor import DataProcessor
from src.models.dashboard import DashboardData
from src.models.carbon import CarbonIntensity
from src.models.aws import EC2Instance
from src.models.business import BusinessCase


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = DataProcessor()
        self.processor._load_time_series = Mock(return_value=[])
        self.processor._save_time_series = Mock()
        self.processor._build_time_series = Mock(return_value=([], None, None))

        # Sample carbon intensity
        self.sample_carbon_intensity = CarbonIntensity(
            value=350.0,
            region="eu-central-1",
            timestamp=datetime.now(),
            source="test"
        )

        # Sample EC2 instance
        self.sample_instance = EC2Instance(
            instance_id="i-test123",
            instance_type="t3.medium",
            state="running",
            region="eu-central-1",
            power_watts=15.0,
            monthly_cost_eur=45.0,
            monthly_co2_kg=4.5,
            confidence_level="high",
            data_sources=["test"],
            last_updated=datetime.now()
        )

        # Sample business case
        self.sample_business_case = BusinessCase(
            baseline_cost_eur=100.0,
            baseline_co2_kg=10.0,
            office_hours_savings_eur=10.0,
            carbon_aware_savings_eur=20.0,
            integrated_savings_eur=20.0,
            office_hours_co2_reduction_kg=1.0,
            carbon_aware_co2_reduction_kg=2.0,
            integrated_co2_reduction_kg=2.0,
            confidence_interval=0.15,
            methodology="Test methodology",
            validation_status="Test validation"
        )

    def test_initialization(self):
        """Test DataProcessor initialization"""
        processor = DataProcessor()
        self.assertIsInstance(processor, DataProcessor)

        # Check that components are initialized
        self.assertIsNotNone(processor.runtime_tracker)
        self.assertIsNotNone(processor.carbon_calculator)
        self.assertIsNotNone(processor.business_calculator)

    def test_initialization_methodology_achievements(self):
        """Test that methodology achievements are properly defined"""
        self.assertIn("DATA_INTEGRATION", self.processor.METHODOLOGY_ACHIEVEMENTS)
        self.assertIn("CLOUDTRAIL_INNOVATION", self.processor.METHODOLOGY_ACHIEVEMENTS)
        self.assertIn("REGIONAL_SPECIALIZATION", self.processor.METHODOLOGY_ACHIEVEMENTS)

        # Check data integration achievement
        data_integration = self.processor.METHODOLOGY_ACHIEVEMENTS["DATA_INTEGRATION"]
        self.assertIn("5-API orchestration", data_integration["description"])
        self.assertEqual(len(data_integration["apis"]), 5)

    def test_initialization_academic_constants(self):
        """Test that academic constants are properly defined"""
        self.assertIn("cloudtrail_precision", self.processor.ACADEMIC_CONSTANTS)
        self.assertIn("carbon_uncertainty", self.processor.ACADEMIC_CONSTANTS)
        self.assertIn("cost_uncertainty", self.processor.ACADEMIC_CONSTANTS)

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_success(self, mock_api_client):
        """Test successful infrastructure data retrieval"""
        # Mock API responses
        mock_api_client.get_current_carbon_intensity.return_value = self.sample_carbon_intensity
        mock_api_client.get_monthly_costs.return_value = Mock(monthly_cost_usd=100.0)
        mock_api_client.get_carbon_intensity_24h.return_value = []
        mock_api_client.get_hourly_costs.return_value = []

        # Mock tracker responses
        mock_instances_data = [{"instance_id": "i-test123", "instance_type": "t3.medium", "state": "running", "region": "eu-central-1"}]
        with patch.object(self.processor.runtime_tracker, 'get_all_ec2_instances', return_value=mock_instances_data):
            with patch.object(self.processor.runtime_tracker, 'process_instance_enhanced', return_value=self.sample_instance):
                with patch.object(self.processor.business_calculator, 'calculate_cloudtrail_enhanced_accuracy', return_value=1.0):
                    with patch.object(self.processor.business_calculator, 'calculate_business_case', return_value=self.sample_business_case):
                        # Health monitoring simplified after cleanup

                        result = self.processor.get_infrastructure_data()

        # Assertions
        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 1)
        self.assertEqual(result.instances[0].instance_id, "i-test123")
        self.assertEqual(result.carbon_intensity.value, 350.0)
        self.assertEqual(result.total_cost_eur, 45.0)
        self.assertEqual(result.total_co2_kg, 4.5)
        self.assertIsInstance(result.business_case, BusinessCase)
        self.processor._build_time_series.assert_called_once()
        self.assertEqual(result.time_series, [])
        self.assertIsNone(result.tac_score)
        self.assertEqual(result.cost_mape, 0.0)

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_no_carbon_intensity(self, mock_api_client):
        """Test infrastructure data retrieval without carbon intensity"""
        mock_api_client.get_current_carbon_intensity.return_value = None
        # Health monitoring simplified after cleanup
        mock_api_client.get_hourly_costs.return_value = []

        # Mock EC2 to avoid real AWS calls
        with patch.object(self.processor.runtime_tracker, 'get_all_ec2_instances', return_value=[]):
            result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 0)
        self.assertEqual(result.total_cost_eur, 0.0)
        self.assertEqual(result.total_co2_kg, 0.0)
        self.assertIn("No carbon data available", result.academic_disclaimers[0])

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_no_instances(self, mock_api_client):
        """Test infrastructure data retrieval without EC2 instances"""
        mock_api_client.get_current_carbon_intensity.return_value = self.sample_carbon_intensity
        # Health monitoring simplified after cleanup
        mock_api_client.get_hourly_costs.return_value = []

        with patch.object(self.processor.runtime_tracker, 'get_all_ec2_instances', return_value=[]):
            result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 0)
        self.assertEqual(result.carbon_intensity.value, 350.0)  # Carbon data preserved
        self.assertTrue(any("No instances found" in disclaimer for disclaimer in result.academic_disclaimers))

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_no_processable_instances(self, mock_api_client):
        """Test infrastructure data retrieval when instances can't be processed"""
        mock_api_client.get_current_carbon_intensity.return_value = self.sample_carbon_intensity
        # Health monitoring simplified after cleanup
        mock_api_client.get_hourly_costs.return_value = []

        mock_instances_data = [{"instance_id": "i-test123", "instance_type": "t3.medium", "state": "running", "region": "eu-central-1"}]
        with patch.object(self.processor.runtime_tracker, 'get_all_ec2_instances', return_value=mock_instances_data):
            with patch.object(self.processor.runtime_tracker, 'process_instance_enhanced', return_value=None):  # Processing fails
                result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 0)
        self.assertTrue(any("Instance processing failed" in disclaimer for disclaimer in result.academic_disclaimers))

    def test_create_empty_response(self):
        """Test empty response creation"""
        error_message = "Test error"
        result = self.processor._create_empty_response(error_message)

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 0)
        self.assertEqual(result.total_cost_eur, 0.0)
        self.assertEqual(result.total_co2_kg, 0.0)
        self.assertIsNone(result.carbon_intensity)
        self.assertIsNone(result.business_case)
        self.assertIn(error_message, result.academic_disclaimers)
        self.assertTrue(any("Academic integrity maintained" in disclaimer for disclaimer in result.academic_disclaimers))
        self.assertEqual(result.time_series, [])
        self.assertIsNone(result.tac_score)

    # Health monitoring removed after cleanup
    def test_create_minimal_response(self):
        """Test minimal response creation with carbon data"""
        # Health monitoring simplified after cleanup
        error_message = "Test minimal error"

        result = self.processor._create_minimal_response(self.sample_carbon_intensity, error_message)

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 0)
        self.assertEqual(result.total_cost_eur, 0.0)
        self.assertEqual(result.carbon_intensity.value, 350.0)
        self.assertIn(error_message, result.academic_disclaimers)
        self.assertTrue(any("preserving available API data" in disclaimer for disclaimer in result.academic_disclaimers))
        self.assertEqual(result.time_series, [])

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_value_error(self, mock_api_client):
        """Test infrastructure data retrieval with ValueError"""
        mock_api_client.get_current_carbon_intensity.side_effect = ValueError("Test error")
        # Health monitoring simplified after cleanup

        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertTrue(any("Data validation error:" in disclaimer for disclaimer in result.academic_disclaimers))

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_attribute_error(self, mock_api_client):
        """Test infrastructure data retrieval with AttributeError"""
        mock_api_client.get_current_carbon_intensity.side_effect = AttributeError("Test error")
        # Health monitoring simplified after cleanup

        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertTrue(any("Module error:" in disclaimer for disclaimer in result.academic_disclaimers))

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_get_infrastructure_data_connection_error(self, mock_api_client):
        """Test infrastructure data retrieval with ConnectionError"""
        mock_api_client.get_current_carbon_intensity.side_effect = ConnectionError("Test error")
        # Health monitoring simplified after cleanup

        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertTrue(any("Network error:" in disclaimer for disclaimer in result.academic_disclaimers))

    # Health monitoring removed after cleanup
    @patch('src.core.processor.unified_api_client')
    def test_totals_calculation(self, mock_api_client):
        """Test totals calculation with multiple instances"""
        # Setup multiple instances
        instance1 = EC2Instance(
            instance_id="i-test1",
            instance_type="t3.small",
            state="running",
            region="eu-central-1",
            power_watts=10.0,
            monthly_cost_eur=30.0,
            monthly_co2_kg=3.0,
            confidence_level="high",
            data_sources=["test"],
            last_updated=datetime.now()
        )

        instance2 = EC2Instance(
            instance_id="i-test2",
            instance_type="t3.medium",
            state="running",
            region="eu-central-1",
            power_watts=15.0,
            monthly_cost_eur=45.0,
            monthly_co2_kg=4.5,
            confidence_level="high",
            data_sources=["test"],
            last_updated=datetime.now()
        )

        # Mock API responses
        mock_api_client.get_current_carbon_intensity.return_value = self.sample_carbon_intensity
        mock_api_client.get_monthly_costs.return_value = Mock(monthly_cost_usd=100.0)

        mock_instances_data = [
            {"instance_id": "i-test1", "instance_type": "t3.small", "state": "running", "region": "eu-central-1"},
            {"instance_id": "i-test2", "instance_type": "t3.medium", "state": "running", "region": "eu-central-1"}
        ]

        with patch.object(self.processor.runtime_tracker, 'get_all_ec2_instances', return_value=mock_instances_data):
            with patch.object(self.processor.runtime_tracker, 'process_instance_enhanced', side_effect=[instance1, instance2]):
                with patch.object(self.processor.business_calculator, 'calculate_cloudtrail_enhanced_accuracy', return_value=1.0):
                    with patch.object(self.processor.business_calculator, 'calculate_business_case', return_value=self.sample_business_case):
                        # Health monitoring simplified after cleanup

                        result = self.processor.get_infrastructure_data()

        # Check totals
        self.assertEqual(result.total_cost_eur, 75.0)  # 30 + 45
        self.assertEqual(result.total_co2_kg, 7.5)     # 3.0 + 4.5

    def test_academic_constants_accessibility(self):
        """Test that academic constants are accessible and complete"""
        constants = self.processor.ACADEMIC_CONSTANTS

        # Check all required constants exist
        required_constants = [
            "cloudtrail_precision",
            "carbon_uncertainty",
            "cost_uncertainty",
            "methodology"
        ]

        for constant in required_constants:
            self.assertIn(constant, constants)
            self.assertIsInstance(constants[constant], str)

    def test_methodology_achievements_structure(self):
        """Test methodology achievements structure"""
        achievements = self.processor.METHODOLOGY_ACHIEVEMENTS

        # Check main categories
        self.assertIn("DATA_INTEGRATION", achievements)
        self.assertIn("CLOUDTRAIL_INNOVATION", achievements)
        self.assertIn("REGIONAL_SPECIALIZATION", achievements)

        # Check data integration structure
        data_integration = achievements["DATA_INTEGRATION"]
        self.assertIn("description", data_integration)
        self.assertIn("apis", data_integration)
        self.assertIn("evidence_level", data_integration)
        self.assertEqual(data_integration["evidence_level"], "IMPLEMENTED")


if __name__ == '__main__':
    unittest.main()
