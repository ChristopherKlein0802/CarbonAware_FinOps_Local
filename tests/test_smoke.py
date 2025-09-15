#!/usr/bin/env python3
"""
Smoke Tests for Carbon-Aware FinOps Dashboard
Bachelor Thesis - Essential functionality verification

Basic smoke tests to ensure all modules can be imported and initialized.
Perfect for continuous integration and quick validation.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_api_client():
    """Test that API client can be imported and initialized"""
    try:
        from src.api_client import UnifiedAPIClient
        client = UnifiedAPIClient()
        assert client is not None

        # Check essential methods exist
        assert hasattr(client, 'get_current_carbon_intensity')
        assert hasattr(client, 'get_power_consumption')
        assert hasattr(client, 'get_monthly_costs')

    except ImportError as e:
        pytest.fail(f"Failed to import API client: {e}")


def test_import_data_processor():
    """Test that data processor can be imported and initialized"""
    try:
        from src.data_processor import DataProcessor
        processor = DataProcessor()
        assert processor is not None

        # Check essential methods exist
        assert hasattr(processor, 'get_infrastructure_data')

    except ImportError as e:
        pytest.fail(f"Failed to import data processor: {e}")


def test_import_health_monitor():
    """Test that health monitor can be imported and initialized"""
    try:
        from src.health_monitor import HealthMonitor
        monitor = HealthMonitor()
        assert monitor is not None

        # Check essential methods exist
        assert hasattr(monitor, 'check_all_apis')

    except ImportError as e:
        pytest.fail(f"Failed to import health monitor: {e}")


def test_import_models():
    """Test that all data models can be imported"""
    try:
        from src.models import EC2Instance, BusinessCase, DashboardData, APIHealthStatus

        # Test model creation
        instance = EC2Instance(
            instance_id="test-123",
            instance_type="t3.micro",
            state="running",
            region="eu-central-1"
        )
        assert instance.instance_id == "test-123"

        business_case = BusinessCase(
            baseline_cost_eur=100.0,
            baseline_co2_kg=50.0
        )
        assert business_case.baseline_cost_eur == 100.0

    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")


def test_import_pages():
    """Test that pages module can be imported"""
    try:
        from src.pages import (
            render_overview_page,
            render_infrastructure_page,
            render_carbon_page,
            render_research_methods_page
        )

        # All page render functions should exist
        assert callable(render_overview_page)
        assert callable(render_infrastructure_page)
        assert callable(render_carbon_page)
        assert callable(render_research_methods_page)

    except ImportError as e:
        pytest.fail(f"Failed to import pages: {e}")


def test_main_app_import():
    """Test that main app can be imported"""
    try:
        from src.app import main, load_custom_css, load_infrastructure_data

        assert callable(main)
        assert callable(load_custom_css)
        assert callable(load_infrastructure_data)

    except ImportError as e:
        pytest.fail(f"Failed to import main app: {e}")


def test_data_models_structure():
    """Test that data models have expected structure"""
    from src.models import EC2Instance, BusinessCase, DashboardData

    # Test EC2Instance
    instance = EC2Instance(
        instance_id="i-123456789",
        instance_type="t3.small",
        state="running",
        region="eu-central-1"
    )

    assert instance.instance_id == "i-123456789"
    assert instance.instance_type == "t3.small"
    assert instance.state == "running"
    assert instance.region == "eu-central-1"
    assert instance.data_sources == []  # Should initialize as empty list

    # Test BusinessCase
    business_case = BusinessCase(
        baseline_cost_eur=200.0,
        baseline_co2_kg=100.0,
        office_hours_savings_eur=50.0
    )

    assert business_case.baseline_cost_eur == 200.0
    assert business_case.office_hours_savings_eur == 50.0
    assert business_case.confidence_interval == 0.15  # Default value

    # Test DashboardData
    dashboard_data = DashboardData(
        instances=[instance],
        total_cost_eur=200.0,
        total_co2_kg=100.0
    )

    assert len(dashboard_data.instances) == 1
    assert dashboard_data.total_cost_eur == 200.0
    assert dashboard_data.uncertainty_ranges == {}  # Should initialize as empty dict


def test_api_client_initialization():
    """Test API client initializes without errors"""
    from src.api_client import UnifiedAPIClient

    # Should initialize without throwing exceptions
    client = UnifiedAPIClient()

    # Should have essential methods (not checking internal attributes)
    assert hasattr(client, 'get_current_carbon_intensity')
    assert hasattr(client, 'get_power_consumption')


def test_data_processor_initialization():
    """Test data processor initializes correctly"""
    from src.data_processor import DataProcessor

    processor = DataProcessor()

    # Should have essential methods (not checking internal attributes)
    assert hasattr(processor, 'get_infrastructure_data')


def test_health_monitor_initialization():
    """Test health monitor initializes correctly"""
    from src.health_monitor import HealthMonitor

    monitor = HealthMonitor()

    # Should initialize without errors
    assert monitor is not None


def test_essential_constants():
    """Test that essential constants are defined"""
    from src.api_client import REGION_MAPPINGS

    # Should have region mappings
    assert isinstance(REGION_MAPPINGS, dict)
    assert 'eu-central-1' in REGION_MAPPINGS
    assert REGION_MAPPINGS['eu-central-1'] == 'DE'


if __name__ == "__main__":
    # Run basic tests without pytest
    print("🧪 Running smoke tests...")

    try:
        test_import_api_client()
        print("✅ API client import: PASSED")

        test_import_data_processor()
        print("✅ Data processor import: PASSED")

        test_import_health_monitor()
        print("✅ Health monitor import: PASSED")

        test_import_models()
        print("✅ Models import: PASSED")

        test_import_pages()
        print("✅ Pages import: PASSED")

        test_main_app_import()
        print("✅ Main app import: PASSED")

        test_data_models_structure()
        print("✅ Data models structure: PASSED")

        test_api_client_initialization()
        print("✅ API client initialization: PASSED")

        test_data_processor_initialization()
        print("✅ Data processor initialization: PASSED")

        test_health_monitor_initialization()
        print("✅ Health monitor initialization: PASSED")

        test_essential_constants()
        print("✅ Essential constants: PASSED")

        print("\n🎉 All smoke tests PASSED!")

    except Exception as e:
        print(f"\n❌ Smoke test FAILED: {e}")
        sys.exit(1)