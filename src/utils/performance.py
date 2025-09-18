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




def optimize_chart_rendering(fig: Any, key_suffix: str = "") -> None:
    """Optimize plotly chart rendering"""
    return st.plotly_chart(
        fig,
        width='stretch',
        key=f"chart_{key_suffix}",
        config={'displayModeBar': False}  # Hide toolbar for better performance
    )


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