"""
Pytest Configuration and Fixtures for Carbon-Aware FinOps Dashboard Tests
Academic-grade test setup and shared fixtures
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_carbon_intensity_data():
    """Mock carbon intensity data for testing"""
    return {"value": 250.5, "timestamp": "2024-01-15T14:30:00Z", "region": "DE", "source": "electricitymap_api"}


@pytest.fixture
def mock_ec2_instance_data():
    """Mock EC2 instance data for testing (v2.0.0 fields)"""
    return {
        "instance_id": "i-1234567890abcdef0",
        "instance_type": "t3.medium",
        "state": "running",
        "region": "eu-central-1",
        "launch_time": datetime.now() - timedelta(hours=5),
        "power_watts": 45.2,
        "co2_kg_average": 12.5,
        "cost_eur_average": 67.50,
        "co2_kg_hourly": 13.2,
        "cost_eur_hourly": 69.00,
        "period_days": 30,
        "confidence_level": "high",
        "data_sources": ["aws_api", "boavizta", "cloudtrail_audit"],
    }


@pytest.fixture
def mock_power_consumption_data():
    """Mock power consumption data from Boavizta"""
    return {
        "min_power_watts": 30.0,
        "avg_power_watts": 45.0,
        "max_power_watts": 85.0,
        "confidence_level": "high",
        "source": "boavizta_api",
    }


@pytest.fixture
def mock_aws_cost_data():
    """Mock AWS Cost Explorer data"""
    return {
        "total_cost_usd": 1250.75,
        "ec2_cost_usd": 890.50,
        "data_transfer_cost_usd": 125.25,
        "storage_cost_usd": 235.00,
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
    }


@pytest.fixture
def mock_business_case_data():
    """Mock business case calculation data"""
    return {
        "baseline_cost_eur": 2500.00,
        "baseline_co2_kg": 450.75,
        "office_hours_savings_eur": 500.00,
        "carbon_aware_savings_eur": 250.00,
        "integrated_savings_eur": 750.00,
        "payback_months": 3.2,
        "implementation_cost_eur": 2400.00,
    }


@pytest.fixture
def mock_cloudtrail_events():
    """Mock CloudTrail events for testing"""
    return [
        {
            "EventTime": datetime.now() - timedelta(hours=24),
            "EventName": "RunInstances",
            "Resources": [{"ResourceName": "i-1234567890abcdef0"}],
        },
        {
            "EventTime": datetime.now() - timedelta(hours=12),
            "EventName": "StopInstances",
            "Resources": [{"ResourceName": "i-1234567890abcdef0"}],
        },
        {
            "EventTime": datetime.now() - timedelta(hours=6),
            "EventName": "StartInstances",
            "Resources": [{"ResourceName": "i-1234567890abcdef0"}],
        },
    ]


@pytest.fixture
def mock_api_responses():
    """Mock API responses for external services"""
    return {
        "electricitymap": {"carbonIntensity": 250.5, "datetime": "2024-01-15T14:30:00Z", "zone": "DE"},
        "boavizta": {"impacts": {"pe": {"use": {"value": 45.0, "unit": "MJ"}}}},
        "aws_pricing": {
            "products": {
                "product1": {"attributes": {"instanceType": "t3.medium", "operatingSystem": "Linux"}, "sku": "TEST123"}
            },
            "terms": {
                "OnDemand": {
                    "TEST123": {
                        "termAttributes": {},
                        "priceDimensions": {"dimension1": {"pricePerUnit": {"USD": "0.0416"}}},
                    }
                }
            },
        },
    }


@pytest.fixture
def mock_cache_directory(tmp_path):
    """Create a temporary cache directory for testing"""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock environment variables for testing"""
    with patch.dict(
        os.environ,
        {
            "ELECTRICITYMAP_API_KEY": "test-electricity-key",
            "AWS_PROFILE": "carbon-finops-sandbox",  # Use same profile as production
            "AWS_DEFAULT_REGION": "eu-central-1",
        },
    ):
        yield


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    return MagicMock()


@pytest.fixture
def academic_test_config():
    """Configuration for academic testing standards"""
    return {
        "no_fallback_policy": True,
        "precision_requirements": {
            "carbon_intensity": 0.1,  # ±0.1 g CO2/kWh
            "cost_calculation": 0.01,  # ±€0.01
            "power_consumption": 0.1,  # ±0.1W
        },
        "timeout_limits": {"api_calls": 30, "cache_operations": 5},  # seconds  # seconds
        "confidence_thresholds": {"high": 0.8, "medium": 0.5, "low": 0.2},
    }


@pytest.fixture
def mock_streamlit_cache():
    """Mock Streamlit caching for testing"""

    def mock_cache_decorator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    with patch("streamlit.cache_data", mock_cache_decorator), patch("streamlit.cache_resource", mock_cache_decorator):
        yield


class AcademicTestCase:
    """Base class for academic testing standards"""

    def assert_no_fallback_policy(self, result):
        """Assert that NO-FALLBACK policy is enforced"""
        if result is None:
            return  # None is acceptable for NO-FALLBACK

        # Check that no synthetic/fallback data is present
        if hasattr(result, "source"):
            assert "fallback" not in result.source.lower()
            assert "synthetic" not in result.source.lower()
            assert "default" not in result.source.lower()

    def assert_academic_precision(self, actual, expected, precision, context=""):
        """Assert values meet academic precision requirements"""
        if actual is None or expected is None:
            assert actual == expected, f"Academic precision check failed for {context}"
        else:
            assert (
                abs(actual - expected) <= precision
            ), f"Academic precision check failed for {context}: {actual} vs {expected} (±{precision})"

    def assert_confidence_level(self, confidence, minimum_threshold=0.5):
        """Assert confidence level meets academic standards"""
        if confidence is not None:
            assert 0.0 <= confidence <= 1.0, "Confidence must be between 0 and 1"
            assert (
                confidence >= minimum_threshold
            ), f"Confidence {confidence} below minimum threshold {minimum_threshold}"


# Make AcademicTestCase available for all tests
@pytest.fixture
def academic_test():
    """Provide academic testing utilities"""
    return AcademicTestCase()
