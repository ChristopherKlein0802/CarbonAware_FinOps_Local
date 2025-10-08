"""
Infrastructure Analytics Page
DevOps-focused infrastructure analytics with CloudTrail precision tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Optional


def render_infrastructure_page(dashboard_data: Optional[Any]) -> None:
    """
    Render focused infrastructure analytics - core features only

    Args:
        dashboard_data: Complete dashboard data object with instances and metrics
    """
    st.header("🏗️ Infrastructure Analytics")
    st.caption("Instance-level cost and carbon analysis with CloudTrail precision tracking")

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
    avg_cost_per_instance = (
        dashboard_data.total_cost_eur / len(dashboard_data.instances) if dashboard_data.instances else 0
    )

    # Essential metrics only
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🟢 Running Instances",
            f"{running_instances}/{total_instances}",
            "Active now",
            help="Number of running EC2 instances out of total monitored. Only running instances consume power and generate costs. "
                 "Stopped instances are tracked but show zero power consumption."
        )

    with col2:
        st.metric(
            "⚡ Total Power",
            f"{total_power:.0f}W",
            "Current draw",
            help="Sum of power consumption across all running instances. Calculated using Boavizta hardware models with "
                 "CPU-based scaling: Power = Base × (30% idle + 70% × CPU utilization). Based on Barroso & Hölzle (2007) energy model."
        )

    with col3:
        st.metric(
            "💰 Avg Cost/Instance",
            f"€{avg_cost_per_instance:.2f}",
            "Per month",
            help="Average monthly cost per instance (total cost ÷ instance count). Useful for comparing instance efficiency. "
                 "Calculated from CloudTrail runtime × AWS Pricing API on-demand rates."
        )

    with col4:
        st.metric(
            "📊 Instance Types",
            f"{len(set(i.instance_type for i in dashboard_data.instances))}",
            "Unique types",
            help="Number of distinct EC2 instance types in your infrastructure. Diversity indicator for right-sizing opportunities. "
                 "Common types: t3.micro (dev), t3.medium (apps), m5.large (prod)."
        )


def _prepare_instance_row_data(instance: Any, grid_intensity: Optional[float]) -> dict[str, str]:
    """
    Prepare table row data for a single instance.

    Args:
        instance: EC2Instance object
        grid_intensity: Current grid carbon intensity (g CO₂/kWh)

    Returns:
        Dictionary with formatted instance data for table display
    """
    # Get CPU utilization with NO-FALLBACK transparency
    cpu_util = "⚠️ CloudWatch missing"
    if hasattr(instance, "cpu_utilization") and instance.cpu_utilization is not None:
        cpu_util = f"{instance.cpu_utilization:.1f}%"

    # Get runtime data with NO-FALLBACK transparency
    runtime_hours = "⚠️ Not available"
    if hasattr(instance, "runtime_hours") and instance.runtime_hours is not None:
        runtime_hours = f"{instance.runtime_hours:.1f}h"

    # Data quality badge
    data_quality = getattr(instance, "data_quality", "limited").lower()
    quality_badge = {
        "measured": "🟢 Measured",
        "partial": "🟡 Partial",
    }.get(data_quality, "🔴 Limited")

    # Formatted values
    power_kw = f"{instance.power_watts / 1000:.3f}" if instance.power_watts is not None else "N/A"
    grid_intensity_display = f"{grid_intensity:.0f}" if grid_intensity else "N/A"
    co2_display = f"{instance.monthly_co2_kg:.3f}" if instance.monthly_co2_kg is not None else "⚠️ Not available"
    cost_display = f"{instance.monthly_cost_eur:.2f}" if instance.monthly_cost_eur is not None else "⚠️ Not available"

    return {
        "Instance Name": instance.instance_name or "Unnamed",
        "Type": instance.instance_type,
        "State": instance.state.title(),
        "Monthly Runtime (h)": runtime_hours,
        "CPU (%)": cpu_util,
        "Power (kW)": power_kw,
        "Grid Intensity (g/kWh)": grid_intensity_display,
        "CO₂/Month (kg)": co2_display,
        "Cost/Month (€)": cost_display,
        "Data Quality": quality_badge,
    }


def _render_calculation_methodology_expander() -> None:
    """Render calculation methodology documentation in expander."""
    with st.expander("📐 Calculation Methodology", expanded=False):
        st.markdown("""
        **Power Consumption Model** (Barroso & Hölzle 2007):
        ```
        Effective Power = Base Power × (30% idle + 70% × CPU%)
        ```
        - **30% idle load**: Mainboard, memory, cooling (constant)
        - **70% variable load**: CPU-dependent, scales linearly
        - **Source**: Boavizta API (hardware power models)

        **CO₂ Emissions Calculation** (IEA/GHG Protocol):
        ```
        CO₂ (kg) = Power (kW) × Carbon Intensity (g/kWh) × Runtime (h) ÷ 1000
        ```
        - **Power**: From model above
        - **Carbon Intensity**: ElectricityMaps (German grid, hourly updates)
        - **Runtime**: CloudTrail Start/Stop events (±5% accuracy)

        **NO-FALLBACK Policy**:
        - Instances without CPU data show "⚠️ CloudWatch missing"
        - No artificial defaults to maintain scientific integrity
        - Missing data reduces power calculation accuracy
        """)


def _render_summary_metrics(dashboard_data: Any) -> None:
    """Render summary metrics and CO₂ formula info."""
    total_cost = sum(i.monthly_cost_eur for i in dashboard_data.instances if i.monthly_cost_eur is not None)
    total_co2 = sum(i.monthly_co2_kg for i in dashboard_data.instances if i.monthly_co2_kg is not None)
    total_power = sum(i.power_watts for i in dashboard_data.instances if i.power_watts is not None)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Monthly Cost",
            f"€{total_cost:.2f}",
            "Sum of all instances",
            help="Total monthly costs across all monitored instances. Calculated from CloudTrail runtime hours × AWS Pricing API rates. Excludes reserved instance discounts and data transfer costs."
        )

    with col2:
        st.metric(
            "Total Monthly CO₂",
            f"{total_co2:.2f} kg",
            "All instances combined",
            help="Total monthly carbon emissions from all instances. Based on Boavizta power models, CPU utilization from CloudWatch, and ElectricityMaps German grid intensity. Formula: CO₂(kg) = Power(kW) × Intensity(g/kWh) × Runtime(h) ÷ 1000"
        )

    with col3:
        st.metric(
            "Total Power Draw",
            f"{total_power:.0f} W",
            "Current consumption",
            help="Sum of current power consumption across all running instances. Based on Boavizta hardware models with CPU-based scaling: Power = Base × (30% idle + 70% × CPU utilization). Stopped instances show 0W."
        )


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
        table_data.append(_prepare_instance_row_data(instance, grid_intensity))

    if table_data:
        # Create DataFrame
        import pandas as pd

        df = pd.DataFrame(table_data)

        # Display table with help text
        st.dataframe(df, width="stretch", hide_index=True)

        # Power & CO₂ Calculation Methodology
        _render_calculation_methodology_expander()

        # Summary insights
        _render_summary_metrics(dashboard_data)

    else:
        st.error("No instance data available for detailed analysis")
