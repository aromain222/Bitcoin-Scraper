#!/usr/bin/env python3
"""
Helper script to set up Google Sheets for the DCF Model Builder.
This script will show you the service account email and provide setup instructions.
"""

import os
import json

def get_service_account_info():
    """Get service account email from credentials file."""
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or 'credentials/google_sheets_credentials.json'
    
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id', 'Unknown')
        client_email = creds_data.get('client_email', 'Unknown')
        
        print("=" * 60)
        print("GOOGLE SHEETS SETUP INFORMATION")
        print("=" * 60)
        print(f"Project ID: {project_id}")
        print(f"Service Account Email: {client_email}")
        print()
        print("SETUP INSTRUCTIONS:")
        print("1. Go to https://sheets.google.com")
        print("2. Create a new Google Sheet")
        print("3. Name it 'DCF' (exactly as shown)")
        print("4. Create a tab named 'Microsoft'")
        print("5. Click 'Share' button (top right)")
        print("6. Add this email as an Editor:")
        print(f"   {client_email}")
        print("7. Make sure to give 'Editor' permissions")
        print("8. Click 'Send' (you don't need to send an email)")
        print()
        print("After setup, run: python microsoft_dcf.py")
        print("=" * 60)
        
        return client_email
        
    except FileNotFoundError:
        print("ERROR: Credentials file not found!")
        print(f"Expected location: {creds_path}")
        print("Make sure you have the correct service account JSON file.")
        return None
    except Exception as e:
        print(f"ERROR reading credentials: {e}")
        return None

if __name__ == "__main__":
    get_service_account_info() 