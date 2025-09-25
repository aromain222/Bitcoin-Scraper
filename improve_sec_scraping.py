#!/usr/bin/env python3
"""
Improved SEC EDGAR scraping with better error handling and rate limiting
"""

import requests
import time
import random
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import logging

class ImprovedSECScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.max_retries = 3
        self.timeout = 30
        
    def scrape_with_retry(self, url, retries=None):
        """Scrape with exponential backoff and retry logic"""
        if retries is None:
            retries = self.max_retries
            
        for attempt in range(retries):
            try:
                # Add random delay to avoid rate limiting
                time.sleep(self.rate_limit_delay + random.uniform(0, 0.1))
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Check if we got blocked
                if 'access denied' in response.text.lower() or 'blocked' in response.text.lower():
                    raise Exception("Access denied - likely blocked")
                    
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise e
                    
                # Exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"   ⚠️ SEC request failed, retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                
    def get_company_facts(self, ticker):
        """Get company facts from SEC with improved error handling"""
        try:
            # Use SEC's JSON API instead of scraping HTML
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{ticker.zfill(10)}.json"
            
            response = self.scrape_with_retry(facts_url)
            data = response.json()
            
            # Extract key financial data
            facts = data.get('facts', {})
            
            # Get revenue from different possible sources
            revenue_sources = ['us-gaap:Revenues', 'us-gaap:SalesRevenueNet', 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax']
            revenue = None
            
            for source in revenue_sources:
                if source in facts:
                    units = facts[source].get('units', {})
                    for unit_type, values in units.items():
                        if unit_type in ['USD', 'usd']:
                            # Get most recent annual value
                            annual_values = [v for v in values if v.get('form') == '10-K']
                            if annual_values:
                                revenue = max(annual_values, key=lambda x: x.get('end', ''))
                                break
                    if revenue:
                        break
            
            # Get other key metrics
            assets = self._extract_metric(facts, 'us-gaap:Assets')
            equity = self._extract_metric(facts, 'us-gaap:StockholdersEquity')
            net_income = self._extract_metric(facts, 'us-gaap:NetIncomeLoss')
            
            return {
                'sec_revenue': revenue.get('val') if revenue else None,
                'sec_total_assets': assets,
                'sec_stockholders_equity': equity,
                'sec_net_income': net_income,
                'data_quality': 'high' if revenue else 'low'
            }
            
        except Exception as e:
            print(f"   ⚠️ SEC scraping failed for {ticker}: {str(e)}")
            return None
            
    def _extract_metric(self, facts, metric_name):
        """Extract metric from SEC facts data"""
        if metric_name not in facts:
            return None
            
        units = facts[metric_name].get('units', {})
        for unit_type, values in units.items():
            if unit_type in ['USD', 'usd']:
                annual_values = [v for v in values if v.get('form') == '10-K']
                if annual_values:
                    latest = max(annual_values, key=lambda x: x.get('end', ''))
                    return latest.get('val')
        return None

def improved_scrape_edgar_sec_data(ticker):
    """Improved SEC EDGAR data scraping"""
    scraper = ImprovedSECScraper()
    return scraper.get_company_facts(ticker)

if __name__ == "__main__":
    # Test the improved scraper
    test_tickers = ['MSFT', 'AAPL', 'GOOGL', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        data = improved_scrape_edgar_sec_data(ticker)
        if data:
            print(f"   ✅ Success: {data}")
        else:
            print(f"   ❌ Failed") 