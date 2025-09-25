#!/usr/bin/env python3
"""
Comprehensive Financial Data Searcher
Using your Google Custom Search API
"""

import requests
import json
import time
from typing import List, Dict, Optional

class FinancialDataSearcher:
    def __init__(self):
        self.api_key = "AIzaSyCfM2DXKyP8-9mo-yyxDICf8GJqX053a4Q"
        self.search_engine_id = "a3eb9b4308a3c4682"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    def search_financial_data(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search for financial data"""
        
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': min(num_results, 10)
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_results(data)
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def search_company(self, ticker: str, data_types: Optional[List[str]] = None) -> Dict:
        """Search for comprehensive company data"""
        
        if data_types is None:
            data_types = [
                "financial statements",
                "revenue earnings", 
                "balance sheet",
                "analyst ratings",
                "market cap",
                "quarterly earnings"
            ]
        
        results = {}
        
        for data_type in data_types:
            query = f"{ticker} {data_type}"
            print(f"🔍 Searching: {query}")
            
            search_results = self.search_financial_data(query, num_results=5)
            results[data_type] = search_results
            
            # Rate limiting
            time.sleep(1)
        
        return results
    
    def search_multiple_companies(self, tickers: List[str]) -> Dict:
        """Search for multiple companies"""
        
        all_results = {}
        
        for ticker in tickers:
            print(f"\n🏢 Searching for {ticker}...")
            company_results = self.search_company(ticker)
            all_results[ticker] = company_results
            
            # Rate limiting between companies
            time.sleep(2)
        
        return all_results
    
    def search_specific_data(self, ticker: str, data_type: str) -> List[Dict]:
        """Search for specific type of data"""
        
        queries = {
            "financial_statements": [
                f"{ticker} financial statements",
                f"{ticker} income statement",
                f"{ticker} balance sheet",
                f"{ticker} cash flow statement"
            ],
            "earnings": [
                f"{ticker} quarterly earnings",
                f"{ticker} earnings report",
                f"{ticker} revenue growth",
                f"{ticker} net income"
            ],
            "analyst_coverage": [
                f"{ticker} analyst ratings",
                f"{ticker} price target",
                f"{ticker} buy sell hold",
                f"{ticker} earnings estimates"
            ],
            "market_data": [
                f"{ticker} market cap",
                f"{ticker} stock price",
                f"{ticker} P/E ratio",
                f"{ticker} dividend yield"
            ],
            "news": [
                f"{ticker} news",
                f"{ticker} latest news",
                f"{ticker} company updates"
            ]
        }
        
        if data_type not in queries:
            print(f"❌ Unknown data type: {data_type}")
            return []
        
        all_results = []
        
        for query in queries[data_type]:
            results = self.search_financial_data(query, num_results=3)
            all_results.extend(results)
            time.sleep(1)
        
        return all_results
    
    def _parse_results(self, data: Dict) -> List[Dict]:
        """Parse search results"""
        
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
    
    def print_results(self, results: List[Dict], title: str = "Search Results"):
        """Print search results nicely"""
        
        print(f"\n📊 {title}")
        print("=" * 60)
        
        if not results:
            print("❌ No results found")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   🌐 {result['url']}")
            print(f"   📰 {result['source']}")
            print(f"   📝 {result['snippet'][:150]}...")
            if result['date']:
                print(f"   📅 {result['date']}")

def main():
    """Main function to demonstrate usage"""
    
    print("🚀 Financial Data Searcher")
    print("=" * 40)
    print("API Key: AIzaSyCfM2DXKyP8-9mo-yyxDICf8GJqX053a4Q")
    print("Search Engine ID: a3eb9b4308a3c4682")
    print()
    
    searcher = FinancialDataSearcher()
    
    # Test 1: Search for Microsoft financial data
    print("🔍 Test 1: Microsoft Financial Data")
    msft_results = searcher.search_financial_data("MSFT financial statements", num_results=3)
    searcher.print_results(msft_results, "Microsoft Financial Data")
    
    # Test 2: Search for Apple earnings
    print("\n🔍 Test 2: Apple Earnings Data")
    aapl_results = searcher.search_financial_data("AAPL quarterly earnings", num_results=3)
    searcher.print_results(aapl_results, "Apple Earnings Data")
    
    # Test 3: Search for Tesla analyst ratings
    print("\n🔍 Test 3: Tesla Analyst Ratings")
    tsla_results = searcher.search_financial_data("TSLA analyst ratings", num_results=3)
    searcher.print_results(tsla_results, "Tesla Analyst Ratings")
    
    # Test 4: Comprehensive company search
    print("\n🔍 Test 4: Comprehensive Google Search")
    googl_comprehensive = searcher.search_company("GOOGL", ["financial statements", "analyst ratings"])
    
    for data_type, results in googl_comprehensive.items():
        searcher.print_results(results, f"Google {data_type.title()}")
    
    print("\n✅ All tests completed successfully!")
    print("\n🎯 You can now search for any company's financial data!")

if __name__ == "__main__":
    main() 