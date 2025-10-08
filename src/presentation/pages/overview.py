"""
Dashboard Overview Page
Professional SME-focused dashboard with German grid status and business value

This module orchestrates the overview page by composing reusable components.
All component logic has been extracted to src/presentation/components/ for better
maintainability and testability.
"""

import streamlit as st
from typing import Optional
from src.domain.models import DashboardData
from src.presentation.components import (
    render_grid_status,
    render_core_metrics,
    render_business_insights,
    render_validation_panel,
    extract_carbon_series,
)


def render_overview_page(dashboard_data: Optional[DashboardData]) -> None:
    """
    Render the dashboard overview page - SME focused.

    This page is composed of modular components that display:
    - Current grid status and core metrics (costs, CO₂)
    - Business case insights and CSRD readiness (in expander)
    - Carbon-aware scheduling insights
    - System health and data precision metrics

    Args:
        dashboard_data: Complete dashboard data object with instances and metrics
    """
    st.header("🏆 Dashboard Overview - Carbon-Aware FinOps")

    # Academic Disclaimer - prominent at top
    st.info("""
    ℹ️ **Academic Prototype - Research Dashboard**

    This tool is a research prototype developed for bachelor thesis purposes. Key considerations:

    - **Optimization calculations** require empirical validation in production environments
    - **Conservative estimates** with ±15% uncertainty range (literature-based: McKinsey [7], MIT [20])
    - **Theoretical scenarios** demonstrate methodology feasibility for SME use cases
    - **Development-scale adjustments** applied for small infrastructures (<€1/month)

    For detailed methodology, see [Documentation](https://github.com/your-repo/docs).
    """, icon="🎓")

    if not dashboard_data or not dashboard_data.instances:
        st.warning("⚠️ No infrastructure data available. Check API connections.")
        return

    # Development Environment Warning
    if dashboard_data.total_cost_eur < 1.0:
        st.warning("""
        ⚠️ **Development Environment Detected**

        Your infrastructure costs are below €1/month. Business case calculations
        use conservative quality modifiers for small-scale deployments.

        **Impact**: Savings estimates are calibrated for development scale and
        may not reflect production optimization potential. See [Calculator Documentation](../docs/methodology/calculations.md)
        for quality modifier logic.
        """, icon="🔬")

    # Extract carbon series for business insights
    carbon_series = extract_carbon_series(dashboard_data)

    # Core sections - simplified for SME decision makers
    render_grid_status(dashboard_data)
    render_core_metrics(dashboard_data)

    # Business case, CSRD readiness, and recommendations
    render_business_insights(dashboard_data, carbon_series)

    st.markdown("---")

    # System status and data quality
    render_validation_panel(dashboard_data)
