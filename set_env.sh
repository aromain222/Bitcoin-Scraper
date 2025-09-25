#!/bin/bash

# Path to your Google Sheets service account credentials JSON file
# Replace with your actual path
export GOOGLE_SHEETS_CREDENTIALS="./credentials/google_sheets_credentials.json"

# Your Google Spreadsheet ID
# Get this from your Google Sheet URL: https://docs.google.com/spreadsheets/d/[THIS-IS-YOUR-SHEET-ID]/edit
export GOOGLE_SHEETS_ID="12Q37rsVhEetQy0V8tc_sPtBTa3IaKsCVGEe8FSoL_40"

# Google Search API credentials
# Get these from:
# 1. API Key: https://console.cloud.google.com/apis/credentials
# 2. Search Engine ID: https://programmablesearch.google.com/
export GOOGLE_SEARCH_API_KEY="AIzaSyBzQfLvbn9e97jtSsGAZXmOdGhIlNxmWKA"
export GOOGLE_SEARCH_CX="66aa9201e6c1f4102"

echo "Environment variables set successfully!" 