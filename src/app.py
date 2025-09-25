"""
Carbon-Aware FinOps Dashboard - Main Streamlit Application
Pragmatic Professional Architecture for Bachelor Thesis

This is the main entry point for the modern Streamlit dashboard.
Clean, professional implementation without overengineering.
"""

import os
import streamlit as st
import logging
from datetime import datetime
from typing import Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from src.constants import APIConstants
from src.core.processor import DataProcessor

# Initialize data processor (lazy loading)
@st.cache_resource
def get_data_processor():
    """Get cached data processor instance"""
    return DataProcessor()

data_processor = get_data_processor()
from src.views import (
    render_overview_page,
    render_infrastructure_page,
    render_carbon_page
)

# Page configuration
st.set_page_config(
    page_title="Carbon-Aware FinOps Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css() -> None:
    """Load custom CSS for professional styling with proper validation"""
    try:
        # Robust path construction relative to src directory
        src_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(src_dir, "assets")
        css_path = os.path.join(assets_dir, "modern-thesis-styles.css")

        # Validate assets directory exists
        if not os.path.exists(assets_dir):
            logger.info(f"Assets directory not found: {assets_dir}")
            return

        # Validate CSS file exists
        if not os.path.exists(css_path):
            logger.warning(f"CSS file not found: {css_path}")
            return

        # Load CSS with size validation
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            if len(css_content.strip()) == 0:
                logger.warning("CSS file is empty - using default Streamlit styles")
                return

            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            logger.debug(f"✅ CSS loaded successfully from {css_path}")

    except (FileNotFoundError, PermissionError) as e:
        logger.warning(f"CSS file access error: {e} - using default Streamlit styles")
    except UnicodeDecodeError as e:
        logger.error(f"CSS file encoding error: {e} - using default Streamlit styles")
    except (OSError, IOError) as e:
        logger.error(f"File system error loading CSS: {e} - using default Streamlit styles")

@st.cache_resource(show_spinner="Loading infrastructure data...")  # Use cache_resource for complex objects
def load_infrastructure_data(force_refresh: bool = False) -> Optional[Any]:
    """Load infrastructure data with proper caching and specific error handling"""
    try:
        return data_processor.get_infrastructure_data(force_refresh=force_refresh)
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Network error loading infrastructure data: {e}")
        return None
    except (ImportError, AttributeError) as e:
        logger.error(f"Module/attribute error in data processor: {e}")
        return None
    except (RuntimeError, ValueError) as e:
        logger.error(f"Runtime/value error in data processor: {e}")
        return None

def main() -> None:
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

    if "force_refresh" not in st.session_state:
        st.session_state["force_refresh"] = False

    st.sidebar.markdown("### 🔧 Actions")
    if st.sidebar.button("🔄 Refresh data", use_container_width=True):
        st.session_state["force_refresh"] = True
        load_infrastructure_data.clear()
        st.sidebar.success("Refreshing API data…")

    # Simplified navigation menu - core features only
    page = st.sidebar.radio(
        "Navigation",
        ["🏆 Executive Summary", "🇩🇪 Carbon Optimization", "🏗️ Infrastructure"],
        index=0
    )

    # Load data once for all pages
    force_refresh_flag = st.session_state.get("force_refresh", False)
    dashboard_data = load_infrastructure_data(force_refresh_flag)
    if force_refresh_flag:
        st.session_state["force_refresh"] = False

    # API Status Widget - Core 6 services
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 API Status")

    if dashboard_data and getattr(dashboard_data, "api_health_status", None):
        api_statuses = dashboard_data.api_health_status
        online_count = sum(1 for status in api_statuses.values() if getattr(status, "healthy", False))

        for api_name, status in api_statuses.items():
            label = api_name.replace("_", " ").title()
            status_code = getattr(status, "status", "error")
            if getattr(status, "healthy", False):
                icon = "✅"
            elif status_code == "degraded":
                icon = "⚠️"
            else:
                icon = "❌"
            st.sidebar.write(f"{icon} {label}")

        st.sidebar.write(f"**{online_count}/{len(api_statuses)} Services Online**")

        if hasattr(dashboard_data, 'instances'):
            st.sidebar.info(f"📡 {len(dashboard_data.instances)} instances monitored")
    else:
        st.sidebar.error("❌ System Offline")
        fallback_services = [
            "ElectricityMaps",
            "Boavizta",
            "AWS Cost Explorer",
            "AWS Pricing",
            "CloudWatch",
            "CloudTrail"
        ]
        for api_name in fallback_services:
            st.sidebar.write(f"❌ {api_name}")
        st.sidebar.write(f"**0/{len(fallback_services)} Services Online**")

    # Render selected page with specific error handling
    try:
        if page == "🏆 Executive Summary":
            render_overview_page(dashboard_data)
        elif page == "🇩🇪 Carbon Optimization":
            render_carbon_page(dashboard_data)
        elif page == "🏗️ Infrastructure":
            render_infrastructure_page(dashboard_data)

    except (AttributeError, KeyError) as e:
        st.error(f"❌ Data structure error: {e}")
        logger.error(f"Page rendering data error: {e}")
    except ImportError as e:
        st.error(f"❌ Module import error: {e}")
        logger.error(f"Page rendering import error: {e}")
    except (RuntimeError, ValueError, TypeError) as e:
        st.error(f"❌ Runtime error rendering page: {e}")
        logger.error(f"Page rendering runtime error: {e}")

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.caption("Bachelor Thesis Project 2025")

if __name__ == "__main__":
    main()
