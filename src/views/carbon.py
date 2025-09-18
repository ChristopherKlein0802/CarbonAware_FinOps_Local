"""
Carbon Optimization Page
German Grid focused carbon optimization analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Any, Optional









def render_carbon_page(dashboard_data: Optional[Any]) -> None:
    """
    Render focused carbon optimization page

    Args:
        dashboard_data: Complete dashboard data object with carbon intensity data
    """
    st.header("🇩🇪 Carbon-Aware Optimization")

    if not dashboard_data or not dashboard_data.carbon_intensity:
        st.warning("⚠️ No carbon intensity data available. Check ElectricityMaps API.")
        return

    # Current status and quick metrics
    current_intensity = dashboard_data.carbon_intensity.value
    _render_current_grid_status(current_intensity)

    # Core feature: 24h pattern visualization with dynamic building from cached hourly data
    from src.api.electricity import ElectricityMapsAPI
    electricity_api = ElectricityMapsAPI()
    historical_data = electricity_api.get_self_collected_24h_data("eu-central-1")
    _render_dynamic_carbon_chart(historical_data, current_intensity)

    # Simple optimization message (Business Impact is on Executive Summary)
    st.success("🎯 **Key Insight**: Use carbon intensity data to schedule workloads during low-carbon hours for optimal environmental impact.")


def _render_current_grid_status(current_intensity: float) -> None:
    """Render current grid status with quick optimization metrics"""
    # Use centralized grid status logic
    from src.utils.ui import determine_grid_status
    status_color, status_text, recommendation = determine_grid_status(current_intensity)

    # Visual status display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Grid Intensity", f"{current_intensity:.0f} g CO₂/kWh", status_text)
    with col2:
        st.metric("Status", f"{status_color} {status_text}", "German electricity grid")
    with col3:
        st.metric("Recommendation", recommendation[:15] + "...", "for cost & carbon optimization")

    # Current status summary
    st.info(f"{status_color} **{recommendation}**")


def _render_dynamic_carbon_chart(historical_data: list, current_intensity: float) -> None:
    """Render progressive 24h carbon chart with dynamic building"""
    st.markdown("### 📊 German Grid 24h Carbon Intensity")

    current_hour = datetime.now().hour

    # Always include current data point
    chart_hours = [current_hour]
    chart_values = [current_intensity]

    # Add historical data if available
    if historical_data and len(historical_data) > 0:
        # Process and sort historical data by hour
        for data_point in historical_data:
            hour = data_point["hour"]
            value = data_point["carbonIntensity"]

            # Avoid duplicate current hour
            if hour != current_hour:
                chart_hours.append(hour)
                chart_values.append(value)

        # Sort by hour for proper line connection
        combined_data = list(zip(chart_hours, chart_values))
        combined_data.sort(key=lambda x: x[0])
        chart_hours, chart_values = zip(*combined_data)

        data_points = len(historical_data)
        if data_points < 6:
            st.info(f"🔄 Building dataset: {data_points + 1} hours collected (collecting hourly)")
        elif data_points < 18:
            st.success(f"📈 Growing dataset: {data_points + 1} hours collected")
        else:
            st.success(f"✅ Full dataset: {data_points + 1} hourly measurements (24h pattern)")
    else:
        st.warning("⚠️ Starting data collection - First hour collected")

    # Create progressive chart
    fig = go.Figure()

    # Progressive line chart - only connect available data points
    if len(chart_hours) >= 2:
        # Multiple points - show as connected line with current hour highlighted
        marker_colors = ['red' if h == current_hour else '#2E8B57' for h in chart_hours]
        marker_sizes = [12 if h == current_hour else 8 for h in chart_hours]
        marker_symbols = ['star' if h == current_hour else 'circle' for h in chart_hours]

        fig.add_trace(go.Scatter(
            x=list(chart_hours),
            y=list(chart_values),
            mode='lines+markers',
            name='German Grid Carbon Intensity',
            line=dict(color='#2E8B57', width=3),
            marker=dict(size=marker_sizes, color=marker_colors, symbol=marker_symbols)
        ))
    else:
        # Single point - show as current hour marker
        fig.add_trace(go.Scatter(
            x=list(chart_hours),
            y=list(chart_values),
            mode='markers',
            name='Current Hour',
            marker=dict(size=12, color='red', symbol='star')
        ))

    # Chart shows carbon intensity without zone lines (status already displayed above)

    # Dynamic chart title based on data availability
    if historical_data and len(historical_data) >= 18:
        chart_title = f'German Grid Carbon Intensity - Complete 24h Pattern ({len(chart_hours)} hours)'
    elif historical_data and len(historical_data) > 0:
        chart_title = f'German Grid Carbon Intensity - Building Pattern ({len(chart_hours)} hours collected)'
    else:
        chart_title = 'German Grid Carbon Intensity - Starting Collection'

    # Update chart layout
    fig.update_layout(
        title=chart_title,
        xaxis_title='Hour of Day',
        yaxis_title='Carbon Intensity (g CO₂/kWh)',
        height=500,
        showlegend=True,
        xaxis=dict(range=[0, 23], dtick=2)  # Show all 24 hours for reference
    )

    st.plotly_chart(fig, width='stretch')

    # Progressive status display
    if historical_data and len(historical_data) > 0:
        total_hours = len(chart_hours)
        coverage_pct = (total_hours / 24) * 100
        st.caption(f"📊 Data Coverage: {total_hours}/24 hours ({coverage_pct:.0f}%) - Progressive building from ElectricityMaps API")
    else:
        st.caption("📊 Starting hourly data collection - Chart will progressively build over 24 hours")