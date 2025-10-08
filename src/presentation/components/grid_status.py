"""
Grid Status Component
Displays current German grid carbon intensity with status indicators
"""

import streamlit as st
from typing import Optional, Tuple
from src.domain.models import DashboardData


def determine_grid_status(intensity: float) -> Tuple[str, str, str]:
    """
    Determine grid status from carbon intensity value.

    Args:
        intensity: Carbon intensity in g CO₂/kWh

    Returns:
        Tuple of (emoji, status_text, color)
    """
    if intensity < 200:
        return "🟢", "Low Carbon", "green"
    elif intensity < 400:
        return "🟡", "Moderate Carbon", "orange"
    else:
        return "🔴", "High Carbon", "red"


def render_grid_status(dashboard_data: Optional[DashboardData]) -> None:
    """
    Render compact German Grid Status widget.

    Args:
        dashboard_data: Complete dashboard data with carbon intensity
    """
    if not dashboard_data or not dashboard_data.carbon_intensity:
        st.warning("⚠️ No carbon intensity data available")
        return

    grid_status = dashboard_data.carbon_intensity.value

    # Determine grid status
    status_color, status_text, _ = determine_grid_status(grid_status)

    # Compact display
    st.info(f"{status_color} **German Grid: {grid_status:.0f} g CO₂/kWh** ({status_text})")
