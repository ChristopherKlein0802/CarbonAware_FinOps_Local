"""
Tests for src.core.tracker module
Testing RuntimeTracker functionality with proper mocking
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List

# Import the class under test
from src.core.tracker import RuntimeTracker
from src.models.aws import EC2Instance


class TestRuntimeTracker(unittest.TestCase):
    """Test cases for RuntimeTracker class"""

    def setUp(self):
        """Set up test fixtures"""
        self.tracker = RuntimeTracker()
        self.sample_instance = {
            "instance_id": "i-test123",
            "instance_type": "t3.medium",
            "state": "running",
            "region": "eu-central-1",
            "launch_time": datetime.now(),
            "state_transition_reason": "User initiated"
        }

    def test_initialization(self):
        """Test RuntimeTracker initialization"""
        tracker = RuntimeTracker()
        self.assertIsInstance(tracker, RuntimeTracker)

    @patch('src.core.tracker.boto3.Session')
    def test_get_all_ec2_instances_success(self, mock_session):
        """Test successful EC2 instance retrieval"""
        # Mock AWS response
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-test123',
                    'InstanceType': 't3.medium',
                    'State': {'Name': 'running'},
                    'LaunchTime': datetime.now(),
                    'StateTransitionReason': 'User initiated'
                }]
            }]
        }

        instances = self.tracker.get_all_ec2_instances()

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]['instance_id'], 'i-test123')
        self.assertEqual(instances[0]['instance_type'], 't3.medium')
        self.assertEqual(instances[0]['state'], 'running')

    @patch('src.core.tracker.boto3.Session')
    def test_get_all_ec2_instances_error(self, mock_session):
        """Test EC2 instance retrieval with AWS error"""
        mock_session.return_value.client.side_effect = Exception("AWS Error")

        instances = self.tracker.get_all_ec2_instances()

        self.assertEqual(instances, [])

    # CloudTrail monitoring removed after cleanup
    def test_get_precise_runtime_hours_cloudtrail_success(self):
        """Test runtime calculation after CloudTrail removal - uses fallback"""
        runtime = self.tracker.get_precise_runtime_hours(self.sample_instance)

        # Should return fallback estimate since CloudTrail is removed
        self.assertIsInstance(runtime, float)
        self.assertGreater(runtime, 0)

    # CloudTrail monitoring removed after cleanup
    def test_get_precise_runtime_hours_cloudtrail_fallback(self):
        """Test runtime calculation after CloudTrail removal - uses fallback"""
        runtime = self.tracker.get_precise_runtime_hours(self.sample_instance)

        # Should fall back to conservative estimate
        self.assertIsInstance(runtime, float)
        self.assertGreater(runtime, 0)

    def test_minimal_conservative_estimate_micro(self):
        """Test conservative estimate for micro instance"""
        instance = {**self.sample_instance, "instance_type": "t3.micro", "state": "running"}

        runtime = self.tracker._get_minimal_conservative_estimate(instance)

        self.assertIsInstance(runtime, float)
        self.assertGreater(runtime, 0)

    def test_minimal_conservative_estimate_large(self):
        """Test conservative estimate for large instance"""
        instance = {**self.sample_instance, "instance_type": "t3.large", "state": "stopped"}

        runtime = self.tracker._get_minimal_conservative_estimate(instance)

        self.assertIsInstance(runtime, float)
        self.assertGreater(runtime, 0)

    @patch('src.core.tracker.boto3.Session')
    @patch('src.utils.cache.is_cache_valid')
    def test_get_cpu_utilization_cached(self, mock_cache_valid, mock_session):
        """Test CPU utilization retrieval from cache"""
        mock_cache_valid.return_value = True

        with patch('builtins.open', mock_open_json({"cpu_utilization": 45.5})):
            cpu_util = self.tracker.get_cpu_utilization("i-test123")

        self.assertEqual(cpu_util, 45.5)

    @patch('src.core.tracker.boto3.Session')
    @patch('src.utils.cache.is_cache_valid')
    def test_get_cpu_utilization_fresh(self, mock_cache_valid, mock_session):
        """Test CPU utilization fresh API call"""
        mock_cache_valid.return_value = False

        # Mock CloudWatch response
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_metric_data.return_value = {
            'MetricDataResults': [{
                'Values': [30.0, 40.0, 50.0]
            }]
        }

        with patch('builtins.open', Mock()):
            with patch('os.makedirs'):
                cpu_util = self.tracker.get_cpu_utilization("i-test123")

        self.assertEqual(cpu_util, 40.0)  # Average of [30, 40, 50]

    @patch('src.core.tracker.boto3.Session')
    @patch('src.utils.cache.is_cache_valid')
    def test_get_cpu_utilization_no_data(self, mock_cache_valid, mock_session):
        """Test CPU utilization with no CloudWatch data"""
        mock_cache_valid.return_value = False

        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_metric_data.return_value = {
            'MetricDataResults': [{'Values': []}]
        }

        cpu_util = self.tracker.get_cpu_utilization("i-test123")

        self.assertIsNone(cpu_util)

    @patch('src.api.client.unified_api_client')
    def test_process_instance_enhanced_success(self, mock_api_client):
        """Test successful enhanced instance processing"""
        # Mock API responses
        mock_power_data = Mock()
        mock_power_data.avg_power_watts = 15.0
        mock_api_client.get_power_consumption.return_value = mock_power_data
        mock_api_client.get_instance_pricing.return_value = 0.05

        # Mock internal methods
        with patch.object(self.tracker, 'get_precise_runtime_hours', return_value=720.0):
            with patch.object(self.tracker, 'get_cpu_utilization', return_value=50.0):
                result = self.tracker.process_instance_enhanced(self.sample_instance, 350.0)

        self.assertIsInstance(result, EC2Instance)
        self.assertEqual(result.instance_id, "i-test123")
        self.assertEqual(result.instance_type, "t3.medium")
        self.assertGreater(result.monthly_cost_eur, 0)
        self.assertGreater(result.monthly_co2_kg, 0)

    @patch('src.api.client.unified_api_client')
    def test_process_instance_enhanced_no_power_data(self, mock_api_client):
        """Test instance processing with missing power data"""
        mock_api_client.get_power_consumption.return_value = None

        result = self.tracker.process_instance_enhanced(self.sample_instance, 350.0)

        self.assertIsNone(result)

    @patch('src.api.client.unified_api_client')
    def test_process_instance_enhanced_no_cpu_data(self, mock_api_client):
        """Test instance processing with missing CPU data (NO-FALLBACK)"""
        mock_power_data = Mock()
        mock_power_data.avg_power_watts = 15.0
        mock_api_client.get_power_consumption.return_value = mock_power_data
        mock_api_client.get_instance_pricing.return_value = 0.05

        with patch.object(self.tracker, 'get_precise_runtime_hours', return_value=720.0):
            with patch.object(self.tracker, 'get_cpu_utilization', return_value=None):
                result = self.tracker.process_instance_enhanced(self.sample_instance, 350.0)

        # Should return EC2Instance with fallback CPU due to changed behavior
        self.assertIsNotNone(result)
        self.assertIsInstance(result, EC2Instance)
        self.assertEqual(result.cpu_utilization, 35.0)  # Fallback CPU value

    def test_get_enhanced_confidence_metadata(self):
        """Test confidence metadata generation"""
        confidence, sources = self.tracker._get_enhanced_confidence_metadata(self.sample_instance, 720.0)

        self.assertIsInstance(confidence, str)
        self.assertIsInstance(sources, list)
        self.assertIn("aws_api", sources)


def mock_open_json(data):
    """Helper function to mock open with JSON data"""
    import json
    mock = MagicMock()
    mock.return_value.__enter__.return_value.read.return_value = json.dumps(data)
    return mock


if __name__ == '__main__':
    unittest.main()