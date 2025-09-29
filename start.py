#!/usr/bin/env python3
import os

# Get port, default to 8080 if not set
port = os.environ.get('PORT', '8080')
print(f"Starting on port {port}")

# Use exec to replace this process with gunicorn
os.execvp('gunicorn', [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1', 
    '--timeout', '120',
    'financial_models_ui:app'
])
