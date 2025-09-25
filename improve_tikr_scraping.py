#!/usr/bin/env python3
"""
Improved Tikr scraping with better error handling and data quality checks
"""

import requests
import time
import random
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import logging

class ImprovedTikrScraper:
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
        self.rate_limit_delay = 4.0  # 4 seconds between requests
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
                print(f"   ⚠️ Tikr request failed, retrying in {wait_time:.1f}s...")
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
            'forbidden',
            'not found'
        ]
        
        text = response.text.lower()
        return any(indicator in text for indicator in blocked_indicators)
        
    def get_company_data(self, ticker):
        """Get company data from Tikr with improved error handling"""
        try:
            # Try multiple Tikr endpoints for redundancy
            endpoints = [
                f"https://tikr.com/{ticker}",
                f"https://tikr.com/{ticker}/financials",
                f"https://tikr.com/{ticker}/ratios",
                f"https://tikr.com/{ticker}/valuation"
            ]
            
            data = {}
            
            for endpoint in endpoints:
                try:
                    response = self.scrape_with_retry(endpoint)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract data based on endpoint type
                    if '/financials' in endpoint:
                        financial_data = self._extract_financials(soup)
                        data.update(financial_data)
                        
                    elif '/ratios' in endpoint:
                        ratios_data = self._extract_ratios(soup)
                        data.update(ratios_data)
                        
                    elif '/valuation' in endpoint:
                        valuation_data = self._extract_valuation(soup)
                        data.update(valuation_data)
                        
                    else:
                        # Main page - try to extract general data
                        general_data = self._extract_general_data(soup)
                        data.update(general_data)
                        
                except Exception as e:
                    print(f"   ⚠️ Tikr endpoint {endpoint} failed: {str(e)}")
                    continue
            
            # Validate data quality
            if data:
                data = self._validate_data_quality(data)
            
            return data if data else None
            
        except Exception as e:
            print(f"   ⚠️ Tikr scraping failed for {ticker}: {str(e)}")
            return None
            
    def _extract_financials(self, soup):
        """Extract financial data from Tikr financials page"""
        data = {}
        
        try:
            # Look for financial tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common Tikr labels to our data structure
                        if 'revenue' in label:
                            data['tikr_revenue'] = self._parse_number(value)
                        elif 'net income' in label:
                            data['tikr_net_income'] = self._parse_number(value)
                        elif 'ebitda' in label:
                            data['tikr_ebitda'] = self._parse_number(value)
                        elif 'total assets' in label:
                            data['tikr_total_assets'] = self._parse_number(value)
                        elif 'total equity' in label:
                            data['tikr_total_equity'] = self._parse_number(value)
                        elif 'operating cash flow' in label:
                            data['tikr_operating_cash_flow'] = self._parse_number(value)
                        elif 'free cash flow' in label:
                            data['tikr_free_cash_flow'] = self._parse_number(value)
                            
        except Exception as e:
            print(f"   ⚠️ Error extracting financials: {str(e)}")
            
        return data
        
    def _extract_ratios(self, soup):
        """Extract ratio data from Tikr ratios page"""
        data = {}
        
        try:
            # Look for ratio tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common Tikr ratio labels
                        if 'roe' in label or 'return on equity' in label:
                            data['tikr_roe'] = self._parse_percentage(value)
                        elif 'roa' in label or 'return on assets' in label:
                            data['tikr_roa'] = self._parse_percentage(value)
                        elif 'roic' in label or 'return on invested capital' in label:
                            data['tikr_roic'] = self._parse_percentage(value)
                        elif 'debt to equity' in label:
                            data['tikr_debt_equity'] = self._parse_ratio(value)
                        elif 'current ratio' in label:
                            data['tikr_current_ratio'] = self._parse_ratio(value)
                        elif 'quick ratio' in label:
                            data['tikr_quick_ratio'] = self._parse_ratio(value)
                            
        except Exception as e:
            print(f"   ⚠️ Error extracting ratios: {str(e)}")
            
        return data
        
    def _extract_valuation(self, soup):
        """Extract valuation data from Tikr valuation page"""
        data = {}
        
        try:
            # Look for valuation tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common Tikr valuation labels
                        if 'pe ratio' in label or 'p/e' in label:
                            data['tikr_pe_ratio'] = self._parse_ratio(value)
                        elif 'ev/ebitda' in label:
                            data['tikr_ev_ebitda'] = self._parse_ratio(value)
                        elif 'ev/revenue' in label:
                            data['tikr_ev_revenue'] = self._parse_ratio(value)
                        elif 'price to book' in label or 'p/b' in label:
                            data['tikr_price_to_book'] = self._parse_ratio(value)
                        elif 'price to sales' in label or 'p/s' in label:
                            data['tikr_price_to_sales'] = self._parse_ratio(value)
                            
        except Exception as e:
            print(f"   ⚠️ Error extracting valuation: {str(e)}")
            
        return data
        
    def _extract_general_data(self, soup):
        """Extract general data from Tikr main page"""
        data = {}
        
        try:
            # Look for key metrics in the page content
            page_text = soup.get_text()
            
            # Use regex patterns to find key metrics
            patterns = {
                'market_cap': r'market cap.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                'revenue': r'revenue.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                'net_income': r'net income.*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                'pe_ratio': r'pe ratio.*?(\d+\.?\d*)',
                'roe': r'roe.*?(\d+\.?\d*)%'
            }
            
            for key, pattern in patterns.items():
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    try:
                        if '%' in pattern:
                            value = float(matches[0]) / 100
                        else:
                            value = float(matches[0].replace(',', ''))
                        data[f'tikr_{key}'] = value
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"   ⚠️ Error extracting general data: {str(e)}")
            
        return data
        
    def _validate_data_quality(self, data):
        """Validate and clean data quality"""
        validated_data = {}
        
        for key, value in data.items():
            if value is not None:
                # Check for reasonable ranges
                if 'revenue' in key and (value < 0 or value > 1e15):  # > $1 quadrillion
                    continue
                elif 'market_cap' in key and (value < 0 or value > 1e15):
                    continue
                elif 'pe_ratio' in key and (value < 0 or value > 1000):
                    continue
                elif 'roe' in key and (value < -1 or value > 10):  # -100% to 1000%
                    continue
                else:
                    validated_data[key] = value
                    
        return validated_data
        
    def _parse_number(self, value):
        """Parse number value from Tikr"""
        try:
            if value == '-' or value == 'N/A':
                return None
                
            # Remove common suffixes
            value = value.replace('$', '').replace(',', '').replace('M', '').replace('B', '').replace('K', '')
            
            # Convert to float
            return float(value)
        except:
            return None
            
    def _parse_percentage(self, value):
        """Parse percentage value from Tikr"""
        try:
            if value == '-' or value == 'N/A':
                return None
                
            # Remove % and convert to decimal
            value = value.replace('%', '').replace(',', '')
            return float(value) / 100
        except:
            return None
            
    def _parse_ratio(self, value):
        """Parse ratio value from Tikr"""
        try:
            if value == '-' or value == 'N/A':
                return None
                
            # Remove common suffixes and convert to float
            value = value.replace(',', '')
            return float(value)
        except:
            return None

def improved_scrape_tikr_data(ticker):
    """Improved Tikr data scraping"""
    scraper = ImprovedTikrScraper()
    return scraper.get_company_data(ticker)

if __name__ == "__main__":
    # Test the improved scraper
    test_tickers = ['MSFT', 'AAPL', 'GOOGL', 'TSLA']
    
    for ticker in test_tickers:
        print(f"\nTesting {ticker}...")
        data = improved_scrape_tikr_data(ticker)
        if data:
            print(f"   ✅ Success: {data}")
        else:
            print(f"   ❌ Failed") 