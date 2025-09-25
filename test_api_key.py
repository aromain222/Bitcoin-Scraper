#!/usr/bin/env python3
"""
Quick test for Google Custom Search API key
"""

import os
import requests

def test_api_key(api_key):
    """Test if the API key works"""
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("❌ No valid API key found")
        print("Please get your API key from: https://console.cloud.google.com/")
        return False
    
    # Test URL
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': 'a3eb9b4308a3c4682',  # Your search engine ID
        'q': 'MSFT financial statements',
        'num': 1
    }
    
    try:
        print("🔍 Testing API key...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                print("✅ API key is working!")
                print(f"Found {len(data['items'])} results")
                return True
            else:
                print("⚠️ API key works but no results found")
                return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

def main():
    """Main function"""
    
    print("🧪 Google Custom Search API Key Test")
    print("=" * 40)
    
    # Try to get API key from different sources
    api_key = None
    
    # 1. Try environment variable
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    if api_key:
        print("📋 Found API key in environment variable")
    
    # 2. Try config file
    if not api_key:
        try:
            from config import GOOGLE_SEARCH_API_KEY
            api_key = GOOGLE_SEARCH_API_KEY
            print("📋 Found API key in config.py")
        except ImportError:
            print("📋 No config.py file found")
    
    # 3. Ask user to input
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("\n🔑 Please enter your Google Custom Search API key:")
        print("Get it from: https://console.cloud.google.com/")
        api_key = input("API Key: ").strip()
        
        if api_key:
            # Save to config file
            with open('config.py', 'w') as f:
                f.write(f'GOOGLE_SEARCH_API_KEY = "{api_key}"\n')
                f.write('GOOGLE_CSE_ID = "a3eb9b4308a3c4682"\n')
            print("💾 Saved API key to config.py")
    
    # Test the API key
    if api_key:
        success = test_api_key(api_key)
        
        if success:
            print("\n🎉 Your API key is working!")
            print("You can now use the Google Custom Search integration.")
        else:
            print("\n❌ API key test failed.")
            print("Please check your API key and try again.")
    else:
        print("\n❌ No API key provided.")

if __name__ == "__main__":
    main() 