"""
Tests for src.core.calculator module
Testing BusinessCaseCalculator functionality
"""

import unittest
from unittest.mock import Mock

from src.application.calculator import BusinessCaseCalculator
from src.domain.models import BusinessCase


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

        # Check scenario calculations (dynamic based on validation factor)
        # For validation_factor=1.0, baseline_cost=100: factors = 0.1 * 0.8 * 0.8 = 6.4% and 0.2 * 0.8 * 0.8 = 12.8%
        self.assertAlmostEqual(result.office_hours_savings_eur, 6.4, places=2)
        self.assertAlmostEqual(result.carbon_aware_savings_eur, 12.8, places=2)
        self.assertAlmostEqual(result.integrated_savings_eur, 12.8, places=2)

        self.assertAlmostEqual(result.office_hours_co2_reduction_kg, 0.64, places=2)
        self.assertAlmostEqual(result.carbon_aware_co2_reduction_kg, 1.28, places=2)
        self.assertAlmostEqual(result.integrated_co2_reduction_kg, 1.28, places=2)
        self.assertIsNotNone(result.source_notes)

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
        instances = [Mock(state="running"), Mock(state="running"), Mock(state="stopped")]

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
        # For validation_factor=1.0, baseline_cost=123.456789: scenario factors = 0.088 and 0.176
        self.assertAlmostEqual(result.office_hours_savings_eur, 10.864, places=3)
        self.assertAlmostEqual(result.carbon_aware_savings_eur, 21.728, places=3)
        self.assertAlmostEqual(result.office_hours_co2_reduction_kg, 1.086, places=3)


if __name__ == "__main__":
    unittest.main()
