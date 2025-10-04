"""Unit tests for the runtime domain service."""

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from src.services.runtime import RuntimeService, RuntimeServiceConfig
from src.utils.errors import AWSAuthenticationError
from src.infrastructure.cache import FileCacheRepository
from src.infrastructure.clients import InfrastructureGateway
from src.infrastructure.clients.aws_runtime import AWSRuntimeGateway


class TestRuntimeService(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repository = FileCacheRepository(Path(self.tempdir.name))
        self.gateway = Mock(spec=InfrastructureGateway)
        self.runtime_gateway = Mock(spec=AWSRuntimeGateway)
        self.service = RuntimeService(
            RuntimeServiceConfig(aws_profile="test-profile"),
            repository=self.repository,
            infrastructure_gateway=self.gateway,
            runtime_gateway=self.runtime_gateway,
        )
        self.sample_instance = {
            "instance_id": "i-test123",
            "instance_type": "t3.medium",
            "state": "running",
            "region": "eu-central-1",
            "launch_time": datetime.now(timezone.utc) - timedelta(hours=5),
        }

    def test_list_instances_success(self) -> None:
        self.runtime_gateway.list_instances.return_value = [self.sample_instance]

        result = self.service.list_instances()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["instance_id"], "i-test123")
        self.runtime_gateway.list_instances.assert_called_once()

    def test_list_instances_auth_error_translated(self) -> None:
        self.runtime_gateway.list_instances.side_effect = AWSAuthenticationError("expired")

        with self.assertRaises(AWSAuthenticationError):
            self.service.list_instances()

    def test_list_instances_generic_error_returns_empty(self) -> None:
        self.runtime_gateway.list_instances.side_effect = Exception("boom")
        self.assertEqual(self.service.list_instances(), [])

    def test_get_precise_runtime_hours_uses_cache(self) -> None:
        cache_path = self.repository.path("cloudtrail_runtime", f"{self.sample_instance['instance_id']}_{self.sample_instance['region']}")
        self.repository.write_json(cache_path, {"runtime_hours": 12.5})
        runtime = self.service._get_precise_runtime_hours(self.sample_instance)
        self.assertEqual(runtime, 12.5)

    def test_get_precise_runtime_hours_from_events(self) -> None:
        now = datetime.now(timezone.utc)
        events = [
            {
                "EventName": "StartInstances",
                "EventTime": now - timedelta(hours=4),
                "Resources": [{"ResourceName": "i-test123"}],
            },
            {
                "EventName": "StopInstances",
                "EventTime": now - timedelta(hours=2),
                "Resources": [{"ResourceName": "i-test123"}],
            },
        ]
        self.runtime_gateway.lookup_instance_events.return_value = events

        runtime = self.service._get_precise_runtime_hours(self.sample_instance, force_refresh=True)

        self.assertGreater(runtime, 0.0)

    def test_get_cpu_utilization_fresh(self) -> None:
        self.runtime_gateway.fetch_cpu_metrics.return_value = [{"Values": [30.0, 40.0, 50.0]}]

        cpu_util = self.service._get_cpu_utilisation("i-test123", force_refresh=True)

        self.assertEqual(cpu_util, 40.0)

    def test_resolve_data_quality(self) -> None:
        quality = self.service._resolve_data_quality(10.0, 50.0, 100.0, 20.0)
        self.assertEqual(quality, "measured")
        quality = self.service._resolve_data_quality(10.0, None, None, None)
        self.assertEqual(quality, "partial")
        quality = self.service._resolve_data_quality(None, None, None, None)
        self.assertEqual(quality, "limited")


if __name__ == '__main__':
    unittest.main()
