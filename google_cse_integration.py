#!/usr/bin/env python3
"""
Google Custom Search Engine Integration for Financial Data
"""

import requests
import json
import time
import os
from typing import List, Dict, Optional
from urllib.parse import quote_plus

class GoogleCSESearch:
    def __init__(self, api_key: Optional[str] = None, search_engine_id: str = "a3eb9b4308a3c4682"):
        """
        Initialize Google Custom Search Engine
        
        Args:
            api_key: Google Custom Search API key
            search_engine_id: Your CSE ID (cx parameter)
        """
        # Try to get API key from multiple sources
        if api_key:
            self.api_key = api_key
        else:
            # Try environment variable first
            self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
            
            # Try config file if not in environment
            if not self.api_key:
                try:
                    from config import GOOGLE_SEARCH_API_KEY
                    self.api_key = GOOGLE_SEARCH_API_KEY
                except ImportError:
                    pass
        
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key:
            print("⚠️ Warning: No Google Search API key found. Set GOOGLE_SEARCH_API_KEY environment variable.")
            print("   Get your API key from: https://console.cloud.google.com/")
        
    def search_financial_data(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Search for financial data using Google CSE
        
        Args:
            query: Search query (e.g., "MSFT financial statements")
            num_results: Number of results to return (max 10 per request)
            
        Returns:
            List of search results with title, url, snippet, and source
        """
        
        if not self.api_key:
            print("❌ No API key available. Cannot perform search.")
            return []
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': min(num_results, 10)  # Google CSE max is 10 per request
        }
        
        try:
            print(f"🔍 Searching: {query}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_search_results(data)
            
            print(f"✅ Found {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Search failed: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse response: {e}")
            return []
            
    def search_company(self, ticker: str, search_types: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        Search for comprehensive company data
        
        Args:
            ticker: Company ticker symbol (e.g., "MSFT")
            search_types: Types of data to search for
            
        Returns:
            Dictionary with search results organized by type
        """
        
        if search_types is None:
            search_types = [
                "financial statements",
                "revenue earnings",
                "balance sheet",
                "analyst ratings",
                "market cap",
                "quarterly earnings"
            ]
        
        all_results = {}
        
        for search_type in search_types:
            query = f"{ticker} {search_type}"
            results = self.search_financial_data(query, num_results=5)
            all_results[search_type] = results
            
            # Rate limiting - Google CSE has limits
            time.sleep(1)
        
        return all_results
        
    def search_multiple_companies(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Search for multiple companies
        
        Args:
            tickers: List of company ticker symbols
            
        Returns:
            Dictionary with results for each company
        """
        
        all_companies = {}
        
        for ticker in tickers:
            print(f"\n🔍 Searching for {ticker}...")
            company_results = self.search_company(ticker)
            all_companies[ticker] = company_results
            
            # Rate limiting between companies
            time.sleep(2)
        
        return all_companies
        
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """Parse Google CSE response"""
        
        results = []
        
        if 'items' in data:
            for item in data['items']:
                result = {
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': self._extract_source(item.get('link', '')),
                    'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', '')
                }
                results.append(result)
        
        return results
        
    def _extract_source(self, url: str) -> str:
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
            'cnbc.com': 'CNBC',
            'zacks.com': 'Zacks',
            'gurufocus.com': 'GuruFocus',
            'tikr.com': 'Tikr'
        }
        
        for domain, name in sources.items():
            if domain in url:
                return name
                
        return 'Other'
        
    def get_financial_websites(self) -> List[str]:
        """Get list of financial websites in the CSE"""
        
        return [
            "https://finance.yahoo.com/",
            "https://seekingalpha.com/",
            "https://marketwatch.com/",
            "https://finviz.com/",
            "https://macrotrends.net/",
            "https://sec.gov/edgar/",
            "https://bloomberg.com/",
            "https://reuters.com/markets/companies/",
            "https://cnbc.com/quotes/",
            "https://zacks.com/",
            "https://gurufocus.com/",
            "https://tikr.com/"
        ]

def test_google_cse():
    """Test the Google CSE integration"""
    
    print("🧪 Testing Google Custom Search Engine Integration")
    print("=" * 60)
    
    # Initialize searcher
    searcher = GoogleCSESearch()
    
    # Test basic search
    print("\n1️⃣ Testing basic search...")
    results = searcher.search_financial_data("MSFT financial statements", num_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n📊 Result {i}:")
        print(f"   Title: {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Source: {result['source']}")
        print(f"   Snippet: {result['snippet'][:100]}...")
    
    # Test company search
    print("\n2️⃣ Testing company search...")
    company_results = searcher.search_company("AAPL", ["financial statements", "revenue"])
    
    for search_type, results in company_results.items():
        print(f"\n🔍 {search_type.upper()}:")
        for result in results[:2]:  # Show first 2 results
            print(f"   - {result['title']} ({result['source']})")
    
    # Test multiple companies
    print("\n3️⃣ Testing multiple companies...")
    companies = ["MSFT", "GOOGL"]
    multi_results = searcher.search_multiple_companies(companies)
    
    for company, results in multi_results.items():
        print(f"\n🏢 {company}:")
        total_results = sum(len(r) for r in results.values())
        print(f"   Total results: {total_results}")
        for search_type, search_results in results.items():
            print(f"   - {search_type}: {len(search_results)} results")

def create_search_queries():
    """Create example search queries for different financial data types"""
    
    queries = {
        "financial_statements": [
            "{TICKER} financial statements",
            "{TICKER} income statement",
            "{TICKER} balance sheet",
            "{TICKER} cash flow statement"
        ],
        "earnings": [
            "{TICKER} quarterly earnings",
            "{TICKER} earnings report",
            "{TICKER} revenue growth",
            "{TICKER} net income"
        ],
        "analyst_coverage": [
            "{TICKER} analyst ratings",
            "{TICKER} price target",
            "{TICKER} buy sell hold",
            "{TICKER} earnings estimates"
        ],
        "market_data": [
            "{TICKER} market cap",
            "{TICKER} stock price",
            "{TICKER} P/E ratio",
            "{TICKER} dividend yield"
        ],
        "news": [
            "{TICKER} news",
            "{TICKER} latest news",
            "{TICKER} company updates",
            "{TICKER} press releases"
        ]
    }
    
    return queries

def search_comprehensive_company_data(ticker: str, api_key: str) -> Dict:
    """
    Comprehensive company data search
    
    Args:
        ticker: Company ticker symbol
        api_key: Google Search API key
        
    Returns:
        Comprehensive search results
    """
    
    searcher = GoogleCSESearch(api_key)
    queries = create_search_queries()
    
    all_results = {}
    
    for category, query_list in queries.items():
        print(f"\n🔍 Searching {category} for {ticker}...")
        category_results = []
        
        for query_template in query_list:
            query = query_template.format(TICKER=ticker)
            results = searcher.search_financial_data(query, num_results=3)
            category_results.extend(results)
            time.sleep(1)  # Rate limiting
        
        all_results[category] = category_results
    
    return all_results

if __name__ == "__main__":
    # Check if API key is available
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    
    if api_key:
        print("✅ Google Search API key found")
        test_google_cse()
    else:
        print("❌ No Google Search API key found")
        print("\n📋 To set up your API key:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Custom Search API")
        print("4. Create credentials (API key)")
        print("5. Set environment variable:")
        print("   export GOOGLE_SEARCH_API_KEY='your_api_key_here'")
        
        print("\n🔍 Example usage with API key:")
        print("searcher = GoogleCSESearch('your_api_key')")
        print("results = searcher.search_company('MSFT')") 