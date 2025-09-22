"""Unit tests for src.core.tracker.RuntimeTracker."""

import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch, mock_open

from src.core.tracker import RuntimeTracker
from src.models.aws import EC2Instance


class TestRuntimeTracker(unittest.TestCase):
    """Test suite for the RuntimeTracker class."""

    def setUp(self) -> None:
        self.tracker = RuntimeTracker()
        self.sample_instance = {
            "instance_id": "i-test123",
            "instance_type": "t3.medium",
            "state": "running",
            "region": "eu-central-1",
            "launch_time": datetime.now(timezone.utc),
            "state_transition_reason": "user-initiated",
        }

    def test_initialization(self) -> None:
        tracker = RuntimeTracker()
        self.assertIsInstance(tracker, RuntimeTracker)

    @patch("src.core.tracker.boto3.Session")
    def test_get_all_ec2_instances_success(self, mock_session: Mock) -> None:
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-test123",
                            "InstanceType": "t3.medium",
                            "State": {"Name": "running"},
                            "LaunchTime": datetime.now(timezone.utc),
                            "StateTransitionReason": "user",
                        }
                    ]
                }
            ]
        }

        instances = self.tracker.get_all_ec2_instances()

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["instance_id"], "i-test123")
        self.assertEqual(instances[0]["instance_type"], "t3.medium")

    @patch("src.core.tracker.boto3.Session")
    def test_get_all_ec2_instances_error(self, mock_session: Mock) -> None:
        mock_session.return_value.client.side_effect = Exception("AWS error")
        instances = self.tracker.get_all_ec2_instances()
        self.assertEqual(instances, [])

    @patch("src.core.tracker.is_cache_valid", return_value=True)
    def test_get_precise_runtime_hours_uses_cache(self, mock_cache_valid: Mock) -> None:
        cached_payload = {"runtime_hours": 12.5}
        with patch("builtins.open", mock_open(read_data=json.dumps(cached_payload))):
            runtime = self.tracker.get_precise_runtime_hours(self.sample_instance)
        self.assertEqual(runtime, 12.5)
        mock_cache_valid.assert_called_once()

    @patch("src.core.tracker.ensure_cache_dir")
    @patch("src.core.tracker.is_cache_valid", return_value=False)
    @patch("src.core.tracker.boto3.Session")
    def test_get_precise_runtime_hours_from_cloudtrail(
        self,
        mock_session: Mock,
        mock_cache_valid: Mock,
        mock_ensure_cache_dir: Mock,
    ) -> None:
        mock_cloudtrail = Mock()
        paginator = Mock()
        now = datetime.now(timezone.utc)
        events = [
            {
                "EventName": "StartInstances",
                "EventTime": now - timedelta(hours=5),
                "Resources": [{"ResourceName": "i-test123"}],
            },
            {
                "EventName": "StopInstances",
                "EventTime": now - timedelta(hours=1),
                "Resources": [{"ResourceName": "i-test123"}],
            },
        ]
        paginator.paginate.return_value = [{"Events": events}]
        mock_cloudtrail.get_paginator.return_value = paginator
        mock_session.return_value.client.return_value = mock_cloudtrail

        with patch("builtins.open", mock_open()) as mocked_open:
            runtime = self.tracker.get_precise_runtime_hours(self.sample_instance)

        self.assertAlmostEqual(runtime, 4.0, places=2)
        mocked_open.assert_called()

    @patch("src.core.tracker.ensure_cache_dir")
    @patch("src.core.tracker.is_cache_valid", return_value=False)
    @patch("src.core.tracker.boto3.Session")
    def test_get_precise_runtime_hours_no_events(
        self,
        mock_session: Mock,
        mock_cache_valid: Mock,
        mock_ensure_cache_dir: Mock,
    ) -> None:
        mock_cloudtrail = Mock()
        paginator = Mock()
        paginator.paginate.return_value = [{"Events": []}]
        mock_cloudtrail.get_paginator.return_value = paginator
        mock_session.return_value.client.return_value = mock_cloudtrail

        runtime = self.tracker.get_precise_runtime_hours(self.sample_instance)
        self.assertIsNone(runtime)

    @patch("src.core.tracker.boto3.Session")
    @patch("src.core.tracker.is_cache_valid", return_value=True)
    def test_get_cpu_utilization_cached(self, mock_cache_valid: Mock, mock_session: Mock) -> None:
        cached_payload = {"cpu_utilization": 45.5}
        with patch("builtins.open", mock_open(read_data=json.dumps(cached_payload))):
            cpu_util = self.tracker.get_cpu_utilization("i-test123")
        self.assertEqual(cpu_util, 45.5)

    @patch("src.core.tracker.boto3.Session")
    @patch("src.core.tracker.is_cache_valid", return_value=False)
    def test_get_cpu_utilization_fresh(self, mock_cache_valid: Mock, mock_session: Mock) -> None:
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_metric_data.return_value = {
            "MetricDataResults": [{"Values": [30.0, 40.0, 50.0]}]
        }

        with patch("builtins.open", mock_open()) as mocked_open:
            with patch("os.makedirs"):
                cpu_util = self.tracker.get_cpu_utilization("i-test123")

        self.assertEqual(cpu_util, 40.0)
        mocked_open.assert_called()

    @patch("src.core.tracker.boto3.Session")
    @patch("src.core.tracker.is_cache_valid", return_value=False)
    def test_get_cpu_utilization_no_data(self, mock_cache_valid: Mock, mock_session: Mock) -> None:
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_metric_data.return_value = {
            "MetricDataResults": [{"Values": []}]
        }

        cpu_util = self.tracker.get_cpu_utilization("i-test123")
        self.assertIsNone(cpu_util)

    @patch("src.api.client.unified_api_client")
    def test_process_instance_enhanced_success(self, mock_api_client: Mock) -> None:
        mock_power_data = Mock()
        mock_power_data.avg_power_watts = 15.0
        mock_api_client.get_power_consumption.return_value = mock_power_data
        mock_api_client.get_instance_pricing.return_value = 0.05

        with patch.object(self.tracker, "get_precise_runtime_hours", return_value=720.0):
            with patch.object(self.tracker, "get_cpu_utilization", return_value=50.0):
                result = self.tracker.process_instance_enhanced(
                    self.sample_instance, 350.0
                )

        self.assertIsInstance(result, EC2Instance)
        self.assertEqual(result.instance_id, "i-test123")
        self.assertGreater(result.monthly_cost_eur, 0)
        self.assertGreater(result.monthly_co2_kg, 0)

    @patch("src.api.client.unified_api_client")
    def test_process_instance_enhanced_missing_power(self, mock_api_client: Mock) -> None:
        mock_api_client.get_power_consumption.return_value = None
        mock_api_client.get_instance_pricing.return_value = 0.05

        with patch.object(self.tracker, "get_precise_runtime_hours", return_value=10.0):
            with patch.object(self.tracker, "get_cpu_utilization", return_value=50.0):
                result = self.tracker.process_instance_enhanced(self.sample_instance, 350.0)

        self.assertIsInstance(result, EC2Instance)
        self.assertIsNone(result.power_watts)
        self.assertEqual(result.data_quality, "partial")

    @patch("src.api.client.unified_api_client")
    def test_process_instance_enhanced_missing_cpu(self, mock_api_client: Mock) -> None:
        mock_power_data = Mock()
        mock_power_data.avg_power_watts = 15.0
        mock_api_client.get_power_consumption.return_value = mock_power_data
        mock_api_client.get_instance_pricing.return_value = 0.05

        with patch.object(self.tracker, "get_precise_runtime_hours", return_value=720.0):
            with patch.object(self.tracker, "get_cpu_utilization", return_value=None):
                result = self.tracker.process_instance_enhanced(
                    self.sample_instance, 350.0
                )

        self.assertIsInstance(result, EC2Instance)
        self.assertIsNone(result.power_watts)
        self.assertEqual(result.data_quality, "partial")

    def test_get_enhanced_confidence_metadata(self) -> None:
        confidence, sources = self.tracker._get_enhanced_confidence_metadata(
            has_power_data=True,
            has_pricing_data=True,
            has_cpu_data=True,
            has_runtime_data=True,
        )
        self.assertEqual(confidence, "high")
        self.assertCountEqual(
            sources,
            ["aws_api", "boavizta", "aws_pricing", "cloudwatch", "cloudtrail_audit"],
        )


if __name__ == "__main__":
    unittest.main()
