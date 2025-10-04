"""
Performance optimization utilities for dashboard
Caching and performance-focused functions
"""

import streamlit as st
from typing import Any, List


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
