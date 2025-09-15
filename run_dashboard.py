#!/usr/bin/env python3
"""
🌍 Carbon-Aware FinOps Dashboard - Professional Startup Script
Modern enterprise-grade application launcher with health monitoring

Features:
- Professional project structure validation
- Comprehensive dependency checking
- API connectivity verification
- Clean separation of concerns (MVC)
- Production-ready error handling
"""

import subprocess
import sys
import time
import requests
from datetime import datetime
from pathlib import Path


def check_project_structure():
    """Validate professional project structure"""
    print("🔍 Validating professional project structure...")

    required_structure = [
        "src/frontend/app.py",
        "src/frontend/pages/streamlit_pages.py",
        "src/backend/services/api_clients/unified_api_client.py",
        "src/backend/controllers/data_processing.py",
        "src/backend/controllers/health_checks.py",
        "src/backend/models/data_models.py",
        "src/shared/components/chartjs_library.py"
    ]

    project_root = Path(__file__).parent
    missing_files = []

    for file_path in required_structure:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print("✅ Professional project structure validated")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking dependencies...")
    required_packages = [
        'streamlit', 'plotly', 'pandas', 'numpy',
        'requests', 'boto3', 'python-dotenv'
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - missing")
            print(f"Install with: pip install {package}")
            return False

    print("✅ All dependencies satisfied")
    return True


def check_api_connectivity():
    """Validate API access and credentials"""
    print("\n🔗 Checking API connectivity...")

    try:
        # Check if we can import the health check system
        project_root = Path(__file__).parent
        sys.path.append(str(project_root))
        sys.path.append(str(project_root / 'src'))

        from src.backend.controllers.health_checks import health_check_manager

        # Run health checks
        health_status = health_check_manager.check_all_apis()

        # Report results
        overall = health_status.get("system_overall", {})
        services_healthy = overall.get("services_healthy", 0)
        total_services = overall.get("total_services", 3)

        print(f"✅ API Health Check: {services_healthy}/{total_services} services healthy")

        if services_healthy >= 2:
            print("✅ Sufficient APIs available for dashboard operation")
            return True
        else:
            print("⚠️ Limited API availability - dashboard will run with reduced functionality")
            return True  # Still allow startup

    except Exception as e:
        print(f"⚠️ API check failed: {e}")
        print("🔄 Dashboard will attempt to start anyway")
        return True  # Still allow startup


def launch_dashboard():
    """Launch the professional Streamlit dashboard"""
    print(f"\n🚀 Launching Carbon-Aware FinOps Dashboard...")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏗️ Architecture: Modern MVC with Clean Separation")

    try:
        # Start Streamlit with professional configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            "src/frontend/app.py",
            "--server.port", "8051",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--theme.base", "light",
            "--theme.primaryColor", "#667eea"
        ]

        print("🔧 Starting professional Streamlit application...")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Wait for startup
        time.sleep(4)

        # Verify server is running
        try:
            response = requests.get("http://localhost:8051", timeout=10)
            if response.status_code == 200:
                print("✅ Dashboard started successfully!")
                print("\n" + "="*80)
                print("🌍 CARBON-AWARE FINOPS DASHBOARD - PROFESSIONAL EDITION")
                print("="*80)
                print("📊 Dashboard URL:    http://localhost:8051")
                print("🏗️ Architecture:    Modern MVC Pattern")
                print("🎓 Project:         Bachelor Thesis 2025")
                print("🔬 APIs:            ElectricityMaps + Boavizta + AWS")
                print("⚡ Framework:       Professional Streamlit")
                print("="*80)
                print("\n✨ Professional Features:")
                print("   📁 Clean Code Architecture (MVC)")
                print("   🗂️ Sidebar Navigation")
                print("   📊 Advanced Data Models")
                print("   🔍 Interactive Filters")
                print("   ⚡ Optimized API Caching")
                print("   📤 Export Functions")
                print("   🏥 Health Monitoring")
                print("\n🛑 Press Ctrl+C to stop the dashboard")

                # Keep the process running
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Shutting down dashboard...")
                    process.terminate()
                    print("✅ Dashboard stopped successfully")

            else:
                print(f"❌ Server responded with status {response.status_code}")
                print("Check logs for detailed error information")

        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to dashboard: {e}")
            print("The application may still be starting up...")

    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return False

    return True


def main():
    """Main application launcher with professional validation"""
    print("🌍 Carbon-Aware FinOps Dashboard - Professional Launch Sequence")
    print("Bachelor Thesis Project (September 2025)")
    print("=" * 80)

    # Validation sequence
    if not check_project_structure():
        print("\n❌ Project structure validation failed")
        sys.exit(1)

    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)

    check_api_connectivity()

    # Launch dashboard
    if launch_dashboard():
        print("\n🎉 Professional dashboard launch completed successfully")
    else:
        print("\n❌ Dashboard launch failed")
        sys.exit(1)


if __name__ == "__main__":
    main()