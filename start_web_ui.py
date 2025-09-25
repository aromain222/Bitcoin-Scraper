#!/usr/bin/env python3
"""
Simple launcher for the Professional Financial Models Web UI
Just run this script to start the web interface!
"""

import subprocess
import sys
import os

def main():
    print("🏦 Starting Professional Financial Models Web UI...")
    print("=" * 60)
    print("🎯 This will launch a beautiful web interface for all your financial models")
    print("📱 Access it at: http://localhost:5000")
    print("=" * 60)

    try:
        # Run the web UI
        subprocess.run([sys.executable, "financial_models_ui.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting web UI: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure Flask is installed: pip install flask")
        print("2. Check that port 5000 is not in use")
        print("3. Try running directly: python financial_models_ui.py")

if __name__ == "__main__":
    main()
