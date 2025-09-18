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
def load_infrastructure_data() -> Optional[Any]:
    """Load infrastructure data with proper caching and specific error handling"""
    try:
        return data_processor.get_infrastructure_data()
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

    # Simplified navigation menu - core features only
    page = st.sidebar.radio(
        "Navigation",
        ["🏆 Executive Summary", "🇩🇪 Carbon Optimization", "🏗️ Infrastructure"],
        index=0
    )

    # Load data once for all pages
    dashboard_data = load_infrastructure_data()

    # API Status Widget - Core 5 APIs
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 API Status")

    if dashboard_data:
        # API health status simplified (monitoring module removed in cleanup)
        api_statuses = {}

        # Core 5 APIs with actual data availability detection
        apis = [
            ("ElectricityMaps", dashboard_data.carbon_intensity is not None and dashboard_data.carbon_intensity.value > 0),
            ("AWS Cost Explorer", dashboard_data.total_cost_eur > 0),
            ("CloudTrail", any(hasattr(i, 'runtime_hours') and i.runtime_hours and i.runtime_hours > 0 for i in dashboard_data.instances) if dashboard_data.instances else False),
            ("Boavizta", any(i.power_watts and i.power_watts > 0 for i in dashboard_data.instances) if dashboard_data.instances else False),
            ("AWS Pricing", any(hasattr(i, 'hourly_price_usd') and i.hourly_price_usd and i.hourly_price_usd > 0 for i in dashboard_data.instances) if dashboard_data.instances else False)
        ]

        online_count = sum(1 for _, status in apis if status)

        # API status display
        for api_name, is_online in apis:
            status_icon = "✅" if is_online else "❌"
            st.sidebar.write(f"{status_icon} {api_name}")

        # Summary
        st.sidebar.write(f"**{online_count}/5 APIs Online**")

        # Instance count
        if hasattr(dashboard_data, 'instances'):
            st.sidebar.info(f"📡 {len(dashboard_data.instances)} instances monitored")
    else:
        st.sidebar.error("❌ System Offline")
        # Show all APIs as offline
        for api_name in ["ElectricityMaps", "AWS Cost Explorer", "CloudTrail", "Boavizta", "AWS Pricing"]:
            st.sidebar.write(f"❌ {api_name}")
        st.sidebar.write("**0/5 APIs Online**")

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