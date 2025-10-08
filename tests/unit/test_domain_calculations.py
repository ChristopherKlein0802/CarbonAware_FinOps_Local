"""
Unit Tests for Domain Calculations Module

Tests mathematical correctness of core calculation functions.
"""

import unittest
from unittest.mock import patch
from src.domain.calculations import (
    safe_round,
    calculate_simple_power_consumption,
    calculate_co2_emissions,
)


class TestSafeRound(unittest.TestCase):
    """Test safe_round utility function"""

    def test_safe_round_normal_values(self):
        """Test safe_round with normal float values"""
        self.assertEqual(safe_round(3.14159, 2), 3.14)
        self.assertEqual(safe_round(3.14159, 3), 3.142)
        self.assertEqual(safe_round(10.0, 0), 10.0)
        self.assertEqual(safe_round(2.5, 0), 2.0)  # Python's banker's rounding

    def test_safe_round_none_value(self):
        """Test safe_round with None input (critical for optional fields)"""
        self.assertIsNone(safe_round(None))
        self.assertIsNone(safe_round(None, 3))
        self.assertIsNone(safe_round(None, 0))

    def test_safe_round_invalid_values(self):
        """Test safe_round gracefully handles invalid inputs"""
        self.assertIsNone(safe_round("invalid"))
        self.assertIsNone(safe_round([1, 2, 3]))
        self.assertIsNone(safe_round({}))
        self.assertIsNone(safe_round(object()))

    def test_safe_round_edge_cases(self):
        """Test safe_round with mathematical edge cases"""
        self.assertEqual(safe_round(0.0), 0.0)
        self.assertEqual(safe_round(-3.14159, 2), -3.14)
        self.assertEqual(safe_round(0.999, 2), 1.0)
        self.assertEqual(safe_round(0.001, 2), 0.0)

    def test_safe_round_large_numbers(self):
        """Test safe_round with large numbers (cost/emissions scenarios)"""
        self.assertEqual(safe_round(12345.6789, 2), 12345.68)
        self.assertEqual(safe_round(999999.99, 0), 1000000.0)

    def test_safe_round_scientific_notation(self):
        """Test safe_round with scientific notation inputs"""
        self.assertEqual(safe_round(1.23e-5, 7), 0.0000123)
        self.assertEqual(safe_round(1.23e5, 2), 123000.0)


class TestPowerConsumption(unittest.TestCase):
    """Test calculate_simple_power_consumption function"""

    def test_power_calculation_idle_state(self):
        """Test power at 0% CPU (idle state) - should be 30% of base"""
        # 100W base at 0% CPU = 30W (idle power)
        result = calculate_simple_power_consumption(100.0, 0.0)
        self.assertEqual(result, 30.0)

        # 200W base at 0% CPU = 60W (idle power)
        result = calculate_simple_power_consumption(200.0, 0.0)
        self.assertEqual(result, 60.0)

    def test_power_calculation_peak_state(self):
        """Test power at 100% CPU (peak state) - should equal base power"""
        # 100W base at 100% CPU = 100W (peak power)
        result = calculate_simple_power_consumption(100.0, 100.0)
        self.assertEqual(result, 100.0)

        # 150W base at 100% CPU = 150W (peak power)
        result = calculate_simple_power_consumption(150.0, 100.0)
        self.assertEqual(result, 150.0)

    def test_power_calculation_mid_utilization(self):
        """Test power at 50% CPU - should be 65% of base"""
        # 100W base at 50% CPU: 100 × (0.3 + 0.7 × 0.5) = 65W
        result = calculate_simple_power_consumption(100.0, 50.0)
        self.assertAlmostEqual(result, 65.0, places=10)

        # 200W base at 50% CPU = 130W
        result = calculate_simple_power_consumption(200.0, 50.0)
        self.assertAlmostEqual(result, 130.0, places=10)

    def test_power_calculation_realistic_scenarios(self):
        """Test power with realistic cloud instance scenarios"""
        # t3.medium baseline: ~15W base, 25% CPU
        result = calculate_simple_power_consumption(15.0, 25.0)
        self.assertAlmostEqual(result, 7.125, places=3)  # 15 × (0.3 + 0.7 × 0.25)

        # m5.large: ~50W base, 75% CPU
        result = calculate_simple_power_consumption(50.0, 75.0)
        self.assertAlmostEqual(result, 41.25, places=2)  # 50 × (0.3 + 0.7 × 0.75)

    def test_power_negative_base_power_clamped(self):
        """Test negative base power is clamped to 0.1W (safety)"""
        # Negative base power should be clamped to 0.1W minimum
        result = calculate_simple_power_consumption(-10.0, 50.0)
        self.assertAlmostEqual(result, 0.065, places=7)  # 0.1 × (0.3 + 0.7 × 0.5)

        result = calculate_simple_power_consumption(0.0, 50.0)
        self.assertAlmostEqual(result, 0.065, places=7)

    def test_power_cpu_above_100_clamped(self):
        """Test CPU utilization above 100% is clamped (data validation)"""
        # CPU > 100% should be clamped to 100%
        result = calculate_simple_power_consumption(100.0, 150.0)
        self.assertEqual(result, 100.0)

        result = calculate_simple_power_consumption(100.0, 200.0)
        self.assertEqual(result, 100.0)

    def test_power_negative_cpu_clamped(self):
        """Test negative CPU utilization is clamped to 0%"""
        # Negative CPU should be clamped to 0%
        result = calculate_simple_power_consumption(100.0, -50.0)
        self.assertEqual(result, 30.0)  # Same as 0% CPU

        result = calculate_simple_power_consumption(100.0, -100.0)
        self.assertEqual(result, 30.0)

    def test_power_calculation_precision(self):
        """Test calculation maintains adequate precision for thesis metrics"""
        # Test decimal precision for accurate carbon calculations
        result = calculate_simple_power_consumption(15.7, 37.3)
        expected = 15.7 * (0.3 + 0.7 * 0.373)
        self.assertAlmostEqual(result, expected, places=8)

    @patch("src.domain.calculations.logger")
    def test_power_calculation_logging(self, mock_logger):
        """Test that power calculation logs debug information"""
        calculate_simple_power_consumption(100.0, 50.0)
        mock_logger.debug.assert_called_once()
        # Verify log message contains key calculation details
        call_args = mock_logger.debug.call_args[0][0]
        self.assertIn("Power calculation", call_args)


class TestCO2Emissions(unittest.TestCase):
    """
    Test calculate_co2_emissions function

    Academic validation: Tests IEA-compliant CO2 calculation
    Formula: CO2(kg) = Power(kW) × Intensity(g/kWh) × Runtime(h) / 1000

    Sources: IEA methodology, EPA guidelines, Carbonfund.org standards
    """

    def test_co2_calculation_basic_validation(self):
        """Test CO2 calculation with academically validated examples"""
        # Example 1: 1000W × 400g/kWh × 1h = 0.4kg CO2
        result = calculate_co2_emissions(1000.0, 400.0, 1.0)
        self.assertEqual(result, 0.4)

        # Example 2: 500W × 300g/kWh × 24h = 3.6kg CO2 (daily)
        result = calculate_co2_emissions(500.0, 300.0, 24.0)
        self.assertEqual(result, 3.6)

    def test_co2_calculation_monthly_footprint(self):
        """Test CO2 calculation for monthly footprints (730h)"""
        # t3.medium monthly: 15W × 350g/kWh × 730h = 3.8325kg CO2
        result = calculate_co2_emissions(15.0, 350.0, 730.0)
        self.assertAlmostEqual(result, 3.833, places=3)

        # m5.large monthly: 50W × 350g/kWh × 730h = 12.775kg CO2
        result = calculate_co2_emissions(50.0, 350.0, 730.0)
        self.assertAlmostEqual(result, 12.775, places=3)

    def test_co2_german_grid_scenarios(self):
        """Test CO2 with realistic German grid intensities"""
        # Optimal (renewable-heavy): 200g/kWh
        result = calculate_co2_emissions(100.0, 200.0, 730.0)
        self.assertAlmostEqual(result, 14.6, places=1)

        # Moderate (mixed): 350g/kWh
        result = calculate_co2_emissions(100.0, 350.0, 730.0)
        self.assertAlmostEqual(result, 25.55, places=2)

        # High (coal-dominant): 450g/kWh
        result = calculate_co2_emissions(100.0, 450.0, 730.0)
        self.assertAlmostEqual(result, 32.85, places=2)

    def test_co2_zero_values_return_zero(self):
        """Test CO2 calculation with zero inputs returns zero"""
        self.assertEqual(calculate_co2_emissions(0.0, 400.0, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, 0.0, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, 400.0, 0.0), 0.0)

    def test_co2_none_values_return_zero(self):
        """Test CO2 calculation with None inputs returns zero (data availability)"""
        self.assertEqual(calculate_co2_emissions(None, 400.0, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, None, 1.0), 0.0)
        self.assertEqual(calculate_co2_emissions(1000.0, 400.0, None), 0.0)
        self.assertEqual(calculate_co2_emissions(None, None, None), 0.0)

    def test_co2_unit_conversion_accuracy(self):
        """Test unit conversions are mathematically correct"""
        # Detailed unit test: 100W = 0.1kW
        # 0.1kW × 300g/kWh × 10h = 300g = 0.3kg
        result = calculate_co2_emissions(100.0, 300.0, 10.0)
        self.assertEqual(result, 0.3)

        # Test precision: 1W × 1g/kWh × 1h = 0.001g = 0.000001kg
        # Note: Function rounds to 3 decimals, so tiny values become 0.0
        result = calculate_co2_emissions(1.0, 1.0, 1.0)
        self.assertEqual(result, 0.0)  # Rounds to 0 (below 3 decimal precision)

        # Test with measurable precision: 100W × 100g/kWh × 1h = 0.01kg
        result = calculate_co2_emissions(100.0, 100.0, 1.0)
        self.assertEqual(result, 0.01)

    def test_co2_rounding_behavior(self):
        """Test CO2 results are rounded to 3 decimal places (kg precision)"""
        # Result should be rounded to 3 decimals via safe_round
        result = calculate_co2_emissions(123.456, 234.567, 12.345)
        self.assertIsInstance(result, float)
        # Verify it's rounded (check it's not the raw calculation)
        raw_result = (123.456 / 1000) * 234.567 * 12.345 / 1000
        self.assertNotEqual(result, raw_result)

    def test_co2_large_scale_scenarios(self):
        """Test CO2 calculation for large-scale cloud deployments"""
        # 100 instances × 50W = 5000W, 350g/kWh, 730h = 1277.5kg CO2/month
        result = calculate_co2_emissions(5000.0, 350.0, 730.0)
        self.assertAlmostEqual(result, 1277.5, places=1)

    @patch("src.domain.calculations.logger")
    def test_co2_calculation_logging(self, mock_logger):
        """Test that CO2 calculation logs debug information"""
        calculate_co2_emissions(1000.0, 400.0, 1.0)
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        self.assertIn("CO2 calculation", call_args)

    def test_co2_inverse_calculation_validation(self):
        """Test CO2 calculation is reversible (validation check)"""
        # If we know CO2, we should be able to reverse-calculate power
        co2_kg = calculate_co2_emissions(100.0, 300.0, 730.0)
        # Reverse: power = (co2_kg * 1000) / (carbon_intensity * runtime) * 1000
        reverse_power = (co2_kg * 1000) / (300.0 * 730.0) * 1000
        self.assertAlmostEqual(reverse_power, 100.0, places=1)


class TestCalculationIntegration(unittest.TestCase):
    """Integration tests combining power and CO2 calculations"""

    def test_full_emission_pipeline(self):
        """Test complete calculation pipeline: base power → effective power → CO2"""
        # Scenario: t3.medium (15W base) at 50% CPU, 350g/kWh, 730h
        base_power = 15.0
        cpu_util = 50.0
        carbon_intensity = 350.0
        runtime_hours = 730.0

        # Step 1: Calculate effective power
        effective_power = calculate_simple_power_consumption(base_power, cpu_util)
        self.assertAlmostEqual(effective_power, 9.75, places=2)  # 15 × 0.65

        # Step 2: Calculate CO2 emissions
        co2_kg = calculate_co2_emissions(effective_power, carbon_intensity, runtime_hours)
        self.assertAlmostEqual(co2_kg, 2.491, places=3)

    def test_idle_vs_peak_emission_comparison(self):
        """Test emissions difference between idle and peak utilization"""
        base_power = 100.0
        carbon_intensity = 300.0
        runtime_hours = 730.0

        # Idle (0% CPU): 30W
        idle_power = calculate_simple_power_consumption(base_power, 0.0)
        idle_co2 = calculate_co2_emissions(idle_power, carbon_intensity, runtime_hours)

        # Peak (100% CPU): 100W
        peak_power = calculate_simple_power_consumption(base_power, 100.0)
        peak_co2 = calculate_co2_emissions(peak_power, carbon_intensity, runtime_hours)

        # Peak should be 3.33x idle (100W / 30W)
        ratio = peak_co2 / idle_co2
        self.assertAlmostEqual(ratio, 3.333, places=2)


if __name__ == "__main__":
    unittest.main()
