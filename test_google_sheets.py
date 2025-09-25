#!/usr/bin/env python3
"""
Test script to verify Google Sheets connectivity.
This tests only the Sheets API, not Drive API.
"""

import os
import json

# Auto-install gspread if needed
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Installing gspread...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gspread", "google-auth"])
    import gspread
    from google.oauth2.service_account import Credentials

def test_google_sheets():
    """Test Google Sheets connectivity."""
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or 'credentials/google_sheets_credentials.json'
    
    try:
        # Load credentials
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id', 'Unknown')
        client_email = creds_data.get('client_email', 'Unknown')
        
        print(f"Testing connection to project: {project_id}")
        print(f"Service account: {client_email}")
        print()
        
        # Use only Sheets API scope
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        
        print("✅ Successfully authenticated with Google Sheets API")
        
        # Try to find the DCF Model sheet
        try:
            sh = gc.open("DCF Model")
            print("✅ Found 'DCF Model' sheet")
            
            # List all worksheets
            worksheets = sh.worksheets()
            print(f"📋 Worksheets found: {[ws.title for ws in worksheets]}")
            
            # Try to access the first worksheet
            if worksheets:
                ws = worksheets[0]
                print(f"✅ Successfully accessed worksheet: {ws.title}")
                print(f"📊 Sheet URL: {sh.url}")
                return True
            else:
                print("❌ No worksheets found in the sheet")
                return False
                
        except gspread.SpreadsheetNotFound:
            print("❌ 'DCF Model' sheet not found")
            print("Please create a Google Sheet named 'DCF Model' and share it with:")
            print(f"   {client_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Google Sheets connectivity...")
    print("=" * 50)
    success = test_google_sheets()
    print("=" * 50)
    if success:
        print("🎉 Google Sheets setup is working!")
        print("You can now run: python dcf_model.py")
    else:
        print("❌ Google Sheets setup needs attention")
        print("Please follow the setup instructions and try again.") 