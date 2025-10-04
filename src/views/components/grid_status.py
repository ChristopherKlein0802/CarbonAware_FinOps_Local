"""
Grid Status Component
Displays current German grid carbon intensity with status indicators
"""

import streamlit as st
from typing import Optional
from src.models.dashboard import DashboardData
from src.utils.ui import determine_grid_status


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

    # Use centralized grid status logic
    status_color, status_text, _ = determine_grid_status(grid_status)

    # Compact display
    st.info(f"{status_color} **German Grid: {grid_status:.0f} g CO₂/kWh** ({status_text})")
