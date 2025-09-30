#!/usr/bin/env python3
"""
Minimal FinModAI app for testing
"""

from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify, send_file
import json
import uuid
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import io
import os
import re
import threading
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Create Flask app
app = Flask(__name__)
app.secret_key = 'finmodai_secret_key_2024'

# Simple storage for models
MODEL_STORAGE = {}

# Session Management System
class ClimateType(str, Enum):
    BASE = "base"
    BULL = "bull"
    BEAR = "bear"
    ESG = "esg"

class ModelType(str, Enum):
    THREE_STATEMENT = "three_statement"
    DCF = "dcf"
    LBO = "lbo"
    MERGER = "merger"
    COMPS = "comps"

@dataclass
class AssumptionProfile:
    growth_pct: float
    ebitda_margin_pct: float
    tax_rate_pct: float
    capex_pct: float
    nwc_pct: float

@dataclass
class SessionData:
    session_id: str
    climate: str
    ticker: str
    model: str
    assumptions: Dict[str, float]
    created_at: datetime
    expires_at: datetime
    ready: bool = True

class SessionManager:
    def __init__(self, ttl_hours: int = 2):
        self.sessions: Dict[str, SessionData] = {}
        self.ttl_hours = ttl_hours
        self.lock = threading.Lock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def create_session(self, climate: str, ticker: str, model: str) -> SessionData:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        expires_at = now + timedelta(hours=self.ttl_hours)
        
        # Get assumption profile based on climate
        assumptions = self._get_assumption_profile(climate)
        
        session_data = SessionData(
            session_id=session_id,
            climate=climate,
            ticker=ticker.upper(),
            model=model,
            assumptions=asdict(assumptions),
            created_at=now,
            expires_at=expires_at
        )
        
        with self.lock:
            self.sessions[session_id] = session_data
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        with self.lock:
            session = self.sessions.get(session_id)
            if session and datetime.now() < session.expires_at:
                return session
            elif session:
                # Session expired, remove it
                del self.sessions[session_id]
        return None
    
    def update_assumptions(self, session_id: str, new_assumptions: Dict[str, float]) -> Optional[SessionData]:
        with self.lock:
            session = self.sessions.get(session_id)
            if session and datetime.now() < session.expires_at:
                session.assumptions.update(new_assumptions)
                return session
        return None
    
    def _get_assumption_profile(self, climate: str) -> AssumptionProfile:
        """Get assumption profile based on climate scenario"""
        base_profile = AssumptionProfile(
            growth_pct=0.06,
            ebitda_margin_pct=0.25,
            tax_rate_pct=0.21,
            capex_pct=0.04,
            nwc_pct=0.10
        )
        
        if climate == ClimateType.BULL:
            return AssumptionProfile(
                growth_pct=base_profile.growth_pct + 0.02,  # +200 bps
                ebitda_margin_pct=base_profile.ebitda_margin_pct + 0.03,  # +300 bps
                tax_rate_pct=base_profile.tax_rate_pct,
                capex_pct=base_profile.capex_pct,
                nwc_pct=base_profile.nwc_pct
            )
        elif climate == ClimateType.BEAR:
            return AssumptionProfile(
                growth_pct=max(0.01, base_profile.growth_pct - 0.03),  # -300 bps, min 1%
                ebitda_margin_pct=max(0.05, base_profile.ebitda_margin_pct - 0.02),  # -200 bps, min 5%
                tax_rate_pct=base_profile.tax_rate_pct,
                capex_pct=base_profile.capex_pct,
                nwc_pct=base_profile.nwc_pct
            )
        elif climate == ClimateType.ESG:
            return AssumptionProfile(
                growth_pct=base_profile.growth_pct,  # Same growth
                ebitda_margin_pct=base_profile.ebitda_margin_pct - 0.01,  # -100 bps
                tax_rate_pct=base_profile.tax_rate_pct,
                capex_pct=base_profile.capex_pct + 0.01,  # +100 bps
                nwc_pct=base_profile.nwc_pct
            )
        else:  # BASE
            return base_profile
    
    def _cleanup_expired_sessions(self):
        """Background thread to clean up expired sessions"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                now = datetime.now()
                expired_sessions = []
                
                with self.lock:
                    for session_id, session in self.sessions.items():
                        if now >= session.expires_at:
                            expired_sessions.append(session_id)
                    
                    for session_id in expired_sessions:
                        del self.sessions[session_id]
                        print(f"Cleaned up expired session: {session_id}")
                        
            except Exception as e:
                print(f"Error in session cleanup: {e}")

# Initialize session manager
session_manager = SessionManager()

def validate_ticker(ticker: str) -> tuple[bool, str]:
    """Validate ticker format"""
    if not ticker:
        return False, "Ticker is required"
    
    if len(ticker) < 1 or len(ticker) > 15:
        return False, "Ticker must be 1-15 characters"
    
    # Allow A-Z, 0-9, dots, and dashes, must start with letter
    pattern = r'^[A-Z][A-Z0-9\.\-]{0,14}$'
    if not re.match(pattern, ticker.upper()):
        return False, "Ticker must be 1-15 alphanumerics/.-"
    
    return True, ""

def lookup_ticker_exists(ticker: str) -> tuple[bool, Optional[str]]:
    """Stub function to check if ticker exists - returns (exists, warning)"""
    try:
        # Quick check using yfinance
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # If we get basic info, ticker likely exists
        if info and info.get('symbol') or info.get('shortName'):
            return True, None
        else:
            return True, f"Could not verify ticker {ticker} - proceeding anyway"
            
    except Exception:
        return True, f"Ticker verification offline - proceeding with {ticker}"

def validate_session_request(data: dict) -> tuple[bool, dict]:
    """Validate session start request"""
    errors = {}
    
    # Validate climate
    climate = data.get('climate', '').lower()
    if climate not in [e.value for e in ClimateType]:
        errors['climate'] = f"Climate must be one of: {[e.value for e in ClimateType]}"
    
    # Validate model
    model = data.get('model', '').lower()
    if model not in [e.value for e in ModelType]:
        errors['model'] = f"Model must be one of: {[e.value for e in ModelType]}"
    
    # Validate ticker
    ticker = data.get('ticker', '').strip().upper()
    if ticker:
        is_valid, error_msg = validate_ticker(ticker)
        if not is_valid:
            errors['ticker'] = error_msg
    else:
        errors['ticker'] = "Ticker is required"
    
    return len(errors) == 0, errors

class FinancialDataEngine:
    """Multi-source financial data engine using yfinance and Google Finance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_company_data(self, ticker):
        """Fetch comprehensive company data with robust error handling"""
        try:
            # Check cache first (5 minute expiry)
            cache_key = f"{ticker}_data"
            if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                print(f"📋 Using cached data for {ticker}")
                return self.cache[cache_key]
            
            print(f"🔍 Fetching fresh data for {ticker}")
            stock = yf.Ticker(ticker)
            
            # Get basic info with error handling
            try:
                info = stock.info
                if not info or len(info) < 5:  # Very basic check
                    print(f"⚠️ Limited info data for {ticker}, but continuing...")
                    info = {}
            except Exception as e:
                print(f"⚠️ Info fetch failed for {ticker}: {e}, using defaults")
                info = {}
            
            # Get current stock data with fallbacks
            current_price = None
            try:
                hist = stock.history(period="1y")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                else:
                    # Fallback to shorter period
                    hist = stock.history(period="1mo")
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
            except Exception as e:
                print(f"⚠️ Price history failed for {ticker}: {e}")
                # Try to get current price from info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            # Get financial statements with error handling
            financials = pd.DataFrame()
            balance_sheet = pd.DataFrame()
            cash_flow = pd.DataFrame()
            
            try:
                financials = stock.financials
            except Exception as e:
                print(f"⚠️ Financials fetch failed for {ticker}: {e}")
            
            try:
                balance_sheet = stock.balance_sheet
            except Exception as e:
                print(f"⚠️ Balance sheet fetch failed for {ticker}: {e}")
            
            try:
                cash_flow = stock.cashflow
            except Exception as e:
                print(f"⚠️ Cash flow fetch failed for {ticker}: {e}")
            
            # Calculate key metrics
            data = {
                'ticker': ticker,
                'company_name': info.get('longName', f"{ticker} Corporation"),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'current_price': current_price,
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'beta': info.get('beta', 1.0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'return_on_assets': info.get('returnOnAssets', 0),
                'profit_margin': info.get('profitMargins', 0),
                'operating_margin': info.get('operatingMargins', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'free_cash_flow': info.get('freeCashflow', 0),
                'total_cash': info.get('totalCash', 0),
                'total_debt': info.get('totalDebt', 0),
                'book_value': info.get('bookValue', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'payout_ratio': info.get('payoutRatio', 0)
            }
            
            # Add historical financial data if available
            if not financials.empty:
                latest_financials = financials.iloc[:, 0]  # Most recent year
                data.update({
                    'revenue': float(latest_financials.get('Total Revenue', 0)) if pd.notna(latest_financials.get('Total Revenue')) else 0,
                    'gross_profit': float(latest_financials.get('Gross Profit', 0)) if pd.notna(latest_financials.get('Gross Profit')) else 0,
                    'operating_income': float(latest_financials.get('Operating Income', 0)) if pd.notna(latest_financials.get('Operating Income')) else 0,
                    'net_income': float(latest_financials.get('Net Income', 0)) if pd.notna(latest_financials.get('Net Income')) else 0,
                    'ebitda': float(latest_financials.get('EBITDA', 0)) if pd.notna(latest_financials.get('EBITDA')) else 0,
                })
            
            # Enhance with Google Finance data
            google_data = self.get_google_finance_data(ticker)
            if google_data:
                print(f"🔗 Merging Google Finance data for {ticker}")
                # Use Google Finance data to fill gaps or override yfinance data
                if google_data.get('company_name') and (not data.get('company_name') or data['company_name'] == f"{ticker} Corporation"):
                    data['company_name'] = google_data['company_name']
                
                if google_data.get('current_price') and not data.get('current_price'):
                    data['current_price'] = google_data['current_price']
                
                if google_data.get('market_cap') and not data.get('market_cap'):
                    data['market_cap'] = google_data['market_cap']
                
                if google_data.get('pe_ratio') and not data.get('pe_ratio'):
                    data['pe_ratio'] = google_data['pe_ratio']
                
                # Add Google-specific data
                if google_data.get('52_week_low'):
                    data['52_week_low'] = google_data['52_week_low']
                if google_data.get('52_week_high'):
                    data['52_week_high'] = google_data['52_week_high']
                
                # Add data source info
                data['data_sources'] = ['yfinance', 'google_finance']
            else:
                data['data_sources'] = ['yfinance']
            
            # Validate we have at least basic data
            if not data.get('company_name') or data['company_name'] == f"{ticker} Corporation":
                # Try to get a better company name
                if current_price:  # If we have a price, it's likely a valid ticker
                    data['company_name'] = f"{ticker} Inc."
                else:
                    print(f"⚠️ Minimal data available for {ticker}")
            
            # Cache the result
            self.cache[cache_key] = data
            self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
            
            sources_str = " + ".join(data.get('data_sources', ['unknown']))
            print(f"✅ Successfully fetched data for {ticker} ({data['company_name']}) from {sources_str}")
            return data
            
        except Exception as e:
            print(f"❌ Complete failure fetching data for {ticker}: {e}")
            # Return fallback data instead of None
            fallback_data = {
                'ticker': ticker,
                'company_name': f"{ticker} Corporation",
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 10000000000,  # $10B default
                'enterprise_value': 10000000000,
                'current_price': 100.0,  # $100 default
                'shares_outstanding': 100000000,  # 100M shares
                'beta': 1.2,
                'pe_ratio': 20,
                'forward_pe': 18,
                'peg_ratio': 1.5,
                'price_to_book': 3.0,
                'debt_to_equity': 0.3,
                'return_on_equity': 0.15,
                'return_on_assets': 0.08,
                'profit_margin': 0.12,
                'operating_margin': 0.18,
                'revenue_growth': 0.08,
                'earnings_growth': 0.10,
                'free_cash_flow': 1000000000,  # $1B
                'total_cash': 5000000000,  # $5B
                'total_debt': 3000000000,  # $3B
                'book_value': 30.0,
                'dividend_yield': 0.02,
                'payout_ratio': 0.3,
                'revenue': 20000000000,  # $20B
                'gross_profit': 8000000000,  # $8B
                'operating_income': 3600000000,  # $3.6B
                'net_income': 2400000000,  # $2.4B
                'ebitda': 4000000000,  # $4B
            }
            print(f"🔄 Using fallback data for {ticker}")
            return fallback_data
    
    def get_google_finance_data(self, ticker):
        """Fetch additional data from Google Finance"""
        try:
            print(f"🔍 Fetching Google Finance data for {ticker}")
            
            # Google Finance search URL
            search_url = f"https://www.google.com/finance/quote/{ticker}:NASDAQ"
            
            # Try different exchanges if NASDAQ doesn't work
            exchanges = ['NASDAQ', 'NYSE', 'NYSEARCA']
            google_data = {}
            
            for exchange in exchanges:
                try:
                    url = f"https://www.google.com/finance/quote/{ticker}:{exchange}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract company name
                        company_name_elem = soup.find('div', {'class': 'zzDege'})
                        if company_name_elem:
                            google_data['company_name'] = company_name_elem.text.strip()
                        
                        # Extract current price
                        price_elem = soup.find('div', {'class': 'YMlKec fxKbKc'})
                        if price_elem:
                            price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                            try:
                                google_data['current_price'] = float(price_text)
                            except ValueError:
                                pass
                        
                        # Extract market cap
                        stats_divs = soup.find_all('div', {'class': 'P6K39c'})
                        for div in stats_divs:
                            text = div.get_text()
                            if 'Market cap' in text:
                                # Extract market cap value
                                cap_match = re.search(r'Market cap\s*([0-9,.]+[KMBT]?)', text)
                                if cap_match:
                                    cap_str = cap_match.group(1)
                                    google_data['market_cap_str'] = cap_str
                                    # Convert to number
                                    google_data['market_cap'] = self._parse_financial_number(cap_str)
                            elif 'P/E ratio' in text:
                                pe_match = re.search(r'P/E ratio\s*([0-9,.]+)', text)
                                if pe_match:
                                    try:
                                        google_data['pe_ratio'] = float(pe_match.group(1))
                                    except ValueError:
                                        pass
                        
                        # Extract 52-week range
                        range_elem = soup.find('div', string=re.compile('52-week'))
                        if range_elem:
                            range_text = range_elem.find_next().text if range_elem.find_next() else ""
                            range_match = re.search(r'([0-9,.]+)\s*-\s*([0-9,.]+)', range_text)
                            if range_match:
                                try:
                                    google_data['52_week_low'] = float(range_match.group(1).replace(',', ''))
                                    google_data['52_week_high'] = float(range_match.group(2).replace(',', ''))
                                except ValueError:
                                    pass
                        
                        if google_data:  # If we got some data, break
                            print(f"✅ Google Finance data found for {ticker} on {exchange}")
                            break
                            
                except Exception as e:
                    print(f"⚠️ Google Finance error for {ticker} on {exchange}: {e}")
                    continue
            
            return google_data if google_data else None
            
        except Exception as e:
            print(f"❌ Google Finance complete failure for {ticker}: {e}")
            return None
    
    def _parse_financial_number(self, num_str):
        """Parse financial numbers like '1.5T', '500B', '10M' to actual numbers"""
        try:
            num_str = num_str.replace(',', '').strip()
            
            if num_str.endswith('T'):
                return float(num_str[:-1]) * 1e12
            elif num_str.endswith('B'):
                return float(num_str[:-1]) * 1e9
            elif num_str.endswith('M'):
                return float(num_str[:-1]) * 1e6
            elif num_str.endswith('K'):
                return float(num_str[:-1]) * 1e3
            else:
                return float(num_str)
        except (ValueError, IndexError):
            return 0
    
    def calculate_dcf_scenarios(self, ticker, base_assumptions=None):
        """Calculate DCF with bull/bear/base scenarios"""
        company_data = self.get_company_data(ticker)
        if not company_data:
            return None
        
        # Base case assumptions (can be overridden)
        if base_assumptions is None:
            base_assumptions = {
                'revenue_growth_1': max(company_data.get('revenue_growth', 0.1), 0.05),
                'revenue_growth_2': max(company_data.get('revenue_growth', 0.08) * 0.8, 0.03),
                'revenue_growth_3': max(company_data.get('revenue_growth', 0.06) * 0.6, 0.025),
                'revenue_growth_4': 0.025,
                'revenue_growth_5': 0.025,
                'operating_margin': max(company_data.get('operating_margin', 0.15), 0.1),
                'tax_rate': 0.25,
                'capex_percent': 0.03,
                'nwc_percent': 0.02,
                'terminal_growth': 0.025,
                'wacc': max(0.08, 0.05 + (company_data.get('beta', 1.0) * 0.06))
            }
        
        scenarios = {}
        
        # Base Case
        scenarios['base'] = self._calculate_dcf_valuation(company_data, base_assumptions)
        
        # Bull Case (more optimistic)
        bull_assumptions = base_assumptions.copy()
        bull_assumptions.update({
            'revenue_growth_1': base_assumptions['revenue_growth_1'] * 1.5,
            'revenue_growth_2': base_assumptions['revenue_growth_2'] * 1.4,
            'revenue_growth_3': base_assumptions['revenue_growth_3'] * 1.3,
            'operating_margin': min(base_assumptions['operating_margin'] * 1.2, 0.35),
            'terminal_growth': 0.035,
            'wacc': max(base_assumptions['wacc'] - 0.01, 0.06)
        })
        scenarios['bull'] = self._calculate_dcf_valuation(company_data, bull_assumptions)
        
        # Bear Case (more conservative)
        bear_assumptions = base_assumptions.copy()
        bear_assumptions.update({
            'revenue_growth_1': base_assumptions['revenue_growth_1'] * 0.5,
            'revenue_growth_2': base_assumptions['revenue_growth_2'] * 0.6,
            'revenue_growth_3': base_assumptions['revenue_growth_3'] * 0.7,
            'operating_margin': base_assumptions['operating_margin'] * 0.8,
            'terminal_growth': 0.015,
            'wacc': base_assumptions['wacc'] + 0.015
        })
        scenarios['bear'] = self._calculate_dcf_valuation(company_data, bear_assumptions)
        
        return {
            'company_data': company_data,
            'scenarios': scenarios,
            'assumptions': {
                'base': base_assumptions,
                'bull': bull_assumptions,
                'bear': bear_assumptions
            }
        }
    
    def _calculate_dcf_valuation(self, company_data, assumptions):
        """Calculate DCF valuation with given assumptions"""
        try:
            # Starting revenue (use actual if available, otherwise estimate from market cap)
            revenue = company_data.get('revenue', 0)
            print(f"🔍 Initial revenue from company_data: ${revenue:,.0f}")
            
            if revenue == 0 and company_data.get('market_cap', 0) > 0:
                # Estimate revenue from market cap using industry average P/S ratio
                revenue = company_data['market_cap'] / 3  # Assume 3x P/S ratio
                print(f"🔍 Estimated revenue from market cap: ${revenue:,.0f}")
            
            if revenue == 0:
                revenue = 1000000000  # Default $1B if no data
                print(f"🔍 Using default revenue: ${revenue:,.0f}")
            else:
                print(f"🔍 Final revenue for DCF: ${revenue:,.0f}")
            
            # Project 5 years of cash flows
            years = 5
            cash_flows = []
            
            for year in range(1, years + 1):
                growth_rate = assumptions.get(f'revenue_growth_{year}', 0.05)
                year_revenue = revenue * ((1 + growth_rate) ** year)
                
                operating_income = year_revenue * assumptions['operating_margin']
                tax = operating_income * assumptions['tax_rate']
                nopat = operating_income - tax
                
                capex = year_revenue * assumptions['capex_percent']
                nwc_change = year_revenue * assumptions['nwc_percent'] * growth_rate
                
                fcf = nopat - capex - nwc_change
                cash_flows.append(fcf)
            
            # Terminal value
            terminal_fcf = cash_flows[-1] * (1 + assumptions['terminal_growth'])
            terminal_value = terminal_fcf / (assumptions['wacc'] - assumptions['terminal_growth'])
            
            # Present value calculations
            pv_cash_flows = []
            for i, cf in enumerate(cash_flows, 1):
                pv = cf / ((1 + assumptions['wacc']) ** i)
                pv_cash_flows.append(pv)
            
            pv_terminal = terminal_value / ((1 + assumptions['wacc']) ** years)
            
            # Enterprise value
            enterprise_value = sum(pv_cash_flows) + pv_terminal
            print(f"🔍 DCF Calculation Details:")
            print(f"   Sum of PV Cash Flows: ${sum(pv_cash_flows):,.0f}")
            print(f"   PV Terminal Value: ${pv_terminal:,.0f}")
            print(f"   Enterprise Value: ${enterprise_value:,.0f}")
            
            # Equity value (subtract net debt)
            net_debt = company_data.get('total_debt', 0) - company_data.get('total_cash', 0)
            equity_value = enterprise_value - net_debt
            print(f"   Net Debt: ${net_debt:,.0f}")
            print(f"   Equity Value: ${equity_value:,.0f}")
            
            # Per share value
            shares = company_data.get('shares_outstanding', 0) or 0
            if shares == 0:
                market_cap = company_data.get('market_cap', 0) or 0
                current_price = company_data.get('current_price', 100) or 100
                shares = market_cap / max(current_price, 1) if market_cap > 0 else 1000000  # Default 1M shares
            
            shares = max(shares, 1)  # Ensure shares is at least 1
            implied_price = equity_value / shares if shares > 0 else 0
            print(f"   Shares Outstanding: {shares:,.0f}")
            print(f"   Implied Price: ${implied_price:.2f}")
            
            return {
                'enterprise_value': float(enterprise_value),
                'equity_value': float(equity_value),
                'implied_price': float(implied_price),
                'current_price': float(company_data.get('current_price', 0)),
                'upside_downside': float((implied_price - (company_data.get('current_price') or 0)) / max((company_data.get('current_price') or 1), 1) * 100) if (company_data.get('current_price') or 0) > 0 else 0,
                'cash_flows': [float(cf) for cf in cash_flows],
                'pv_cash_flows': [float(pv) for pv in pv_cash_flows],
                'terminal_value': float(terminal_value),
                'pv_terminal': float(pv_terminal)
            }
            
        except Exception as e:
            print(f"Error in DCF calculation: {e}")
            return None

# Initialize the financial data engine
financial_engine = FinancialDataEngine()

class ExcelModelGenerator:
    """Generate professional Excel financial models"""
    
    def __init__(self):
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        self.number_font = Font(name="Calibri", size=11)
        self.currency_format = '"$"#,##0.0_);[Red]("$"#,##0.0)'
        self.percent_format = '0.0%'
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    def generate_dcf_model(self, model_data):
        """Generate a professional DCF Excel model"""
        wb = openpyxl.Workbook()
        
        # Remove default sheet and create our sheets
        wb.remove(wb.active)
        
        # Create sheets
        summary_ws = wb.create_sheet("Executive Summary")
        dcf_ws = wb.create_sheet("DCF Model")
        assumptions_ws = wb.create_sheet("Assumptions")
        
        # Generate each sheet
        self._create_summary_sheet(summary_ws, model_data)
        self._create_dcf_sheet(dcf_ws, model_data)
        self._create_assumptions_sheet(assumptions_ws, model_data)
        
        return wb
    
    def _create_summary_sheet(self, ws, model_data):
        """Create executive summary sheet"""
        company_data = model_data.get('company_data', {})
        scenarios = model_data.get('scenarios', {})
        
        # Title
        ws['A1'] = f"DCF Valuation - {company_data.get('company_name', 'Company')}"
        ws['A1'].font = Font(bold=True, size=16)
        ws.merge_cells('A1:F1')
        
        # Company info
        row = 3
        ws[f'A{row}'] = "Ticker:"
        ws[f'B{row}'] = company_data.get('ticker', '')
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        ws[f'A{row}'] = "Sector:"
        ws[f'B{row}'] = company_data.get('sector', '')
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        ws[f'A{row}'] = "Market Cap:"
        ws[f'B{row}'] = company_data.get('market_cap', 0) / 1e9
        ws[f'B{row}'].number_format = '"$"#,##0.0"B"'
        ws[f'A{row}'].font = Font(bold=True)
        
        row += 1
        ws[f'A{row}'] = "Current Price:"
        ws[f'B{row}'] = company_data.get('current_price', 0)
        ws[f'B{row}'].number_format = self.currency_format
        ws[f'A{row}'].font = Font(bold=True)
        
        # Valuation summary
        row += 3
        ws[f'A{row}'] = "VALUATION SUMMARY"
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].fill = self.header_fill
        ws.merge_cells(f'A{row}:F{row}')
        
        row += 2
        headers = ['Scenario', 'Enterprise Value', 'Equity Value', 'Implied Price', 'Current Price', 'Upside/Downside']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        
        # Add scenario data
        for scenario_name, scenario_data in scenarios.items():
            row += 1
            ws.cell(row=row, column=1, value=scenario_name.title())
            ws.cell(row=row, column=2, value=scenario_data.get('enterprise_value', 0) / 1e9)
            ws.cell(row=row, column=3, value=scenario_data.get('equity_value', 0) / 1e9)
            ws.cell(row=row, column=4, value=scenario_data.get('implied_price', 0))
            ws.cell(row=row, column=5, value=scenario_data.get('current_price', 0))
            ws.cell(row=row, column=6, value=scenario_data.get('upside_downside', 0) / 100)
            
            # Format numbers
            ws.cell(row=row, column=2).number_format = '"$"#,##0.0"B"'
            ws.cell(row=row, column=3).number_format = '"$"#,##0.0"B"'
            ws.cell(row=row, column=4).number_format = self.currency_format
            ws.cell(row=row, column=5).number_format = self.currency_format
            ws.cell(row=row, column=6).number_format = self.percent_format
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_dcf_sheet(self, ws, model_data):
        """Create detailed DCF model sheet"""
        company_data = model_data.get('company_data', {})
        base_scenario = model_data.get('scenarios', {}).get('base', {})
        assumptions = model_data.get('assumptions', {}).get('base', {})
        
        # Title
        ws['A1'] = f"DCF Model - {company_data.get('company_name', 'Company')}"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:H1')
        
        # Years header
        row = 3
        ws[f'A{row}'] = "Projection Period"
        ws[f'A{row}'].font = Font(bold=True)
        
        years = ['Base Year', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Terminal']
        for col, year in enumerate(years, 2):
            cell = ws.cell(row=row, column=col, value=year)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        
        # Revenue projections
        row += 2
        ws[f'A{row}'] = "REVENUE PROJECTIONS"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        
        row += 1
        ws[f'A{row}'] = "Revenue ($M)"
        base_revenue = company_data.get('revenue', 1000000000) / 1e6  # Convert to millions
        
        # Base year
        ws.cell(row=row, column=2, value=base_revenue)
        
        # Projected years
        for year in range(1, 6):
            growth_rate = assumptions.get(f'revenue_growth_{year}', 0.05)
            revenue = base_revenue * ((1 + growth_rate) ** year)
            ws.cell(row=row, column=year + 2, value=revenue)
        
        # Terminal year
        terminal_growth = assumptions.get('terminal_growth', 0.025)
        terminal_revenue = base_revenue * ((1 + assumptions.get('revenue_growth_5', 0.05)) ** 5) * (1 + terminal_growth)
        ws.cell(row=row, column=8, value=terminal_revenue)
        
        # Format revenue row
        for col in range(2, 9):
            ws.cell(row=row, column=col).number_format = '"$"#,##0.0'
        
        # Operating metrics
        row += 2
        ws[f'A{row}'] = "OPERATING METRICS"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        
        row += 1
        ws[f'A{row}'] = "Operating Margin"
        operating_margin = assumptions.get('operating_margin', 0.15)
        for col in range(2, 9):
            ws.cell(row=row, column=col, value=operating_margin)
            ws.cell(row=row, column=col).number_format = self.percent_format
        
        row += 1
        ws[f'A{row}'] = "Tax Rate"
        tax_rate = assumptions.get('tax_rate', 0.25)
        for col in range(2, 9):
            ws.cell(row=row, column=col, value=tax_rate)
            ws.cell(row=row, column=col).number_format = self.percent_format
        
        # Cash flow calculations
        row += 2
        ws[f'A{row}'] = "FREE CASH FLOW"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        
        cash_flows = base_scenario.get('cash_flows', [0] * 5)
        
        row += 1
        ws[f'A{row}'] = "Free Cash Flow ($M)"
        ws.cell(row=row, column=2, value=0)  # Base year
        
        for i, cf in enumerate(cash_flows, 1):
            ws.cell(row=row, column=i + 2, value=cf / 1e6)  # Convert to millions
            ws.cell(row=row, column=i + 2).number_format = '"$"#,##0.0'
        
        # Terminal FCF
        if cash_flows:
            terminal_fcf = cash_flows[-1] * (1 + terminal_growth) / 1e6
            ws.cell(row=row, column=8, value=terminal_fcf)
            ws.cell(row=row, column=8).number_format = '"$"#,##0.0'
        
        # Valuation
        row += 2
        ws[f'A{row}'] = "VALUATION"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        
        row += 1
        ws[f'A{row}'] = "WACC"
        ws[f'B{row}'] = assumptions.get('wacc', 0.10)
        ws[f'B{row}'].number_format = self.percent_format
        
        row += 1
        ws[f'A{row}'] = "Terminal Growth Rate"
        ws[f'B{row}'] = terminal_growth
        ws[f'B{row}'].number_format = self.percent_format
        
        row += 1
        ws[f'A{row}'] = "Enterprise Value ($B)"
        ws[f'B{row}'] = base_scenario.get('enterprise_value', 0) / 1e9
        ws[f'B{row}'].number_format = '"$"#,##0.0'
        
        row += 1
        ws[f'A{row}'] = "Equity Value ($B)"
        ws[f'B{row}'] = base_scenario.get('equity_value', 0) / 1e9
        ws[f'B{row}'].number_format = '"$"#,##0.0'
        
        row += 1
        ws[f'A{row}'] = "Implied Share Price"
        ws[f'B{row}'] = base_scenario.get('implied_price', 0)
        ws[f'B{row}'].number_format = self.currency_format
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 20)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_assumptions_sheet(self, ws, model_data):
        """Create assumptions sheet"""
        assumptions = model_data.get('assumptions', {})
        company_data = model_data.get('company_data', {})
        
        # Title
        ws['A1'] = "Model Assumptions"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:D1')
        
        row = 3
        
        # Company data section
        ws[f'A{row}'] = "COMPANY DATA"
        ws[f'A{row}'].font = self.header_font
        ws[f'A{row}'].fill = self.header_fill
        ws.merge_cells(f'A{row}:D{row}')
        
        company_items = [
            ('Company Name', company_data.get('company_name', '')),
            ('Ticker', company_data.get('ticker', '')),
            ('Sector', company_data.get('sector', '')),
            ('Market Cap ($B)', company_data.get('market_cap', 0) / 1e9),
            ('Current Price', company_data.get('current_price', 0)),
            ('Shares Outstanding (M)', company_data.get('shares_outstanding', 0) / 1e6),
            ('Beta', company_data.get('beta', 0)),
        ]
        
        for item, value in company_items:
            row += 1
            ws[f'A{row}'] = item
            ws[f'B{row}'] = value
            ws[f'A{row}'].font = Font(bold=True)
            
            if 'Price' in item or 'Market Cap' in item:
                ws[f'B{row}'].number_format = self.currency_format
        
        # Scenario assumptions
        for scenario_name, scenario_assumptions in assumptions.items():
            row += 3
            ws[f'A{row}'] = f"{scenario_name.upper()} CASE ASSUMPTIONS"
            ws[f'A{row}'].font = self.header_font
            ws[f'A{row}'].fill = self.header_fill
            ws.merge_cells(f'A{row}:D{row}')
            
            assumption_items = [
                ('Revenue Growth Year 1', scenario_assumptions.get('revenue_growth_1', 0)),
                ('Revenue Growth Year 2', scenario_assumptions.get('revenue_growth_2', 0)),
                ('Revenue Growth Year 3', scenario_assumptions.get('revenue_growth_3', 0)),
                ('Revenue Growth Year 4', scenario_assumptions.get('revenue_growth_4', 0)),
                ('Revenue Growth Year 5', scenario_assumptions.get('revenue_growth_5', 0)),
                ('Operating Margin', scenario_assumptions.get('operating_margin', 0)),
                ('Tax Rate', scenario_assumptions.get('tax_rate', 0)),
                ('WACC', scenario_assumptions.get('wacc', 0)),
                ('Terminal Growth Rate', scenario_assumptions.get('terminal_growth', 0)),
                ('CapEx % of Revenue', scenario_assumptions.get('capex_percent', 0)),
                ('NWC % of Revenue', scenario_assumptions.get('nwc_percent', 0)),
            ]
            
            for item, value in assumption_items:
                row += 1
                ws[f'A{row}'] = item
                ws[f'B{row}'] = value
                ws[f'A{row}'].font = Font(bold=True)
                ws[f'B{row}'].number_format = self.percent_format
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 25)
            ws.column_dimensions[column_letter].width = adjusted_width

# Initialize Excel generator
excel_generator = ExcelModelGenerator()

def cleanup_old_files():
    """Clean up old Excel files from temp directory"""
    try:
        temp_dir = '/tmp'
        if not os.path.exists(temp_dir):
            return
        
        current_time = datetime.now()
        
        for filename in os.listdir(temp_dir):
            if filename.endswith('.xlsx'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    # Get file modification time
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Delete files older than 4 hours
                    if (current_time - file_time).total_seconds() > 4 * 3600:
                        os.remove(file_path)
                        print(f"Cleaned up old file: {filename}")
                        
                except Exception as e:
                    print(f"Error cleaning up file {filename}: {e}")
                    
    except Exception as e:
        print(f"Error in cleanup_old_files: {e}")

# Clean up old files on startup
cleanup_old_files()

def generate_valuation_html(result):
    """Generate HTML for valuation results with scenario support"""
    
    # Check if we have multiple scenarios
    scenarios = result.get('scenarios', {})
    if scenarios and len(scenarios) > 1:
        # Multiple scenarios - create tabs
        html = '''
        <div class="mb-6">
            <div class="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        '''
        
        for i, (scenario_name, scenario_data) in enumerate(scenarios.items()):
            active_class = 'bg-white text-navy shadow-sm' if i == 0 else 'text-gray-600 hover:text-gray-900'
            html += f'''
                <button onclick="showScenario('{scenario_name}')" 
                        class="scenario-tab px-4 py-2 text-sm font-medium rounded-md transition-colors {active_class}" 
                        data-scenario="{scenario_name}">
                    {scenario_name.title()} Case
                </button>
            '''
        
        html += '''
            </div>
        </div>
        '''
        
        # Scenario content
        for i, (scenario_name, scenario_data) in enumerate(scenarios.items()):
            display_style = 'block' if i == 0 else 'none'
            html += f'''
            <div id="scenario-{scenario_name}" class="scenario-content" style="display: {display_style};">
                {_generate_metrics_grid(scenario_data, scenario_name)}
            </div>
            '''
            
        # Add JavaScript for tab switching
        html += '''
        <script>
            function showScenario(scenarioName) {
                // Hide all scenarios
                document.querySelectorAll('.scenario-content').forEach(content => {
                    content.style.display = 'none';
                });
                
                // Show selected scenario
                document.getElementById('scenario-' + scenarioName).style.display = 'block';
                
                // Update tab styling
                document.querySelectorAll('.scenario-tab').forEach(tab => {
                    if (tab.getAttribute('data-scenario') === scenarioName) {
                        tab.className = 'scenario-tab px-4 py-2 text-sm font-medium rounded-md transition-colors bg-white text-navy shadow-sm';
                    } else {
                        tab.className = 'scenario-tab px-4 py-2 text-sm font-medium rounded-md transition-colors text-gray-600 hover:text-gray-900';
                    }
                });
            }
        </script>
        '''
        
    else:
        # Single scenario - just show the metrics
        valuation_data = result.get('model_summary', {}).get('valuation_outputs', {})
        html = _generate_metrics_grid(valuation_data, 'base')
    
    return html

def _generate_metrics_grid(data, scenario_name='base'):
    """Generate metrics grid for a single scenario"""
    
    # Handle different data structures
    if isinstance(data, dict):
        enterprise_value = data.get('enterprise_value', 0)
        equity_value = data.get('equity_value', 0)
        implied_price = data.get('implied_price', 0)
        current_price = data.get('current_price', 0)
        upside_downside = data.get('upside_downside', 0)
    else:
        # Fallback values
        enterprise_value = equity_value = implied_price = current_price = upside_downside = 0
    
    # Color scheme based on scenario
    if scenario_name == 'bull':
        color_class = 'bg-green-50'
        text_class = 'text-green-700'
    elif scenario_name == 'bear':
        color_class = 'bg-red-50'
        text_class = 'text-red-700'
    else:
        color_class = 'bg-success-bg'
        text_class = 'text-success'
    
    upside_color = 'text-green-600' if upside_downside > 0 else 'text-red-600'
    upside_sign = '+' if upside_downside > 0 else ''
    
    return f'''
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="{color_class} rounded-lg p-4 text-center">
            <h3 class="text-sm font-medium {text_class} mb-2">Enterprise Value</h3>
            <div class="text-2xl font-bold {text_class}">${enterprise_value/1000000000:.1f}B</div>
        </div>
        <div class="{color_class} rounded-lg p-4 text-center">
            <h3 class="text-sm font-medium {text_class} mb-2">Equity Value</h3>
            <div class="text-2xl font-bold {text_class}">${equity_value/1000000000:.1f}B</div>
        </div>
        <div class="bg-blue-50 rounded-lg p-4 text-center">
            <h3 class="text-sm font-medium text-blue-700 mb-2">Implied Price</h3>
            <div class="text-2xl font-bold text-blue-700">${implied_price:.2f}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 text-center">
            <h3 class="text-sm font-medium text-gray-700 mb-2">Current Price</h3>
            <div class="text-2xl font-bold text-gray-700">${current_price:.2f}</div>
        </div>
    </div>
    <div class="mt-4 text-center">
        <div class="inline-flex items-center px-4 py-2 bg-gray-50 rounded-lg">
            <span class="text-sm text-gray-600 mr-2">Upside/Downside:</span>
            <span class="text-lg font-bold {upside_color}">{upside_sign}{upside_downside:.1f}%</span>
        </div>
    </div>
    '''

def format_assumptions_html(result):
    """Format assumptions for display"""
    assumptions = result.get('model_summary', {}).get('key_assumptions', {})
    
    # Handle different assumption formats
    if 'revenue_growth_rate' in assumptions:
        # Simple format
        return f'''
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Revenue Growth</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('revenue_growth_rate', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">WACC</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('wacc', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Terminal Growth</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('terminal_growth_rate', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Operating Margin</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('operating_margin', 0)*100:.1f}%</span>
        </div>
        '''
    else:
        # Detailed DCF format
        return f'''
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Revenue Growth (Yr 1)</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('revenue_growth_1', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Operating Margin</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('operating_margin', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">WACC</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('wacc', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Terminal Growth</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('terminal_growth', 0)*100:.1f}%</span>
        </div>
        <div class="flex justify-between">
            <span class="text-sm text-gray-600">Tax Rate</span>
            <span class="text-sm font-medium text-gray-900">{assumptions.get('tax_rate', 0)*100:.1f}%</span>
        </div>
        '''

def generate_download_section(model):
    """Generate download section with proper states"""
    file_ready = model.get('file_ready', False)
    excel_filename = model.get('excel_filename')
    
    if file_ready and excel_filename:
        # File is ready for download
        return f'''
        <!-- Success State -->
        <div class="bg-success-bg border border-success/20 rounded-lg p-3 mb-4">
            <div class="flex items-center">
                <svg class="w-4 h-4 text-success mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-sm font-medium text-success">Your model is ready. Click below to download.</span>
            </div>
        </div>
        
        <div class="bg-gray-50 rounded-lg p-3 mb-4">
            <p class="text-sm font-mono text-gray-700">{excel_filename}</p>
        </div>
        
        <a href="/download/{excel_filename}" class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors flex items-center justify-center">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            Download Excel
        </a>
        
        <p class="text-xs text-gray-500 mt-3">
            <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Files are temporary and may be deleted after a few hours.
        </p>
        '''
    else:
        # File not ready or failed to generate
        return f'''
        <!-- Error State -->
        <div class="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <div class="flex items-center">
                <svg class="w-4 h-4 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-sm font-medium text-red-800">Model not found. Please regenerate.</span>
            </div>
        </div>
        
        <div class="bg-gray-50 rounded-lg p-3 mb-4">
            <p class="text-sm text-gray-500">Excel file not available</p>
        </div>
        
        <button disabled class="w-full bg-gray-300 text-gray-500 px-4 py-2 rounded-lg font-medium cursor-not-allowed flex items-center justify-center">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            Download Unavailable
        </button>
        
        <div class="mt-3">
            <a href="/generate-model" class="text-sm text-navy hover:text-navy/80 font-medium">
                ← Generate a new model
            </a>
        </div>
        '''

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IB Modeling Assistant - Professional Financial Models</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        },
                        fontFamily: {
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/models" class="text-sm text-navy hover:text-navy/80 font-medium">View Models</a>
                        <a href="/status" class="text-sm text-gray-600 hover:text-gray-800">Status</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="grid grid-cols-12 gap-6">
                <!-- Input Panel -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="bg-gray-50 rounded-xl p-6 shadow-sm">
                        <h2 class="text-lg font-semibold text-gray-900 mb-4">Model Selection</h2>
                        
                        <!-- Model Tabs -->
                        <div class="mb-6">
                            <div class="flex flex-wrap gap-2" role="tablist">
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-navy text-white" role="tab" onclick="setActiveModel('dcf')">DCF</button>
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors" role="tab" onclick="setActiveModel('lbo')">LBO</button>
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors" role="tab" onclick="setActiveModel('merger')">Merger</button>
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors" role="tab" onclick="setActiveModel('comps')">Comps</button>
                            </div>
                        </div>

                        <!-- Quick Start -->
                        <div class="bg-white rounded-xl p-4 border border-gray-200 mb-4">
                            <h3 class="font-medium text-gray-900 mb-3">Quick Start</h3>
                            <a href="/generate-model" class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors inline-block text-center">
                                Generate Model
                            </a>
                        </div>

                        <!-- Status -->
                        <div class="bg-white rounded-xl p-4 border border-gray-200">
                            <div class="flex items-center">
                                <div class="w-2 h-2 bg-success rounded-full mr-3"></div>
                                <span class="text-sm font-medium text-gray-900">System Ready</span>
                            </div>
                            <p class="text-xs text-gray-600 mt-1">Ready to generate banker-formatted Excel models</p>
                        </div>
                    </div>
                </div>

                <!-- Output Panel -->
                <div class="col-span-12 lg:col-span-8">
                    <div class="space-y-6">
                        <!-- Welcome Card -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h2 class="text-xl font-semibold text-gray-900 mb-2">Professional Financial Modeling Platform</h2>
                            <p class="text-gray-600 mb-4">Create investment-grade financial models with institutional-quality formatting and analysis.</p>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                <div class="bg-success-bg rounded-lg p-4">
                                    <h3 class="font-medium text-success mb-1">DCF Models</h3>
                                    <p class="text-sm text-gray-600">Discounted cash flow analysis with sensitivity tables</p>
                                </div>
                                <div class="bg-blue-50 rounded-lg p-4">
                                    <h3 class="font-medium text-blue-700 mb-1">LBO Models</h3>
                                    <p class="text-sm text-gray-600">Leveraged buyout modeling with returns analysis</p>
                                </div>
                                <div class="bg-purple-50 rounded-lg p-4">
                                    <h3 class="font-medium text-purple-700 mb-1">M&A Models</h3>
                                    <p class="text-sm text-gray-600">Merger analysis with accretion/dilution</p>
                                </div>
                                <div class="bg-orange-50 rounded-lg p-4">
                                    <h3 class="font-medium text-orange-700 mb-1">Comps Analysis</h3>
                                    <p class="text-sm text-gray-600">Trading and transaction comparables</p>
                                </div>
                            </div>
                        </div>

                        <!-- Key Features -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">Platform Features</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="text-center">
                                    <div class="w-12 h-12 bg-navy/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                                        <svg class="w-6 h-6 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                        </svg>
                                    </div>
                                    <h4 class="font-medium text-gray-900 mb-1">Professional Output</h4>
                                    <p class="text-sm text-gray-600">Investment-grade Excel formatting</p>
                                </div>
                                <div class="text-center">
                                    <div class="w-12 h-12 bg-success/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                                        <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                        </svg>
                                    </div>
                                    <h4 class="font-medium text-gray-900 mb-1">Fast Generation</h4>
                                    <p class="text-sm text-gray-600">Models ready in seconds</p>
                                </div>
                                <div class="text-center">
                                    <div class="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mx-auto mb-3">
                                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                    </div>
                                    <h4 class="font-medium text-gray-900 mb-1">Validated Models</h4>
                                    <p class="text-sm text-gray-600">Industry-standard methodologies</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function setActiveModel(model) {
                // Update active tab styling
                const tabs = document.querySelectorAll('[role="tab"]');
                tabs.forEach(tab => {
                    if (tab.textContent.toLowerCase() === model.toLowerCase()) {
                        tab.className = 'px-3 py-2 text-sm font-medium rounded-lg bg-navy text-white';
                    } else {
                        tab.className = 'px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors';
                    }
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/ping')
def ping():
    return "pong"

@app.route('/api/company-data/<ticker>')
def get_company_data_api(ticker):
    """API endpoint to fetch real company data"""
    try:
        data = financial_engine.get_company_data(ticker.upper())
        if data:
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Could not fetch data for {ticker}'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Session Management API Endpoints

@app.route('/config', methods=['GET'])
def get_config():
    """Provide allowed values and defaults for the landing screen"""
    return jsonify({
        "climates": [e.value for e in ClimateType],
        "models": [e.value for e in ModelType],
        "defaults": {
            "climate": ClimateType.BASE.value,
            "model": ModelType.THREE_STATEMENT.value
        }
    })

@app.route('/session/start', methods=['POST'])
def start_session():
    """Validate selections and create a modeling session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "fields": {"request": "JSON body required"}
            }), 400
        
        # Validate inputs
        is_valid, errors = validate_session_request(data)
        if not is_valid:
            return jsonify({
                "error": "validation_error",
                "fields": errors
            }), 400
        
        # Extract and normalize inputs
        climate = data['climate'].lower()
        ticker = data['ticker'].strip().upper()
        model = data['model'].lower()
        
        # Check if ticker exists (optional verification)
        warnings = []
        try:
            exists, warning = lookup_ticker_exists(ticker)
            if warning:
                warnings.append(warning)
        except Exception as e:
            warnings.append(f"Ticker verification failed: {str(e)}")
        
        # Create session
        session_data = session_manager.create_session(climate, ticker, model)
        
        # Log session creation
        print(f"Created session {session_data.session_id} for {ticker} ({model}, {climate})")
        
        return jsonify({
            "session_id": session_data.session_id,
            "next_route": "/model",
            "view": "model",
            "model": session_data.model,
            "ticker": session_data.ticker,
            "climate": session_data.climate,
            "assumptions": session_data.assumptions,
            "warnings": warnings
        }), 201
        
    except Exception as e:
        print(f"Error in start_session: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to create session"
        }), 500

@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Allow the model screen to re-hydrate on refresh"""
    try:
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            return jsonify({
                "error": "not_found"
            }), 404
        
        return jsonify({
            "session_id": session_data.session_id,
            "view": "model",
            "model": session_data.model,
            "ticker": session_data.ticker,
            "climate": session_data.climate,
            "assumptions": session_data.assumptions,
            "ready": session_data.ready
        })
        
    except Exception as e:
        print(f"Error in get_session: {e}")
        return jsonify({
            "error": "internal_error"
        }), 500

@app.route('/assumptions/apply', methods=['POST'])
def apply_assumptions():
    """Update assumptions on the model screen"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "fields": {"request": "JSON body required"}
            }), 400
        
        session_id = data.get('session_id')
        new_assumptions = data.get('assumptions', {})
        
        if not session_id:
            return jsonify({
                "error": "validation_error",
                "fields": {"session_id": "Session ID required"}
            }), 400
        
        if not isinstance(new_assumptions, dict):
            return jsonify({
                "error": "validation_error",
                "fields": {"assumptions": "Assumptions must be an object"}
            }), 400
        
        # Validate assumption values are numbers
        for key, value in new_assumptions.items():
            if not isinstance(value, (int, float)):
                return jsonify({
                    "error": "validation_error",
                    "fields": {f"assumptions.{key}": "Must be a number"}
                }), 400
        
        # Update session
        session_data = session_manager.update_assumptions(session_id, new_assumptions)
        
        if not session_data:
            return jsonify({
                "error": "not_found"
            }), 404
        
        print(f"Updated assumptions for session {session_id}: {new_assumptions}")
        
        return jsonify({
            "session_id": session_data.session_id,
            "view": "model",
            "model": session_data.model,
            "ticker": session_data.ticker,
            "climate": session_data.climate,
            "assumptions": session_data.assumptions,
            "ready": session_data.ready
        })
        
    except Exception as e:
        print(f"Error in apply_assumptions: {e}")
        return jsonify({
            "error": "internal_error"
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download Excel file from temp directory"""
    try:
        # Security: Only allow .xlsx files and sanitize filename
        if not filename.endswith('.xlsx') or '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_path = os.path.join('/tmp', filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'Model not found. Please regenerate.'}), 404
        
        # Send file with proper headers
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/download-model/<model_id>')
def download_model(model_id):
    """Legacy download route - redirects to new file-based download"""
    try:
        if model_id not in MODEL_STORAGE:
            return jsonify({'error': 'Model not found'}), 404
        
        model = MODEL_STORAGE[model_id]
        
        # Check if Excel file was generated
        if model.get('excel_filename'):
            return redirect(url_for('download_file', filename=model['excel_filename']))
        else:
            # Fallback: generate file on-demand
            result = model['result']
            
            if model['type'] == 'dcf' and result.get('scenarios'):
                wb = excel_generator.generate_dcf_model(result)
            else:
                # Create fallback model
                wb = excel_generator.generate_dcf_model({
                    'company_data': {
                        'company_name': result.get('company_name', f"{model['ticker']} Corporation"),
                        'ticker': model['ticker'],
                        'sector': result.get('sector', 'Unknown'),
                        'market_cap': 1000000000,
                        'current_price': 100,
                        'shares_outstanding': 10000000,
                        'beta': 1.0
                    },
                    'scenarios': {
                        'base': result.get('model_summary', {}).get('valuation_outputs', {})
                    },
                    'assumptions': {
                        'base': result.get('model_summary', {}).get('key_assumptions', {})
                    }
                })
            
            # Save to memory buffer and serve directly
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{model['type'].upper()}_{model['ticker']}_{timestamp}.xlsx"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
    except Exception as e:
        print(f"Error in download_model: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/status')
def status():
    import os
    return {
        "status": "running",
        "port": os.environ.get('PORT', 'not_set'),
        "app": "minimal_finmodai",
        "active_sessions": len(session_manager.sessions)
    }

@app.route('/test-session-flow', methods=['GET'])
def test_session_flow():
    """Test endpoint to demonstrate the complete session flow"""
    return jsonify({
        "message": "Session API Test Flow",
        "steps": [
            "1. GET /config - Get allowed values",
            "2. POST /session/start - Create session with climate/ticker/model",
            "3. GET /session/{session_id} - Retrieve session state",
            "4. POST /assumptions/apply - Update assumptions (optional)"
        ],
        "example_flow": {
            "step_1": {
                "method": "GET",
                "url": "/config",
                "response": {
                    "climates": ["base", "bull", "bear", "esg"],
                    "models": ["three_statement", "dcf", "lbo", "merger", "comps"],
                    "defaults": {"climate": "base", "model": "three_statement"}
                }
            },
            "step_2": {
                "method": "POST",
                "url": "/session/start",
                "body": {"climate": "bull", "ticker": "AAPL", "model": "dcf"},
                "response": {
                    "session_id": "uuid",
                    "next_route": "/model",
                    "view": "model",
                    "assumptions": {"growth_pct": 0.08, "ebitda_margin_pct": 0.28}
                }
            }
        },
        "current_sessions": len(session_manager.sessions)
    })

@app.route('/test')
def test():
    return "Minimal FinModAI Test - Working!"

@app.route('/debug-form', methods=['GET', 'POST'])
def debug_form():
    """Debug endpoint to test form submission"""
    if request.method == 'POST':
        form_data = {
            'ticker': request.form.get('ticker'),
            'model_type': request.form.get('model_type'),
            'use_market_data': request.form.get('use_market_data'),
            'scenario': request.form.get('scenario'),
            'all_form_data': dict(request.form)
        }
        
        return jsonify({
            'message': 'Form received successfully!',
            'method': 'POST',
            'form_data': form_data,
            'timestamp': datetime.now().isoformat()
        })
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Form Test</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow">
            <h1 class="text-xl font-bold mb-4">Debug Form Test</h1>
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Ticker:</label>
                    <input type="text" name="ticker" value="AAPL" class="w-full border rounded px-3 py-2">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Model Type:</label>
                    <select name="model_type" class="w-full border rounded px-3 py-2">
                        <option value="dcf">DCF</option>
                        <option value="lbo">LBO</option>
                    </select>
                </div>
                <div>
                    <label class="flex items-center">
                        <input type="checkbox" name="use_market_data" value="true" checked class="mr-2">
                        Use Market Data
                    </label>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Scenario:</label>
                    <select name="scenario" class="w-full border rounded px-3 py-2">
                        <option value="base">Base</option>
                        <option value="bull">Bull</option>
                        <option value="bear">Bear</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600">
                    Test Submit
                </button>
            </form>
            <div class="mt-4">
                <a href="/generate-model" class="text-blue-500 hover:underline">← Back to Generate Model</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/generate-model', methods=['GET', 'POST'])
def generate_model():
    if request.method == 'POST':
        print(f"🔥 POST request received!")
        print(f"📋 Form data: {dict(request.form)}")
        
        model_type = request.form.get('model_type', 'dcf')
        ticker = request.form.get('ticker', '').upper()
        use_market_data = request.form.get('use_market_data', 'true') == 'true'
        scenario = request.form.get('scenario', 'base')  # base, bull, bear, or all
        
        print(f"📊 Parsed data: model_type={model_type}, ticker={ticker}, use_market_data={use_market_data}, scenario={scenario}")
        
        if not ticker:
            flash('Please enter a ticker symbol', 'error')
            return redirect(url_for('generate_model'))
        
        try:
            start_time = datetime.now()
            model_id = str(uuid.uuid4())
            
            print(f"🚀 Starting model generation: {model_type} for {ticker}")
            print(f"📊 Use market data: {use_market_data}, Scenario: {scenario}")
            
            if model_type == 'dcf' and use_market_data:
                # Use real financial data for DCF
                print(f"📈 Fetching real financial data for {ticker}")
                dcf_data = financial_engine.calculate_dcf_scenarios(ticker)
                
                if dcf_data:
                    print(f"✅ Financial data processed successfully for {ticker}")
                    company_data = dcf_data['company_data']
                    scenarios = dcf_data['scenarios']
                    assumptions = dcf_data['assumptions']
                    
                    # Determine which scenario(s) to show
                    if scenario == 'all':
                        selected_scenarios = scenarios
                    else:
                        selected_scenarios = {scenario: scenarios[scenario]}
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    model_result = {
                        'model_type': model_type,
                        'ticker': ticker,
                        'status': 'completed',
                        'company_name': company_data['company_name'],
                        'sector': company_data.get('sector', 'Unknown'),
                        'industry': company_data.get('industry', 'Unknown'),
                        'processing_time_seconds': round(processing_time, 2),
                        'use_market_data': use_market_data,
                        'scenario_type': scenario,
                        'company_data': company_data,
                        'scenarios': selected_scenarios,
                        'assumptions': assumptions,
                        'model_summary': {
                            'key_assumptions': assumptions['base'],
                            'valuation_outputs': scenarios['base']  # Default to base case for summary
                        }
                    }
                    print(f"📊 DCF model created with data for {company_data['company_name']}")
                else:
                    print(f"⚠️ Falling back to mock data for {ticker}")
                    flash(f'Using estimated data for {ticker} - market data may be temporarily unavailable.', 'warning')
                    # Fall through to mock data section below
                    use_market_data = False  # Switch to mock data
            
            if not (model_type == 'dcf' and use_market_data and dcf_data):
                # Fallback to mock data for other model types or when market data is disabled
                print(f"📋 Using mock data for {model_type} model")
                processing_time = (datetime.now() - start_time).total_seconds()
                
                model_result = {
                    'model_type': model_type,
                    'ticker': ticker,
                    'status': 'completed',
                    'company_name': f"{ticker} Corporation",
                    'processing_time_seconds': round(processing_time, 2),
                    'use_market_data': use_market_data,
                    'scenario_type': scenario,
                    'model_summary': {
                        'key_assumptions': {
                            'revenue_growth_rate': 0.12,
                            'wacc': 0.095,
                            'terminal_growth_rate': 0.025,
                            'operating_margin': 0.25
                        },
                        'valuation_outputs': {
                            'enterprise_value': 850000000000,
                            'equity_value': 800000000000,
                            'implied_price': 165.50,
                            'current_price': 150.00,
                            'upside_downside': 10.33
                        }
                    }
                }
            
            # Generate Excel file and save to temp directory
            excel_filename = None
            if model_type == 'dcf' and model_result:  # Generate Excel for any DCF model with results
                try:
                    print(f"📄 Generating Excel file for {ticker}")
                    # Generate Excel file
                    wb = excel_generator.generate_dcf_model(model_result)
                    
                    # Create temp directory if it doesn't exist
                    temp_dir = '/tmp'
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    excel_filename = f"{model_type.upper()}_{ticker}_{timestamp}.xlsx"
                    file_path = os.path.join(temp_dir, excel_filename)
                    
                    # Save Excel file
                    wb.save(file_path)
                    print(f"✅ Excel file saved: {file_path}")
                    
                    # Verify file exists
                    if os.path.exists(file_path):
                        print(f"✅ File verified at: {file_path}")
                    else:
                        print(f"❌ File not found after save: {file_path}")
                        excel_filename = None
                    
                except Exception as e:
                    print(f"❌ Error generating Excel file: {e}")
                    import traceback
                    traceback.print_exc()
                    excel_filename = None
            
            MODEL_STORAGE[model_id] = {
                'id': model_id,
                'type': model_type,
                'ticker': ticker,
                'result': model_result,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'excel_filename': excel_filename,
                'file_ready': excel_filename is not None
            }
            
            print(f"🎉 Model {model_id} created successfully for {ticker}")
            return redirect(url_for('model_results', model_id=model_id))
            
        except Exception as e:
            print(f"❌ Error generating model: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error generating model: {str(e)}', 'error')
            return redirect(url_for('generate_model'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generate Model - IB Modeling Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        },
                        fontFamily: {
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/" class="text-sm text-navy hover:text-navy/80 font-medium">Home</a>
                        <a href="/models" class="text-sm text-navy hover:text-navy/80 font-medium">View Models</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="grid grid-cols-12 gap-6">
                <!-- Input Panel -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="bg-gray-50 rounded-xl p-6 shadow-sm sticky top-8">
                        <!-- Flash Messages -->
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                <div class="mb-4">
                                    {% for category, message in messages %}
                                        <div class="alert alert-{{ 'danger' if category == 'error' else category }} mb-3 p-3 rounded-lg border-l-4 
                                                    {{ 'bg-red-50 border-red-500 text-red-700' if category == 'error' else 'bg-green-50 border-green-500 text-green-700' }}">
                                            <div class="flex items-center">
                                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    {% if category == 'error' %}
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                                    {% else %}
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                                    {% endif %}
                                                </svg>
                                                {{ message }}
                                            </div>
                                        </div>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        {% endwith %}
                        
                        <h2 class="text-lg font-semibold text-gray-900 mb-6">Model Configuration</h2>
                        
                        <form method="POST" class="space-y-6">
                            <!-- Operating Assumptions -->
                            <div class="bg-white rounded-xl p-4 border border-gray-200">
                                <h3 class="font-medium text-gray-900 mb-4 flex items-center">
                                    <svg class="w-5 h-5 text-navy mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                    </svg>
                                    Operating Assumptions
                                </h3>
                                
                                <div class="space-y-4">
                                    <div>
                                        <label for="model_type" class="block text-sm font-medium text-gray-700 mb-2">Model Type</label>
                                        <select name="model_type" id="model_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-navy">
                                            <option value="dcf">DCF (Discounted Cash Flow)</option>
                                            <option value="lbo">LBO (Leveraged Buyout)</option>
                                            <option value="comps">Trading Comparables</option>
                                            <option value="merger">M&A Analysis</option>
                                        </select>
                                    </div>
                                    
                                    <div>
                                        <label for="ticker" class="block text-sm font-medium text-gray-700 mb-2">Company Ticker</label>
                                        <input type="text" name="ticker" id="ticker" placeholder="e.g., AAPL, MSFT, TSLA" required
                                               class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-navy uppercase">
                                    </div>
                                </div>
                            </div>

                            <!-- Market Data -->
                            <div class="bg-white rounded-xl p-4 border border-gray-200">
                                <h3 class="font-medium text-gray-900 mb-4 flex items-center">
                                    <svg class="w-5 h-5 text-navy mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                                    </svg>
                                    Market Data & Scenarios
                                </h3>
                                
                                <div class="space-y-4">
                                    <!-- Market Data Toggle -->
                                    <div>
                                        <label class="flex items-center">
                                            <input type="checkbox" name="use_market_data" value="true" checked 
                                                   class="w-4 h-4 text-navy bg-gray-100 border-gray-300 rounded focus:ring-navy focus:ring-2">
                                            <span class="ml-2 text-sm text-gray-700">Use real-time market data</span>
                                        </label>
                                        <p class="text-xs text-gray-500 ml-6">Fetch live financial data from yfinance</p>
                                    </div>
                                    
                                    <!-- Scenario Selection -->
                                    <div>
                                        <label for="scenario" class="block text-sm font-medium text-gray-700 mb-2">Scenario Analysis</label>
                                        <select name="scenario" id="scenario" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-navy">
                                            <option value="base">Base Case Only</option>
                                            <option value="bull">Bull Case Only</option>
                                            <option value="bear">Bear Case Only</option>
                                            <option value="all">All Scenarios (Base/Bull/Bear)</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <!-- Scenario Pills (Interactive Preview) -->
                                <div class="flex gap-2 mt-4">
                                    <button type="button" onclick="setScenario('base')" class="scenario-pill px-3 py-1 text-xs font-medium bg-navy text-white rounded-full transition-colors" data-scenario="base">Base Case</button>
                                    <button type="button" onclick="setScenario('bull')" class="scenario-pill px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-success hover:text-white transition-colors" data-scenario="bull">Bull Case</button>
                                    <button type="button" onclick="setScenario('bear')" class="scenario-pill px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-red-100 hover:text-red-700 transition-colors" data-scenario="bear">Bear Case</button>
                                    <button type="button" onclick="setScenario('all')" class="scenario-pill px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-purple-100 hover:text-purple-700 transition-colors" data-scenario="all">All</button>
                                </div>
                            </div>

                            <!-- Generate Button -->
                            <button type="submit" class="w-full bg-navy text-white px-6 py-3 rounded-lg font-medium hover:bg-navy/90 transition-colors flex items-center justify-center">
                                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                </svg>
                                Generate Model
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Output Panel -->
                <div class="col-span-12 lg:col-span-8">
                    <div class="space-y-6">
                        <!-- Status -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <div class="flex items-center justify-between mb-4">
                                <h2 class="text-lg font-semibold text-gray-900">Model Generation</h2>
                                <div class="flex items-center">
                                    <div class="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                                    <span class="text-sm text-gray-600">Ready to generate</span>
                                </div>
                            </div>
                            <p class="text-gray-600">Select a model type and enter a company ticker to generate a banker-formatted Excel model.</p>
                        </div>

                        <!-- Instructions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">How It Works</h3>
                            <div class="space-y-4">
                                <div class="flex items-start">
                                    <div class="w-8 h-8 bg-navy/10 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                        <span class="text-sm font-medium text-navy">1</span>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-gray-900">Select Model Type</h4>
                                        <p class="text-sm text-gray-600">Choose from DCF, LBO, M&A, or Comparables analysis</p>
                                    </div>
                                </div>
                                <div class="flex items-start">
                                    <div class="w-8 h-8 bg-navy/10 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                        <span class="text-sm font-medium text-navy">2</span>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-gray-900">Enter Company Ticker</h4>
                                        <p class="text-sm text-gray-600">Input the stock symbol (e.g., AAPL, MSFT, TSLA)</p>
                                    </div>
                                </div>
                                <div class="flex items-start">
                                    <div class="w-8 h-8 bg-navy/10 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                        <span class="text-sm font-medium text-navy">3</span>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-gray-900">Generate & Download</h4>
                                        <p class="text-sm text-gray-600">Get a professional Excel model ready for analysis</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function setScenario(scenario) {
                // Update select dropdown
                document.getElementById('scenario').value = scenario;
                
                // Update pill styling
                document.querySelectorAll('.scenario-pill').forEach(pill => {
                    const pillScenario = pill.getAttribute('data-scenario');
                    if (pillScenario === scenario) {
                        pill.className = 'scenario-pill px-3 py-1 text-xs font-medium bg-navy text-white rounded-full transition-colors';
                    } else {
                        pill.className = 'scenario-pill px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors';
                    }
                });
            }

            // Auto-fetch company data when ticker is entered
            let companyDataTimeout;
            document.getElementById('ticker').addEventListener('input', function(e) {
                const ticker = e.target.value.toUpperCase();
                e.target.value = ticker; // Force uppercase
                if (ticker.length >= 2) {
                    clearTimeout(companyDataTimeout);
                    companyDataTimeout = setTimeout(() => fetchCompanyPreview(ticker), 1000);
                }
            });

            function fetchCompanyPreview(ticker) {
                if (!ticker) return;
                
                fetch(`/api/company-data/${ticker}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showCompanyPreview(data.data);
                        } else {
                            hideCompanyPreview();
                        }
                    })
                    .catch(error => {
                        console.log('Could not fetch preview for', ticker);
                        hideCompanyPreview();
                    });
            }

            function showCompanyPreview(data) {
                // Create or update preview panel
                let previewPanel = document.getElementById('company-preview');
                if (!previewPanel) {
                    previewPanel = document.createElement('div');
                    previewPanel.id = 'company-preview';
                    previewPanel.className = 'bg-blue-50 rounded-lg p-3 mt-3 border border-blue-200';
                    // Insert after the ticker input div
                    const tickerDiv = document.querySelector('input[name="ticker"]').closest('div');
                    tickerDiv.parentNode.insertBefore(previewPanel, tickerDiv.nextSibling);
                }

                const marketCap = data.market_cap ? `$${(data.market_cap / 1e9).toFixed(1)}B` : 'N/A';
                const currentPrice = data.current_price ? `$${data.current_price.toFixed(2)}` : 'N/A';
                const sector = data.sector || 'Unknown';

                previewPanel.innerHTML = `
                    <div class="flex items-center mb-2">
                        <svg class="w-4 h-4 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span class="text-sm font-medium text-blue-800">Company Data Found</span>
                    </div>
                    <div class="text-xs text-blue-700">
                        <p><strong>${data.company_name}</strong> (${data.ticker})</p>
                        <p>Sector: ${sector} | Market Cap: ${marketCap} | Price: ${currentPrice}</p>
                    </div>
                `;
            }

            function hideCompanyPreview() {
                const previewPanel = document.getElementById('company-preview');
                if (previewPanel) {
                    previewPanel.remove();
                }
            }

            // Form submission handler
            document.addEventListener('DOMContentLoaded', function() {
                const form = document.querySelector('form');
                if (form) {
                    form.addEventListener('submit', function(e) {
                        const formData = new FormData(form);
                        const ticker = formData.get('ticker');
                        
                        if (!ticker || ticker.trim() === '') {
                            e.preventDefault();
                            alert('Please enter a company ticker');
                            return false;
                        }
                        
                        // Show loading state (don't prevent default, let form submit naturally)
                        const submitBtn = form.querySelector('button[type="submit"]');
                        if (submitBtn) {
                            submitBtn.innerHTML = '<svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>Generating...';
                            submitBtn.disabled = true;
                        }
                        
                        // Let the form submit naturally to Flask
                        return true;
                    });
                }
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/model-results/<model_id>')
def model_results(model_id):
    if model_id not in MODEL_STORAGE:
        return f"<h1>Model not found</h1><p><a href='/'>Back to Home</a></p>"
    
    model = MODEL_STORAGE[model_id]
    result = model['result']
    
    # Generate the HTML sections
    download_section_html = generate_download_section(model)
    assumptions_html = format_assumptions_html(result)
    valuation_html = generate_valuation_html(result)
    
    return f'''
    <!DOCTYPE html>
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{model['type'].upper()} Model - {model['ticker']} - IB Modeling Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        }},
                        fontFamily: {{
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/" class="text-sm text-navy hover:text-navy/80 font-medium">Home</a>
                        <a href="/models" class="text-sm text-navy hover:text-navy/80 font-medium">View Models</a>
                        <a href="/generate-model" class="text-sm text-navy hover:text-navy/80 font-medium">Generate</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Success Banner -->
            <div class="bg-success-bg border border-success/20 rounded-xl p-4 mb-6">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-success mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div>
                        <h3 class="font-medium text-success">Model Generated Successfully</h3>
                        <p class="text-sm text-success/80">{model['type'].upper()} model for {result['company_name']} completed in {result['processing_time_seconds']}s</p>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-12 gap-6">
                <!-- Left Panel - Model Info -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="space-y-6">
                        <!-- Model Header -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <div class="flex items-center mb-4">
                                <div class="w-12 h-12 bg-navy/10 rounded-lg flex items-center justify-center mr-4">
                                    <svg class="w-6 h-6 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h2 class="text-lg font-semibold text-gray-900">{model['type'].upper()} Model</h2>
                                    <p class="text-sm text-gray-600">{result['company_name']} ({model['ticker']})</p>
                                </div>
                            </div>
                            <div class="text-xs text-gray-500">
                                <p>Generated: {model['timestamp'][:19].replace('T', ' at ')}</p>
                            </div>
                        </div>

                        <!-- Download Card -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Your Excel Model</h3>
                            
{download_section_html}
                        </div>

                        <!-- Key Assumptions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Key Assumptions</h3>
                            <div class="space-y-3">
{assumptions_html}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Panel - Valuation Results -->
                <div class="col-span-12 lg:col-span-8">
                    <div class="space-y-6">
                        <!-- Key Outputs -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h2 class="text-lg font-semibold text-gray-900 mb-6">Valuation Results</h2>
                            
{valuation_html}
                        </div>

                        <!-- Actions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Next Steps</h3>
                            <div class="flex flex-wrap gap-3">
                                <a href="/generate-model" class="bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors">
                                    Generate Another Model
                                </a>
                                <a href="/models" class="bg-white text-navy border border-navy px-4 py-2 rounded-lg font-medium hover:bg-navy hover:text-white transition-colors">
                                    View All Models
                                </a>
                                <a href="/" class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors">
                                    Home
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/models')
def list_models():
    models_html = ""
    for model_id, model in MODEL_STORAGE.items():
        models_html += f'''
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div class="flex items-center mb-4">
                <div class="w-10 h-10 bg-navy/10 rounded-lg flex items-center justify-center mr-3">
                    <svg class="w-5 h-5 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                </div>
                <div>
                    <h3 class="font-semibold text-gray-900">{model['type'].upper()} Model</h3>
                    <p class="text-sm text-gray-600">{model['ticker']}</p>
                </div>
            </div>
            <div class="mb-4">
                <div class="text-xs text-gray-500 mb-2">Generated: {model['timestamp'][:19].replace('T', ' at ')}</div>
                <div class="flex items-center">
                    <div class="w-2 h-2 bg-success rounded-full mr-2"></div>
                    <span class="text-sm text-success font-medium">Completed</span>
                </div>
            </div>
            <a href="/model-results/{model_id}" class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors inline-block text-center">
                View Results
            </a>
        </div>
        '''
    
    if not models_html:
        models_html = '''
        <div class="col-span-full">
            <div class="bg-white rounded-xl p-12 shadow-sm border border-gray-200 text-center">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No models generated yet</h3>
                <p class="text-gray-600 mb-6">Get started by creating your first financial model</p>
                <a href="/generate-model" class="bg-navy text-white px-6 py-3 rounded-lg font-medium hover:bg-navy/90 transition-colors inline-flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                    </svg>
                    Generate Your First Model
                </a>
            </div>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Models - IB Modeling Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        }},
                        fontFamily: {{
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/" class="text-sm text-navy hover:text-navy/80 font-medium">Home</a>
                        <a href="/generate-model" class="text-sm text-navy hover:text-navy/80 font-medium">Generate</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-gray-900">Generated Models</h2>
                <a href="/generate-model" class="bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors">
                    Generate New Model
                </a>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {models_html}
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting minimal app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
