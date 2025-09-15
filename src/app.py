"""
Carbon-Aware FinOps Dashboard - Main Streamlit Application
Pragmatic Professional Architecture for Bachelor Thesis

This is the main entry point for the modern Streamlit dashboard.
Clean, professional implementation without overengineering.
"""

import streamlit as st
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from api_client import unified_api_client
from data_processor import data_processor
from health_monitor import health_check_manager
from pages import (
    render_overview_page,
    render_infrastructure_page,
    render_carbon_page,
    render_competitive_analysis_page,
    render_research_methods_page
)

# Page configuration
st.set_page_config(
    page_title="Carbon-Aware FinOps Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    """Load custom CSS for professional styling"""
    try:
        with open("assets/modern-thesis-styles.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        logger.warning("CSS file not found - using default Streamlit styles")

@st.cache_data(ttl=1800, show_spinner="Loading infrastructure data...")  # 30 minute cache
def load_infrastructure_data():
    """Load infrastructure data with proper caching"""
    try:
        return data_processor.get_infrastructure_data()
    except Exception as e:
        logger.error(f"Failed to load infrastructure data: {e}")
        return None

def main():
    """Main application entry point"""
    # Initialize session state for startup logging
    if 'dashboard_initialized' not in st.session_state:
        logger.info("🚀 Carbon-Aware FinOps Dashboard starting...")
        st.session_state.dashboard_initialized = True

    # Load custom styling
    load_custom_css()

    # Sidebar navigation
    st.sidebar.title("🌱 Carbon-Aware FinOps")
    st.sidebar.markdown("*Bachelor Thesis Dashboard*")

    # Navigation menu
    page = st.sidebar.radio(
        "Navigation",
        ["🏆 Executive Summary", "🇩🇪 Carbon Optimization", "🔄 Competitive Analysis", "🏗️ Infrastructure", "🔬 Research Methods"],
        index=0
    )

    # Load data once for all pages
    dashboard_data = load_infrastructure_data()

    # System status in sidebar
    st.sidebar.markdown("---")
    if dashboard_data:
        st.sidebar.success("✅ System Online")
        if hasattr(dashboard_data, 'instances'):
            st.sidebar.info(f"📡 {len(dashboard_data.instances)} instances monitored")
    else:
        st.sidebar.error("❌ System Offline")

    # Render selected page
    try:
        if page == "🏆 Executive Summary":
            render_overview_page(dashboard_data)
        elif page == "🇩🇪 Carbon Optimization":
            render_carbon_page(dashboard_data)
        elif page == "🔄 Competitive Analysis":
            render_competitive_analysis_page(dashboard_data)
        elif page == "🏗️ Infrastructure":
            render_infrastructure_page(dashboard_data)
        elif page == "🔬 Research Methods":
            render_research_methods_page(dashboard_data)

    except Exception as e:
        st.error(f"❌ Page rendering failed: {e}")
        logger.error(f"Page rendering error: {e}")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.caption("Bachelor Thesis Project 2025")

if __name__ == "__main__":
    main()