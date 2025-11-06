"""
Validation Panel Component
Displays data precision, quality metrics, and API health status
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional
from src.domain.models import DashboardData
from src.domain.validation import validate_dashboard_data, get_data_quality_score


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
    st.caption("Real-time monitoring of infrastructure and API integrations")

    # Dynamic system metrics
    if dashboard_data and dashboard_data.instances:
        running_instances = len([i for i in dashboard_data.instances if i.state == "running"])
        total_instances = len(dashboard_data.instances)
    else:
        running_instances = 0
        total_instances = 0

    if dashboard_data and hasattr(dashboard_data, "api_health_status") and dashboard_data.api_health_status:
        apis_online = len([api for api, status in dashboard_data.api_health_status.items() if status.healthy])
        total_apis = len(dashboard_data.api_health_status)
    else:
        apis_online = 0
        total_apis = 5  # Known total APIs

    # Data quality indicators for system status
    cost_available = dashboard_data and dashboard_data.total_cost_average > 0
    carbon_available = dashboard_data and dashboard_data.carbon_intensity

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🟢 Running Instances",
            f"{running_instances}/{total_instances}",
            help="Active EC2 instances included in cost and carbon calculations. Stopped instances are tracked but don't consume power."
        )

    with col2:
        st.metric(
            "🔗 API Health",
            f"{apis_online}/{total_apis} online",
            help="Number of external APIs successfully responding. Includes AWS (CloudTrail, CloudWatch, Cost Explorer, Pricing), ElectricityMaps, and Boavizta."
        )

    with col3:
        st.metric(
            "💰 Cost Data",
            f"{'✅ Live' if cost_available else '❌ Missing'}",
            help="AWS Cost Explorer provides aggregated EC2 costs for validation. Used to compare against instance-specific calculations (CloudTrail × Pricing API)."
        )

    with col4:
        st.metric(
            "🌍 Carbon Data",
            f"{'✅ Live' if carbon_available else '❌ Missing'}",
            help="ElectricityMaps provides real-time German grid carbon intensity (g CO₂/kWh). Updated hourly, cached for 1 hour. Essential for carbon-aware scheduling."
        )

    api_health = getattr(dashboard_data, "api_health_status", {}) if dashboard_data else {}
    if api_health:
        # Standardized API service names and roles
        role_map = {
            "ElectricityMaps": "Grid carbon intensity (1 h cache)",
            "Boavizta": "Power models (7 day cache)",
            "AWS Pricing": "Instance pricing (7 day cache)",
            "AWS Cost Explorer": "Aggregated cost comparison (24 h cache)",
            "AWS CloudWatch": "CPU utilisation (1 h cache)",
            "AWS CloudTrail": "Instance-specific runtime (3 h cache)",
        }

        # Normalize service names to standard format
        display_labels = {
            "CloudWatch": "AWS CloudWatch",
            "CloudTrail": "AWS CloudTrail",
            "Aws Cloudwatch": "AWS CloudWatch",
            "Aws Cloudtrail": "AWS CloudTrail",
            "AWS Cloudwatch": "AWS CloudWatch",
            "AWS Cloudtrail": "AWS CloudTrail",
        }

        status_rows: list[dict[str, str]] = []
        berlin_tz = ZoneInfo("Europe/Berlin")

        for service, status in sorted(api_health.items()):
            label = display_labels.get(service, service.replace("_", " "))
            state = getattr(status, "status", "unknown").replace("_", " ").title()
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

            status_rows.append(
                {
                    "Service": label,
                    "Status": f"{icon} {state}",
                    "Last check": checked_at,
                    "Last API call": last_api_call,
                    "Role": role,
                }
            )

        df = pd.DataFrame(status_rows)
        st.dataframe(df, hide_index=True, width="stretch")


def _render_precision_insights(dashboard_data: DashboardData) -> None:
    """Render precision and validation insights with actual calculations."""
    st.markdown("### 🎯 Precision & Data Quality")
    st.caption("Measurement accuracy and data completeness metrics")

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
    measured_runtime = len([i for i in dashboard_data.instances if getattr(i, "runtime_hours", None) is not None])
    pricing_available = len([i for i in dashboard_data.instances if getattr(i, "hourly_price_usd", None)])
    measured_quality = len([i for i in dashboard_data.instances if getattr(i, "data_quality", "") == "measured"])

    validation_factor = getattr(dashboard_data, "validation_factor", None)
    # Type-safe validation: ensure it's a number
    if not isinstance(validation_factor, (int, float)):
        validation_factor = None

    accuracy_status = getattr(dashboard_data, "accuracy_status", "UNKNOWN") or "UNKNOWN"
    if not isinstance(accuracy_status, str):
        accuracy_status = "UNKNOWN"

    runtime_pct = (measured_runtime / total_instances * 100) if total_instances else 0
    pricing_pct = (pricing_available / total_instances * 100) if total_instances else 0
    measured_pct = (measured_quality / total_instances * 100) if total_instances else 0

    row1_col1, row1_col2, row1_col3 = st.columns(3)

    with row1_col1:
        st.metric(
            "Runtime Coverage",
            f"{runtime_pct:.0f}%",
            f"{measured_runtime}/{total_instances} instances",
            help="Percentage of instances with CloudTrail runtime data (Start/Stop events). High coverage (≥90%) enables accurate cost calculations. Low values indicate CloudTrail retention gaps or permission issues."
        )

    with row1_col2:
        st.metric(
            "Pricing Coverage",
            f"{pricing_pct:.0f}%",
            f"{pricing_available}/{total_instances} instances",
            help="Percentage of instances with AWS Pricing API data (hourly on-demand rates). 100% coverage expected for all public instance types. Missing data indicates API issues or unsupported regions."
        )

    with row1_col3:
        st.metric(
            "Measured Quality",
            f"{measured_pct:.0f}%",
            f"{measured_quality}/{total_instances} instances",
            help="Percentage of instances with complete data (runtime + pricing + power + CPU). 'Measured' quality means all calculations use real data, not estimates. Target: 100%."
        )

    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row2_col1:
        cost_comparison_help = (
            "Compares instance-specific calculations (CloudTrail runtime × Pricing API) with AWS Cost Explorer EC2 costs. "
            "Deviations occur due to: (1) CloudTrail runtime precision (±5% target), (2) on-demand pricing vs. actual billing "
            "(reserved instances, savings plans), (3) additional EC2 charges (data transfer, EBS-optimized fees). "
            "Close match (±30%) validates calculation accuracy."
        )

        if validation_factor is not None:
            delta_pct = abs(1 - validation_factor) * 100

            if validation_factor > 100:
                st.metric(
                    "📊 Cost Validation",
                    "Explorer >> Calculated",
                    f"{validation_factor:.1f}× higher",
                    help=cost_comparison_help
                )
            elif validation_factor > 10:
                st.metric(
                    "📊 Cost Validation",
                    "Explorer much higher",
                    f"{validation_factor:.1f}× higher",
                    help=cost_comparison_help
                )
            elif validation_factor > 2:
                st.metric(
                    "📊 Cost Validation",
                    "Explorer higher",
                    f"{validation_factor:.1f}× higher",
                    help=cost_comparison_help
                )
            elif delta_pct <= 30:
                st.metric(
                    "📊 Cost Validation",
                    "✅ Close match",
                    f"±{delta_pct:.0f}%",
                    help=cost_comparison_help
                )
            elif delta_pct <= 60:
                st.metric(
                    "📊 Cost Validation",
                    "Moderate diff",
                    f"±{delta_pct:.0f}%",
                    help=cost_comparison_help
                )
            else:
                st.metric(
                    "📊 Cost Validation",
                    "Large diff",
                    f"±{delta_pct:.0f}%",
                    help=cost_comparison_help
                )
        else:
            st.metric(
                "📊 Cost Validation",
                "Calculating...",
                "Fetching Cost Explorer",
                help=cost_comparison_help
            )

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
            help="Overall data quality score combining runtime coverage, pricing availability, and measurement completeness. "
                 "High (≥80%): Excellent for production decisions. Moderate (50-80%): Suitable for trends. Low (<50%): Indicative only."
        )

    with row2_col3:
        cloudtrail_coverage = getattr(dashboard_data, "cloudtrail_coverage", None)
        # Type-safe validation: ensure it's a number
        if not isinstance(cloudtrail_coverage, (int, float)):
            cloudtrail_coverage = None

        cloudtrail_tracked = getattr(dashboard_data, "cloudtrail_tracked_instances", None) or 0
        if not isinstance(cloudtrail_tracked, int):
            cloudtrail_tracked = 0

        if cloudtrail_coverage is not None:
            coverage_pct = cloudtrail_coverage * 100
            if coverage_pct >= 90:
                status_label = "Excellent"
                status_icon = "📋 Runtime Data Quality"
            elif coverage_pct >= 70:
                status_label = "Good"
                status_icon = "📋 Runtime Data Quality"
            elif coverage_pct >= 50:
                status_label = "Moderate"
                status_icon = "⚠️ Runtime Data Quality"
            else:
                status_label = "Low"
                status_icon = "⚠️ Runtime Data Quality"

            st.metric(
                status_icon,
                f"{coverage_pct:.0f}%",
                f"{cloudtrail_tracked}/{total_instances} tracked · {status_label}",
                help="Percentage of instances with CloudTrail runtime data. "
                     "High coverage (≥90%) ensures accurate cost calculations. "
                     "Low values indicate CloudTrail retention or permission issues."
            )
        else:
            st.metric("📋 Runtime Data Quality", "n/a", "Calculating...")

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

    # NEW: Document calculation assumptions
    with st.expander("📝 Calculation Assumptions & Constants", expanded=False):
        from src.domain.constants import AcademicConstants

        eur_usd_rate = AcademicConstants.get_eur_usd_rate()

        st.markdown(f"""
        **Currency Conversion:**
        - **EUR/USD Rate**: {eur_usd_rate:.4f} (1 USD = {eur_usd_rate:.4f} EUR)
        - **Source**: European Central Bank (ECB) official rates
        - **Configurable**: Set via `EUR_USD_RATE` environment variable in `.env`
        - **Usage**: All costs calculated in USD (AWS Pricing API) are converted to EUR for display
        - **Formula**: `cost_eur = cost_usd × {eur_usd_rate:.4f}`

        **Calculation Methods:**
        - **24h Projected**: Uses last 24h data × 30 for monthly projection
        - **30d Actual**: Uses total runtime from last 30 days for monthly calculation
        - **Validation**: Cost Explorer comparison uses 30d actual (not projected) for factual validation

        **Power Consumption Model:**
        - **Idle Power**: 30% of peak power (constant baseline)
        - **Variable Power**: 70% of peak power (scales linearly with CPU utilization)
        - **Source**: Barroso & Hölzle (2007) - "The Case for Energy-Proportional Computing"

        **Academic Constants:**
        - **EU ETS Price**: €{AcademicConstants.EU_ETS_PRICE_PER_TONNE:.2f}/tonne CO₂ (European Energy Exchange market data)
        - **Hours per Month**: {AcademicConstants.HOURS_PER_MONTH} hours (365.25 × 24 ÷ 12)

        **Note**: These assumptions are documented for thesis transparency and can be adjusted as needed.
        """)

        st.caption("💡 For methodology details, see docs/methodology/ in the repository.")

        st.info(
            "💡 **Academic outlook**: With sufficient runtime history, AWS CloudTrail can reach ±5% accuracy; currently only indicative estimates (≈±40%) are available."
        )
