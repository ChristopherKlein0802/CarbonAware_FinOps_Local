"""
Unit Tests for Constants Module
Validates centralized constants and their academic integrity
"""

import unittest
from src.domain.constants import AcademicConstants, CarbonConstants, UIConstants


class TestAcademicConstants(unittest.TestCase):
    """Test academic and business constants"""

    def test_academic_constants_values(self):
        """Validate academic constant values are reasonable"""
        # EUR_USD_RATE is now a static method
        eur_usd = AcademicConstants.get_eur_usd_rate()
        self.assertAlmostEqual(eur_usd, 0.92, places=1)
        self.assertGreater(AcademicConstants.EU_ETS_PRICE_PER_TONNE, 0)
        self.assertEqual(AcademicConstants.HOURS_PER_MONTH, 730)

    def test_scenario_factors(self):
        """Test scenario factor ranges are reasonable"""
        self.assertGreater(AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR, 0)
        self.assertLess(AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR, 1)
        self.assertGreater(AcademicConstants.MODERATE_SCENARIO_FACTOR, 0)
        self.assertLess(AcademicConstants.MODERATE_SCENARIO_FACTOR, 1)


class TestCarbonConstants(unittest.TestCase):
    """Test carbon intensity thresholds and classifications"""

    def test_carbon_thresholds_logical_order(self):
        """Test carbon intensity thresholds are in logical order"""
        self.assertLess(CarbonConstants.OPTIMAL_THRESHOLD, CarbonConstants.MODERATE_THRESHOLD)
        self.assertLess(CarbonConstants.MODERATE_THRESHOLD, CarbonConstants.HIGH_CARBON_THRESHOLD)


class TestUIConstants(unittest.TestCase):
    """Test UI and cache configuration"""

    def test_streamlit_cache_ttl(self):
        """Ensure Streamlit cache TTL is positive"""
        self.assertGreater(UIConstants.STREAMLIT_CACHE_TTL_SECONDS, 0)


if __name__ == "__main__":
    unittest.main()
