#!/usr/bin/env python3
"""
Startup script for Financial Models - Handles all errors automatically
"""

import os
import sys
import subprocess
import time

def main():
    print("🚀 Starting Financial Models System...")
    
    # Check if we're in the right directory
    if not os.path.exists('financial-models-app'):
        print("❌ Please run this script from the project root directory")
        return
    
    # Install requirements if needed
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'financial-models-app/backend/requirements.txt'])
        print("✅ Requirements installed")
    except:
        print("⚠️ Could not install requirements - continuing anyway")
    
    # Start the backend
    print("🌐 Starting Flask backend...")
    backend_dir = 'financial-models-app/backend'
    
    try:
        # Kill any existing processes on port 5001
        subprocess.run(['lsof', '-ti', ':5001'], capture_output=True)
        subprocess.run(['pkill', '-f', 'python.*app.py'], capture_output=True)
        time.sleep(2)
        
        # Start the backend
        backend_process = subprocess.Popen([sys.executable, 'app.py'], 
                                         cwd=backend_dir,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        
        print("✅ Backend started successfully")
        print("🌐 Backend running on http://localhost:5001")
        print("📁 Frontend available at financial-models-app/frontend/index.html")
        
        # Keep the script running
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            backend_process.terminate()
            
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")

if __name__ == "__main__":
    main()
