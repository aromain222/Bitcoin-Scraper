#!/usr/bin/env python3
import os

# Check what Railway is giving us
railway_port = os.environ.get('PORT')
print(f"Railway PORT environment variable: {railway_port}")

# Use Railway's port if available, otherwise default to 8080
if railway_port and railway_port.isdigit():
    port = railway_port
    print(f"Using Railway's assigned port: {port}")
else:
    port = '8080'
    print(f"Using default port: {port}")

print(f"Starting MINIMAL FinModAI on 0.0.0.0:{port}")

# Use minimal app instead of the complex one
os.execvp('gunicorn', [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1', 
    '--timeout', '30',
    'minimal_app:app'
])
