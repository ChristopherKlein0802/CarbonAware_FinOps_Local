"""
Tests for src.core.calculator module
Testing CarbonCalculator and BusinessCaseCalculator functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from src.core.calculator import CarbonCalculator, BusinessCaseCalculator
from src.models.business import BusinessCase


class TestCarbonCalculator(unittest.TestCase):
    """Test cases for CarbonCalculator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = CarbonCalculator()

    def test_initialization(self):
        """Test CarbonCalculator initialization"""
        calculator = CarbonCalculator()
        self.assertIsInstance(calculator, CarbonCalculator)

    def test_calculate_instance_emissions_normal(self):
        """Test normal CO2 emissions calculation"""
        power_watts = 15.0
        carbon_intensity = 350.0  # g CO2/kWh
        runtime_hours = 720.0  # 30 days

        result = self.calculator.calculate_instance_emissions(power_watts, carbon_intensity, runtime_hours)

        # Expected: (15 * 350 / 1000) * 720 / 1000 = 3.78 kg CO2
        expected = 3.78
        self.assertAlmostEqual(result, expected, places=2)

    def test_calculate_instance_emissions_zero_power(self):
        """Test CO2 calculation with zero power"""
        result = self.calculator.calculate_instance_emissions(0.0, 350.0, 720.0)
        self.assertEqual(result, 0.0)

    def test_calculate_instance_emissions_zero_carbon(self):
        """Test CO2 calculation with zero carbon intensity"""
        result = self.calculator.calculate_instance_emissions(15.0, 0.0, 720.0)
        self.assertEqual(result, 0.0)

    def test_calculate_instance_emissions_zero_runtime(self):
        """Test CO2 calculation with zero runtime"""
        result = self.calculator.calculate_instance_emissions(15.0, 350.0, 0.0)
        self.assertEqual(result, 0.0)

    def test_calculate_instance_emissions_high_values(self):
        """Test CO2 calculation with high values"""
        power_watts = 100.0
        carbon_intensity = 600.0
        runtime_hours = 8760.0  # Full year

        result = self.calculator.calculate_instance_emissions(power_watts, carbon_intensity, runtime_hours)

        # Expected: (100 * 600 / 1000) * 8760 / 1000 = 525.6 kg CO2
        expected = 525.6
        self.assertAlmostEqual(result, expected, places=1)


class TestBusinessCaseCalculator(unittest.TestCase):
    """Test cases for BusinessCaseCalculator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = BusinessCaseCalculator()

    def test_initialization(self):
        """Test BusinessCaseCalculator initialization"""
        calculator = BusinessCaseCalculator()
        self.assertIsInstance(calculator, BusinessCaseCalculator)

    def test_calculate_business_case_normal(self):
        """Test normal business case calculation"""
        baseline_cost = 100.0
        baseline_co2 = 10.0
        validation_factor = 1.0

        result = self.calculator.calculate_business_case(baseline_cost, baseline_co2, validation_factor)

        self.assertIsInstance(result, BusinessCase)
        self.assertEqual(result.baseline_cost_eur, 100.0)
        self.assertEqual(result.baseline_co2_kg, 10.0)

        # Check scenario calculations (10% and 20%)
        self.assertEqual(result.office_hours_savings_eur, 10.0)  # 10% of 100
        self.assertEqual(result.carbon_aware_savings_eur, 20.0)  # 20% of 100
        self.assertEqual(result.integrated_savings_eur, 20.0)    # Using scenario B

        self.assertEqual(result.office_hours_co2_reduction_kg, 1.0)  # 10% of 10
        self.assertEqual(result.carbon_aware_co2_reduction_kg, 2.0)  # 20% of 10
        self.assertEqual(result.integrated_co2_reduction_kg, 2.0)    # Using scenario B

    def test_calculate_business_case_zero_baseline(self):
        """Test business case with zero baseline values"""
        result = self.calculator.calculate_business_case(0.0, 0.0, 1.0)

        self.assertIsInstance(result, BusinessCase)
        self.assertEqual(result.baseline_cost_eur, 0.0)
        self.assertEqual(result.baseline_co2_kg, 0.0)
        self.assertEqual(result.office_hours_savings_eur, 0.0)
        self.assertEqual(result.carbon_aware_savings_eur, 0.0)

    def test_calculate_business_case_high_validation_factor(self):
        """Test business case with high validation factor"""
        result = self.calculator.calculate_business_case(100.0, 10.0, 2.0)

        # Validation factor should be included in validation_status
        self.assertIn("2.00", result.validation_status)

    def test_calculate_scenario_savings_normal(self):
        """Test scenario savings calculation"""
        baseline_cost = 100.0
        scenario_factor = 0.15  # 15%

        result = self.calculator.calculate_scenario_savings(baseline_cost, scenario_factor)

        self.assertEqual(result, 15.0)

    def test_calculate_scenario_savings_zero(self):
        """Test scenario savings with zero baseline"""
        result = self.calculator.calculate_scenario_savings(0.0, 0.15)
        self.assertEqual(result, 0.0)

    def test_calculate_cloudtrail_enhanced_accuracy_no_cost_data(self):
        """Test accuracy calculation without cost data"""
        instances = []
        calculated_cost = 100.0

        result = self.calculator.calculate_cloudtrail_enhanced_accuracy(instances, calculated_cost, None)

        self.assertEqual(result, 1.0)  # Default validation factor

    def test_calculate_cloudtrail_enhanced_accuracy_zero_calculated_cost(self):
        """Test accuracy calculation with zero calculated cost"""
        instances = []
        cost_data = Mock()
        cost_data.monthly_cost_usd = 100.0

        result = self.calculator.calculate_cloudtrail_enhanced_accuracy(instances, 0.0, cost_data)

        self.assertEqual(result, 1.0)  # Default validation factor

    def test_calculate_cloudtrail_enhanced_accuracy_normal(self):
        """Test normal accuracy calculation"""
        # Mock instances
        instances = [
            Mock(state="running"),
            Mock(state="running"),
            Mock(state="stopped")
        ]

        # Mock cost data
        cost_data = Mock()
        cost_data.monthly_cost_usd = 92.0  # Will be converted to EUR: 92 * 0.92 = 84.64

        calculated_cost_eur = 100.0

        result = self.calculator.calculate_cloudtrail_enhanced_accuracy(instances, calculated_cost_eur, cost_data)

        # Expected: 84.64 / 100.0 = 0.8464
        self.assertAlmostEqual(result, 0.8464, places=3)

    def test_calculate_cloudtrail_enhanced_accuracy_mostly_running(self):
        """Test accuracy calculation with mostly running instances"""
        instances = [Mock(state="running")] * 4 + [Mock(state="stopped")] * 1

        cost_data = Mock()
        cost_data.monthly_cost_usd = 110.0  # EUR: 110 * 0.92 = 101.2

        calculated_cost_eur = 100.0

        result = self.calculator.calculate_cloudtrail_enhanced_accuracy(instances, calculated_cost_eur, cost_data)

        # Should return validation factor: 101.2 / 100.0 = 1.012
        self.assertAlmostEqual(result, 1.012, places=3)

    def test_calculate_cloudtrail_enhanced_accuracy_mostly_stopped(self):
        """Test accuracy calculation with mostly stopped instances"""
        instances = [Mock(state="stopped")] * 4 + [Mock(state="running")] * 1

        cost_data = Mock()
        cost_data.monthly_cost_usd = 50.0  # EUR: 50 * 0.92 = 46.0

        calculated_cost_eur = 100.0

        result = self.calculator.calculate_cloudtrail_enhanced_accuracy(instances, calculated_cost_eur, cost_data)

        # Should return validation factor: 46.0 / 100.0 = 0.46
        self.assertAlmostEqual(result, 0.46, places=2)

    def test_calculate_cloudtrail_enhanced_accuracy_empty_instances(self):
        """Test accuracy calculation with empty instances list"""
        instances = []
        cost_data = Mock()
        cost_data.monthly_cost_usd = 100.0

        result = self.calculator.calculate_cloudtrail_enhanced_accuracy(instances, 100.0, cost_data)

        self.assertEqual(result, 1.0)  # Default when no instances

    def test_business_case_confidence_assessment(self):
        """Test confidence assessment in business case"""
        result = self.calculator.calculate_business_case(100.0, 10.0, 1.0)

        # Check that confidence interval is set
        self.assertEqual(result.confidence_interval, 0.15)

        # Check methodology field contains expected content
        self.assertIn("INTEGRATION_EXCELLENCE", result.methodology)

        # Check validation status contains validation information
        self.assertIn("validation factor", result.validation_status)

    def test_business_case_calculation_precision(self):
        """Test precision of business case calculations with safe_round"""
        baseline_cost = 123.456789
        baseline_co2 = 12.3456789

        result = self.calculator.calculate_business_case(baseline_cost, baseline_co2, 1.0)

        # Check that values are properly rounded (approximately)
        self.assertAlmostEqual(result.office_hours_savings_eur, 12.35, places=1)  # 10% of 123.46
        self.assertAlmostEqual(result.carbon_aware_savings_eur, 24.69, places=1)  # 20% of 123.46
        self.assertAlmostEqual(result.office_hours_co2_reduction_kg, 1.235, places=2)  # 10% of 12.346


if __name__ == '__main__':
    unittest.main()