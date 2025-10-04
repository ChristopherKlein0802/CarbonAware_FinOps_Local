"""
Validation Panel Component
Displays data precision, quality metrics, and API health status
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional
from src.models.dashboard import DashboardData
from src.utils.validation import validate_dashboard_data, get_data_quality_score
from src.utils.performance import render_4_column_metrics


def render_validation_panel(dashboard_data: Optional[DashboardData]) -> None:
    """
    Render validation and quality metrics including system status and precision insights.

    Args:
        dashboard_data: Complete dashboard data with instances and API status
    """
    if not dashboard_data:
        st.warning("⚠️ No data available")
        return

    _render_system_status(dashboard_data)
    _render_precision_insights(dashboard_data)


def _render_system_status(dashboard_data: DashboardData) -> None:
    """Render current system status with API health monitoring."""
    st.markdown("### 📊 System Status")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Displays how many instances are running and which data categories (cost/carbon) are live.
            - Lists the health of each API integration with the role it plays and when the dashboard last checked it (local time).
            """
        )

    # Dynamic system metrics
    if dashboard_data and dashboard_data.instances:
        running_instances = len([i for i in dashboard_data.instances if i.state == "running"])
        total_instances = len(dashboard_data.instances)
    else:
        running_instances = 0
        total_instances = 0

    if dashboard_data and hasattr(dashboard_data, 'api_health_status') and dashboard_data.api_health_status:
        apis_online = len([api for api, status in dashboard_data.api_health_status.items() if status.healthy])
        total_apis = len(dashboard_data.api_health_status)
    else:
        apis_online = 0
        total_apis = 5  # Known total APIs

    # Data quality indicators for system status
    cost_available = dashboard_data and dashboard_data.total_cost_eur > 0
    carbon_available = dashboard_data and dashboard_data.carbon_intensity

    status_metrics = [
        ("🟢 Running Instances", f"{running_instances}", "Used for calculations"),
        ("🔗 APIs", f"{apis_online}/{total_apis}", "Online/Total"),
        ("💰 Cost Data", f"{'✅ Live' if cost_available else '❌ None'}", f"AWS Cost Explorer {'(ACTIVE)' if cost_available else '(NO DATA)'}"),
        ("🌍 Carbon Data", f"{'✅ Live' if carbon_available else '❌ None'}", f"ElectricityMaps {'(ACTIVE)' if carbon_available else '(NO DATA)'}")
    ]
    render_4_column_metrics(status_metrics)

    api_health = getattr(dashboard_data, 'api_health_status', {}) if dashboard_data else {}
    if api_health:
        role_map = {
            "ElectricityMaps": "Grid carbon intensity (1 h cache)",
            "Boavizta": "Power models (7 day cache)",
            "AWS Pricing": "Instance pricing (7 day cache)",
            "AWS Cost Explorer": "Aggregated cost comparison (6 h cache)",
            "AWS CloudWatch": "CPU utilisation (3 h cache)",
            "AWS CloudTrail": "Instance-specific runtime (24 h cache)",
            "CloudWatch": "CPU utilisation (3 h cache)",
            "CloudTrail": "Instance-specific runtime (24 h cache)"
        }

        display_labels = {
            "CloudWatch": "AWS CloudWatch",
            "CloudTrail": "AWS CloudTrail",
            "Aws Cloudwatch": "AWS CloudWatch",
            "Aws Cloudtrail": "AWS CloudTrail",
        }

        status_rows: list[dict[str, str]] = []
        berlin_tz = ZoneInfo("Europe/Berlin")

        for service, status in sorted(api_health.items()):
            label = display_labels.get(service, service.replace('_', ' '))
            state = getattr(status, "status", "unknown").replace('_', ' ').title()
            icon = "🟢" if getattr(status, "healthy", False) else ("🟡" if state.lower() == "degraded" else "🔴")

            last_check = getattr(status, "last_check", None)
            if last_check is None:
                checked_at = "–"
            else:
                try:
                    ts_obj = last_check
                    if hasattr(ts_obj, "tzinfo") and ts_obj.tzinfo is not None:
                        localized = ts_obj.astimezone(berlin_tz)
                    else:
                        localized = ts_obj.replace(tzinfo=berlin_tz)
                    # Show relative age if older than 24 hours, else absolute time
                    age_hours = (datetime.now(timezone.utc) - localized.astimezone(timezone.utc)).total_seconds() / 3600
                    if age_hours > 24:
                        checked_at = f"{age_hours:.0f}h ago"
                    else:
                        checked_at = localized.strftime("%d.%m.%Y %H:%M")
                except Exception:  # pragma: no cover - defensive formatting
                    checked_at = str(last_check)

            api_call = getattr(status, "last_api_call", None)
            if api_call is None:
                last_api_call = "–"
            else:
                try:
                    if hasattr(api_call, "tzinfo") and api_call.tzinfo is not None:
                        api_call_local = api_call.astimezone(berlin_tz)
                    else:
                        api_call_local = api_call.replace(tzinfo=berlin_tz)
                    last_api_call = api_call_local.strftime("%d.%m.%Y %H:%M")
                except Exception:  # pragma: no cover - defensive formatting
                    last_api_call = str(api_call)

            role = role_map.get(service, role_map.get(label, "Monitoring service"))

            status_rows.append({
                "Service": label,
                "Status": f"{icon} {state}",
                "Last check": checked_at,
                "Last API call": last_api_call,
                "Role": role,
            })

        df = pd.DataFrame(status_rows)
        st.dataframe(df, hide_index=True, width='stretch')


def _render_precision_insights(dashboard_data: DashboardData) -> None:
    """Render precision and validation insights with actual calculations."""
    st.markdown("### 🎯 Precision & Data Quality")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Coverage metrics show what share of instances has runtime, pricing, and fully measured data.
            - **Cost Comparison**: Shows deviation between instance-specific calculations (CloudTrail + Pricing API)
              and aggregated AWS Cost Explorer data. Large deviations indicate Cost Explorer includes additional
              services or instances not tracked by CloudTrail.
            - "Data precision" summarises overall measurement coverage across all instances.
            """
        )

    if not dashboard_data or not dashboard_data.instances:
        st.warning("No data available for precision analysis")
        return

    # Add data quality validation
    validation_results = validate_dashboard_data(dashboard_data.instances)
    quality_score = get_data_quality_score(dashboard_data.instances)

    # Show validation warnings if any
    if validation_results["total_errors"] > 0:
        st.error(f"⚠️ Data Quality Issues: {validation_results['total_errors']} errors found")
        for error in validation_results["summary_errors"]:
            st.error(f"• {error}")
    elif validation_results["total_warnings"] > 0:
        st.warning(f"📊 Data Quality Notes: {validation_results['total_warnings']} plausibility warnings")
        with st.expander("View warnings"):
            for warning in validation_results["summary_warnings"]:
                st.warning(f"• {warning}")

    # Calculate basic metrics
    total_instances = len(dashboard_data.instances)
    measured_runtime = len([i for i in dashboard_data.instances if getattr(i, 'runtime_hours', None) is not None])
    pricing_available = len([i for i in dashboard_data.instances if getattr(i, 'hourly_price_usd', None)])
    measured_quality = len([i for i in dashboard_data.instances if getattr(i, 'data_quality', '') == 'measured'])

    validation_factor = getattr(dashboard_data, 'validation_factor', None)
    accuracy_status = getattr(dashboard_data, 'accuracy_status', 'UNKNOWN') or 'UNKNOWN'

    runtime_pct = (measured_runtime / total_instances * 100) if total_instances else 0
    pricing_pct = (pricing_available / total_instances * 100) if total_instances else 0
    measured_pct = (measured_quality / total_instances * 100) if total_instances else 0

    row1_col1, row1_col2, row1_col3 = st.columns(3)

    with row1_col1:
        st.metric("Runtime coverage", f"{runtime_pct:.0f}%", f"{measured_runtime}/{total_instances} instances")

    with row1_col2:
        st.metric("Pricing coverage", f"{pricing_pct:.0f}%", f"{pricing_available}/{total_instances} instances")

    with row1_col3:
        st.metric("Measured quality", f"{measured_pct:.0f}%", f"{measured_quality}/{total_instances} instances")

    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row2_col1:
        if validation_factor is not None:
            delta_pct = abs(1 - validation_factor) * 100

            if validation_factor > 100:
                st.metric("📊 Cost Explorer vs Calculated", "Explorer >> Calculated", f"{validation_factor:.1f}× higher")
            elif validation_factor > 10:
                st.metric("📊 Cost Explorer vs Calculated", "Explorer much higher", f"{validation_factor:.1f}× higher")
            elif validation_factor > 2:
                st.metric("📊 Cost Explorer vs Calculated", "Explorer higher", f"{validation_factor:.1f}× (other services incl.)")
            elif delta_pct <= 30:
                st.metric("📊 Cost Explorer vs Calculated", "Close match", f"±{delta_pct:.0f}%")
            elif delta_pct <= 60:
                st.metric("📊 Cost Explorer vs Calculated", "Moderate diff", f"±{delta_pct:.0f}%")
            else:
                st.metric("📊 Cost Explorer vs Calculated", "Large diff", f"±{delta_pct:.0f}%")
        else:
            st.metric("📊 Cost Explorer vs Calculated", "No data", "Fetching Explorer data...")

    precision_pct = (quality_score or 0.0) * 100
    if quality_score is None:
        precision_label = "Unknown"
    elif quality_score >= 0.8:
        precision_label = "High"
    elif quality_score >= 0.5:
        precision_label = "Moderate"
    else:
        precision_label = "Low"

    with row2_col2:
        st.metric(
            "🎯 Data Precision",
            f"{precision_pct:.0f}%",
            f"{precision_label} coverage",
        )

    with row2_col3:
        st.empty()

    # Show runtime insights if validation factor is problematic
    if validation_factor and validation_factor > 10:
        if validation_factor > 100:
            st.error(
                "⚠️ **Insufficient Runtime Data**: Cost validation requires instances to run for meaningful periods. Current data is too limited for accurate cost comparison."
            )
        else:
            st.warning(
                "⚠️ **Building Runtime History**: AWS CloudTrail precision improves over time. Current validation factor indicates developing accuracy."
            )

        st.info(
            "💡 **Academic outlook**: With sufficient runtime history, AWS CloudTrail can reach ±5% accuracy; currently only indicative estimates (≈±40%) are available."
        )
