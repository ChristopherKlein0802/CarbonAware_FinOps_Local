"""Integration tests for the end-to-end data pipeline."""

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pytest

from src.application.orchestrator import DashboardDataOrchestrator


ARTIFACT_DIR = Path("artifacts/integration")


def _secrets_available() -> bool:
    """Check required environment variables for live API calls."""
    electricity_api = os.getenv("ELECTRICITYMAP_API_KEY")
    aws_profile = os.getenv("AWS_PROFILE", "carbon-finops-sandbox")
    return bool(electricity_api and aws_profile)


def _prepare_artifact_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    target = ARTIFACT_DIR / timestamp
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.mark.integration
def test_full_pipeline_runs_and_exports_artifacts():
    """Run DashboardDataOrchestrator with live dependencies and export artefacts."""
    if not _secrets_available():
        pytest.skip("Integration secrets unavailable; set ELECTRICITYMAP_API_KEY and AWS_PROFILE")

    processor = DashboardDataOrchestrator()
    dashboard_data = processor.get_infrastructure_data()

    assert dashboard_data is not None, "DashboardDataOrchestrator returned no data"

    # Integration test may return no data if no AWS resources exist
    # This is expected behavior - verify structure instead
    if dashboard_data.carbon_intensity is None:
        pytest.skip("No carbon intensity data available (expected if no AWS resources or API rate limits)")

    # If carbon intensity exists, verify structure
    assert dashboard_data.carbon_intensity.value > 0, "Invalid carbon intensity value"

    artifact_dir = _prepare_artifact_dir()
    payload_path = artifact_dir / "dashboard_data.json"
    with payload_path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(dashboard_data), fh, default=str, indent=2)

    def _serialise_api_health(statuses):
        serialised = {}
        for service, status in (statuses or {}).items():
            serialised[service] = {
                "service": status.service,
                "status": status.status,
                "response_time_ms": status.response_time_ms,
                "last_check": status.last_check.isoformat() if status.last_check else None,
                "error_message": status.error_message,
                "healthy": status.healthy,
                "last_api_call": status.last_api_call.isoformat() if status.last_api_call else None,
            }
        return serialised

    summary = {
        "timestamp": datetime.now().isoformat(),
        "instances": len(dashboard_data.instances or []),
        "carbon_intensity_available": dashboard_data.carbon_intensity is not None,
        "api_health_status": _serialise_api_health(dashboard_data.api_health_status),
        "academic_disclaimers": dashboard_data.academic_disclaimers,
    }
    summary_path = artifact_dir / "metadata.json"
    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    assert payload_path.exists(), "Dashboard artefact not created"
    assert summary_path.exists(), "Metadata artefact not created"
