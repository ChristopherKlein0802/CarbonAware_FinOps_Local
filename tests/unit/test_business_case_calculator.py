"""
Unit Tests for Business Case Calculator

Tests business case scenario calculations for cost and CO2 savings.
"""

import unittest
from unittest.mock import patch
from src.application.calculator import BusinessCaseCalculator
from src.domain.models import BusinessCase
from src.domain.constants import AcademicConstants


class TestBusinessCaseCalculatorInit(unittest.TestCase):
    """Test calculator initialization"""

    @patch("src.application.calculator.logger")
    def test_calculator_initialization_logs(self, mock_logger):
        """Test calculator logs initialization"""
        calc = BusinessCaseCalculator()
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Business Case Calculator", call_args)


class TestBusinessCaseBasicScenarios(unittest.TestCase):
    """Test basic business case calculation scenarios"""

    def setUp(self):
        """Set up test calculator"""
        self.calc = BusinessCaseCalculator()

    def test_zero_baseline_returns_zero_savings(self):
        """Test zero baseline cost/CO2 returns zero savings"""
        result = self.calc.calculate_business_case(0.0, 0.0)

        self.assertIsInstance(result, BusinessCase)
        self.assertEqual(result.baseline_cost_eur, 0.0)
        self.assertEqual(result.baseline_co2_kg, 0.0)
        self.assertEqual(result.office_hours_savings_eur, 0.0)
        self.assertEqual(result.carbon_aware_savings_eur, 0.0)
        self.assertEqual(result.integrated_savings_eur, 0.0)

    def test_negative_baseline_normalized_to_zero(self):
        """Test negative inputs are normalized to zero (defensive)"""
        result = self.calc.calculate_business_case(-100.0, -50.0)

        self.assertEqual(result.baseline_cost_eur, 0.0)
        self.assertEqual(result.baseline_co2_kg, 0.0)
        self.assertEqual(result.office_hours_savings_eur, 0.0)

    def test_small_baseline_returns_conservative_savings(self):
        """Test small infrastructure (< €100) returns conservative factors"""
        result = self.calc.calculate_business_case(50.0, 10.0, validation_factor=1.0)

        # Small infrastructure has cost_scaling = 0.8
        # Good validation (1.0) has quality_modifier = 0.8
        # Conservative: 0.10 × 0.8 × 0.8 = 0.064 (6.4%)
        # Moderate: 0.20 × 0.8 × 0.8 = 0.128 (12.8%)

        self.assertGreater(result.office_hours_savings_eur, 0)
        self.assertLess(result.office_hours_savings_eur, 50.0 * 0.15)  # Capped at 15%
        self.assertGreater(result.carbon_aware_savings_eur, result.office_hours_savings_eur)


class TestBusinessCaseValidationFactors(unittest.TestCase):
    """Test business case responds correctly to validation factors"""

    def setUp(self):
        """Set up test calculator and baseline"""
        self.calc = BusinessCaseCalculator()
        self.baseline_cost = 200.0
        self.baseline_co2 = 50.0

    def test_excellent_validation_factor(self):
        """Test excellent validation (≤1.5) gives high quality modifier"""
        result = self.calc.calculate_business_case(self.baseline_cost, self.baseline_co2, validation_factor=1.2)

        # Medium infrastructure (100-500): cost_scaling = 1.1
        # Good validation (≤1.5): quality_modifier = 0.8
        # Conservative: 0.10 × 0.8 × 1.1 = 0.088 (8.8%)
        # Moderate: 0.20 × 0.8 × 1.1 = 0.176 (17.6%)

        self.assertGreater(result.office_hours_savings_eur, 0)
        self.assertGreater(result.carbon_aware_savings_eur, result.office_hours_savings_eur)
        self.assertEqual(result.integrated_savings_eur, result.carbon_aware_savings_eur)

    def test_moderate_validation_factor(self):
        """Test moderate validation (1.5-5.0) reduces quality modifier"""
        result_good = self.calc.calculate_business_case(self.baseline_cost, self.baseline_co2, validation_factor=1.2)
        result_moderate = self.calc.calculate_business_case(
            self.baseline_cost, self.baseline_co2, validation_factor=3.0
        )

        # Moderate should have lower savings than good validation
        self.assertLess(result_moderate.carbon_aware_savings_eur, result_good.carbon_aware_savings_eur)

    def test_limited_validation_factor(self):
        """Test limited validation (5.0-50.0) significantly reduces savings"""
        result_good = self.calc.calculate_business_case(self.baseline_cost, self.baseline_co2, validation_factor=1.2)
        result_limited = self.calc.calculate_business_case(
            self.baseline_cost, self.baseline_co2, validation_factor=10.0
        )

        # Limited should have much lower savings
        self.assertLess(
            result_limited.carbon_aware_savings_eur,
            result_good.carbon_aware_savings_eur * 0.7,  # At least 30% reduction
        )

    def test_poor_validation_factor(self):
        """Test poor validation (>50.0) gives minimal savings"""
        result = self.calc.calculate_business_case(self.baseline_cost, self.baseline_co2, validation_factor=100.0)

        # Poor validation should give minimal savings
        self.assertLess(result.carbon_aware_savings_eur, self.baseline_cost * 0.1)


class TestBusinessCaseScalingFactors(unittest.TestCase):
    """Test cost-based scaling for different infrastructure sizes"""

    def setUp(self):
        """Set up test calculator"""
        self.calc = BusinessCaseCalculator()
        self.validation_factor = 1.0  # Keep constant to test scaling

    def test_small_infrastructure_scaling(self):
        """Test small infrastructure (<€100) has reduced scaling"""
        result = self.calc.calculate_business_case(50.0, 10.0, validation_factor=self.validation_factor)

        # Small infrastructure: cost_scaling = 0.8
        # Should give lower absolute savings due to scaling
        savings_percentage = result.carbon_aware_savings_eur / 50.0
        self.assertLess(savings_percentage, 0.15)  # Below 15%

    def test_medium_infrastructure_scaling(self):
        """Test medium infrastructure (€100-500) has normal scaling"""
        result = self.calc.calculate_business_case(200.0, 50.0, validation_factor=self.validation_factor)

        # Medium infrastructure: cost_scaling = 1.1
        savings_percentage = result.carbon_aware_savings_eur / 200.0
        self.assertGreater(savings_percentage, 0.05)  # At least 5%
        self.assertLess(savings_percentage, 0.25)  # Below 25% cap

    def test_large_infrastructure_scaling(self):
        """Test large infrastructure (>€500) has enhanced scaling"""
        result = self.calc.calculate_business_case(1000.0, 250.0, validation_factor=self.validation_factor)

        # Large infrastructure: cost_scaling = 1.3
        savings_percentage = result.carbon_aware_savings_eur / 1000.0
        self.assertGreater(savings_percentage, 0.10)  # At least 10%

    def test_scaling_proportional_across_sizes(self):
        """Test savings scale proportionally with infrastructure size"""
        small = self.calc.calculate_business_case(100.0, 25.0, 1.0)
        large = self.calc.calculate_business_case(1000.0, 250.0, 1.0)

        # Large should have higher percentage savings due to scaling
        small_pct = small.carbon_aware_savings_eur / 100.0
        large_pct = large.carbon_aware_savings_eur / 1000.0
        self.assertGreater(large_pct, small_pct)


class TestBusinessCaseAcademicConstraints(unittest.TestCase):
    """Test academic constraints and literature-based caps"""

    def setUp(self):
        """Set up test calculator"""
        self.calc = BusinessCaseCalculator()

    def test_conservative_scenario_capped_at_15_percent(self):
        """Test conservative scenario respects 15% literature cap"""
        # Even with perfect conditions, should not exceed 15%
        result = self.calc.calculate_business_case(1000.0, 250.0, validation_factor=1.0)

        conservative_pct = result.office_hours_savings_eur / 1000.0
        self.assertLessEqual(conservative_pct, 0.15)  # McKinsey lower bound

    def test_moderate_scenario_capped_at_25_percent(self):
        """Test moderate scenario respects 25% literature cap"""
        # Even with perfect conditions, should not exceed 25%
        result = self.calc.calculate_business_case(1000.0, 250.0, validation_factor=1.0)

        moderate_pct = result.carbon_aware_savings_eur / 1000.0
        self.assertLessEqual(moderate_pct, 0.25)  # McKinsey/MIT upper bound

    def test_co2_reduction_matches_cost_reduction(self):
        """Test CO2 reduction percentage matches cost reduction (academic assumption)"""
        result = self.calc.calculate_business_case(200.0, 50.0, 1.0)

        cost_reduction_pct = result.carbon_aware_savings_eur / 200.0
        co2_reduction_pct = result.carbon_aware_co2_reduction_kg / 50.0

        # Should be identical (same factor applied)
        self.assertAlmostEqual(cost_reduction_pct, co2_reduction_pct, places=10)

    def test_confidence_interval_is_fixed(self):
        """Test confidence interval is ±15% as per academic standards"""
        result = self.calc.calculate_business_case(100.0, 25.0, 1.0)
        self.assertEqual(result.confidence_interval, 0.15)

    def test_methodology_tag_present(self):
        """Test methodology is properly tagged"""
        result = self.calc.calculate_business_case(100.0, 25.0, 1.0)
        self.assertEqual(result.methodology, "INTEGRATION_EXCELLENCE")

    def test_validation_status_includes_factor(self):
        """Test validation status documents the validation factor"""
        validation_factor = 2.5
        result = self.calc.calculate_business_case(100.0, 25.0, validation_factor)
        self.assertIn(str(validation_factor), result.validation_status)

    def test_source_notes_reference_literature(self):
        """Test source notes reference academic literature"""
        result = self.calc.calculate_business_case(100.0, 25.0, 1.0)
        self.assertIn("McKinsey", result.source_notes)
        self.assertIn("MIT", result.source_notes)


class TestBusinessCaseDevelopmentEnvironment(unittest.TestCase):
    """Test special handling for development environments"""

    def setUp(self):
        """Set up test calculator"""
        self.calc = BusinessCaseCalculator()

    def test_dev_environment_identified_by_low_cost(self):
        """Test development environment identified by cost < €1"""
        result = self.calc.calculate_business_case(0.5, 0.1, 1.0)

        # Development environment: quality_modifier = 0.4 (very conservative)
        # Should give minimal savings
        savings_pct = result.carbon_aware_savings_eur / 0.5
        self.assertLess(savings_pct, 0.10)  # Very conservative

    @patch("src.application.calculator.logger")
    def test_dev_environment_logs_warning(self, mock_logger):
        """Test development environment logs informational message"""
        self.calc.calculate_business_case(0.5, 0.1, 1.0)

        # Check that logger was called with dev environment message
        mock_logger.info.assert_called()
        # Find the call containing dev environment message
        calls = [str(call) for call in mock_logger.info.call_args_list]
        dev_call = any("Development" in str(call) for call in calls)
        self.assertTrue(dev_call)


class TestBusinessCaseRealisticScenarios(unittest.TestCase):
    """Test realistic cloud infrastructure scenarios"""

    def setUp(self):
        """Set up test calculator"""
        self.calc = BusinessCaseCalculator()

    def test_typical_sme_scenario(self):
        """Test typical SME cloud infrastructure (€200-500/month)"""
        result = self.calc.calculate_business_case(350.0, 87.5, validation_factor=2.0)

        # Medium infrastructure, moderate validation
        # Should give reasonable savings (5-15%)
        savings_pct = result.carbon_aware_savings_eur / 350.0
        self.assertGreater(savings_pct, 0.05)
        self.assertLess(savings_pct, 0.20)

        # CO2 reduction should be proportional
        co2_reduction = result.carbon_aware_co2_reduction_kg / 87.5
        self.assertAlmostEqual(savings_pct, co2_reduction, places=5)

    def test_enterprise_scenario(self):
        """Test enterprise cloud infrastructure (>€1000/month)"""
        result = self.calc.calculate_business_case(2500.0, 625.0, validation_factor=1.3)

        # Large infrastructure, good validation
        # Should give substantial savings (10-25%)
        savings_pct = result.carbon_aware_savings_eur / 2500.0
        self.assertGreater(savings_pct, 0.10)
        self.assertLess(savings_pct, 0.25)

        # Absolute savings should be significant
        self.assertGreater(result.carbon_aware_savings_eur, 250.0)  # At least €250

    def test_startup_scenario(self):
        """Test startup cloud infrastructure (€50-100/month)"""
        result = self.calc.calculate_business_case(75.0, 18.75, validation_factor=3.0)

        # Small infrastructure, moderate validation
        # Should give conservative savings (<10%)
        savings_pct = result.carbon_aware_savings_eur / 75.0
        self.assertGreater(savings_pct, 0.02)  # At least 2%
        self.assertLess(savings_pct, 0.15)

    def test_integrated_savings_equals_moderate_scenario(self):
        """Test integrated savings uses moderate scenario"""
        result = self.calc.calculate_business_case(200.0, 50.0, 1.0)

        self.assertEqual(result.integrated_savings_eur, result.carbon_aware_savings_eur)
        self.assertEqual(result.integrated_co2_reduction_kg, result.carbon_aware_co2_reduction_kg)


class TestBusinessCaseEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        """Set up test calculator"""
        self.calc = BusinessCaseCalculator()

    def test_extremely_high_validation_factor(self):
        """Test extremely high validation factor (>1000)"""
        result = self.calc.calculate_business_case(100.0, 25.0, validation_factor=5000.0)

        # Should give minimal but non-zero savings
        self.assertGreater(result.carbon_aware_savings_eur, 0)
        self.assertLess(result.carbon_aware_savings_eur, 5.0)  # Very conservative

    def test_boundary_at_100_euro(self):
        """Test cost scaling boundary at €100"""
        result_99 = self.calc.calculate_business_case(99.0, 25.0, 1.0)
        result_101 = self.calc.calculate_business_case(101.0, 25.0, 1.0)

        # €101 should have higher percentage savings (medium tier)
        pct_99 = result_99.carbon_aware_savings_eur / 99.0
        pct_101 = result_101.carbon_aware_savings_eur / 101.0
        self.assertGreater(pct_101, pct_99)

    def test_boundary_at_500_euro(self):
        """Test cost scaling boundary at €500"""
        result_499 = self.calc.calculate_business_case(499.0, 125.0, 1.0)
        result_501 = self.calc.calculate_business_case(501.0, 125.0, 1.0)

        # €501 should have higher percentage savings (large tier)
        pct_499 = result_499.carbon_aware_savings_eur / 499.0
        pct_501 = result_501.carbon_aware_savings_eur / 501.0
        self.assertGreater(pct_501, pct_499)

    def test_very_large_infrastructure(self):
        """Test very large infrastructure (€10,000+/month)"""
        result = self.calc.calculate_business_case(15000.0, 3750.0, validation_factor=1.2)

        # Should cap at 25% even for large infrastructure
        savings_pct = result.carbon_aware_savings_eur / 15000.0
        self.assertLessEqual(savings_pct, 0.25)
        self.assertGreater(result.carbon_aware_savings_eur, 1500.0)


if __name__ == "__main__":
    unittest.main()
