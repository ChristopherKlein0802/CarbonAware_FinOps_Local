"""
Executive Summary / Overview Page
Professional SME-focused dashboard with German grid status and business value
"""

import streamlit as st
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Optional

from src.constants import AcademicConstants
from src.utils.ui import determine_grid_status, calculate_weighted_tradeoff
from src.utils.performance import (
    render_4_column_metrics,
    render_grid_status_hero
)


def _load_recent_carbon_series() -> list[tuple[datetime, float]]:
    """Fetch and normalize the latest 24h carbon intensity series."""
    try:
        from src.api.client import unified_api_client

        historical_data = unified_api_client.electricity_api.get_carbon_intensity_24h("eu-central-1")
        if not historical_data:
            historical_data = unified_api_client.electricity_api.get_self_collected_24h_data("eu-central-1")
    except Exception as error:  # pragma: no cover - external API resilience
        st.warning(f"⚠️ Unable to load 24h carbon data: {error}")
        return []

    if not historical_data:
        return []

    normalized_points: dict[datetime, float] = {}
    for point in historical_data:
        timestamp_raw = point.get("datetime") or point.get("hour_key")
        if not timestamp_raw:
            continue

        try:
            ts = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        value = point.get("carbonIntensity") or point.get("value")
        if value is None:
            continue
        try:
            normalized_points[ts] = float(value)
        except (TypeError, ValueError):
            continue

    sorted_points = sorted((ts.astimezone(), value) for ts, value in normalized_points.items())
    return sorted_points


def _render_compact_grid_status(dashboard_data: Any) -> None:
    """Render compact German Grid Status"""
    if dashboard_data.carbon_intensity:
        grid_status = dashboard_data.carbon_intensity.value

        # Use centralized grid status logic
        status_color, status_text, _ = determine_grid_status(grid_status)

        # Compact display
        st.info(f"{status_color} **German Grid: {grid_status:.0f} g CO₂/kWh** ({status_text})")
    else:
        st.warning("⚠️ No carbon intensity data available")


def _render_core_metrics(dashboard_data: Any) -> None:
    """Render core business metrics - simplified for SME"""
    total_cost = dashboard_data.total_cost_eur
    total_co2 = dashboard_data.total_co2_kg

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - **Monthly costs** derive from live AWS Cost Explorer data (6 h cache).
            - **Carbon footprint** combines ElectricityMaps intensity with Boavizta power models.
            """
        )

    # Data quality assessment
    cost_quality = "🟢 Real API" if total_cost > 0 else "🔴 No Data"
    co2_quality = "🟢 Real API" if total_co2 > 0 else "🔴 No Data"

    # Check data sources
    has_real_cost = dashboard_data.total_cost_eur > 0
    has_carbon_data = dashboard_data.carbon_intensity is not None
    has_instance_data = len(dashboard_data.instances) > 0

    # Core metrics with quality badges
    col1, col2 = st.columns(2)

    with col1:
        st.metric("💰 Monthly Costs", f"€{total_cost:.2f}", f"AWS Cost Explorer - {cost_quality}")
        if not has_real_cost:
            st.warning("⚠️ No real AWS cost data")

    with col2:
        st.metric("🌍 Carbon Footprint", f"{total_co2:.2f} kg CO₂", f"ElectricityMaps+Boavizta - {co2_quality}")
        if not has_carbon_data:
            st.warning("⚠️ No real carbon data")


def _render_system_status(dashboard_data: Any) -> None:
    """Render current system status"""
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
        import pandas as pd

        role_map = {
            "ElectricityMaps": "Grid carbon intensity (30 min cache)",
            "Boavizta": "Power models (7 day cache)",
            "AWS Pricing": "Instance pricing (7 day cache)",
            "AWS Cost Explorer": "Cost validation (6 h cache)",
            "AWS CloudWatch": "CPU utilisation (3 h cache)",
            "AWS CloudTrail": "Runtime tracking (24 h cache)",
            "CloudWatch": "CPU utilisation (3 h cache)",
            "CloudTrail": "Runtime tracking (24 h cache)"
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


def _render_csrd_readiness(dashboard_data: Any) -> None:
    """Show CSRD readiness indicators for German SMEs."""
    st.markdown("### 🏛️ CSRD Readiness Snapshot")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Scope 2: live grid intensity via ElectricityMaps (German compliance view).
            - Scope 3: percentage of instances with measured emissions (AWS CloudTrail + Boavizta).
            - FinOps Controls: cost validation coverage (Cost Explorer) and runtime tracking completeness.
            """
        )

    total_instances = len(dashboard_data.instances)
    measured_instances = len([
        i for i in dashboard_data.instances if getattr(i, "data_quality", "") == "measured"
    ])
    runtime_tracked = len([
        i for i in dashboard_data.instances if getattr(i, "runtime_hours", None) is not None
    ])

    grid_available = dashboard_data.carbon_intensity is not None
    cost_available = dashboard_data.total_cost_eur > 0

    col1, col2, col3 = st.columns(3)

    with col1:
        scope2_status = "✅ Live" if grid_available else "⚠️ Missing"
        grid_value = dashboard_data.carbon_intensity.value if grid_available else 0
        st.metric("Scope 2 – Grid", f"{grid_value:.0f} g CO₂/kWh" if grid_available else "No data", scope2_status)
        st.caption("ElectricityMaps live feed for German grid")

    with col2:
        if total_instances:
            measured_ratio = measured_instances / total_instances * 100
            st.metric("Scope 3 – Cloud", f"{measured_ratio:.0f}% covered", f"{measured_instances}/{total_instances} measured")
        else:
            st.metric("Scope 3 – Cloud", "0%", "No instances")
        st.caption("Boavizta + AWS CloudTrail coverage for emissions")

    with col3:
        validation_badge = "✅" if cost_available and runtime_tracked == total_instances else "⚠️"
        st.metric("FinOps Controls", f"{validation_badge} AWS Cost + Runtime", f"Runtime data for {runtime_tracked}/{total_instances}")
        st.caption("Required for CSRD audit trails")

    st.info("📘 **Interpretation**: CSRD reporting needs reliable Scope 2/3 evidence. Once every instance provides runtime and emission data, the prototype is ready for reporting.")


def _render_carbon_scheduling_insight(dashboard_data: Any, carbon_series: list[tuple[datetime, float]]) -> None:
    """Summarise low-carbon scheduling opportunities from 24h series."""
    st.markdown("### ⏱️ Carbon-Aware Scheduling Window")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Compares the current grid intensity with the lowest value observed in the past 24 hours.
            - Highlights potential CO₂ savings (%) if workloads shift to the low-carbon slot.
            """
        )

    if not dashboard_data.carbon_intensity or not carbon_series:
        st.warning("⚠️ 24h carbon dataset not complete yet – see Carbon tab for details.")
        return

    current_value = dashboard_data.carbon_intensity.value
    best_point = min(carbon_series, key=lambda entry: entry[1], default=None)

    if not best_point:
        st.warning("⚠️ Not enough datapoints for scheduling analysis")
        return

    best_time, best_value = best_point
    potential_delta = current_value - best_value
    potential_pct = (potential_delta / current_value * 100) if current_value else 0

    schedule_col1, schedule_col2, schedule_col3 = st.columns(3)

    with schedule_col1:
        st.metric("Current intensity", f"{current_value:.0f} g CO₂/kWh", "Now")

    with schedule_col2:
        st.metric("Lowest slot", f"{best_value:.0f} g CO₂/kWh", best_time.strftime("%a %H:%M"))

    with schedule_col3:
        delta_text = f"-{potential_delta:.0f} g ({potential_pct:.0f}%)" if potential_delta > 0 else "Stable"
        st.metric("Shift potential", delta_text, "vs. now")



def _render_action_recommendations(dashboard_data: Any, carbon_series: list[tuple[datetime, float]]) -> None:
    """Highlight top optimisation ideas for SME decision makers."""
    st.markdown("### 🎯 Top Action Recommendations")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Right-sizing suggestions derived from low CPU utilisation metrics (AWS CloudWatch).
            """
        )

    instances = dashboard_data.instances or []
    if not instances:
        st.info("No instances available – no actions required")
        return

    recommendations: list[str] = []

    low_cpu_candidates = []
    for inst in instances:
        state_value = (getattr(inst, "state", "") or "").lower()
        cpu_value = getattr(inst, "cpu_utilization", None)
        if state_value == "running" and cpu_value is not None and cpu_value < 15:
            low_cpu_candidates.append(inst)
    for inst in sorted(low_cpu_candidates, key=lambda i: (i.monthly_cost_eur or 0), reverse=True):
        name = inst.instance_name or inst.instance_id
        recommendations.append(
            f"💤 **Rightsize {name}** – {inst.cpu_utilization:.1f}% CPU at €{(inst.monthly_cost_eur or 0):.2f}/month."
            " Consider a smaller instance class or automated stop scheduling."
        )

    missing_runtime = [inst for inst in instances if getattr(inst, "runtime_hours", None) is None]
    if missing_runtime:
        recommendations.append(
            "📡 **Keep AWS CloudTrail active** – "
            f"runtime data missing for {len(missing_runtime)} instance(s). Maintain `aws cloudtrail` logging for CSRD-ready audit trails."
        )

    # Scheduling tip omitted: current dataset only contains historical slots without forecast

    if not recommendations:
        st.success("All instances run efficiently – no immediate actions required.")
        return

    for rec in recommendations:
        st.markdown(f"- {rec}")



def _render_precision_insights(dashboard_data: Any) -> None:
    """Render precision and validation insights with actual calculations"""
    st.markdown("### 🎯 Precision & Data Quality")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Coverage metrics show what share of instances has runtime, pricing, and fully measured data.
            - "Cost validation" compares calculated costs with AWS Cost Explorer to assess accuracy.
            - "Data precision" summarises overall measurement coverage across all instances.
            """
        )

    if not dashboard_data or not dashboard_data.instances:
        st.warning("No data available for precision analysis")
        return

    # Add data quality validation
    from src.utils.validation import validate_dashboard_data, get_data_quality_score
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

    col1, col2, col3 = st.columns(3)

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
                st.metric("📊 Cost Validation", "Runtime limited", "Need more runtime data")
            elif validation_factor > 10:
                st.metric("📊 Cost Validation", "Building", f"Factor {validation_factor:.1f}")
            elif delta_pct <= 30:
                st.metric("📊 Cost Validation", "Excellent", f"±{delta_pct:.0f}% vs AWS")
            elif delta_pct <= 60:
                st.metric("📊 Cost Validation", "Good", f"±{delta_pct:.0f}% vs AWS")
            else:
                accuracy_label = accuracy_status or "Variance"
                if "-" in accuracy_label:
                    accuracy_label = accuracy_label.split("-")[0].strip()
                accuracy_label = accuracy_label.title()
                st.metric("📊 Cost Validation", accuracy_label, f"±{delta_pct:.0f}% vs AWS")
        else:
            st.metric("📊 Cost Validation", "No data", "Fetching AWS costs...")

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


def render_overview_page(dashboard_data: Optional[Any]) -> None:
    """
    Render the executive summary overview page - SME focused

    Args:
        dashboard_data: Complete dashboard data object with instances and metrics
    """
    st.header("🏆 Executive Summary - Carbon-Aware FinOps")

    if not dashboard_data or not dashboard_data.instances:
        st.warning("⚠️ No infrastructure data available. Check API connections.")
        return

    # Core sections - simplified for SME decision makers
    _render_compact_grid_status(dashboard_data)
    _render_core_metrics(dashboard_data)

    # Quick business case summary
    _render_business_case_summary(dashboard_data)
    _render_tradeoff_controls(dashboard_data)
    _render_cost_carbon_alignment(dashboard_data)

    st.markdown("---")

    carbon_series = _load_recent_carbon_series()

    _render_csrd_readiness(dashboard_data)
    _render_carbon_scheduling_insight(dashboard_data, carbon_series)
    _render_action_recommendations(dashboard_data, carbon_series)

    st.markdown("---")

    _render_system_status(dashboard_data)
    _render_precision_insights(dashboard_data)


def _render_business_case_summary(dashboard_data: Any) -> None:
    """Render quick business case summary for SME decision makers"""
    if not dashboard_data or not dashboard_data.business_case:
        st.info("💡 **Quick Insight**: Carbon-aware scheduling can reduce both costs and emissions by 8-15% typically")
        return

    st.markdown("### 📈 Business Impact Summary")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - **Monthly savings / ROI** are derived from the `BusinessCaseCalculator` moderate scenario (literature-based 15–25 % factors).
            - **CO₂ reduction** reuses the same scenario factors applied to the measured baseline footprint.
            - The EU ETS value estimates the monetary impact of the reported CO₂ reduction.
            - Sources: McKinsey [7] for cost factors, MIT carbon-aware scheduling [20] for emissions.
            """
        )

    business_case = dashboard_data.business_case

    def _format_eur(amount: float) -> str:
        """Format EUR values with precision that keeps small amounts visible"""
        if amount is None:
            return "€0.00"
        absolute = abs(amount)
        if absolute >= 1000:
            return f"€{amount:,.0f}".replace(",", " ")
        if absolute >= 100:
            return f"€{amount:,.0f}"
        if absolute >= 10:
            return f"€{amount:,.1f}"
        return f"€{amount:.2f}"

    def _format_co2(amount: float) -> str:
        """Format CO₂ values to avoid rounding tiny improvements to zero"""
        if amount is None:
            return "0.00 kg"
        absolute = abs(amount)
        if absolute >= 100:
            return f"{amount:.0f} kg"
        if absolute >= 10:
            return f"{amount:.1f} kg"
        return f"{amount:.2f} kg"

    # Visual business case with simple graphics
    impact_col1, impact_col2 = st.columns(2)

    with impact_col1:
        st.markdown("**💰 Financial Impact**")
        st.metric(
            "Monthly Savings",
            _format_eur(business_case.integrated_savings_eur),
            "vs current spending"
        )
        st.metric(
            "Annual ROI",
            _format_eur((business_case.integrated_savings_eur or 0.0) * 12),
            "yearly optimization"
        )

    with impact_col2:
        st.markdown("**🌍 Environmental Impact**")
        current_co2 = dashboard_data.total_co2_kg
        co2_savings = business_case.integrated_co2_reduction_kg or (current_co2 * 0.08 if current_co2 else 0.0)
        st.metric(
            "CO₂ Reduction",
            f"{_format_co2(co2_savings)} /month",
            "Literature-aligned scenario" if business_case.integrated_co2_reduction_kg else "Heuristic (8%)"
        )

        # EU carbon pricing Sensitivität
        eu_carbon_value = (co2_savings / 1000) * AcademicConstants.EU_ETS_PRICE_PER_TONNE if co2_savings else 0.0
        st.metric(
            "Carbon Value",
            f"{_format_eur(eu_carbon_value)}/month",
            "EU ETS sensitivity"
        )


def _render_tradeoff_controls(dashboard_data: Any) -> None:
    """Interactive slider to explore cost/CO₂ trade-offs."""

    baseline_cost = getattr(dashboard_data, "total_cost_eur", 0.0) or 0.0
    baseline_co2 = getattr(dashboard_data, "total_co2_kg", 0.0) or 0.0

    if baseline_cost <= 0 and baseline_co2 <= 0:
        st.info("⚠️ No valid baseline data – trade-off explorer requires real cost and CO₂ measurements.")
        return

    st.markdown("### ⚖️ Cost vs CO₂ Trade-off Explorer")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - The slider changes the weighting between cost and CO₂ priorities (0 % = full CO₂ focus, 100 % = full cost focus).
            - Scenario factors (10 % conservative / 20 % moderate) stem from the same literature as the Business Impact summary (McKinsey [7], MIT carbon-aware scheduling [20]).
            - Outputs show the adjusted cost and CO₂ reductions plus the absolute savings (EUR / kg CO₂).
            """
        )

    cost_weight = st.slider(
        "Cost vs. CO₂ priority",
        min_value=0,
        max_value=100,
        value=60,
        step=5,
        help="0% = full CO₂ priority, 100% = full cost priority",
        key="tradeoff_weight_slider",
    )

    tradeoff = calculate_weighted_tradeoff(baseline_cost, baseline_co2, cost_weight)

    def _fmt_currency(value: float) -> str:
        if value >= 100:
            return f"€{value:,.0f}".replace(",", " ")
        if value >= 10:
            return f"€{value:,.1f}"
        return f"€{value:.2f}"

    def _fmt_co2(value: float) -> str:
        if value >= 10:
            return f"{value:.1f} kg"
        return f"{value:.3f} kg"

    col1, col2, col3 = st.columns(3)

    summary_text = (tradeoff["summary"]
                    .replace("Kostenfokus", "cost priority")
                    .replace("Kostensenkung", "cost reduction")
                    .replace("CO₂-Reduktion", "CO₂ reduction"))

    with col1:
        st.metric("Cost priority", f"{cost_weight}%", summary_text)

    with col2:
        st.metric(
            "Expected cost reduction",
            _fmt_currency(tradeoff["cost_reduction"]),
            f"{tradeoff['cost_factor']:.1%} scenario"
        )

    with col3:
        st.metric(
            "Expected CO₂ reduction",
            _fmt_co2(tradeoff["co2_reduction"]),
            f"{tradeoff['co2_factor']:.1%} scenario"
        )



def _render_cost_carbon_alignment(dashboard_data: Any) -> None:
    """Visualise hourly cost and CO₂ data to evidence TAC."""

    series = getattr(dashboard_data, "time_series", []) or []
    st.markdown("### ⏱️ Cost & CO₂ Trend (last 24 h)")

    with st.expander("ℹ️ What this section shows", expanded=False):
        st.markdown(
            """
            - Combines the past 24 hours of EC2 costs (AWS Cost Explorer, hourly granularity) with ElectricityMaps carbon intensity.
            - TAC (Time Alignment Coverage) reports how many hourly cost points have matching carbon data (>95 % required by R1).
            - Cost MAPE compares calculated costs vs. Cost Explorer and supports Requirement R2 (target <10 %).
            """
        )

    if not series:
        st.info("No historical datapoints yet – the dashboard will collect new values with each run.")
        return

    import pandas as pd  # Local import to avoid global dependency during tests
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
            st.metric("Cost MAPE", "n/a")
