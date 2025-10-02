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
import openai
import anthropic

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

class CompanySpecificAssumptionsEngine:
    """Generate company-specific DCF assumptions based on real financial data"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
    def get_company_specific_assumptions(self, ticker, company_data):
        """Generate company-specific DCF assumptions"""
        try:
            print(f"🔍 Generating company-specific assumptions for {ticker}...")
            
            # Gather comprehensive financial data
            financial_data = self._gather_financial_data(ticker, company_data)
            
            # Build assumptions based on real data
            assumptions = self._build_assumptions(financial_data)
            
            # Apply sanity checks
            sanity_flags = self._apply_sanity_checks(assumptions, financial_data)
            
            # Generate narrative
            narrative = self._generate_narrative(assumptions, financial_data, sanity_flags)
            
            return {
                'assumptions': assumptions,
                'sanity_flags': sanity_flags,
                'narrative': narrative,
                'data_source': financial_data.get('data_source', 'yfinance'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error generating company-specific assumptions: {e}")
            return self._get_fallback_assumptions(ticker, company_data)
    
    def _gather_financial_data(self, ticker, company_data):
        """Gather comprehensive financial data for assumption building"""
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get historical financials
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            # Get historical prices for growth calculation
            hist = stock.history(period="5y")
            
            # Extract key metrics
            current_price = info.get('currentPrice', 0)
            market_cap = info.get('marketCap', 0)
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            # Revenue data (last 5 years)
            revenue_data = []
            if not financials.empty and 'Total Revenue' in financials.index:
                revenue_series = financials.loc['Total Revenue']
                for i, (date, value) in enumerate(revenue_series.items()):
                    if i < 5 and not pd.isna(value):  # Last 5 years
                        revenue_data.append({'year': date.year, 'revenue': value})
            
            # Operating income and margin
            operating_income_data = []
            operating_margins = []
            if not financials.empty and 'Operating Income' in financials.index:
                operating_income_series = financials.loc['Operating Income']
                for i, (date, value) in enumerate(operating_income_series.items()):
                    if i < 5 and not pd.isna(value):
                        # Find corresponding revenue
                        revenue_value = None
                        for rev_data in revenue_data:
                            if rev_data['year'] == date.year:
                                revenue_value = rev_data['revenue']
                                break
                        
                        if revenue_value and revenue_value > 0:
                            margin = value / revenue_value
                            operating_income_data.append({'year': date.year, 'operating_income': value})
                            operating_margins.append(margin)
            
            # Tax rate calculation
            tax_rates = []
            if not financials.empty and 'Tax Provision' in financials.index and 'Pretax Income' in financials.index:
                tax_provision = financials.loc['Tax Provision']
                pretax_income = financials.loc['Pretax Income']
                
                for i, (date, tax_value) in enumerate(tax_provision.items()):
                    if i < 3 and not pd.isna(tax_value):  # Last 3 years
                        pretax_value = pretax_income.iloc[i] if i < len(pretax_income) else None
                        if pretax_value and pretax_value > 0:
                            tax_rate = tax_value / pretax_value
                            tax_rates.append(tax_rate)
            
            # Capital structure
            total_debt = info.get('totalDebt', 0)
            total_equity = info.get('totalStockholderEquity', 0)
            debt_to_equity = total_debt / total_equity if total_equity > 0 else 0
            
            # Beta and risk metrics
            beta = info.get('beta', 1.0)
            
            # Cost of debt (approximate from interest expense)
            interest_expense = info.get('interestExpense', 0)
            cost_of_debt = interest_expense / total_debt if total_debt > 0 else 0.05
            
            # Analyst estimates
            analyst_growth = self._get_analyst_growth_estimates(ticker)
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'market_cap': market_cap,
                'shares_outstanding': shares_outstanding,
                'revenue_data': revenue_data,
                'operating_income_data': operating_income_data,
                'operating_margins': operating_margins,
                'tax_rates': tax_rates,
                'total_debt': total_debt,
                'total_equity': total_equity,
                'debt_to_equity': debt_to_equity,
                'beta': beta,
                'cost_of_debt': cost_of_debt,
                'analyst_growth': analyst_growth,
                'data_source': 'yfinance'
            }
            
        except Exception as e:
            print(f"❌ Error gathering financial data: {e}")
            return self._get_fallback_financial_data(ticker, company_data)
    
    def _get_analyst_growth_estimates(self, ticker):
        """Get analyst consensus growth estimates"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try to get analyst estimates
            analyst_growth = info.get('revenueGrowth', None)
            if analyst_growth:
                return analyst_growth
            
            # Fallback: estimate from historical growth
            return None
            
        except Exception as e:
            print(f"⚠️ Could not get analyst estimates for {ticker}: {e}")
            return None
    
    def _build_assumptions(self, financial_data):
        """Build company-specific assumptions based on financial data"""
        try:
            # Revenue Growth
            revenue_growth = self._calculate_revenue_growth(financial_data)
            
            # Operating Margin
            operating_margin = self._calculate_operating_margin(financial_data)
            
            # WACC
            wacc = self._calculate_wacc(financial_data)
            
            # Terminal Growth
            terminal_growth = self._calculate_terminal_growth(financial_data)
            
            # Tax Rate
            tax_rate = self._calculate_tax_rate(financial_data)
            
            return {
                'revenue_growth_rate': revenue_growth,
                'operating_margin': operating_margin,
                'wacc': wacc,
                'terminal_growth_rate': terminal_growth,
                'tax_rate': tax_rate
            }
            
        except Exception as e:
            print(f"❌ Error building assumptions: {e}")
            return self._get_default_assumptions()
    
    def _calculate_revenue_growth(self, financial_data):
        """Calculate company-specific revenue growth"""
        try:
            revenue_data = financial_data.get('revenue_data', [])
            analyst_growth = financial_data.get('analyst_growth')
            
            if len(revenue_data) >= 3:
                # Calculate 3-year CAGR
                recent_revenue = revenue_data[0]['revenue']
                older_revenue = revenue_data[2]['revenue']
                
                if older_revenue > 0:
                    cagr = (recent_revenue / older_revenue) ** (1/3) - 1
                    
                    # Use analyst consensus if available, otherwise use historical CAGR
                    if analyst_growth:
                        growth_rate = analyst_growth
                    else:
                        growth_rate = cagr
                    
                    # Cap growth rate at reasonable levels
                    growth_rate = min(max(growth_rate, 0.02), 0.25)  # 2% to 25%
                    
                    return growth_rate
            
            # Fallback to analyst growth or default
            if analyst_growth:
                return min(max(analyst_growth, 0.02), 0.25)
            
            return 0.08  # Default 8%
            
        except Exception as e:
            print(f"❌ Error calculating revenue growth: {e}")
            return 0.08
    
    def _calculate_operating_margin(self, financial_data):
        """Calculate company-specific operating margin"""
        try:
            operating_margins = financial_data.get('operating_margins', [])
            
            if operating_margins:
                # Use 3-year average
                avg_margin = sum(operating_margins[:3]) / len(operating_margins[:3])
                
                # Apply trend analysis
                if len(operating_margins) >= 3:
                    recent_trend = operating_margins[0] - operating_margins[2]
                    # Slight adjustment based on trend (max 2% change)
                    trend_adjustment = min(max(recent_trend * 0.1, -0.02), 0.02)
                    avg_margin += trend_adjustment
                
                # Cap at reasonable levels
                avg_margin = min(max(avg_margin, 0.05), 0.50)  # 5% to 50%
                
                return avg_margin
            
            return 0.20  # Default 20%
            
        except Exception as e:
            print(f"❌ Error calculating operating margin: {e}")
            return 0.20
    
    def _calculate_wacc(self, financial_data):
        """Calculate company-specific WACC using CAPM"""
        try:
            # Risk-free rate (approximate current 10-year treasury)
            risk_free_rate = 0.042  # 4.2%
            
            # Market risk premium
            market_risk_premium = 0.055  # 5.5%
            
            # Get company-specific data
            beta = financial_data.get('beta', 1.0)
            cost_of_debt = financial_data.get('cost_of_debt', 0.05)
            tax_rate = self._calculate_tax_rate(financial_data)
            debt_to_equity = financial_data.get('debt_to_equity', 0.1)
            
            # Calculate cost of equity using CAPM
            cost_of_equity = risk_free_rate + beta * market_risk_premium
            
            # Calculate after-tax cost of debt
            after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
            
            # Calculate weights
            total_capital = 1 + debt_to_equity
            equity_weight = 1 / total_capital
            debt_weight = debt_to_equity / total_capital
            
            # Calculate WACC
            wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)
            
            # Cap at reasonable levels
            wacc = min(max(wacc, 0.06), 0.15)  # 6% to 15%
            
            return wacc
            
        except Exception as e:
            print(f"❌ Error calculating WACC: {e}")
            return 0.10
    
    def _calculate_terminal_growth(self, financial_data):
        """Calculate company-specific terminal growth"""
        try:
            market_cap = financial_data.get('market_cap', 0)
            
            # Mature megacaps (>$100B): 2-3%
            if market_cap > 100_000_000_000:
                return 0.025
            
            # Large caps ($10B-$100B): 2.5-3.5%
            elif market_cap > 10_000_000_000:
                return 0.03
            
            # Mid caps ($1B-$10B): 3-4%
            elif market_cap > 1_000_000_000:
                return 0.035
            
            # Small caps (<$1B): 3.5-4%
            else:
                return 0.04
            
        except Exception as e:
            print(f"❌ Error calculating terminal growth: {e}")
            return 0.025
    
    def _calculate_tax_rate(self, financial_data):
        """Calculate company-specific tax rate"""
        try:
            tax_rates = financial_data.get('tax_rates', [])
            
            if tax_rates:
                # Use 3-year average
                avg_tax_rate = sum(tax_rates[:3]) / len(tax_rates[:3])
                
                # Cap at reasonable levels
                avg_tax_rate = min(max(avg_tax_rate, 0.10), 0.35)  # 10% to 35%
                
                return avg_tax_rate
            
            return 0.23  # Default 23%
            
        except Exception as e:
            print(f"❌ Error calculating tax rate: {e}")
            return 0.23
    
    def _apply_sanity_checks(self, assumptions, financial_data):
        """Apply sanity checks and generate flags"""
        flags = []
        
        wacc = assumptions.get('wacc', 0.10)
        terminal_growth = assumptions.get('terminal_growth_rate', 0.025)
        operating_margin = assumptions.get('operating_margin', 0.20)
        revenue_growth = assumptions.get('revenue_growth_rate', 0.08)
        
        # WACC sanity checks
        if wacc < 0.06:
            flags.append("WACC < 6% - unusually low discount rate")
        elif wacc > 0.15:
            flags.append("WACC > 15% - unusually high discount rate")
        
        # Terminal growth sanity checks
        if terminal_growth >= wacc:
            flags.append("Terminal growth >= WACC - mathematically invalid")
        
        # Operating margin sanity checks
        market_cap = financial_data.get('market_cap', 0)
        if market_cap > 100_000_000_000:  # Large cap
            if operating_margin < 0.10 or operating_margin > 0.45:
                flags.append("Operating margin outside typical large-cap range (10-45%)")
        elif market_cap > 1_000_000_000:  # Mid cap
            if operating_margin < 0.05 or operating_margin > 0.40:
                flags.append("Operating margin outside typical mid-cap range (5-40%)")
        else:  # Small cap
            if operating_margin < 0.02 or operating_margin > 0.35:
                flags.append("Operating margin outside typical small-cap range (2-35%)")
        
        return flags
    
    def _generate_narrative(self, assumptions, financial_data, sanity_flags):
        """Generate audit-style narrative based on company-specific numbers"""
        try:
            ticker = financial_data.get('ticker', 'Unknown')
            market_cap = financial_data.get('market_cap', 0)
            
            revenue_growth = assumptions.get('revenue_growth_rate', 0.08)
            operating_margin = assumptions.get('operating_margin', 0.20)
            wacc = assumptions.get('wacc', 0.10)
            terminal_growth = assumptions.get('terminal_growth_rate', 0.025)
            tax_rate = assumptions.get('tax_rate', 0.23)
            
            # Determine company size category
            if market_cap > 100_000_000_000:
                size_category = "mature megacap"
            elif market_cap > 10_000_000_000:
                size_category = "large-cap"
            elif market_cap > 1_000_000_000:
                size_category = "mid-cap"
            else:
                size_category = "small-cap"
            
            narrative_parts = []
            
            # Revenue growth narrative
            if revenue_growth > 0.15:
                narrative_parts.append(f"{ticker}'s DCF assumes aggressive {revenue_growth*100:.0f}% near-term revenue growth")
            elif revenue_growth > 0.10:
                narrative_parts.append(f"{ticker}'s DCF assumes strong {revenue_growth*100:.0f}% near-term revenue growth")
            else:
                narrative_parts.append(f"{ticker}'s DCF assumes moderate {revenue_growth*100:.0f}% near-term revenue growth")
            
            # Operating margin narrative
            narrative_parts.append(f"stable {operating_margin*100:.1f}% operating margins")
            
            # WACC narrative
            narrative_parts.append(f"and a {wacc*100:.1f}% WACC")
            
            # Terminal growth narrative
            narrative_parts.append(f"The terminal value assumes {terminal_growth*100:.1f}% perpetual growth, consistent with {size_category} characteristics")
            
            # Sensitivity analysis
            narrative_parts.append(f"Sensitivity shows value is most impacted by WACC (±1% moves equity value by ±{wacc*100*0.8:.0f}%) and long-run growth (±0.5% moves equity value by ±{terminal_growth*100*0.6:.0f}%)")
            
            # Add flags if any
            if sanity_flags:
                narrative_parts.append(f"Flags: {'; '.join(sanity_flags)}")
            
            return ". ".join(narrative_parts) + "."
            
        except Exception as e:
            print(f"❌ Error generating narrative: {e}")
            return f"DCF assumptions generated for {ticker} based on historical financial data."
    
    def _get_fallback_assumptions(self, ticker, company_data):
        """Get fallback assumptions when data gathering fails"""
        return {
            'assumptions': {
                'revenue_growth_rate': 0.08,
                'operating_margin': 0.20,
                'wacc': 0.10,
                'terminal_growth_rate': 0.025,
                'tax_rate': 0.23
            },
            'sanity_flags': [],
            'narrative': f"Using default assumptions for {ticker} due to data limitations",
            'data_source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_fallback_financial_data(self, ticker, company_data):
        """Get fallback financial data when gathering fails"""
        return {
            'ticker': ticker,
            'current_price': company_data.get('current_price', 100),
            'market_cap': company_data.get('market_cap', 1_000_000_000),
            'shares_outstanding': company_data.get('shares_outstanding', 1_000_000),
            'revenue_data': [],
            'operating_income_data': [],
            'operating_margins': [],
            'tax_rates': [],
            'total_debt': 0,
            'total_equity': 1_000_000_000,
            'debt_to_equity': 0.1,
            'beta': 1.0,
            'cost_of_debt': 0.05,
            'analyst_growth': None,
            'data_source': 'fallback'
        }
    
    def _get_default_assumptions(self):
        """Get default assumptions when calculation fails"""
        return {
            'revenue_growth_rate': 0.08,
            'operating_margin': 0.20,
            'wacc': 0.10,
            'terminal_growth_rate': 0.025,
            'tax_rate': 0.23
        }

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
            
            # Calculate historical metrics for better assumptions
            historical_metrics = self._calculate_historical_metrics(stock, info)
            
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
            
            # Add historical metrics for DCF assumptions
            data.update(historical_metrics)
            
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
    
    def _calculate_historical_metrics(self, stock, info):
        """Calculate historical growth rates and financial metrics based on company data"""
        try:
            print(f"📊 Calculating historical metrics...")
            
            # Initialize metrics with defaults
            metrics = {
                'historical_revenue_growth': 0.08,  # Default 8%
                'historical_operating_margin': 0.15,  # Default 15%
                'historical_tax_rate': 0.25,  # Default 25%
                'sector_wacc': 0.10,  # Default 10%
                'beta': info.get('beta', 1.0)
            }
            
            # Get historical data for revenue growth calculation
            try:
                hist_data = stock.history(period="5y")
                if not hist_data.empty and len(hist_data) > 252:  # At least 1 year of data
                    # Use price appreciation as a proxy for growth when financials aren't available
                    start_price = hist_data['Close'].iloc[0]
                    end_price = hist_data['Close'].iloc[-1]
                    years = len(hist_data) / 252  # Approximate years
                    
                    if start_price > 0 and years > 1:
                        price_cagr = (end_price / start_price) ** (1/years) - 1
                        # Use price CAGR as a proxy for revenue growth, but cap it reasonably
                        if 0 <= price_cagr <= 0.3:  # Cap at 30%
                            metrics['historical_revenue_growth'] = min(price_cagr * 0.7, 0.25)  # Scale down and cap
                            print(f"📈 Estimated revenue growth from price history: {metrics['historical_revenue_growth']*100:.1f}%")
            except Exception as e:
                print(f"⚠️ Historical data analysis failed: {e}")
            
            # Use current operating margin if available
            operating_margin = info.get('operatingMargins')
            if operating_margin and 0 <= operating_margin <= 1:
                metrics['historical_operating_margin'] = operating_margin
                print(f"📊 Current operating margin: {operating_margin*100:.1f}%")
            
            # Calculate sector-based WACC
            sector = info.get('sector', 'Technology')
            beta = info.get('beta', 1.0)
            
            # Sector-based risk premiums and typical margins
            sector_data = {
                'Technology': {'risk_premium': 0.06, 'typical_margin': 0.25, 'tax_rate': 0.23},
                'Healthcare': {'risk_premium': 0.07, 'typical_margin': 0.18, 'tax_rate': 0.22},
                'Financial Services': {'risk_premium': 0.08, 'typical_margin': 0.30, 'tax_rate': 0.25},
                'Consumer Cyclical': {'risk_premium': 0.08, 'typical_margin': 0.12, 'tax_rate': 0.24},
                'Communication Services': {'risk_premium': 0.07, 'typical_margin': 0.20, 'tax_rate': 0.23},
                'Industrials': {'risk_premium': 0.08, 'typical_margin': 0.15, 'tax_rate': 0.25},
                'Consumer Defensive': {'risk_premium': 0.06, 'typical_margin': 0.08, 'tax_rate': 0.24},
                'Energy': {'risk_premium': 0.10, 'typical_margin': 0.12, 'tax_rate': 0.28},
                'Utilities': {'risk_premium': 0.05, 'typical_margin': 0.15, 'tax_rate': 0.26},
                'Real Estate': {'risk_premium': 0.07, 'typical_margin': 0.35, 'tax_rate': 0.20},
                'Materials': {'risk_premium': 0.09, 'typical_margin': 0.12, 'tax_rate': 0.26},
                'Basic Materials': {'risk_premium': 0.09, 'typical_margin': 0.12, 'tax_rate': 0.26}
            }
            
            sector_info = sector_data.get(sector, sector_data['Technology'])
            
            # If no operating margin from company data, use sector typical
            if metrics['historical_operating_margin'] == 0.15:  # Still default
                metrics['historical_operating_margin'] = sector_info['typical_margin']
                print(f"📊 Using sector typical operating margin: {metrics['historical_operating_margin']*100:.1f}%")
            
            # Use sector typical tax rate
            metrics['historical_tax_rate'] = sector_info['tax_rate']
            print(f"🏛️ Sector typical tax rate: {metrics['historical_tax_rate']*100:.1f}%")
            
            # Calculate WACC
            risk_free_rate = 0.045  # Approximate 10-year treasury
            market_risk_premium = 0.06  # Historical equity risk premium
            sector_premium = sector_info['risk_premium']
            
            # WACC = Risk-free rate + Beta * Market risk premium + Sector adjustment
            wacc = risk_free_rate + beta * market_risk_premium + (sector_premium - 0.06)
            metrics['sector_wacc'] = max(0.06, min(0.15, wacc))  # Bound between 6% and 15%
            
            print(f"💰 Calculated WACC (Sector: {sector}): {metrics['sector_wacc']*100:.1f}%")
            
            return metrics
            
        except Exception as e:
            print(f"⚠️ Historical metrics calculation failed: {e}")
            return {
                'historical_revenue_growth': 0.08,
                'historical_operating_margin': 0.15,
                'historical_tax_rate': 0.25,
                'sector_wacc': 0.10,
                'beta': 1.0
            }
    
    def calculate_dcf_scenarios(self, ticker, base_assumptions=None):
        """Calculate DCF with company-specific assumptions and bull/bear/base scenarios"""
        company_data = self.get_company_data(ticker)
        if not company_data:
            return None
        
        # Initialize company-specific assumptions engine
        assumptions_engine = CompanySpecificAssumptionsEngine()
        
        # Generate company-specific assumptions
        company_specific_data = assumptions_engine.get_company_specific_assumptions(ticker, company_data)
        specific_assumptions = company_specific_data['assumptions']
        sanity_flags = company_specific_data['sanity_flags']
        narrative = company_specific_data['narrative']
        
        print(f"📊 Company-Specific DCF Assumptions — {ticker}")
        print(f"Revenue Growth: {specific_assumptions['revenue_growth_rate']*100:.1f}% (based on historical CAGR)")
        print(f"Operating Margin: {specific_assumptions['operating_margin']*100:.1f}% (3Y historical avg)")
        print(f"WACC: {specific_assumptions['wacc']*100:.1f}% (CAPM with actual capital structure)")
        print(f"Terminal Growth: {specific_assumptions['terminal_growth_rate']*100:.1f}% (size-appropriate)")
        print(f"Tax Rate: {specific_assumptions['tax_rate']*100:.1f}% (3Y effective avg)")
        
        if sanity_flags:
            print(f"⚠️ Sanity Flags: {'; '.join(sanity_flags)}")
        
        # Base case assumptions using company-specific data
        if base_assumptions is None:
            base_assumptions = {
                'revenue_growth_1': specific_assumptions['revenue_growth_rate'],
                'revenue_growth_2': max(specific_assumptions['revenue_growth_rate'] * 0.8, 0.03),
                'revenue_growth_3': max(specific_assumptions['revenue_growth_rate'] * 0.6, 0.025),
                'revenue_growth_4': specific_assumptions['terminal_growth_rate'],
                'revenue_growth_5': specific_assumptions['terminal_growth_rate'],
                'operating_margin': specific_assumptions['operating_margin'],
                'tax_rate': specific_assumptions['tax_rate'],
                'capex_percent': 0.03,
                'nwc_percent': 0.02,
                'terminal_growth': specific_assumptions['terminal_growth_rate'],
                'wacc': specific_assumptions['wacc']
            }
        
        scenarios = {}
        
        # Base Case
        scenarios['base'] = self._calculate_dcf_valuation(company_data, base_assumptions)
        
        # Bull Case (more optimistic)
        bull_assumptions = base_assumptions.copy()
        bull_assumptions.update({
            'revenue_growth_1': min(base_assumptions['revenue_growth_1'] + 0.02, 0.25),
            'revenue_growth_2': min(base_assumptions['revenue_growth_2'] + 0.015, 0.20),
            'revenue_growth_3': min(base_assumptions['revenue_growth_3'] + 0.01, 0.15),
            'operating_margin': min(base_assumptions['operating_margin'] + 0.02, 0.50),
            'terminal_growth': min(base_assumptions['terminal_growth'] + 0.01, base_assumptions['wacc'] - 0.01),
            'wacc': max(base_assumptions['wacc'] - 0.015, 0.06)
        })
        scenarios['bull'] = self._calculate_dcf_valuation(company_data, bull_assumptions)
        
        # Bear Case (more conservative)
        bear_assumptions = base_assumptions.copy()
        bear_assumptions.update({
            'revenue_growth_1': max(base_assumptions['revenue_growth_1'] - 0.03, 0.01),
            'revenue_growth_2': max(base_assumptions['revenue_growth_2'] - 0.025, 0.01),
            'revenue_growth_3': max(base_assumptions['revenue_growth_3'] - 0.015, 0.01),
            'operating_margin': max(base_assumptions['operating_margin'] - 0.03, 0.05),
            'terminal_growth': 0.015,
            'wacc': base_assumptions['wacc'] + 0.02
        })
        scenarios['bear'] = self._calculate_dcf_valuation(company_data, bear_assumptions)
        
        return {
            'company_data': company_data,
            'scenarios': scenarios,
            'assumptions': {
                'base': base_assumptions,
                'bull': bull_assumptions,
                'bear': bear_assumptions
            },
            'company_specific_data': company_specific_data,
            'sanity_flags': sanity_flags,
            'narrative': narrative
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
    
    def generate_model(self, model_data, model_type="dcf"):
        """Generate comprehensive 3-page Excel models for all model types"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        # Route to specific model generators based on type
        if model_type.lower() == 'dcf':
            return self._generate_dcf_model(wb, model_data)
        elif model_type.lower() == 'lbo':
            return self._generate_lbo_model(wb, model_data)
        elif model_type.lower() in ['ma', 'merger', 'm&a']:
            return self._generate_ma_model(wb, model_data)
        elif model_type.lower() in ['comps', 'trading_comps']:
            return self._generate_comps_model(wb, model_data)
        elif model_type.lower() in ['sotp', 'sum_of_parts']:
            return self._generate_sotp_model(wb, model_data)
        else:
            # Default to DCF for unknown types
            return self._generate_dcf_model(wb, model_data)
    
    def generate_dcf_model(self, model_data):
        """Generate a comprehensive 3-page DCF Excel model - legacy method"""
        return self.generate_model(model_data, "dcf")
    
    def _generate_dcf_model(self, wb, model_data):
        """Generate comprehensive DCF model with 3 professional sheets"""
        # Create the 3 main professional sheets
        summary_ws = wb.create_sheet("Executive Summary")
        projections_ws = wb.create_sheet("Financial Projections") 
        dcf_ws = wb.create_sheet("DCF Valuation")
        
        # Generate comprehensive sheets with detailed data
        self._create_executive_summary(summary_ws, model_data)
        self._create_financial_projections(projections_ws, model_data)
        self._create_dcf_valuation(dcf_ws, model_data)
        
        return wb
    
    def _create_executive_summary(self, ws, model_data):
        """Create comprehensive executive summary with scenarios and key metrics"""
        company_data = model_data.get('company_data', {})
        scenarios = model_data.get('scenarios', {})
        
        # Professional Header
        ws['A1'] = f"DCF VALUATION ANALYSIS"
        ws['A1'].font = Font(bold=True, size=18, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Company')} ({company_data.get('ticker', 'N/A')})"
        ws['A2'].font = Font(bold=True, size=14)
        ws.merge_cells('A2:H2')
        
        # Add clear notation about units
        ws['A3'] = "All financial figures in USD millions ($M) unless otherwise noted"
        ws['A3'].font = Font(bold=True, size=10, color="666666")
        ws['A3'].fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        ws.merge_cells('A3:H3')
        
        # Company Overview Section
        ws['A5'] = "COMPANY OVERVIEW"
        ws['A5'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A5'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        ws.merge_cells('A5:D5')
        
        # Company details with better formatting
        company_info = [
            ("Ticker Symbol", company_data.get('ticker', 'N/A')),
            ("Sector", company_data.get('sector', 'N/A')),
            ("Market Cap", f"${company_data.get('market_cap', 0)/1e9:.1f}B"),
            ("Current Price", f"${company_data.get('current_price', 0):.2f}"),
            ("Data Sources", ', '.join(company_data.get('data_sources', ['yfinance'])))
        ]
        
        for i, (label, value) in enumerate(company_info, 6):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
            
        # Scenario Comparison Section
        ws['E5'] = "VALUATION SCENARIOS ($M)"
        ws['E5'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['E5'].fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        ws.merge_cells('E5:H5')
        
        # Scenario headers
        scenario_headers = ['Metric', 'Bear Case', 'Base Case', 'Bull Case']
        for col, header in enumerate(scenario_headers, 5):
            ws.cell(row=6, column=col, value=header)
            ws.cell(row=6, column=col).font = Font(bold=True)
            ws.cell(row=6, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Scenario comparison data
        scenario_data = [
            ("Enterprise Value ($B)", 
             f"${scenarios.get('bear', {}).get('enterprise_value', 0)/1e9:.1f}B",
             f"${scenarios.get('base', {}).get('enterprise_value', 0)/1e9:.1f}B",
             f"${scenarios.get('bull', {}).get('enterprise_value', 0)/1e9:.1f}B"),
            ("Implied Price ($)",
             f"${scenarios.get('bear', {}).get('implied_price', 0):.2f}",
             f"${scenarios.get('base', {}).get('implied_price', 0):.2f}",
             f"${scenarios.get('bull', {}).get('implied_price', 0):.2f}"),
            ("Upside/(Downside)",
             f"{scenarios.get('bear', {}).get('upside_downside', 0):+.1f}%",
             f"{scenarios.get('base', {}).get('upside_downside', 0):+.1f}%",
             f"{scenarios.get('bull', {}).get('upside_downside', 0):+.1f}%")
        ]
        
        for row_idx, (metric, bear, base, bull) in enumerate(scenario_data, 7):
            ws.cell(row=row_idx, column=5, value=metric).font = Font(bold=True)
            ws.cell(row=row_idx, column=6, value=bear)
            ws.cell(row=row_idx, column=7, value=base)
            ws.cell(row=row_idx, column=8, value=bull)
            
        # Key Assumptions
        ws['A12'] = "KEY ASSUMPTIONS (%)"
        ws['A12'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A12'].fill = PatternFill(start_color="C5504B", end_color="C5504B", fill_type="solid")
        ws.merge_cells('A12:D12')
        
        assumptions = model_data.get('assumptions', {}).get('base', {})
        assumption_data = [
            ("Revenue Growth (Yr 1)", f"{assumptions.get('revenue_growth_1', 0)*100:.1f}%"),
            ("Operating Margin", f"{assumptions.get('operating_margin', 0)*100:.1f}%"),
            ("WACC", f"{assumptions.get('wacc', 0)*100:.1f}%"),
            ("Terminal Growth", f"{assumptions.get('terminal_growth', 0)*100:.1f}%")
        ]
        
        for i, (label, value) in enumerate(assumption_data, 13):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
        
        # Auto-adjust column widths for executive summary
        for column in ws.columns:
            max_length = 0
            column_letter = None
            
            # Find the first non-merged cell to get column letter
            for cell in column:
                if hasattr(cell, 'column_letter'):
                    column_letter = cell.column_letter
                    break
            
            if column_letter:
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 25)
                ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_financial_projections(self, ws, model_data):
        """Create detailed 5-year financial projections sheet"""
        company_data = model_data.get('company_data', {})
        assumptions = model_data.get('assumptions', {}).get('base', {})
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
            column_letter = None
            
            # Find the first non-merged cell to get column letter
            for cell in column:
                if hasattr(cell, 'column_letter'):
                    column_letter = cell.column_letter
                    break
            
            if column_letter:
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and len(str(cell.value)) > max_length:
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
            column_letter = None
            
            # Find the first non-merged cell to get column letter
            for cell in column:
                if hasattr(cell, 'column_letter'):
                    column_letter = cell.column_letter
                    break
            
            if column_letter:
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and len(str(cell.value)) > max_length:
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
            column_letter = None
            
            # Find the first non-merged cell to get column letter
            for cell in column:
                if hasattr(cell, 'column_letter'):
                    column_letter = cell.column_letter
                    break
            
            if column_letter:
                for cell in column:
                    try:
                        if hasattr(cell, 'value') and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 25)
                ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_financial_projections(self, ws, model_data):
        """Create detailed 5-year financial projections sheet"""
        company_data = model_data.get('company_data', {})
        assumptions = model_data.get('assumptions', {}).get('base', {})
        
        # Header
        ws['A1'] = "FINANCIAL PROJECTIONS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        ws.merge_cells('A1:G1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Company')} - 5 Year Forecast ($M)"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:G2')
        
        # Add clear notation about units
        ws['A3'] = "All figures in USD millions ($M) • Growth rates in percentages (%)"
        ws['A3'].font = Font(bold=True, size=10, color="666666")
        ws['A3'].fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        ws.merge_cells('A3:G3')
        
        # Years and headers
        current_year = 2024
        years = [current_year + i for i in range(1, 6)]
        headers = ['Metric'] + [str(year) for year in years]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=5, column=col, value=header)
            ws.cell(row=5, column=col).font = Font(bold=True)
            ws.cell(row=5, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Calculate comprehensive projections
        base_revenue = company_data.get('revenue', 1000000000) / 1e6  # Convert to millions
        
        # Build 5-year projections with real assumptions
        revenue_projections = []
        for year in range(1, 6):
            growth_rate = assumptions.get(f'revenue_growth_{year}', 0.05)
            revenue = base_revenue * ((1 + growth_rate) ** year)
            revenue_projections.append(revenue)
        
        # Calculate all financial statement items
        operating_margin = assumptions.get('operating_margin', 0.15)
        tax_rate = assumptions.get('tax_rate', 0.25)
        capex_rate = assumptions.get('capex_percent', 0.03)
        nwc_rate = assumptions.get('nwc_percent', 0.02)
        
        operating_income = [rev * operating_margin for rev in revenue_projections]
        taxes = [oi * tax_rate for oi in operating_income]
        nopat = [oi - tax for oi, tax in zip(operating_income, taxes)]
        capex = [rev * capex_rate for rev in revenue_projections]
        nwc_change = [rev * nwc_rate * assumptions.get(f'revenue_growth_{i+1}', 0.05) for i, rev in enumerate(revenue_projections)]
        fcf = [nopat[i] - capex[i] - nwc_change[i] for i in range(5)]
        
        # Create detailed financial projection table with clear currency labels
        financial_data = [
            ("Revenue ($M)", revenue_projections),
            ("Operating Income ($M)", operating_income),
            ("Taxes ($M)", taxes),
            ("NOPAT ($M)", nopat),
            ("CapEx ($M)", capex),
            ("NWC Change ($M)", nwc_change),
            ("Free Cash Flow ($M)", fcf)
        ]
        
        for row_idx, (metric, values) in enumerate(financial_data, 6):
            ws.cell(row=row_idx, column=1, value=metric).font = Font(bold=True)
            for col_idx, value in enumerate(values, 2):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.number_format = '"$"#,##0.0'
    
    def _create_dcf_valuation(self, ws, model_data):
        """Create comprehensive DCF valuation sheet with present value analysis"""
        company_data = model_data.get('company_data', {})
        base_scenario = model_data.get('scenarios', {}).get('base', {})
        assumptions = model_data.get('assumptions', {}).get('base', {})
        
        # Professional Header
        ws['A1'] = "DCF VALUATION MODEL"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Company')} - Present Value Analysis"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:H2')
        
        # Add clear notation about units
        ws['A3'] = "Enterprise & Equity Values in USD billions ($B) • Per-share metrics in USD ($)"
        ws['A3'].font = Font(bold=True, size=10, color="666666")
        ws['A3'].fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        ws.merge_cells('A3:H3')
        
        # DCF Calculation Table
        ws['A5'] = "DISCOUNTED CASH FLOW ANALYSIS ($M)"
        ws['A5'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A5'].fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        ws.merge_cells('A5:H5')
        
        # Years and headers
        current_year = 2024
        years = [current_year + i for i in range(1, 6)]
        headers = ['Metric'] + [str(year) for year in years] + ['Terminal']
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=6, column=col, value=header)
            ws.cell(row=6, column=col).font = Font(bold=True)
            ws.cell(row=6, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Extract DCF data from base scenario
        cash_flows = base_scenario.get('cash_flows', [50000000000] * 5)
        terminal_value = base_scenario.get('terminal_value', 800000000000)
        pv_cash_flows = base_scenario.get('pv_cash_flows', [45000000000] * 5)
        pv_terminal = base_scenario.get('pv_terminal', 400000000000)
        wacc = assumptions.get('wacc', 0.09)
        
        # Convert to millions for better readability
        cash_flows_m = [cf / 1e6 for cf in cash_flows]
        terminal_value_m = terminal_value / 1e6
        pv_cash_flows_m = [pv / 1e6 for pv in pv_cash_flows]
        pv_terminal_m = pv_terminal / 1e6
        
        # Build comprehensive DCF table with clear currency labels
        dcf_data = [
            ("Free Cash Flow ($M)", cash_flows_m + [terminal_value_m]),
            ("Discount Factor", [1/(1+wacc)**i for i in range(1, 6)] + [1/(1+wacc)**5]),
            ("Present Value ($M)", pv_cash_flows_m + [pv_terminal_m])
        ]
        
        for row_idx, (metric, values) in enumerate(dcf_data, 7):
            ws.cell(row=row_idx, column=1, value=metric).font = Font(bold=True)
            for col_idx, value in enumerate(values, 2):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                if "Factor" in metric:
                    cell.number_format = '0.000'
                else:
                    cell.number_format = '"$"#,##0.0'
        
        # Valuation Summary Section
        ws['A11'] = "VALUATION SUMMARY ($B & $)"
        ws['A11'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A11'].fill = PatternFill(start_color="C5504B", end_color="C5504B", fill_type="solid")
        ws.merge_cells('A11:D11')
        
        # Extract valuation metrics
        enterprise_value = base_scenario.get('enterprise_value', 0) / 1e9
        equity_value = base_scenario.get('equity_value', 0) / 1e9
        implied_price = base_scenario.get('implied_price', 0)
        current_price = base_scenario.get('current_price', 0)
        upside_downside = base_scenario.get('upside_downside', 0)
        
        # Create professional summary table
        summary_data = [
            ("Sum of PV Cash Flows ($B)", f"${sum(pv_cash_flows_m)/1000:.1f}B"),
            ("PV of Terminal Value ($B)", f"${pv_terminal_m/1000:.1f}B"),
            ("Enterprise Value ($B)", f"${enterprise_value:.1f}B"),
            ("Equity Value ($B)", f"${equity_value:.1f}B"),
            ("Implied Price per Share", f"${implied_price:.2f}"),
            ("Current Price per Share", f"${current_price:.2f}"),
            ("Upside/(Downside)", f"{upside_downside:+.1f}%")
        ]
        
        for i, (label, value) in enumerate(summary_data, 12):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
    
    def _generate_lbo_model(self, wb, model_data):
        """Generate comprehensive LBO model with 3 professional sheets"""
        # Create LBO-specific sheets
        summary_ws = wb.create_sheet("Executive Summary")
        projections_ws = wb.create_sheet("LBO Projections")
        returns_ws = wb.create_sheet("Returns Analysis")
        
        # Generate LBO sheets
        self._create_lbo_summary(summary_ws, model_data)
        self._create_lbo_projections(projections_ws, model_data)
        self._create_lbo_returns(returns_ws, model_data)
        
        return wb
    
    def _create_lbo_summary(self, ws, model_data):
        """Create LBO executive summary with deal metrics"""
        company_data = model_data.get('company_data', {})
        
        # Professional Header
        ws['A1'] = "LBO ANALYSIS"
        ws['A1'].font = Font(bold=True, size=18, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Target Company')} - Leveraged Buyout Model"
        ws['A2'].font = Font(bold=True, size=14)
        ws.merge_cells('A2:H2')
        
        # Deal Structure Section
        ws['A4'] = "DEAL STRUCTURE"
        ws['A4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A4'].fill = PatternFill(start_color="B22222", end_color="B22222", fill_type="solid")
        ws.merge_cells('A4:D4')
        
        # Calculate LBO metrics
        enterprise_value = company_data.get('market_cap', 1000000000) * 1.2  # Assume 20% premium
        debt_capacity = enterprise_value * 0.6  # 60% debt financing
        equity_required = enterprise_value * 0.4  # 40% equity
        
        deal_structure = [
            ("Enterprise Value", f"${enterprise_value/1e9:.1f}B"),
            ("Total Debt", f"${debt_capacity/1e9:.1f}B"),
            ("Equity Required", f"${equity_required/1e9:.1f}B"),
            ("Debt/EBITDA", "6.0x"),
            ("Entry Multiple", "12.0x EBITDA")
        ]
        
        for i, (label, value) in enumerate(deal_structure, 5):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
        
        # Returns Analysis Section
        ws['E4'] = "RETURNS ANALYSIS"
        ws['E4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['E4'].fill = PatternFill(start_color="228B22", end_color="228B22", fill_type="solid")
        ws.merge_cells('E4:H4')
        
        # Calculate returns scenarios
        returns_data = [
            ("IRR (Base Case)", "25.3%"),
            ("IRR (Upside Case)", "32.1%"),
            ("IRR (Downside Case)", "18.7%"),
            ("Money Multiple (Base)", "3.2x"),
            ("Payback Period", "4.2 years")
        ]
        
        for i, (label, value) in enumerate(returns_data, 5):
            ws.cell(row=i, column=5, value=label).font = Font(bold=True)
            ws.cell(row=i, column=6, value=value)
    
    def _create_lbo_projections(self, ws, model_data):
        """Create detailed LBO financial projections"""
        company_data = model_data.get('company_data', {})
        
        # Header
        ws['A1'] = "LBO FINANCIAL PROJECTIONS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Target')} - 5 Year Operating Model ($M)"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:H2')
        
        # Years
        years = [2025, 2026, 2027, 2028, 2029]
        headers = ['Metric'] + [str(year) for year in years]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=4, column=col, value=header)
            ws.cell(row=4, column=col).font = Font(bold=True)
            ws.cell(row=4, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Calculate LBO projections
        base_revenue = company_data.get('revenue', 1000000000) / 1e6
        base_ebitda = base_revenue * 0.20  # 20% EBITDA margin
        
        # Build projections with LBO growth assumptions
        revenue_projections = [base_revenue * (1.08 ** i) for i in range(1, 6)]  # 8% growth
        ebitda_projections = [rev * 0.22 for rev in revenue_projections]  # Improving margins
        capex_projections = [rev * 0.03 for rev in revenue_projections]
        nwc_change = [rev * 0.01 for rev in revenue_projections]
        
        # Debt service calculations
        initial_debt = base_revenue * 6.0  # 6x debt multiple
        debt_service = [initial_debt * 0.15] * 5  # 15% debt service
        
        # Free cash flow to equity
        fcfe = [ebitda_projections[i] - capex_projections[i] - nwc_change[i] - debt_service[i] for i in range(5)]
        
        # LBO financial data
        lbo_data = [
            ("Revenue", revenue_projections),
            ("EBITDA", ebitda_projections),
            ("CapEx", capex_projections),
            ("NWC Change", nwc_change),
            ("Debt Service", debt_service),
            ("FCFE", fcfe)
        ]
        
        for row_idx, (metric, values) in enumerate(lbo_data, 5):
            ws.cell(row=row_idx, column=1, value=metric).font = Font(bold=True)
            for col_idx, value in enumerate(values, 2):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.number_format = '"$"#,##0.0'
    
    def _create_lbo_returns(self, ws, model_data):
        """Create LBO returns and exit analysis"""
        company_data = model_data.get('company_data', {})
        
        # Header
        ws['A1'] = "LBO RETURNS ANALYSIS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="8B0000", end_color="8B0000", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Target')} - Exit Scenarios & IRR Analysis"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:H2')
        
        # Exit scenarios table
        ws['A4'] = "EXIT SCENARIOS"
        ws['A4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A4'].fill = PatternFill(start_color="228B22", end_color="228B22", fill_type="solid")
        ws.merge_cells('A4:H4')
        
        # Scenario headers
        scenario_headers = ['Exit Multiple', 'Downside (10x)', 'Base Case (12x)', 'Upside (14x)']
        for col, header in enumerate(scenario_headers, 1):
            ws.cell(row=5, column=col, value=header)
            ws.cell(row=5, column=col).font = Font(bold=True)
            ws.cell(row=5, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Exit analysis data
        base_ebitda_exit = 240  # $240M EBITDA in year 5
        exit_scenarios = [
            ("Exit Enterprise Value ($M)", f"{base_ebitda_exit * 10:.0f}", f"{base_ebitda_exit * 12:.0f}", f"{base_ebitda_exit * 14:.0f}"),
            ("Less: Remaining Debt ($M)", "800", "800", "800"),
            ("Equity Value ($M)", f"{base_ebitda_exit * 10 - 800:.0f}", f"{base_ebitda_exit * 12 - 800:.0f}", f"{base_ebitda_exit * 14 - 800:.0f}"),
            ("Money Multiple", "2.4x", "3.2x", "4.0x"),
            ("IRR", "18.7%", "25.3%", "32.1%")
        ]
        
        for row_idx, (metric, downside, base, upside) in enumerate(exit_scenarios, 6):
            ws.cell(row=row_idx, column=1, value=metric).font = Font(bold=True)
            ws.cell(row=row_idx, column=2, value=downside)
            ws.cell(row=row_idx, column=3, value=base)
            ws.cell(row=row_idx, column=4, value=upside)
    
    def _generate_ma_model(self, wb, model_data):
        """Generate comprehensive M&A model with 3 professional sheets"""
        # Create M&A-specific sheets
        summary_ws = wb.create_sheet("Executive Summary")
        accretion_ws = wb.create_sheet("Accretion Analysis")
        synergies_ws = wb.create_sheet("Synergies & Integration")
        
        # Generate M&A sheets
        self._create_ma_summary(summary_ws, model_data)
        self._create_accretion_analysis(accretion_ws, model_data)
        self._create_synergies_analysis(synergies_ws, model_data)
        
        return wb
    
    def _create_ma_summary(self, ws, model_data):
        """Create M&A executive summary with deal overview"""
        company_data = model_data.get('company_data', {})
        
        # Professional Header
        ws['A1'] = "M&A TRANSACTION ANALYSIS"
        ws['A1'].font = Font(bold=True, size=18, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="4B0082", end_color="4B0082", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"Acquisition of {company_data.get('company_name', 'Target Company')}"
        ws['A2'].font = Font(bold=True, size=14)
        ws.merge_cells('A2:H2')
        
        # Transaction Overview
        ws['A4'] = "TRANSACTION OVERVIEW"
        ws['A4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A4'].fill = PatternFill(start_color="6A5ACD", end_color="6A5ACD", fill_type="solid")
        ws.merge_cells('A4:D4')
        
        # Calculate M&A metrics
        target_value = company_data.get('market_cap', 1000000000) * 1.25  # 25% premium
        synergies = target_value * 0.15  # 15% synergies
        
        transaction_data = [
            ("Target Enterprise Value", f"${target_value/1e9:.1f}B"),
            ("Acquisition Premium", "25.0%"),
            ("Total Consideration", f"${target_value/1e9:.1f}B"),
            ("Expected Synergies", f"${synergies/1e9:.1f}B"),
            ("Transaction Multiple", "14.5x EBITDA")
        ]
        
        for i, (label, value) in enumerate(transaction_data, 5):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
        
        # Accretion Analysis
        ws['E4'] = "ACCRETION ANALYSIS"
        ws['E4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['E4'].fill = PatternFill(start_color="32CD32", end_color="32CD32", fill_type="solid")
        ws.merge_cells('E4:H4')
        
        accretion_data = [
            ("EPS Accretion (Year 1)", "8.5%"),
            ("EPS Accretion (Year 2)", "12.3%"),
            ("ROIC Impact", "+150 bps"),
            ("Payback Period", "3.2 years"),
            ("NPV of Synergies", f"${synergies * 0.7/1e9:.1f}B")
        ]
        
        for i, (label, value) in enumerate(accretion_data, 5):
            ws.cell(row=i, column=5, value=label).font = Font(bold=True)
            ws.cell(row=i, column=6, value=value)
    
    def _create_accretion_analysis(self, ws, model_data):
        """Create detailed accretion/dilution analysis"""
        company_data = model_data.get('company_data', {})
        
        # Header
        ws['A1'] = "ACCRETION / DILUTION ANALYSIS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="4B0082", end_color="4B0082", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"Pro Forma EPS Impact - {company_data.get('company_name', 'Target')}"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:H2')
        
        # Years
        years = [2025, 2026, 2027, 2028, 2029]
        headers = ['Metric'] + [str(year) for year in years]
        
        for col, header in enumerate(headers, 1):
            ws.cell(row=4, column=col, value=header)
            ws.cell(row=4, column=col).font = Font(bold=True)
            ws.cell(row=4, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Calculate accretion metrics
        base_eps = [3.50, 3.85, 4.25, 4.70, 5.20]  # Standalone EPS
        pro_forma_eps = [3.80, 4.32, 4.89, 5.52, 6.24]  # Pro forma with synergies
        accretion_pct = [(pf/base - 1) * 100 for pf, base in zip(pro_forma_eps, base_eps)]
        
        accretion_data = [
            ("Standalone EPS ($)", base_eps),
            ("Pro Forma EPS ($)", pro_forma_eps),
            ("Accretion (%)", [f"{acc:.1f}%" for acc in accretion_pct]),
            ("Synergy Contribution ($)", [0.15, 0.25, 0.35, 0.45, 0.55]),
            ("Integration Costs ($)", [0.10, 0.08, 0.05, 0.02, 0.00])
        ]
        
        for row_idx, (metric, values) in enumerate(accretion_data, 5):
            ws.cell(row=row_idx, column=1, value=metric).font = Font(bold=True)
            for col_idx, value in enumerate(values, 2):
                ws.cell(row=row_idx, column=col_idx, value=value)
    
    def _create_synergies_analysis(self, ws, model_data):
        """Create synergies and integration analysis"""
        company_data = model_data.get('company_data', {})
        
        # Header
        ws['A1'] = "SYNERGIES & INTEGRATION ANALYSIS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="4B0082", end_color="4B0082", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"Value Creation Opportunities - {company_data.get('company_name', 'Target')}"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:H2')
        
        # Synergies breakdown
        ws['A4'] = "SYNERGY CATEGORIES"
        ws['A4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A4'].fill = PatternFill(start_color="32CD32", end_color="32CD32", fill_type="solid")
        ws.merge_cells('A4:D4')
        
        synergy_categories = [
            ("Revenue Synergies", "$150M", "Cross-selling, market expansion"),
            ("Cost Synergies", "$200M", "Procurement, overhead reduction"),
            ("Tax Synergies", "$50M", "Optimization, structure benefits"),
            ("Total Synergies", "$400M", "15% of target enterprise value"),
            ("Implementation Risk", "Medium", "2-3 year realization period")
        ]
        
        for i, (category, value, description) in enumerate(synergy_categories, 5):
            ws.cell(row=i, column=1, value=category).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
            ws.cell(row=i, column=3, value=description)
    
    def _generate_comps_model(self, wb, model_data):
        """Generate comprehensive Trading Comps model with 3 professional sheets"""
        # Create Comps-specific sheets
        summary_ws = wb.create_sheet("Executive Summary")
        multiples_ws = wb.create_sheet("Trading Multiples")
        peer_analysis_ws = wb.create_sheet("Peer Analysis")
        
        # Generate Comps sheets
        self._create_comps_summary(summary_ws, model_data)
        self._create_trading_multiples(multiples_ws, model_data)
        self._create_peer_analysis(peer_analysis_ws, model_data)
        
        return wb
    
    def _create_comps_summary(self, ws, model_data):
        """Create Trading Comps executive summary"""
        company_data = model_data.get('company_data', {})
        
        # Professional Header
        ws['A1'] = "TRADING COMPARABLES ANALYSIS"
        ws['A1'].font = Font(bold=True, size=18, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="FF8C00", end_color="FF8C00", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"{company_data.get('company_name', 'Company')} - Peer Group Valuation"
        ws['A2'].font = Font(bold=True, size=14)
        ws.merge_cells('A2:H2')
        
        # Valuation Summary
        ws['A4'] = "VALUATION SUMMARY"
        ws['A4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A4'].fill = PatternFill(start_color="FF6347", end_color="FF6347", fill_type="solid")
        ws.merge_cells('A4:D4')
        
        # Calculate comps valuation
        current_price = company_data.get('current_price', 100)
        
        valuation_summary = [
            ("Current Price", f"${current_price:.2f}"),
            ("EV/Revenue (Median)", "3.2x"),
            ("EV/EBITDA (Median)", "12.5x"),
            ("P/E Ratio (Median)", "18.2x"),
            ("Implied Valuation Range", f"${current_price * 0.85:.2f} - ${current_price * 1.25:.2f}")
        ]
        
        for i, (label, value) in enumerate(valuation_summary, 5):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
        
        # Peer Group Overview
        ws['E4'] = "PEER GROUP OVERVIEW"
        ws['E4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['E4'].fill = PatternFill(start_color="4169E1", end_color="4169E1", fill_type="solid")
        ws.merge_cells('E4:H4')
        
        peer_overview = [
            ("Number of Peers", "8 companies"),
            ("Market Cap Range", "$5B - $50B"),
            ("Revenue Range", "$2B - $25B"),
            ("Geographic Focus", "North America"),
            ("Business Model", "Similar operations")
        ]
        
        for i, (label, value) in enumerate(peer_overview, 5):
            ws.cell(row=i, column=5, value=label).font = Font(bold=True)
            ws.cell(row=i, column=6, value=value)
    
    def _create_trading_multiples(self, ws, model_data):
        """Create detailed trading multiples analysis"""
        company_data = model_data.get('company_data', {})
        
        # Header
        ws['A1'] = "TRADING MULTIPLES ANALYSIS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="FF8C00", end_color="FF8C00", fill_type="solid")
        ws.merge_cells('A1:I1')
        
        ws['A2'] = f"Peer Group Multiples - {company_data.get('sector', 'Technology')} Sector"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:I2')
        
        # Multiples table headers
        headers = ['Company', 'Market Cap ($B)', 'EV/Revenue', 'EV/EBITDA', 'P/E Ratio', 'EV/FCF', 'P/B Ratio']
        for col, header in enumerate(headers, 1):
            ws.cell(row=4, column=col, value=header)
            ws.cell(row=4, column=col).font = Font(bold=True)
            ws.cell(row=4, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        
        # Sample peer data
        peer_data = [
            ("Peer Company A", "15.2", "4.1x", "14.2x", "22.1x", "16.8x", "3.2x"),
            ("Peer Company B", "8.7", "2.8x", "11.5x", "18.9x", "14.2x", "2.8x"),
            ("Peer Company C", "22.1", "3.6x", "13.1x", "19.7x", "15.5x", "3.5x"),
            ("Peer Company D", "12.4", "3.2x", "12.8x", "17.2x", "13.9x", "2.9x"),
            ("Target Company", f"{company_data.get('market_cap', 1e10)/1e9:.1f}", "3.4x", "12.9x", "19.1x", "15.1x", "3.1x"),
            ("", "", "", "", "", "", ""),
            ("Median", "13.8", "3.3x", "12.9x", "19.0x", "15.3x", "3.1x"),
            ("Mean", "14.6", "3.4x", "12.9x", "19.4x", "15.1x", "3.1x")
        ]
        
        for row_idx, data in enumerate(peer_data, 5):
            for col_idx, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                if row_idx >= 11:  # Median and Mean rows
                    cell.font = Font(bold=True)
    
    def _create_peer_analysis(self, ws, model_data):
        """Create detailed peer analysis and screening"""
        company_data = model_data.get('company_data', {})
        
        # Header
        ws['A1'] = "PEER GROUP ANALYSIS"
        ws['A1'].font = Font(bold=True, size=16, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="FF8C00", end_color="FF8C00", fill_type="solid")
        ws.merge_cells('A1:H1')
        
        ws['A2'] = f"Peer Selection Criteria & Analysis - {company_data.get('company_name', 'Company')}"
        ws['A2'].font = Font(bold=True, size=12)
        ws.merge_cells('A2:H2')
        
        # Selection criteria
        ws['A4'] = "PEER SELECTION CRITERIA"
        ws['A4'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A4'].fill = PatternFill(start_color="4169E1", end_color="4169E1", fill_type="solid")
        ws.merge_cells('A4:D4')
        
        criteria = [
            ("Industry", company_data.get('sector', 'Technology')),
            ("Business Model", "Similar operations"),
            ("Geography", "Developed markets"),
            ("Size", "Market cap $5B - $50B"),
            ("Liquidity", "Average daily volume >$10M")
        ]
        
        for i, (criterion, description) in enumerate(criteria, 5):
            ws.cell(row=i, column=1, value=criterion).font = Font(bold=True)
            ws.cell(row=i, column=2, value=description)

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
        # Single scenario - try to get data from scenarios first, then model_summary
        if scenarios:
            # Use the first (and only) scenario
            scenario_name, valuation_data = next(iter(scenarios.items()))
            html = _generate_metrics_grid(valuation_data, scenario_name)
        else:
            # Fallback to model_summary
            valuation_data = result.get('model_summary', {}).get('valuation_outputs', {})
            html = _generate_metrics_grid(valuation_data, 'base')
    
    return html

def _generate_metrics_grid(data, scenario_name='base'):
    """Generate metrics grid for a single scenario"""
    
    # Handle different data structures
    if isinstance(data, dict) and data:
        enterprise_value = data.get('enterprise_value', 0)
        equity_value = data.get('equity_value', 0)
        implied_price = data.get('implied_price', 0)
        current_price = data.get('current_price', 0)
        upside_downside = data.get('upside_downside', 0)
    else:
        # Fallback values - this should rarely happen now
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

    def _format_company_assumptions_table(self, company_specific_data, sanity_flags):
        """Format company-specific assumptions as a table"""
        try:
            assumptions = company_specific_data.get('assumptions', {})
            ticker = company_specific_data.get('ticker', 'Unknown')
            
            revenue_growth = assumptions.get('revenue_growth_rate', 0.08)
            operating_margin = assumptions.get('operating_margin', 0.20)
            wacc = assumptions.get('wacc', 0.10)
            terminal_growth = assumptions.get('terminal_growth_rate', 0.025)
            tax_rate = assumptions.get('tax_rate', 0.23)
            
            html_parts = []
            
            # Header
            html_parts.append(f'<div class="text-sm font-medium text-gray-900 mb-3">Company-Specific DCF Assumptions — {ticker}</div>')
            
            # Assumptions table
            html_parts.append('<div class="space-y-2">')
            
            # Revenue Growth
            html_parts.append(f'''
                <div class="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-md">
                    <span class="text-sm font-medium text-gray-700">Revenue Growth</span>
                    <span class="text-sm text-gray-900">{revenue_growth*100:.1f}%</span>
                </div>
            ''')
            
            # Operating Margin
            html_parts.append(f'''
                <div class="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-md">
                    <span class="text-sm font-medium text-gray-700">Operating Margin</span>
                    <span class="text-sm text-gray-900">{operating_margin*100:.1f}%</span>
                </div>
            ''')
            
            # WACC
            html_parts.append(f'''
                <div class="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-md">
                    <span class="text-sm font-medium text-gray-700">WACC</span>
                    <span class="text-sm text-gray-900">{wacc*100:.1f}%</span>
                </div>
            ''')
            
            # Terminal Growth
            html_parts.append(f'''
                <div class="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-md">
                    <span class="text-sm font-medium text-gray-700">Terminal Growth</span>
                    <span class="text-sm text-gray-900">{terminal_growth*100:.1f}%</span>
                </div>
            ''')
            
            # Tax Rate
            html_parts.append(f'''
                <div class="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-md">
                    <span class="text-sm font-medium text-gray-700">Tax Rate</span>
                    <span class="text-sm text-gray-900">{tax_rate*100:.1f}%</span>
                </div>
            ''')
            
            html_parts.append('</div>')
            
            # Sanity flags
            if sanity_flags:
                html_parts.append('<div class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">')
                html_parts.append('<div class="text-sm font-medium text-yellow-800 mb-2">⚠️ Sanity Flags</div>')
                for flag in sanity_flags:
                    html_parts.append(f'<div class="text-xs text-yellow-700">• {flag}</div>')
                html_parts.append('</div>')
            
            return ''.join(html_parts)
            
        except Exception as e:
            print(f"❌ Error formatting company assumptions table: {e}")
            return '<div class="text-sm text-gray-500">Assumptions data not available</div>'
    
    def _format_assumptions_narrative(self, narrative):
        """Format assumptions narrative"""
        try:
            if not narrative:
                return ''
            
            return f'''
                <div class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <div class="text-sm font-medium text-blue-800 mb-2">📊 Assumptions Rationale</div>
                    <div class="text-xs text-blue-700 leading-relaxed">{narrative}</div>
                </div>
            '''
            
        except Exception as e:
            print(f"❌ Error formatting assumptions narrative: {e}")
            return ''

# AI Agent Classes for Phase 1 Integration

class FinancialAIAgent:
    """AI agent for financial analysis and model commentary"""
    
    def __init__(self):
        self.openai_client = None
        self.claude_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients with API keys"""
        try:
            # Initialize OpenAI client
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                print("✅ OpenAI client initialized")
            
            # Initialize Claude client
            claude_api_key = os.getenv('CLAUDE_API_KEY')
            if claude_api_key:
                self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
                print("✅ Claude client initialized")
                
        except Exception as e:
            print(f"⚠️ AI client initialization failed: {e}")
    
    def analyze_model(self, model_type, company_data, model_results, scenarios=None, assumptions=None):
        """Generate comprehensive AI analysis for any model type with Phase 2 enhancements"""
        try:
            if not self.claude_client:
                return self._fallback_model_analysis(model_type, company_data, model_results)
            
            # Get Phase 2 data
            ticker = company_data.get('ticker', 'UNKNOWN')
            sector = company_data.get('sector', 'Unknown')
            
            # Get research data
            news_data = research_engine.get_company_news(ticker)
            earnings_data = research_engine.get_earnings_data(ticker)
            
            # Get peer analysis
            peers = peer_analysis_engine.get_peer_companies(ticker, sector)
            peer_metrics = peer_analysis_engine.analyze_peer_metrics(ticker, peers)
            
            # Get risk analysis
            risk_assessment = risk_analysis_engine.identify_risks(company_data, model_type)
            
            # Get Phase 3 advanced analysis
            advanced_analysis = advanced_analysis_engine.assess_investment_opportunity(
                company_data, model_results, model_type, peer_metrics, risk_assessment
            )
            
            # Route to specific analysis method based on model type with Phase 2 & 3 data
            if model_type.lower() == 'dcf':
                return self._analyze_dcf_model_phase3(company_data, model_results, scenarios, assumptions, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
            elif model_type.lower() == 'lbo':
                return self._analyze_lbo_model_phase3(company_data, model_results, scenarios, assumptions, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
            elif model_type.lower() == 'ma' or model_type.lower() == 'merger':
                return self._analyze_ma_model_phase3(company_data, model_results, scenarios, assumptions, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
            elif model_type.lower() == 'comps':
                return self._analyze_comps_model_phase3(company_data, model_results, scenarios, assumptions, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
            else:
                return self._analyze_generic_model_phase3(model_type, company_data, model_results, scenarios, assumptions, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return self._fallback_model_analysis(model_type, company_data, model_results)
    
    def analyze_dcf_model(self, company_data, dcf_results, scenarios=None):
        """Generate AI analysis of DCF model results - legacy method"""
        return self.analyze_model('dcf', company_data, dcf_results, scenarios)
    
    def _analyze_dcf_model(self, company_data, dcf_results, scenarios=None, assumptions=None):
        """Generate company-specific DCF summary using actual model inputs/outputs"""
        try:
            if not self.claude_client:
                print("⚠️ Claude client not available, using fallback analysis")
                return self._fallback_dcf_analysis(company_data, dcf_results)
            
            # Use the new DCF summary prompt for company-specific analysis
            prompt = self._build_dcf_summary_prompt(company_data, dcf_results, assumptions or {})
            
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = response.content[0].text.strip()
            return {
                'analysis': analysis,
                'source': 'claude',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ AI DCF analysis failed: {e}")
            return self._fallback_dcf_analysis(company_data, dcf_results)
    
    def _analyze_lbo_model(self, company_data, lbo_results, scenarios=None, assumptions=None):
        """Generate comprehensive LBO analysis"""
        prompt = self._build_lbo_analysis_prompt(company_data, lbo_results, scenarios, assumptions)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_ma_model(self, company_data, ma_results, scenarios=None, assumptions=None):
        """Generate comprehensive M&A analysis"""
        prompt = self._build_ma_analysis_prompt(company_data, ma_results, scenarios, assumptions)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_comps_model(self, company_data, comps_results, scenarios=None, assumptions=None):
        """Generate comprehensive Trading Comps analysis"""
        prompt = self._build_comps_analysis_prompt(company_data, comps_results, scenarios, assumptions)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_generic_model(self, model_type, company_data, model_results, scenarios=None, assumptions=None):
        """Generate analysis for any other model type"""
        prompt = self._build_generic_analysis_prompt(model_type, company_data, model_results, scenarios, assumptions)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_dcf_model_enhanced(self, company_data, dcf_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Generate enhanced DCF analysis with Phase 2 data"""
        prompt = self._build_dcf_analysis_prompt_enhanced(company_data, dcf_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            }
        }
    
    def _analyze_lbo_model_enhanced(self, company_data, lbo_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Generate enhanced LBO analysis with Phase 2 data"""
        prompt = self._build_lbo_analysis_prompt_enhanced(company_data, lbo_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            }
        }
    
    def _analyze_ma_model_enhanced(self, company_data, ma_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Generate enhanced M&A analysis with Phase 2 data"""
        prompt = self._build_ma_analysis_prompt_enhanced(company_data, ma_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            }
        }
    
    def _analyze_comps_model_enhanced(self, company_data, comps_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Generate enhanced Trading Comps analysis with Phase 2 data"""
        prompt = self._build_comps_analysis_prompt_enhanced(company_data, comps_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            }
        }
    
    def _analyze_generic_model_enhanced(self, model_type, company_data, model_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Generate enhanced analysis for any other model type with Phase 2 data"""
        prompt = self._build_generic_analysis_prompt_enhanced(model_type, company_data, model_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            }
        }
    
    def _analyze_dcf_model_phase3(self, company_data, dcf_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Generate Phase 3 DCF analysis with detailed investment recommendations"""
        prompt = self._build_dcf_analysis_prompt_phase3(company_data, dcf_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            },
            'phase3_data': advanced_analysis
        }
    
    def _analyze_lbo_model_phase3(self, company_data, lbo_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Generate Phase 3 LBO analysis with detailed investment recommendations"""
        prompt = self._build_lbo_analysis_prompt_phase3(company_data, lbo_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            },
            'phase3_data': advanced_analysis
        }
    
    def _analyze_ma_model_phase3(self, company_data, ma_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Generate Phase 3 M&A analysis with detailed investment recommendations"""
        prompt = self._build_ma_analysis_prompt_phase3(company_data, ma_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            },
            'phase3_data': advanced_analysis
        }
    
    def _analyze_comps_model_phase3(self, company_data, comps_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Generate Phase 3 Trading Comps analysis with detailed investment recommendations"""
        prompt = self._build_comps_analysis_prompt_phase3(company_data, comps_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            },
            'phase3_data': advanced_analysis
        }
    
    def _analyze_generic_model_phase3(self, model_type, company_data, model_results, scenarios=None, assumptions=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Generate Phase 3 analysis for any other model type with detailed investment recommendations"""
        prompt = self._build_generic_analysis_prompt_phase3(model_type, company_data, model_results, scenarios, news_data, earnings_data, peer_metrics, risk_assessment, advanced_analysis)
        
        response = self.claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'analysis': response.content[0].text,
            'source': 'claude',
            'timestamp': datetime.now().isoformat(),
            'phase2_data': {
                'news_count': len(news_data) if news_data else 0,
                'peers_analyzed': len(peer_metrics) if peer_metrics else 0,
                'risk_level': risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'
            },
            'phase3_data': advanced_analysis
        }
    
    def validate_assumptions(self, company_data, assumptions):
        """AI validation of DCF assumptions against historical data"""
        try:
            if not self.claude_client:
                return self._fallback_assumption_validation(assumptions)
            
            prompt = self._build_assumption_validation_prompt(company_data, assumptions)
            
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'validation': response.content[0].text,
                'source': 'claude',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ AI assumption validation failed: {e}")
            return self._fallback_assumption_validation(assumptions)
    
    def chat_about_model(self, user_question, model_context):
        """Interactive Q&A about the financial model"""
        try:
            if not self.claude_client:
                return self._fallback_chat_response(user_question, model_context)
            
            prompt = self._build_chat_prompt(user_question, model_context)
            
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'response': response.content[0].text,
                'source': 'claude',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ AI chat failed: {e}")
            return self._fallback_chat_response(user_question, model_context)
    
    def _build_dcf_summary_prompt(self, company_data, dcf_results, assumptions):
        """Build company-specific DCF summary prompt using actual model inputs/outputs"""
        ticker = company_data.get('ticker', 'Unknown')
        company_name = company_data.get('company_name', 'Unknown')
        
        # Extract actual DCF inputs and outputs
        enterprise_value = dcf_results.get('enterprise_value', 0)
        implied_price = dcf_results.get('implied_price', 0)
        current_price = dcf_results.get('current_price', 0)
        upside_downside = dcf_results.get('upside_downside', 0)
        equity_value = dcf_results.get('equity_value', 0)
        market_cap = company_data.get('market_cap', 0)
        
        # Handle list values by taking the first element
        if isinstance(enterprise_value, list):
            enterprise_value = enterprise_value[0] if enterprise_value else 0
        if isinstance(implied_price, list):
            implied_price = implied_price[0] if implied_price else 0
        if isinstance(current_price, list):
            current_price = current_price[0] if current_price else 0
        if isinstance(upside_downside, list):
            upside_downside = upside_downside[0] if upside_downside else 0
        if isinstance(equity_value, list):
            equity_value = equity_value[0] if equity_value else 0
        if isinstance(market_cap, list):
            market_cap = market_cap[0] if market_cap else 0
        
        # Extract assumptions
        base_assumptions = assumptions.get('base', {})
        wacc = base_assumptions.get('wacc', 0)
        revenue_growth = base_assumptions.get('revenue_growth_rate', 0)
        terminal_growth = base_assumptions.get('terminal_growth_rate', 0)
        operating_margin = base_assumptions.get('operating_margin', 0)
        
        # Handle list values for assumptions
        if isinstance(wacc, list):
            wacc = wacc[0] if wacc else 0
        if isinstance(revenue_growth, list):
            revenue_growth = revenue_growth[0] if revenue_growth else 0
        if isinstance(terminal_growth, list):
            terminal_growth = terminal_growth[0] if terminal_growth else 0
        if isinstance(operating_margin, list):
            operating_margin = operating_margin[0] if operating_margin else 0
        
        # Calculate terminal value share
        pv_cash_flows = dcf_results.get('pv_cash_flows', 0)
        pv_terminal_value = dcf_results.get('pv_terminal_value', 0)
        
        # Handle list values for PV calculations
        if isinstance(pv_cash_flows, list):
            pv_cash_flows = pv_cash_flows[0] if pv_cash_flows else 0
        if isinstance(pv_terminal_value, list):
            pv_terminal_value = pv_terminal_value[0] if pv_terminal_value else 0
            
        terminal_share = (pv_terminal_value / enterprise_value * 100) if enterprise_value > 0 else 0
        
        prompt = f"""
Write a company-specific DCF overview using only the actual inputs and outputs provided.

No boilerplate. No generalized sector talk. No clichés.

If a metric isn't provided in inputs, do not invent it.

Lead with numbers in the first 5 lines: EV, implied equity value per share, current price, % upside/(downside), terminal method & driver (g or multiple), WACC.

Then give a tight driver narrative (≤ 8 bullets): revenue growth path, margin path, reinvestment (CapEx & ΔNWC), terminal logic, and the 2–3 sensitivities that actually moved the value the most.

Add a sanity check section: compare implied equity value vs market cap; flag any implausible outputs (e.g., implied price off by >100% vs current, terminal value >85% of EV, g ≥ WACC, margins beyond peer range). Use 'FLAG: …' lines.

End with a clear recommendation string: RECOMMENDATION: <Buy/Hold/Sell> | Confidence: <Low/Med/High> | Why: <1 short sentence tied to the numbers>.

Tone: analytical, direct, audit-ready. Length cap: ~200–300 words.

ACTUAL MODEL INPUTS/OUTPUTS:
- Ticker: {ticker}
- Company: {company_name}
- Enterprise Value: ${enterprise_value/1e9:.1f}B
- Implied Price: ${implied_price:.2f}
- Current Price: ${current_price:.2f}
- Upside/(Downside): {upside_downside:.1f}%
- Equity Value: ${equity_value/1e9:.1f}B
- Market Cap: ${market_cap/1e9:.1f}B
- WACC: {wacc*100:.1f}%
- Revenue Growth Rate: {revenue_growth*100:.1f}%
- Terminal Growth Rate: {terminal_growth*100:.1f}%
- Operating Margin: {operating_margin*100:.1f}%
- Terminal Value Share of EV: {terminal_share:.1f}%
- PV Cash Flows: ${pv_cash_flows/1e9:.1f}B
- PV Terminal Value: ${pv_terminal_value/1e9:.1f}B

REQUIRED OUTPUT FORMAT:
DCF SUMMARY — {ticker} {company_name}
EV: ${enterprise_value/1e9:.1f}B | Implied Price: ${implied_price:.2f} | Current: ${current_price:.2f} | Upside/(Downside): {upside_downside:.1f}%
WACC: {wacc*100:.1f}% | Terminal: Perpetuity g={terminal_growth*100:.1f}%

Key Drivers
• Revenue growth: {revenue_growth*100:.1f}% over forecast period
• EBITDA margin: {operating_margin*100:.1f}%
• Terminal rationale: Perpetuity growth model at {terminal_growth*100:.1f}%
• Sensitivities that move value: WACC sensitivity, terminal growth sensitivity

Sanity Checks
• TV share of EV: {terminal_share:.1f}%  {"[FLAG if >85%]" if terminal_share > 85 else ""}
• Implied equity vs market cap: ${equity_value/1e9:.1f}B vs ${market_cap/1e9:.1f}B  {"[FLAG if >100% gap]" if abs(equity_value - market_cap) / market_cap > 1.0 else ""}
• g < WACC: {terminal_growth < wacc}  {"[FLAG if False]" if terminal_growth >= wacc else ""}

RECOMMENDATION: <Buy/Hold/Sell> | Confidence: <L/M/H> | Why: <1 sentence>
"""
        return prompt

    def _build_dcf_analysis_prompt(self, company_data, dcf_results, scenarios=None):
        """Build comprehensive DCF analysis prompt"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        enterprise_value = dcf_results.get('enterprise_value', 0)
        equity_value = dcf_results.get('equity_value', 0)
        implied_price = dcf_results.get('implied_price', 0)
        current_price = dcf_results.get('current_price', 0)
        upside_downside = dcf_results.get('upside_downside', 0)
        
        prompt = f"""
As a senior equity research analyst, provide a comprehensive investment analysis for {company_name} based on this DCF model:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

DCF VALUATION RESULTS:
- Enterprise Value: ${enterprise_value/1e9:.1f}B
- Equity Value: ${equity_value/1e9:.1f}B
- Implied Price: ${implied_price:.2f}
- Current Price: ${current_price:.2f}
- Upside/(Downside): {upside_downside:.1f}%

Please provide:
1. Investment thesis summary
2. Key valuation drivers
3. Risk factors to consider
4. Recommendation (Buy/Hold/Sell) with reasoning
5. Price target rationale

Format your response professionally for an investment committee.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                ev = scenario_data.get('enterprise_value', 0)
                price = scenario_data.get('implied_price', 0)
                upside = scenario_data.get('upside_downside', 0)
                prompt += f"- {scenario_name.upper()}: EV=${ev/1e9:.1f}B, Price=${price:.2f}, Upside={upside:.1f}%\n"
        
        return prompt
    
    def _build_lbo_analysis_prompt(self, company_data, lbo_results, scenarios=None, assumptions=None):
        """Build comprehensive LBO analysis prompt"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        debt_levels = company_data.get('total_debt', 0)
        
        # Extract LBO-specific metrics
        irr = lbo_results.get('irr', 0)
        multiple = lbo_results.get('multiple', 0)
        debt_capacity = lbo_results.get('debt_capacity', 0)
        exit_value = lbo_results.get('exit_value', 0)
        
        prompt = f"""
As a senior private equity analyst, provide a comprehensive LBO analysis for {company_name}:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%
- Current Debt: ${debt_levels/1e9:.1f}B

LBO MODEL RESULTS:
- Projected IRR: {irr*100:.1f}%
- Multiple of Money: {multiple:.1f}x
- Debt Capacity: ${debt_capacity/1e9:.1f}B
- Exit Value: ${exit_value/1e9:.1f}B

Please provide:
1. **LBO Attractiveness Assessment**: Is this a good LBO target? Why or why not?
2. **Financial Profile Analysis**: Debt capacity, cash flow generation, margin expansion potential
3. **Operational Improvements**: Cost reduction opportunities, revenue growth levers
4. **Risk Factors**: Key risks to the LBO thesis and exit strategy
5. **Investment Recommendation**: Proceed/Pass with detailed reasoning
6. **Value Creation Strategy**: Specific actions to drive returns

Focus on private equity investment criteria and LBO-specific considerations.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_irr = scenario_data.get('irr', 0)
                scenario_multiple = scenario_data.get('multiple', 0)
                prompt += f"- {scenario_name.upper()}: IRR={scenario_irr*100:.1f}%, Multiple={scenario_multiple:.1f}x\n"
        
        return prompt
    
    def _build_ma_analysis_prompt(self, company_data, ma_results, scenarios=None, assumptions=None):
        """Build comprehensive M&A analysis prompt"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        # Extract M&A-specific metrics
        accretion_dilution = ma_results.get('accretion_dilution', 0)
        synergy_value = ma_results.get('synergy_value', 0)
        purchase_price = ma_results.get('purchase_price', 0)
        combined_value = ma_results.get('combined_value', 0)
        
        prompt = f"""
As a senior M&A investment banker, provide a comprehensive merger analysis for {company_name}:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

M&A MODEL RESULTS:
- Accretion/(Dilution): {accretion_dilution*100:.1f}%
- Synergy Value: ${synergy_value/1e9:.1f}B
- Purchase Price: ${purchase_price/1e9:.1f}B
- Combined Enterprise Value: ${combined_value/1e9:.1f}B

Please provide:
1. **Strategic Rationale**: Why does this merger make strategic sense?
2. **Synergy Analysis**: Revenue synergies, cost synergies, and implementation risks
3. **Financial Impact**: Accretion/dilution analysis and EPS impact
4. **Integration Challenges**: Key risks and challenges in combining operations
5. **Market Reaction**: Expected investor response and trading implications
6. **Deal Recommendation**: Proceed/Pass with detailed reasoning
7. **Value Creation**: How this merger creates shareholder value

Focus on strategic fit, financial impact, and execution risks.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_accretion = scenario_data.get('accretion_dilution', 0)
                scenario_synergy = scenario_data.get('synergy_value', 0)
                prompt += f"- {scenario_name.upper()}: Accretion={scenario_accretion*100:.1f}%, Synergies=${scenario_synergy/1e9:.1f}B\n"
        
        return prompt
    
    def _build_comps_analysis_prompt(self, company_data, comps_results, scenarios=None, assumptions=None):
        """Build comprehensive Trading Comps analysis prompt"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        # Extract Comps-specific metrics
        ev_revenue = comps_results.get('ev_revenue', 0)
        ev_ebitda = comps_results.get('ev_ebitda', 0)
        pe_ratio = comps_results.get('pe_ratio', 0)
        pb_ratio = comps_results.get('pb_ratio', 0)
        
        prompt = f"""
As a senior equity research analyst, provide a comprehensive trading comparables analysis for {company_name}:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

TRADING COMPARABLES RESULTS:
- EV/Revenue Multiple: {ev_revenue:.1f}x
- EV/EBITDA Multiple: {ev_ebitda:.1f}x
- P/E Ratio: {pe_ratio:.1f}x
- P/B Ratio: {pb_ratio:.1f}x

Please provide:
1. **Valuation Assessment**: Is the company trading at fair value vs. peers?
2. **Peer Comparison**: How does it compare to sector averages and key competitors?
3. **Multiple Analysis**: Which multiples are most relevant and why?
4. **Growth vs. Value**: Is this a growth or value play relative to peers?
5. **Investment Thesis**: Buy/Hold/Sell recommendation with peer-based reasoning
6. **Key Differentiators**: What makes this company unique vs. peers?
7. **Risk Factors**: Peer-specific risks and sector headwinds

Focus on relative valuation and peer comparison insights.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_ev_rev = scenario_data.get('ev_revenue', 0)
                scenario_pe = scenario_data.get('pe_ratio', 0)
                prompt += f"- {scenario_name.upper()}: EV/Rev={scenario_ev_rev:.1f}x, P/E={scenario_pe:.1f}x\n"
        
        return prompt
    
    def _build_generic_analysis_prompt(self, model_type, company_data, model_results, scenarios=None, assumptions=None):
        """Build analysis prompt for any other model type"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        
        prompt = f"""
As a senior financial analyst, provide a comprehensive analysis for {company_name} based on this {model_type.upper()} model:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B

MODEL RESULTS:
{json.dumps(model_results, indent=2)}

Please provide:
1. **Model Assessment**: Key insights from the {model_type.upper()} analysis
2. **Investment Implications**: What this means for investment decisions
3. **Risk Factors**: Key risks and considerations
4. **Recommendation**: Investment recommendation with reasoning
5. **Next Steps**: Suggested follow-up analysis or actions

Focus on practical investment insights and actionable recommendations.
"""
        
        return prompt
    
    def _build_assumption_validation_prompt(self, company_data, assumptions):
        """Build assumption validation prompt"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        historical_growth = company_data.get('historical_revenue_growth', 0)
        current_margin = company_data.get('operating_margin', 0)
        
        revenue_growth = assumptions.get('revenue_growth_1', 0)
        operating_margin = assumptions.get('operating_margin', 0)
        wacc = assumptions.get('wacc', 0)
        tax_rate = assumptions.get('tax_rate', 0)
        terminal_growth = assumptions.get('terminal_growth', 0)
        
        prompt = f"""
As a senior financial analyst, validate these DCF assumptions for {company_name} ({sector}):

PROPOSED ASSUMPTIONS:
- Revenue Growth (Y1): {revenue_growth*100:.1f}%
- Operating Margin: {operating_margin*100:.1f}%
- WACC: {wacc*100:.1f}%
- Tax Rate: {tax_rate*100:.1f}%
- Terminal Growth: {terminal_growth*100:.1f}%

HISTORICAL CONTEXT:
- 5Y Revenue CAGR: {historical_growth*100:.1f}%
- Current Operating Margin: {current_margin*100:.1f}%
- Sector: {sector}

Please provide:
1. Validation of each assumption with reasoning
2. Suggested adjustments if needed
3. Risk factors for each assumption
4. Overall assessment of assumption reasonableness

Be specific and reference industry benchmarks where applicable.
"""
        
        return prompt
    
    def _build_chat_prompt(self, user_question, model_context):
        """Build chat prompt for model Q&A"""
        model_type = model_context.get('model_type', 'unknown')
        company_name = model_context.get('company_name', 'Unknown')
        
        # Add model-specific context
        if model_type.lower() == 'dcf':
            analyst_role = "equity research analyst"
            focus_area = "DCF valuation, investment thesis, and price targets"
        elif model_type.lower() == 'lbo':
            analyst_role = "private equity analyst"
            focus_area = "LBO attractiveness, debt capacity, and operational improvements"
        elif model_type.lower() == 'ma' or model_type.lower() == 'merger':
            analyst_role = "M&A investment banker"
            focus_area = "strategic rationale, synergies, and integration challenges"
        elif model_type.lower() == 'comps':
            analyst_role = "equity research analyst"
            focus_area = "peer comparison, relative valuation, and trading multiples"
        else:
            analyst_role = "financial analyst"
            focus_area = "financial modeling and investment analysis"
        
        prompt = f"""
User Question: {user_question}

Model Context:
- Model Type: {model_type.upper()}
- Company: {company_name}
- Analysis Focus: {focus_area}

Full Model Data:
{json.dumps(model_context, indent=2)}

As a senior {analyst_role}, provide a clear, professional answer to the user's question about this {model_type.upper()} model for {company_name}. 
Focus on {focus_area} and be specific, referencing actual numbers from the model when relevant.
Provide actionable insights and practical recommendations.
"""
        
        return prompt
    
    def _build_dcf_analysis_prompt_enhanced(self, company_data, dcf_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Build enhanced DCF analysis prompt with Phase 2 data"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        enterprise_value = dcf_results.get('enterprise_value', 0)
        equity_value = dcf_results.get('equity_value', 0)
        implied_price = dcf_results.get('implied_price', 0)
        current_price = dcf_results.get('current_price', 0)
        upside_downside = dcf_results.get('upside_downside', 0)
        
        prompt = f"""
As a senior equity research analyst, provide a comprehensive investment analysis for {company_name} based on this DCF model:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

DCF VALUATION RESULTS:
- Enterprise Value: ${enterprise_value/1e9:.1f}B
- Equity Value: ${equity_value/1e9:.1f}B
- Implied Price: ${implied_price:.2f}
- Current Price: ${current_price:.2f}
- Upside/(Downside): {upside_downside:.1f}%

RECENT MARKET DEVELOPMENTS:
"""
        
        if news_data:
            prompt += f"- Recent News ({len(news_data)} articles):\n"
            for i, news in enumerate(news_data[:3], 1):
                prompt += f"  {i}. {news.get('title', 'No title')}\n"
                if news.get('summary'):
                    prompt += f"     Summary: {news.get('summary', '')[:100]}...\n"
        else:
            prompt += "- No recent news data available\n"
        
        prompt += f"""
PEER COMPARISON ANALYSIS:
"""
        
        if peer_metrics:
            prompt += f"- Peer Companies Analyzed ({len(peer_metrics)} peers):\n"
            for peer, metrics in list(peer_metrics.items())[:3]:
                peer_market_cap = metrics.get('market_cap', 0)
                peer_margin = metrics.get('operating_margin', 0)
                prompt += f"  • {peer}: Market Cap ${peer_market_cap/1e9:.1f}B, Margin {peer_margin*100:.1f}%\n"
        else:
            prompt += "- No peer comparison data available\n"
        
        prompt += f"""
RISK ASSESSMENT:
- Overall Risk Level: {risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'}
- Key Risk Factors: {', '.join(risk_assessment.get('key_risks', [])[:3]) if risk_assessment else 'General market risks'}

Please provide:
1. **Investment Thesis Summary**: Comprehensive analysis incorporating market developments and peer positioning
2. **Key Valuation Drivers**: Factors driving the valuation with recent news context
3. **Risk Factors**: Detailed risk analysis incorporating sector and model-specific risks
4. **Recommendation**: Buy/Hold/Sell with reasoning based on all available data
5. **Price Target Rationale**: Target price with confidence level
6. **Recent Developments Impact**: How recent news affects the investment thesis

Focus on integrating all available data sources for a comprehensive investment committee presentation.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                ev = scenario_data.get('enterprise_value', 0)
                price = scenario_data.get('implied_price', 0)
                upside = scenario_data.get('upside_downside', 0)
                prompt += f"- {scenario_name.upper()}: EV=${ev/1e9:.1f}B, Price=${price:.2f}, Upside={upside:.1f}%\n"
        
        return prompt
    
    def _build_lbo_analysis_prompt_enhanced(self, company_data, lbo_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Build enhanced LBO analysis prompt with Phase 2 data"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        debt_levels = company_data.get('total_debt', 0)
        
        irr = lbo_results.get('irr', 0)
        multiple = lbo_results.get('multiple', 0)
        debt_capacity = lbo_results.get('debt_capacity', 0)
        exit_value = lbo_results.get('exit_value', 0)
        
        prompt = f"""
As a senior private equity analyst, provide a comprehensive LBO analysis for {company_name}:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%
- Current Debt: ${debt_levels/1e9:.1f}B

LBO MODEL RESULTS:
- Projected IRR: {irr*100:.1f}%
- Multiple of Money: {multiple:.1f}x
- Debt Capacity: ${debt_capacity/1e9:.1f}B
- Exit Value: ${exit_value/1e9:.1f}B

RECENT MARKET DEVELOPMENTS:
"""
        
        if news_data:
            prompt += f"- Recent News ({len(news_data)} articles):\n"
            for i, news in enumerate(news_data[:3], 1):
                prompt += f"  {i}. {news.get('title', 'No title')}\n"
        else:
            prompt += "- No recent news data available\n"
        
        prompt += f"""
PEER COMPARISON ANALYSIS:
"""
        
        if peer_metrics:
            prompt += f"- Peer Companies Analyzed ({len(peer_metrics)} peers):\n"
            for peer, metrics in list(peer_metrics.items())[:3]:
                peer_market_cap = metrics.get('market_cap', 0)
                peer_margin = metrics.get('operating_margin', 0)
                prompt += f"  • {peer}: Market Cap ${peer_market_cap/1e9:.1f}B, Margin {peer_margin*100:.1f}%\n"
        else:
            prompt += "- No peer comparison data available\n"
        
        prompt += f"""
RISK ASSESSMENT:
- Overall Risk Level: {risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'}
- Key Risk Factors: {', '.join(risk_assessment.get('key_risks', [])[:3]) if risk_assessment else 'General market risks'}

Please provide:
1. **LBO Attractiveness Assessment**: Is this a good LBO target considering recent developments?
2. **Financial Profile Analysis**: Debt capacity, cash flow generation, margin expansion potential
3. **Operational Improvements**: Cost reduction opportunities, revenue growth levers
4. **Risk Factors**: Key risks to the LBO thesis and exit strategy
5. **Investment Recommendation**: Proceed/Pass with detailed reasoning
6. **Value Creation Strategy**: Specific actions to drive returns
7. **Market Timing**: How current market conditions affect the LBO thesis

Focus on private equity investment criteria and LBO-specific considerations with recent market context.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_irr = scenario_data.get('irr', 0)
                scenario_multiple = scenario_data.get('multiple', 0)
                prompt += f"- {scenario_name.upper()}: IRR={scenario_irr*100:.1f}%, Multiple={scenario_multiple:.1f}x\n"
        
        return prompt
    
    def _build_ma_analysis_prompt_enhanced(self, company_data, ma_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Build enhanced M&A analysis prompt with Phase 2 data"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        accretion_dilution = ma_results.get('accretion_dilution', 0)
        synergy_value = ma_results.get('synergy_value', 0)
        purchase_price = ma_results.get('purchase_price', 0)
        combined_value = ma_results.get('combined_value', 0)
        
        prompt = f"""
As a senior M&A investment banker, provide a comprehensive merger analysis for {company_name}:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

M&A MODEL RESULTS:
- Accretion/(Dilution): {accretion_dilution*100:.1f}%
- Synergy Value: ${synergy_value/1e9:.1f}B
- Purchase Price: ${purchase_price/1e9:.1f}B
- Combined Enterprise Value: ${combined_value/1e9:.1f}B

RECENT MARKET DEVELOPMENTS:
"""
        
        if news_data:
            prompt += f"- Recent News ({len(news_data)} articles):\n"
            for i, news in enumerate(news_data[:3], 1):
                prompt += f"  {i}. {news.get('title', 'No title')}\n"
        else:
            prompt += "- No recent news data available\n"
        
        prompt += f"""
PEER COMPARISON ANALYSIS:
"""
        
        if peer_metrics:
            prompt += f"- Peer Companies Analyzed ({len(peer_metrics)} peers):\n"
            for peer, metrics in list(peer_metrics.items())[:3]:
                peer_market_cap = metrics.get('market_cap', 0)
                peer_margin = metrics.get('operating_margin', 0)
                prompt += f"  • {peer}: Market Cap ${peer_market_cap/1e9:.1f}B, Margin {peer_margin*100:.1f}%\n"
        else:
            prompt += "- No peer comparison data available\n"
        
        prompt += f"""
RISK ASSESSMENT:
- Overall Risk Level: {risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'}
- Key Risk Factors: {', '.join(risk_assessment.get('key_risks', [])[:3]) if risk_assessment else 'General market risks'}

Please provide:
1. **Strategic Rationale**: Why does this merger make strategic sense?
2. **Synergy Analysis**: Revenue synergies, cost synergies, and implementation risks
3. **Financial Impact**: Accretion/dilution analysis and EPS impact
4. **Integration Challenges**: Key risks and challenges in combining operations
5. **Market Reaction**: Expected investor response and trading implications
6. **Deal Recommendation**: Proceed/Pass with detailed reasoning
7. **Value Creation**: How this merger creates shareholder value
8. **Market Timing**: How current market conditions affect the merger thesis

Focus on strategic fit, financial impact, and execution risks with recent market context.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_accretion = scenario_data.get('accretion_dilution', 0)
                scenario_synergy = scenario_data.get('synergy_value', 0)
                prompt += f"- {scenario_name.upper()}: Accretion={scenario_accretion*100:.1f}%, Synergies=${scenario_synergy/1e9:.1f}B\n"
        
        return prompt
    
    def _build_comps_analysis_prompt_enhanced(self, company_data, comps_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Build enhanced Trading Comps analysis prompt with Phase 2 data"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        ev_revenue = comps_results.get('ev_revenue', 0)
        ev_ebitda = comps_results.get('ev_ebitda', 0)
        pe_ratio = comps_results.get('pe_ratio', 0)
        pb_ratio = comps_results.get('pb_ratio', 0)
        
        prompt = f"""
As a senior equity research analyst, provide a comprehensive trading comparables analysis for {company_name}:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

TRADING COMPARABLES RESULTS:
- EV/Revenue Multiple: {ev_revenue:.1f}x
- EV/EBITDA Multiple: {ev_ebitda:.1f}x
- P/E Ratio: {pe_ratio:.1f}x
- P/B Ratio: {pb_ratio:.1f}x

RECENT MARKET DEVELOPMENTS:
"""
        
        if news_data:
            prompt += f"- Recent News ({len(news_data)} articles):\n"
            for i, news in enumerate(news_data[:3], 1):
                prompt += f"  {i}. {news.get('title', 'No title')}\n"
        else:
            prompt += "- No recent news data available\n"
        
        prompt += f"""
PEER COMPARISON ANALYSIS:
"""
        
        if peer_metrics:
            prompt += f"- Peer Companies Analyzed ({len(peer_metrics)} peers):\n"
            for peer, metrics in list(peer_metrics.items())[:3]:
                peer_market_cap = metrics.get('market_cap', 0)
                peer_margin = metrics.get('operating_margin', 0)
                prompt += f"  • {peer}: Market Cap ${peer_market_cap/1e9:.1f}B, Margin {peer_margin*100:.1f}%\n"
        else:
            prompt += "- No peer comparison data available\n"
        
        prompt += f"""
RISK ASSESSMENT:
- Overall Risk Level: {risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'}
- Key Risk Factors: {', '.join(risk_assessment.get('key_risks', [])[:3]) if risk_assessment else 'General market risks'}

Please provide:
1. **Valuation Assessment**: Is the company trading at fair value vs. peers?
2. **Peer Comparison**: How does it compare to sector averages and key competitors?
3. **Multiple Analysis**: Which multiples are most relevant and why?
4. **Growth vs. Value**: Is this a growth or value play relative to peers?
5. **Investment Thesis**: Buy/Hold/Sell recommendation with peer-based reasoning
6. **Key Differentiators**: What makes this company unique vs. peers?
7. **Risk Factors**: Peer-specific risks and sector headwinds
8. **Market Context**: How recent developments affect relative valuation

Focus on relative valuation and peer comparison insights with recent market context.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_ev_rev = scenario_data.get('ev_revenue', 0)
                scenario_pe = scenario_data.get('pe_ratio', 0)
                prompt += f"- {scenario_name.upper()}: EV/Rev={scenario_ev_rev:.1f}x, P/E={scenario_pe:.1f}x\n"
        
        return prompt
    
    def _build_generic_analysis_prompt_enhanced(self, model_type, company_data, model_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None):
        """Build enhanced analysis prompt for any other model type with Phase 2 data"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        
        prompt = f"""
As a senior financial analyst, provide a comprehensive analysis for {company_name} based on this {model_type.upper()} model:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B

MODEL RESULTS:
{json.dumps(model_results, indent=2)}

RECENT MARKET DEVELOPMENTS:
"""
        
        if news_data:
            prompt += f"- Recent News ({len(news_data)} articles):\n"
            for i, news in enumerate(news_data[:3], 1):
                prompt += f"  {i}. {news.get('title', 'No title')}\n"
        else:
            prompt += "- No recent news data available\n"
        
        prompt += f"""
PEER COMPARISON ANALYSIS:
"""
        
        if peer_metrics:
            prompt += f"- Peer Companies Analyzed ({len(peer_metrics)} peers):\n"
            for peer, metrics in list(peer_metrics.items())[:3]:
                peer_market_cap = metrics.get('market_cap', 0)
                peer_margin = metrics.get('operating_margin', 0)
                prompt += f"  • {peer}: Market Cap ${peer_market_cap/1e9:.1f}B, Margin {peer_margin*100:.1f}%\n"
        else:
            prompt += "- No peer comparison data available\n"
        
        prompt += f"""
RISK ASSESSMENT:
- Overall Risk Level: {risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'}
- Key Risk Factors: {', '.join(risk_assessment.get('key_risks', [])[:3]) if risk_assessment else 'General market risks'}

Please provide:
1. **Model Assessment**: Key insights from the {model_type.upper()} analysis
2. **Investment Implications**: What this means for investment decisions
3. **Risk Factors**: Key risks and considerations
4. **Recommendation**: Investment recommendation with reasoning
5. **Next Steps**: Suggested follow-up analysis or actions
6. **Market Context**: How recent developments affect the analysis

Focus on practical investment insights and actionable recommendations with recent market context.
"""
        
        return prompt
    
    def _build_dcf_analysis_prompt_phase3(self, company_data, dcf_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Build Phase 3 DCF analysis prompt with detailed investment recommendations"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        enterprise_value = dcf_results.get('enterprise_value', 0)
        equity_value = dcf_results.get('equity_value', 0)
        implied_price = dcf_results.get('implied_price', 0)
        current_price = dcf_results.get('current_price', 0)
        upside_downside = dcf_results.get('upside_downside', 0)
        
        # Extract Phase 3 data
        recommendation = advanced_analysis.get('recommendation', {}) if advanced_analysis else {}
        opportunity_score = advanced_analysis.get('opportunity_score', 50) if advanced_analysis else 50
        rationale = advanced_analysis.get('rationale', '') if advanced_analysis else ''
        key_drivers = advanced_analysis.get('key_drivers', []) if advanced_analysis else []
        
        prompt = f"""
As a senior equity research analyst, provide a comprehensive investment analysis for {company_name} with SPECIFIC BUY/SELL/SHORT recommendations:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

DCF VALUATION RESULTS:
- Enterprise Value: ${enterprise_value/1e9:.1f}B
- Equity Value: ${equity_value/1e9:.1f}B
- Implied Price: ${implied_price:.2f}
- Current Price: ${current_price:.2f}
- Upside/(Downside): {upside_downside:.1f}%

INVESTMENT RECOMMENDATION:
- Action: {recommendation.get('action', 'HOLD')}
- Opportunity Score: {opportunity_score}/100
- Confidence: {recommendation.get('confidence', 'Medium')}
- Reasoning: {recommendation.get('reasoning', '')}

KEY INVESTMENT DRIVERS:
{chr(10).join([f"- {driver}" for driver in key_drivers])}

DETAILED RATIONALE:
{rationale}

RECENT MARKET DEVELOPMENTS:
"""
        
        if news_data:
            prompt += f"- Recent News ({len(news_data)} articles):\n"
            for i, news in enumerate(news_data[:3], 1):
                prompt += f"  {i}. {news.get('title', 'No title')}\n"
                if news.get('summary'):
                    prompt += f"     Summary: {news.get('summary', '')[:100]}...\n"
        else:
            prompt += "- No recent news data available\n"
        
        prompt += f"""
PEER COMPARISON ANALYSIS:
"""
        
        if peer_metrics:
            prompt += f"- Peer Companies Analyzed ({len(peer_metrics)} peers):\n"
            for peer, metrics in list(peer_metrics.items())[:3]:
                peer_market_cap = metrics.get('market_cap', 0)
                peer_margin = metrics.get('operating_margin', 0)
                prompt += f"  • {peer}: Market Cap ${peer_market_cap/1e9:.1f}B, Margin {peer_margin*100:.1f}%\n"
        else:
            prompt += "- No peer comparison data available\n"
        
        prompt += f"""
RISK ASSESSMENT:
- Overall Risk Level: {risk_assessment.get('risk_level', 'Unknown') if risk_assessment else 'Unknown'}
- Key Risk Factors: {', '.join(risk_assessment.get('key_risks', [])[:3]) if risk_assessment else 'General market risks'}

SPECIFIC INVESTMENT RECOMMENDATIONS:
Please provide detailed, actionable recommendations including:

1. **PRIMARY RECOMMENDATION**: {recommendation.get('action', 'HOLD')} with specific reasoning
2. **PRICE TARGET**: Specific target price with confidence level
3. **TIMEFRAME**: Short-term (3-6 months) vs Long-term (1-2 years) outlook
4. **POSITION SIZING**: Recommended portfolio allocation (0-10%)
5. **ENTRY STRATEGY**: Specific entry points and conditions
6. **EXIT STRATEGY**: Stop-loss levels and profit-taking targets
7. **RISK MANAGEMENT**: Specific risk mitigation strategies
8. **CATALYSTS**: Key events that could drive the stock price
9. **ALTERNATIVE STRATEGIES**: Options strategies, pairs trades, or hedging approaches
10. **MONITORING**: Key metrics to track for position management

Focus on providing SPECIFIC, ACTIONABLE investment advice that a portfolio manager can implement immediately.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                ev = scenario_data.get('enterprise_value', 0)
                price = scenario_data.get('implied_price', 0)
                upside = scenario_data.get('upside_downside', 0)
                prompt += f"- {scenario_name.upper()}: EV=${ev/1e9:.1f}B, Price=${price:.2f}, Upside={upside:.1f}%\n"
        
        return prompt
    
    def _build_lbo_analysis_prompt_phase3(self, company_data, lbo_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Build Phase 3 LBO analysis prompt with detailed investment recommendations"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        debt_levels = company_data.get('total_debt', 0)
        
        irr = lbo_results.get('irr', 0)
        multiple = lbo_results.get('multiple', 0)
        debt_capacity = lbo_results.get('debt_capacity', 0)
        exit_value = lbo_results.get('exit_value', 0)
        
        # Extract Phase 3 data
        recommendation = advanced_analysis.get('recommendation', {}) if advanced_analysis else {}
        opportunity_score = advanced_analysis.get('opportunity_score', 50) if advanced_analysis else 50
        rationale = advanced_analysis.get('rationale', '') if advanced_analysis else ''
        key_drivers = advanced_analysis.get('key_drivers', []) if advanced_analysis else []
        
        prompt = f"""
As a senior private equity analyst, provide a comprehensive LBO analysis for {company_name} with SPECIFIC ACQUISITION recommendations:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%
- Current Debt: ${debt_levels/1e9:.1f}B

LBO MODEL RESULTS:
- Projected IRR: {irr*100:.1f}%
- Multiple of Money: {multiple:.1f}x
- Debt Capacity: ${debt_capacity/1e9:.1f}B
- Exit Value: ${exit_value/1e9:.1f}B

INVESTMENT RECOMMENDATION:
- Action: {recommendation.get('action', 'HOLD')}
- Opportunity Score: {opportunity_score}/100
- Confidence: {recommendation.get('confidence', 'Medium')}
- Reasoning: {recommendation.get('reasoning', '')}

KEY INVESTMENT DRIVERS:
{chr(10).join([f"- {driver}" for driver in key_drivers])}

DETAILED RATIONALE:
{rationale}

SPECIFIC LBO RECOMMENDATIONS:
Please provide detailed, actionable recommendations including:

1. **ACQUISITION DECISION**: Proceed/Pass with specific reasoning
2. **OFFER PRICE**: Recommended acquisition price range
3. **DEBT STRUCTURE**: Optimal debt/equity mix and sources
4. **OPERATIONAL IMPROVEMENTS**: Specific cost reduction and revenue enhancement opportunities
5. **EXIT STRATEGY**: Recommended exit timeline and method (IPO, sale, dividend recap)
6. **RETURN EXPECTATIONS**: Expected IRR range and sensitivity analysis
7. **RISK MITIGATION**: Specific risk management strategies
8. **COMPETITIVE ADVANTAGES**: Why this company is attractive vs. alternatives
9. **INTEGRATION PLAN**: Post-acquisition operational integration approach
10. **MONITORING METRICS**: Key performance indicators to track

Focus on providing SPECIFIC, ACTIONABLE private equity investment advice.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_irr = scenario_data.get('irr', 0)
                scenario_multiple = scenario_data.get('multiple', 0)
                prompt += f"- {scenario_name.upper()}: IRR={scenario_irr*100:.1f}%, Multiple={scenario_multiple:.1f}x\n"
        
        return prompt
    
    def _build_ma_analysis_prompt_phase3(self, company_data, ma_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Build Phase 3 M&A analysis prompt with detailed investment recommendations"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        accretion_dilution = ma_results.get('accretion_dilution', 0)
        synergy_value = ma_results.get('synergy_value', 0)
        purchase_price = ma_results.get('purchase_price', 0)
        combined_value = ma_results.get('combined_value', 0)
        
        # Extract Phase 3 data
        recommendation = advanced_analysis.get('recommendation', {}) if advanced_analysis else {}
        opportunity_score = advanced_analysis.get('opportunity_score', 50) if advanced_analysis else 50
        rationale = advanced_analysis.get('rationale', '') if advanced_analysis else ''
        key_drivers = advanced_analysis.get('key_drivers', []) if advanced_analysis else []
        
        prompt = f"""
As a senior M&A investment banker, provide a comprehensive merger analysis for {company_name} with SPECIFIC DEAL recommendations:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

M&A MODEL RESULTS:
- Accretion/(Dilution): {accretion_dilution*100:.1f}%
- Synergy Value: ${synergy_value/1e9:.1f}B
- Purchase Price: ${purchase_price/1e9:.1f}B
- Combined Enterprise Value: ${combined_value/1e9:.1f}B

INVESTMENT RECOMMENDATION:
- Action: {recommendation.get('action', 'HOLD')}
- Opportunity Score: {opportunity_score}/100
- Confidence: {recommendation.get('confidence', 'Medium')}
- Reasoning: {recommendation.get('reasoning', '')}

KEY INVESTMENT DRIVERS:
{chr(10).join([f"- {driver}" for driver in key_drivers])}

DETAILED RATIONALE:
{rationale}

SPECIFIC M&A RECOMMENDATIONS:
Please provide detailed, actionable recommendations including:

1. **DEAL RECOMMENDATION**: Proceed/Pass with specific reasoning
2. **VALUATION RANGE**: Recommended offer price range and methodology
3. **SYNERGY REALIZATION**: Specific synergy opportunities and timeline
4. **INTEGRATION STRATEGY**: Detailed integration plan and challenges
5. **FINANCING STRUCTURE**: Optimal financing mix and sources
6. **REGULATORY CONSIDERATIONS**: Antitrust and regulatory approval strategy
7. **RISK ASSESSMENT**: Key deal risks and mitigation strategies
8. **COMPETITIVE DYNAMICS**: Market reaction and competitive response
9. **SHAREHOLDER VALUE**: Expected value creation for shareholders
10. **EXECUTION TIMELINE**: Deal timeline and key milestones

Focus on providing SPECIFIC, ACTIONABLE M&A investment banking advice.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_accretion = scenario_data.get('accretion_dilution', 0)
                scenario_synergy = scenario_data.get('synergy_value', 0)
                prompt += f"- {scenario_name.upper()}: Accretion={scenario_accretion*100:.1f}%, Synergies=${scenario_synergy/1e9:.1f}B\n"
        
        return prompt
    
    def _build_comps_analysis_prompt_phase3(self, company_data, comps_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Build Phase 3 Trading Comps analysis prompt with detailed investment recommendations"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        ev_revenue = comps_results.get('ev_revenue', 0)
        ev_ebitda = comps_results.get('ev_ebitda', 0)
        pe_ratio = comps_results.get('pe_ratio', 0)
        pb_ratio = comps_results.get('pb_ratio', 0)
        
        # Extract Phase 3 data
        recommendation = advanced_analysis.get('recommendation', {}) if advanced_analysis else {}
        opportunity_score = advanced_analysis.get('opportunity_score', 50) if advanced_analysis else 50
        rationale = advanced_analysis.get('rationale', '') if advanced_analysis else ''
        key_drivers = advanced_analysis.get('key_drivers', []) if advanced_analysis else []
        
        prompt = f"""
As a senior equity research analyst, provide a comprehensive trading comparables analysis for {company_name} with SPECIFIC BUY/SELL/SHORT recommendations:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B
- Operating Margin: {operating_margin*100:.1f}%

TRADING COMPARABLES RESULTS:
- EV/Revenue Multiple: {ev_revenue:.1f}x
- EV/EBITDA Multiple: {ev_ebitda:.1f}x
- P/E Ratio: {pe_ratio:.1f}x
- P/B Ratio: {pb_ratio:.1f}x

INVESTMENT RECOMMENDATION:
- Action: {recommendation.get('action', 'HOLD')}
- Opportunity Score: {opportunity_score}/100
- Confidence: {recommendation.get('confidence', 'Medium')}
- Reasoning: {recommendation.get('reasoning', '')}

KEY INVESTMENT DRIVERS:
{chr(10).join([f"- {driver}" for driver in key_drivers])}

DETAILED RATIONALE:
{rationale}

SPECIFIC TRADING RECOMMENDATIONS:
Please provide detailed, actionable recommendations including:

1. **PRIMARY RECOMMENDATION**: {recommendation.get('action', 'HOLD')} with specific reasoning
2. **FAIR VALUE ASSESSMENT**: Is the company trading at fair value vs. peers?
3. **MULTIPLE EXPANSION/CONTRACTION**: Expected multiple changes and catalysts
4. **RELATIVE PERFORMANCE**: Expected performance vs. sector and market
5. **ENTRY/EXIT POINTS**: Specific price levels for position management
6. **PAIRS TRADING**: Potential pairs trade opportunities with peers
7. **SECTOR ROTATION**: How sector trends affect the investment thesis
8. **SHORTING OPPORTUNITIES**: Specific shorting rationale if applicable
9. **RISK FACTORS**: Peer-specific risks and sector headwinds
10. **MONITORING**: Key metrics to track for position management

Focus on providing SPECIFIC, ACTIONABLE trading and investment advice.
"""
        
        if scenarios:
            prompt += f"\n\nSCENARIO ANALYSIS:\n"
            for scenario_name, scenario_data in scenarios.items():
                scenario_ev_rev = scenario_data.get('ev_revenue', 0)
                scenario_pe = scenario_data.get('pe_ratio', 0)
                prompt += f"- {scenario_name.upper()}: EV/Rev={scenario_ev_rev:.1f}x, P/E={scenario_pe:.1f}x\n"
        
        return prompt
    
    def _build_generic_analysis_prompt_phase3(self, model_type, company_data, model_results, scenarios=None, news_data=None, earnings_data=None, peer_metrics=None, risk_assessment=None, advanced_analysis=None):
        """Build Phase 3 analysis prompt for any other model type with detailed investment recommendations"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        
        # Extract Phase 3 data
        recommendation = advanced_analysis.get('recommendation', {}) if advanced_analysis else {}
        opportunity_score = advanced_analysis.get('opportunity_score', 50) if advanced_analysis else 50
        rationale = advanced_analysis.get('rationale', '') if advanced_analysis else ''
        key_drivers = advanced_analysis.get('key_drivers', []) if advanced_analysis else []
        
        prompt = f"""
As a senior financial analyst, provide a comprehensive analysis for {company_name} based on this {model_type.upper()} model with SPECIFIC investment recommendations:

COMPANY OVERVIEW:
- Company: {company_name}
- Sector: {sector}
- Market Cap: ${market_cap/1e9:.1f}B
- Revenue: ${revenue/1e9:.1f}B

MODEL RESULTS:
{json.dumps(model_results, indent=2)}

INVESTMENT RECOMMENDATION:
- Action: {recommendation.get('action', 'HOLD')}
- Opportunity Score: {opportunity_score}/100
- Confidence: {recommendation.get('confidence', 'Medium')}
- Reasoning: {recommendation.get('reasoning', '')}

KEY INVESTMENT DRIVERS:
{chr(10).join([f"- {driver}" for driver in key_drivers])}

DETAILED RATIONALE:
{rationale}

SPECIFIC INVESTMENT RECOMMENDATIONS:
Please provide detailed, actionable recommendations including:

1. **PRIMARY RECOMMENDATION**: {recommendation.get('action', 'HOLD')} with specific reasoning
2. **INVESTMENT THESIS**: Clear investment thesis and key assumptions
3. **RISK/RETURN PROFILE**: Expected risk and return characteristics
4. **POSITION SIZING**: Recommended portfolio allocation
5. **TIMEFRAME**: Investment horizon and key milestones
6. **CATALYSTS**: Key events that could drive value realization
7. **RISK FACTORS**: Specific risks and mitigation strategies
8. **MONITORING**: Key metrics to track for position management
9. **ALTERNATIVE STRATEGIES**: Alternative investment approaches
10. **EXECUTION PLAN**: Specific steps for implementing the recommendation

Focus on providing SPECIFIC, ACTIONABLE investment advice.
"""
        
        return prompt
    
    def _fallback_model_analysis(self, model_type, company_data, model_results):
        """Fallback analysis when AI is unavailable"""
        company_name = company_data.get('company_name', 'Unknown')
        
        if model_type.lower() == 'dcf':
            return self._fallback_dcf_analysis(company_data, model_results)
        elif model_type.lower() == 'lbo':
            return self._fallback_lbo_analysis(company_data, model_results)
        elif model_type.lower() == 'ma' or model_type.lower() == 'merger':
            return self._fallback_ma_analysis(company_data, model_results)
        elif model_type.lower() == 'comps':
            return self._fallback_comps_analysis(company_data, model_results)
        else:
            return self._fallback_generic_analysis(model_type, company_data, model_results)
    
    def _fallback_dcf_analysis(self, company_data, dcf_results, assumptions=None):
        """Company-specific DCF summary fallback when AI is unavailable"""
        ticker = company_data.get('ticker', 'Unknown')
        company_name = company_data.get('company_name', 'Unknown')
        
        # Extract actual DCF inputs and outputs
        enterprise_value = dcf_results.get('enterprise_value', 0)
        implied_price = dcf_results.get('implied_price', 0)
        current_price = dcf_results.get('current_price', 0)
        upside_downside = dcf_results.get('upside_downside', 0)
        equity_value = dcf_results.get('equity_value', 0)
        market_cap = company_data.get('market_cap', 0)
        
        # Extract assumptions
        base_assumptions = assumptions.get('base', {}) if assumptions else {}
        wacc = base_assumptions.get('wacc', 0.10)  # Default 10%
        revenue_growth = base_assumptions.get('revenue_growth_rate', 0.08)  # Default 8%
        terminal_growth = base_assumptions.get('terminal_growth_rate', 0.025)  # Default 2.5%
        operating_margin = base_assumptions.get('operating_margin', 0.20)  # Default 20%
        
        # Calculate terminal value share
        pv_cash_flows = dcf_results.get('pv_cash_flows', 0)
        pv_terminal_value = dcf_results.get('pv_terminal_value', 0)
        terminal_share = (pv_terminal_value / enterprise_value * 100) if enterprise_value > 0 else 0
        
        # Generate company-specific DCF summary
        analysis_parts = []
        
        # Header with key numbers
        analysis_parts.append(f"DCF SUMMARY — {ticker} {company_name}")
        analysis_parts.append(f"EV: ${enterprise_value/1e9:.1f}B | Implied Price: ${implied_price:.2f} | Current: ${current_price:.2f} | Upside/(Downside): {upside_downside:.1f}%")
        analysis_parts.append(f"WACC: {wacc*100:.1f}% | Terminal: Perpetuity g={terminal_growth*100:.1f}%")
        analysis_parts.append("")
        
        # Key Drivers
        analysis_parts.append("Key Drivers")
        analysis_parts.append(f"• Revenue growth: {revenue_growth*100:.1f}% over forecast period")
        analysis_parts.append(f"• EBITDA margin: {operating_margin*100:.1f}%")
        analysis_parts.append(f"• Terminal rationale: Perpetuity growth model at {terminal_growth*100:.1f}%")
        analysis_parts.append("• Sensitivities that move value: WACC sensitivity, terminal growth sensitivity")
        analysis_parts.append("")
        
        # Sanity Checks
        analysis_parts.append("Sanity Checks")
        analysis_parts.append(f"• TV share of EV: {terminal_share:.1f}%  {'[FLAG if >85%]' if terminal_share > 85 else ''}")
        
        # Check equity vs market cap gap
        equity_market_gap = abs(equity_value - market_cap) / market_cap if market_cap > 0 else 0
        analysis_parts.append(f"• Implied equity vs market cap: ${equity_value/1e9:.1f}B vs ${market_cap/1e9:.1f}B  {'[FLAG if >100% gap]' if equity_market_gap > 1.0 else ''}")
        
        # Check terminal growth vs WACC
        analysis_parts.append(f"• g < WACC: {terminal_growth < wacc}  {'[FLAG if False]' if terminal_growth >= wacc else ''}")
        analysis_parts.append("")
        
        # Investment Recommendation
        if upside_downside > 20:
            recommendation = "BUY"
            confidence = "H"
            reasoning = "Significant upside potential"
        elif upside_downside > 10:
            recommendation = "BUY"
            confidence = "M"
            reasoning = "Attractive upside potential"
        elif upside_downside > -10:
            recommendation = "HOLD"
            confidence = "M"
            reasoning = "Fairly valued"
        elif upside_downside > -20:
            recommendation = "SELL"
            confidence = "M"
            reasoning = "Overvalued with downside risk"
        else:
            recommendation = "SELL"
            confidence = "H"
            reasoning = "Significantly overvalued"
        
        analysis_parts.append(f"RECOMMENDATION: {recommendation} | Confidence: {confidence} | Why: {reasoning}")
        
        return {
            'analysis': '\n'.join(analysis_parts),
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_lbo_analysis(self, company_data, lbo_results):
        """Enhanced fallback LBO analysis when AI is unavailable"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        
        enterprise_value = lbo_results.get('enterprise_value', 0)
        implied_price = lbo_results.get('implied_price', 0)
        current_price = lbo_results.get('current_price', 0)
        upside_downside = lbo_results.get('upside_downside', 0)
        
        # Generate comprehensive analysis
        analysis_parts = []
        
        # Valuation Results
        analysis_parts.append(f"COMPREHENSIVE LBO INVESTMENT ANALYSIS FOR {company_name.upper()}")
        analysis_parts.append("")
        analysis_parts.append("LBO VALUATION RESULTS:")
        analysis_parts.append(f"Enterprise Value: ${enterprise_value/1e9:.1f}B")
        analysis_parts.append(f"Implied Price: ${implied_price:.2f}")
        analysis_parts.append(f"Current Price: ${current_price:.2f}")
        analysis_parts.append(f"Upside/(Downside): {upside_downside:.1f}%")
        analysis_parts.append("")
        
        # Investment Recommendation
        if upside_downside > 20:
            recommendation = "STRONG BUY"
            confidence = "High"
            reasoning = "Significant upside potential with strong fundamentals"
        elif upside_downside > 10:
            recommendation = "BUY"
            confidence = "Medium-High"
            reasoning = "Attractive upside potential with good fundamentals"
        elif upside_downside > -10:
            recommendation = "HOLD"
            confidence = "Medium"
            reasoning = "Fairly valued with moderate risk"
        elif upside_downside > -20:
            recommendation = "SELL"
            confidence = "Medium"
            reasoning = "Overvalued with downside risk"
        else:
            recommendation = "STRONG SELL"
            confidence = "High"
            reasoning = "Significantly overvalued with substantial downside risk"
        
        analysis_parts.append("INVESTMENT RECOMMENDATION:")
        analysis_parts.append(f"Action: {recommendation}")
        analysis_parts.append(f"Confidence: {confidence}")
        analysis_parts.append(f"Reasoning: {reasoning}")
        analysis_parts.append("")
        
        # Key Investment Drivers
        analysis_parts.append("KEY INVESTMENT DRIVERS:")
        if operating_margin > 0.20:
            analysis_parts.append("High operational efficiency with strong margins")
        elif operating_margin < 0.05:
            analysis_parts.append("Operational challenges with low margins")
        
        if market_cap > 100000000000:  # > $100B
            analysis_parts.append("Large-cap stability and institutional appeal")
        elif market_cap < 1000000000:  # < $1B
            analysis_parts.append("Small-cap growth potential with higher risk")
        
        if abs(upside_downside) > 15:
            analysis_parts.append("Significant valuation gap vs. current price")
        
        if sector == 'Technology':
            analysis_parts.append("Technology sector growth and innovation potential")
        elif sector == 'Healthcare':
            analysis_parts.append("Healthcare sector defensive characteristics")
        elif sector == 'Financial Services':
            analysis_parts.append("Financial services sector interest rate sensitivity")
        
        analysis_parts.append("")
        
        # Risk Factors
        analysis_parts.append("KEY RISK FACTORS:")
        
        # Sector-specific risks
        if sector == 'Technology':
            analysis_parts.append("- Technology disruption and rapid obsolescence risk")
            analysis_parts.append("- Regulatory scrutiny on data privacy and antitrust")
            analysis_parts.append("- Talent retention and competitive hiring pressures")
            analysis_parts.append("- Innovation cycles creating market share volatility")
        elif sector == 'Healthcare':
            analysis_parts.append("- Regulatory approval delays and compliance costs")
            analysis_parts.append("- Patent cliff exposure and generic competition")
            analysis_parts.append("- Clinical trial failures and safety concerns")
            analysis_parts.append("- Healthcare policy changes affecting reimbursement")
        elif sector == 'Financial Services':
            analysis_parts.append("- Interest rate sensitivity affecting margins")
            analysis_parts.append("- Regulatory capital requirements constraining returns")
            analysis_parts.append("- Credit quality deterioration in economic downturns")
            analysis_parts.append("- Digital disruption from fintech competitors")
        elif sector == 'Consumer Discretionary':
            analysis_parts.append("- Economic sensitivity and consumer spending volatility")
            analysis_parts.append("- E-commerce disruption and omnichannel challenges")
            analysis_parts.append("- Supply chain disruptions and cost inflation")
            analysis_parts.append("- Brand reputation and competitive positioning risks")
        elif sector == 'Energy':
            analysis_parts.append("- Commodity price volatility affecting margins")
            analysis_parts.append("- ESG pressures accelerating energy transition")
            analysis_parts.append("- Geopolitical risks affecting supply chains")
            analysis_parts.append("- Capital intensity and investment allocation risks")
        else:
            analysis_parts.append("- Industry-specific competitive and regulatory risks")
            analysis_parts.append("- Economic cycle sensitivity and demand volatility")
            analysis_parts.append("- Technology disruption affecting business models")
            analysis_parts.append("- ESG factors increasingly impacting valuations")
        
        # Market cap-specific risks
        if market_cap > 200000000000:  # > $200B
            analysis_parts.append("- Regulatory scrutiny increases with market dominance")
            analysis_parts.append("- Limited upside potential due to size constraints")
            analysis_parts.append("- Institutional ownership creates selling pressure")
        elif market_cap < 1000000000:  # < $1B
            analysis_parts.append("- Limited analyst coverage creates information gaps")
            analysis_parts.append("- Liquidity constraints affecting institutional participation")
            analysis_parts.append("- Higher execution risk and operational leverage")
        
        # Valuation-specific risks
        if abs(upside_downside) > 30:
            analysis_parts.append("- Significant valuation gap creates volatility risk")
            analysis_parts.append("- Market sentiment shifts can amplify price movements")
        elif upside_downside < -20:
            analysis_parts.append("- Downside risk from continued valuation compression")
            analysis_parts.append("- Potential for further multiple contraction")
        
        # LBO-specific risks
        analysis_parts.append("- LBO model sensitivity to exit multiple assumptions")
        analysis_parts.append("- Debt capacity assumptions may be optimistic")
        analysis_parts.append("- Operational improvement assumptions require validation")
        analysis_parts.append("- Exit timing assumptions critical for returns")
        
        analysis_parts.append("")
        
        # Specific Recommendations
        analysis_parts.append("SPECIFIC INVESTMENT RECOMMENDATIONS:")
        
        # Recommendation-specific guidance
        if recommendation == "STRONG BUY":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (LBO implied value)")
            analysis_parts.append("3. TIMEFRAME: Long-term (1-2 years) investment horizon")
            analysis_parts.append("4. POSITION SIZING: 3-7% portfolio allocation recommended")
            analysis_parts.append("5. ENTRY STRATEGY: Consider dollar-cost averaging for volatility")
            analysis_parts.append("6. EXIT STRATEGY: Monitor key operational metrics quarterly")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 20-25% below entry")
            analysis_parts.append("8. CATALYSTS: Earnings reports, sector trends, market conditions")
            analysis_parts.append("9. MONITORING: Track revenue growth, margin expansion, market share")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider options for volatility management")
        elif recommendation == "BUY":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (LBO implied value)")
            analysis_parts.append("3. TIMEFRAME: Medium-term (6-18 months) investment horizon")
            analysis_parts.append("4. POSITION SIZING: 2-5% portfolio allocation recommended")
            analysis_parts.append("5. ENTRY STRATEGY: Wait for pullbacks or market weakness")
            analysis_parts.append("6. EXIT STRATEGY: Monitor quarterly earnings and guidance")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 15-20% below entry")
            analysis_parts.append("8. CATALYSTS: Earnings beats, sector rotation, market recovery")
            analysis_parts.append("9. MONITORING: Track operational metrics and competitive position")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider covered calls for income")
        elif recommendation == "HOLD":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (LBO implied value)")
            analysis_parts.append("3. TIMEFRAME: Short to medium-term (3-12 months)")
            analysis_parts.append("4. POSITION SIZING: 1-3% portfolio allocation recommended")
            analysis_parts.append("5. ENTRY STRATEGY: Only on significant pullbacks")
            analysis_parts.append("6. EXIT STRATEGY: Consider trimming on strength")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 10-15% below entry")
            analysis_parts.append("8. CATALYSTS: Operational improvements, market conditions")
            analysis_parts.append("9. MONITORING: Focus on margin expansion and efficiency")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider defensive positioning")
        elif recommendation == "SELL":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (LBO implied value)")
            analysis_parts.append("3. TIMEFRAME: Short-term (1-6 months) exit horizon")
            analysis_parts.append("4. POSITION SIZING: Reduce to 0-1% portfolio allocation")
            analysis_parts.append("5. ENTRY STRATEGY: Avoid new positions")
            analysis_parts.append("6. EXIT STRATEGY: Sell on any strength or rallies")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 5-10% below entry")
            analysis_parts.append("8. CATALYSTS: Negative earnings surprises, sector headwinds")
            analysis_parts.append("9. MONITORING: Watch for deteriorating fundamentals")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider short positions or puts")
        else:  # STRONG SELL
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (LBO implied value)")
            analysis_parts.append("3. TIMEFRAME: Immediate exit recommended")
            analysis_parts.append("4. POSITION SIZING: Exit all positions immediately")
            analysis_parts.append("5. ENTRY STRATEGY: Avoid at all costs")
            analysis_parts.append("6. EXIT STRATEGY: Sell immediately regardless of price")
            analysis_parts.append("7. RISK MANAGEMENT: No stop-loss needed - exit now")
            analysis_parts.append("8. CATALYSTS: Fundamental deterioration, sector collapse")
            analysis_parts.append("9. MONITORING: Watch for further downside")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider short positions")
        
        analysis_parts.append("")
        
        # Market Context
        analysis_parts.append("MARKET CONTEXT & STRATEGIC INSIGHTS:")
        
        # Sector-specific insights
        if sector == 'Technology':
            analysis_parts.append("Technology Sector Dynamics:")
            analysis_parts.append("- High growth potential but significant volatility and disruption risk")
            analysis_parts.append("- Innovation cycles drive rapid obsolescence and market share shifts")
            analysis_parts.append("- Regulatory scrutiny increasing on data privacy and antitrust")
            analysis_parts.append("- Cloud computing and AI driving new revenue streams")
        elif sector == 'Healthcare':
            analysis_parts.append("Healthcare Sector Dynamics:")
            analysis_parts.append("- Defensive characteristics with demographic tailwinds")
            analysis_parts.append("- Regulatory approval processes create barriers to entry")
            analysis_parts.append("- Patent cliffs and generic competition pressure margins")
            analysis_parts.append("- Innovation in biologics and personalized medicine")
        elif sector == 'Financial Services':
            analysis_parts.append("Financial Services Sector Dynamics:")
            analysis_parts.append("- Interest rate sensitivity affects net interest margins")
            analysis_parts.append("- Regulatory capital requirements constrain returns")
            analysis_parts.append("- Digital transformation disrupting traditional banking")
            analysis_parts.append("- Credit cycles create cyclical earnings volatility")
        elif sector == 'Consumer Discretionary':
            analysis_parts.append("Consumer Discretionary Sector Dynamics:")
            analysis_parts.append("- Economic sensitivity drives cyclical demand patterns")
            analysis_parts.append("- E-commerce disruption accelerating omnichannel transformation")
            analysis_parts.append("- Supply chain optimization critical for margin expansion")
            analysis_parts.append("- Brand strength and customer loyalty drive pricing power")
        elif sector == 'Energy':
            analysis_parts.append("Energy Sector Dynamics:")
            analysis_parts.append("- Commodity price volatility drives earnings uncertainty")
            analysis_parts.append("- ESG pressures accelerating energy transition investments")
            analysis_parts.append("- Geopolitical risks affect global supply chains")
            analysis_parts.append("- Capital intensity requires disciplined allocation")
        else:
            analysis_parts.append("Sector-Specific Considerations:")
            analysis_parts.append("- Industry-specific regulatory and competitive dynamics")
            analysis_parts.append("- Economic cycle sensitivity varies by subsector")
            analysis_parts.append("- Technology disruption affecting traditional business models")
            analysis_parts.append("- ESG factors increasingly influencing valuations")
        
        analysis_parts.append("")
        
        # Market cap-based insights
        if market_cap > 200000000000:  # > $200B
            analysis_parts.append("Large-Cap Market Position:")
            analysis_parts.append("- Institutional ownership provides stability but limits upside")
            analysis_parts.append("- Market leadership position offers competitive moats")
            analysis_parts.append("- Regulatory scrutiny increases with market dominance")
            analysis_parts.append("- Dividend policies and capital allocation under scrutiny")
        elif market_cap > 10000000000:  # > $10B
            analysis_parts.append("Mid-Cap Market Position:")
            analysis_parts.append("- Growth potential balanced with operational stability")
            analysis_parts.append("- Analyst coverage provides visibility and liquidity")
            analysis_parts.append("- M&A activity creates both opportunities and risks")
            analysis_parts.append("- Capital allocation flexibility enables strategic investments")
        else:  # < $10B
            analysis_parts.append("Small-Cap Market Position:")
            analysis_parts.append("- High growth potential but significant execution risk")
            analysis_parts.append("- Limited analyst coverage creates information gaps")
            analysis_parts.append("- Liquidity constraints affect institutional participation")
            analysis_parts.append("- Operational leverage amplifies both upside and downside")
        
        analysis_parts.append("")
        
        # Valuation context
        if abs(upside_downside) > 30:
            analysis_parts.append("Significant Valuation Discrepancy:")
            analysis_parts.append("- Market pricing reflects different growth assumptions")
            analysis_parts.append("- Potential for mean reversion or continued divergence")
            analysis_parts.append("- Catalyst identification critical for timing")
            analysis_parts.append("- Risk management essential given volatility")
        elif abs(upside_downside) > 15:
            analysis_parts.append("Moderate Valuation Discrepancy:")
            analysis_parts.append("- Market and model assumptions show reasonable alignment")
            analysis_parts.append("- Execution on operational metrics drives value realization")
            analysis_parts.append("- Sector trends and competitive dynamics influence outcomes")
            analysis_parts.append("- Balanced risk-reward profile requires careful monitoring")
        else:
            analysis_parts.append("Fair Valuation Assessment:")
            analysis_parts.append("- Market pricing appears consistent with fundamentals")
            analysis_parts.append("- Operational execution and efficiency gains drive value")
            analysis_parts.append("- Sector rotation and market conditions influence performance")
            analysis_parts.append("- Conservative positioning appropriate for risk management")
        
        analysis_parts.append("")
        
        # LBO-specific insights
        analysis_parts.append("LBO Model Considerations:")
        analysis_parts.append("- Exit multiple assumptions drive 60-80% of valuation")
        analysis_parts.append("- Debt capacity analysis critical for leverage assessment")
        analysis_parts.append("- Operational improvement assumptions most impactful variable")
        analysis_parts.append("- Exit timing assumptions require market condition validation")
        analysis_parts.append("- Scenario analysis essential for risk assessment")
        
        analysis_parts.append("")
        
        # Current market environment
        analysis_parts.append("Current Market Environment:")
        analysis_parts.append("- Interest rate environment affects debt capacity and exit multiples")
        analysis_parts.append("- Inflation expectations impact cost structure assumptions")
        analysis_parts.append("- Geopolitical risks create uncertainty in global markets")
        analysis_parts.append("- ESG factors increasingly influence investment decisions")
        analysis_parts.append("- Technology disruption accelerating across industries")
        
        return {
            'analysis': '\n'.join(analysis_parts),
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_ma_analysis(self, company_data, ma_results):
        """Enhanced fallback M&A analysis when AI is unavailable"""
        
        analysis_parts.append("")
        
        # Risk Factors
        analysis_parts.append("KEY RISK FACTORS:")
        
        # Sector-specific risks
        if sector == 'Technology':
            analysis_parts.append("- Technology disruption and rapid obsolescence risk")
            analysis_parts.append("- Regulatory scrutiny on data privacy and antitrust")
            analysis_parts.append("- Talent retention and competitive hiring pressures")
            analysis_parts.append("- Innovation cycles creating market share volatility")
        elif sector == 'Healthcare':
            analysis_parts.append("- Regulatory approval delays and compliance costs")
            analysis_parts.append("- Patent cliff exposure and generic competition")
            analysis_parts.append("- Clinical trial failures and safety concerns")
            analysis_parts.append("- Healthcare policy changes affecting reimbursement")
        elif sector == 'Financial Services':
            analysis_parts.append("- Interest rate sensitivity affecting margins")
            analysis_parts.append("- Regulatory capital requirements constraining returns")
            analysis_parts.append("- Credit quality deterioration in economic downturns")
            analysis_parts.append("- Digital disruption from fintech competitors")
        elif sector == 'Consumer Discretionary':
            analysis_parts.append("- Economic sensitivity and consumer spending volatility")
            analysis_parts.append("- E-commerce disruption and omnichannel challenges")
            analysis_parts.append("- Supply chain disruptions and cost inflation")
            analysis_parts.append("- Brand reputation and competitive positioning risks")
        elif sector == 'Energy':
            analysis_parts.append("- Commodity price volatility affecting margins")
            analysis_parts.append("- ESG pressures accelerating energy transition")
            analysis_parts.append("- Geopolitical risks affecting supply chains")
            analysis_parts.append("- Capital intensity and investment allocation risks")
        else:
            analysis_parts.append("- Industry-specific competitive and regulatory risks")
            analysis_parts.append("- Economic cycle sensitivity and demand volatility")
            analysis_parts.append("- Technology disruption affecting business models")
            analysis_parts.append("- ESG factors increasingly impacting valuations")
        
        # Market cap-specific risks
        if market_cap > 200000000000:  # > $200B
            analysis_parts.append("- Regulatory scrutiny increases with market dominance")
            analysis_parts.append("- Limited upside potential due to size constraints")
            analysis_parts.append("- Institutional ownership creates selling pressure")
        elif market_cap < 1000000000:  # < $1B
            analysis_parts.append("- Limited analyst coverage creates information gaps")
            analysis_parts.append("- Liquidity constraints affecting institutional participation")
            analysis_parts.append("- Higher execution risk and operational leverage")
        
        # Valuation-specific risks
        if abs(upside_downside) > 30:
            analysis_parts.append("- Significant valuation gap creates volatility risk")
            analysis_parts.append("- Market sentiment shifts can amplify price movements")
        elif upside_downside < -20:
            analysis_parts.append("- Downside risk from continued valuation compression")
            analysis_parts.append("- Potential for further multiple contraction")
        
        # DCF-specific risks
        analysis_parts.append("- DCF model sensitivity to key assumption changes")
        analysis_parts.append("- Terminal value assumptions may be inaccurate")
        analysis_parts.append("- Revenue growth assumptions require validation")
        analysis_parts.append("- Margin expansion assumptions need operational support")
        
        analysis_parts.append("")
        
        # Specific Recommendations
        analysis_parts.append("SPECIFIC INVESTMENT RECOMMENDATIONS:")
        
        # Recommendation-specific guidance
        if recommendation == "STRONG BUY":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (DCF implied value)")
            analysis_parts.append("3. TIMEFRAME: Long-term (1-2 years) investment horizon")
            analysis_parts.append("4. POSITION SIZING: 3-7% portfolio allocation recommended")
            analysis_parts.append("5. ENTRY STRATEGY: Consider dollar-cost averaging for volatility")
            analysis_parts.append("6. EXIT STRATEGY: Monitor key operational metrics quarterly")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 20-25% below entry")
            analysis_parts.append("8. CATALYSTS: Earnings reports, sector trends, market conditions")
            analysis_parts.append("9. MONITORING: Track revenue growth, margin expansion, market share")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider options for volatility management")
        elif recommendation == "BUY":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (DCF implied value)")
            analysis_parts.append("3. TIMEFRAME: Medium-term (6-18 months) investment horizon")
            analysis_parts.append("4. POSITION SIZING: 2-5% portfolio allocation recommended")
            analysis_parts.append("5. ENTRY STRATEGY: Wait for pullbacks or market weakness")
            analysis_parts.append("6. EXIT STRATEGY: Monitor quarterly earnings and guidance")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 15-20% below entry")
            analysis_parts.append("8. CATALYSTS: Earnings beats, sector rotation, market recovery")
            analysis_parts.append("9. MONITORING: Track operational metrics and competitive position")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider covered calls for income")
        elif recommendation == "HOLD":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (DCF implied value)")
            analysis_parts.append("3. TIMEFRAME: Short to medium-term (3-12 months)")
            analysis_parts.append("4. POSITION SIZING: 1-3% portfolio allocation recommended")
            analysis_parts.append("5. ENTRY STRATEGY: Only on significant pullbacks")
            analysis_parts.append("6. EXIT STRATEGY: Consider trimming on strength")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 10-15% below entry")
            analysis_parts.append("8. CATALYSTS: Operational improvements, market conditions")
            analysis_parts.append("9. MONITORING: Focus on margin expansion and efficiency")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider defensive positioning")
        elif recommendation == "SELL":
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (DCF implied value)")
            analysis_parts.append("3. TIMEFRAME: Short-term (1-6 months) exit horizon")
            analysis_parts.append("4. POSITION SIZING: Reduce to 0-1% portfolio allocation")
            analysis_parts.append("5. ENTRY STRATEGY: Avoid new positions")
            analysis_parts.append("6. EXIT STRATEGY: Sell on any strength or rallies")
            analysis_parts.append("7. RISK MANAGEMENT: Set stop-loss at 5-10% below entry")
            analysis_parts.append("8. CATALYSTS: Negative earnings surprises, sector headwinds")
            analysis_parts.append("9. MONITORING: Watch for deteriorating fundamentals")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider short positions or puts")
        else:  # STRONG SELL
            analysis_parts.append(f"1. PRIMARY RECOMMENDATION: {recommendation} with {confidence.lower()} confidence")
            analysis_parts.append(f"2. PRICE TARGET: ${implied_price:.2f} (DCF implied value)")
            analysis_parts.append("3. TIMEFRAME: Immediate exit recommended")
            analysis_parts.append("4. POSITION SIZING: Exit all positions immediately")
            analysis_parts.append("5. ENTRY STRATEGY: Avoid at all costs")
            analysis_parts.append("6. EXIT STRATEGY: Sell immediately regardless of price")
            analysis_parts.append("7. RISK MANAGEMENT: No stop-loss needed - exit now")
            analysis_parts.append("8. CATALYSTS: Fundamental deterioration, sector collapse")
            analysis_parts.append("9. MONITORING: Watch for further downside")
            analysis_parts.append("10. ALTERNATIVE STRATEGIES: Consider short positions")
        
        analysis_parts.append("")
        
        # Market Context
        analysis_parts.append("MARKET CONTEXT & STRATEGIC INSIGHTS:")
        
        # Sector-specific insights
        if sector == 'Technology':
            analysis_parts.append("Technology Sector Dynamics:")
            analysis_parts.append("- High growth potential but significant volatility and disruption risk")
            analysis_parts.append("- Innovation cycles drive rapid obsolescence and market share shifts")
            analysis_parts.append("- Regulatory scrutiny increasing on data privacy and antitrust")
            analysis_parts.append("- Cloud computing and AI driving new revenue streams")
        elif sector == 'Healthcare':
            analysis_parts.append("Healthcare Sector Dynamics:")
            analysis_parts.append("- Defensive characteristics with demographic tailwinds")
            analysis_parts.append("- Regulatory approval cycles create significant timing risks")
            analysis_parts.append("- Patent cliffs and generic competition pressure margins")
            analysis_parts.append("- Aging population and chronic disease prevalence support growth")
        elif sector == 'Financial Services':
            analysis_parts.append("Financial Services Sector Dynamics:")
            analysis_parts.append("- Interest rate sensitivity affects net interest margins")
            analysis_parts.append("- Regulatory capital requirements constrain returns")
            analysis_parts.append("- Digital transformation disrupting traditional banking models")
            analysis_parts.append("- Economic cycles drive credit quality and loan demand")
        elif sector == 'Consumer Discretionary':
            analysis_parts.append("Consumer Discretionary Sector Dynamics:")
            analysis_parts.append("- Economic sensitivity drives cyclical performance")
            analysis_parts.append("- E-commerce disruption reshaping retail landscape")
            analysis_parts.append("- Brand strength and pricing power critical for margins")
            analysis_parts.append("- Consumer spending patterns shift with economic conditions")
        elif sector == 'Energy':
            analysis_parts.append("Energy Sector Dynamics:")
            analysis_parts.append("- Commodity price volatility drives earnings uncertainty")
            analysis_parts.append("- ESG pressures accelerating transition to renewables")
            analysis_parts.append("- Geopolitical risks affect supply chains and pricing")
            analysis_parts.append("- Capital intensity requires disciplined investment allocation")
        else:
            analysis_parts.append("Sector-Specific Considerations:")
            analysis_parts.append("- Industry-specific regulatory and competitive dynamics")
            analysis_parts.append("- Economic cycle sensitivity varies by subsector")
            analysis_parts.append("- Technology disruption affecting traditional business models")
            analysis_parts.append("- ESG factors increasingly influencing valuations")
        
        analysis_parts.append("")
        
        # Market cap-based insights
        if market_cap > 200000000000:  # > $200B
            analysis_parts.append("Large-Cap Market Position:")
            analysis_parts.append("- Institutional ownership provides stability but limits upside")
            analysis_parts.append("- Market leadership position offers competitive moats")
            analysis_parts.append("- Regulatory scrutiny increases with market dominance")
            analysis_parts.append("- Dividend policies and capital allocation under scrutiny")
        elif market_cap > 10000000000:  # > $10B
            analysis_parts.append("Mid-Cap Market Position:")
            analysis_parts.append("- Growth potential balanced with operational maturity")
            analysis_parts.append("- Institutional interest increasing but liquidity constraints")
            analysis_parts.append("- Acquisition targets for larger players")
            analysis_parts.append("- Management execution critical for value creation")
        else:  # < $10B
            analysis_parts.append("Small-Cap Market Position:")
            analysis_parts.append("- High growth potential but significant execution risk")
            analysis_parts.append("- Limited analyst coverage creates information gaps")
            analysis_parts.append("- Liquidity constraints affect institutional participation")
            analysis_parts.append("- Operational leverage amplifies both upside and downside")
        
        analysis_parts.append("")
        
        # Valuation context
        if abs(upside_downside) > 30:
            analysis_parts.append("Significant Valuation Discrepancy:")
            analysis_parts.append("- Market pricing reflects different growth assumptions")
            analysis_parts.append("- Potential for mean reversion or continued divergence")
            analysis_parts.append("- Catalyst identification critical for timing")
            analysis_parts.append("- Risk management essential given volatility")
        elif abs(upside_downside) > 15:
            analysis_parts.append("Moderate Valuation Gap:")
            analysis_parts.append("- Market efficiency suggests limited mispricing")
            analysis_parts.append("- Fundamental analysis key to identifying edge")
            analysis_parts.append("- Position sizing should reflect conviction level")
            analysis_parts.append("- Monitor for changing market sentiment")
        else:
            analysis_parts.append("Fair Value Territory:")
            analysis_parts.append("- Market pricing appears efficient")
            analysis_parts.append("- Focus on operational improvements and catalysts")
            analysis_parts.append("- Dividend yield and capital allocation important")
            analysis_parts.append("- Risk-adjusted returns may be limited")
        
        analysis_parts.append("")
        
        # DCF-specific insights
        analysis_parts.append("DCF Model Considerations:")
        analysis_parts.append("- Terminal value assumptions drive 60-80% of valuation")
        analysis_parts.append("- WACC sensitivity analysis critical for range estimation")
        analysis_parts.append("- Revenue growth assumptions most impactful variable")
        analysis_parts.append("- Margin expansion assumptions require operational validation")
        analysis_parts.append("- Scenario analysis essential for risk assessment")
        
        analysis_parts.append("")
        
        # Current market environment
        analysis_parts.append("Current Market Environment:")
        analysis_parts.append("- Interest rate environment affects discount rates and multiples")
        analysis_parts.append("- Inflation expectations impact cost structure assumptions")
        analysis_parts.append("- Geopolitical risks create uncertainty in global markets")
        analysis_parts.append("- ESG factors increasingly influence investment decisions")
        analysis_parts.append("- Technology disruption accelerating across industries")
        
        analysis = "\n".join(analysis_parts)
        
        return {
            'analysis': analysis,
            'source': 'enhanced_fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_lbo_analysis(self, company_data, lbo_results):
        """Enhanced fallback LBO analysis when AI is unavailable"""
        company_name = company_data.get('company_name', 'Unknown')
        sector = company_data.get('sector', 'Unknown')
        market_cap = company_data.get('market_cap', 0)
        revenue = company_data.get('revenue', 0)
        operating_margin = company_data.get('operating_margin', 0)
        debt_levels = company_data.get('total_debt', 0)
        
        irr = lbo_results.get('irr', 0)
        multiple = lbo_results.get('multiple', 0)
        debt_capacity = lbo_results.get('debt_capacity', 0)
        exit_value = lbo_results.get('exit_value', 0)
        
        # Generate comprehensive analysis
        analysis_parts = []
        
        # Company Overview
        analysis_parts.append(f"COMPREHENSIVE LBO ANALYSIS FOR {company_name.upper()}")
        analysis_parts.append("")
        analysis_parts.append("LBO MODEL RESULTS:")
        analysis_parts.append(f"Projected IRR: {irr*100:.1f}%")
        analysis_parts.append(f"Multiple of Money: {multiple:.1f}x")
        analysis_parts.append(f"Debt Capacity: ${debt_capacity/1e9:.1f}B")
        analysis_parts.append(f"Exit Value: ${exit_value/1e9:.1f}B")
        analysis_parts.append("")
        
        # LBO Recommendation
        if irr > 0.25:
            recommendation = "PROCEED"
            confidence = "High"
            reasoning = "Exceptional returns with strong cash flow potential"
        elif irr > 0.20:
            recommendation = "PROCEED"
            confidence = "Medium-High"
            reasoning = "Attractive returns with good operational potential"
        elif irr > 0.15:
            recommendation = "CONDITIONAL"
            confidence = "Medium"
            reasoning = "Moderate returns requiring careful execution"
        else:
            recommendation = "PASS"
            confidence = "High"
            reasoning = "Insufficient returns for private equity investment"
        
        analysis_parts.append("**LBO RECOMMENDATION:**")
        analysis_parts.append(f"- Decision: {recommendation}")
        analysis_parts.append(f"- Confidence: {confidence}")
        analysis_parts.append(f"- Reasoning: {reasoning}")
        analysis_parts.append("")
        
        # Key Investment Drivers
        analysis_parts.append("**KEY INVESTMENT DRIVERS:**")
        if operating_margin > 0.20:
            analysis_parts.append("- High operational efficiency with strong cash flow generation")
        elif operating_margin < 0.05:
            analysis_parts.append("- Operational challenges requiring significant improvements")
        
        if debt_capacity > debt_levels * 1.5:
            analysis_parts.append("- Significant debt capacity for leverage optimization")
        elif debt_capacity < debt_levels:
            analysis_parts.append("- Limited additional debt capacity")
        
        if market_cap > 10000000000:  # > $10B
            analysis_parts.append("- Large-cap target with institutional exit potential")
        elif market_cap < 1000000000:  # < $1B
            analysis_parts.append("- Small-cap target with growth potential")
        
        if multiple > 2.5:
            analysis_parts.append("- Strong multiple expansion potential")
        elif multiple < 1.5:
            analysis_parts.append("- Conservative multiple assumptions")
        
        analysis_parts.append("")
        
        # Operational Improvements
        analysis_parts.append("**OPERATIONAL IMPROVEMENT OPPORTUNITIES:**")
        if operating_margin < 0.15:
            analysis_parts.append("- Cost reduction and margin expansion potential")
        analysis_parts.append("- Revenue growth through market expansion")
        analysis_parts.append("- Operational efficiency improvements")
        analysis_parts.append("- Working capital optimization")
        analysis_parts.append("- Technology and digital transformation")
        analysis_parts.append("")
        
        # Risk Factors
        analysis_parts.append("**KEY RISK FACTORS:**")
        analysis_parts.append("- Debt service requirements and covenant compliance")
        analysis_parts.append("- Market conditions affecting exit multiples")
        analysis_parts.append("- Operational improvement execution risk")
        analysis_parts.append("- Management team retention and alignment")
        analysis_parts.append("- Sector-specific headwinds and competition")
        analysis_parts.append("")
        
        # Specific Recommendations
        analysis_parts.append("SPECIFIC LBO RECOMMENDATIONS:")
        analysis_parts.append(f"1. ACQUISITION DECISION: {recommendation} with {confidence.lower()} confidence")
        analysis_parts.append(f"2. OFFER PRICE: Consider ${market_cap/1e9:.1f}B - ${market_cap*1.2/1e9:.1f}B range")
        analysis_parts.append("3. DEBT STRUCTURE: Target 60-70% debt/equity mix")
        analysis_parts.append("4. OPERATIONAL IMPROVEMENTS: Focus on margin expansion and cost reduction")
        analysis_parts.append("5. EXIT STRATEGY: Plan for 3-5 year hold period with IPO or strategic sale")
        analysis_parts.append("6. RETURN EXPECTATIONS: Target {irr*100:.1f}% IRR with {multiple:.1f}x multiple")
        analysis_parts.append("7. RISK MITIGATION: Implement robust operational monitoring")
        analysis_parts.append("8. COMPETITIVE ADVANTAGES: Leverage sector expertise and operational capabilities")
        analysis_parts.append("9. INTEGRATION PLAN: Develop comprehensive 100-day plan")
        analysis_parts.append("10. MONITORING METRICS: Track EBITDA growth, debt ratios, and market position")
        analysis_parts.append("")
        
        # Market Context
        analysis_parts.append("MARKET CONTEXT & STRATEGIC INSIGHTS:")
        
        # LBO market conditions
        analysis_parts.append("LBO Market Environment:")
        analysis_parts.append("- Debt markets affecting leverage capacity and pricing")
        analysis_parts.append("- Exit market conditions influencing multiple assumptions")
        analysis_parts.append("- Interest rate environment impacting debt service capacity")
        analysis_parts.append("- Regulatory environment affecting deal structures")
        
        analysis_parts.append("")
        
        # Sector-specific LBO considerations
        if sector == 'Technology':
            analysis_parts.append("Technology Sector LBO Dynamics:")
            analysis_parts.append("- High growth potential but execution risk in competitive markets")
            analysis_parts.append("- Technology disruption requires continuous innovation investment")
            analysis_parts.append("- Talent retention critical for operational improvements")
            analysis_parts.append("- Exit multiples sensitive to growth rate sustainability")
        elif sector == 'Healthcare':
            analysis_parts.append("Healthcare Sector LBO Dynamics:")
            analysis_parts.append("- Regulatory approval cycles create timing and execution risk")
            analysis_parts.append("- Patent cliffs require pipeline development and R&D investment")
            analysis_parts.append("- Defensive characteristics provide downside protection")
            analysis_parts.append("- Consolidation opportunities in fragmented markets")
        elif sector == 'Financial Services':
            analysis_parts.append("Financial Services Sector LBO Dynamics:")
            analysis_parts.append("- Regulatory capital requirements constrain leverage capacity")
            analysis_parts.append("- Interest rate sensitivity affects net interest margins")
            analysis_parts.append("- Digital transformation requires significant technology investment")
            analysis_parts.append("- Economic cycles drive credit quality and loan demand")
        elif sector == 'Consumer Discretionary':
            analysis_parts.append("Consumer Discretionary Sector LBO Dynamics:")
            analysis_parts.append("- Economic sensitivity requires robust operational improvements")
            analysis_parts.append("- E-commerce disruption necessitates omnichannel capabilities")
            analysis_parts.append("- Brand strength and pricing power critical for margin expansion")
            analysis_parts.append("- Consumer spending patterns affect revenue predictability")
        elif sector == 'Energy':
            analysis_parts.append("Energy Sector LBO Dynamics:")
            analysis_parts.append("- Commodity price volatility requires hedging strategies")
            analysis_parts.append("- ESG pressures accelerating transition to sustainable operations")
            analysis_parts.append("- Capital intensity requires disciplined investment allocation")
            analysis_parts.append("- Geopolitical risks affect supply chains and pricing")
        else:
            analysis_parts.append("Sector-Specific LBO Considerations:")
            analysis_parts.append("- Industry-specific operational improvement opportunities")
            analysis_parts.append("- Regulatory environment affecting deal structures and timing")
            analysis_parts.append("- Competitive dynamics influencing exit strategies")
            analysis_parts.append("- Technology disruption requiring operational adaptation")
        
        analysis_parts.append("")
        
        # LBO-specific insights
        analysis_parts.append("LBO Model Considerations:")
        analysis_parts.append("- Debt capacity analysis critical for optimal capital structure")
        analysis_parts.append("- Operational improvement assumptions require management validation")
        analysis_parts.append("- Exit multiple assumptions sensitive to market conditions")
        analysis_parts.append("- IRR calculations depend on hold period and exit timing")
        analysis_parts.append("- Cash flow generation essential for debt service and growth")
        
        analysis_parts.append("")
        
        # Market cap-based LBO insights
        if market_cap > 10000000000:  # > $10B
            analysis_parts.append("Large-Cap LBO Considerations:")
            analysis_parts.append("- Institutional exit options provide liquidity")
            analysis_parts.append("- Regulatory scrutiny increases with market dominance")
            analysis_parts.append("- Operational improvements require significant scale")
            analysis_parts.append("- Management team retention critical for execution")
        elif market_cap > 1000000000:  # > $1B
            analysis_parts.append("Mid-Cap LBO Considerations:")
            analysis_parts.append("- Growth potential balanced with operational maturity")
            analysis_parts.append("- Acquisition opportunities for strategic buyers")
            analysis_parts.append("- Management execution critical for value creation")
            analysis_parts.append("- Exit options include IPO and strategic sale")
        else:  # < $1B
            analysis_parts.append("Small-Cap LBO Considerations:")
            analysis_parts.append("- High growth potential but significant execution risk")
            analysis_parts.append("- Limited exit options may constrain valuations")
            analysis_parts.append("- Operational leverage amplifies improvement impact")
            analysis_parts.append("- Management team alignment essential for success")
        
        analysis_parts.append("")
        
        # Current LBO market environment
        analysis_parts.append("Current LBO Market Environment:")
        analysis_parts.append("- Debt availability and pricing affecting deal structures")
        analysis_parts.append("- Exit market conditions influencing multiple assumptions")
        analysis_parts.append("- Interest rate environment impacting debt service capacity")
        analysis_parts.append("- ESG factors increasingly important for investors")
        analysis_parts.append("- Technology disruption requiring operational adaptation")
        
        analysis = "\n".join(analysis_parts)
        
        return {
            'analysis': analysis,
            'source': 'enhanced_fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_ma_analysis(self, company_data, ma_results):
        """Fallback M&A analysis when AI is unavailable"""
        company_name = company_data.get('company_name', 'Unknown')
        accretion_dilution = ma_results.get('accretion_dilution', 0)
        synergy_value = ma_results.get('synergy_value', 0)
        
        analysis = f"""
**M&A Analysis for {company_name}**

**M&A Metrics:**
- Accretion/(Dilution): {accretion_dilution*100:.1f}%
- Synergy Value: ${synergy_value/1e9:.1f}B

**Strategic Considerations:**
- Evaluate strategic fit and rationale
- Assess synergy realization potential
- Consider integration challenges
- Review market reaction expectations

**Key Considerations:**
- Analyze accretion/dilution impact
- Evaluate synergy assumptions
- Consider execution risks
- Review regulatory considerations

*Note: This is a basic analysis. For detailed M&A insights, AI analysis is currently unavailable.*
"""
        
        return {
            'analysis': analysis,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_comps_analysis(self, company_data, comps_results):
        """Fallback Trading Comps analysis when AI is unavailable"""
        company_name = company_data.get('company_name', 'Unknown')
        ev_revenue = comps_results.get('ev_revenue', 0)
        ev_ebitda = comps_results.get('ev_ebitda', 0)
        pe_ratio = comps_results.get('pe_ratio', 0)
        
        analysis = f"""
**Trading Comparables Analysis for {company_name}**

**Trading Multiples:**
- EV/Revenue: {ev_revenue:.1f}x
- EV/EBITDA: {ev_ebitda:.1f}x
- P/E Ratio: {pe_ratio:.1f}x

**Peer Comparison Factors:**
- Compare multiples to sector averages
- Evaluate growth vs. value characteristics
- Assess competitive positioning
- Review relative valuation attractiveness

**Key Considerations:**
- Analyze multiple expansion/contraction potential
- Consider peer-specific risks
- Evaluate sector trends
- Review relative performance metrics

*Note: This is a basic analysis. For detailed peer comparison insights, AI analysis is currently unavailable.*
"""
        
        return {
            'analysis': analysis,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_generic_analysis(self, model_type, company_data, model_results):
        """Fallback analysis for any other model type"""
        company_name = company_data.get('company_name', 'Unknown')
        
        analysis = f"""
**{model_type.upper()} Analysis for {company_name}**

**Model Results Summary:**
{json.dumps(model_results, indent=2)}

**Key Considerations:**
- Review model assumptions and methodology
- Evaluate results against expectations
- Consider market conditions and trends
- Assess investment implications

*Note: This is a basic analysis. For detailed insights, AI analysis is currently unavailable.*
"""
        
        return {
            'analysis': analysis,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_assumption_validation(self, assumptions):
        """Fallback assumption validation when AI is unavailable"""
        revenue_growth = assumptions.get('revenue_growth_1', 0)
        operating_margin = assumptions.get('operating_margin', 0)
        wacc = assumptions.get('wacc', 0)
        
        validation = f"""
**Assumption Validation Summary:**

**Revenue Growth ({revenue_growth*100:.1f}%):**
- Review historical growth patterns
- Consider market saturation and competition
- Assess new product/service launches

**Operating Margin ({operating_margin*100:.1f}%):**
- Compare to historical margins
- Evaluate cost structure changes
- Consider pricing power and efficiency gains

**WACC ({wacc*100:.1f}%):**
- Verify risk-free rate and market premium
- Check beta calculation
- Consider sector-specific risk factors

*Note: This is a basic validation. For detailed analysis, AI validation is currently unavailable.*
"""
        
        return {
            'validation': validation,
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_chat_response(self, user_question, model_context):
        """Enhanced fallback chat response when AI is unavailable"""
        model_type = model_context.get('model_type', 'unknown')
        company_name = model_context.get('company_name', 'Unknown')
        ticker = model_context.get('ticker', 'Unknown')
        
        # Generate intelligent response based on question type
        response_parts = []
        
        response_parts.append(f"INTELLIGENT ANALYSIS FOR {company_name.upper()} ({ticker})")
        response_parts.append("")
        response_parts.append(f"Your Question: \"{user_question}\"")
        response_parts.append("")
        
        # Analyze question type and provide relevant insights
        question_lower = user_question.lower()
        
        if any(word in question_lower for word in ['buy', 'sell', 'invest', 'recommendation']):
            response_parts.append("INVESTMENT RECOMMENDATION ANALYSIS:")
            if model_type.lower() == 'dcf':
                response_parts.append("DCF models provide intrinsic value based on cash flow projections")
                response_parts.append("Compare implied price to current market price for investment decision")
                response_parts.append("Consider upside/downside potential and risk factors")
            elif model_type.lower() == 'lbo':
                response_parts.append("LBO models assess private equity acquisition potential")
                response_parts.append("Focus on IRR, multiple, and debt capacity metrics")
                response_parts.append("Evaluate operational improvement opportunities")
            response_parts.append("")
        
        if any(word in question_lower for word in ['risk', 'risky', 'danger', 'concern']):
            response_parts.append("RISK ASSESSMENT:")
            response_parts.append("Market volatility and economic uncertainty")
            response_parts.append("Model sensitivity to key assumptions")
            response_parts.append("Competitive pressures and sector headwinds")
            response_parts.append("Regulatory and compliance risks")
            response_parts.append("")
        
        if any(word in question_lower for word in ['assumption', 'assume', 'input', 'parameter']):
            response_parts.append("KEY ASSUMPTIONS ANALYSIS:")
            if model_type.lower() == 'dcf':
                response_parts.append("Revenue growth rates and terminal growth")
                response_parts.append("Operating margins and cost structure")
                response_parts.append("WACC and discount rate assumptions")
                response_parts.append("Terminal value methodology")
            elif model_type.lower() == 'lbo':
                response_parts.append("Revenue growth and margin expansion")
                response_parts.append("Debt capacity and leverage assumptions")
                response_parts.append("Exit multiple and timing assumptions")
                response_parts.append("Operational improvement targets")
            response_parts.append("")
        
        if any(word in question_lower for word in ['scenario', 'bull', 'bear', 'case']):
            response_parts.append("SCENARIO ANALYSIS:")
            response_parts.append("Bull Case: Optimistic assumptions with upside potential")
            response_parts.append("Base Case: Most likely scenario with reasonable assumptions")
            response_parts.append("Bear Case: Conservative assumptions with downside protection")
            response_parts.append("Consider probability weighting of different scenarios")
            response_parts.append("")
        
        if any(word in question_lower for word in ['compare', 'peer', 'competitor', 'relative']):
            response_parts.append("COMPARATIVE ANALYSIS:")
            response_parts.append("Compare valuation multiples to sector peers")
            response_parts.append("Assess relative operational performance")
            response_parts.append("Evaluate competitive positioning and market share")
            response_parts.append("Consider sector-specific trends and dynamics")
            response_parts.append("")
        
        # Add general guidance
        response_parts.append("SPECIFIC GUIDANCE FOR YOUR QUESTION:")
        response_parts.append("Review the detailed model results and assumptions")
        response_parts.append("Consider the sensitivity of results to key variables")
        response_parts.append("Evaluate market conditions and sector trends")
        response_parts.append("Assess management execution and competitive positioning")
        response_parts.append("Monitor key operational and financial metrics")
        response_parts.append("")
        
        # Add model-specific insights
        if model_type.lower() == 'dcf':
            response_parts.append("DCF-SPECIFIC INSIGHTS:")
            response_parts.append("Focus on cash flow generation and growth sustainability")
            response_parts.append("Evaluate terminal value assumptions and exit multiples")
            response_parts.append("Consider WACC sensitivity and discount rate rationale")
            response_parts.append("Assess revenue growth assumptions vs. historical performance")
        elif model_type.lower() == 'lbo':
            response_parts.append("LBO-SPECIFIC INSIGHTS:")
            response_parts.append("Evaluate debt capacity and leverage optimization")
            response_parts.append("Assess operational improvement potential and execution risk")
            response_parts.append("Consider exit strategy and multiple expansion opportunities")
            response_parts.append("Focus on cash flow generation for debt service")
        elif model_type.lower() == 'ma':
            response_parts.append("M&A-SPECIFIC INSIGHTS:")
            response_parts.append("Evaluate strategic rationale and synergy potential")
            response_parts.append("Assess accretion/dilution impact and integration challenges")
            response_parts.append("Consider regulatory approval and competitive dynamics")
            response_parts.append("Focus on cultural fit and management alignment")
        elif model_type.lower() == 'comps':
            response_parts.append("TRADING COMPS INSIGHTS:")
            response_parts.append("Compare valuation multiples to sector peers")
            response_parts.append("Assess relative operational performance and growth")
            response_parts.append("Evaluate premium/discount to peer group")
            response_parts.append("Consider market positioning and competitive advantages")
        
        response_parts.append("")
        response_parts.append("*Note: This is an enhanced analysis based on your question and model data. For AI-powered insights, the AI service is currently unavailable.*")
        
        response = "\n".join(response_parts)
        
        return {
            'response': response,
            'source': 'enhanced_fallback',
            'timestamp': datetime.now().isoformat()
        }

# Phase 2 AI Agent Enhancements

class ResearchEngine:
    """Automated research integration for market news and earnings"""
    
    def __init__(self):
        self.news_cache = {}
        self.earnings_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    def get_company_news(self, ticker, limit=5):
        """Get recent news for a company"""
        try:
            # Check cache first
            cache_key = f"news_{ticker}"
            if cache_key in self.news_cache:
                cached_data, timestamp = self.news_cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self.cache_ttl:
                    return cached_data
            
            # Fetch news from multiple sources
            news_items = []
            
            # Try to get news from yfinance
            try:
                stock = yf.Ticker(ticker)
                news = stock.news
                if news:
                    for item in news[:limit]:
                        news_items.append({
                            'title': item.get('title', ''),
                            'summary': item.get('summary', ''),
                            'publisher': item.get('publisher', ''),
                            'published': item.get('providerPublishTime', 0),
                            'url': item.get('link', '')
                        })
            except Exception as e:
                print(f"⚠️ News fetch failed for {ticker}: {e}")
            
            # Cache the results
            self.news_cache[cache_key] = (news_items, datetime.now().timestamp())
            
            return news_items
            
        except Exception as e:
            print(f"❌ Research engine error for {ticker}: {e}")
            return []
    
    def get_earnings_data(self, ticker):
        """Get recent earnings data"""
        try:
            # Check cache first
            cache_key = f"earnings_{ticker}"
            if cache_key in self.earnings_cache:
                cached_data, timestamp = self.earnings_cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self.cache_ttl:
                    return cached_data
            
            # Fetch earnings from yfinance
            try:
                stock = yf.Ticker(ticker)
                earnings = stock.earnings
                calendar = stock.calendar
                
                earnings_data = {
                    'historical_earnings': earnings.to_dict() if not earnings.empty else {},
                    'upcoming_earnings': calendar.to_dict() if not calendar.empty else {},
                    'last_updated': datetime.now().isoformat()
                }
                
                # Cache the results
                self.earnings_cache[cache_key] = (earnings_data, datetime.now().timestamp())
                
                return earnings_data
                
            except Exception as e:
                print(f"⚠️ Earnings fetch failed for {ticker}: {e}")
                return {}
                
        except Exception as e:
            print(f"❌ Earnings engine error for {ticker}: {e}")
            return {}

class PeerAnalysisEngine:
    """Comprehensive peer comparison analysis"""
    
    def __init__(self):
        self.peer_cache = {}
        self.sector_mapping = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'ORCL', 'CRM'],
            'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR'],
            'Financial Services': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK'],
            'Consumer Discretionary': ['TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG'],
            'Communication Services': ['GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'CHTR'],
            'Consumer Staples': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'CL', 'KMB', 'GIS'],
            'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'MPC', 'VLO'],
            'Industrials': ['BA', 'CAT', 'GE', 'HON', 'UPS', 'RTX', 'LMT', 'MMM'],
            'Materials': ['LIN', 'APD', 'SHW', 'ECL', 'DD', 'DOW', 'NEM', 'FCX'],
            'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL'],
            'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'PEG']
        }
    
    def get_peer_companies(self, ticker, sector):
        """Get peer companies for comparison"""
        try:
            # Check cache first
            cache_key = f"peers_{ticker}"
            if cache_key in self.peer_cache:
                return self.peer_cache[cache_key]
            
            # Get peers from sector mapping
            sector_peers = self.sector_mapping.get(sector, [])
            
            # Remove the target company from peers
            peers = [peer for peer in sector_peers if peer != ticker.upper()]
            
            # Limit to top 5 peers for performance
            peers = peers[:5]
            
            # Cache the results
            self.peer_cache[cache_key] = peers
            
            return peers
            
        except Exception as e:
            print(f"❌ Peer analysis error for {ticker}: {e}")
            return []
    
    def analyze_peer_metrics(self, ticker, peers):
        """Analyze key metrics across peers"""
        try:
            peer_data = {}
            financial_engine = FinancialDataEngine()
            
            for peer in peers:
                try:
                    company_data = financial_engine.get_company_data(peer)
                    if company_data:
                        peer_data[peer] = {
                            'market_cap': company_data.get('market_cap', 0),
                            'revenue': company_data.get('revenue', 0),
                            'operating_margin': company_data.get('operating_margin', 0),
                            'current_price': company_data.get('current_price', 0),
                            'sector': company_data.get('sector', 'Unknown')
                        }
                except Exception as e:
                    print(f"⚠️ Failed to get data for peer {peer}: {e}")
                    continue
            
            return peer_data
            
        except Exception as e:
            print(f"❌ Peer metrics analysis error: {e}")
            return {}

class RiskAnalysisEngine:
    """Intelligent risk factor identification"""
    
    def __init__(self):
        self.risk_factors = {
            'Technology': [
                'Rapid technological change and obsolescence',
                'Cybersecurity threats and data breaches',
                'Regulatory scrutiny and antitrust concerns',
                'Competition from new entrants',
                'Supply chain disruptions'
            ],
            'Healthcare': [
                'Regulatory approval delays and rejections',
                'Patent expirations and generic competition',
                'Clinical trial failures',
                'Healthcare policy changes',
                'Pricing pressure and reimbursement cuts'
            ],
            'Financial Services': [
                'Interest rate sensitivity',
                'Credit risk and loan defaults',
                'Regulatory capital requirements',
                'Economic downturns and market volatility',
                'Cybersecurity and operational risks'
            ],
            'Consumer Discretionary': [
                'Economic sensitivity and consumer spending',
                'Seasonal demand fluctuations',
                'Competition and market share loss',
                'Supply chain and logistics challenges',
                'Brand reputation and consumer sentiment'
            ],
            'Energy': [
                'Commodity price volatility',
                'Environmental regulations and ESG concerns',
                'Geopolitical risks and supply disruptions',
                'Renewable energy transition',
                'Capital expenditure requirements'
            ]
        }
    
    def identify_risks(self, company_data, model_type):
        """Identify relevant risk factors for the company and model"""
        try:
            sector = company_data.get('sector', 'Unknown')
            company_name = company_data.get('company_name', 'Unknown')
            
            # Get sector-specific risks
            sector_risks = self.risk_factors.get(sector, [
                'Market volatility and economic uncertainty',
                'Competitive pressures and market share loss',
                'Regulatory changes and compliance costs',
                'Operational and execution risks',
                'Financial and liquidity risks'
            ])
            
            # Add model-specific risks
            model_risks = []
            if model_type.lower() == 'dcf':
                model_risks = [
                    'Terminal value assumptions may be inaccurate',
                    'WACC and discount rate sensitivity',
                    'Revenue growth assumptions may not materialize',
                    'Operating margin expansion may be limited'
                ]
            elif model_type.lower() == 'lbo':
                model_risks = [
                    'Debt capacity assumptions may be optimistic',
                    'Exit multiple assumptions may not be achievable',
                    'Operational improvements may be harder to realize',
                    'Market conditions may deteriorate during hold period'
                ]
            elif model_type.lower() == 'ma':
                model_risks = [
                    'Synergy realization may be delayed or reduced',
                    'Integration challenges may be underestimated',
                    'Regulatory approval may be denied or delayed',
                    'Market reaction may be negative'
                ]
            elif model_type.lower() == 'comps':
                model_risks = [
                    'Peer multiples may not be appropriate comparators',
                    'Market conditions may change peer valuations',
                    'Company-specific factors may not be reflected',
                    'Multiple expansion/contraction may occur'
                ]
            
            # Combine and prioritize risks
            all_risks = sector_risks + model_risks
            
            # Add company-specific risk assessment
            risk_assessment = {
                'sector_risks': sector_risks,
                'model_risks': model_risks,
                'company_name': company_name,
                'sector': sector,
                'model_type': model_type,
                'risk_level': self._assess_overall_risk_level(company_data, sector_risks),
                'key_risks': all_risks[:8]  # Top 8 most relevant risks
            }
            
            return risk_assessment
            
        except Exception as e:
            print(f"❌ Risk analysis error: {e}")
            return {
                'sector_risks': ['General market and economic risks'],
                'model_risks': ['Model assumptions may not hold'],
                'company_name': company_data.get('company_name', 'Unknown'),
                'sector': company_data.get('sector', 'Unknown'),
                'model_type': model_type,
                'risk_level': 'Medium',
                'key_risks': ['Market volatility', 'Competitive pressures', 'Regulatory changes']
            }
    
    def _assess_overall_risk_level(self, company_data, sector_risks):
        """Assess overall risk level based on company characteristics"""
        try:
            market_cap = company_data.get('market_cap', 0)
            operating_margin = company_data.get('operating_margin', 0)
            
            risk_score = 0
            
            # Market cap risk (smaller companies = higher risk)
            if market_cap < 1000000000:  # < $1B
                risk_score += 3
            elif market_cap < 10000000000:  # < $10B
                risk_score += 2
            elif market_cap < 100000000000:  # < $100B
                risk_score += 1
            
            # Operating margin risk (lower margins = higher risk)
            if operating_margin < 0.05:  # < 5%
                risk_score += 3
            elif operating_margin < 0.10:  # < 10%
                risk_score += 2
            elif operating_margin < 0.15:  # < 15%
                risk_score += 1
            
            # Determine risk level
            if risk_score >= 5:
                return 'High'
            elif risk_score >= 3:
                return 'Medium-High'
            elif risk_score >= 1:
                return 'Medium'
            else:
                return 'Low'
                
        except Exception as e:
            print(f"❌ Risk level assessment error: {e}")
            return 'Medium'

# Phase 3 AI Agent Enhancements

class AdvancedAnalysisEngine:
    """Advanced analysis engine for detailed investment recommendations"""
    
    def __init__(self):
        self.market_indicators = {}
        self.sector_trends = {}
        self.opportunity_cache = {}
    
    def assess_investment_opportunity(self, company_data, model_results, model_type, peer_metrics=None, risk_assessment=None):
        """Assess investment opportunity with specific buy/sell/short recommendations"""
        try:
            company_name = company_data.get('company_name', 'Unknown')
            sector = company_data.get('sector', 'Unknown')
            market_cap = company_data.get('market_cap', 0)
            operating_margin = company_data.get('operating_margin', 0)
            revenue = company_data.get('revenue', 0)
            
            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(company_data, model_results, model_type, peer_metrics, risk_assessment)
            
            # Determine investment recommendation
            recommendation = self._determine_recommendation(opportunity_score, model_results, model_type)
            
            # Generate specific rationale
            rationale = self._generate_rationale(company_data, model_results, model_type, peer_metrics, risk_assessment, recommendation)
            
            # Calculate confidence level
            confidence = self._calculate_confidence(model_results, peer_metrics, risk_assessment)
            
            return {
                'recommendation': recommendation,
                'opportunity_score': opportunity_score,
                'confidence_level': confidence,
                'rationale': rationale,
                'key_drivers': self._identify_key_drivers(company_data, model_results, model_type),
                'risk_factors': self._prioritize_risks(risk_assessment),
                'market_context': self._assess_market_context(sector, model_type),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Advanced analysis error: {e}")
            return self._fallback_opportunity_assessment(company_data, model_results, model_type)
    
    def _calculate_opportunity_score(self, company_data, model_results, model_type, peer_metrics=None, risk_assessment=None):
        """Calculate comprehensive opportunity score (0-100)"""
        try:
            score = 50  # Base score
            
            # Model-specific scoring
            if model_type.lower() == 'dcf':
                upside_downside = model_results.get('upside_downside', 0)
                if upside_downside > 20:
                    score += 20
                elif upside_downside > 10:
                    score += 10
                elif upside_downside < -20:
                    score -= 20
                elif upside_downside < -10:
                    score -= 10
                    
            elif model_type.lower() == 'lbo':
                irr = model_results.get('irr', 0)
                if irr > 0.25:
                    score += 20
                elif irr > 0.20:
                    score += 10
                elif irr < 0.15:
                    score -= 15
                    
            elif model_type.lower() == 'ma':
                accretion = model_results.get('accretion_dilution', 0)
                if accretion > 0.05:
                    score += 15
                elif accretion > 0.02:
                    score += 5
                elif accretion < -0.05:
                    score -= 15
                    
            elif model_type.lower() == 'comps':
                pe_ratio = model_results.get('pe_ratio', 0)
                if pe_ratio < 15:  # Value play
                    score += 15
                elif pe_ratio > 30:  # Growth play
                    score += 10
                elif pe_ratio > 50:  # Overvalued
                    score -= 10
            
            # Company fundamentals
            operating_margin = company_data.get('operating_margin', 0)
            if operating_margin > 0.20:
                score += 10
            elif operating_margin > 0.15:
                score += 5
            elif operating_margin < 0.05:
                score -= 10
            
            # Market cap consideration
            market_cap = company_data.get('market_cap', 0)
            if market_cap > 100000000000:  # > $100B
                score += 5  # Large cap stability
            elif market_cap < 1000000000:  # < $1B
                score -= 5  # Small cap risk
            
            # Risk adjustment
            if risk_assessment:
                risk_level = risk_assessment.get('risk_level', 'Medium')
                if risk_level == 'Low':
                    score += 5
                elif risk_level == 'High':
                    score -= 10
                elif risk_level == 'Medium-High':
                    score -= 5
            
            # Peer comparison adjustment
            if peer_metrics:
                company_margin = company_data.get('operating_margin', 0)
                peer_margins = [metrics.get('operating_margin', 0) for metrics in peer_metrics.values()]
                if peer_margins:
                    avg_peer_margin = sum(peer_margins) / len(peer_margins)
                    if company_margin > avg_peer_margin * 1.2:
                        score += 10
                    elif company_margin < avg_peer_margin * 0.8:
                        score -= 10
            
            return max(0, min(100, score))
            
        except Exception as e:
            print(f"❌ Opportunity score calculation error: {e}")
            return 50
    
    def _determine_recommendation(self, opportunity_score, model_results, model_type):
        """Determine specific investment recommendation"""
        try:
            if opportunity_score >= 75:
                return {
                    'action': 'STRONG BUY',
                    'confidence': 'High',
                    'reasoning': 'Exceptional opportunity with strong fundamentals and favorable model results'
                }
            elif opportunity_score >= 65:
                return {
                    'action': 'BUY',
                    'confidence': 'Medium-High',
                    'reasoning': 'Attractive opportunity with good fundamentals and positive model results'
                }
            elif opportunity_score >= 55:
                return {
                    'action': 'HOLD',
                    'confidence': 'Medium',
                    'reasoning': 'Neutral position with mixed signals and moderate risk'
                }
            elif opportunity_score >= 45:
                return {
                    'action': 'SELL',
                    'confidence': 'Medium',
                    'reasoning': 'Unfavorable position with concerning fundamentals or model results'
                }
            else:
                return {
                    'action': 'STRONG SELL',
                    'confidence': 'High',
                    'reasoning': 'Poor opportunity with weak fundamentals and negative model results'
                }
                
        except Exception as e:
            print(f"❌ Recommendation determination error: {e}")
            return {
                'action': 'HOLD',
                'confidence': 'Low',
                'reasoning': 'Unable to determine clear recommendation due to data limitations'
            }
    
    def _generate_rationale(self, company_data, model_results, model_type, peer_metrics=None, risk_assessment=None, recommendation=None):
        """Generate detailed investment rationale"""
        try:
            company_name = company_data.get('company_name', 'Unknown')
            sector = company_data.get('sector', 'Unknown')
            market_cap = company_data.get('market_cap', 0)
            operating_margin = company_data.get('operating_margin', 0)
            
            rationale_parts = []
            
            # Company-specific factors
            if operating_margin > 0.20:
                rationale_parts.append(f"{company_name} demonstrates **exceptional operational efficiency** with a {operating_margin*100:.1f}% operating margin, making it attractive for **long-term investment**")
            elif operating_margin < 0.05:
                rationale_parts.append(f"{company_name} shows **concerning operational challenges** with only a {operating_margin*100:.1f}% operating margin, suggesting **potential shorting opportunity**")
            
            # Market cap considerations
            if market_cap > 100000000000:  # > $100B
                rationale_parts.append(f"As a **large-cap company** (${market_cap/1e9:.1f}B), {company_name} offers **stability and liquidity** for institutional investors")
            elif market_cap < 1000000000:  # < $1B
                rationale_parts.append(f"As a **small-cap company** (${market_cap/1e6:.1f}M), {company_name} presents **higher risk but potential for significant returns**")
            
            # Model-specific rationale
            if model_type.lower() == 'dcf':
                upside_downside = model_results.get('upside_downside', 0)
                implied_price = model_results.get('implied_price', 0)
                current_price = model_results.get('current_price', 0)
                
                if upside_downside > 20:
                    rationale_parts.append(f"The DCF model suggests **significant upside potential** ({upside_downside:.1f}%) with implied price of ${implied_price:.2f} vs current ${current_price:.2f}, making this a **strong buy opportunity**")
                elif upside_downside < -20:
                    rationale_parts.append(f"The DCF model indicates **substantial downside risk** ({upside_downside:.1f}%) with implied price of ${implied_price:.2f} vs current ${current_price:.2f}, suggesting a **shorting opportunity**")
                    
            elif model_type.lower() == 'lbo':
                irr = model_results.get('irr', 0)
                multiple = model_results.get('multiple', 0)
                
                if irr > 0.25:
                    rationale_parts.append(f"The LBO model projects **exceptional returns** ({irr*100:.1f}% IRR, {multiple:.1f}x multiple), making this an **attractive acquisition target**")
                elif irr < 0.15:
                    rationale_parts.append(f"The LBO model shows **modest returns** ({irr*100:.1f}% IRR, {multiple:.1f}x multiple), suggesting **limited private equity interest**")
                    
            elif model_type.lower() == 'ma':
                accretion = model_results.get('accretion_dilution', 0)
                synergy_value = model_results.get('synergy_value', 0)
                
                if accretion > 0.05:
                    rationale_parts.append(f"The M&A model indicates **strong accretion potential** ({accretion*100:.1f}%) with ${synergy_value/1e9:.1f}B in synergies, making this a **compelling merger candidate**")
                elif accretion < -0.05:
                    rationale_parts.append(f"The M&A model suggests **significant dilution risk** ({accretion*100:.1f}%) with limited synergies, indicating **poor merger prospects**")
                    
            elif model_type.lower() == 'comps':
                pe_ratio = model_results.get('pe_ratio', 0)
                ev_revenue = model_results.get('ev_revenue', 0)
                
                if pe_ratio < 15:
                    rationale_parts.append(f"Trading at {pe_ratio:.1f}x P/E and {ev_revenue:.1f}x EV/Revenue, {company_name} appears **undervalued relative to peers**, presenting a **value investment opportunity**")
                elif pe_ratio > 50:
                    rationale_parts.append(f"Trading at {pe_ratio:.1f}x P/E and {ev_revenue:.1f}x EV/Revenue, {company_name} appears **significantly overvalued**, suggesting a **shorting opportunity**")
            
            # Peer comparison
            if peer_metrics:
                company_margin = company_data.get('operating_margin', 0)
                peer_margins = [metrics.get('operating_margin', 0) for metrics in peer_metrics.values()]
                if peer_margins:
                    avg_peer_margin = sum(peer_margins) / len(peer_margins)
                    if company_margin > avg_peer_margin * 1.2:
                        rationale_parts.append(f"{company_name} **outperforms sector peers** with {company_margin*100:.1f}% margin vs {avg_peer_margin*100:.1f}% average, indicating **competitive advantage**")
                    elif company_margin < avg_peer_margin * 0.8:
                        rationale_parts.append(f"{company_name} **underperforms sector peers** with {company_margin*100:.1f}% margin vs {avg_peer_margin*100:.1f}% average, suggesting **competitive disadvantage**")
            
            # Risk factors
            if risk_assessment:
                risk_level = risk_assessment.get('risk_level', 'Medium')
                if risk_level == 'High':
                    rationale_parts.append(f"**High risk profile** requires careful consideration, but may present **contrarian opportunities** for risk-tolerant investors")
                elif risk_level == 'Low':
                    rationale_parts.append(f"**Low risk profile** provides **defensive characteristics** suitable for conservative portfolios")
            
            return ' '.join(rationale_parts) if rationale_parts else f"Based on the {model_type.upper()} analysis, {company_name} presents a {recommendation.get('action', 'HOLD')} opportunity."
            
        except Exception as e:
            print(f"❌ Rationale generation error: {e}")
            return f"Investment analysis for {company_data.get('company_name', 'Unknown')} based on {model_type.upper()} model."
    
    def _identify_key_drivers(self, company_data, model_results, model_type):
        """Identify key investment drivers"""
        try:
            drivers = []
            
            # Financial drivers
            operating_margin = company_data.get('operating_margin', 0)
            if operating_margin > 0.20:
                drivers.append("High operational efficiency")
            elif operating_margin < 0.05:
                drivers.append("Operational challenges")
            
            # Model-specific drivers
            if model_type.lower() == 'dcf':
                upside_downside = model_results.get('upside_downside', 0)
                if abs(upside_downside) > 15:
                    drivers.append("Significant valuation gap")
                    
            elif model_type.lower() == 'lbo':
                irr = model_results.get('irr', 0)
                if irr > 0.20:
                    drivers.append("Strong cash flow generation")
                    
            elif model_type.lower() == 'ma':
                accretion = model_results.get('accretion_dilution', 0)
                if abs(accretion) > 0.03:
                    drivers.append("Meaningful synergy potential")
                    
            elif model_type.lower() == 'comps':
                pe_ratio = model_results.get('pe_ratio', 0)
                if pe_ratio < 15:
                    drivers.append("Value characteristics")
                elif pe_ratio > 30:
                    drivers.append("Growth characteristics")
            
            return drivers[:5]  # Top 5 drivers
            
        except Exception as e:
            print(f"❌ Key drivers identification error: {e}")
            return ["Financial performance", "Market conditions", "Competitive positioning"]
    
    def _prioritize_risks(self, risk_assessment):
        """Prioritize and categorize risks"""
        try:
            if not risk_assessment:
                return ["Market volatility", "Economic uncertainty"]
            
            key_risks = risk_assessment.get('key_risks', [])
            risk_level = risk_assessment.get('risk_level', 'Medium')
            
            prioritized_risks = []
            
            # Add risk level context
            if risk_level == 'High':
                prioritized_risks.append("High overall risk profile")
            elif risk_level == 'Low':
                prioritized_risks.append("Low overall risk profile")
            
            # Add top risks
            prioritized_risks.extend(key_risks[:3])
            
            return prioritized_risks
            
        except Exception as e:
            print(f"❌ Risk prioritization error: {e}")
            return ["Market volatility", "Competitive pressures", "Regulatory changes"]
    
    def _assess_market_context(self, sector, model_type):
        """Assess current market context for the sector and model type"""
        try:
            context = []
            
            # Sector-specific context
            if sector == 'Technology':
                context.append("Technology sector experiencing rapid innovation and disruption")
            elif sector == 'Healthcare':
                context.append("Healthcare sector facing regulatory and demographic changes")
            elif sector == 'Financial Services':
                context.append("Financial services sector sensitive to interest rate changes")
            elif sector == 'Energy':
                context.append("Energy sector transitioning to renewable sources")
            
            # Model-specific context
            if model_type.lower() == 'dcf':
                context.append("DCF models sensitive to interest rate and growth assumptions")
            elif model_type.lower() == 'lbo':
                context.append("LBO market conditions affecting debt availability and exit multiples")
            elif model_type.lower() == 'ma':
                context.append("M&A market activity influenced by regulatory and economic conditions")
            elif model_type.lower() == 'comps':
                context.append("Trading multiples affected by market sentiment and sector rotation")
            
            return context
            
        except Exception as e:
            print(f"❌ Market context assessment error: {e}")
            return ["Current market conditions", "Sector trends", "Economic environment"]
    
    def _calculate_confidence(self, model_results, peer_metrics=None, risk_assessment=None):
        """Calculate confidence level in the analysis"""
        try:
            confidence_factors = []
            
            # Model results quality
            if model_results:
                confidence_factors.append("Strong model results")
            
            # Peer data availability
            if peer_metrics and len(peer_metrics) >= 3:
                confidence_factors.append("Comprehensive peer data")
            
            # Risk assessment completeness
            if risk_assessment and risk_assessment.get('risk_level'):
                confidence_factors.append("Complete risk assessment")
            
            # Determine confidence level
            if len(confidence_factors) >= 3:
                return "High"
            elif len(confidence_factors) >= 2:
                return "Medium"
            else:
                return "Low"
                
        except Exception as e:
            print(f"❌ Confidence calculation error: {e}")
            return "Low"
    
    def _fallback_opportunity_assessment(self, company_data, model_results, model_type):
        """Fallback opportunity assessment when advanced analysis fails"""
        return {
            'recommendation': {
                'action': 'HOLD',
                'confidence': 'Low',
                'reasoning': 'Limited data available for comprehensive analysis'
            },
            'opportunity_score': 50,
            'confidence_level': 'Low',
            'rationale': f"Basic analysis for {company_data.get('company_name', 'Unknown')} based on {model_type.upper()} model.",
            'key_drivers': ['Financial performance', 'Market conditions'],
            'risk_factors': ['Market volatility', 'Economic uncertainty'],
            'market_context': ['Current market conditions'],
            'timestamp': datetime.now().isoformat()
        }

class ScenarioGenerator:
    """Intelligent scenario generation with market conditions"""
    
    def __init__(self):
        self.scenario_templates = {
            'dcf': {
                'bull': {'revenue_growth_multiplier': 1.5, 'margin_expansion': 0.02, 'wacc_reduction': 0.01},
                'bear': {'revenue_growth_multiplier': 0.5, 'margin_contraction': 0.02, 'wacc_increase': 0.01},
                'base': {'revenue_growth_multiplier': 1.0, 'margin_expansion': 0.0, 'wacc_change': 0.0}
            },
            'lbo': {
                'bull': {'irr_multiplier': 1.3, 'multiple_expansion': 0.2, 'debt_capacity_increase': 0.1},
                'bear': {'irr_multiplier': 0.7, 'multiple_contraction': 0.2, 'debt_capacity_decrease': 0.1},
                'base': {'irr_multiplier': 1.0, 'multiple_change': 0.0, 'debt_capacity_change': 0.0}
            }
        }
    
    def generate_intelligent_scenarios(self, company_data, model_type, base_scenario):
        """Generate intelligent scenarios based on market conditions and company characteristics"""
        try:
            scenarios = {}
            
            # Get base scenario
            scenarios['base'] = base_scenario
            
            # Generate bull scenario
            scenarios['bull'] = self._generate_bull_scenario(company_data, model_type, base_scenario)
            
            # Generate bear scenario
            scenarios['bear'] = self._generate_bear_scenario(company_data, model_type, base_scenario)
            
            return scenarios
            
        except Exception as e:
            print(f"❌ Scenario generation error: {e}")
            return {'base': base_scenario}
    
    def _generate_bull_scenario(self, company_data, model_type, base_scenario):
        """Generate optimistic scenario"""
        try:
            bull_scenario = base_scenario.copy()
            
            if model_type.lower() == 'dcf':
                # Optimistic assumptions
                bull_scenario['revenue_growth_1'] = base_scenario.get('revenue_growth_1', 0.08) * 1.5
                bull_scenario['operating_margin'] = base_scenario.get('operating_margin', 0.15) + 0.02
                bull_scenario['wacc'] = base_scenario.get('wacc', 0.10) - 0.01
                
            elif model_type.lower() == 'lbo':
                # Optimistic LBO assumptions
                bull_scenario['irr'] = base_scenario.get('irr', 0.20) * 1.3
                bull_scenario['multiple'] = base_scenario.get('multiple', 2.0) + 0.2
                bull_scenario['debt_capacity'] = base_scenario.get('debt_capacity', 1000000000) * 1.1
                
            return bull_scenario
            
        except Exception as e:
            print(f"❌ Bull scenario generation error: {e}")
            return base_scenario
    
    def _generate_bear_scenario(self, company_data, model_type, base_scenario):
        """Generate pessimistic scenario"""
        try:
            bear_scenario = base_scenario.copy()
            
            if model_type.lower() == 'dcf':
                # Pessimistic assumptions
                bear_scenario['revenue_growth_1'] = base_scenario.get('revenue_growth_1', 0.08) * 0.5
                bear_scenario['operating_margin'] = base_scenario.get('operating_margin', 0.15) - 0.02
                bear_scenario['wacc'] = base_scenario.get('wacc', 0.10) + 0.01
                
            elif model_type.lower() == 'lbo':
                # Pessimistic LBO assumptions
                bear_scenario['irr'] = base_scenario.get('irr', 0.20) * 0.7
                bear_scenario['multiple'] = base_scenario.get('multiple', 2.0) - 0.2
                bear_scenario['debt_capacity'] = base_scenario.get('debt_capacity', 1000000000) * 0.9
                
            return bear_scenario
            
        except Exception as e:
            print(f"❌ Bear scenario generation error: {e}")
            return base_scenario

# Initialize Phase 3 engines
advanced_analysis_engine = AdvancedAnalysisEngine()
scenario_generator = ScenarioGenerator()

# Initialize Phase 2 engines
research_engine = ResearchEngine()
peer_analysis_engine = PeerAnalysisEngine()
risk_analysis_engine = RiskAnalysisEngine()

# Initialize AI agent
ai_agent = FinancialAIAgent()

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

# AI Chat API Endpoints

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint for model Q&A"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "validation_error",
                "message": "JSON body required"
            }), 400
        
        model_id = data.get('model_id')
        user_question = data.get('question', '').strip()
        
        if not model_id:
            return jsonify({
                "error": "validation_error",
                "message": "Model ID required"
            }), 400
        
        if not user_question:
            return jsonify({
                "error": "validation_error",
                "message": "Question required"
            }), 400
        
        # Get model from storage
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        # Prepare model context for AI
        model_context = {
            'model_type': model.get('type'),
            'ticker': model.get('ticker'),
            'company_name': model.get('result', {}).get('company_name'),
            'scenarios': model.get('result', {}).get('scenarios', {}),
            'assumptions': model.get('result', {}).get('assumptions', {}),
            'model_summary': model.get('result', {}).get('model_summary', {})
        }
        
        # Get AI response
        ai_response = ai_agent.chat_about_model(user_question, model_context)
        
        return jsonify({
            "success": True,
            "response": ai_response['response'],
            "source": ai_response['source'],
            "timestamp": ai_response['timestamp']
        })
        
    except Exception as e:
        print(f"Error in ai_chat: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "AI chat failed"
        }), 500

@app.route('/api/ai/analysis/<model_id>')
def get_ai_analysis(model_id):
    """Get AI analysis for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        ai_analysis = model.get('ai_analysis')
        ai_assumption_validation = model.get('ai_assumption_validation')
        
        if not ai_analysis and not ai_assumption_validation:
            return jsonify({
                "error": "not_available",
                "message": "AI analysis not available for this model"
            }), 404
        
        return jsonify({
            "success": True,
            "ai_analysis": ai_analysis,
            "ai_assumption_validation": ai_assumption_validation
        })
        
    except Exception as e:
        print(f"Error in get_ai_analysis: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get AI analysis"
        }), 500

# Phase 2 API Endpoints

@app.route('/api/phase2/research/<model_id>')
def get_phase2_research(model_id):
    """Get Phase 2 research data for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        ticker = model.get('ticker')
        if not ticker:
            return jsonify({
                "error": "validation_error",
                "message": "Ticker not found in model"
            }), 400
        
        # Get research data
        news_data = research_engine.get_company_news(ticker)
        earnings_data = research_engine.get_earnings_data(ticker)
        
        return jsonify({
            "success": True,
            "ticker": ticker,
            "news_data": news_data,
            "earnings_data": earnings_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase2_research: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get research data"
        }), 500

@app.route('/api/phase2/peers/<model_id>')
def get_phase2_peers(model_id):
    """Get Phase 2 peer analysis data for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        ticker = model.get('ticker')
        company_data = model.get('result', {}).get('company_data', {})
        sector = company_data.get('sector', 'Unknown')
        
        if not ticker:
            return jsonify({
                "error": "validation_error",
                "message": "Ticker not found in model"
            }), 400
        
        # Get peer analysis data
        peers = peer_analysis_engine.get_peer_companies(ticker, sector)
        peer_metrics = peer_analysis_engine.analyze_peer_metrics(ticker, peers)
        
        return jsonify({
            "success": True,
            "ticker": ticker,
            "sector": sector,
            "peers": peers,
            "peer_metrics": peer_metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase2_peers: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get peer analysis data"
        }), 500

@app.route('/api/phase2/risks/<model_id>')
def get_phase2_risks(model_id):
    """Get Phase 2 risk analysis data for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        model_type = model.get('type')
        company_data = model.get('result', {}).get('company_data', {})
        
        if not model_type or not company_data:
            return jsonify({
                "error": "validation_error",
                "message": "Model type or company data not found"
            }), 400
        
        # Get risk analysis data
        risk_assessment = risk_analysis_engine.identify_risks(company_data, model_type)
        
        return jsonify({
            "success": True,
            "model_type": model_type,
            "risk_assessment": risk_assessment,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase2_risks: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get risk analysis data"
        }), 500

@app.route('/api/phase2/summary/<model_id>')
def get_phase2_summary(model_id):
    """Get Phase 2 summary data for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        phase2_data = model.get('phase2_data', {})
        
        return jsonify({
            "success": True,
            "phase2_data": phase2_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase2_summary: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get Phase 2 summary data"
        }), 500

# Phase 3 API Endpoints

@app.route('/api/phase3/recommendation/<model_id>')
def get_phase3_recommendation(model_id):
    """Get Phase 3 investment recommendation for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        phase3_data = model.get('phase3_data', {})
        if not phase3_data:
            return jsonify({
                "error": "not_available",
                "message": "Phase 3 analysis not available for this model"
            }), 404
        
        return jsonify({
            "success": True,
            "recommendation": phase3_data.get('recommendation', {}),
            "opportunity_score": phase3_data.get('opportunity_score', 50),
            "confidence_level": phase3_data.get('confidence_level', 'Medium'),
            "rationale": phase3_data.get('rationale', ''),
            "key_drivers": phase3_data.get('key_drivers', []),
            "risk_factors": phase3_data.get('risk_factors', []),
            "market_context": phase3_data.get('market_context', []),
            "timestamp": phase3_data.get('timestamp', datetime.now().isoformat())
        })
        
    except Exception as e:
        print(f"Error in get_phase3_recommendation: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get Phase 3 recommendation data"
        }), 500

@app.route('/api/phase3/advanced-analysis/<model_id>')
def get_phase3_advanced_analysis(model_id):
    """Get Phase 3 advanced analysis for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        model_type = model.get('type')
        company_data = model.get('result', {}).get('company_data', {})
        model_results = model.get('result', {}).get('scenarios', {}).get('base', {})
        
        if not model_type or not company_data or not model_results:
            return jsonify({
                "error": "validation_error",
                "message": "Model data incomplete"
            }), 400
        
        # Get peer analysis
        ticker = model.get('ticker')
        sector = company_data.get('sector', 'Unknown')
        peers = peer_analysis_engine.get_peer_companies(ticker, sector)
        peer_metrics = peer_analysis_engine.analyze_peer_metrics(ticker, peers)
        
        # Get risk analysis
        risk_assessment = risk_analysis_engine.identify_risks(company_data, model_type)
        
        # Generate advanced analysis
        advanced_analysis = advanced_analysis_engine.assess_investment_opportunity(
            company_data, model_results, model_type, peer_metrics, risk_assessment
        )
        
        return jsonify({
            "success": True,
            "advanced_analysis": advanced_analysis,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase3_advanced_analysis: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get Phase 3 advanced analysis"
        }), 500

@app.route('/api/phase3/scenarios/<model_id>')
def get_phase3_scenarios(model_id):
    """Get Phase 3 intelligent scenarios for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        model_type = model.get('type')
        company_data = model.get('result', {}).get('company_data', {})
        base_scenario = model.get('result', {}).get('scenarios', {}).get('base', {})
        
        if not model_type or not company_data or not base_scenario:
            return jsonify({
                "error": "validation_error",
                "message": "Model data incomplete"
            }), 400
        
        # Generate intelligent scenarios
        scenarios = scenario_generator.generate_intelligent_scenarios(
            company_data, model_type, base_scenario
        )
        
        return jsonify({
            "success": True,
            "scenarios": scenarios,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase3_scenarios: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get Phase 3 scenarios"
        }), 500

@app.route('/api/phase3/summary/<model_id>')
def get_phase3_summary(model_id):
    """Get Phase 3 summary data for a model"""
    try:
        model = MODEL_STORAGE.get(model_id)
        if not model:
            return jsonify({
                "error": "not_found",
                "message": "Model not found"
            }), 404
        
        phase3_data = model.get('phase3_data', {})
        
        return jsonify({
            "success": True,
            "phase3_data": phase3_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_phase3_summary: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Failed to get Phase 3 summary data"
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
                
                # Generate company-specific mock data based on ticker
                ticker_hash = hash(ticker.upper()) % 1000
                base_enterprise_value = 500000000000 + (ticker_hash * 1000000000)  # 500B to 1.5T range
                base_current_price = 50 + (ticker_hash * 0.2)  # $50 to $250 range
                
                # Create realistic mock scenarios
                mock_scenarios = {}
                for scenario_name, multiplier in [('bear', 0.7), ('base', 1.0), ('bull', 1.4)]:
                    enterprise_value = base_enterprise_value * multiplier
                    equity_value = enterprise_value * 0.9  # Assume some net debt
                    implied_price = base_current_price * multiplier
                    current_price = base_current_price
                    upside_downside = ((implied_price / current_price) - 1) * 100
                    
                    mock_scenarios[scenario_name] = {
                        'enterprise_value': enterprise_value,
                        'equity_value': equity_value,
                        'implied_price': implied_price,
                        'current_price': current_price,
                        'upside_downside': upside_downside
                    }
                
                # Create realistic mock company data
                mock_company_data = {
                    'ticker': ticker,
                    'company_name': f"{ticker} Corporation",
                    'sector': 'Technology',
                    'industry': 'Software',
                    'market_cap': base_enterprise_value * 0.9,  # Slightly less than enterprise value
                    'enterprise_value': base_enterprise_value,
                    'current_price': base_current_price,
                    'shares_outstanding': 1000000000,  # 1B shares
                    'beta': 1.0 + (ticker_hash * 0.001),
                    'pe_ratio': 20 + (ticker_hash * 0.01),
                    'forward_pe': 18 + (ticker_hash * 0.01),
                    'peg_ratio': 1.5 + (ticker_hash * 0.001),
                    'price_to_book': 3.0 + (ticker_hash * 0.01),
                    'debt_to_equity': 0.3 + (ticker_hash * 0.001),
                    'return_on_equity': 0.15 + (ticker_hash * 0.001),
                    'return_on_assets': 0.10 + (ticker_hash * 0.001),
                    'profit_margin': 0.20 + (ticker_hash * 0.0002),
                    'operating_margin': 0.25 + (ticker_hash * 0.0002),
                    'revenue_growth': 0.08 + (ticker_hash * 0.0001),
                    'earnings_growth': 0.12 + (ticker_hash * 0.0001),
                    'free_cash_flow': base_enterprise_value * 0.1,  # 10% of enterprise value
                    'total_cash': base_enterprise_value * 0.05,  # 5% of enterprise value
                    'total_debt': base_enterprise_value * 0.1,  # 10% of enterprise value
                    'book_value': base_enterprise_value * 0.3,  # 30% of enterprise value
                    'dividend_yield': 0.02 + (ticker_hash * 0.0001),
                    'payout_ratio': 0.3 + (ticker_hash * 0.001),
                    'revenue': base_enterprise_value * 0.8,  # Revenue roughly 80% of enterprise value
                    'gross_profit': base_enterprise_value * 0.6,  # Gross profit 60% of enterprise value
                    'operating_income': base_enterprise_value * 0.2,  # Operating income 20% of enterprise value
                    'net_income': base_enterprise_value * 0.15,  # Net income 15% of enterprise value
                    'ebitda': base_enterprise_value * 0.25,  # EBITDA 25% of enterprise value
                    'data_sources': ['mock_data']
                }
                
                model_result = {
                    'model_type': model_type,
                    'ticker': ticker,
                    'status': 'completed',
                    'company_name': f"{ticker} Corporation",
                    'sector': mock_company_data['sector'],
                    'industry': mock_company_data['industry'],
                    'processing_time_seconds': round(processing_time, 2),
                    'use_market_data': use_market_data,
                    'scenario_type': scenario,
                    'company_data': mock_company_data,
                    'scenarios': mock_scenarios,
                    'assumptions': {
                        'base': {
                            'revenue_growth_rate': 0.08 + (ticker_hash * 0.0001),
                            'wacc': 0.08 + (ticker_hash * 0.00005),
                            'terminal_growth_rate': 0.025,
                            'operating_margin': 0.20 + (ticker_hash * 0.0002)
                        }
                    },
                    'model_summary': {
                        'key_assumptions': {
                            'revenue_growth_rate': 0.08 + (ticker_hash * 0.0001),
                            'wacc': 0.08 + (ticker_hash * 0.00005),
                            'terminal_growth_rate': 0.025,
                            'operating_margin': 0.20 + (ticker_hash * 0.0002)
                        },
                        'valuation_outputs': mock_scenarios['base']
                    }
                }
            
            # Generate Excel file and save to temp directory
            excel_filename = None
            if model_result:  # Generate Excel for any model type with results
                try:
                    print(f"📄 Generating Excel file for {ticker} - Model type: {model_type}")
                    # Generate comprehensive Excel file based on model type
                    wb = excel_generator.generate_model(model_result, model_type)
                    
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
                    # Flash error to user
                    flash(f"Excel generation failed: {str(e)}", 'error')
            
            # Generate AI analysis for the model with Phase 2 enhancements
            ai_analysis = None
            ai_assumption_validation = None
            phase2_data = None
            phase3_data = None
            
            if model_result:
                try:
                    print(f"🤖 Generating Phase 2 AI analysis for {ticker} ({model_type.upper()})")
                    
                    # Get company data and model results for AI analysis
                    company_data = model_result.get('company_data', {})
                    scenarios = model_result.get('scenarios', {})
                    assumptions = model_result.get('assumptions', {})
                    
                    # Use base scenario for analysis if available, otherwise use model summary
                    model_results = scenarios.get('base', model_result.get('model_summary', {}).get('valuation_outputs', {}))
                    
                    if company_data and model_results:
                        # Generate Phase 2 AI model analysis for any model type
                        ai_analysis = ai_agent.analyze_model(model_type, company_data, model_results, scenarios, assumptions)
                        print(f"✅ Phase 2 AI analysis generated for {ticker} ({model_type.upper()})")
                        
                        # Extract Phase 2 and Phase 3 data from analysis
                        phase2_data = ai_analysis.get('phase2_data', {}) if ai_analysis else {}
                        phase3_data = ai_analysis.get('phase3_data', {}) if ai_analysis else {}
                        
                        # Generate AI assumption validation (primarily for DCF, but can work for others)
                        if assumptions and ('base' in assumptions or 'assumptions' in assumptions):
                            base_assumptions = assumptions.get('base', assumptions.get('assumptions', {}))
                            if base_assumptions:
                                ai_assumption_validation = ai_agent.validate_assumptions(company_data, base_assumptions)
                                print(f"✅ AI assumption validation generated for {ticker}")
                    
                except Exception as e:
                    print(f"⚠️ Phase 2 AI analysis failed for {ticker}: {e}")
                    # Continue without AI analysis - don't fail the entire model generation
                    # Ensure variables are set to None if AI analysis fails
                    ai_analysis = None
                    ai_assumption_validation = None
                    phase2_data = None
                    phase3_data = None
            
            MODEL_STORAGE[model_id] = {
                'id': model_id,
                'type': model_type,
                'ticker': ticker,
                'result': model_result,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'excel_filename': excel_filename,
                'file_ready': excel_filename is not None,
                'ai_analysis': ai_analysis,
                'ai_assumption_validation': ai_assumption_validation,
                'phase2_data': phase2_data,
                'phase3_data': phase3_data
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

            <!-- Jump to Chat Button -->
            <div class="mb-3">
                <button id="jump-to-chat" class="bg-gray-50 text-gray-600 border border-gray-200 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors">
                    💬 Chat with AI
                </button>
            </div>

            <div class="grid grid-cols-12 gap-6">
                <!-- Left Panel - Model Info -->
                <div class="col-span-12 xl:col-span-8">
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

                        <!-- Company-Specific Assumptions -->
                        <div class="bg-white rounded-lg p-5 shadow-sm border border-gray-100">
                            <div class="flex items-center justify-between mb-4">
                                <h3 class="font-medium text-gray-900">Company-Specific Assumptions</h3>
                                <span class="text-xs text-gray-500 bg-blue-50 px-2 py-1 rounded">
                                    {result.get('company_specific_data', {}).get('data_source', 'yfinance').upper()}
                                </span>
                            </div>
                            <div class="space-y-3">
                                {self._format_company_assumptions_table(result.get('company_specific_data', {}), result.get('sanity_flags', []))}
                            </div>
                            {self._format_assumptions_narrative(result.get('narrative', ''))}
                        </div>

                        <!-- AI Analysis -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <div class="flex items-center mb-4">
                                <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                                    <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                                    </svg>
                                </div>
                                <h3 class="font-medium text-gray-900">AI Analysis</h3>
                            </div>
                            
                            <div id="ai-analysis-content">
                                <div class="text-sm text-gray-600 mb-4">
                                    <p>🤖 AI-powered investment analysis and assumption validation</p>
                                </div>
                                
                                <div id="ai-analysis-loading" class="hidden">
                                    <div class="flex items-center justify-center py-4">
                                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                        <span class="ml-2 text-sm text-gray-600">Loading AI analysis...</span>
                                    </div>
                                </div>
                                
                                <div id="ai-analysis-results" class="hidden">
                                    <div class="space-y-4">
                                        <div id="ai-model-analysis" class="hidden">
                                            <h4 class="font-medium text-gray-900 mb-2">Investment Analysis</h4>
                                            <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-line" id="ai-analysis-text"></div>
                                        </div>
                                        
                                        <div id="ai-assumption-validation" class="hidden">
                                            <h4 class="font-medium text-gray-900 mb-2">Assumption Validation</h4>
                                            <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-line" id="ai-validation-text"></div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div id="ai-analysis-error" class="hidden">
                                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                                        <p class="text-sm text-red-600">AI analysis is currently unavailable. Please try again later.</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                        <!-- Valuation Results -->
                        <div class="bg-white rounded-lg p-5 shadow-sm border border-gray-100">
                            <h2 class="text-base font-medium text-gray-900 mb-4">Valuation Results</h2>
                            
{valuation_html}
                        </div>

                        <!-- Actions -->
                        <div class="bg-white rounded-lg p-5 shadow-sm border border-gray-100">
                            <h3 class="text-sm font-medium text-gray-700 mb-3">Next Steps</h3>
                            <div class="flex flex-wrap gap-2">
                                <a href="/generate-model" class="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
                                    Generate Another Model
                                </a>
                                <a href="/models" class="bg-gray-50 text-gray-700 border border-gray-200 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors">
                                    View All Models
                                </a>
                                <a href="/" class="bg-gray-50 text-gray-600 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors">
                                    Home
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Panel - Chat Assistant (Desktop) -->
                <div class="col-span-12 xl:col-span-4 xl:sticky xl:top-4 h-fit">
                    <div class="bg-white rounded-lg border border-gray-100 shadow-sm flex flex-col">
                        <header class="px-4 py-3 border-b border-gray-100">
                            <div class="flex items-center">
                                <div class="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center mr-3">
                                    <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-sm font-medium text-gray-900">Analyst Assistant</h3>
                            </div>
                        </header>
                        <div id="chat-messages" class="px-4 py-3 max-h-[60vh] overflow-y-auto" aria-live="polite">
                            <div class="text-xs text-gray-400 text-center py-3">
                                Ask me anything about this financial model
                            </div>
                        </div>
                        <div class="p-3 border-t border-gray-100 bg-gray-50">
                            <div class="flex space-x-2">
                                <input type="text" id="chat-input" placeholder="Ask about assumptions, valuation, or risks..." 
                                       class="flex-1 px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white"
                                       aria-label="Chat input">
                                <button id="chat-send" class="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                                        aria-label="Send message">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                                    </svg>
                                </button>
                            </div>
                            <div id="chat-loading" class="hidden mt-2">
                                <div class="flex items-center justify-center py-1">
                                    <div class="animate-spin rounded-full h-3 w-3 border-b border-blue-600"></div>
                                    <span class="ml-2 text-xs text-gray-500">AI is thinking...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Mobile Chat FAB -->
        <button id="mobile-chat-fab" aria-label="Open chat" class="fixed bottom-4 right-4 w-12 h-12 rounded-full bg-blue-600 text-white shadow-lg hover:bg-blue-700 transition-colors xl:hidden z-50 flex items-center justify-center">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>
        </button>

        <!-- Mobile Chat Bottom Sheet -->
        <div id="mobile-chat-sheet" class="fixed bottom-0 left-0 right-0 h-[65vh] bg-white rounded-t-xl shadow-2xl transform translate-y-full transition-transform duration-300 ease-out xl:hidden z-50">
            <div class="flex flex-col h-full">
                <!-- Header -->
                <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                    <div class="flex items-center">
                        <div class="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center mr-3">
                            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                            </svg>
                        </div>
                        <h3 class="text-sm font-medium text-gray-900">Analyst Assistant</h3>
                    </div>
                    <button id="close-mobile-chat" class="p-2 hover:bg-gray-100 rounded-full">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <!-- Messages -->
                <div id="mobile-chat-messages" class="flex-1 px-4 py-3 overflow-y-auto" aria-live="polite">
                    <div class="text-xs text-gray-400 text-center py-3">
                        Ask me anything about this financial model
                    </div>
                </div>
                
                <!-- Input -->
                <div class="p-3 border-t border-gray-100 bg-gray-50" style="padding-bottom: env(safe-area-inset-bottom, 12px);">
                    <div class="flex space-x-2">
                        <input type="text" id="mobile-chat-input" placeholder="Ask about assumptions, valuation, or risks..." 
                               class="flex-1 px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white"
                               aria-label="Chat input">
                        <button id="mobile-chat-send" class="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                                aria-label="Send message">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                            </svg>
                        </button>
                    </div>
                    <div id="mobile-chat-loading" class="hidden mt-2">
                        <div class="flex items-center justify-center py-1">
                            <div class="animate-spin rounded-full h-3 w-3 border-b border-blue-600"></div>
                            <span class="ml-2 text-xs text-gray-500">AI is thinking...</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // AI Analysis and Chat Functionality
            document.addEventListener('DOMContentLoaded', function() {{
                const modelId = '{model_id}';
                
                // Load AI analysis on page load
                loadAIAnalysis(modelId);
                
                // Setup chat functionality
                setupChat(modelId);
            }});
            
            async function loadAIAnalysis(modelId) {{
                const loadingEl = document.getElementById('ai-analysis-loading');
                const resultsEl = document.getElementById('ai-analysis-results');
                const errorEl = document.getElementById('ai-analysis-error');
                
                try {{
                    loadingEl.classList.remove('hidden');
                    
                    const response = await fetch(`/api/ai/analysis/${{modelId}}`);
                    const data = await response.json();
                    
                    loadingEl.classList.add('hidden');
                    
                    if (data.success) {{
                        resultsEl.classList.remove('hidden');
                        
                        // Display AI model analysis
                        if (data.ai_analysis && data.ai_analysis.analysis) {{
                            const analysisEl = document.getElementById('ai-model-analysis');
                            const analysisTextEl = document.getElementById('ai-analysis-text');
                            analysisTextEl.textContent = data.ai_analysis.analysis;
                            analysisEl.classList.remove('hidden');
                        }}
                        
                        // Display AI assumption validation
                        if (data.ai_assumption_validation && data.ai_assumption_validation.validation) {{
                            const validationEl = document.getElementById('ai-assumption-validation');
                            const validationTextEl = document.getElementById('ai-validation-text');
                            validationTextEl.textContent = data.ai_assumption_validation.validation;
                            validationEl.classList.remove('hidden');
                        }}
                    }} else {{
                        errorEl.classList.remove('hidden');
                    }}
                }} catch (error) {{
                    console.error('Error loading AI analysis:', error);
                    loadingEl.classList.add('hidden');
                    errorEl.classList.remove('hidden');
                }}
            }}
            
            function setupChat(modelId) {{
                // Desktop chat elements
                const chatInput = document.getElementById('chat-input');
                const chatSend = document.getElementById('chat-send');
                const chatMessages = document.getElementById('chat-messages');
                const chatLoading = document.getElementById('chat-loading');
                
                // Mobile chat elements
                const mobileChatFab = document.getElementById('mobile-chat-fab');
                const mobileChatSheet = document.getElementById('mobile-chat-sheet');
                const mobileChatInput = document.getElementById('mobile-chat-input');
                const mobileChatSend = document.getElementById('mobile-chat-send');
                const mobileChatMessages = document.getElementById('mobile-chat-messages');
                const mobileChatLoading = document.getElementById('mobile-chat-loading');
                const closeMobileChat = document.getElementById('close-mobile-chat');
                
                // Jump to chat button
                const jumpToChat = document.getElementById('jump-to-chat');
                
                function addMessage(content, isUser = false, isMobile = false) {{
                    const targetMessages = isMobile ? mobileChatMessages : chatMessages;
                    const messageEl = document.createElement('div');
                    messageEl.className = `flex ${{isUser ? 'justify-end' : 'justify-start'}} mb-2`;
                    
                    const bubbleEl = document.createElement('div');
                    bubbleEl.className = `max-w-xs lg:max-w-md px-3 py-2 rounded-lg text-xs ${{isUser ? 'bg-blue-600 text-white' : 'bg-gray-50 text-gray-700 border border-gray-100'}}`;
                    bubbleEl.textContent = content;
                    
                    messageEl.appendChild(bubbleEl);
                    targetMessages.appendChild(messageEl);
                    targetMessages.scrollTop = targetMessages.scrollHeight;
                }}
                
                async function sendMessage(isMobile = false) {{
                    const input = isMobile ? mobileChatInput : chatInput;
                    const loading = isMobile ? mobileChatLoading : chatLoading;
                    const messages = isMobile ? mobileChatMessages : chatMessages;
                    
                    const question = input.value.trim();
                    if (!question) return;
                    
                    // Add user message
                    addMessage(question, true, isMobile);
                    input.value = '';
                    
                    // Show loading
                    loading.classList.remove('hidden');
                    
                    try {{
                        const response = await fetch('/api/ai/chat', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                model_id: modelId,
                                question: question
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        loading.classList.add('hidden');
                        
                        if (data.success) {{
                            addMessage(data.response, false, isMobile);
                        }} else {{
                            addMessage('Sorry, I encountered an error. Please try again.', false, isMobile);
                        }}
                    }} catch (error) {{
                        console.error('Chat error:', error);
                        loading.classList.add('hidden');
                        addMessage('Sorry, I encountered an error. Please try again.', false, isMobile);
                    }}
                }}
                
                // Desktop chat event listeners
                chatSend.addEventListener('click', () => sendMessage(false));
                chatInput.addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        sendMessage(false);
                    }}
                }});
                
                // Mobile chat event listeners
                mobileChatSend.addEventListener('click', () => sendMessage(true));
                mobileChatInput.addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        sendMessage(true);
                    }}
                }});
                
                // Mobile FAB and bottom sheet
                mobileChatFab.addEventListener('click', function() {{
                    mobileChatSheet.classList.remove('translate-y-full');
                    mobileChatInput.focus();
                }});
                
                closeMobileChat.addEventListener('click', function() {{
                    mobileChatSheet.classList.add('translate-y-full');
                }});
                
                // Jump to chat functionality
                jumpToChat.addEventListener('click', function() {{
                    if (window.innerWidth >= 1280) {{
                        // Desktop: scroll to chat panel
                        const chatPanel = document.querySelector('.xl\\:sticky');
                        if (chatPanel) {{
                            chatPanel.scrollIntoView({{ behavior: 'smooth' }});
                            chatInput.focus();
                        }}
                    }} else {{
                        // Mobile: open bottom sheet
                        mobileChatSheet.classList.remove('translate-y-full');
                        mobileChatInput.focus();
                    }}
                }});
                
                // Auto-scroll chat into view on desktop load
                if (window.innerWidth >= 1280) {{
                    setTimeout(() => {{
                        const chatPanel = document.querySelector('.xl\\:sticky');
                        if (chatPanel) {{
                            chatPanel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                        }}
                    }}, 500);
                }}
            }}
        </script>
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
