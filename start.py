#!/usr/bin/env python3
"""
Startup script for FinModAI on Railway
Handles PORT environment variable properly
"""
import os
import subprocess
import sys

def main():
    # Get port from environment, default to 8080
    port = os.environ.get('PORT', '8080')
    
    print(f"🚀 Starting FinModAI on port {port}")
    
    # Build gunicorn command
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--timeout', '300',
        '--keep-alive', '5',
        '--max-requests', '50',
        '--max-requests-jitter', '5',
        '--worker-class', 'sync',
        '--log-level', 'info',
        '--access-logfile', '-',
        '--error-logfile', '-',
        'financial_models_ui:app'
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    # Execute gunicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Gunicorn failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()
