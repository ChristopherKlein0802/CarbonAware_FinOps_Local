"""
Executive Summary / Overview Page
Professional SME-focused dashboard with German grid status and business value

This module orchestrates the overview page by composing reusable components.
All component logic has been extracted to src/views/components/ for better
maintainability and testability.
"""

import streamlit as st
from typing import Optional
from src.models.dashboard import DashboardData
from .components import (
    render_grid_status,
    render_core_metrics,
    render_business_insights,
    render_validation_panel,
    render_time_series_charts,
    extract_carbon_series,
)


def render_overview_page(dashboard_data: Optional[DashboardData]) -> None:
    """
    Render the executive summary overview page - SME focused.

    This page is composed of modular components that display:
    - Current grid status and core metrics (costs, CO₂)
    - Business case insights and CSRD readiness
    - Cost/carbon alignment charts
    - System health and data precision metrics

    Args:
        dashboard_data: Complete dashboard data object with instances and metrics
    """
    st.header("🏆 Executive Summary - Carbon-Aware FinOps")

    if not dashboard_data or not dashboard_data.instances:
        st.warning("⚠️ No infrastructure data available. Check API connections.")
        return

    # Extract carbon series for business insights
    carbon_series = extract_carbon_series(dashboard_data)

    # Core sections - simplified for SME decision makers
    render_grid_status(dashboard_data)
    render_core_metrics(dashboard_data)

    # Business case, CSRD readiness, and recommendations
    render_business_insights(dashboard_data, carbon_series)

    # Cost/Carbon alignment visualization
    render_time_series_charts(dashboard_data)

    st.markdown("---")

    # System status and data quality
    render_validation_panel(dashboard_data)
