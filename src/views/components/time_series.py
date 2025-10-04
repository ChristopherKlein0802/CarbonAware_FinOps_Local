"""
Time Series Component
Displays cost and carbon alignment charts with TAC metrics
"""

import streamlit as st
from typing import Optional
from src.models.dashboard import DashboardData


def render_time_series_charts(dashboard_data: Optional[DashboardData]) -> None:
    """
    Visualise hourly cost and CO₂ data to evidence TAC (Time Alignment Coverage).

    Args:
        dashboard_data: Complete dashboard data with time series points
    """
    if not dashboard_data:
        return

    series = getattr(dashboard_data, "time_series", []) or []
    st.markdown("### ⏱️ Cost & CO₂ Trend (last 24 h)")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Combines the past 24 hours of aggregated EC2 costs (AWS Cost Explorer) with ElectricityMaps carbon intensity.
            - **TAC (Time Alignment Coverage)**: Reports how many hourly cost points have matching carbon data (>95% required by R1).
            - **Cost MAPE**: Shows deviation between instance-specific calculations (CloudTrail + Pricing API) and
              aggregated Cost Explorer data. High values indicate Cost Explorer includes additional services beyond tracked instances.
            - **Note**: Cost Explorer provides aggregated account-level costs, not instance-specific breakdown.
            """
        )

    if not series:
        st.info("No historical datapoints yet – the dashboard will collect new values with each run.")
        return

    import pandas as pd
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    data = pd.DataFrame(
        [
            {
                "timestamp": point.timestamp,
                "cost_eur_per_hour": point.cost_eur_per_hour,
                "co2_kg_per_hour": point.co2_kg_per_hour,
            }
            for point in series
        ]
    ).sort_values("timestamp")

    if data.empty:
        st.info("Keine auswertbaren Datenpunkte vorhanden.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=data["timestamp"],
            y=data["cost_eur_per_hour"],
            name="Kosten (€/h)",
            marker_color="#1f77b4",
            opacity=0.7,
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=data["timestamp"],
            y=data["co2_kg_per_hour"],
            name="CO₂ (kg/h)",
            mode="lines+markers",
            line=dict(color="#d62728", width=3),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
        margin=dict(t=40, l=60, r=60, b=40),
    )
    fig.update_xaxes(title_text="Zeitpunkt")
    fig.update_yaxes(title_text="Kosten (€/h)", secondary_y=False)
    fig.update_yaxes(title_text="CO₂ (kg/h)", secondary_y=True)

    st.plotly_chart(fig, width='stretch')

    tac_col1, tac_col2 = st.columns(2)
    tac_score = getattr(dashboard_data, "tac_score", None)
    tac_hours = getattr(dashboard_data, "tac_aligned_hours", None) or 0

    with tac_col1:
        if tac_score is not None:
            st.metric("Time Alignment Coverage", f"{tac_score * 100:.0f}%", f"{tac_hours} h aligned")
        else:
            st.metric("Time Alignment Coverage", "n/a", "Sammle weitere Daten")

    with tac_col2:
        cost_mape = getattr(dashboard_data, "cost_mape", None)
        if cost_mape is not None:
            st.metric("Cost MAPE", f"{cost_mape * 100:.1f}%")
        else:
            st.metric("Cost MAPE", "n/a", "Keine AWS-Kostendaten")
