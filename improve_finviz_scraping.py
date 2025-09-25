#!/usr/bin/env python3
"""
Improved Finviz scraping with better error handling and anti-blocking measures
"""

import requests
import time
import random
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import logging

class ImprovedFinvizScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        self.rate_limit_delay = 2.0  # 2 seconds between requests
        self.max_retries = 3
        self.timeout = 30
        self.proxy_rotation = False  # Set to True if you have proxies
        
    def scrape_with_retry(self, url, retries=None):
        """Scrape with exponential backoff and retry logic"""
        if retries is None:
            retries = self.max_retries
            
        for attempt in range(retries):
            try:
                # Add random delay to avoid rate limiting
                time.sleep(self.rate_limit_delay + random.uniform(0, 1))
                
                # Rotate user agent if needed
                if attempt > 0:
                    self._rotate_user_agent()
                
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
                wait_time = (2 ** attempt) + random.uniform(0, 2)
                print(f"   ⚠️ Finviz request failed, retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                
    def _is_blocked(self, response):
        """Check if we've been blocked"""
        blocked_indicators = [
            'access denied',
            'blocked',
            'captcha',
            'cloudflare',
            'rate limit',
            'too many requests'
        ]
        
        text = response.text.lower()
        return any(indicator in text for indicator in blocked_indicators)
        
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.session.headers['User-Agent'] = random.choice(user_agents)
        
    def get_company_data(self, ticker):
        """Get company data from Finviz with improved error handling"""
        try:
            # Use multiple Finviz endpoints for redundancy
            endpoints = [
                f"https://finviz.com/quote.ashx?t={ticker}",
                f"https://finviz.com/insidertrading.ashx?t={ticker}",
                f"https://finviz.com/news.ashx?t={ticker}"
            ]
            
            data = {}
            
            for endpoint in endpoints:
                try:
                    response = self.scrape_with_retry(endpoint)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract data from quote page
                    if 'quote.ashx' in endpoint:
                        quote_data = self._extract_quote_data(soup)
                        data.update(quote_data)
                        
                    # Extract insider trading data
                    elif 'insidertrading.ashx' in endpoint:
                        insider_data = self._extract_insider_data(soup)
                        data.update(insider_data)
                        
                    # Extract news data
                    elif 'news.ashx' in endpoint:
                        news_data = self._extract_news_data(soup)
                        data.update(news_data)
                        
                except Exception as e:
                    print(f"   ⚠️ Finviz endpoint {endpoint} failed: {str(e)}")
                    continue
            
            return data if data else None
            
        except Exception as e:
            print(f"   ⚠️ Finviz scraping failed for {ticker}: {str(e)}")
            return None
            
    def _extract_quote_data(self, soup):
        """Extract data from quote page"""
        data = {}
        
        try:
            # Find the main quote table
            quote_table = soup.find('table', {'class': 'snapshot-table2'})
            if not quote_table:
                return data
                
            # Extract key metrics
            rows = quote_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # Map common Finviz labels to our data structure
                    if 'Market Cap' in label:
                        data['finviz_market_cap'] = self._parse_market_cap(value)
                    elif 'P/E' in label:
                        data['finviz_pe_ratio'] = self._parse_ratio(value)
                    elif 'Forward P/E' in label:
                        data['finviz_forward_pe'] = self._parse_ratio(value)
                    elif 'PEG' in label:
                        data['finviz_peg'] = self._parse_ratio(value)
                    elif 'Debt/Eq' in label:
                        data['finviz_debt_equity'] = self._parse_ratio(value)
                    elif 'Profit Margin' in label:
                        data['finviz_profit_margin'] = self._parse_percentage(value)
                    elif 'ROE' in label:
                        data['finviz_roe'] = self._parse_percentage(value)
                    elif 'ROA' in label:
                        data['finviz_roa'] = self._parse_percentage(value)
                    elif 'Sales Q/Q' in label:
                        data['finviz_sales_growth'] = self._parse_percentage(value)
                    elif 'EPS (ttm)' in label:
                        data['finviz_eps_ttm'] = self._parse_number(value)
                        
        except Exception as e:
            print(f"   ⚠️ Error extracting quote data: {str(e)}")
            
        return data
        
    def _extract_insider_data(self, soup):
        """Extract insider trading data"""
        data = {}
        
        try:
            # Find insider trading table
            insider_table = soup.find('table', {'class': 'table-light'})
            if insider_table:
                # Count recent insider transactions
                rows = insider_table.find_all('tr')[1:]  # Skip header
                data['finviz_insider_transactions'] = len(rows)
                
        except Exception as e:
            print(f"   ⚠️ Error extracting insider data: {str(e)}")
            
        return data
        
    def _extract_news_data(self, soup):
        """Extract news data"""
        data = {}
        
        try:
            # Find news table
            news_table = soup.find('table', {'class': 'table-light'})
            if news_table:
                # Count recent news items
                rows = news_table.find_all('tr')[1:]  # Skip header
                data['finviz_news_count'] = len(rows)
                
        except Exception as e:
            print(f"   ⚠️ Error extracting news data: {str(e)}")
            
        return data
        
    def _parse_market_cap(self, value):
        """Parse market cap value"""
        try:
            if 'B' in value:
                return float(value.replace('B', '')) * 1e9
            elif 'M' in value:
                return float(value.replace('M', '')) * 1e6
            elif 'K' in value:
                return float(value.replace('K', '')) * 1e3
            else:
                return float(value)
        except:
            return None
            
    def _parse_ratio(self, value):
        """Parse ratio value"""
        try:
            return float(value) if value != '-' else None
        except:
            return None
            
    def _parse_percentage(self, value):
        """Parse percentage value"""
        try:
            if '%' in value:
                return float(value.replace('%', '')) / 100
            else:
                return float(value) / 100
        except:
            return None
            
    def _parse_number(self, value):
        """Parse number value"""
        try:
            return float(value) if value != '-' else None
        except:
            return None

def improved_scrape_finviz_data(ticker):
    """Improved Finviz data scraping"""
    scraper = ImprovedFinvizScraper()
    return scraper.get_company_data(ticker)

if __name__ == "__main__":
    # Test the improved scraper
    test_tickers = ['MSFT', 'AAPL', 'GOOGL', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        data = improved_scrape_finviz_data(ticker)
        if data:
            print(f"   ✅ Success: {data}")
        else:
            print(f"   ❌ Failed") 