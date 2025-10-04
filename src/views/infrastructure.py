"""
Infrastructure Analytics Page
DevOps-focused infrastructure analytics with CloudTrail precision tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Any, Optional

from src.utils.performance import (
    render_4_column_metrics,
    optimize_chart_rendering
)
import plotly.graph_objects as go


def render_infrastructure_page(dashboard_data: Optional[Any]) -> None:
    """
    Render focused infrastructure analytics - core features only

    Args:
        dashboard_data: Complete dashboard data object with instances and metrics
    """
    st.header("🏗️ Infrastructure Analytics")

    with st.expander("ℹ️ What this page shows", expanded=False):
        st.markdown(
            """
            - Summarises runtime, power and cost metrics gathered from CloudTrail, Boavizta and AWS Pricing.
            - Highlights data-quality gaps following the strict NO-FALLBACK policy (⚠️ markers).
            - Provides a detailed instance table so FinOps and DevOps teams can trace CO₂ and cost calculations.
            """
        )

    if not dashboard_data or not dashboard_data.instances:
        st.warning("⚠️ No infrastructure data available. Check API connections.")
        return

    # Essential infrastructure overview
    _render_infrastructure_overview(dashboard_data)

    # Core feature: Instance Detail Table with all calculations
    _render_instance_detail_table(dashboard_data)


def _render_infrastructure_overview(dashboard_data: Any) -> None:
    """Render essential infrastructure metrics"""
    running_instances = len([i for i in dashboard_data.instances if i.state == "running"])
    total_instances = len(dashboard_data.instances)
    total_power = sum(i.power_watts for i in dashboard_data.instances if i.power_watts is not None)
    avg_cost_per_instance = dashboard_data.total_cost_eur / len(dashboard_data.instances) if dashboard_data.instances else 0

    # Essential metrics only
    infra_metrics = [
        ("🟢 Running Instances", f"{running_instances}", "Active infrastructure for calculations"),
        ("⚡ Total Power", f"{total_power:.0f}W", "Current consumption"),
        ("💰 Average Cost", f"€{avg_cost_per_instance:.0f}", "Per instance/month"),
        ("📊 Instance Types", f"{len(set(i.instance_type for i in dashboard_data.instances))}", "Different types")
    ]
    render_4_column_metrics(infra_metrics)


def _render_instance_detail_table(dashboard_data: Any) -> None:
    """Render detailed instance table with CO₂ formula components"""
    st.markdown("### 📊 Instance Detail Analysis")

    if not dashboard_data or not dashboard_data.instances:
        st.warning("No instance data available")
        return

    # Get carbon intensity for formula display
    grid_intensity = dashboard_data.carbon_intensity.value if dashboard_data.carbon_intensity else None

    # Prepare data for table
    table_data = []

    for instance in dashboard_data.instances:
        # Get CPU utilization with NO-FALLBACK transparency
        cpu_util = "⚠️ Not available"
        if hasattr(instance, 'cpu_utilization') and instance.cpu_utilization is not None:
            cpu_util = f"{instance.cpu_utilization:.1f}%"
        else:
            cpu_util = "⚠️ CloudWatch missing"

        # Get runtime data with NO-FALLBACK transparency
        runtime_hours = "⚠️ Not available"
        runtime_explanation = "CloudTrail data missing"
        data_quality_raw = getattr(instance, 'data_quality', 'limited') if hasattr(instance, 'data_quality') else 'limited'
        if hasattr(instance, 'runtime_hours') and instance.runtime_hours is not None:
            runtime_hours = f"{instance.runtime_hours:.1f}h"
            runtime_explanation = "CloudTrail data available"
        data_quality = data_quality_raw.lower()

        # CO₂ Formula Components: Power(kW) × Grid_Intensity(g/kWh) × Runtime(h) ÷ 1000 = kg CO₂
        power_kw = f"{instance.power_watts / 1000:.3f}" if instance.power_watts is not None else "N/A"
        grid_intensity_display = f"{grid_intensity:.0f}" if grid_intensity else "N/A"

        # Data quality badge
        if data_quality == "measured":
            quality_badge = "🟢 Measured"
        elif data_quality == "partial":
            quality_badge = "🟡 Partial"
        else:
            quality_badge = "🔴 Limited"

        table_data.append({
            "Instance Name": instance.instance_name or "Unnamed",
            "Type": instance.instance_type,
            "State": instance.state.title(),
            "Monthly Runtime (h)": runtime_hours,
            "CPU (%)": cpu_util,
            "Power (kW)": power_kw,
            "Grid Intensity (g/kWh)": grid_intensity_display,
            "CO₂/Month (kg)": f"{instance.monthly_co2_kg:.3f}" if instance.monthly_co2_kg is not None else "⚠️ Not available",
            "Cost/Month (€)": f"{instance.monthly_cost_eur:.2f}" if instance.monthly_cost_eur is not None else "⚠️ Not available",
            "Data Quality": quality_badge
        })

    if table_data:
        # Create DataFrame
        import pandas as pd
        df = pd.DataFrame(table_data)

        # Display table
        st.dataframe(df, width='stretch', hide_index=True)

        # NO-FALLBACK Policy explanation
        st.info("💡 **NO-FALLBACK Policy**: Only real API data is shown. "
                "Missing values (⚠️) indicate that no verifiable CloudTrail or CloudWatch readings are available. "
                "Estimated figures are omitted to preserve academic integrity.")

        # Summary insights
        total_cost = sum(i.monthly_cost_eur for i in dashboard_data.instances if i.monthly_cost_eur is not None)
        total_co2 = sum(i.monthly_co2_kg for i in dashboard_data.instances if i.monthly_co2_kg is not None)
        total_power = sum(i.power_watts for i in dashboard_data.instances if i.power_watts is not None)

        # Show calculation transparency
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Monthly Cost", f"€{total_cost:.2f}", "Sum of all instances")

        with col2:
            st.metric("Total Monthly CO₂", f"{total_co2:.2f} kg", "All instances combined")

        with col3:
            st.metric("Total Power Draw", f"{total_power:.0f} W", "Current consumption")

        # Show CO₂ calculation formula with transparency
        st.info("💡 **CO₂ Formula**: Power(kW) × Grid_Intensity(g/kWh) × Monthly_Runtime(h) ÷ 1000 = kg CO₂")

    else:
        st.error("No instance data available for detailed analysis")
