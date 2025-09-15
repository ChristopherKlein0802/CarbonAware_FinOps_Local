#!/usr/bin/env python3
"""
Carbon-Aware FinOps Dashboard - Clean Architecture Launcher
Professional startup script for the simplified architecture

Usage:
    python run_clean_dashboard.py

Features:
- Professional validation and health checks
- Clean architecture verification
- Development-friendly logging
- Academic-ready presentation
"""

import sys
import os
import logging
from pathlib import Path

# Add src to Python path for clean imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Configure logging for development and academic transparency"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def validate_environment():
    """Validate environment and dependencies"""
    logger = logging.getLogger(__name__)

    logger.info("🔍 Validating environment...")

    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ required")
        return False

    # Check required packages
    required_packages = ['streamlit', 'requests', 'boto3', 'plotly', 'pandas']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} missing")

    if missing_packages:
        logger.error(f"Install missing packages: pip install {' '.join(missing_packages)}")
        return False

    # Check environment variables
    api_keys = ['ELECTRICITYMAP_API_KEY', 'AWS_PROFILE']
    missing_keys = []

    for key in api_keys:
        if not os.getenv(key):
            missing_keys.append(key)
            logger.warning(f"⚠️ {key} not set")

    if missing_keys:
        logger.warning("Some API keys missing - demo mode will have limited functionality")

    logger.info("✅ Environment validation complete")
    return True

def validate_architecture():
    """Validate clean architecture structure"""
    logger = logging.getLogger(__name__)

    logger.info("🏗️ Validating clean architecture...")

    required_files = [
        "src/app.py",
        "src/api_client.py",
        "src/data_processor.py",
        "src/models.py",
        "src/pages.py",
        "src/health_monitor.py",
        "src/assets/modern-thesis-styles.css"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.error(f"❌ Missing: {file_path}")
        else:
            logger.info(f"✅ Found: {file_path}")

    if missing_files:
        logger.error("❌ Architecture validation failed - missing files")
        return False

    logger.info("✅ Clean architecture validated")
    return True

def check_api_health():
    """Quick API health check"""
    logger = logging.getLogger(__name__)

    try:
        from src.health_monitor import health_check_manager
        logger.info("🏥 Running quick health check...")

        is_healthy = health_check_manager.quick_health_check()
        if is_healthy:
            logger.info("✅ APIs are healthy - dashboard ready")
        else:
            logger.warning("⚠️ Some APIs unavailable - dashboard will work with limited functionality")

        return True
    except Exception as e:
        logger.warning(f"⚠️ Health check failed: {e}")
        return True  # Don't block startup

def main():
    """Main startup sequence"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting Carbon-Aware FinOps Dashboard (Clean Architecture)")

    # Validation sequence
    if not validate_environment():
        logger.error("❌ Environment validation failed")
        sys.exit(1)

    if not validate_architecture():
        logger.error("❌ Architecture validation failed")
        sys.exit(1)

    # Quick health check (non-blocking)
    check_api_health()

    # Import and run the app
    try:
        logger.info("🎯 Launching Streamlit dashboard...")

        # Import the main app
        from src.app import main as run_app

        # Run the Streamlit app
        logger.info("✅ Dashboard ready at http://localhost:8501")
        logger.info("📊 Professional Carbon-Aware FinOps Dashboard")
        logger.info("🎓 Bachelor Thesis Project - Clean Architecture")

        run_app()

    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        logger.error("Make sure all files are in the correct locations")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()