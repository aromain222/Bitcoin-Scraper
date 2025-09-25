#!/usr/bin/env python3
"""
Quick test of Google Custom Search with your API key
"""

import requests
import json

# Your API key and search engine ID
API_KEY = "AIzaSyCfM2DXKyP8-9mo-yyxDICf8GJqX053a4Q"
SEARCH_ENGINE_ID = "a3eb9b4308a3c4682"

def test_search():
    """Test the Google Custom Search API"""
    
    print("🧪 Testing Google Custom Search API")
    print("=" * 40)
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Search Engine ID: {SEARCH_ENGINE_ID}")
    print()
    
    # Test search for Microsoft financial data
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': 'MSFT financial statements',
        'num': 3
    }
    
    try:
        print("🔍 Searching for 'MSFT financial statements'...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data:
                print(f"✅ Success! Found {len(data['items'])} results")
                print()
                
                for i, item in enumerate(data['items'], 1):
                    print(f"📊 Result {i}:")
                    print(f"   Title: {item.get('title', 'N/A')}")
                    print(f"   URL: {item.get('link', 'N/A')}")
                    print(f"   Source: {extract_source(item.get('link', ''))}")
                    print(f"   Snippet: {item.get('snippet', 'N/A')[:100]}...")
                    print()
                
                return True
            else:
                print("⚠️ No results found")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def extract_source(url):
    """Extract source website from URL"""
    sources = {
        'finance.yahoo.com': 'Yahoo Finance',
        'seekingalpha.com': 'Seeking Alpha',
        'marketwatch.com': 'MarketWatch',
        'finviz.com': 'Finviz',
        'macrotrends.net': 'Macrotrends',
        'sec.gov': 'SEC EDGAR',
        'bloomberg.com': 'Bloomberg',
        'reuters.com': 'Reuters',
        'cnbc.com': 'CNBC'
    }
    
    for domain, name in sources.items():
        if domain in url:
            return name
    return 'Other'

def search_company(ticker):
    """Search for a specific company"""
    
    print(f"🔍 Searching for {ticker}...")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': f'{ticker} financial data',
        'num': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data:
                print(f"✅ Found {len(data['items'])} results for {ticker}")
                
                for i, item in enumerate(data['items'], 1):
                    source = extract_source(item.get('link', ''))
                    print(f"   {i}. {item.get('title', 'N/A')} ({source})")
                
                return data['items']
            else:
                print(f"⚠️ No results found for {ticker}")
                return []
        else:
            print(f"❌ Error searching for {ticker}: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    # Test basic functionality
    success = test_search()
    
    if success:
        print("🎉 Your Google Custom Search is working perfectly!")
        print()
        
        # Test multiple companies
        companies = ["AAPL", "GOOGL", "TSLA"]
        
        print("🔍 Testing multiple companies...")
        for company in companies:
            search_company(company)
            print()
        
        print("✅ All tests completed successfully!")
        print("\n🚀 You can now use this for:")
        print("   - Searching financial websites")
        print("   - Getting company data")
        print("   - Finding analyst reports")
        print("   - Accessing SEC filings")
        
    else:
        print("❌ There was an issue with the API key or search engine") 