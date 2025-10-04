"""
Unit Tests for Calculation Utils Module
Academic-grade testing for core calculation functions
"""

import unittest
from unittest.mock import patch
from src.utils.calculations import (
    safe_round,
    calculate_simple_power_consumption,
    calculate_co2_emissions,
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
        # 100W base with 50% CPU: 100 × (0.3 + 0.7 × 0.5) = 65W
        result = calculate_simple_power_consumption(100.0, 50.0)
        self.assertAlmostEqual(result, 65.0, places=10)  # Use assertAlmostEqual for floating point comparison

        # 200W base with 0% CPU: 200 × (0.3 + 0.7 × 0) = 60W
        result = calculate_simple_power_consumption(200.0, 0.0)
        self.assertEqual(result, 60.0)

        # 100W base with 100% CPU: 100 × (0.3 + 0.7 × 1) = 100W
        result = calculate_simple_power_consumption(100.0, 100.0)
        self.assertEqual(result, 100.0)

    def test_calculate_simple_power_consumption_edge_cases(self):
        """Test power calculation with edge cases"""
        # Negative base power should be clamped to 0.1W: 0.1 × (0.3 + 0.7 × 0.5) = 0.065W
        result = calculate_simple_power_consumption(-10.0, 50.0)
        self.assertAlmostEqual(result, 0.065, places=7)

        # CPU utilization above 100% should be clamped: 100 × (0.3 + 0.7 × 1) = 100W
        result = calculate_simple_power_consumption(100.0, 150.0)
        self.assertEqual(result, 100.0)

        # Negative CPU utilization should be clamped to 0: 100 × (0.3 + 0.7 × 0) = 30W
        result = calculate_simple_power_consumption(100.0, -50.0)
        self.assertEqual(result, 30.0)

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


if __name__ == '__main__':
    unittest.main()
