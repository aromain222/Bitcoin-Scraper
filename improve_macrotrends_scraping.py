#!/usr/bin/env python3
"""
Improved Macrotrends scraping with better error handling and data format handling
"""

import requests
import time
import random
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import logging

class ImprovedMacrotrendsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        self.rate_limit_delay = 3.0  # 3 seconds between requests
        self.max_retries = 3
        self.timeout = 30
        
    def scrape_with_retry(self, url, retries=None):
        """Scrape with exponential backoff and retry logic"""
        if retries is None:
            retries = self.max_retries
            
        for attempt in range(retries):
            try:
                # Add random delay to avoid rate limiting
                time.sleep(self.rate_limit_delay + random.uniform(0, 2))
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Check if we got blocked
                if self._is_blocked(response):
                    raise Exception("Access denied - likely blocked")
                    
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise e
                    
                # Exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 3)
                print(f"   ⚠️ Macrotrends request failed, retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                
    def _is_blocked(self, response):
        """Check if we've been blocked"""
        blocked_indicators = [
            'access denied',
            'blocked',
            'captcha',
            'cloudflare',
            'rate limit',
            'too many requests',
            'forbidden'
        ]
        
        text = response.text.lower()
        return any(indicator in text for indicator in blocked_indicators)
        
    def get_company_data(self, ticker):
        """Get company data from Macrotrends with improved error handling"""
        try:
            # Try multiple Macrotrends endpoints for redundancy
            endpoints = [
                f"https://www.macrotrends.net/stocks/charts/{ticker}/financial-statements",
                f"https://www.macrotrends.net/stocks/charts/{ticker}/balance-sheet",
                f"https://www.macrotrends.net/stocks/charts/{ticker}/cash-flow-statement",
                f"https://www.macrotrends.net/stocks/charts/{ticker}/financial-ratios"
            ]
            
            data = {}
            
            for endpoint in endpoints:
                try:
                    response = self.scrape_with_retry(endpoint)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract data based on endpoint type
                    if 'financial-statements' in endpoint:
                        financial_data = self._extract_financial_statements(soup)
                        data.update(financial_data)
                        
                    elif 'balance-sheet' in endpoint:
                        balance_data = self._extract_balance_sheet(soup)
                        data.update(balance_data)
                        
                    elif 'cash-flow-statement' in endpoint:
                        cashflow_data = self._extract_cash_flow(soup)
                        data.update(cashflow_data)
                        
                    elif 'financial-ratios' in endpoint:
                        ratios_data = self._extract_financial_ratios(soup)
                        data.update(ratios_data)
                        
                except Exception as e:
                    print(f"   ⚠️ Macrotrends endpoint {endpoint} failed: {str(e)}")
                    continue
            
            return data if data else None
            
        except Exception as e:
            print(f"   ⚠️ Macrotrends scraping failed for {ticker}: {str(e)}")
            return None
            
    def _extract_financial_statements(self, soup):
        """Extract data from financial statements page"""
        data = {}
        
        try:
            # Look for revenue data in various formats
            revenue_patterns = [
                r'revenue.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'total revenue.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'net sales.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
            ]
            
            page_text = soup.get_text()
            
            for pattern in revenue_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    # Convert to number
                    revenue_str = matches[0].replace(',', '')
                    try:
                        revenue = float(revenue_str)
                        data['macrotrends_revenue'] = revenue
                        break
                    except ValueError:
                        continue
            
            # Look for net income
            income_patterns = [
                r'net income.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'net profit.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'net earnings.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
            ]
            
            for pattern in income_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    income_str = matches[0].replace(',', '')
                    try:
                        income = float(income_str)
                        data['macrotrends_net_income'] = income
                        break
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"   ⚠️ Error extracting financial statements: {str(e)}")
            
        return data
        
    def _extract_balance_sheet(self, soup):
        """Extract data from balance sheet page"""
        data = {}
        
        try:
            page_text = soup.get_text()
            
            # Look for total assets
            assets_patterns = [
                r'total assets.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'assets.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
            ]
            
            for pattern in assets_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    assets_str = matches[0].replace(',', '')
                    try:
                        assets = float(assets_str)
                        data['macrotrends_total_assets'] = assets
                        break
                    except ValueError:
                        continue
            
            # Look for total equity
            equity_patterns = [
                r'total equity.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'stockholders equity.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'shareholders equity.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
            ]
            
            for pattern in equity_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    equity_str = matches[0].replace(',', '')
                    try:
                        equity = float(equity_str)
                        data['macrotrends_total_equity'] = equity
                        break
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"   ⚠️ Error extracting balance sheet: {str(e)}")
            
        return data
        
    def _extract_cash_flow(self, soup):
        """Extract data from cash flow statement page"""
        data = {}
        
        try:
            page_text = soup.get_text()
            
            # Look for operating cash flow
            ocf_patterns = [
                r'operating cash flow.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'cash from operations.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'net cash from operating activities.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
            ]
            
            for pattern in ocf_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    ocf_str = matches[0].replace(',', '')
                    try:
                        ocf = float(ocf_str)
                        data['macrotrends_operating_cash_flow'] = ocf
                        break
                    except ValueError:
                        continue
            
            # Look for free cash flow
            fcf_patterns = [
                r'free cash flow.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'fcf.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
            ]
            
            for pattern in fcf_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    fcf_str = matches[0].replace(',', '')
                    try:
                        fcf = float(fcf_str)
                        data['macrotrends_free_cash_flow'] = fcf
                        break
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"   ⚠️ Error extracting cash flow: {str(e)}")
            
        return data
        
    def _extract_financial_ratios(self, soup):
        """Extract data from financial ratios page"""
        data = {}
        
        try:
            page_text = soup.get_text()
            
            # Look for ROE
            roe_patterns = [
                r'roe.*?(\d+\.?\d*)%',
                r'return on equity.*?(\d+\.?\d*)%',
                r'return on equity.*?(\d+\.?\d*)'
            ]
            
            for pattern in roe_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        roe = float(matches[0]) / 100
                        data['macrotrends_roe'] = roe
                        break
                    except ValueError:
                        continue
            
            # Look for ROA
            roa_patterns = [
                r'roa.*?(\d+\.?\d*)%',
                r'return on assets.*?(\d+\.?\d*)%',
                r'return on assets.*?(\d+\.?\d*)'
            ]
            
            for pattern in roa_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        roa = float(matches[0]) / 100
                        data['macrotrends_roa'] = roa
                        break
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"   ⚠️ Error extracting financial ratios: {str(e)}")
            
        return data

def improved_scrape_macrotrends_data(ticker):
    """Improved Macrotrends data scraping"""
    scraper = ImprovedMacrotrendsScraper()
    return scraper.get_company_data(ticker)

if __name__ == "__main__":
    # Test the improved scraper
    test_tickers = ['MSFT', 'AAPL', 'GOOGL', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        data = improved_scrape_macrotrends_data(ticker)
        if data:
            print(f"   ✅ Success: {data}")
        else:
            print(f"   ❌ Failed") 