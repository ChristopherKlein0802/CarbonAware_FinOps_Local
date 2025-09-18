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
    from src.api.client import unified_api_client
    historical_data = unified_api_client.electricity_api.get_self_collected_24h_data("eu-central-1")
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
    """Render progressive 24h carbon chart with datetime axis"""
    from datetime import datetime, timedelta
    st.markdown("### 📊 German Grid 24h Carbon Intensity")

    current_time = datetime.now()

    # Always include current data point with full timestamp
    chart_datetimes = [current_time]
    chart_values = [current_intensity]
    chart_labels = [f"{current_time.strftime('%d.%m.%Y %H:00')} (Jetzt)"]

    # Add historical data if available
    if historical_data and len(historical_data) > 0:
        # Process and sort historical data by actual datetime
        for data_point in historical_data:
            # Parse the full datetime from hour_key
            point_datetime = datetime.fromisoformat(data_point["hour_key"].replace('Z', ''))
            value = data_point["carbonIntensity"]

            # Only add if not the same hour as current (avoid duplicates)
            if point_datetime.hour != current_time.hour or point_datetime.date() != current_time.date():
                chart_datetimes.append(point_datetime)
                chart_values.append(value)

                # Create descriptive label with full date
                time_diff = current_time - point_datetime
                if time_diff.days > 0:
                    chart_labels.append(f"{point_datetime.strftime('%d.%m.%Y %H:00')} (Gestern)")
                else:
                    chart_labels.append(f"{point_datetime.strftime('%d.%m.%Y %H:00')} (Heute)")

        # Sort by datetime for proper chronological order
        combined_data = list(zip(chart_datetimes, chart_values, chart_labels))
        combined_data.sort(key=lambda x: x[0])
        chart_datetimes, chart_values, chart_labels = zip(*combined_data)

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

    # Progressive line chart with datetime axis
    if len(chart_datetimes) >= 2:
        # Multiple points - show as connected line with colors by day
        marker_colors = []
        marker_sizes = []
        marker_symbols = []

        for dt, label in zip(chart_datetimes, chart_labels):
            if "(Jetzt)" in label:
                marker_colors.append('red')
                marker_sizes.append(12)
                marker_symbols.append('star')
            elif "(Gestern)" in label:
                marker_colors.append('#FFA500')  # Orange for yesterday
                marker_sizes.append(8)
                marker_symbols.append('circle')
            else:
                marker_colors.append('#2E8B57')  # Green for today
                marker_sizes.append(8)
                marker_symbols.append('circle')

        fig.add_trace(go.Scatter(
            x=list(chart_datetimes),
            y=list(chart_values),
            mode='lines+markers',
            name='German Grid Carbon Intensity',
            line=dict(color='#2E8B57', width=3),
            marker=dict(size=marker_sizes, color=marker_colors, symbol=marker_symbols),
            text=chart_labels,
            hovertemplate='<b>%{text}</b><br>%{y}g CO₂/kWh<extra></extra>'
        ))
    else:
        # Single point - show as current hour marker
        fig.add_trace(go.Scatter(
            x=list(chart_datetimes),
            y=list(chart_values),
            mode='markers',
            name='Current Hour',
            marker=dict(size=12, color='red', symbol='star'),
            text=chart_labels,
            hovertemplate='<b>%{text}</b><br>%{y}g CO₂/kWh<extra></extra>'
        ))

    # Chart shows carbon intensity without zone lines (status already displayed above)

    # Dynamic chart title based on data availability
    if historical_data and len(historical_data) >= 18:
        chart_title = f'German Grid Carbon Intensity - Complete 24h Pattern ({len(chart_datetimes)} hours)'
    elif historical_data and len(historical_data) > 0:
        chart_title = f'German Grid Carbon Intensity - Building Pattern ({len(chart_datetimes)} hours collected)'
    else:
        chart_title = 'German Grid Carbon Intensity - Starting Collection'

    # Update chart layout with datetime axis
    fig.update_layout(
        title=chart_title,
        xaxis_title='Time (Last 24 Hours)',
        yaxis_title='Carbon Intensity (g CO₂/kWh)',
        height=500,
        showlegend=True,
        xaxis=dict(
            type='date',
            tickformat='%d.%m.%Y\n%H:%M',
            dtick=3600000 * 2  # Show every 2 hours in milliseconds
        )
    )

    st.plotly_chart(fig, width='stretch')

    # Progressive status display with datetime information
    if historical_data and len(historical_data) > 0:
        total_hours = len(chart_datetimes)
        coverage_pct = (total_hours / 24) * 100

        # Count today vs yesterday points
        today_points = len([label for label in chart_labels if "Today" in label or label == "Now"])
        yesterday_points = len([label for label in chart_labels if "Yesterday" in label])

        st.caption(f"📊 Data Coverage: {total_hours}/24 hours ({coverage_pct:.0f}%) | Today: {today_points} | Yesterday: {yesterday_points}")
        st.caption("🟢 Today • 🟠 Yesterday • ⭐ Current Hour")
    else:
        st.caption("📊 Starting hourly data collection - Chart will progressively build over 24 hours")