#!/usr/bin/env python3
"""
Google Drive OAuth2 Setup for Excel Sharing System
Creates OAuth2 credentials for Google Drive integration
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# OAuth2 scopes for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def setup_google_drive_oauth():
    """Set up OAuth2 credentials for Google Drive."""
    print("🔐 Google Drive OAuth2 Setup")
    print("=" * 40)
    
    print("\n📋 Step 1: Create OAuth2 Credentials")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Select your project: ecstatic-magpie-466323-s3")
    print("3. Go to APIs & Services > Credentials")
    print("4. Click 'Create Credentials' > 'OAuth client ID'")
    print("5. Choose 'Desktop application'")
    print("6. Download the JSON file")
    
    # Check if we have the service account file
    service_account_file = "google_drive_credentials.json"
    if os.path.exists(service_account_file):
        print(f"\n✅ Found service account file: {service_account_file}")
        
        # Convert service account to OAuth2 client credentials
        print("\n🔄 Converting service account to OAuth2 client...")
        
        with open(service_account_file, 'r') as f:
            service_account = json.load(f)
        
        # Create OAuth2 client credentials
        oauth2_credentials = {
            "installed": {
                "client_id": service_account.get("client_id", ""),
                "project_id": service_account.get("project_id", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "",  # Service accounts don't have client_secret
                "redirect_uris": ["http://localhost"]
            }
        }
        
        # Save OAuth2 credentials
        oauth2_file = "google_drive_oauth2_credentials.json"
        with open(oauth2_file, 'w') as f:
            json.dump(oauth2_credentials, f, indent=2)
        
        print(f"✅ OAuth2 credentials saved to: {oauth2_file}")
        print("\n⚠️  Note: You need to create a proper OAuth2 client ID in Google Cloud Console")
        print("   The service account approach won't work for file uploads.")
        
        return oauth2_file
    else:
        print(f"\n❌ Service account file not found: {service_account_file}")
        return None

def authenticate_google_drive():
    """Authenticate with Google Drive using OAuth2."""
    oauth2_file = setup_google_drive_oauth()
    
    if not oauth2_file or not os.path.exists(oauth2_file):
        print("\n❌ OAuth2 credentials not found. Please create them in Google Cloud Console.")
        return None
    
    try:
        # Start OAuth2 flow
        flow = InstalledAppFlow.from_client_secrets_file(oauth2_file, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        token_file = 'google_drive_token.pickle'
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        
        print(f"\n✅ Authentication successful!")
        print(f"✅ Credentials saved to: {token_file}")
        return creds
        
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Setting up Google Drive OAuth2 authentication...")
    creds = authenticate_google_drive()
    
    if creds:
        print("\n🎉 Google Drive setup complete!")
        print("You can now use the Excel sharing system with Google Drive.")
    else:
        print("\n❌ Setup failed. Please check the instructions above.")
