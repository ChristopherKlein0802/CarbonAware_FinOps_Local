"""
Unit Tests for Constants Module
Validates centralized constants and their academic integrity
"""

import unittest
from src.constants import (
    AcademicConstants, CarbonConstants, APIConstants,
    UIConstants, AWSConstants, ValidationConstants,
    get_scenario_factor, get_grid_status_threshold, get_cache_ttl
)


class TestAcademicConstants(unittest.TestCase):
    """Test academic and business constants"""

    def test_academic_constants_values(self):
        """Validate academic constant values are reasonable"""
        self.assertAlmostEqual(AcademicConstants.EUR_USD_RATE, 0.92, places=2)
        self.assertGreater(AcademicConstants.EU_ETS_PRICE_PER_TONNE, 0)
        self.assertEqual(AcademicConstants.HOURS_PER_MONTH, 730)

    def test_scenario_factors(self):
        """Test scenario factor ranges are reasonable"""
        self.assertGreater(AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR, 0)
        self.assertLess(AcademicConstants.CONSERVATIVE_SCENARIO_FACTOR, 1)
        self.assertGreater(AcademicConstants.MODERATE_SCENARIO_FACTOR, 0)
        self.assertLess(AcademicConstants.MODERATE_SCENARIO_FACTOR, 1)

    def test_sme_instance_ranges(self):
        """Test SME instance count ranges are logical"""
        self.assertLess(AcademicConstants.TYPICAL_SME_MIN_INSTANCES,
                       AcademicConstants.TYPICAL_SME_MID_INSTANCES)
        self.assertLess(AcademicConstants.TYPICAL_SME_MID_INSTANCES,
                       AcademicConstants.TYPICAL_SME_MAX_INSTANCES)


class TestCarbonConstants(unittest.TestCase):
    """Test carbon intensity thresholds and classifications"""

    def test_carbon_thresholds_logical_order(self):
        """Test carbon intensity thresholds are in logical order"""
        self.assertLess(CarbonConstants.OPTIMAL_THRESHOLD,
                       CarbonConstants.MODERATE_THRESHOLD)
        self.assertLess(CarbonConstants.MODERATE_THRESHOLD,
                       CarbonConstants.HIGH_CARBON_THRESHOLD)

    def test_power_conversion_constants(self):
        """Test power conversion constants are correct"""
        self.assertEqual(CarbonConstants.WATTS_TO_KW_CONVERSION, 1000)
        self.assertEqual(CarbonConstants.GRAMS_TO_KG_CONVERSION, 1000)
        self.assertEqual(CarbonConstants.SECONDS_TO_HOURS_CONVERSION, 3600)

    def test_cpu_utilization_bounds(self):
        """Test CPU utilization bounds are valid"""
        self.assertEqual(CarbonConstants.MIN_CPU_UTILIZATION, 0)
        self.assertEqual(CarbonConstants.MAX_CPU_UTILIZATION, 100)
        self.assertGreaterEqual(CarbonConstants.DEFAULT_CPU_UTILIZATION, 0)
        self.assertLessEqual(CarbonConstants.DEFAULT_CPU_UTILIZATION, 100)


class TestAPIConstants(unittest.TestCase):
    """Test API timeout and cache configuration"""

    def test_timeout_values_reasonable(self):
        """Test API timeouts are reasonable for production use"""
        self.assertGreaterEqual(APIConstants.ELECTRICITYMAP_TIMEOUT, 10)
        self.assertLessEqual(APIConstants.ELECTRICITYMAP_TIMEOUT, 60)
        self.assertGreaterEqual(APIConstants.BOAVIZTA_TIMEOUT, 5)
        self.assertLessEqual(APIConstants.BOAVIZTA_TIMEOUT, 30)

    def test_cache_ttl_values(self):
        """Test cache TTL values are logical"""
        # Carbon data should be cached less than historical data
        self.assertLess(APIConstants.CARBON_DATA_TTL, APIConstants.CARBON_24H_TTL)
        # Power data should be cached longer than cost data
        self.assertGreater(APIConstants.POWER_DATA_TTL, APIConstants.COST_DATA_TTL)

    def test_cloudtrail_config(self):
        """Test CloudTrail configuration is reasonable"""
        self.assertGreaterEqual(APIConstants.CLOUDTRAIL_LOOKBACK_DAYS, 7)
        self.assertLessEqual(APIConstants.CLOUDTRAIL_LOOKBACK_DAYS, 90)


class TestAWSConstants(unittest.TestCase):
    """Test AWS region mappings and configuration"""

    def test_region_mappings_exist(self):
        """Test essential AWS regions are mapped"""
        essential_regions = ["eu-central-1", "eu-west-1", "us-east-1"]
        for region in essential_regions:
            self.assertIn(region, AWSConstants.REGION_MAPPINGS)

    def test_mapping_values_valid(self):
        """Test mapping values are valid ElectricityMaps zones"""
        for aws_region, em_zone in AWSConstants.REGION_MAPPINGS.items():
            self.assertIsInstance(em_zone, str)
            self.assertGreater(len(em_zone), 0)

    def test_default_configuration(self):
        """Test default AWS configuration is set"""
        self.assertIsInstance(AWSConstants.DEFAULT_AWS_PROFILE, str)
        self.assertIsInstance(AWSConstants.DEFAULT_REGION, str)
        self.assertIn(AWSConstants.DEFAULT_REGION, AWSConstants.REGION_MAPPINGS)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions for constants"""

    def test_get_scenario_factor(self):
        """Test scenario factor retrieval"""
        self.assertGreater(get_scenario_factor("conservative"), 0)
        self.assertGreater(get_scenario_factor("moderate"), 0)
        self.assertEqual(get_scenario_factor("invalid"), 0.0)

    def test_get_grid_status_threshold(self):
        """Test grid status threshold retrieval"""
        self.assertEqual(get_grid_status_threshold("optimal"),
                        CarbonConstants.OPTIMAL_THRESHOLD)
        self.assertEqual(get_grid_status_threshold("moderate"),
                        CarbonConstants.MODERATE_THRESHOLD)
        self.assertEqual(get_grid_status_threshold("invalid"),
                        CarbonConstants.MODERATE_THRESHOLD)

    def test_get_cache_ttl(self):
        """Test cache TTL retrieval"""
        self.assertEqual(get_cache_ttl("carbon"), APIConstants.CARBON_DATA_TTL)
        self.assertEqual(get_cache_ttl("power"), APIConstants.POWER_DATA_TTL)
        self.assertEqual(get_cache_ttl("invalid"), APIConstants.CARBON_DATA_TTL)


class TestNoFallbackPolicy(unittest.TestCase):
    """Test NO-FALLBACK policy enforcement in constants"""

    def test_no_default_fallback_values(self):
        """Test that fallback constants have been removed per NO-FALLBACK policy"""
        # These should not exist or be commented out
        with self.assertRaises(AttributeError):
            _ = AcademicConstants.DEFAULT_COST_PER_INSTANCE_EUR

        with self.assertRaises(AttributeError):
            _ = AcademicConstants.DEFAULT_CO2_PER_INSTANCE_KG

        with self.assertRaises(AttributeError):
            _ = CarbonConstants.EU_CONSERVATIVE_AVERAGE

    def test_no_fallback_policy_documented(self):
        """Test that NO-FALLBACK policy is properly documented"""
        self.assertEqual(ValidationConstants.NO_FALLBACK_POLICY, "NO-FALLBACK")


if __name__ == '__main__':
    unittest.main()