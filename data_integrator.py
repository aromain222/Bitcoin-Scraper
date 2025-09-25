#!/usr/bin/env python3
"""
Comprehensive Data Integrator for DCF Models
Combines data from multiple sources: Yahoo Finance, Finviz, SEC, MacroTrends, TikR, and web scrapers
"""

import sys
import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import yfinance as yf
import time
import random
from typing import Dict, List, Optional, Any

# Import existing scrapers
from improve_finviz_scraping import improved_scrape_finviz_data
from scraper import GrantScraper

class ComprehensiveDataIntegrator:
    """Integrates data from multiple financial sources for DCF modeling"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Initialize scrapers
        self.finviz_scraper = None
        self.grant_scraper = None

        # Data sources tracking
        self.data_sources = {}

    def collect_comprehensive_data(self, ticker: str, company_name: str = None) -> Dict[str, Any]:
        """
        Collect financial data from all available sources

        Args:
            ticker: Stock ticker symbol
            company_name: Company name (optional)

        Returns:
            Dictionary containing data from all sources
        """
        if not company_name:
            company_name = ticker

        print(f"🔍 Collecting comprehensive data for {company_name} ({ticker})")
        print("=" * 60)

        all_data = {
            'company_info': {
                'ticker': ticker,
                'company_name': company_name,
                'collection_date': datetime.now().isoformat()
            },
            'data_sources': {},
            'integrated_data': {}
        }

        # 1. Yahoo Finance
        print("📊 Collecting Yahoo Finance data...")
        yfinance_data = self._collect_yfinance_data(ticker)
        if yfinance_data:
            all_data['data_sources']['yfinance'] = yfinance_data
            print("   ✅ Yahoo Finance data collected")

        # 2. Finviz
        print("📈 Collecting Finviz data...")
        finviz_data = self._collect_finviz_data(ticker)
        if finviz_data:
            all_data['data_sources']['finviz'] = finviz_data
            print("   ✅ Finviz data collected")

        # 3. MacroTrends (for historical data)
        print("📉 Collecting MacroTrends data...")
        macrotrends_data = self._collect_macrotrends_data(ticker)
        if macrotrends_data:
            all_data['data_sources']['macrotrends'] = macrotrends_data
            print("   ✅ MacroTrends data collected")

        # 4. SEC Filings
        print("📄 Collecting SEC filings data...")
        sec_data = self._collect_sec_data(ticker)
        if sec_data:
            all_data['data_sources']['sec'] = sec_data
            print("   ✅ SEC data collected")

        # 5. TikR (for additional metrics)
        print("🎯 Collecting TikR data...")
        tikr_data = self._collect_tikr_data(ticker)
        if tikr_data:
            all_data['data_sources']['tikr'] = tikr_data
            print("   ✅ TikR data collected")

        # 6. Grant/Investment Data
        print("💰 Collecting grant and investment data...")
        grant_data = self._collect_grant_data(company_name)
        if grant_data:
            all_data['data_sources']['grants'] = grant_data
            print("   ✅ Grant data collected")

        # 7. Integrate data
        print("🔗 Integrating data sources...")
        all_data['integrated_data'] = self._integrate_data(all_data['data_sources'])

        print("=" * 60)
        print(f"✅ Data collection complete for {company_name}")
        print(f"   Sources collected: {len(all_data['data_sources'])}")
        print("=" * 60)

        return all_data

    def _collect_yfinance_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Collect data from Yahoo Finance"""
        try:
            ticker_obj = yf.Ticker(ticker)

            # Get basic info
            info = ticker_obj.info

            # Get financial statements (last 4 years)
            financials = ticker_obj.financials.T.head(4) if not ticker_obj.financials.empty else pd.DataFrame()
            balance_sheet = ticker_obj.balance_sheet.T.head(4) if not ticker_obj.balance_sheet.empty else pd.DataFrame()
            cash_flow = ticker_obj.cashflow.T.head(4) if not ticker_obj.cashflow.empty else pd.DataFrame()

            # Get analyst recommendations
            recommendations = ticker_obj.recommendations if hasattr(ticker_obj, 'recommendations') else pd.DataFrame()

            # Get institutional holders
            institutional_holders = ticker_obj.institutional_holders if hasattr(ticker_obj, 'institutional_holders') else pd.DataFrame()

            return {
                'info': info,
                'financials': financials.to_dict() if not financials.empty else {},
                'balance_sheet': balance_sheet.to_dict() if not balance_sheet.empty else {},
                'cash_flow': cash_flow.to_dict() if not cash_flow.empty else {},
                'recommendations': recommendations.to_dict() if not recommendations.empty else {},
                'institutional_holders': institutional_holders.to_dict() if not institutional_holders.empty else {}
            }

        except Exception as e:
            print(f"   ⚠️ Yahoo Finance error: {e}")
            return None

    def _collect_finviz_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Collect data from Finviz"""
        try:
            return improved_scrape_finviz_data(ticker)
        except Exception as e:
            print(f"   ⚠️ Finviz error: {e}")
            return None

    def _collect_macrotrends_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Collect historical data from MacroTrends"""
        try:
            # Revenue data
            revenue_url = f"https://www.macrotrends.net/stocks/charts/{ticker}/revenue"
            response = self.session.get(revenue_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to extract revenue table
            tables = soup.find_all('table')
            revenue_data = {}

            for table in tables:
                if 'revenue' in table.get_text().lower():
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            year = cols[0].get_text().strip()
                            revenue = cols[1].get_text().strip().replace('$', '').replace(',', '')
                            try:
                                revenue_data[year] = float(revenue) * 1e6  # Convert to millions
                            except ValueError:
                                continue

            return {'historical_revenue': revenue_data} if revenue_data else None

        except Exception as e:
            print(f"   ⚠️ MacroTrends error: {e}")
            return None

    def _collect_sec_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Collect data from SEC filings"""
        try:
            # Get company CIK
            cik_url = f"https://www.sec.gov/include/ticker.txt"
            response = self.session.get(cik_url)
            cik_data = {}

            for line in response.text.split('\n'):
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        cik_data[parts[0].upper()] = parts[1]

            cik = cik_data.get(ticker.upper())
            if not cik:
                return None

            # Get recent filings
            filings_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=&owner=exclude&count=10"
            response = self.session.get(filings_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract filing links
            filings = []
            table = soup.find('table', {'class': 'tableFile2'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        filing = {
                            'date': cols[3].get_text().strip(),
                            'type': cols[0].get_text().strip(),
                            'description': cols[2].get_text().strip(),
                            'link': urljoin('https://www.sec.gov', cols[1].find('a')['href']) if cols[1].find('a') else None
                        }
                        filings.append(filing)

            return {'cik': cik, 'filings': filings[:5]}  # Return last 5 filings

        except Exception as e:
            print(f"   ⚠️ SEC error: {e}")
            return None

    def _collect_tikr_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Collect additional metrics from TikR"""
        try:
            # This would integrate with TikR scraping
            # For now, return placeholder structure
            return {
                'additional_metrics': {
                    'momentum_score': None,
                    'quality_score': None,
                    'value_score': None
                }
            }
        except Exception as e:
            print(f"   ⚠️ TikR error: {e}")
            return None

    def _collect_grant_data(self, company_name: str) -> Optional[List[Dict[str, Any]]]:
        """Collect grant and investment data"""
        try:
            if self.grant_scraper is None:
                self.grant_scraper = GrantScraper()

            # Search for company-specific grants
            grants = self.grant_scraper.run_search(max_results=20)

            # Filter for relevant grants
            relevant_grants = []
            company_keywords = company_name.lower().split()

            for grant in grants:
                grant_text = f"{grant.get('title', '')} {grant.get('description', '')} {grant.get('company', '')}".lower()

                if any(keyword in grant_text for keyword in company_keywords):
                    relevant_grants.append(grant)

            return relevant_grants[:10] if relevant_grants else None

        except Exception as e:
            print(f"   ⚠️ Grant data error: {e}")
            return None

    def _integrate_data(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate data from multiple sources into a unified format"""
        integrated = {
            'company_info': {},
            'financial_statements': {},
            'valuation_metrics': {},
            'risk_factors': {},
            'growth_drivers': {}
        }

        # 1. Company Info Integration
        if 'yfinance' in data_sources:
            info = data_sources['yfinance'].get('info', {})
            integrated['company_info'] = {
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'total_debt': info.get('totalDebt', 0),
                'cash': info.get('cash', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'beta': info.get('beta', 1.0),
                'dividend_yield': info.get('dividendYield', 0),
                'pe_ratio': info.get('trailingPE', None),
                'pb_ratio': info.get('priceToBook', None)
            }

        # 2. Financial Statements Integration
        if 'yfinance' in data_sources:
            yfinance_data = data_sources['yfinance']

            # Income Statement
            if 'financials' in yfinance_data and yfinance_data['financials']:
                integrated['financial_statements']['income_statement'] = self._clean_financial_data(yfinance_data['financials'])

            # Balance Sheet
            if 'balance_sheet' in yfinance_data and yfinance_data['balance_sheet']:
                integrated['financial_statements']['balance_sheet'] = self._clean_financial_data(yfinance_data['balance_sheet'])

            # Cash Flow
            if 'cash_flow' in yfinance_data and yfinance_data['cash_flow']:
                integrated['financial_statements']['cash_flow'] = self._clean_financial_data(yfinance_data['cash_flow'])

        # 3. Valuation Metrics Integration
        valuation_metrics = {}

        # From Yahoo Finance
        if 'yfinance' in data_sources:
            info = data_sources['yfinance'].get('info', {})
            valuation_metrics.update({
                'yfinance_pe_ratio': info.get('trailingPE'),
                'yfinance_forward_pe': info.get('forwardPE'),
                'yfinance_peg': info.get('pegRatio'),
                'yfinance_pb_ratio': info.get('priceToBook'),
                'yfinance_ev_ebitda': info.get('enterpriseToEbitda'),
                'yfinance_ev_revenue': info.get('enterpriseToRevenue')
            })

        # From Finviz
        if 'finviz' in data_sources:
            finviz_data = data_sources['finviz']
            valuation_metrics.update({
                'finviz_market_cap': finviz_data.get('finviz_market_cap'),
                'finviz_pe_ratio': finviz_data.get('finviz_pe_ratio'),
                'finviz_forward_pe': finviz_data.get('finviz_forward_pe'),
                'finviz_peg': finviz_data.get('finviz_peg'),
                'finviz_debt_equity': finviz_data.get('finviz_debt_equity'),
                'finviz_profit_margin': finviz_data.get('finviz_profit_margin'),
                'finviz_roe': finviz_data.get('finviz_roe'),
                'finviz_roa': finviz_data.get('finviz_roa')
            })

        integrated['valuation_metrics'] = valuation_metrics

        # 4. Risk Factors Integration
        risk_factors = {}

        # Beta and volatility from multiple sources
        beta_sources = []
        if 'yfinance' in data_sources:
            beta = data_sources['yfinance'].get('info', {}).get('beta')
            if beta:
                beta_sources.append({'source': 'yfinance', 'beta': beta})

        if beta_sources:
            risk_factors['beta'] = beta_sources

        # Debt ratios
        if integrated['company_info'].get('market_cap') and integrated['company_info'].get('total_debt'):
            market_cap = integrated['company_info']['market_cap']
            total_debt = integrated['company_info']['total_debt']
            risk_factors['debt_to_equity'] = total_debt / (market_cap + total_debt) if (market_cap + total_debt) > 0 else None

        integrated['risk_factors'] = risk_factors

        # 5. Growth Drivers Integration
        growth_drivers = {}

        # Historical revenue growth
        if 'macrotrends' in data_sources and 'historical_revenue' in data_sources['macrotrends']:
            revenue_data = data_sources['macrotrends']['historical_revenue']
            if len(revenue_data) >= 2:
                years = sorted(revenue_data.keys())
                recent_years = years[-3:] if len(years) >= 3 else years

                growth_rates = []
                for i in range(1, len(recent_years)):
                    current = revenue_data[recent_years[i]]
                    previous = revenue_data[recent_years[i-1]]
                    if previous > 0:
                        growth = (current - previous) / previous
                        growth_rates.append(growth)

                if growth_rates:
                    growth_drivers['historical_revenue_cagr'] = sum(growth_rates) / len(growth_rates)

        # Recent grants and investments
        if 'grants' in data_sources and data_sources['grants']:
            growth_drivers['recent_grants'] = data_sources['grants'][:5]  # Top 5 recent grants

        integrated['growth_drivers'] = growth_drivers

        return integrated

    def _clean_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize financial data"""
        cleaned = {}

        for key, value in data.items():
            if isinstance(value, dict):
                # Convert nested dict values
                cleaned_values = {}
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)) and not pd.isna(sub_value):
                        cleaned_values[sub_key] = float(sub_value)
                    else:
                        cleaned_values[sub_key] = sub_value
                cleaned[key] = cleaned_values
            elif isinstance(value, (int, float)) and not pd.isna(value):
                cleaned[key] = float(value)
            else:
                cleaned[key] = value

        return cleaned

    def export_integrated_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """Export integrated data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ticker = data['company_info'].get('ticker', 'unknown')
            filename = f"integrated_data_{ticker}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"💾 Integrated data exported to {filename}")
        return filename

def main():
    """Main function for testing the data integrator"""
    integrator = ComprehensiveDataIntegrator()

    # Test with a few companies
    test_companies = [
        {'ticker': 'MSFT', 'name': 'Microsoft Corporation'},
        {'ticker': 'AAPL', 'name': 'Apple Inc.'},
        {'ticker': 'GOOGL', 'name': 'Alphabet Inc.'}
    ]

    for company in test_companies:
        print(f"\n{'='*80}")
        data = integrator.collect_comprehensive_data(company['ticker'], company['name'])

        # Export data
        filename = integrator.export_integrated_data(data)
        print(f"📁 Data saved to: {filename}")

if __name__ == "__main__":
    main()
