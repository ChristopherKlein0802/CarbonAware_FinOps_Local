"""
Performance optimization utilities for dashboard
Caching and performance-focused functions
"""

import streamlit as st
from api_client import UnifiedAPIClient

# Global API client instance to avoid repeated instantiation
@st.cache_resource
def get_api_client():
    """Get cached API client instance"""
    return UnifiedAPIClient()

@st.cache_data(ttl=1800)  # 30 minutes cache
def get_cached_historical_data(region):
    """Get cached historical carbon data"""
    api_client = get_api_client()
    historical_data = api_client.get_carbon_intensity_24h(region)

    # If official API fails, use self-collected data
    if not historical_data:
        historical_data = api_client.get_self_collected_24h_data(region)

    return historical_data

@st.cache_data(ttl=600)  # 10 minutes cache for rapid calculations
def cached_calculate_projections(baseline_cost, baseline_co2, instance_count):
    """Cache expensive projection calculations"""
    projected_cost = baseline_cost * instance_count
    projected_co2 = baseline_co2 * instance_count

    return projected_cost, projected_co2

@st.cache_data(ttl=300)  # 5 minutes cache for dynamic calculations
def cached_scenario_analysis(projected_cost):
    """Cache scenario analysis calculations"""
    from page_utils import calculate_scenario_savings, calculate_roi_metrics

    scenario_a_savings, scenario_b_savings, integrated_savings = calculate_scenario_savings(projected_cost)
    _, _, _, payback_months, implementation_cost = calculate_roi_metrics(projected_cost)

    return {
        'scenario_a_savings': scenario_a_savings,
        'scenario_b_savings': scenario_b_savings,
        'integrated_savings': integrated_savings,
        'payback_months': payback_months,
        'implementation_cost': implementation_cost
    }

def optimize_dataframe_display(df, key_suffix=""):
    """Optimize dataframe display with column configuration"""
    # Use column_config for better performance on large datasets
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        key=f"df_{key_suffix}"
    )

def optimize_chart_rendering(fig, key_suffix=""):
    """Optimize plotly chart rendering"""
    return st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"chart_{key_suffix}",
        config={'displayModeBar': False}  # Hide toolbar for better performance
    )

@st.fragment  # Streamlit fragment for partial page updates
def render_metrics_section(metrics_data):
    """Render metrics section as fragment for better performance"""
    cols = st.columns(len(metrics_data))
    for i, (label, value, delta) in enumerate(metrics_data):
        with cols[i]:
            st.metric(label, value, delta)

def render_4_column_metrics(metric_data_list):
    """Render 4-column metric layout - eliminates repetitive column code"""
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]

    for i, (label, value, delta) in enumerate(metric_data_list[:4]):
        with cols[i]:
            st.metric(label, value, delta)

def render_3_column_metrics(metric_data_list):
    """Render 3-column metric layout"""
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for i, (label, value, delta) in enumerate(metric_data_list[:3]):
        with cols[i]:
            st.metric(label, value, delta)

def render_2_column_content(content_data_list):
    """Render 2-column content layout with markdown"""
    col1, col2 = st.columns(2)
    cols = [col1, col2]

    for i, content in enumerate(content_data_list[:2]):
        with cols[i]:
            if isinstance(content, dict):
                if 'header' in content:
                    st.subheader(content['header'])
                if 'markdown' in content:
                    st.markdown(content['markdown'])
                if 'metric' in content:
                    st.metric(content['metric']['label'], content['metric']['value'], content['metric'].get('delta', ''))
            else:
                st.markdown(content)

def render_3_column_content(content_data_list):
    """Render 3-column content layout with markdown"""
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for i, content in enumerate(content_data_list[:3]):
        with cols[i]:
            if isinstance(content, dict):
                if 'header' in content:
                    st.subheader(content['header'])
                if 'markdown' in content:
                    st.markdown(content['markdown'])
                if 'metric' in content:
                    st.metric(content['metric']['label'], content['metric']['value'], content['metric'].get('delta', ''))
            else:
                st.markdown(content)

def render_grid_status_hero(grid_status, status_color, status_text, recommendation):
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