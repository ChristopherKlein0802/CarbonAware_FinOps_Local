"""
Helper utilities for view components
"""

from datetime import datetime, timezone
from typing import Optional
from src.domain.models import DashboardData


def extract_carbon_series(dashboard_data: Optional[DashboardData]) -> list[tuple[datetime, float]]:
    """
    Normalise the latest carbon history already provided via DashboardData.

    Args:
        dashboard_data: Dashboard data with carbon history

    Returns:
        List of (timestamp, carbon_intensity) tuples sorted by timestamp
    """
    if not dashboard_data:
        return []

    historical_data = getattr(dashboard_data, "carbon_history", None) or []
    if not historical_data:
        historical_data = getattr(dashboard_data, "self_collected_carbon_history", None) or []

    if not historical_data:
        return []

    normalized_points: dict[datetime, float] = {}
    for point in historical_data:
        timestamp_raw = point.get("datetime") or point.get("hour_key")
        if not timestamp_raw:
            continue

        try:
            ts = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        value = point.get("carbonIntensity") or point.get("value")
        if value is None:
            continue
        try:
            normalized_points[ts] = float(value)
        except (TypeError, ValueError):
            continue

    sorted_points = sorted((ts.astimezone(), value) for ts, value in normalized_points.items())
    return sorted_points
