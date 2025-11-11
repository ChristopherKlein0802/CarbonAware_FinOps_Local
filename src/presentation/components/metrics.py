"""
Core Metrics Component
Displays monthly costs and carbon footprint with quality indicators
"""

import streamlit as st
from typing import Optional
from src.domain.models import DashboardData
from src.presentation.utils import get_period_label


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
    period_label = get_period_label(period_days, format_type="long")

    st.markdown("### 📊 Core Metrics")
    st.caption(f"{period_label.title()} costs and carbon emissions for monitored infrastructure")

    # Use primary field names (average-based method as default)
    total_cost = dashboard_data.total_cost_average
    total_co2 = dashboard_data.total_co2_average

    # Data quality assessment
    num_instances = len(dashboard_data.instances) if dashboard_data.instances else 0
    cost_quality = "🟢 Calculated" if total_cost > 0 else "🔴 No Data"
    co2_quality = "🟢 Real API" if total_co2 > 0 else "🔴 No Data"

    # Check data sources
    has_real_cost = dashboard_data.total_cost_average > 0
    has_carbon_data = dashboard_data.carbon_intensity is not None

    # Core metrics with quality badges
    col1, col2, col3 = st.columns(3)

    with col1:
        instance_label = f"{num_instances} instance{'s' if num_instances != 1 else ''}"
        st.metric(
            f"💰 {period_label.title()} Costs",
            f"€{total_cost:.2f}",
            f"{instance_label}",
            help=f"**Calculation Method**: Average Runtime Based\n\n"
                 f"Instance-specific costs calculated from CloudTrail runtime data over {period_days} days × AWS Pricing API on-demand rates.\n\n"
                 f"**Includes**: EC2 instance compute hours only\n"
                 f"**Excludes**: Reserved instance discounts, data transfer, EBS costs, EBS-optimized charges\n\n"
                 f"For full AWS billing comparison, see Cost Explorer metric below."
        )
        if not has_real_cost:
            st.warning("⚠️ No cost data - check AWS Pricing API")

    with col2:
        st.metric(
            f"🌍 {period_label.title()} Carbon",
            f"{total_co2:.2f} kg CO₂",
            f"{co2_quality}",
            help=f"**Calculation Method**: Average Runtime Based\n\n"
                 f"Carbon emissions calculated over {period_days} days using:\n"
                 f"• Power consumption (Boavizta hardware models)\n"
                 f"• Runtime hours (CloudTrail tracking)\n"
                 f"• Grid intensity (ElectricityMaps German grid)\n\n"
                 f"**Formula**: CO₂(kg) = Power(kW) × Intensity(g/kWh) × Runtime(h) ÷ 1000\n\n"
                 f"Updated hourly. See Infrastructure Details for 24h-Pattern Based comparison."
        )
        if not has_carbon_data:
            st.warning("⚠️ No carbon data - check ElectricityMaps API")

    with col3:
        # Cost Explorer comparison - only show for periods >= 7 days due to 24h billing lag
        period_days = getattr(dashboard_data, "analysis_period_days", 30)

        if period_days >= 7:
            # Show Cost Explorer for longer periods (billing lag is acceptable)
            cost_explorer_eur = getattr(dashboard_data, "cost_explorer_eur", None)
            validation_factor = getattr(dashboard_data, "validation_factor", None)

            # Type-safe validation: ensure it's a number
            if cost_explorer_eur is not None and isinstance(cost_explorer_eur, (int, float)) and cost_explorer_eur > 0:
                # Show actual Cost Explorer value
                delta_pct = ((validation_factor - 1.0) * 100) if validation_factor and validation_factor != 1.0 else None
                delta_text = f"{delta_pct:+.0f}% vs calculated" if delta_pct else None

                st.metric(
                    "📊 Cost Explorer",
                    f"€{cost_explorer_eur:.2f}",
                    delta_text,
                    help=f"AWS Cost Explorer total EC2 costs for {period_label} period (all charges: instances + data transfer + EBS-optimized + storage). "
                         f"Validation factor: {validation_factor:.2f}x calculated costs. "
                         "Higher values are normal due to additional EC2 service charges not tracked by CloudTrail."
                )
            else:
                st.metric(
                    "📊 Cost Explorer",
                    "Calculating...",
                    "Fetching data",
                    help="AWS Cost Explorer total EC2 costs for validation. Updates daily, cached for 24 hours."
                )
        else:
            # Cost Explorer unavailable for short periods (24h billing lag makes data unreliable)
            st.info(
                f"📊 **Cost Explorer Unavailable**\n\n"
                f"AWS Cost Explorer has a **24-hour billing lag** and is not shown for {period_days}-day periods.\n\n"
                f"**Impact:** {period_days}-day period = {(1/period_days)*100:.0f}% incomplete data\n\n"
                f"💡 Use **7-day** (14% lag) or **30-day** (3% lag) periods for Cost Explorer validation."
            )
