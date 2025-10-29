"""
Core Metrics Component
Displays monthly costs and carbon footprint with quality indicators
"""

import streamlit as st
from typing import Optional
from src.domain.models import DashboardData


def render_core_metrics(dashboard_data: Optional[DashboardData]) -> None:
    """
    Render core business metrics - simplified for SME.

    Args:
        dashboard_data: Complete dashboard data with cost and CO₂ metrics
    """
    if not dashboard_data:
        st.warning("⚠️ No data available")
        return

    # Get analysis period
    period_days = getattr(dashboard_data, "analysis_period_days", 30)
    period_label = f"{period_days}-day" if period_days < 30 else "monthly"

    st.markdown("### 📊 Core Metrics")
    st.caption(f"{period_label.title()} costs and carbon emissions for monitored infrastructure")

    # Use new field names with fallback for backward compatibility
    total_cost = getattr(dashboard_data, "total_cost_average", dashboard_data.total_cost_eur)
    total_co2 = getattr(dashboard_data, "total_co2_average", dashboard_data.total_co2_kg)

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
        instance_label = f"{num_instances} instance{'s' if num_instances != 1 else ''}"
        st.metric(
            f"💰 {period_label.title()} Costs",
            f"€{total_cost:.2f}",
            f"{instance_label}",
            help=f"Instance-specific costs calculated from CloudTrail runtime data over {period_days} days × AWS Pricing API on-demand rates. "
                 "Covers only monitored EC2 instances. Excludes reserved instances discounts, data transfer, and EBS costs. "
                 "For full AWS billing, see Cost Explorer metric."
        )
        if not has_real_cost:
            st.warning("⚠️ No cost data - check AWS Pricing API")

    with col2:
        st.metric(
            f"🌍 {period_label.title()} Carbon",
            f"{total_co2:.2f} kg CO₂",
            f"{co2_quality}",
            help=f"Carbon emissions calculated over {period_days} days using: Power consumption (Boavizta hardware models) × Runtime (CloudTrail) × "
                 "Grid intensity (ElectricityMaps German grid). Updated hourly. Formula: CO₂(kg) = Power(kW) × Intensity(g/kWh) × Runtime(h) ÷ 1000"
        )
        if not has_carbon_data:
            st.warning("⚠️ No carbon data - check ElectricityMaps API")

    with col3:
        # Cost Explorer comparison
        validation_factor = getattr(dashboard_data, "validation_factor", None)
        # Type-safe validation: ensure it's a number
        if not isinstance(validation_factor, (int, float)):
            validation_factor = None

        if validation_factor and validation_factor > 0:
            ce_cost = total_cost * validation_factor
            st.metric(
                "📊 Cost Explorer",
                f"€{ce_cost:.2f}",
                "All EC2 charges",
                help="AWS Cost Explorer total EC2 costs (all charges: instances + data transfer + EBS-optimized + storage). "
                     "Used for validation against calculated costs. Higher values are normal due to additional EC2 service charges not tracked by CloudTrail."
            )
        else:
            st.metric(
                "📊 Cost Explorer",
                "Calculating...",
                "Fetching data",
                help="AWS Cost Explorer total EC2 costs for validation. Updates daily, cached for 24 hours."
            )
