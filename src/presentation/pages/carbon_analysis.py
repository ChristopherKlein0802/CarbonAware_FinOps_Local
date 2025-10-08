"""
Carbon Optimization Page
German Grid focused carbon optimization analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


def _determine_grid_status(intensity: float) -> Tuple[str, str, str]:
    """
    Determine grid status from carbon intensity value.

    Args:
        intensity: Carbon intensity in g CO₂/kWh

    Returns:
        Tuple of (emoji, status_text, recommendation)
    """
    if intensity < 200:
        return "🟢", "Low Carbon", "Excellent time for workload scheduling"
    elif intensity < 400:
        return "🟡", "Moderate Carbon", "Consider delaying non-critical workloads"
    else:
        return "🔴", "High Carbon", "Avoid new workload starts if possible"


def render_carbon_page(dashboard_data: Optional[Any]) -> None:
    """
    Render focused carbon optimization page

    Args:
        dashboard_data: Complete dashboard data object with carbon intensity data
    """
    st.header("🇩🇪 Carbon-Aware Optimization")
    st.caption("German grid carbon intensity tracking for optimal workload scheduling")

    if not dashboard_data or not dashboard_data.carbon_intensity:
        st.warning("⚠️ No carbon intensity data available. Check ElectricityMaps API.")
        return

    # Current status and quick metrics
    current_intensity = dashboard_data.carbon_intensity.value
    _render_current_grid_status(current_intensity)

    # Core feature: 24h pattern visualization using data provided by backend services
    historical_data = getattr(dashboard_data, "carbon_history", None) or []
    self_collected_data = getattr(dashboard_data, "self_collected_carbon_history", None) or []

    # Fallback: use self-collected cache if official API unavailable
    if not historical_data:
        historical_data = self_collected_data

    _render_dynamic_carbon_chart(historical_data, current_intensity, self_collected_data)

    # Simple optimization message (Business Impact is on Executive Summary)
    st.success(
        "🎯 **Key Insight**: Use carbon intensity data to schedule workloads during low-carbon hours for optimal environmental impact."
    )


def _render_current_grid_status(current_intensity: float) -> None:
    """Render current grid status with quick optimization metrics"""
    # Determine grid status
    status_color, status_text, recommendation = _determine_grid_status(current_intensity)

    status_display = status_text.split()[0]
    recommendation_display = recommendation.split(":")[0] if ":" in recommendation else recommendation

    # Visual status display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Current Grid Intensity",
            f"{current_intensity:.0f} g CO₂/kWh",
            status_text,
            help="Real-time German grid carbon intensity from ElectricityMaps. Lower values mean cleaner energy mix "
                 "(more renewables like solar/wind). Updated hourly. Thresholds: <200 Low, 200-400 Moderate, >400 High."
        )
    with col2:
        st.metric(
            "Grid Status",
            f"{status_color} {status_display}",
            "German grid",
            help="Grid status classification based on carbon intensity. 🟢 Low: Optimal for workloads. "
                 "🟡 Moderate: Consider delaying. 🔴 High: Avoid new starts if possible."
        )
    with col3:
        st.metric(
            "Recommendation",
            recommendation_display,
            "Workload timing",
            help="Actionable recommendation for workload scheduling based on current grid status. "
                 "Time-shift batch jobs, CI/CD pipelines, or dev environments to low-carbon windows for maximum CO₂ reduction."
        )

    # Current status summary
    st.info(f"{status_color} **{recommendation}**")


def _render_dynamic_carbon_chart(
    historical_data: Optional[list],
    current_intensity: float,
    self_collected_data: Optional[list] = None,
) -> None:
    """Render progressive 24h carbon chart with datetime axis"""
    from datetime import datetime, timedelta, timezone

    st.markdown("### 📊 German Grid 24h Carbon Intensity")

    current_time_local = datetime.now(timezone.utc).astimezone()
    current_time_utc = datetime.now(timezone.utc)
    current_hour_local = current_time_local.replace(minute=0, second=0, microsecond=0)
    current_hour_utc = current_time_utc.replace(minute=0, second=0, microsecond=0)

    # Always include current data point snapped to hour
    chart_datetimes = [current_hour_local]
    chart_values = [current_intensity]
    chart_labels = [f"{current_hour_local.strftime('%d.%m.%Y %H:00')} (Now)"]

    # Add historical data if available
    if historical_data:
        # Normalise input structure (API or self-collected cache)
        dedup_points = {}
        for data_point in historical_data:
            timestamp_str = data_point.get("datetime") or data_point.get("hour_key")
            if not timestamp_str:
                continue
            try:
                point_datetime = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
                if point_datetime.tzinfo is None:
                    point_datetime = point_datetime.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            value = data_point.get("carbonIntensity") or data_point.get("value")
            if value is None:
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue

            dedup_points[point_datetime] = value

        # Merge self-collected readings to fill potential gaps
        for data_point in self_collected_data or []:
            timestamp_str = data_point.get("datetime") or data_point.get("hour_key")
            if not timestamp_str:
                continue
            try:
                point_datetime = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
                if point_datetime.tzinfo is None:
                    point_datetime = point_datetime.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            value = data_point.get("carbonIntensity") or data_point.get("value")
            if value is None:
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            dedup_points[point_datetime] = value

        # Sort chronologically and extend chart data
        now_utc = datetime.now(timezone.utc)

        for point_datetime, value in sorted(dedup_points.items()):
            if point_datetime > now_utc:
                continue  # Skip future datapoints not yet observed
            if point_datetime == current_hour_utc:
                continue  # Skip duplicate of current hour
            local_dt = point_datetime.astimezone()
            chart_datetimes.append(local_dt)
            chart_values.append(value)

            if local_dt.date() == current_time_local.date():
                label_suffix = "(Heute)"
            elif local_dt.date() == (current_time_local.date() - timedelta(days=1)):
                label_suffix = "(Gestern)"
            else:
                label_suffix = ""
            chart_labels.append(f"{local_dt.strftime('%d.%m.%Y %H:00')} {label_suffix}".strip())

        # Sort by datetime for proper chronological order
        combined_data = sorted(zip(chart_datetimes, chart_values, chart_labels), key=lambda x: x[0])
        chart_datetimes, chart_values, chart_labels = map(list, zip(*combined_data))

        # Ensure exactly 24 data points (current hour + previous 23 hours)
        if len(chart_datetimes) > 24:
            chart_datetimes = chart_datetimes[-24:]
            chart_values = chart_values[-24:]
            chart_labels = chart_labels[-24:]

        historical_points = max(len(chart_datetimes) - 1, 0)  # exclude current hour point
        if historical_points < 6:
            st.info(f"🔄 Building dataset: {historical_points + 1} hours available")
        elif historical_points < 18:
            st.info(f"📈 Growing dataset: {historical_points + 1} hours available")
    else:
        st.warning("⚠️ Starting data collection - First hour collected")
        historical_points = 0

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
                marker_colors.append("red")
                marker_sizes.append(12)
                marker_symbols.append("star")
            elif "(Gestern)" in label:
                marker_colors.append("#FFA500")  # Orange for yesterday
                marker_sizes.append(8)
                marker_symbols.append("circle")
            else:
                marker_colors.append("#2E8B57")  # Green for today
                marker_sizes.append(8)
                marker_symbols.append("circle")

        fig.add_trace(
            go.Scatter(
                x=list(chart_datetimes),
                y=list(chart_values),
                mode="lines+markers",
                name="German Grid Carbon Intensity",
                line=dict(color="#2E8B57", width=3),
                marker=dict(size=marker_sizes, color=marker_colors, symbol=marker_symbols),
                text=chart_labels,
                hovertemplate="<b>%{text}</b><br>%{y}g CO₂/kWh<extra></extra>",
            )
        )
    else:
        # Single point - show as current hour marker
        fig.add_trace(
            go.Scatter(
                x=list(chart_datetimes),
                y=list(chart_values),
                mode="markers",
                name="Current Hour",
                marker=dict(size=12, color="red", symbol="star"),
                text=chart_labels,
                hovertemplate="<b>%{text}</b><br>%{y}g CO₂/kWh<extra></extra>",
            )
        )

    # Chart shows carbon intensity without zone lines (status already displayed above)

    # Dynamic chart title based on data availability
    if historical_data and historical_points >= 18:
        chart_title = f"German Grid Carbon Intensity - Complete 24h Pattern ({historical_points + 1} hours)"
    elif historical_data and historical_points > 0:
        chart_title = f"German Grid Carbon Intensity - Building Pattern ({historical_points + 1} hours collected)"
    else:
        chart_title = "German Grid Carbon Intensity - Starting Collection"

    # Update chart layout with datetime axis
    fig.update_layout(
        title=chart_title,
        xaxis_title="Time (Last 24 Hours)",
        yaxis_title="Carbon Intensity (g CO₂/kWh)",
        height=500,
        showlegend=True,
        xaxis=dict(type="date", tickformat="%d.%m.%Y\n%H:%M", dtick=3600000 * 2),  # Show every 2 hours in milliseconds
    )

    st.plotly_chart(fig, width="stretch")

    # Progressive status display with datetime information
    if historical_data:
        total_hours = historical_points + 1  # include current hour
        coverage_pct = min((total_hours / 24) * 100, 100)

        today_points = len([dt for dt in chart_datetimes if dt.date() == current_time_local.date()])
        yesterday_points = len(
            [dt for dt in chart_datetimes if dt.date() == (current_time_local.date() - timedelta(days=1))]
        )

        st.caption(
            f"📊 Data Coverage: {total_hours}/24 hours ({coverage_pct:.0f}%) | Today: {today_points} | Yesterday: {yesterday_points}"
        )
        st.caption("🟢 Today • 🟠 Yesterday • ⭐ Current Hour")
    else:
        st.caption("📊 Starting hourly data collection - Chart will progressively build over 24 hours")
