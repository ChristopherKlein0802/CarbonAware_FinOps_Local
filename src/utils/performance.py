"""
Performance optimization utilities for dashboard
Caching and performance-focused functions
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from ..api.client import UnifiedAPIClient
from ..constants import APIConstants

# Global API client instance to avoid repeated instantiation
@st.cache_resource
def get_api_client() -> UnifiedAPIClient:
    """
    Get cached API client instance for optimal performance

    Returns a singleton UnifiedAPIClient instance cached in Streamlit's
    resource cache to avoid repeated instantiation across dashboard pages.

    Returns:
        UnifiedAPIClient: Cached instance for all API operations
    """
    return UnifiedAPIClient()

@st.cache_data(ttl=APIConstants.STREAMLIT_INFRASTRUCTURE_CACHE)  # 30 minutes cache
def get_cached_historical_data(region: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get cached historical carbon intensity data for the specified region

    Retrieves 24-hour historical carbon intensity data with intelligent
    fallback to self-collected data if ElectricityMaps API fails.
    Uses 30-minute caching for optimal performance.

    Args:
        region: AWS region code or ElectricityMaps zone ID (e.g., "eu-central-1" or "DE")

    Returns:
        Optional[List[Dict[str, Any]]]: List of carbon intensity data points,
        None if both official and self-collected data unavailable
    """
    api_client = get_api_client()
    historical_data = api_client.get_carbon_intensity_24h(region)

    # If official API fails, use self-collected data
    if not historical_data:
        historical_data = api_client.get_self_collected_24h_data(region)

    return historical_data

@st.cache_data(ttl=APIConstants.STREAMLIT_RAPID_CALCULATIONS)  # 10 minutes cache for rapid calculations
def cached_calculate_projections(baseline_cost: float, baseline_co2: float, instance_count: int) -> tuple[float, float]:
    """
    Cache expensive projection calculations for scaling scenarios

    Performs simple linear scaling of cost and CO2 emissions based on
    instance count. Uses 10-minute caching for rapid dashboard updates.

    Args:
        baseline_cost: Monthly cost for single instance (EUR)
        baseline_co2: Monthly CO2 emissions for single instance (kg)
        instance_count: Number of instances to scale to

    Returns:
        tuple[float, float]: (projected_cost_eur, projected_co2_kg)
    """
    projected_cost = baseline_cost * instance_count
    projected_co2 = baseline_co2 * instance_count

    return projected_cost, projected_co2

@st.cache_data(ttl=APIConstants.STREAMLIT_DYNAMIC_CALCULATIONS)  # 5 minutes cache for dynamic calculations
def cached_scenario_analysis(projected_cost: float) -> Dict[str, Any]:
    """
    Cache scenario analysis calculations for optimization strategies

    Calculates potential savings and ROI metrics for different optimization
    scenarios. Uses 5-minute caching for dynamic dashboard interactions.

    Args:
        projected_cost: Total projected monthly cost (EUR)

    Returns:
        Dict[str, Any]: Dictionary containing:
            - scenario_a_savings: Conservative optimization savings (EUR)
            - scenario_b_savings: Moderate optimization savings (EUR)
            - integrated_savings: Combined optimization savings (EUR)
            - payback_months: ROI payback period (months)
            - implementation_cost: One-time implementation cost (EUR)
    """
    from .ui import calculate_scenario_savings, calculate_roi_metrics

    scenario_a_savings, scenario_b_savings, integrated_savings = calculate_scenario_savings(projected_cost)
    _, _, _, payback_months, implementation_cost = calculate_roi_metrics(projected_cost)

    return {
        'scenario_a_savings': scenario_a_savings,
        'scenario_b_savings': scenario_b_savings,
        'integrated_savings': integrated_savings,
        'payback_months': payback_months,
        'implementation_cost': implementation_cost
    }

def optimize_dataframe_display(df: Any, key_suffix: str = "") -> None:
    """Optimize dataframe display with column configuration"""
    # Use column_config for better performance on large datasets
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        key=f"df_{key_suffix}"
    )

def optimize_chart_rendering(fig: Any, key_suffix: str = "") -> None:
    """Optimize plotly chart rendering"""
    return st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"chart_{key_suffix}",
        config={'displayModeBar': False}  # Hide toolbar for better performance
    )

@st.fragment  # Streamlit fragment for partial page updates
def render_metrics_section(metrics_data: List[tuple[str, str, str]]) -> None:
    """Render metrics section as fragment for better performance"""
    cols = st.columns(len(metrics_data))
    for i, (label, value, delta) in enumerate(metrics_data):
        with cols[i]:
            st.metric(label, value, delta)

def render_4_column_metrics(metric_data_list: List[tuple[str, str, str]]) -> None:
    """
    Render metrics in a 4-column layout for optimal dashboard space usage

    Eliminates repetitive column creation code across dashboard pages
    by providing a standardized 4-column metric display pattern.

    Args:
        metric_data_list: List of tuples containing (label, value, delta)
                         for each metric. Only first 4 items used.
    """
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]

    for i, (label, value, delta) in enumerate(metric_data_list[:4]):
        with cols[i]:
            st.metric(label, value, delta)

def render_3_column_metrics(metric_data_list: List[tuple[str, str, str]]) -> None:
    """Render 3-column metric layout"""
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for i, (label, value, delta) in enumerate(metric_data_list[:3]):
        with cols[i]:
            st.metric(label, value, delta)

def _render_content_item(content: Any) -> None:
    """Helper function to render individual content items"""
    if isinstance(content, dict):
        if 'header' in content:
            st.subheader(content['header'])
        if 'markdown' in content:
            st.markdown(content['markdown'])
        if 'metric' in content:
            st.metric(content['metric']['label'], content['metric']['value'], content['metric'].get('delta', ''))
    else:
        st.markdown(content)

def render_n_column_content(content_data_list: List[Any], num_columns: int) -> None:
    """Generic function to render N-column content layout with markdown"""
    cols = st.columns(num_columns)

    for i, content in enumerate(content_data_list[:num_columns]):
        with cols[i]:
            _render_content_item(content)

def render_2_column_content(content_data_list: List[Any]) -> None:
    """Render 2-column content layout with markdown"""
    render_n_column_content(content_data_list, 2)

def render_3_column_content(content_data_list: List[Any]) -> None:
    """Render 3-column content layout with markdown"""
    render_n_column_content(content_data_list, 3)

def render_grid_status_hero(grid_status: float, status_color: str, status_text: str, recommendation: str) -> None:
    """Render the German Grid Status hero section"""
    st.markdown(f"""
    ### 🇩🇪 German Grid Status (Live)
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <h2 style="margin: 0; color: #1f77b4;">{status_color} {grid_status:.0f} g CO₂/kWh</h2>
        <p style="margin: 5px 0; font-size: 16px;"><strong>Status:</strong> {status_text}</p>
        <p style="margin: 5px 0; font-size: 14px; color: #666;">{recommendation}</p>
        <small>Updates every 30 minutes • Source: ElectricityMaps API</small>
    </div>
    """, unsafe_allow_html=True)