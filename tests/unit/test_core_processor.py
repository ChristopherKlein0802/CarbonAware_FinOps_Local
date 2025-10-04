"""Tests for src.core.processor module."""

import unittest
from unittest.mock import Mock
from datetime import datetime

from src.core.processor import DataProcessor
from src.models.business import BusinessCase
from src.models.carbon import CarbonIntensity
from src.models.aws import EC2Instance
from src.models.dashboard import DashboardData
from src.services import RuntimeService, CarbonDataService, BusinessInsightsService


class TestDataProcessor(unittest.TestCase):
    """Test cases for the high-level data processor."""

    def setUp(self) -> None:
        runtime_mock = Mock(spec=RuntimeService)
        carbon_mock = Mock(spec=CarbonDataService)
        business_mock = Mock(spec=BusinessInsightsService)
        self.processor = DataProcessor(
            runtime_service=runtime_mock,
            carbon_service=carbon_mock,
            business_service=business_mock,
        )
        # Replace domain services with mocks to avoid external calls
        self.processor.runtime_service = runtime_mock
        self.processor.carbon_service = carbon_mock
        self.processor.business_service = business_mock
        self.processor.carbon_service.get_self_collected_history.return_value = []
        self.processor.gateway = Mock()

        self.sample_carbon_intensity = CarbonIntensity(
            value=350.0,
            region="eu-central-1",
            timestamp=datetime.now(),
            source="test",
        )
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
            last_updated=datetime.now(),
        )
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
            validation_status="Test validation",
        )

    def test_initialization(self) -> None:
        processor = DataProcessor()
        self.assertIsInstance(processor.runtime_service, RuntimeService)
        self.assertIsInstance(processor.business_service, BusinessInsightsService)
        self.assertIsInstance(processor.carbon_service, CarbonDataService)

    def test_get_infrastructure_data_success(self) -> None:
        # API facade mocks
        self.processor.gateway.get_monthly_costs.return_value = Mock(monthly_cost_usd=100.0)
        self.processor.gateway.get_hourly_costs.return_value = []

        # Service mocks
        self.processor.carbon_service.get_current_intensity.return_value = self.sample_carbon_intensity
        self.processor.carbon_service.get_recent_history.return_value = []
        self.processor.carbon_service.build_time_series.return_value = ([], None, None)
        self.processor.carbon_service.get_cached_time_series.return_value = []

        self.processor.runtime_service.list_instances.return_value = [
            {
                "instance_id": "i-test123",
                "instance_type": "t3.medium",
                "state": "running",
                "region": "eu-central-1",
            }
        ]
        self.processor.runtime_service.enrich_instance.return_value = self.sample_instance

        self.processor.business_service.validate_costs.return_value = (1.0, "GOOD")
        self.processor.business_service.calculate_business_case.return_value = self.sample_business_case

        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 1)
        self.assertEqual(result.total_cost_eur, 45.0)
        self.assertEqual(result.total_co2_kg, 4.5)
        self.assertEqual(result.business_case, self.sample_business_case)

    def test_get_infrastructure_data_no_carbon_intensity(self) -> None:
        self.processor.carbon_service.get_current_intensity.return_value = None
        self.processor.carbon_service.get_cached_time_series.return_value = []
        self.processor.runtime_service.list_instances.return_value = []

        self.processor.gateway.get_hourly_costs.return_value = []
        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(result.instances, [])
        self.assertIn("No carbon data available", result.academic_disclaimers[0])

    def test_get_infrastructure_data_no_instances(self) -> None:
        self.processor.gateway.get_monthly_costs.return_value = Mock(monthly_cost_usd=100.0)
        self.processor.gateway.get_hourly_costs.return_value = []

        self.processor.carbon_service.get_current_intensity.return_value = self.sample_carbon_intensity
        self.processor.carbon_service.get_recent_history.return_value = []
        self.processor.carbon_service.get_cached_time_series.return_value = []
        self.processor.runtime_service.list_instances.return_value = []

        result = self.processor.get_infrastructure_data()
        self.assertEqual(result.instances, [])
        self.assertTrue(any("No instances found" in item for item in result.academic_disclaimers))

    def test_get_infrastructure_data_processing_failure(self) -> None:
        self.processor.gateway.get_monthly_costs.return_value = Mock(monthly_cost_usd=100.0)
        self.processor.gateway.get_hourly_costs.return_value = []

        self.processor.carbon_service.get_current_intensity.return_value = self.sample_carbon_intensity
        self.processor.carbon_service.get_recent_history.return_value = []
        self.processor.carbon_service.get_cached_time_series.return_value = []
        self.processor.runtime_service.list_instances.return_value = [
            {
                "instance_id": "i-test123",
                "instance_type": "t3.medium",
                "state": "running",
                "region": "eu-central-1",
            }
        ]
        self.processor.runtime_service.enrich_instance.return_value = None

        result = self.processor.get_infrastructure_data()
        self.assertTrue(any("Instance processing failed" in item for item in result.academic_disclaimers))

    def test_create_empty_response(self) -> None:
        result = self.processor._create_empty_response("Test error")
        self.assertEqual(result.instances, [])
        self.assertEqual(result.total_cost_eur, 0.0)
        self.assertEqual(result.academic_disclaimers[0], "Test error")


if __name__ == '__main__':
    unittest.main()
