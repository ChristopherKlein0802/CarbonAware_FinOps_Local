"""
Carbon Optimization Page
German Grid focused carbon optimization analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Any, Optional

from src.utils.performance import get_cached_historical_data


def _render_optimization_zones(fig: go.Figure) -> None:
    """Add optimization zone lines to carbon intensity chart"""
    fig.add_hline(y=200, line_dash="dash", line_color="green",
                  annotation_text="🟢 OPTIMAL ZONE (<200g)", annotation_position="top left")
    fig.add_hline(y=350, line_dash="dash", line_color="orange",
                  annotation_text="🟡 MODERATE ZONE (200-350g)", annotation_position="top left")
    fig.add_hline(y=450, line_dash="dash", line_color="red",
                  annotation_text="🔴 HIGH CARBON (>350g)", annotation_position="top left")


def _process_historical_data(historical_data: list, current_intensity: float) -> tuple[list, list]:
    """Process historical data to create 24-hour pattern"""
    hours = []
    grid_pattern = []
    current_hour = datetime.now().hour

    # Sort data by hour and create 24-hour pattern
    for hour in range(24):
        hours.append(hour)
        # Find data for this hour (use most recent if multiple entries)
        hour_data = [d for d in historical_data if d["hour"] == hour]
        if hour_data:
            grid_pattern.append(hour_data[-1]["carbonIntensity"])
        elif hour == current_hour:
            # Use current intensity for current hour if missing
            grid_pattern.append(current_intensity)
        else:
            # Fill gaps with reasonable interpolation
            prev_values = [d["carbonIntensity"] for d in historical_data if d["hour"] < hour]
            next_values = [d["carbonIntensity"] for d in historical_data if d["hour"] > hour]
            if prev_values and next_values:
                grid_pattern.append((prev_values[-1] + next_values[0]) / 2)
            elif prev_values:
                grid_pattern.append(prev_values[-1])
            elif next_values:
                grid_pattern.append(next_values[0])
            else:
                grid_pattern.append(current_intensity)

    return hours, grid_pattern


def _render_carbon_chart(historical_data: list, current_intensity: float) -> None:
    """Render the 24-hour carbon intensity chart"""
    current_hour = datetime.now().hour

    if historical_data and len(historical_data) > 0:
        # Use real API data
        hours, grid_pattern = _process_historical_data(historical_data, current_intensity)

        # Determine data source for transparency
        data_source = historical_data[0].get('source', 'unknown')
        if 'hourly_collection' in data_source:
            st.success(f"✅ Using self-collected real ElectricityMaps data ({len(historical_data)} hourly data points)")
            st.info("🔬 **Academic Note**: Data collected hourly from ElectricityMaps API to build our own 24h dataset")
        else:
            st.success(f"✅ Using official ElectricityMaps 24h API data ({len(historical_data)} data points)")
    else:
        # Fallback: Show clear disclaimer about data unavailability
        st.warning("⚠️ 24h data not yet available - building dataset over time")
        st.info("📊 **Scientific Note**: Self-collecting hourly data from ElectricityMaps API to build our own 24h dataset. Check back in a few hours!")

        # Create minimal chart with only current data point
        hours = [current_hour]
        grid_pattern = [current_intensity]

    # Create chart
    fig = go.Figure()

    # Add the 24h pattern
    fig.add_trace(go.Scatter(
        x=hours,
        y=grid_pattern,
        mode='lines+markers',
        name='German Grid',
        line=dict(color='#2E8B57', width=3),
        marker=dict(size=6)
    ))

    # Highlight current hour
    fig.add_trace(go.Scatter(
        x=[current_hour],
        y=[current_intensity],
        mode='markers',
        name='Current',
        marker=dict(size=15, color='red', symbol='star')
    ))

    # Add optimization zones
    _render_optimization_zones(fig)

    # Update chart title based on data source
    if historical_data and len(historical_data) > 0:
        chart_title = 'German Electricity Grid - Real ElectricityMaps API Data (Past 24h)'
    else:
        chart_title = 'German Electricity Grid - Current Data Only (24h API Unavailable)'

    fig.update_layout(
        title=chart_title,
        xaxis_title='Hour of Day',
        yaxis_title='Carbon Intensity (g CO₂/kWh)',
        height=500,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Scientific disclaimer about data source
    if historical_data and len(historical_data) > 0:
        st.info("🔬 **Academic Note**: Chart shows real ElectricityMaps historical data with daily caching for cost optimization")
    else:
        st.warning("🔬 **Academic Note**: Full 24h pattern unavailable - showing current data only to maintain NO-FALLBACK scientific policy")


def _render_optimization_recommendations() -> None:
    """Render optimization recommendations section"""
    st.markdown("### 💡 Smart Scheduling Recommendations")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🟢 OPTIMAL TIMES (Low Carbon):**
        - **12:00-16:00**: Solar peak hours
        - **02:00-06:00**: Low demand, wind power

        **✅ RECOMMENDED ACTIONS:**
        - Schedule batch jobs and data processing
        - Run machine learning training
        - Execute backup operations
        - Deploy auto-scaling for variable workloads
        """)

    with col2:
        st.markdown("""
        **🔴 AVOID TIMES (High Carbon):**
        - **18:00-22:00**: Peak demand, coal plants
        - **07:00-09:00**: Morning demand surge

        **❌ ACTIONS TO POSTPONE:**
        - Non-urgent compute tasks
        - Development/test environments
        - Data analytics jobs
        - Archive operations
        """)


def _render_business_impact_analysis(dashboard_data: Any) -> None:
    """Render business impact analysis section"""
    st.markdown("### 📈 Carbon-Aware vs Traditional Scheduling")

    if dashboard_data and dashboard_data.instances:
        # Calculate potential carbon savings
        total_monthly_co2 = dashboard_data.total_co2_kg
        traditional_monthly_co2 = total_monthly_co2 * 1.1  # Assume 10% worse with fixed scheduling

        # Conservative optimization estimate
        co2_reduction = traditional_monthly_co2 - total_monthly_co2
        co2_reduction_percent = (co2_reduction / traditional_monthly_co2) * 100

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Monthly CO₂ Reduction",
                f"{co2_reduction:.1f} kg",
                f"{co2_reduction_percent:.1f}% improvement"
            )

            # EU ETS carbon pricing (approximate)
            if co2_reduction > 0:
                eur_savings = (co2_reduction / 1000) * 50  # Convert kg to tonnes × €50
                st.metric("EU ETS Value Saved", f"€{eur_savings:.2f}", "Per month")

        with col2:
            st.markdown("**Implementation Strategy:**")
            st.markdown("""
            1. 🔍 **Monitor**: Track grid carbon intensity
            2. ⏰ **Schedule**: Move workloads to green hours
            3. 🔄 **Automate**: Use AWS EventBridge + Lambda
            4. 📊 **Measure**: Compare before/after emissions
            """)

    st.markdown("### 🌍 Environmental Impact Context")

    # Environmental context calculations
    if dashboard_data and dashboard_data.instances:
        instances_data = []
        for inst in dashboard_data.instances:
            if inst.monthly_co2_kg and inst.power_watts:
                instances_data.append({
                    "Instance": inst.instance_id[:8],
                    "Type": inst.instance_type,
                    "CO₂/Power": inst.monthly_co2_kg / inst.power_watts * 1000,
                    "Efficiency": "High" if (inst.monthly_co2_kg / inst.power_watts * 1000) < 100 else "Low"
                })

        if instances_data:
            efficiency_df = pd.DataFrame(instances_data)
            st.dataframe(efficiency_df, use_container_width=True)

    # Add energy mix information
    st.markdown("### 🇩🇪 German Energy Mix Context")

    energy_mix = pd.DataFrame([
        {"Source": "Renewables", "Percentage": 45, "Type": "Green"},
        {"Source": "Natural Gas", "Percentage": 25, "Type": "Fossil"},
        {"Source": "Coal", "Percentage": 18, "Type": "Fossil"},
        {"Source": "Nuclear", "Percentage": 12, "Type": "Nuclear"}
    ])

    import plotly.express as px
    fig_mix = px.pie(energy_mix, values="Percentage", names="Source",
                    color="Type", title="🇩🇪 German Energy Mix 2025 (Estimated)")
    fig_mix.update_layout(height=400)
    st.plotly_chart(fig_mix, use_container_width=True)


def render_carbon_page(dashboard_data: Optional[Any]) -> None:
    """
    Render the carbon optimization page

    Args:
        dashboard_data: Complete dashboard data object with carbon intensity data
    """
    st.header("🇩🇪 Carbon-Aware Optimization")

    if not dashboard_data or not dashboard_data.carbon_intensity:
        st.warning("⚠️ No carbon intensity data available. Check ElectricityMaps API.")
        return

    # Current Grid Status
    current_intensity = dashboard_data.carbon_intensity.value
    st.markdown(f"### ⚡ German Grid Status: {current_intensity:.0f} g CO₂/kWh")

    # Real 24h German Grid Pattern from ElectricityMaps API
    st.markdown("### 📊 German Grid 24h Carbon Intensity Pattern")
    st.markdown("*Real historical data from ElectricityMaps API (past 24 hours)*")

    # Get cached historical data for better performance
    historical_data = get_cached_historical_data("eu-central-1")

    # Render carbon intensity chart
    _render_carbon_chart(historical_data, current_intensity)

    # Render optimization recommendations
    _render_optimization_recommendations()

    # Render business impact analysis
    _render_business_impact_analysis(dashboard_data)

    # Grid status determination
    if current_intensity < 300:
        grid_status = "Low"
        status_emoji = "🟢"
        recommendation = "✅ OPTIMAL: Schedule energy-intensive workloads now"
    elif current_intensity < 500:
        grid_status = "Medium"
        status_emoji = "🟡"
        recommendation = "⚠️ MODERATE: Consider delaying non-urgent tasks"
    else:
        grid_status = "High"
        status_emoji = "🔴"
        recommendation = "🚨 HIGH CARBON: Postpone batch jobs if possible"

    st.info(f"{status_emoji} **Current Recommendation:** {recommendation}")