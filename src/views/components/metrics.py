"""
Core Metrics Component
Displays monthly costs and carbon footprint with quality indicators
"""

import streamlit as st
from typing import Optional
from src.models.dashboard import DashboardData


def render_core_metrics(dashboard_data: Optional[DashboardData]) -> None:
    """
    Render core business metrics - simplified for SME.

    Args:
        dashboard_data: Complete dashboard data with cost and CO₂ metrics
    """
    if not dashboard_data:
        st.warning("⚠️ No data available")
        return

    total_cost = dashboard_data.total_cost_eur
    total_co2 = dashboard_data.total_co2_kg

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - **Monthly costs** calculated from CloudTrail runtime × AWS Pricing API for monitored instances only.
            - **Carbon footprint** combines ElectricityMaps intensity with Boavizta power models.
            - Cost Explorer comparison available in Validation Panel below.
            """
        )

    # Data quality assessment
    num_instances = len(dashboard_data.instances) if dashboard_data.instances else 0
    cost_quality = "🟢 Calculated" if total_cost > 0 else "🔴 No Data"
    co2_quality = "🟢 Real API" if total_co2 > 0 else "🔴 No Data"

    # Check data sources
    has_real_cost = dashboard_data.total_cost_eur > 0
    has_carbon_data = dashboard_data.carbon_intensity is not None

    # Core metrics with quality badges
    col1, col2, col3 = st.columns(3)

    with col1:
        instance_label = f"{num_instances} monitored instance{'s' if num_instances != 1 else ''}"
        st.metric("💰 Monthly Costs (Calculated)", f"€{total_cost:.2f}", f"{instance_label} - {cost_quality}")
        if not has_real_cost:
            st.warning("⚠️ No cost data available")

    with col2:
        st.metric("🌍 Carbon Footprint", f"{total_co2:.2f} kg CO₂", f"ElectricityMaps+Boavizta - {co2_quality}")
        if not has_carbon_data:
            st.warning("⚠️ No real carbon data")

    with col3:
        # Cost Explorer comparison
        validation_factor = getattr(dashboard_data, 'validation_factor', None)
        if validation_factor and validation_factor > 0:
            ce_cost = total_cost * validation_factor
            st.metric("📊 Cost Explorer (Total)", f"€{ce_cost:.2f}", f"All EC2 services - 🟢 Real API")
        else:
            st.metric("📊 Cost Explorer (Total)", "–", "Fetching...")
