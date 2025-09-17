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


def render_infrastructure_page(dashboard_data: Optional[Any]) -> None:
    """
    Render the infrastructure analytics page

    Args:
        dashboard_data: Complete dashboard data object with instances and metrics
    """
    st.header("🏗️ Infrastructure Analytics")

    if not dashboard_data or not dashboard_data.instances:
        st.warning("⚠️ No infrastructure data available. Check API connections.")
        return

    # Infrastructure KPIs - streamlined calculation and rendering
    running_instances = len([i for i in dashboard_data.instances if i.state == "running"])
    total_power = sum(i.power_watts for i in dashboard_data.instances if i.power_watts)
    avg_cost_per_instance = dashboard_data.total_cost_eur / len(dashboard_data.instances) if dashboard_data.instances else 0
    efficiency_score = (total_power / dashboard_data.total_cost_eur) if dashboard_data.total_cost_eur > 0 else 0

    infra_metrics = [
        ("🟢 Running", f"{running_instances}", "Active instances"),
        ("⚡ Total Power", f"{total_power:.1f}W", "Current draw"),
        ("💰 Avg Cost", f"€{avg_cost_per_instance:.2f}", "Per instance"),
        ("📊 Efficiency", f"{efficiency_score:.1f}", "W/€")
    ]
    render_4_column_metrics(infra_metrics)

    # Infrastructure charts
    st.markdown("### 📊 Infrastructure Analysis")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Instance type distribution
        instance_types = {}
        for inst in dashboard_data.instances:
            instance_types[inst.instance_type] = instance_types.get(inst.instance_type, 0) + 1

        type_df = pd.DataFrame(list(instance_types.items()), columns=["Type", "Count"])
        fig_types = px.pie(type_df, values="Count", names="Type",
                          title="🏗️ Instance Type Distribution")
        fig_types.update_layout(height=400)
        optimize_chart_rendering(fig_types, "instance_types")

    with chart_col2:
        # Power consumption by instance
        power_data = []
        for inst in dashboard_data.instances:
            if inst.power_watts:
                power_data.append({
                    "Instance": inst.instance_id[:8],
                    "Type": inst.instance_type,
                    "Power (W)": inst.power_watts,
                    "State": inst.state
                })

        if power_data:
            power_df = pd.DataFrame(power_data)
            fig_power = px.bar(power_df, x="Instance", y="Power (W)",
                             color="Type", title="⚡ Power Consumption by Instance")
            fig_power.update_layout(height=400)
            optimize_chart_rendering(fig_power, "power_consumption")

    # System health monitoring
    st.markdown("### 🏥 System Health")

    health_col1, health_col2 = st.columns(2)

    with health_col1:
        # API health status - only when dashboard_data is refreshed
        if dashboard_data and hasattr(dashboard_data, 'api_health_status'):
            # Show cached health status from data refresh
            health_data = []
            for service_name, health_status in dashboard_data.api_health_status.items():
                health_data.append({
                    "Service": service_name.replace("_", " ").title(),
                    "Status": health_status.status.title(),
                    "Response Time": f"{health_status.response_time_ms:.1f}ms",
                    "Healthy": "✅" if health_status.healthy else "❌"
                })

            health_df = pd.DataFrame(health_data)
            st.dataframe(health_df, use_container_width=True)
        else:
            st.info("🔄 Health status updates with data refresh")

    with health_col2:
        st.info(f"""
        **System Status:**
        - Data Freshness: {dashboard_data.data_freshness.strftime('%H:%M:%S') if dashboard_data.data_freshness else 'Unknown'}
        - Cache Strategy: 30min Carbon, 1h Cost, 24h Power
        - Academic Mode: NO-FALLBACK data policy
        - Uncertainty Range: ±15% conservative approach
        """)