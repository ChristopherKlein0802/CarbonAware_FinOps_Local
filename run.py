#!/usr/bin/env python3
"""
Simple Launch Script - Carbon-Aware FinOps Dashboard
Bachelor Thesis 2025

MODES:
- Development: Fast reload, debug mode
- Production: Multi-worker, optimized performance
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_development():
    """Run in development mode - fast and simple"""
    print("🚀 Starting Carbon-Aware FinOps Dashboard (Development Mode)")
    print("📍 Dashboard: http://localhost:8050")
    print("⚡ Hot-reload enabled")
    print("🔧 Debug mode active")
    print("-" * 50)
    
    # Change to dashboard directory
    os.chdir("dashboard")
    
    # Run with Python directly
    subprocess.run([sys.executable, "dashboard_main.py"])

def run_production():
    """Run in production mode - professional setup"""
    print("🏭 Starting Carbon-Aware FinOps Dashboard (Production Mode)")
    print("📍 Dashboard: http://localhost:8050")
    print("⚡ Multi-worker setup (2 workers)")
    print("🛡️ Production optimizations active")
    print("-" * 50)
    
    # Create gunicorn config
    gunicorn_config = """
# Gunicorn configuration for Carbon-Aware FinOps Dashboard
bind = "0.0.0.0:8050"
workers = 2
worker_class = "sync"
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "carbon-finops-dashboard"

# Worker recycling
worker_connections = 1000
"""
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Write config file
    with open("gunicorn.conf.py", "w") as f:
        f.write(gunicorn_config.strip())
    
    # Run with Gunicorn
    subprocess.run([
        "gunicorn", 
        "--config", "gunicorn.conf.py",
        "dashboard.dashboard_main:server"
    ])

def run_demo():
    """Run optimized demo mode"""
    print("🎓 Starting Carbon-Aware FinOps Dashboard (Demo Mode)")
    print("📍 Dashboard: http://localhost:8050")
    print("🎯 Optimized for Bachelor Thesis presentation")
    print("📊 All APIs active, performance monitoring enabled")
    print("-" * 50)
    
    # Set demo environment
    os.environ["DASH_ENV"] = "demo"
    os.environ["ENABLE_PERFORMANCE_MONITORING"] = "true"
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run with single worker for stability
    subprocess.run([
        "gunicorn", 
        "--bind", "0.0.0.0:8050",
        "--workers", "1",
        "--timeout", "60",
        "--access-logfile", "logs/demo-access.log",
        "--error-logfile", "logs/demo-error.log",
        "--log-level", "info",
        "dashboard.dashboard_main:server"
    ])

def show_hybrid_help():
    """Show integrated help for both systems"""
    print("🔗 HYBRID SYSTEM - Choose your workflow:")
    print("=" * 50)
    print()
    print("🐍 PYTHON Commands (Quick Dashboard Development):")
    print("  python run.py dev          # Development mode")
    print("  python run.py demo         # Bachelor Thesis presentation")
    print("  python run.py prod         # Production mode")
    print("  python status.py           # Health check")
    print()
    print("🛠️ MAKEFILE Commands (Infrastructure & DevOps):")
    print("  make quick                 # Setup + dev (first time)")
    print("  make dev                   # Development mode")
    print("  make demo                  # Demo mode")
    print("  make health                # Health check")
    print("  make setup                 # Environment setup")
    print("  make deploy                # AWS infrastructure")
    print("  make test                  # API tests")
    print()
    print("💡 Recommendation:")
    print("  Daily work:    python run.py dev")
    print("  First setup:   make quick")
    print("  AWS work:      make deploy")
    print()

def main():
    parser = argparse.ArgumentParser(
        description="Carbon-Aware FinOps Dashboard Launcher - Hybrid System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Hybrid System Examples:
  python run.py dev          # Development mode (default)
  python run.py prod         # Production mode
  python run.py demo         # Bachelor Thesis demo mode
  python run.py --hybrid     # Show integrated help

Makefile alternatives:
  make dev                   # Same as: python run.py dev
  make demo                  # Same as: python run.py demo
  make quick                 # Setup + development
        """
    )
    
    parser.add_argument(
        "--hybrid", 
        action="store_true",
        help="Show hybrid system help"
    )
    
    parser.add_argument(
        "mode", 
        nargs="?", 
        default="dev",
        choices=["dev", "prod", "demo"],
        help="Run mode (default: dev)"
    )
    
    args = parser.parse_args()
    
    # Handle hybrid help
    if args.hybrid:
        show_hybrid_help()
        return
    
    # Banner
    print("=" * 50)
    print("🌍 Carbon-Aware FinOps Dashboard")
    print("🎓 Bachelor Thesis Project 2025")
    print("🔗 Hybrid System: Makefile + Python")
    print("=" * 50)
    
    # Show alternative commands
    if args.mode == "dev":
        print("💡 Alternative: make dev")
    elif args.mode == "demo":
        print("💡 Alternative: make demo")
    print("💡 Full help: python run.py --hybrid")
    print()
    
    try:
        if args.mode == "dev":
            run_development()
        elif args.mode == "prod":
            run_production()
        elif args.mode == "demo":
            run_demo()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()