"""
Business Case Component
Displays business impact, CSRD readiness, and optimization recommendations
"""

import streamlit as st
from datetime import datetime, timezone
from typing import Optional, Any
from src.domain.models import DashboardData
from src.domain.constants import AcademicConstants


def render_business_insights(
    dashboard_data: Optional[DashboardData], carbon_series: list[tuple[datetime, float]]
) -> None:
    """
    Render business case insights including savings, CSRD readiness, and recommendations.

    Args:
        dashboard_data: Complete dashboard data
        carbon_series: Historical carbon intensity data points
    """
    if not dashboard_data:
        return

    _render_business_case_summary(dashboard_data)
    _render_csrd_readiness(dashboard_data)
    _render_carbon_scheduling_insight(dashboard_data, carbon_series)
    _render_action_recommendations(dashboard_data, carbon_series)


def _render_business_case_summary(dashboard_data: DashboardData) -> None:
    """Render quick business case summary for SME decision makers."""
    if not dashboard_data.business_case:
        st.info("💡 **Quick Insight**: Carbon-aware scheduling can reduce both costs and emissions by 8-15% typically")
        return

    st.markdown("### 📈 Business Impact Summary")
    st.caption("Optimization potential based on McKinsey and MIT research")

    business_case = dashboard_data.business_case

    def _format_eur(amount: float) -> str:
        """Format EUR values with precision that keeps small amounts visible."""
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
        """Format CO₂ values to avoid rounding tiny improvements to zero."""
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
            "vs current spending",
            help="Estimated monthly cost savings from carbon-aware scheduling and office-hours optimization. "
                 "Based on moderate scenario (15-25% factors from McKinsey). Adjusted for infrastructure size and data quality. "
                 "Conservative estimate requires empirical validation."
        )
        st.metric(
            "Annual ROI",
            _format_eur((business_case.integrated_savings_eur or 0.0) * 12),
            "yearly optimization",
            help="Annualized savings projection (monthly × 12). Assumes consistent optimization over time. "
                 "Actual ROI depends on workload patterns, reserved instance coverage, and implementation effort."
        )

    with impact_col2:
        st.markdown("**🌍 Environmental Impact**")
        current_co2 = dashboard_data.total_co2_kg
        co2_savings = business_case.integrated_co2_reduction_kg or (current_co2 * 0.08 if current_co2 else 0.0)
        st.metric(
            "CO₂ Reduction",
            f"{_format_co2(co2_savings)} /month",
            "Literature-aligned" if business_case.integrated_co2_reduction_kg else "Heuristic (8%)",
            help="Monthly CO₂ emission reduction from carbon-aware workload scheduling. Based on MIT research showing "
                 "15-35% reduction potential. Uses same scenario factors as cost savings for consistency."
        )

        # EU carbon pricing sensitivity
        eu_carbon_value = (co2_savings / 1000) * AcademicConstants.EU_ETS_PRICE_PER_TONNE if co2_savings else 0.0
        st.metric(
            "Carbon Value",
            f"{_format_eur(eu_carbon_value)}/month",
            "EU ETS sensitivity",
            help=f"Monetary value of CO₂ reduction at current EU ETS price (~€{AcademicConstants.EU_ETS_PRICE_PER_TONNE}/tonne). "
                 "Indicates financial impact if carbon pricing expands to cloud computing. Currently informational only."
        )


def _render_csrd_readiness(dashboard_data: DashboardData) -> None:
    """Show CSRD readiness indicators for German SMEs."""
    with st.expander("🏛️ **CSRD Readiness Snapshot** - Compliance Dashboard", expanded=False):
        st.markdown("""
        **What this shows:**
        - Scope 2: live grid intensity via ElectricityMaps (German compliance view)
        - Scope 3: percentage of instances with measured emissions (AWS CloudTrail + Boavizta)
        - FinOps Controls: cost validation coverage (Cost Explorer) and runtime tracking completeness
        """)

        total_instances = len(dashboard_data.instances)
        measured_instances = len([i for i in dashboard_data.instances if getattr(i, "data_quality", "") == "measured"])
        runtime_tracked = len([i for i in dashboard_data.instances if getattr(i, "runtime_hours", None) is not None])

        grid_available = dashboard_data.carbon_intensity is not None
        cost_available = dashboard_data.total_cost_eur > 0

        col1, col2, col3 = st.columns(3)

        with col1:
            scope2_status = "✅ Live" if grid_available else "⚠️ Missing"
            grid_value = dashboard_data.carbon_intensity.value if grid_available else 0
            st.metric(
                "Scope 2 – Grid",
                f"{grid_value:.0f} g CO₂/kWh" if grid_available else "No data",
                scope2_status,
                help="Scope 2: Indirect emissions from purchased electricity. ElectricityMaps provides hourly German grid "
                     "carbon intensity for CSRD location-based reporting. Market-based reporting requires supplier-specific data."
            )

        with col2:
            if total_instances:
                measured_ratio = measured_instances / total_instances * 100
                st.metric(
                    "Scope 3 – Cloud",
                    f"{measured_ratio:.0f}% covered",
                    f"{measured_instances}/{total_instances} measured",
                    help="Scope 3 Category 1: Purchased cloud services emissions. Calculated using Boavizta power models + "
                         "CloudTrail runtime tracking. 100% coverage means all instances have measured emissions data for CSRD reporting."
                )
            else:
                st.metric(
                    "Scope 3 – Cloud",
                    "0%",
                    "No instances",
                    help="Scope 3 Category 1: Purchased cloud services emissions."
                )

        with col3:
            validation_badge = "✅" if cost_available and runtime_tracked == total_instances else "⚠️"
            st.metric(
                "FinOps Controls",
                f"{validation_badge} Cost + Runtime",
                f"{runtime_tracked}/{total_instances} tracked",
                help="FinOps control validation for CSRD audit trails. Combines AWS Cost Explorer (financial controls) with "
                     "CloudTrail runtime tracking (operational evidence). Required for demonstrating cost-emission correlation."
            )

        st.info(
            "📘 **Interpretation**: CSRD reporting needs reliable Scope 2/3 evidence. Once every instance provides runtime and emission data, the prototype is ready for reporting."
        )


def _render_carbon_scheduling_insight(
    dashboard_data: DashboardData, carbon_series: list[tuple[datetime, float]]
) -> None:
    """Summarise low-carbon scheduling opportunities from 24h series."""
    st.markdown("### ⏱️ Carbon-Aware Scheduling Window")
    st.caption("24-hour grid analysis for optimal workload timing")

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
        st.metric(
            "Current Intensity",
            f"{current_value:.0f} g CO₂/kWh",
            "Now",
            help="Current German grid carbon intensity. Lower values indicate cleaner energy mix (more renewables). "
                 "Updated hourly via ElectricityMaps."
        )

    with schedule_col2:
        st.metric(
            "Best Slot (24h)",
            f"{best_value:.0f} g CO₂/kWh",
            best_time.strftime("%a %H:%M"),
            help="Lowest carbon intensity observed in the past 24 hours. This represents the optimal time for "
                 "carbon-aware workload scheduling. Typically occurs during midday (solar peak) or windy periods."
        )

    with schedule_col3:
        delta_text = f"-{potential_delta:.0f} g ({potential_pct:.0f}%)" if potential_delta > 0 else "Stable"
        st.metric(
            "Reduction Potential",
            delta_text,
            "vs. now",
            help="Potential CO₂ reduction if current workloads shifted to the best 24h slot. Percentage indicates "
                 "emission savings achievable through time-shifting batch jobs, CI/CD pipelines, or development environments."
        )


def _render_action_recommendations(dashboard_data: DashboardData, carbon_series: list[tuple[datetime, float]]) -> None:
    """Highlight top optimisation ideas for SME decision makers."""
    st.markdown("### 🎯 Action Recommendations")
    st.caption("Prioritized optimization opportunities for cost and carbon reduction")

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

    if not recommendations:
        st.success("All instances run efficiently – no immediate actions required.")
        return

    for rec in recommendations:
        st.markdown(f"- {rec}")
