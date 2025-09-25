#!/usr/bin/env python3
"""
Quick system test for the Financial Models API
Tests the enhanced backend functionality
"""

import requests
import json
import sys
import time

def test_api():
    """Test the financial models API"""
    
    print("🧪 Testing Professional Financial Models API")
    print("=" * 50)
    
    # Test data
    test_companies = [
        {"company_name": "Apple Inc.", "ticker": "AAPL", "models": ["dcf"]},
        {"company_name": "Microsoft Corporation", "ticker": "MSFT", "models": ["lbo"]},
        {"company_name": "Tesla Inc.", "ticker": "TSLA", "models": ["comps"]},
    ]
    
    base_url = "http://localhost:5001"
    
    # Test health check
    print("1️⃣ Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Message: {health_data.get('message')}")
        else:
            print("❌ Health check failed")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to API: {e}")
        print("   Make sure the backend is running on port 5001")
        return False
    
    print()
    
    # Test model generation
    print("2️⃣ Testing enhanced model generation...")
    
    for i, test_data in enumerate(test_companies, 1):
        print(f"\n   Test {i}: {test_data['company_name']} ({test_data['models'][0].upper()})")
        
        try:
            response = requests.post(
                f"{base_url}/api/generate",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   ✅ Model generated successfully!")
                    print(f"   📊 Model: {result['results'][0]['model_type']}")
                    print(f"   📁 Filename: {result['results'][0]['filename']}")
                    print(f"   📈 Data Quality: {result['results'][0]['data_quality']}")
                    print(f"   🔗 Download URL: {result['results'][0]['download_url']}")
                else:
                    print(f"   ❌ Generation failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ Request failed with status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API testing complete!")
    print("\n💡 Next steps:")
    print("   1. Open frontend/index.html in your browser")
    print("   2. Try generating models through the web interface")
    print("   3. Download and open the generated Excel files")
    
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)