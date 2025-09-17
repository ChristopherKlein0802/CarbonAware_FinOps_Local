"""
Tests for src.core.optimizer module
Testing CarbonOptimizer functionality
"""

import unittest
from unittest.mock import Mock
from datetime import datetime

from src.core.optimizer import CarbonOptimizer
from src.models.aws import EC2Instance


class TestCarbonOptimizer(unittest.TestCase):
    """Test cases for CarbonOptimizer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = CarbonOptimizer()

        # Create sample instances for testing
        self.sample_instances = [
            EC2Instance(
                instance_id="i-test1",
                instance_type="t3.micro",
                state="running",
                region="eu-central-1",
                power_watts=8.0,
                monthly_cost_eur=15.0,
                monthly_co2_kg=1.5,
                confidence_level="high",
                data_sources=["test"],
                last_updated=datetime.now()
            ),
            EC2Instance(
                instance_id="i-test2",
                instance_type="t3.medium",
                state="running",
                region="eu-central-1",
                power_watts=25.0,
                monthly_cost_eur=45.0,
                monthly_co2_kg=4.5,
                confidence_level="high",
                data_sources=["test"],
                last_updated=datetime.now()
            )
        ]

    def test_initialization(self):
        """Test CarbonOptimizer initialization"""
        optimizer = CarbonOptimizer()
        self.assertIsInstance(optimizer, CarbonOptimizer)

    def test_analyze_optimization_opportunities_normal(self):
        """Test normal optimization opportunities analysis"""
        result = self.optimizer.analyze_optimization_opportunities(self.sample_instances)

        # Check structure
        self.assertIn("office_hours_potential", result)
        self.assertIn("carbon_aware_potential", result)
        self.assertIn("integrated_potential", result)
        self.assertIn("baseline_cost_eur", result)
        self.assertIn("baseline_co2_kg", result)

        # Check calculations (total cost = 15 + 45 = 60, total CO2 = 1.5 + 4.5 = 6.0)
        self.assertEqual(result["baseline_cost_eur"], 60.0)
        self.assertEqual(result["baseline_co2_kg"], 6.0)

        # Check scenario calculations
        self.assertEqual(result["office_hours_potential"], 6.0)  # 10% of 60
        self.assertEqual(result["carbon_aware_potential"], 12.0)  # 20% of 60
        self.assertEqual(result["integrated_potential"], 12.0)    # Using scenario B

        # Check CO2 potentials
        self.assertEqual(result["office_hours_co2_potential"], 0.6)   # 10% of 6.0
        self.assertEqual(result["carbon_aware_co2_potential"], 1.2)   # 20% of 6.0
        self.assertEqual(result["integrated_co2_potential"], 1.2)     # Using scenario B

        # Check quality indicator
        self.assertEqual(result["analysis_quality"], "demonstrative_scenarios")

    def test_analyze_optimization_opportunities_empty_list(self):
        """Test optimization analysis with empty instances list"""
        result = self.optimizer.analyze_optimization_opportunities([])

        self.assertEqual(result["office_hours_potential"], 0.0)
        self.assertEqual(result["carbon_aware_potential"], 0.0)
        self.assertEqual(result["integrated_potential"], 0.0)
        self.assertEqual(result["analysis_quality"], "insufficient_data")

    def test_analyze_optimization_opportunities_single_instance(self):
        """Test optimization analysis with single instance"""
        single_instance = [self.sample_instances[0]]  # 15 EUR, 1.5 kg CO2

        result = self.optimizer.analyze_optimization_opportunities(single_instance)

        self.assertEqual(result["baseline_cost_eur"], 15.0)
        self.assertEqual(result["baseline_co2_kg"], 1.5)
        self.assertEqual(result["office_hours_potential"], 1.5)   # 10% of 15
        self.assertEqual(result["carbon_aware_potential"], 3.0)   # 20% of 15

    def test_analyze_optimization_opportunities_zero_costs(self):
        """Test optimization analysis with instances having zero costs"""
        zero_cost_instance = EC2Instance(
            instance_id="i-zero",
            instance_type="t3.nano",
            state="stopped",
            region="eu-central-1",
            power_watts=0.0,
            monthly_cost_eur=0.0,
            monthly_co2_kg=0.0,
            confidence_level="low",
            data_sources=["test"],
            last_updated=datetime.now()
        )

        result = self.optimizer.analyze_optimization_opportunities([zero_cost_instance])

        self.assertEqual(result["baseline_cost_eur"], 0.0)
        self.assertEqual(result["baseline_co2_kg"], 0.0)
        self.assertEqual(result["office_hours_potential"], 0.0)
        self.assertEqual(result["carbon_aware_potential"], 0.0)

    def test_calculate_carbon_aware_scheduling_normal(self):
        """Test normal carbon-aware scheduling calculation"""
        carbon_history = [
            {"hour": 0, "intensity": 300},
            {"hour": 1, "intensity": 250},
            {"hour": 2, "intensity": 400},
            {"hour": 3, "intensity": 350},
            {"hour": 4, "intensity": 200},
            {"hour": 5, "intensity": 450}
        ]

        result = self.optimizer.calculate_carbon_aware_scheduling(carbon_history)

        # Check structure
        self.assertIn("optimal_hours", result)
        self.assertIn("peak_hours", result)
        self.assertIn("savings_potential", result)
        self.assertIn("analysis_quality", result)

        # Check that hours are sorted
        self.assertTrue(all(result["optimal_hours"][i] <= result["optimal_hours"][i+1]
                          for i in range(len(result["optimal_hours"])-1)))
        self.assertTrue(all(result["peak_hours"][i] <= result["peak_hours"][i+1]
                          for i in range(len(result["peak_hours"])-1)))

        # Lowest intensity should be in optimal hours
        self.assertIn(4, result["optimal_hours"])  # Hour 4 has intensity 200 (lowest)

        # Highest intensity should be in peak hours
        self.assertIn(5, result["peak_hours"])     # Hour 5 has intensity 450 (highest)

        self.assertEqual(result["analysis_quality"], "pattern_based")

    def test_calculate_carbon_aware_scheduling_empty_history(self):
        """Test carbon-aware scheduling with empty history"""
        result = self.optimizer.calculate_carbon_aware_scheduling([])

        self.assertEqual(result["optimal_hours"], [])
        self.assertEqual(result["peak_hours"], [])
        self.assertEqual(result["savings_potential"], 0.0)
        self.assertEqual(result["analysis_quality"], "insufficient_data")

    def test_calculate_carbon_aware_scheduling_insufficient_data(self):
        """Test carbon-aware scheduling with insufficient data points"""
        carbon_history = [
            {"hour": 0, "intensity": 300},
            {"hour": 1, "intensity": 250}
        ]

        result = self.optimizer.calculate_carbon_aware_scheduling(carbon_history)

        self.assertEqual(result["analysis_quality"], "insufficient_data_points")

    def test_calculate_carbon_aware_scheduling_savings_potential(self):
        """Test savings potential calculation in carbon-aware scheduling"""
        # Large variance in carbon intensity
        carbon_history = [
            {"hour": 0, "intensity": 100},  # Very low
            {"hour": 1, "intensity": 200},
            {"hour": 2, "intensity": 300},
            {"hour": 3, "intensity": 400},
            {"hour": 4, "intensity": 500},  # Very high
            {"hour": 5, "intensity": 600}
        ]

        result = self.optimizer.calculate_carbon_aware_scheduling(carbon_history)

        # Should have some savings potential due to high variance
        self.assertGreater(result["savings_potential"], 0.0)
        self.assertLessEqual(result["savings_potential"], 0.15)  # Capped at 15%

    def test_suggest_instance_rightsizing_normal(self):
        """Test normal instance rightsizing suggestions"""
        result = self.optimizer.suggest_instance_rightsizing(self.sample_instances)

        self.assertEqual(len(result), 2)  # Two instances

        # Check first instance (low power)
        rec1 = result[0]
        self.assertEqual(rec1["instance_id"], "i-test1")
        self.assertEqual(rec1["current_type"], "t3.micro")
        self.assertEqual(rec1["current_power_watts"], 8.0)
        self.assertEqual(rec1["utilization_category"], "underutilized")
        self.assertIn("downsizing", rec1["recommendation"])

        # Check second instance (moderate power)
        rec2 = result[1]
        self.assertEqual(rec2["instance_id"], "i-test2")
        self.assertEqual(rec2["current_type"], "t3.medium")
        self.assertEqual(rec2["current_power_watts"], 25.0)
        self.assertEqual(rec2["utilization_category"], "moderate")
        self.assertIn("appropriate", rec2["recommendation"])

    def test_suggest_instance_rightsizing_high_power(self):
        """Test rightsizing suggestions for high power instance"""
        high_power_instance = EC2Instance(
            instance_id="i-high",
            instance_type="t3.xlarge",
            state="running",
            region="eu-central-1",
            power_watts=75.0,  # High power
            monthly_cost_eur=150.0,
            monthly_co2_kg=15.0,
            confidence_level="high",
            data_sources=["test"],
            last_updated=datetime.now()
        )

        result = self.optimizer.suggest_instance_rightsizing([high_power_instance])

        self.assertEqual(len(result), 1)
        rec = result[0]
        self.assertEqual(rec["utilization_category"], "high")
        self.assertIn("upsizing", rec["recommendation"])
        self.assertEqual(rec["potential_savings"], "Performance optimization")

    def test_suggest_instance_rightsizing_empty_list(self):
        """Test rightsizing suggestions with empty instances list"""
        result = self.optimizer.suggest_instance_rightsizing([])
        self.assertEqual(result, [])

    def test_suggest_instance_rightsizing_no_power_data(self):
        """Test rightsizing suggestions with instances lacking power data"""
        no_power_instance = EC2Instance(
            instance_id="i-nopower",
            instance_type="t3.medium",
            state="running",
            region="eu-central-1",
            power_watts=None,  # No power data
            monthly_cost_eur=45.0,
            monthly_co2_kg=4.5,
            confidence_level="low",
            data_sources=["test"],
            last_updated=datetime.now()
        )

        result = self.optimizer.suggest_instance_rightsizing([no_power_instance])

        # Should skip instances without power data
        self.assertEqual(result, [])

    def test_optimization_methodology_notes(self):
        """Test that methodology notes are included in results"""
        result = self.optimizer.analyze_optimization_opportunities(self.sample_instances)
        self.assertIn("methodology_note", result)
        self.assertIn("Conservative estimates", result["methodology_note"])

        scheduling_result = self.optimizer.calculate_carbon_aware_scheduling([
            {"hour": 0, "intensity": 300},
            {"hour": 1, "intensity": 250},
            {"hour": 2, "intensity": 400},
            {"hour": 3, "intensity": 350}
        ])
        self.assertIn("methodology_note", scheduling_result)
        self.assertIn("Demonstrative analysis", scheduling_result["methodology_note"])

        rightsizing_result = self.optimizer.suggest_instance_rightsizing(self.sample_instances)
        if rightsizing_result:
            self.assertIn("methodology_note", rightsizing_result[0])
            self.assertIn("power consumption patterns", rightsizing_result[0]["methodology_note"])


if __name__ == '__main__':
    unittest.main()