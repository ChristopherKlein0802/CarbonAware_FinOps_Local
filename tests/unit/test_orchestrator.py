"""Tests for src.application.orchestrator module.

Updated for new Use Case architecture after Phase 3 refactoring.
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.application.orchestrator import DashboardDataOrchestrator
from src.domain.models import BusinessCase, CarbonIntensity, EC2Instance, DashboardData
from src.domain.services import RuntimeService, CarbonDataService


class TestDashboardDataOrchestrator(unittest.TestCase):
    """Test cases for the dashboard data orchestrator with Use Case architecture."""

    def setUp(self) -> None:
        # Create mocked services
        runtime_mock = Mock(spec=RuntimeService)
        carbon_mock = Mock(spec=CarbonDataService)

        # Initialize orchestrator with mocked services
        self.processor = DashboardDataOrchestrator(runtime_service=runtime_mock, carbon_service=carbon_mock)

        # Setup mock returns
        self.processor.carbon_service.get_self_collected_history.return_value = []

        # Sample test data
        self.sample_carbon_intensity = CarbonIntensity(
            value=350.0, region="eu-central-1", timestamp=datetime.now(), source="test"
        )
        self.sample_instance = EC2Instance(
            instance_id="i-test123",
            instance_type="t3.medium",
            state="running",
            region="eu-central-1",
            power_watts=15.0,
            cost_eur_average=45.0,
            co2_kg_average=4.5,
            cost_eur_hourly=46.0,
            co2_kg_hourly=4.6,
            period_days=30,
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
        """Test orchestrator initializes with services and use cases."""
        processor = DashboardDataOrchestrator()
        self.assertIsInstance(processor.runtime_service, RuntimeService)
        self.assertIsInstance(processor.carbon_service, CarbonDataService)
        # Verify use cases exist
        self.assertTrue(hasattr(processor, "fetch_use_case"))
        self.assertTrue(hasattr(processor, "health_use_case"))
        self.assertTrue(hasattr(processor, "error_use_case"))

    def test_get_infrastructure_data_success(self) -> None:
        """Test successful data retrieval through use cases."""
        # Mock the fetch use case to return valid dashboard data
        mock_dashboard_data = DashboardData(
            instances=[self.sample_instance],
            carbon_intensity=self.sample_carbon_intensity,
            total_cost_average=45.0,
            total_co2_average=4.5,
            analysis_period_days=30,
            business_case=self.sample_business_case,
            data_freshness=datetime.now(),
            academic_disclaimers=[],
            api_health_status={},
        )

        self.processor.fetch_use_case = Mock()
        self.processor.fetch_use_case.execute.return_value = mock_dashboard_data

        self.processor.health_use_case = Mock()
        self.processor.health_use_case.execute.return_value = {}

        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(len(result.instances), 1)
        self.assertEqual(result.total_cost_average, 45.0)
        self.assertEqual(result.total_co2_average, 4.5)
        self.assertEqual(result.analysis_period_days, 30)
        self.assertEqual(result.business_case, self.sample_business_case)

    def test_get_infrastructure_data_no_carbon_intensity(self) -> None:
        """Test orchestrator handles missing carbon intensity gracefully."""
        # Mock use case returning data without carbon intensity
        mock_dashboard_data = DashboardData(
            instances=[],
            carbon_intensity=None,
            total_cost_average=0.0,
            total_co2_average=0.0,
            analysis_period_days=30,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=["No carbon intensity data available"],
            api_health_status={},
        )

        self.processor.fetch_use_case = Mock()
        self.processor.fetch_use_case.execute.return_value = mock_dashboard_data

        self.processor.health_use_case = Mock()
        self.processor.health_use_case.execute.return_value = {}

        result = self.processor.get_infrastructure_data()

        self.assertIsInstance(result, DashboardData)
        self.assertEqual(result.instances, [])
        self.assertIn("carbon intensity", result.academic_disclaimers[0].lower())

    def test_get_infrastructure_data_no_instances(self) -> None:
        """Test orchestrator handles no instances found."""
        mock_dashboard_data = DashboardData(
            instances=[],
            carbon_intensity=self.sample_carbon_intensity,
            total_cost_average=0.0,
            total_co2_average=0.0,
            analysis_period_days=30,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=["No EC2 instances found"],
            api_health_status={},
        )

        self.processor.fetch_use_case = Mock()
        self.processor.fetch_use_case.execute.return_value = mock_dashboard_data

        self.processor.health_use_case = Mock()
        self.processor.health_use_case.execute.return_value = {}

        result = self.processor.get_infrastructure_data()

        self.assertEqual(result.instances, [])
        self.assertTrue(any("instances" in item.lower() for item in result.academic_disclaimers))

    def test_get_infrastructure_data_processing_failure(self) -> None:
        """Test orchestrator handles processing failures."""
        mock_dashboard_data = DashboardData(
            instances=[],
            carbon_intensity=self.sample_carbon_intensity,
            total_cost_average=0.0,
            total_co2_average=0.0,
            analysis_period_days=30,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=["Module error: Instance processing failed"],
            api_health_status={},
        )

        self.processor.fetch_use_case = Mock()
        self.processor.fetch_use_case.execute.return_value = mock_dashboard_data

        self.processor.health_use_case = Mock()
        self.processor.health_use_case.execute.return_value = {}

        result = self.processor.get_infrastructure_data()

        self.assertTrue(any("error" in item.lower() for item in result.academic_disclaimers))

    def test_error_response_creation(self) -> None:
        """Test error response use case is invoked on ValueError."""
        # Mock fetch use case to raise ValueError
        self.processor.fetch_use_case = Mock()
        self.processor.fetch_use_case.execute.side_effect = ValueError("Test validation error")

        # Mock error use case
        mock_error_response = DashboardData(
            instances=[],
            carbon_intensity=None,
            total_cost_average=0.0,
            total_co2_average=0.0,
            analysis_period_days=30,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=["Validation error: Test validation error"],
            api_health_status={},
        )

        self.processor.error_use_case = Mock()
        self.processor.error_use_case.create_minimal_response.return_value = mock_error_response

        result = self.processor.get_infrastructure_data()

        self.assertEqual(result.instances, [])
        self.assertEqual(result.total_cost_average, 0.0)
        self.assertEqual(result.analysis_period_days, 30)
        self.assertTrue(any("error" in item.lower() for item in result.academic_disclaimers))

    def test_orchestrator_delegates_to_use_cases(self) -> None:
        """Test orchestrator correctly delegates to use cases (thin coordinator pattern)."""
        # Setup mocks
        self.processor.fetch_use_case = Mock()
        self.processor.health_use_case = Mock()

        mock_dashboard_data = DashboardData(
            instances=[],
            carbon_intensity=None,
            total_cost_average=0.0,
            total_co2_average=0.0,
            analysis_period_days=30,
            business_case=None,
            data_freshness=datetime.now(),
            academic_disclaimers=[],
            api_health_status={},
        )

        self.processor.fetch_use_case.execute.return_value = mock_dashboard_data
        self.processor.health_use_case.execute.return_value = {}

        # Call orchestrator
        result = self.processor.get_infrastructure_data()

        # Verify use cases were called
        self.processor.fetch_use_case.execute.assert_called_once()
        self.processor.health_use_case.execute.assert_called_once()

        # Verify orchestrator is thin (just delegates, doesn't do business logic)
        self.assertIsInstance(result, DashboardData)


if __name__ == "__main__":
    unittest.main()
