#!/usr/bin/env python3
import os

# Force port to 8080 - ignore Railway's PORT variable for now
port = '8080'
print(f"FORCING port to {port}")

# Use exec to replace this process with gunicorn
os.execvp('gunicorn', [
    'gunicorn',
    '--bind', f'0.0.0.0:{port}',
    '--workers', '1', 
    '--timeout', '120',
    'financial_models_ui:app'
])
