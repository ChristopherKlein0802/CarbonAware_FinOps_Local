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

# Reduce noisy boto3/botocore logging when AWS SSO tokens expire
_NOISY_AWS_LOGGERS = (
    "botocore",
    "botocore.credentials",
    "botocore.auth",
    "botocore.session",
    "botocore.utils",
    "botocore.tokens",
    "boto3",
)
for _logger_name in _NOISY_AWS_LOGGERS:
    noisy_logger = logging.getLogger(_logger_name)
    noisy_logger.handlers.clear()
    noisy_logger.addHandler(logging.NullHandler())
    noisy_logger.setLevel(logging.CRITICAL)
    noisy_logger.propagate = False

# Import our modules
from src.domain.constants import UIConstants
from src.application.orchestrator import DashboardDataOrchestrator
from src.domain.models import DashboardData
from src.presentation import render_overview_page, render_infrastructure_page


# Initialize data orchestrator (lazy loading)
@st.cache_resource
def get_data_orchestrator():
    """Get cached data orchestrator instance"""
    return DashboardDataOrchestrator()


data_processor = get_data_orchestrator()

_CACHE_KEY = "dashboard_data_cache"
_CACHE_TIMESTAMP_KEY = "dashboard_data_cache_timestamp"
_CACHE_TTL_SECONDS = UIConstants.STREAMLIT_CACHE_TTL_SECONDS

# Page configuration
st.set_page_config(
    page_title="Carbon-Aware FinOps Dashboard", page_icon="🌱", layout="wide", initial_sidebar_state="expanded"
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


def _clear_dashboard_cache() -> None:
    """Remove cached dashboard data from session state."""
    st.session_state.pop(_CACHE_KEY, None)
    st.session_state.pop(_CACHE_TIMESTAMP_KEY, None)


def _get_cached_dashboard_data() -> tuple[Optional[DashboardData], Optional[datetime]]:
    """Retrieve cached dashboard data and its timestamp."""
    cached_data = st.session_state.get(_CACHE_KEY)
    cached_at = st.session_state.get(_CACHE_TIMESTAMP_KEY)
    if cached_at is not None and not isinstance(cached_at, datetime):
        # Clean up unexpected types to prevent timedelta errors
        cached_at = None
    return cached_data, cached_at


def _cache_dashboard_data(data: Optional[DashboardData]) -> None:
    """Persist dashboard data and timestamp in session state."""
    st.session_state[_CACHE_KEY] = data
    st.session_state[_CACHE_TIMESTAMP_KEY] = datetime.now()


def load_infrastructure_data(force_refresh: bool = False, period_days: int = 30) -> Optional[DashboardData]:
    """
    Load infrastructure data with manual TTL caching and specific error handling.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data
        period_days: Analysis period in days (1, 7, or 30)

    Returns:
        DashboardData object with instances, metrics, and API status, or None on error
    """
    if force_refresh:
        _clear_dashboard_cache()

    cached_data, cached_at = _get_cached_dashboard_data()
    if not force_refresh and cached_data is not None and cached_at is not None:
        age_seconds = (datetime.now() - cached_at).total_seconds()
        if age_seconds < _CACHE_TTL_SECONDS:
            # Check if cached data has same period
            if getattr(cached_data, "analysis_period_days", 30) == period_days:
                return cached_data

    try:
        with st.spinner("Loading infrastructure data..."):
            dashboard_data = data_processor.get_infrastructure_data(force_refresh=force_refresh, period_days=period_days)
        _cache_dashboard_data(dashboard_data)
        return dashboard_data
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Network error loading infrastructure data: {e}")
        return cached_data if cached_data is not None else None
    except (ImportError, AttributeError) as e:
        logger.error(f"Module/attribute error in data processor: {e}")
        return cached_data if cached_data is not None else None
    except (RuntimeError, ValueError) as e:
        logger.error(f"Runtime/value error in data processor: {e}")
        return cached_data if cached_data is not None else None


def main() -> None:
    """Main application entry point"""
    # Initialize session state for startup logging
    if "dashboard_initialized" not in st.session_state:
        logger.info("🚀 Carbon-Aware FinOps Dashboard starting...")
        st.session_state.dashboard_initialized = True

        # Automatic cache cleanup on startup (once per session)
        try:
            from pathlib import Path
            from src.infrastructure.cache import FileCacheRepository
            cache_root = Path.home() / ".cache" / "carbon_finops"
            if cache_root.exists():
                cache_repo = FileCacheRepository(cache_root)
                api_data_dir = cache_root / "api_data"
                if api_data_dir.exists():
                    deleted_count = cache_repo.clean_old(api_data_dir, max_age_days=7)
                    if deleted_count > 0:
                        logger.info(f"🧹 Cache cleanup: Removed {deleted_count} expired files")
        except Exception as error:
            logger.warning(f"Cache cleanup failed (non-critical): {error}")

    # Load custom styling
    load_custom_css()

    # Sidebar navigation
    st.sidebar.title("🌱 Carbon-Aware FinOps")
    st.sidebar.markdown("*Bachelor Thesis Dashboard*")

    # Analysis Period Selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Analysis Period")

    period_options = {
        "Last 24 hours": 1,
        "Last 7 days": 7,
        "Last 30 days": 30,
    }

    selected_period_label = st.sidebar.selectbox(
        "Time Window",
        options=list(period_options.keys()),
        index=2,  # Default to "Last 30 days"
        help="Select the time window for cost and carbon analysis. Carbon data is always based on 24h ElectricityMaps data, scaled to the selected period."
    )

    period_days = period_options[selected_period_label]

    # Validate period_days (safety check)
    VALID_PERIODS = {1, 7, 30}
    if period_days not in VALID_PERIODS:
        st.error(f"⚠️ Invalid analysis period: {period_days} days. Using default of 30 days.")
        period_days = 30

    # Store in session state for cross-component access
    if "analysis_period_days" not in st.session_state or st.session_state["analysis_period_days"] != period_days:
        st.session_state["analysis_period_days"] = period_days
        # Clear cache when period changes
        _clear_dashboard_cache()

    if "force_refresh" not in st.session_state:
        st.session_state["force_refresh"] = False

    # Rate limiting for refresh button
    if "refresh_count" not in st.session_state:
        st.session_state["refresh_count"] = 0
        st.session_state["refresh_reset_at"] = datetime.now().timestamp() + 600  # 10 minutes

    # Reset counter if 10 minutes passed
    if datetime.now().timestamp() > st.session_state["refresh_reset_at"]:
        st.session_state["refresh_count"] = 0
        st.session_state["refresh_reset_at"] = datetime.now().timestamp() + 600

    st.sidebar.markdown("### 🔧 Actions")

    # Check rate limit
    if st.session_state["refresh_count"] >= 5:
        remaining_seconds = int(st.session_state["refresh_reset_at"] - datetime.now().timestamp())
        st.sidebar.warning(f"""
        ⚠️ **Rate Limit Reached**

        Please wait {remaining_seconds // 60} minutes before refreshing again.
        This protects against API rate limits (ElectricityMaps: 100 req/h).

        The dashboard uses cached data (5min TTL) to minimize API calls.
        """)
        st.sidebar.button("🔄 Refresh data", width="stretch", disabled=True)
    else:
        if st.sidebar.button("🔄 Refresh data", width="stretch"):
            st.session_state["refresh_count"] += 1
            st.session_state["force_refresh"] = True
            _clear_dashboard_cache()
            st.sidebar.success(f"Refreshing API data… ({st.session_state['refresh_count']}/5 in 10min)")

    # Simplified navigation menu - core features only
    page = st.sidebar.radio(
        "Navigation", ["Dashboard Overview", "Infrastructure Details"], index=0
    )

    # Load data once for all pages
    force_refresh_flag = st.session_state.get("force_refresh", False)
    dashboard_data = load_infrastructure_data(force_refresh_flag, period_days=period_days)
    if force_refresh_flag:
        st.session_state["force_refresh"] = False

    # API Status Widget - Core 6 services
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 API Status")

    display_labels = {
        "CloudWatch": "AWS CloudWatch",
        "CloudTrail": "AWS CloudTrail",
        "Aws Cloudwatch": "AWS CloudWatch",
        "Aws Cloudtrail": "AWS CloudTrail",
    }

    if dashboard_data and getattr(dashboard_data, "api_health_status", None):
        api_statuses = dashboard_data.api_health_status
        online_count = sum(1 for status in api_statuses.values() if getattr(status, "healthy", False))

        for api_name, status in api_statuses.items():
            label = display_labels.get(api_name, api_name.replace("_", " "))
            status_code = getattr(status, "status", "error")
            if getattr(status, "healthy", False):
                icon = "✅"
            elif status_code == "degraded":
                icon = "⚠️"
            else:
                icon = "❌"
            st.sidebar.write(f"{icon} {label}")

        st.sidebar.write(f"**{online_count}/{len(api_statuses)} Services Online**")

        if hasattr(dashboard_data, "instances"):
            st.sidebar.info(f"📡 {len(dashboard_data.instances)} instances monitored")
    else:
        st.sidebar.error("❌ System Offline")
        fallback_services = [
            "ElectricityMaps",
            "Boavizta",
            "AWS Cost Explorer",
            "AWS Pricing",
            "AWS CloudWatch",
            "AWS CloudTrail",
        ]
        for api_name in fallback_services:
            st.sidebar.write(f"❌ {api_name}")
        st.sidebar.write(f"**0/{len(fallback_services)} Services Online**")

    # Render selected page with specific error handling
    try:
        if page == "Dashboard Overview":
            render_overview_page(dashboard_data)
        elif page == "Infrastructure Details":
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
