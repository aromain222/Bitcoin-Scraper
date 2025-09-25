# Google Sheets Integration Setup Guide

## Overview
This application creates professional financial models directly in your Google Drive using Google Sheets. To enable this functionality, you need to set up Google OAuth credentials.

## Step-by-Step Setup

### 1. Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### 2. Create a New Project (or select existing)
- Click "Select a Project" → "New Project"
- Name: "Financial Models App"
- Click "Create"

### 3. Enable Required APIs
Go to "APIs & Services" → "Library" and enable these APIs:
- ✅ **Google Sheets API**
- ✅ **Google Drive API**
- ✅ **Google OAuth2 API**

### 4. Configure OAuth Consent Screen
Go to "APIs & Services" → "OAuth consent screen":
- Choose "External" (unless you have a Google Workspace)
- Fill in required fields:
  - App name: "Financial Models Generator"
  - User support email: Your email
  - Developer contact: Your email
- Add scopes:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive.file`
  - `https://www.googleapis.com/auth/userinfo.email`

### 5. Create OAuth Credentials
Go to "APIs & Services" → "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs":
- Application type: "Web application"
- Name: "Financial Models Web Client"
- Authorized JavaScript origins:
  - `http://localhost:8080`
- Authorized redirect URIs:
  - `http://localhost:5001/callback`

### 6. Update Your App Configuration
After creating credentials, you'll get a Client ID and Client Secret. Update `backend/app.py`:

```python
CLIENT_CONFIG = {
    "web": {
        "client_id": "YOUR_ACTUAL_CLIENT_ID.googleusercontent.com",
        "client_secret": "YOUR_ACTUAL_CLIENT_SECRET",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:5001/callback"],
        "javascript_origins": ["http://localhost:8080"]
    }
}
```

## Testing the Setup

1. **Start the servers**:
   ```bash
   ./start.sh    # Mac/Linux
   # or
   start.bat     # Windows
   ```

2. **Open the app**: http://localhost:8080

3. **Enter your email** (must be the same email you used in Google Cloud Console)

4. **Complete OAuth flow** - you should see a Google permission screen

5. **Generate models** - sheets should be created in your Google Drive!

## Troubleshooting

### "redirect_uri_mismatch" Error
- Make sure redirect URI in Google Console exactly matches: `http://localhost:5001/callback`

### "access_denied" Error
- Check that you added the correct scopes in OAuth consent screen
- Make sure APIs are enabled

### "invalid_client" Error
- Verify Client ID and Client Secret are correct
- Check that JavaScript origins include `http://localhost:8080`

### Models Not Appearing in Drive
- Check Google Drive's "Recent" section
- Search for your company name in Drive
- Verify the app has permission to create files

## Security Notes

⚠️ **Important**: The current setup is for development only!

For production:
- Use environment variables for credentials
- Set up proper domain verification
- Use HTTPS
- Implement proper error handling
- Add rate limiting

## Support

If you encounter issues:
1. Check the browser console for errors
2. Check the Python console for backend errors
3. Verify all Google Cloud Console settings
4. Make sure all required APIs are enabled

The app will create beautiful, formatted Google Sheets directly in your Drive with professional financial models! 