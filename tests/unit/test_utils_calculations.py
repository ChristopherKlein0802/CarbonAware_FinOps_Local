"""
Unit Tests for Calculation Utils Module
Academic-grade testing for core calculation functions
"""

import unittest
from unittest.mock import patch, MagicMock
from src.utils.calculations import (
    safe_round, calculate_simple_power_consumption,
    calculate_co2_emissions, calculate_monthly_cost,
    calculate_scenario_savings, calculate_confidence_score,
    validate_calculation_inputs
)


class TestSafeRound(unittest.TestCase):
    """Test safe rounding function"""

    def test_safe_round_normal_values(self):
        """Test safe_round with normal float values"""
        self.assertEqual(safe_round(3.14159, 2), 3.14)
        self.assertEqual(safe_round(3.14159, 3), 3.142)
        self.assertEqual(safe_round(10.0, 0), 10.0)

    def test_safe_round_none_value(self):
        """Test safe_round with None input"""
        self.assertIsNone(safe_round(None))
        self.assertIsNone(safe_round(None, 3))

    def test_safe_round_invalid_values(self):
        """Test safe_round with invalid inputs"""
        self.assertIsNone(safe_round("invalid"))
        self.assertIsNone(safe_round([1, 2, 3]))
        self.assertIsNone(safe_round({}))

    def test_safe_round_edge_cases(self):
        """Test safe_round with edge cases"""
        self.assertEqual(safe_round(0.0), 0.0)
        self.assertEqual(safe_round(-3.14159, 2), -3.14)


class TestPowerConsumption(unittest.TestCase):
    """Test power consumption calculation"""

    def test_calculate_simple_power_consumption_normal(self):
        """Test power calculation with normal values"""
        # 100W base with 50% CPU should be 150W
        result = calculate_simple_power_consumption(100.0, 50.0)
        self.assertEqual(result, 150.0)

        # 200W base with 0% CPU should be 200W
        result = calculate_simple_power_consumption(200.0, 0.0)
        self.assertEqual(result, 200.0)

        # 100W base with 100% CPU should be 200W
        result = calculate_simple_power_consumption(100.0, 100.0)
        self.assertEqual(result, 200.0)

    def test_calculate_simple_power_consumption_edge_cases(self):
        """Test power calculation with edge cases"""
        # Negative base power should be clamped to 0.1W
        result = calculate_simple_power_consumption(-10.0, 50.0)
        self.assertAlmostEqual(result, 0.15, places=7)  # 0.1 * 1.5

        # CPU utilization above 100% should be clamped
        result = calculate_simple_power_consumption(100.0, 150.0)
        self.assertEqual(result, 200.0)  # 100 * 2.0

        # Negative CPU utilization should be clamped to 0
        result = calculate_simple_power_consumption(100.0, -50.0)
        self.assertEqual(result, 100.0)  # 100 * 1.0

    @patch('src.utils.calculations.logger')
    def test_calculate_simple_power_consumption_logging(self, mock_logger):
        """Test that power calculation logs debug information"""
        calculate_simple_power_consumption(100.0, 50.0)
        mock_logger.debug.assert_called_once()


class TestCO2Emissions(unittest.TestCase):
    """Test CO2 emissions calculation"""

    def test_calculate_co2_emissions_normal(self):
        """Test CO2 calculation with normal values"""
        # 1000W * 400 g/kWh * 1h = 0.4 kg CO2
        result = calculate_co2_emissions(1000.0, 400.0, 1.0)
        self.assertEqual(result, 0.4)

        # 500W * 300 g/kWh * 24h = 3.6 kg CO2
        result = calculate_co2_emissions(500.0, 300.0, 24.0)
        self.assertEqual(result, 3.6)

    def test_calculate_co2_emissions_zero_values(self):
        """Test CO2 calculation with zero values"""
        self.assertEqual(calculate_co2_emissions(0.0, 400.0, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, 0.0, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, 400.0, 0.0), 0.0)

    def test_calculate_co2_emissions_none_values(self):
        """Test CO2 calculation with None values"""
        self.assertEqual(calculate_co2_emissions(None, 400.0, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, None, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, 400.0, None), 0.0)

    @patch('src.utils.calculations.logger')
    def test_calculate_co2_emissions_logging(self, mock_logger):
        """Test that CO2 calculation logs debug information"""
        calculate_co2_emissions(1000.0, 400.0, 1.0)
        mock_logger.debug.assert_called_once()


class TestMonthlyCost(unittest.TestCase):
    """Test monthly cost calculation"""

    def test_calculate_monthly_cost_normal(self):
        """Test cost calculation with normal values"""
        # $0.10/h * 730h * 0.92 EUR/USD = €67.16
        result = calculate_monthly_cost(0.10, 730.0, 0.92)
        self.assertEqual(result, 67.16)

        # $1.00/h * 365h * 0.92 EUR/USD = €335.8
        result = calculate_monthly_cost(1.00, 365.0, 0.92)
        self.assertEqual(result, 335.8)

    def test_calculate_monthly_cost_zero_values(self):
        """Test cost calculation with zero values"""
        self.assertEqual(calculate_monthly_cost(0.0, 730.0, 0.92), 0.0)
        self.assertEqual(calculate_monthly_cost(0.10, 0.0, 0.92), 0.0)

    def test_calculate_monthly_cost_none_values(self):
        """Test cost calculation with None values"""
        self.assertEqual(calculate_monthly_cost(None, 730.0, 0.92), 0.0)
        self.assertEqual(calculate_monthly_cost(0.10, None, 0.92), 0.0)

    @patch('src.utils.calculations.logger')
    def test_calculate_monthly_cost_logging(self, mock_logger):
        """Test that cost calculation logs debug information"""
        calculate_monthly_cost(0.10, 730.0, 0.92)
        mock_logger.debug.assert_called_once()


class TestScenarioSavings(unittest.TestCase):
    """Test scenario savings calculation"""

    def test_calculate_scenario_savings_normal(self):
        """Test scenario savings calculation"""
        # €1000 * 0.20 = €200 savings
        result = calculate_scenario_savings(1000.0, 0.20)
        self.assertEqual(result, 200.0)

        # €500 * 0.10 = €50 savings
        result = calculate_scenario_savings(500.0, 0.10)
        self.assertEqual(result, 50.0)

    def test_calculate_scenario_savings_edge_cases(self):
        """Test scenario savings with edge cases"""
        # Zero baseline cost
        self.assertEqual(calculate_scenario_savings(0.0, 0.20), 0.0)

        # None baseline cost
        self.assertEqual(calculate_scenario_savings(None, 0.20), 0.0)

        # Zero scenario factor
        self.assertEqual(calculate_scenario_savings(1000.0, 0.0), 0.0)

        # Negative scenario factor
        self.assertEqual(calculate_scenario_savings(1000.0, -0.10), 0.0)


class TestConfidenceScore(unittest.TestCase):
    """Test confidence score calculation"""

    def test_calculate_confidence_score_normal(self):
        """Test confidence score with normal values"""
        # Geometric mean of 0.8, 0.9, 0.7 ≈ 0.796
        result = calculate_confidence_score(0.8, 0.9, 0.7)
        self.assertAlmostEqual(result, 0.796, places=3)

        # Single factor
        result = calculate_confidence_score(0.85)
        self.assertEqual(result, 0.85)

    def test_calculate_confidence_score_edge_cases(self):
        """Test confidence score with edge cases"""
        # No factors
        self.assertEqual(calculate_confidence_score(), 0.0)

        # Zero factors should be filtered out
        result = calculate_confidence_score(0.0, 0.8, 0.9)
        self.assertAlmostEqual(result, 0.849, places=3)

        # All zero factors
        self.assertEqual(calculate_confidence_score(0.0, 0.0), 0.0)


class TestValidationInputs(unittest.TestCase):
    """Test input validation"""

    def test_validate_calculation_inputs_valid(self):
        """Test validation with valid inputs"""
        self.assertTrue(validate_calculation_inputs(
            power_watts=100.0,
            runtime_hours=24.0,
            carbon_intensity=400.0
        ))

    def test_validate_calculation_inputs_invalid(self):
        """Test validation with invalid inputs"""
        # Negative values should fail
        self.assertFalse(validate_calculation_inputs(
            power_watts=-100.0,
            runtime_hours=24.0,
            carbon_intensity=400.0
        ))

        # None values should fail
        self.assertFalse(validate_calculation_inputs(
            power_watts=None,
            runtime_hours=24.0,
            carbon_intensity=400.0
        ))

    def test_validate_calculation_inputs_non_required(self):
        """Test validation ignores non-required fields"""
        self.assertTrue(validate_calculation_inputs(
            other_field="ignored",
            power_watts=100.0,
            runtime_hours=24.0,
            carbon_intensity=400.0
        ))


if __name__ == '__main__':
    unittest.main()