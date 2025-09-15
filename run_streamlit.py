#!/usr/bin/env python3
"""
🚀 Carbon-Aware FinOps Streamlit Dashboard Launcher
Modern dashboard startup script with health checks
"""

import subprocess
import sys
import time
import requests
from datetime import datetime

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy']

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - installed")
        except ImportError:
            print(f"❌ {package} - missing")
            print(f"Install with: pip install {package}")
            return False

    return True

def check_apis():
    """Check if backend APIs are accessible"""
    print("\n🔍 Checking API connectivity...")

    try:
        # Add project paths for imports
        sys.path.append('dashboard')
        from dashboard.utils.health_checks import health_check_manager

        health_status = health_check_manager.check_all_apis()

        if health_status.get("all_healthy", False):
            print("✅ All APIs are healthy")
            return True
        else:
            print("⚠️ Some APIs may be unavailable")
            return True  # Still allow startup

    except Exception as e:
        print(f"⚠️ API check failed: {e}")
        return True  # Still allow startup

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    print(f"\n🚀 Launching Carbon-Aware FinOps Dashboard...")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Start Streamlit with optimized settings
        cmd = [
            sys.executable, "-m", "streamlit", "run", "streamlit_main.py",
            "--server.port", "8051",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ]

        print("🔧 Starting Streamlit server...")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Wait for startup
        time.sleep(3)

        # Check if server is running
        try:
            response = requests.get("http://localhost:8051", timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard started successfully!")
                print("\n" + "="*60)
                print("🌍 CARBON-AWARE FINOPS DASHBOARD")
                print("="*60)
                print("📊 Local URL:    http://localhost:8051")
                print("📱 Network URL:  http://192.168.0.72:8051")
                print("🎓 Thesis:      Bachelor Project 2025")
                print("🔬 APIs:        ElectricityMaps + Boavizta + AWS")
                print("⚡ Framework:   Modern Streamlit")
                print("="*60)
                print("\n✨ Features:")
                print("   🗂️  Sidebar Navigation")
                print("   📈 Dense Information Layout")
                print("   🔍 Interactive Filters")
                print("   ⚡ Real-time Updates")
                print("   📤 Export Functions")
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

        except requests.exceptions.RequestException:
            print("❌ Could not connect to dashboard")

    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")

def main():
    """Main startup function"""
    print("🌍 Carbon-Aware FinOps Dashboard - Modern Streamlit Version")
    print("Bachelor Thesis Project (September 2025)")
    print("-" * 60)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install required packages.")
        sys.exit(1)

    # Check API connectivity
    check_apis()

    # Launch dashboard
    launch_dashboard()

if __name__ == "__main__":
    main()