#!/usr/bin/env python3
"""
Test script for Microsoft tab in DCF Google Sheet
Uses the correct project: modeo-466403
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

def test_microsoft_sheet():
    """Test connection to Microsoft tab in DCF sheet."""
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
        
        # Verify correct project
        if project_id != 'modeo-466403':
            print(f"❌ Wrong project! Expected 'modeo-466403', got '{project_id}'")
            print("Please use the correct service account credentials file.")
            return False
        
        # Use only Sheets API scope
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        
        print("✅ Successfully authenticated with Google Sheets API")
        
        # Try to find the DCF sheet
        try:
            sh = gc.open("DCF")
            print("✅ Found 'DCF' sheet")
            
            # List all worksheets
            worksheets = sh.worksheets()
            print(f"📋 Worksheets found: {[ws.title for ws in worksheets]}")
            
            # Try to access the Microsoft worksheet
            try:
                ws = sh.worksheet("Microsoft")
                print("✅ Found 'Microsoft' tab")
                print(f"📊 Sheet URL: {sh.url}")
                return True
            except gspread.WorksheetNotFound:
                print("❌ 'Microsoft' tab not found")
                print("Please create a tab named 'Microsoft' in your DCF sheet")
                return False
                
        except gspread.SpreadsheetNotFound:
            print("❌ 'DCF' sheet not found")
            print("Please create a Google Sheet named 'DCF' and share it with:")
            print(f"   {client_email}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Microsoft tab in DCF sheet...")
    print("=" * 50)
    success = test_microsoft_sheet()
    print("=" * 50)
    if success:
        print("🎉 Microsoft tab setup is working!")
        print("You can now run: python microsoft_dcf.py")
    else:
        print("❌ Setup needs attention")
        print("Please follow the setup instructions and try again.") 