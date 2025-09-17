"""
Competitive Analysis Page
Theoretical competitive analysis for academic research
"""

import streamlit as st
import pandas as pd
from typing import Any, Optional

from src.utils.performance import optimize_dataframe_display


def _render_comparison_matrix() -> None:
    """Render the tool comparison matrix"""
    st.markdown("### 📊 Tool Comparison Matrix")

    comparison_data = {
        "Feature": [
            "Real-time Carbon Data",
            "AWS Cost Integration",
            "Business Case Generator",
            "German Grid Specificity",
            "SME Focus (≤100 instances)",
            "Optimization Scheduling",
            "EU Compliance Support",
            "Implementation Time",
            "Monthly Cost"
        ],
        "Our Integrated Tool": [
            "✅ ElectricityMaps API (30min)",
            "✅ Cost Explorer + Pricing API",
            "✅ ROI calculator with scenarios",
            "✅ German grid real-time data",
            "✅ SME-optimized approach",
            "✅ Carbon + Cost optimization",
            "✅ EU ETS integration",
            "🟢 3 days",
            "🟢 €20/month API costs"
        ],
        "Separate Tools": [
            "⚠️ Multiple subscriptions needed",
            "⚠️ Manual correlation required",
            "❌ No integrated business case",
            "❌ Generic EU averages only",
            "❌ Enterprise-focused pricing",
            "❌ Separate optimizations",
            "⚠️ Manual compliance tracking",
            "🟡 2-4 weeks",
            "🔴 €200+/month combined"
        ],
        "Cloud Carbon Footprint": [
            "❌ Historical averages only",
            "✅ AWS integration",
            "❌ Reporting only",
            "❌ Global averages",
            "✅ Open source",
            "❌ No scheduling",
            "❌ Limited compliance",
            "🟡 1-2 weeks",
            "🟢 Free (self-hosted)"
        ]
    }

    comparison_df = pd.DataFrame(comparison_data)
    optimize_dataframe_display(comparison_df, "tool_comparison")


def _render_integration_scenarios(dashboard_data: Any) -> None:
    """Render theoretical integration advantage scenarios"""
    if not dashboard_data or not dashboard_data.instances:
        return

    st.markdown("### 📈 Theoretical Integration Scenarios")
    st.markdown("*⚠️ Academic Note: Scenarios based on literature estimates - require empirical validation*")

    total_cost = dashboard_data.total_cost_eur

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔴 Separate Tools**")
        separate_savings = total_cost * 0.25  # 25% separate optimization
        st.metric("Savings", f"€{separate_savings:.2f}", "Cost OR Carbon")
        st.metric("Tool Cost", "€200/month", "Multiple tools")
        st.metric("Net ROI", f"€{separate_savings - 200:.2f}", "Limited synergy")

    with col2:
        st.markdown("**🟡 Single Tool**")
        single_savings = total_cost * 0.28  # 28% single tool
        st.metric("Savings", f"€{single_savings:.2f}", "Generic optimization")
        st.metric("Tool Cost", "€50/month", "Single subscription")
        st.metric("Net ROI", f"€{single_savings - 50:.2f}", "No integration")

    with col3:
        st.markdown("**🟢 Our Integration**")
        if dashboard_data.business_case:
            integrated_savings = dashboard_data.business_case.integrated_savings_eur
        else:
            integrated_savings = total_cost * 0.32  # 32% integrated
        st.metric("Savings", f"€{integrated_savings:.2f}", "Carbon + Cost synergy")
        st.metric("Tool Cost", "€20/month", "API only")
        st.metric("Net ROI", f"€{integrated_savings - 20:.2f}", "Full integration")

    # Calculate theoretical advantages
    net_integrated = integrated_savings - 20
    net_separate = separate_savings - 200
    net_single = single_savings - 50

    if net_separate > 0 and net_integrated > net_separate:
        advantage_vs_separate = (net_integrated - net_separate) / net_separate * 100
        st.success(f"🎯 **Theoretical advantage vs separate tools:** {advantage_vs_separate:.0f}% better ROI")

    if net_single > 0 and net_integrated > net_single:
        advantage_vs_single = (net_integrated - net_single) / net_single * 100
        st.success(f"🎯 **Theoretical advantage vs single tool:** {advantage_vs_single:.0f}% better ROI")


def _render_academic_positioning() -> None:
    """Render academic research positioning section"""
    st.markdown("""
    ### 🎯 Academic Research Positioning

    **Prototype exploring integrated Carbon-Aware FinOps approach with real-time German grid data**

    ⚠️ **Academic Disclaimer:** Competitive analysis based on public documentation review - not validated market research
    """)


def _render_key_differentiators() -> None:
    """Render key differentiators section"""
    st.markdown("### 🎯 Key Differentiators (Academic Hypothesis)")

    differentiators = [
        "🇩🇪 **German Grid Specialization**: Real-time ElectricityMaps integration vs generic EU averages",
        "⚡ **Sub-30-minute Updates**: Fresh carbon data vs daily/weekly updates",
        "🎯 **SME Optimization**: 20-100 instance sweet spot vs enterprise focus",
        "💰 **Integrated Business Cases**: Carbon + Cost ROI vs separate analysis",
        "🔄 **Real-time Scheduling**: Dynamic workload optimization",
        "📊 **Academic Transparency**: Open methodology vs proprietary algorithms",
        "💡 **Implementation Speed**: 3-day deployment vs weeks of integration",
        "💸 **95% lower API costs** (€20 vs €200+ monthly - estimated)"
    ]

    for diff in differentiators:
        st.markdown(f"- {diff}")


def _render_market_gap_analysis() -> None:
    """Render market gap analysis section"""
    st.markdown("### 🕳️ Identified Market Gaps (Literature Review)")

    st.markdown("""
    **Current Tools Analysis:**

    1. **Carbon Tracking Tools** (CloudCarbonFootprint, etc.)
       - ✅ Good for reporting and awareness
       - ❌ Limited real-time optimization
       - ❌ No cost integration

    2. **FinOps Tools** (CloudHealth, Cloudability)
       - ✅ Excellent cost optimization
       - ❌ No carbon considerations
       - ❌ Enterprise pricing models

    3. **Cloud Optimization** (AWS Trusted Advisor)
       - ✅ Performance optimization
       - ❌ No carbon awareness
       - ❌ Generic recommendations

    **Our Integration Hypothesis:**
    Real-time carbon data + cost optimization + German grid specificity =
    Better SME outcomes with €20/month vs €200+ for separate tools
    """)


def render_competitive_analysis_page(dashboard_data: Optional[Any]) -> None:
    """
    Render the competitive analysis page

    Args:
        dashboard_data: Complete dashboard data object for scenarios
    """
    st.header("🔄 Theoretical Competitive Analysis")

    # Academic research positioning
    _render_academic_positioning()

    # Tool comparison matrix
    _render_comparison_matrix()

    # Integration advantage scenarios
    _render_integration_scenarios(dashboard_data)

    # Key differentiators
    _render_key_differentiators()

    # Market gap analysis
    _render_market_gap_analysis()

    # Footer disclaimer
    st.markdown("---")
    st.info("""
    **Academic Note:** This competitive analysis represents a theoretical framework for research purposes.
    Market positioning claims require empirical validation through user studies and market research.

    **Research Focus:** Integration excellence and German SME market optimization rather than feature completeness.
    """)