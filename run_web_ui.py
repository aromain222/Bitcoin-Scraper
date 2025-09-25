#!/usr/bin/env python3
"""
Launcher script for the Professional Financial Models Web UI
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'flask',
        'openpyxl',
        'pandas',
        'numpy',
        'yfinance',
        'gspread',
        'google-auth',
        'requests'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == 'google-auth':
                import google.auth
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("📦 Installing missing dependencies...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                '--user' if os.name == 'nt' else '',
                *missing_packages
            ])
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False

    return True

def main():
    """Main launcher function"""
    print("🏦 Professional Financial Models Web UI")
    print("=" * 50)

    # Check if UI file exists
    ui_file = "financial_models_ui.py"
    if not os.path.exists(ui_file):
        print(f"❌ UI file '{ui_file}' not found!")
        return

    # Check dependencies
    if not check_dependencies():
        return

    # Start the web server
    print("\n🚀 Launching Financial Models Web UI...")
    print("📱 Opening browser in a moment...")

    try:
        # Import and run the UI
        from financial_models_ui import run_server
        run_server()
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped by user")
    except Exception as e:
        print(f"❌ Error starting web UI: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all dependencies are installed")
        print("2. Check that port 5000 is not in use")
        print("3. Try running: python financial_models_ui.py")

if __name__ == '__main__':
    main()