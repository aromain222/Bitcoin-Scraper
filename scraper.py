"""
An advanced web scraping tool for extracting information about Bitcoin-related grants and investments.
Uses multiple search strategies and sources to find grant information across the internet.

This module provides functionality to:
- Search Google for Bitcoin grant and investment announcements
- Extract structured data from search results including:
  - Grant/investment amounts
  - Sectors (based on predefined keywords)
  - Companies
  - Dates
  - Funding stages
  - Investors
- Automatically update a Google Spreadsheet with new grants
- Run daily to keep track of new grants

Required environment variables:
- GOOGLE_SEARCH_API_KEY: Google Custom Search API key
- GOOGLE_SEARCH_CX: Custom Search Engine ID
- GOOGLE_SHEETS_CREDENTIALS: Path to Google Sheets credentials JSON file
- GOOGLE_SHEETS_ID: ID of the Google Spreadsheet to update

The scraper uses BeautifulSoup for HTML parsing and includes various heuristics
for extracting semi-structured data from news articles and press releases.
"""

from __future__ import annotations

import argparse
import json
import re
from urllib.parse import quote_plus, urlparse
from datetime import datetime
import os
import time
import logging
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor

import dateparser
import requests
from bs4 import BeautifulSoup, Tag
import feedparser
import trafilatura
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# Constants
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# Expanded search queries
SEARCH_QUERIES = [
    "bitcoin grant awarded",
    "bitcoin foundation grant",
    "crypto grant program",
    "blockchain research grant",
    "bitcoin development grant",
    "cryptocurrency grant announcement",
    "bitcoin fellowship program",
    "blockchain grant recipient",
    "bitcoin funding announcement",
    "crypto project grant"
]

# Extended list of grant sources
GRANT_SOURCES = {
    'BitMEX Research': {
        'url': 'https://blog.bitmex.com/research',
        'type': 'blog'
    },
    'Bitcoin Magazine': {
        'url': 'https://bitcoinmagazine.com/feed',
        'type': 'rss'
    },
    'Kraken Blog': {
        'url': 'https://blog.kraken.com',
        'type': 'blog'
    },
    'Brink': {
        'url': 'https://brink.dev/blog',
        'type': 'blog'
    },
    'Chaincode Labs': {
        'url': 'https://chaincode.com/about',
        'type': 'static'
    },
    'BTCPay Server': {
        'url': 'https://blog.btcpayserver.org',
        'type': 'blog'
    },
    'Blockstream': {
        'url': 'https://blog.blockstream.com',
        'type': 'blog'
    },
    'Bitcoin.org Blog': {
        'url': 'https://bitcoin.org/en/blog',
        'type': 'blog'
    },
    'Open Crypto Foundation': {
        'url': 'https://opencrypto.org/grants',
        'type': 'static'
    },
    'Human Rights Foundation': {
        'url': 'https://hrf.org/devfund',
        'type': 'static'
    },
    'Ethereum Foundation': {  # They sometimes fund Bitcoin projects
        'url': 'https://blog.ethereum.org',
        'type': 'blog'
    },
    'Digital Currency Initiative': {
        'url': 'https://dci.mit.edu/research',
        'type': 'static'
    },
    'Square Crypto': {
        'url': 'https://squarecrypto.org/#grants',
        'type': 'static'
    },
    'Binance': {
        'url': 'https://www.binance.com/en/blog',
        'type': 'blog'
    },
    'Gitcoin Grants': {
        'url': 'https://gitcoin.co/grants/explorer',
        'type': 'dynamic'
    }
}

# Keywords for grant detection
GRANT_KEYWORDS = [
    'grant', 'funding', 'awarded', 'recipient', 'fellowship', 'donation',
    'sponsored', 'backed', 'funded', 'investment', 'initiative', 'program',
    'research grant', 'development fund', 'scholarship'
]

class GrantScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.setup_selenium()
        
    def setup_selenium(self):
        """Set up Selenium WebDriver for dynamic content."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def search_google_custom(self, query: str, max_results: int = 100) -> List[Dict]:
        """Search using Google Custom Search API."""
        try:
            api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
            cx = os.getenv('GOOGLE_SEARCH_CX')
            
            if not api_key or not cx:
                logging.error("Google Search API credentials not found")
                return []
                
            results = []
            for start in range(0, max_results, 10):
                url = (
                    f"https://www.googleapis.com/customsearch/v1?"
                    f"key={api_key}&cx={cx}&q={quote_plus(query)}"
                    f"&start={start + 1}"
                )
                
                response = self.session.get(url)
                data = response.json()
                
                if 'items' not in data:
                    break
                    
                results.extend([
                    {'title': item['title'], 'url': item['link']}
                    for item in data['items']
                ])
                
            return results
            
        except Exception as e:
            logging.error(f"Error in Google Custom Search: {e}")
            return []
            
    def scrape_dynamic_content(self, url: str) -> str:
        """Scrape content from dynamic websites using Selenium."""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Error scraping dynamic content from {url}: {e}")
            return ""
            
    def extract_text_with_trafilatura(self, url: str) -> str:
        """Extract clean text from webpage using trafilatura."""
        try:
            downloaded = trafilatura.fetch_url(url)
            text = trafilatura.extract(downloaded, include_comments=False)
            return text or ""
        except Exception as e:
            logging.error(f"Error extracting text from {url}: {e}")
            return ""
            
    def parse_rss_feed(self, url: str) -> List[Dict]:
        """Parse RSS feed for grant information."""
        try:
            feed = feedparser.parse(url)
            results = []
            
            # Skip if no entries
            if not hasattr(feed, 'entries'):
                return []
            
            for entry in feed.entries:
                title = entry.get('title', '')
                description = entry.get('description', '')
                
                # Handle content field safely
                content = ''
                content_list = entry.get('content', [])
                if content_list and isinstance(content_list, list) and len(content_list) > 0:
                    content = content_list[0].get('value', '')
                    
                link = entry.get('link', '')
                
                if not link:  # Skip entries without links
                    continue
                    
                # Combine all text fields for better keyword matching
                full_text = f"{title} {description} {content}".lower()
                
                # Check for grant-related keywords in the full text
                if any(keyword in full_text for keyword in GRANT_KEYWORDS):
                    # Get the actual article content
                    article_data = self.process_article(str(link))
                    if article_data:
                        results.append(article_data)
                    
            return results
        except Exception as e:
            logging.error(f"Error parsing RSS feed {url}: {e}")
            return []
            
    def search_grant_sources(self, max_results: int = 100) -> List[Dict]:
        """Search known grant sources for information."""
        results = []
        seen_urls = set()
        
        for source_name, source_info in GRANT_SOURCES.items():
            try:
                logging.info(f"Searching source: {source_name}")
                url = source_info['url']
                source_type = source_info['type']
                
                if source_type == 'rss':
                    source_results = self.parse_rss_feed(url)
                elif source_type == 'dynamic':
                    html = self.scrape_dynamic_content(url)
                    soup = BeautifulSoup(html, 'html.parser')
                    source_results = self.extract_grant_info(soup, url)
                else:
                    response = self.session.get(url, allow_redirects=True)
                    final_url = response.url  # Get the final URL after redirects
                    soup = BeautifulSoup(response.text, 'html.parser')
                    source_results = self.extract_grant_info(soup, final_url)
                
                # Process each result and deduplicate
                for result in source_results:
                    result_url = result.get('url', '')
                    if result_url and result_url not in seen_urls:
                        seen_urls.add(result_url)
                        # Try to get full article data
                        article_data = self.process_article(result_url)
                        if article_data:
                            results.append(article_data)
                    
            except Exception as e:
                logging.error(f"Error processing source {source_name}: {e}")
                continue
                
        return results[:max_results]
        
    def extract_grant_info(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """Extract grant information from HTML content."""
        results = []
        base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
        
        # Find all links that might lead to grant announcements
        for link in soup.find_all('a', href=True):
            try:
                # Skip if link is not a Tag
                if not isinstance(link, Tag):
                    continue
                    
                href = str(link.get('href', ''))  # Convert to string
                if not href or href.startswith(('#', 'mailto:', 'tel:')):
                    continue
                    
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = base_url + href
                elif not href.startswith(('http://', 'https://')):
                    href = base_url + '/' + href
                    
                # Basic URL validation
                if not urlparse(href).scheme in ('http', 'https'):
                    continue
                    
                # Check if the link text or surrounding text contains grant keywords
                link_text = link.get_text().lower()
                parent = link.parent
                parent_text = parent.get_text().lower() if isinstance(parent, Tag) else ''
                
                if any(keyword in link_text or keyword in parent_text 
                      for keyword in GRANT_KEYWORDS):
                    results.append({
                        'url': href,
                        'title': link.get_text().strip()
                    })
                    
            except Exception as e:
                logging.error(f"Error processing link in {url}: {e}")
                continue
                
        return results
        
    def process_article(self, url: str) -> Optional[Dict]:
        """Process an article to extract grant information."""
        try:
            # Get clean text content
            text = self.extract_text_with_trafilatura(url)
            if not text:
                return None
                
            # Extract grant information
            data = {
                'url': url,
                'title': None,
                'date': None,
                'amount': None,
                'sector': None,
                'company': None,
                'investors': [],
                'stage': 'grant',
                'description': None,
                'status': 'active'  # Default to active
            }

            # Clean the text
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            text = text.replace('\n', ' ').strip()
            
            # Only process if it looks like a Bitcoin grant announcement
            bitcoin_keywords = ['bitcoin', 'btc', 'lightning', 'satoshi']
            grant_keywords = ['grant', 'awarded', 'funding', 'investment', 'donation', 'fellowship']
            
            if not (any(kw in text.lower() for kw in bitcoin_keywords) and 
                    any(kw in text.lower() for kw in grant_keywords)):
                return None

            # Try to extract title
            title_patterns = [
                r'(?:announces?|awards?|receives?|grants?)\s+\$?\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|BTC)?\s+(?:grant|funding|investment)',
                r'(?:grant|funding|investment)\s+of\s+\$?\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|BTC)?',
                r'[^.!?]*(?:grant|funding|investment)[^.!?]*(?:awarded|announced|received)[^.!?]*'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data['title'] = match.group(0).strip().capitalize()
                    break
                    
            # If no grant-specific title found, use first sentence if it contains keywords
            if not data['title']:
                first_sentence = text.split('.')[0].strip()
                if (any(kw in first_sentence.lower() for kw in bitcoin_keywords) and
                    any(kw in first_sentence.lower() for kw in grant_keywords)):
                    data['title'] = first_sentence
            
            # Find date - expanded patterns
            date_patterns = [
                r'\b\d{1,2}[\s./-]\w{3,9}[\s./-]\d{2,4}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s./-]\d{1,2}(?:st|nd|rd|th)?[\s./-]\d{2,4}\b',
                r'\b\d{4}[\s./-]\d{1,2}[\s./-]\d{1,2}\b',
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parsed_date = dateparser.parse(match.group())
                    if parsed_date:
                        data['date'] = parsed_date
                        break
                
            # Find amount - expanded patterns with BTC support
            amount_patterns = [
                r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*[kKmMbB](?:illion)?)?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|BTC)',
                r'(?:grant|funding|investment)\s+of\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*[kKmMbB](?:illion)?)?)',
                r'(\d+(?:\.\d{1,8})?)\s*(?:₿|BTC|bitcoin)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:sats|satoshis)'
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    multiplier = 1
                    
                    # Handle different units
                    if any(unit in amount_str.lower() for unit in ['k', 'thousand']):
                        multiplier = 1_000
                    elif any(unit in amount_str.lower() for unit in ['m', 'million']):
                        multiplier = 1_000_000
                    elif any(unit in amount_str.lower() for unit in ['b', 'billion']):
                        multiplier = 1_000_000_000
                        
                    # Convert BTC/sats to USD (approximate)
                    if 'btc' in text.lower() or '₿' in text or 'bitcoin' in text.lower():
                        btc_price = 65000  # Approximate BTC price - should be fetched from API
                        multiplier *= btc_price
                    elif 'sats' in text.lower() or 'satoshis' in text.lower():
                        btc_price = 65000  # Approximate BTC price
                        multiplier *= btc_price / 100_000_000  # Convert sats to BTC
                        
                    amount = float(re.sub(r'[kKmMbB].*$', '', amount_str))
                    data['amount'] = amount * multiplier
                    break
                    
            # Find sector - expanded list
            sectors = {
                'development': ['development', 'software', 'programming', 'coding', 'protocol', 'implementation'],
                'research': ['research', 'study', 'investigation', 'analysis', 'academic'],
                'infrastructure': ['infrastructure', 'protocol', 'network', 'scaling', 'node'],
                'education': ['education', 'learning', 'teaching', 'training', 'workshop'],
                'privacy': ['privacy', 'security', 'encryption', 'confidential', 'anonymous'],
                'scaling': ['scaling', 'layer2', 'lightning', 'performance', 'throughput'],
                'tooling': ['tools', 'libraries', 'frameworks', 'sdk', 'api'],
                'community': ['community', 'ecosystem', 'adoption', 'outreach', 'advocacy']
            }
            
            for sector, keywords in sectors.items():
                if any(keyword in text.lower() for keyword in keywords):
                    data['sector'] = sector
                    break
                    
            # Find company/recipient - improved patterns
            company_patterns = [
                r'awarded to\s+([^.!?\n,]+(?:Inc\.|LLC|Ltd\.)?)',
                r'recipient\s+(?:is|was)?\s+([^.!?\n,]+(?:Inc\.|LLC|Ltd\.)?)',
                r'granted to\s+([^.!?\n,]+(?:Inc\.|LLC|Ltd\.)?)',
                r'received by\s+([^.!?\n,]+(?:Inc\.|LLC|Ltd\.)?)',
                r'([^.!?\n,]+(?:Inc\.|LLC|Ltd\.)?)\s+(?:has|have)\s+(?:been\s+)?(?:awarded|received|granted)'
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    # Clean up common suffixes
                    company = re.sub(r'\s+(?:Inc\.|LLC|Ltd\.|Corporation|Corp\.|Limited)$', '', company, flags=re.IGNORECASE)
                    data['company'] = company
                    break
                    
            # Find investors/grantors - improved patterns
            investor_patterns = [
                r'(?:from|by|through)\s+(?:the)?\s*([^.!?\n,]+(?:Foundation|Fund|Initiative|Program))',
                r'funded by\s+(?:the)?\s*([^.!?\n,]+(?:Foundation|Fund|Initiative|Program))',
                r'(?:grant|funding)\s+(?:provided|offered|given)\s+by\s+(?:the)?\s*([^.!?\n,]+(?:Foundation|Fund|Initiative|Program))',
                r'([^.!?\n,]+(?:Foundation|Fund|Initiative|Program))\s+(?:has|have)\s+(?:awarded|granted|provided)'
            ]
            
            for pattern in investor_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    investor = match.group(1).strip()
                    # Clean up and validate investor
                    if (len(investor) > 3 and  # Reasonable length
                        not any(x in investor.lower() for x in ['click', 'link', 'here', 'learn', 'visit']) and  # Not navigation text
                        investor not in data['investors']):  # Not duplicate
                        data['investors'].append(investor)

            # Extract description
            if data['title']:
                # Get the paragraph containing the title
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if data['title'].lower() in para.lower():
                        data['description'] = para.strip()
                        break
                
                # If no paragraph found with title, use first non-empty paragraph
                if not data['description']:
                    for para in paragraphs:
                        if para.strip():
                            data['description'] = para.strip()
                            break

            # Generate a fallback title if none was found
            if not data['title']:
                title_parts = []
                if data['amount']:
                    title_parts.append(f"${data['amount']:,.0f}")
                if data['sector']:
                    title_parts.append(data['sector'].title())
                title_parts.append("Bitcoin Grant")
                if data['company']:
                    title_parts.append(f"to {data['company']}")
                data['title'] = " ".join(title_parts)

            # Only return if we have at least some meaningful data
            if (data['title'] and 
                (data['amount'] or data['company'] or 
                 (data['investors'] and len(data['investors']) > 0))):
                return data
            return None
            
        except Exception as e:
            logging.error(f"Error processing article {url}: {e}")
            return None
            
    def run_search(self, max_results: int = 100) -> List[Dict]:
        """Run comprehensive search for grant information."""
        all_results = []
        
        # Search using multiple queries
        for query in SEARCH_QUERIES:
            results = self.search_google_custom(query, max_results // len(SEARCH_QUERIES))
            all_results.extend(results)
            
        # Search known grant sources
        grant_source_results = self.search_grant_sources(max_results)
        all_results.extend(grant_source_results)
        
        # Process results
        processed_results = []
        seen_urls = set()
        
        for result in all_results:
            if result['url'] in seen_urls:
                continue
                
            try:
                article_data = self.process_article(result['url'])
                if article_data:
                    processed_results.append(article_data)
                    seen_urls.add(result['url'])
            except Exception as e:
                logging.error(f"Error processing result: {e}")
                continue
                
        return processed_results
        
    def close(self):
        """Clean up resources."""
        self.executor.shutdown()
        self.driver.quit()

def get_google_sheets_service():
    """Get Google Sheets service with proper error handling."""
    try:
        # Get credentials file path
        creds_path = os.path.join('credentials', 'google_sheets_credentials.json')
        if not os.path.exists(creds_path):
            raise ValueError(f"Credentials file not found at {creds_path}")

        # Get spreadsheet ID
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        if not spreadsheet_id:
            raise ValueError("Please set GOOGLE_SHEETS_ID environment variable")

        # Set up credentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = ServiceAccountCredentials.from_service_account_file(
            creds_path, scopes=scopes
        )

        # Build service
        service = build('sheets', 'v4', credentials=creds)
        return service, spreadsheet_id

    except Exception as e:
        logging.error(f"Error setting up Google Sheets service: {str(e)}")
        return None, None

def get_existing_grants(service, spreadsheet_id):
    """Get existing grants from the Google Spreadsheet."""
    try:
        # Get values from row 493 onwards
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Grants!A493:G'  # Start from row 493
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return set()
            
        # Get URLs (last column)
        existing_urls = {row[-1] for row in values if len(row) > 0}
        return existing_urls
        
    except Exception as e:
        logging.error(f"Error getting existing grants: {e}")
        return set()

def update_google_sheet(service, spreadsheet_id: str, deals: List[Dict[str, Any]]) -> None:
    """Update Google Spreadsheet with new deals."""
    try:
        # Get existing deals from sheet to avoid duplicates
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Grants!A493:Z'  # Start from row 493 in Grants tab
        ).execute()
        
        existing_deals = result.get('values', [])
        existing_urls = {row[0] for row in existing_deals if row} if existing_deals else set()
        
        # Format new deals for sheet
        new_deals = []
        for deal in deals:
            # Skip if URL already exists
            if deal.get('url') in existing_urls:
                continue
                
            # Format date
            date_str = ''
            if deal.get('date'):
                if isinstance(deal['date'], str):
                    date_str = deal['date']
                else:
                    date_str = deal['date'].strftime('%Y-%m-%d')
                    
            # Format amount
            amount_str = ''
            if deal.get('amount'):
                amount = float(deal['amount'])
                if amount >= 1_000_000:
                    amount_str = f"${amount/1_000_000:.1f}M"
                elif amount >= 1_000:
                    amount_str = f"${amount/1_000:.1f}K"
                else:
                    amount_str = f"${amount:,.0f}"
                    
            # Format investors
            investors_str = ', '.join(deal.get('investors', []))
            
            # Prepare row data
            row = [
                deal.get('url', ''),                    # URL
                deal.get('title', ''),                  # Title
                date_str,                               # Date
                amount_str,                             # Amount
                deal.get('sector', ''),                 # Sector
                deal.get('company', ''),                # Company
                investors_str,                          # Investors
                deal.get('stage', 'grant'),             # Stage
                deal.get('status', 'active'),           # Status
                deal.get('description', '')             # Description
            ]
            
            new_deals.append(row)
            
        if new_deals:
            # Append new deals to sheet
            body = {
                'values': new_deals
            }
            
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Grants!A493',  # Start appending from row 493 in Grants tab
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logging.info(f"Added {len(new_deals)} new grants to spreadsheet")
        else:
            logging.info("No new grants to add to spreadsheet")
            
    except Exception as e:
        logging.error(f"Error updating Google Sheet: {str(e)}")
        raise

def run_daily_update():
    """Run the scraper daily and update the spreadsheet."""
    scraper = GrantScraper()
    
    while True:
        try:
            logging.info(f"Starting grant update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the scraper
            results = scraper.run_search(max_results=100)
            
            # Get Google Sheets service
            service, spreadsheet_id = get_google_sheets_service()
            if service and spreadsheet_id:
                # Update Google Sheet
                update_google_sheet(service, spreadsheet_id, results)
            else:
                logging.error("Failed to set up Google Sheets service")
            
            # Save backup to JSON
            with open('results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
                
            logging.info("Waiting 24 hours before next update...")
            time.sleep(24 * 60 * 60)  # Wait 24 hours
            
        except Exception as e:
            logging.error(f"Error in daily update: {e}")
            logging.info("Retrying in 1 hour...")
            time.sleep(60 * 60)  # Wait 1 hour before retrying

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Advanced Bitcoin grant information scraper')
    parser.add_argument('--output', default='results.json', help='Output JSON file')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum number of results to fetch')
    parser.add_argument('--daemon', action='store_true', help='Run as a daemon and update daily')
    args = parser.parse_args()
    
    if args.daemon:
        run_daily_update()
        return
        
    # One-time run
    scraper = GrantScraper()
    try:
        logging.info("Starting grant search...")
        results = scraper.run_search(args.max_results)
        
        # Get Google Sheets service
        service, spreadsheet_id = get_google_sheets_service()
        if service and spreadsheet_id:
            # Update Google Sheet
            update_google_sheet(service, spreadsheet_id, results)
        else:
            logging.error("Failed to set up Google Sheets service")
        
        # Convert datetime objects to strings before saving to JSON
        json_results = []
        for result in results:
            json_result = result.copy()
            if json_result.get('date'):
                if isinstance(json_result['date'], str):
                    json_result['date'] = json_result['date']
                else:
                    json_result['date'] = json_result['date'].strftime('%Y-%m-%d')
            json_results.append(json_result)
            
        # Save to JSON
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2)
            logging.info(f"Saved grant details to {args.output}")
            
    finally:
        scraper.close()

if __name__ == '__main__':
    main()
