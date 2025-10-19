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

    # NEW: Dual Comparison (24h vs 30d)
    _render_dual_comparison_section(dashboard_data)

    # Core feature: Instance Detail Table with all calculations
    _render_instance_detail_table(dashboard_data)

    # NEW: Hourly CO2 Analysis (only for instances with hourly data)
    _render_hourly_co2_analysis_section(dashboard_data)


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
        "Monthly Runtime (30d)": runtime_hours,
        "CPU Avg (%)": cpu_util,
        "Power (kW)": power_kw,
        "Grid Intensity (g/kWh)": grid_intensity_display,
        "CO₂/Month (30d avg)": co2_display,
        "Cost/Month (30d)": cost_display,
        "Data Quality": quality_badge,
    }


def _render_dual_comparison_section(dashboard_data: Any) -> None:
    """
    Render side-by-side comparison of 24h projected vs 30d actual calculations.

    Shows methodology validation and pattern analysis for Bachelor thesis.
    """
    st.markdown("---")
    st.subheader("📊 Calculation Method Comparison")
    st.caption("24-Hour Precise vs. 30-Day Actual - Methodology Validation")

    # Get aggregated values
    hourly_precise_count = getattr(dashboard_data, "hourly_precise_count", 0)
    fallback_count = getattr(dashboard_data, "fallback_count", 0)
    total_co2_projected = getattr(dashboard_data, "total_co2_projected_kg", 0.0)
    total_co2_30d = getattr(dashboard_data, "total_co2_30d_kg", 0.0)
    total_cost_projected = getattr(dashboard_data, "total_cost_projected_eur", 0.0)
    total_cost_30d = getattr(dashboard_data, "total_cost_30d_eur", 0.0)

    # Show instance counts
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Hourly-Precise Instances",
            f"{hourly_precise_count}",
            help="Instances with complete 24h data (CPU, Carbon, Runtime) using hourly-precise calculation"
        )
    with col2:
        st.metric(
            "Fallback Instances",
            f"{fallback_count}",
            help="Instances using 30d average calculation (missing hourly data)"
        )

    # Side-by-side comparison cards
    st.markdown("### CO₂ Emissions Comparison")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 24h Projected")
        st.markdown(f"**{total_co2_projected:.3f} kg**")
        st.caption(f"Daily × 30 projection")
        st.caption(f"({hourly_precise_count} instances)")

    with col2:
        st.markdown("#### 30d Actual")
        st.markdown(f"**{total_co2_30d:.3f} kg**")
        st.caption(f"Actual runtime basis")
        st.caption(f"({len(dashboard_data.instances)} instances)")

    with col3:
        # Calculate difference and pattern
        if total_co2_30d > 0:
            diff_pct = ((total_co2_projected - total_co2_30d) / total_co2_30d) * 100
            pattern = "Stable" if abs(diff_pct) < 5 else ("Increasing" if diff_pct > 0 else "Decreasing")
            st.markdown("#### Difference")
            st.markdown(f"**{diff_pct:+.1f}%**")
            st.caption(f"Pattern: {pattern}")
            st.caption(f"Δ {total_co2_projected - total_co2_30d:+.3f} kg")
        else:
            st.markdown("#### Difference")
            st.caption("N/A")

    # Cost comparison
    st.markdown("### Cost Comparison")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 24h Projected")
        st.markdown(f"**€{total_cost_projected:.2f}**")
        st.caption(f"Daily × 30 projection")
        st.caption(f"({hourly_precise_count} instances)")

    with col2:
        st.markdown("#### 30d Actual")
        st.markdown(f"**€{total_cost_30d:.2f}**")
        st.caption(f"Actual runtime basis")
        st.caption(f"({len(dashboard_data.instances)} instances)")

    with col3:
        if total_cost_30d > 0:
            diff_pct = ((total_cost_projected - total_cost_30d) / total_cost_30d) * 100
            pattern = "Stable" if abs(diff_pct) < 5 else ("Increasing" if diff_pct > 0 else "Decreasing")
            st.markdown("#### Difference")
            st.markdown(f"**{diff_pct:+.1f}%**")
            st.caption(f"Pattern: {pattern}")
            st.caption(f"Δ €{total_cost_projected - total_cost_30d:+.2f}")
        else:
            st.markdown("#### Difference")
            st.caption("N/A")

    # Methodology explanation
    with st.expander("📖 Understanding the Comparison", expanded=False):
        st.markdown("""
        **24h Projected (Hourly-Precise Method):**
        - Calculates CO₂ for each of the last 24 hours individually
        - Uses hourly CPU data, carbon intensity, and runtime fractions
        - Projects to monthly: `daily_co2 × 30`
        - **Best for:** Variable workloads, carbon intensity tracking

        **30d Actual (Monthly Average Method):**
        - Uses total runtime from last 30 days
        - Uses average CPU and current carbon intensity
        - **Best for:** Stable workloads, cost validation

        **Pattern Analysis:**
        - **Stable (<5% difference):** Consistent workload, both methods agree
        - **Increasing (>5% higher):** 24h period had higher activity than 30d average
        - **Decreasing (>5% lower):** 24h period had lower activity than 30d average

        **Thesis Relevance:**
        This comparison validates the hourly-precise method by showing how it differs from
        traditional average calculations. Large differences indicate variable workloads where
        hourly-precise calculations provide significantly better accuracy.
        """)


def _render_calculation_methodology_expander() -> None:
    """Render calculation methodology documentation in expander."""
    with st.expander("📐 Calculation Methodology", expanded=False):
        st.markdown("""
        **This Table Uses: 30-Day Actual Calculation Method**

        The instance table above shows metrics calculated using the **30-day actual runtime** method:
        - **Runtime**: Total hours from CloudTrail events over last 30 days
        - **CPU**: Average CPU utilization from CloudWatch (24h window)
        - **Carbon Intensity**: Current grid intensity (snapshot)

        For **hourly-precise 24h calculations**, see the "Calculation Method Comparison" section above.

        ---

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
    st.markdown("### 📊 Instance Analysis - 30-Day Actual Data")
    st.caption("Per-instance metrics calculated using 30-day actual runtime and average CPU utilization")

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


def _render_hourly_co2_analysis_section(dashboard_data: Any) -> None:
    """
    Render hourly CO2 analysis section for instances with hourly breakdown data.

    Only displays for instances that have hourly_24h_precise calculation method.
    """
    # Filter instances with hourly data
    instances_with_hourly = [
        inst for inst in dashboard_data.instances
        if inst.co2_calculation_method == "hourly_24h_precise" and inst.hourly_co2_breakdown
    ]

    if not instances_with_hourly:
        # No hourly data available - show info message
        with st.expander("📊 24-Hour CO2 Analysis", expanded=False):
            st.info(
                "ℹ️ Hourly CO2 analysis not yet available. The system is collecting data.\n\n"
                "**Requirements for hourly analysis:**\n"
                "- Hourly CPU utilization data (CloudWatch)\n"
                "- 24h carbon intensity history (ElectricityMaps)\n"
                "- CloudTrail runtime events\n\n"
                "This feature provides detailed hour-by-hour CO2 emissions tracking."
            )
        return

    # Show hourly analysis section
    st.markdown("---")
    st.markdown("### 📊 24-Hour Precise CO2 Analysis")
    st.caption(
        f"Detailed hourly breakdown for {len(instances_with_hourly)} instance(s) "
        f"with complete data (CPU, Carbon Intensity, Runtime)"
    )

    # Instance selector if multiple instances
    if len(instances_with_hourly) == 1:
        selected_instance = instances_with_hourly[0]
    else:
        instance_options = {
            f"{inst.instance_name or inst.instance_id} ({inst.instance_type})": inst
            for inst in instances_with_hourly
        }
        selected_name = st.selectbox(
            "Select instance for detailed hourly analysis:",
            options=list(instance_options.keys())
        )
        selected_instance = instance_options[selected_name]

    # Render hourly analysis for selected instance
    _render_instance_hourly_analysis(selected_instance)


def _render_instance_hourly_analysis(instance: Any) -> None:
    """
    Render detailed hourly CO2 analysis for a single instance.

    Displays:
    - Calculation method badge
    - Summary statistics
    - Hourly CO2 emissions chart
    - Multi-axis chart (CO2, CPU, Carbon Intensity)
    """
    # Display calculation method badge
    _render_co2_method_badge(instance.co2_calculation_method)

    # Extract hourly data
    breakdown = instance.hourly_co2_breakdown
    if not breakdown:
        st.warning("⚠️ Hourly breakdown data missing")
        return

    # Parse timestamps and convert from UTC to local timezone for display
    from datetime import datetime, timezone
    timestamps = []
    for entry in breakdown:
        ts = entry.get("timestamp")
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts)
        else:
            dt = ts

        # Ensure datetime is timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert to local timezone for display
        timestamps.append(dt.astimezone())

    co2_values = [e.get("co2_g", 0) for e in breakdown]
    cpu_values = [e.get("cpu_percent") for e in breakdown if e.get("running", False)]
    carbon_values = [e.get("carbon_intensity") for e in breakdown if e.get("running", False)]
    power_values = [e.get("power_watts") for e in breakdown if e.get("running", False)]
    runtime_fractions = [e.get("runtime_fraction", 0) for e in breakdown]

    # Summary statistics
    st.markdown("#### Summary Statistics (24h)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total CO2 (24h)",
            f"{instance.daily_co2_kg:.4f} kg" if instance.daily_co2_kg else "N/A",
            help="Total CO2 emissions over the last 24 hours (hourly-precise calculation)"
        )

    with col2:
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        st.metric(
            "Avg CPU",
            f"{avg_cpu:.1f}%",
            help="Average CPU utilization over the last 24 hours"
        )

    with col3:
        avg_carbon = sum(carbon_values) / len(carbon_values) if carbon_values else 0
        st.metric(
            "Avg Carbon",
            f"{avg_carbon:.0f} g/kWh",
            help="Average grid carbon intensity over the last 24 hours"
        )

    with col4:
        monthly_projection = instance.daily_co2_kg * 30 if instance.daily_co2_kg else 0
        delta = monthly_projection - (instance.monthly_co2_kg or 0)
        st.metric(
            "Monthly (projected)",
            f"{monthly_projection:.2f} kg",
            delta=f"{delta:+.2f} kg" if instance.monthly_co2_kg else None,
            help="Monthly projection: daily × 30 days"
        )

    # Create detailed hourly chart
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=(
            'CO2 Emissions per Hour',
            'CPU Utilization & Carbon Intensity'
        ),
        vertical_spacing=0.15,
        specs=[[{"secondary_y": False}],
               [{"secondary_y": True}]],
        row_heights=[0.4, 0.6]
    )

    # Row 1: CO2 emissions as bar chart
    fig.add_trace(
        go.Bar(
            x=timestamps,
            y=co2_values,
            name='CO2 (g/h)',
            marker_color='rgba(255, 99, 71, 0.7)',
            hovertemplate='<b>%{x}</b><br>CO2: %{y:.2f} g<extra></extra>'
        ),
        row=1, col=1
    )

    # Row 2: CPU utilization (primary y-axis)
    running_timestamps = [ts for ts, e in zip(timestamps, breakdown) if e.get('running')]
    fig.add_trace(
        go.Scatter(
            x=running_timestamps,
            y=cpu_values,
            name='CPU %',
            line=dict(color='blue', width=2),
            hovertemplate='<b>%{x}</b><br>CPU: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=1, secondary_y=False
    )

    # Row 2: Carbon intensity (secondary y-axis)
    fig.add_trace(
        go.Scatter(
            x=running_timestamps,
            y=carbon_values,
            name='Carbon Intensity (g/kWh)',
            line=dict(color='green', width=2, dash='dot'),
            hovertemplate='<b>%{x}</b><br>Carbon: %{y:.0f} g/kWh<extra></extra>'
        ),
        row=2, col=1, secondary_y=True
    )

    # Update layout
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="CO2 (g/h)", row=1, col=1)
    fig.update_yaxes(title_text="CPU Utilization (%)", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Carbon Intensity (g/kWh)", row=2, col=1, secondary_y=True)

    # Get local timezone name for display
    import time
    local_tz_name = time.strftime('%Z')  # e.g., "CET", "EDT", "UTC+4"

    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode='x unified',
        title_text=f"24-Hour Analysis: {instance.instance_name or instance.instance_id}<br><sub>Last 24 complete hours (times in {local_tz_name})</sub>"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Additional insights
    with st.expander("📈 Hourly Data Insights", expanded=False):
        st.markdown("**Peak Hours:**")
        max_co2_idx = co2_values.index(max(co2_values)) if co2_values else 0
        max_cpu_idx = cpu_values.index(max(cpu_values)) if cpu_values else 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Highest CO2 Hour",
                f"{timestamps[max_co2_idx].strftime('%H:%M')}",
                f"{co2_values[max_co2_idx]:.2f} g"
            )
        with col2:
            st.metric(
                "Highest CPU Hour",
                f"{running_timestamps[max_cpu_idx].strftime('%H:%M')}" if cpu_values else "N/A",
                f"{cpu_values[max_cpu_idx]:.1f}%" if cpu_values else "N/A"
            )

        st.markdown("**Runtime Coverage:**")
        hours_running = sum(1 for rf in runtime_fractions if rf > 0)
        st.metric(
            "Hours Running",
            f"{hours_running}/24",
            f"{(hours_running/24)*100:.0f}% uptime"
        )


def _render_co2_method_badge(method: str) -> None:
    """Render badge indicating CO2 calculation method."""
    if method == "hourly_24h_precise":
        st.success("🟢 Calculation Method: Hourly Precise (24h)")
        st.caption(
            "This instance uses hourly-precise calculation with individual CPU, "
            "carbon intensity, and runtime values for each of the last 24 hours."
        )
    elif method == "monthly_average":
        st.info("🔵 Calculation Method: Monthly Average")
        st.caption(
            "This instance uses average calculation (24h CPU average × current carbon intensity × total runtime)."
        )
    else:
        st.warning("⚪ Calculation Method: No Data")
        st.caption("Insufficient data available for CO2 calculation.")
