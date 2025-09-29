#!/usr/bin/env python3
import os

# Check what Railway is giving us
railway_port = os.environ.get('PORT')
print(f"Railway PORT environment variable: {railway_port}")

# Use assigned port if available, otherwise default to 10000 (Render default)
if railway_port and railway_port.isdigit():
    port = railway_port
    print(f"Using assigned port: {port}")
else:
    port = '10000'
    print(f"Using default port: {port}")

print(f"Starting MINIMAL FinModAI on 0.0.0.0:{port}")

# Use minimal app instead of the complex one
os.execvp('gunicorn', [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1', 
    '--timeout', '120',
    '--keep-alive', '5',
    '--max-requests', '100',
    '--worker-class', 'sync',
    '--log-level', 'info',
    'minimal_app:app'
])
