#!/usr/bin/env python3
"""
FinModAI Data Ingestion Engine
Handles automatic data pulling from financial databases and APIs.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import requests

logger = logging.getLogger('FinModAI.DataIngestion')

# Import available data sources
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available")

try:
    from alpha_vantage.fundamentaldata import FundamentalData
    from alpha_vantage.timeseries import TimeSeries
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False
    logger.warning("Alpha Vantage not available")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available")

@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit_per_minute: int = 60
    priority: int = 1
    enabled: bool = True

@dataclass
class FinancialData:
    """Standardized financial data structure."""
    company_name: str
    ticker: str
    corrected_ticker: Optional[str] = None  # For ticker corrections like APPL -> AAPL
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    shares_outstanding: float = 0.0
    beta: float = 1.2

    # Income Statement (most recent)
    revenue: float = 0.0
    ebitda: float = 0.0
    ebit: float = 0.0
    net_income: float = 0.0
    eps: float = 0.0

    # Balance Sheet
    total_assets: float = 0.0
    total_debt: float = 0.0
    cash_and_equivalents: float = 0.0
    total_equity: float = 0.0

    # Cash Flow
    operating_cash_flow: float = 0.0
    capex: float = 0.0
    free_cash_flow: float = 0.0

    # Growth Rates
    revenue_growth: float = 0.0
    ebitda_growth: float = 0.0
    eps_growth: float = 0.0

    # Metadata
    data_source: str = ""
    last_updated: str = ""
    data_quality_score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialData':
        """Create from dictionary."""
        return cls(**data)

class DataIngestionEngine:
    """Main data ingestion engine coordinating multiple data sources."""

    def __init__(self, config):
        self.config = config
        self.cache_dir = Path(config.data_cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize data sources
        self.data_sources = self._initialize_data_sources()

        # Rate limiting
        self.last_request_time = {}
        self.request_counts = {}

        logger.info("🔄 Data Ingestion Engine initialized")

    def _initialize_data_sources(self) -> Dict[str, DataSourceConfig]:
        """Initialize available data sources."""
        sources = {}

        # Free/Personal Use Sources (Highest Priority)
        # yfinance (free, no API key needed)
        if YFINANCE_AVAILABLE:
            sources['yfinance'] = DataSourceConfig(
                name='yfinance',
                priority=1,
                rate_limit_per_minute=2000
            )

        # Financial Modeling Prep (free tier available)
        fmp_key = os.getenv('FMP_API_KEY')
        if fmp_key:
            sources['financial_modeling_prep'] = DataSourceConfig(
                name='financial_modeling_prep',
                api_key=fmp_key,
                base_url='https://financialmodelingprep.com/api/v3',
                priority=2,
                rate_limit_per_minute=300
            )

        # IEX Cloud (free tier available)
        iex_key = os.getenv('IEX_API_KEY')
        if iex_key:
            sources['iex_cloud'] = DataSourceConfig(
                name='iex_cloud',
                api_key=iex_key,
                base_url='https://cloud.iexapis.com/stable',
                priority=3,
                rate_limit_per_minute=100000  # Very generous limits
            )

        # Professional/Enterprise Sources
        # Alpha Vantage
        alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if ALPHA_VANTAGE_AVAILABLE and alpha_key:
            sources['alpha_vantage'] = DataSourceConfig(
                name='alpha_vantage',
                api_key=alpha_key,
                priority=4,
                rate_limit_per_minute=5
            )

        # Polygon.io
        polygon_key = os.getenv('POLYGON_API_KEY')
        if polygon_key:
            sources['polygon'] = DataSourceConfig(
                name='polygon',
                api_key=polygon_key,
                base_url='https://api.polygon.io/v2',
                priority=5,
                rate_limit_per_minute=5000
            )

        # Twelve Data
        twelve_key = os.getenv('TWELVE_DATA_API_KEY')
        if twelve_key:
            sources['twelve_data'] = DataSourceConfig(
                name='twelve_data',
                api_key=twelve_key,
                base_url='https://api.twelvedata.com',
                priority=6,
                rate_limit_per_minute=800
            )

        # Intrinio
        intrinio_key = os.getenv('INTRINIO_API_KEY')
        if intrinio_key:
            sources['intrinio'] = DataSourceConfig(
                name='intrinio',
                api_key=intrinio_key,
                base_url='https://api-v2.intrinio.com',
                priority=7,
                rate_limit_per_minute=1000
            )

        # Quandl (Nasdaq Data Link)
        quandl_key = os.getenv('QUANDL_API_KEY')
        if quandl_key:
            sources['quandl'] = DataSourceConfig(
                name='quandl',
                api_key=quandl_key,
                base_url='https://www.quandl.com/api/v3',
                priority=8,
                rate_limit_per_minute=2000
            )

        # Institutional/Enterprise Sources
        # Bloomberg Terminal
        bloomberg_key = os.getenv('BLOOMBERG_API_KEY')
        if bloomberg_key:
            sources['bloomberg'] = DataSourceConfig(
                name='bloomberg',
                api_key=bloomberg_key,
                priority=9,
                rate_limit_per_minute=100
            )

        # CapIQ
        capiq_key = os.getenv('CAPIQ_API_KEY')
        if capiq_key:
            sources['capiq'] = DataSourceConfig(
                name='capiq',
                api_key=capiq_key,
                priority=10,
                rate_limit_per_minute=50
            )

        # PitchBook
        pitchbook_key = os.getenv('PITCHBOOK_API_KEY')
        if pitchbook_key:
            sources['pitchbook'] = DataSourceConfig(
                name='pitchbook',
                api_key=pitchbook_key,
                priority=11,
                rate_limit_per_minute=30
            )

        # Refinitiv (Thomson Reuters)
        refinitiv_key = os.getenv('REFINITIV_API_KEY')
        if refinitiv_key:
            sources['refinitiv'] = DataSourceConfig(
                name='refinitiv',
                api_key=refinitiv_key,
                priority=12,
                rate_limit_per_minute=100
            )

        # FactSet
        factset_key = os.getenv('FACTSET_API_KEY')
        if factset_key:
            sources['factset'] = DataSourceConfig(
                name='factset',
                api_key=factset_key,
                priority=13,
                rate_limit_per_minute=200
            )

        # SEC EDGAR
        sources['sec_edgar'] = DataSourceConfig(
            name='sec_edgar',
            base_url='https://www.sec.gov/edgar',
            priority=14,
            rate_limit_per_minute=10  # Respect SEC limits
        )

        logger.info(f"📊 Initialized {len(sources)} data sources")
        return sources

    def get_company_data(self, company_identifier: str) -> Optional[FinancialData]:
        """
        Get comprehensive financial data for a company.

        Args:
            company_identifier: Company ticker, name, or CIK

        Returns:
            FinancialData object or None if not found
        """

        logger.info(f"🔍 Fetching data for: {company_identifier}")
        # Always pull fresh data from multiple sources
        logger.info("🔄 Pulling fresh data from multiple financial sources...")

        # Try each data source in priority order
        for source_name in sorted(self.data_sources.keys(),
                                key=lambda x: self.data_sources[x].priority):

            if not self.data_sources[source_name].enabled:
                continue

            logger.debug(f"🔍 Trying {source_name}...")
            try:
                data = self._fetch_from_source(source_name, company_identifier)
                if data:
                    # Check if the data is complete (has essential fields like market_cap)
                    if data.market_cap is not None and data.market_cap > 0:
                        logger.info(f"✅ Complete data retrieved from {source_name}")
                        return data
                    else:
                        logger.debug(f"⚠️ Incomplete data from {source_name}, trying other sources...")
                        continue

            except Exception as e:
                logger.warning(f"❌ {source_name} failed: {e}")
                continue

        # Suggest common ticker corrections and try corrected version
        suggestions = {
            'APPL': 'AAPL',
            'GOOGL': 'GOOGL',
            'AMZN': 'AMZN',
            'TSLA': 'TSLA',
            'META': 'META',
            'NVDA': 'NVDA',
            'MSFT': 'MSFT',
            'NFLX': 'NFLX'
        }

        suggestion = suggestions.get(company_identifier.upper(), "")
        if suggestion:
            logger.info(f"🔄 Correcting ticker '{company_identifier}' to '{suggestion}' and retrying...")
            corrected_data = self.get_company_data(suggestion)
            if corrected_data:
                logger.info(f"✅ Successfully retrieved data using corrected ticker '{suggestion}'")
                # Set the corrected ticker info
                corrected_data.corrected_ticker = suggestion
                return corrected_data
            else:
                logger.error(f"❌ No data found for {company_identifier} (tried correction to {suggestion}). Please check the ticker symbol.")
        else:
            logger.error(f"❌ No data found for {company_identifier}. Please check the ticker symbol.")
        return None

    def _fetch_from_source(self, source_name: str, identifier: str) -> Optional[FinancialData]:
        """Fetch data from specific source."""
        self._rate_limit_check(source_name)

        if source_name == 'yfinance':
            return self._fetch_yfinance_data(identifier)
        elif source_name == 'financial_modeling_prep':
            return self._fetch_fmp_data(identifier)
        elif source_name == 'iex_cloud':
            return self._fetch_iex_data(identifier)
        elif source_name == 'polygon':
            return self._fetch_polygon_data(identifier)
        elif source_name == 'twelve_data':
            return self._fetch_twelve_data(identifier)
        elif source_name == 'intrinio':
            return self._fetch_intrinio_data(identifier)
        elif source_name == 'quandl':
            return self._fetch_quandl_data(identifier)
        elif source_name == 'alpha_vantage':
            return self._fetch_alpha_vantage_data(identifier)
        elif source_name == 'bloomberg':
            return self._fetch_bloomberg_data(identifier)
        elif source_name == 'capiq':
            return self._fetch_capiq_data(identifier)
        elif source_name == 'pitchbook':
            return self._fetch_pitchbook_data(identifier)
        elif source_name == 'refinitiv':
            return self._fetch_refinitiv_data(identifier)
        elif source_name == 'factset':
            return self._fetch_factset_data(identifier)
        elif source_name == 'sec_edgar':
            return self._fetch_sec_edgar_data(identifier)

        return None

    def _fetch_fmp_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Financial Modeling Prep."""
        try:
            config = self.data_sources['financial_modeling_prep']
            base_url = config.base_url
            api_key = config.api_key

            # Get company profile
            profile_url = f"{base_url}/profile/{identifier}?apikey={api_key}"
            profile_response = requests.get(profile_url)

            if profile_response.status_code != 200:
                return None

            profile_data = profile_response.json()
            if not profile_data:
                return None

            company = profile_data[0]

            # Get income statement
            income_url = f"{base_url}/income-statement/{identifier}?period=annual&apikey={api_key}"
            income_response = requests.get(income_url)

            if income_response.status_code != 200:
                return None

            income_data = income_response.json()
            if not income_data:
                return None

            latest_income = income_data[0]

            data = FinancialData(
                company_name=company.get('companyName', identifier),
                ticker=identifier,
                sector=company.get('sector', ''),
                industry=company.get('industry', ''),
                market_cap=company.get('mktCap', 0),
                shares_outstanding=company.get('outstandingShares', 0) if company.get('outstandingShares') else 0,
                beta=company.get('beta', 1.2),
                data_source='financial_modeling_prep',
                last_updated=datetime.now().isoformat(),
                data_quality_score=90
            )

            # Extract financials
            data.revenue = latest_income.get('revenue', 0)
            data.ebitda = latest_income.get('ebitda', 0)
            data.net_income = latest_income.get('netIncome', 0)

            # Calculate growth rates if we have multiple years
            if len(income_data) >= 2:
                current_rev = income_data[0].get('revenue', 0)
                prev_rev = income_data[1].get('revenue', 0)
                if prev_rev > 0:
                    data.revenue_growth = ((current_rev / prev_rev) - 1) * 100

            return data

        except Exception as e:
            logger.error(f"Financial Modeling Prep error: {e}")
            return None

    def _fetch_iex_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from IEX Cloud."""
        try:
            config = self.data_sources['iex_cloud']
            base_url = config.base_url
            api_key = config.api_key

            # Get company info
            company_url = f"{base_url}/stock/{identifier}/company?token={api_key}"
            company_response = requests.get(company_url)

            if company_response.status_code != 200:
                return None

            company_data = company_response.json()

            # Get financials
            stats_url = f"{base_url}/stock/{identifier}/stats?token={api_key}"
            stats_response = requests.get(stats_url)

            if stats_response.status_code != 200:
                return None

            stats_data = stats_response.json()

            data = FinancialData(
                company_name=company_data.get('companyName', identifier),
                ticker=identifier,
                sector=company_data.get('sector', ''),
                industry=company_data.get('industry', ''),
                market_cap=stats_data.get('marketcap', 0),
                shares_outstanding=stats_data.get('outstandingShares', 0) if stats_data.get('outstandingShares') else 0,
                beta=stats_data.get('beta', 1.2),
                data_source='iex_cloud',
                last_updated=datetime.now().isoformat(),
                data_quality_score=95
            )

            # Get income statement data
            income_url = f"{base_url}/stock/{identifier}/income?period=annual&token={api_key}"
            income_response = requests.get(income_url)

            if income_response.status_code == 200:
                income_data = income_response.json()
                if income_data.get('income'):
                    latest_income = income_data['income'][0]
                    data.revenue = latest_income.get('totalRevenue', 0)
                    data.net_income = latest_income.get('netIncome', 0)

            return data

        except Exception as e:
            logger.error(f"IEX Cloud error: {e}")
            return None

    def _fetch_polygon_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Polygon.io."""
        try:
            config = self.data_sources['polygon']
            base_url = config.base_url
            api_key = config.api_key

            # Get company details
            details_url = f"{base_url}/reference/tickers/{identifier}?apikey={api_key}"
            details_response = requests.get(details_url)

            if details_response.status_code != 200:
                return None

            details_data = details_response.json().get('results', {})

            # Get financials
            financials_url = f"{base_url}/reference/financials/{identifier}?limit=1&apikey={api_key}"
            financials_response = requests.get(financials_url)

            if financials_response.status_code != 200:
                return None

            financials_data = financials_response.json().get('results', [])
            if not financials_data:
                return None

            latest_financials = financials_data[0]

            data = FinancialData(
                company_name=details_data.get('name', identifier),
                ticker=identifier,
                sector=details_data.get('sic_description', ''),
                industry=details_data.get('industry', ''),
                market_cap=details_data.get('market_cap', 0),
                shares_outstanding=details_data.get('weighted_shares_outstanding', 0),
                beta=1.2,  # Polygon doesn't provide beta directly
                data_source='polygon',
                last_updated=datetime.now().isoformat(),
                data_quality_score=85
            )

            # Extract financials
            data.revenue = latest_financials.get('revenues', 0)
            data.ebitda = latest_financials.get('earnings_before_interest_taxes_depreciation_amortization', 0)
            data.net_income = latest_financials.get('net_income_loss', 0)

            return data

        except Exception as e:
            logger.error(f"Polygon.io error: {e}")
            return None

    def _fetch_twelve_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Twelve Data."""
        try:
            config = self.data_sources['twelve_data']
            base_url = config.base_url
            api_key = config.api_key

            # Get company profile
            profile_url = f"{base_url}/profile?symbol={identifier}&apikey={api_key}"
            profile_response = requests.get(profile_url)

            if profile_response.status_code != 200:
                return None

            profile_data = profile_response.json()
            if not profile_data:
                return None

            # Get fundamentals
            fundamentals_url = f"{base_url}/fundamentals?symbol={identifier}&apikey={api_key}"
            fundamentals_response = requests.get(fundamentals_url)

            data = FinancialData(
                company_name=profile_data.get('name', identifier),
                ticker=identifier,
                sector=profile_data.get('sector', ''),
                industry=profile_data.get('industry', ''),
                market_cap=profile_data.get('market_capitalization', 0),
                shares_outstanding=0,  # Twelve Data may not provide this
                beta=1.2,  # May be available in fundamentals
                data_source='twelve_data',
                last_updated=datetime.now().isoformat(),
                data_quality_score=80
            )

            if fundamentals_response.status_code == 200:
                fundamentals_data = fundamentals_response.json()
                if fundamentals_data:
                    # Extract financials from fundamentals (structure may vary)
                    pass  # Implementation depends on API response structure

            return data

        except Exception as e:
            logger.error(f"Twelve Data error: {e}")
            return None

    def _fetch_intrinio_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Intrinio."""
        try:
            config = self.data_sources['intrinio']
            base_url = config.base_url
            api_key = config.api_key

            # Get company info
            company_url = f"{base_url}/companies?identifier={identifier}&api_key={api_key}"
            company_response = requests.get(company_url)

            if company_response.status_code != 200:
                return None

            company_data = company_response.json()
            if not company_data.get('companies'):
                return None

            company = company_data['companies'][0]

            data = FinancialData(
                company_name=company.get('name', identifier),
                ticker=identifier,
                sector=company.get('sector', ''),
                industry=company.get('industry', ''),
                market_cap=0,  # May need separate call
                shares_outstanding=0,
                beta=1.2,
                data_source='intrinio',
                last_updated=datetime.now().isoformat(),
                data_quality_score=95
            )

            # Get financial data (simplified - would need more specific endpoints)
            # This is a placeholder for the full implementation

            return data

        except Exception as e:
            logger.error(f"Intrinio error: {e}")
            return None

    def _fetch_quandl_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Quandl/Nasdaq Data Link."""
        try:
            config = self.data_sources['quandl']
            base_url = config.base_url
            api_key = config.api_key

            # This is a simplified implementation
            # Quandl has many datasets, would need specific dataset codes

            data = FinancialData(
                company_name=identifier,  # Would need to look up proper name
                ticker=identifier,
                sector='',
                industry='',
                market_cap=0,
                shares_outstanding=0,
                beta=1.2,
                data_source='quandl',
                last_updated=datetime.now().isoformat(),
                data_quality_score=75
            )

            # Implementation would depend on specific Quandl datasets
            # Many financial datasets are available (SF0, SF1, etc.)

            return data

        except Exception as e:
            logger.error(f"Quandl error: {e}")
            return None

    def _fetch_yfinance_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(identifier)
            info = ticker.info

            if not info or info.get('regularMarketPrice') is None:
                return None

            # Check if we have basic financial data
            if not info.get('marketCap') or info.get('marketCap') <= 0:
                return None

            # Get financial statements
            income_stmt = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow

            data = FinancialData(
                company_name=info.get('longName', identifier),
                ticker=identifier,
                sector=info.get('sector', ''),
                industry=info.get('industry', ''),
                market_cap=info.get('marketCap', 0),
                shares_outstanding=info.get('sharesOutstanding', 0),
                beta=info.get('beta', 1.2),
                data_source='yfinance',
                last_updated=datetime.now().isoformat(),
                data_quality_score=85
            )

            # Extract most recent financials
            if not income_stmt.empty:
                print(f"📊 DEBUG: Income statement rows: {list(income_stmt.index)}")
                print(f"📊 DEBUG: Income statement shape: {income_stmt.shape}")

                # Try multiple possible revenue labels
                revenue_labels = ['Total Revenue', 'Revenue', 'TotalRevenue', 'totalRevenue']
                for label in revenue_labels:
                    if label in income_stmt.index:
                        raw_revenue = income_stmt.loc[label].iloc[0]
                        print(f"🔍 DEBUG: Raw revenue value for {label}: {raw_revenue} (type: {type(raw_revenue)})")
                        data.revenue = float(raw_revenue) / 1_000_000_000 if pd.notna(raw_revenue) else 0
                        print(f"✅ Found revenue: {label} = ${data.revenue:.1f}B")
                        break
                else:
                    print("❌ No revenue found in income statement")
                    data.revenue = 0

                # Try multiple possible net income labels
                ni_labels = ['Net Income', 'NetIncome', 'netIncome', 'Net Income Applicable To Common Shares']
                for label in ni_labels:
                    if label in income_stmt.index:
                        raw_ni = income_stmt.loc[label].iloc[0]
                        print(f"🔍 DEBUG: Raw net income value for {label}: {raw_ni} (type: {type(raw_ni)})")
                        data.net_income = float(raw_ni) / 1_000_000_000 if pd.notna(raw_ni) else 0
                        print(f"✅ Found net income: {label} = ${data.net_income:.1f}B")
                        break
                else:
                    print("❌ No net income found in income statement")
                    data.net_income = 0

                # Calculate EBITDA
                if 'EBITDA' in income_stmt.index:
                    data.ebitda = income_stmt.loc['EBITDA'].iloc[0] / 1_000_000_000
                elif 'Operating Income' in income_stmt.index:
                    op_income = income_stmt.loc['Operating Income'].iloc[0]
                    dep = cash_flow.loc['Depreciation'].iloc[0] if not cash_flow.empty and 'Depreciation' in cash_flow.index else 0
                    data.ebitda = (op_income + dep) / 1_000_000_000

            if not balance_sheet.empty:
                data.total_assets = balance_sheet.loc['Total Assets'].iloc[0] / 1_000_000_000 if 'Total Assets' in balance_sheet.index else 0
                data.total_debt = balance_sheet.loc['Total Debt'].iloc[0] / 1_000_000_000 if 'Total Debt' in balance_sheet.index else 0
                data.cash_and_equivalents = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] / 1_000_000_000 if 'Cash And Cash Equivalents' in balance_sheet.index else 0
                data.total_equity = balance_sheet.loc['Total Stockholder Equity'].iloc[0] / 1_000_000_000 if 'Total Stockholder Equity' in balance_sheet.index else 0

            if not cash_flow.empty:
                data.operating_cash_flow = cash_flow.loc['Operating Cash Flow'].iloc[0] / 1_000_000_000 if 'Operating Cash Flow' in cash_flow.index else 0
                data.capex = abs(cash_flow.loc['Capital Expenditures'].iloc[0] / 1_000_000_000) if 'Capital Expenditures' in cash_flow.index else 0

            # Calculate growth rates
            if len(income_stmt.columns) >= 2 and not income_stmt.empty:
                rev_series = income_stmt.loc['Total Revenue'] if 'Total Revenue' in income_stmt.index else None
                if rev_series is not None and len(rev_series) >= 2:
                    try:
                        current_rev = float(rev_series.iloc[0])
                        previous_rev = float(rev_series.iloc[1])
                        if previous_rev > 0 and not pd.isna(current_rev) and not pd.isna(previous_rev):
                            data.revenue_growth = (current_rev / previous_rev - 1) * 100
                            print(f"📈 DEBUG: Calculated revenue growth: {data.revenue_growth:.2f}% (Current: ${current_rev/1_000_000_000:.1f}B, Previous: ${previous_rev/1_000_000_000:.1f}B)")
                            print(f"📊 DEBUG: Setting data.revenue_growth = {data.revenue_growth}")
                        else:
                            print(f"⚠️ DEBUG: Invalid revenue data for growth calculation")
                            data.revenue_growth = 0
                    except Exception as e:
                        print(f"⚠️ DEBUG: Error calculating revenue growth: {e}")
                        data.revenue_growth = 0
                else:
                    print(f"⚠️ DEBUG: Insufficient revenue data for growth calculation (columns: {len(rev_series) if rev_series is not None else 0})")
                    data.revenue_growth = 0

            return data

        except Exception as e:
            logger.error(f"yfinance error: {e}")
            return None

    def _fetch_alpha_vantage_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Alpha Vantage."""
        try:
            config = self.data_sources['alpha_vantage']
            fd = FundamentalData(key=config.api_key)

            # Get company overview
            overview, _ = fd.get_company_overview(symbol=identifier)
            if overview.empty:
                return None

            # Get income statement
            income, _ = fd.get_income_statement_annual(symbol=identifier)
            if income.empty:
                return None

            data = FinancialData(
                company_name=overview.loc[0, 'Name'],
                ticker=identifier,
                sector=overview.loc[0, 'Sector'],
                industry=overview.loc[0, 'Industry'],
                market_cap=float(overview.loc[0, 'MarketCapitalization']),
                shares_outstanding=float(overview.loc[0, 'SharesOutstanding']),
                beta=float(overview.loc[0, 'Beta']) if overview.loc[0, 'Beta'] != 'None' else 1.2,
                data_source='alpha_vantage',
                last_updated=datetime.now().isoformat(),
                data_quality_score=95
            )

            # Extract financials
            latest_income = income.iloc[0]

            data.revenue = float(latest_income['totalRevenue']) / 1_000_000
            data.net_income = float(latest_income['netIncome']) / 1_000_000
            data.ebitda = float(latest_income['ebitda']) / 1_000_000 if 'ebitda' in latest_income else 0

            return data

        except Exception as e:
            logger.error(f"Alpha Vantage error: {e}")
            return None

    def _fetch_bloomberg_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Bloomberg Terminal."""
        try:
            config = self.data_sources['bloomberg']
            api_key = config.api_key

            # Bloomberg API integration would go here
            # This is a placeholder for the actual Bloomberg OpenFIGI/BLPAPI implementation

            logger.info("Bloomberg Terminal integration requires Bloomberg subscription and API setup")
            return None

        except Exception as e:
            logger.error(f"Bloomberg error: {e}")
            return None

    def _fetch_capiq_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from CapIQ (S&P Capital IQ)."""
        try:
            config = self.data_sources['capiq']
            api_key = config.api_key

            # CapIQ API integration would go here
            # This is a placeholder for the actual CapIQ API implementation

            logger.info("CapIQ integration requires S&P Capital IQ subscription")
            return None

        except Exception as e:
            logger.error(f"CapIQ error: {e}")
            return None

    def _fetch_pitchbook_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from PitchBook."""
        try:
            config = self.data_sources['pitchbook']
            api_key = config.api_key

            # PitchBook API integration would go here
            # This is a placeholder for the actual PitchBook API implementation

            logger.info("PitchBook integration requires PitchBook subscription")
            return None

        except Exception as e:
            logger.error(f"PitchBook error: {e}")
            return None

    def _fetch_refinitiv_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from Refinitiv (Thomson Reuters)."""
        try:
            config = self.data_sources['refinitiv']
            api_key = config.api_key

            # Refinitiv API integration would go here
            # This is a placeholder for the actual Refinitiv API implementation

            logger.info("Refinitiv integration requires Thomson Reuters subscription")
            return None

        except Exception as e:
            logger.error(f"Refinitiv error: {e}")
            return None

    def _fetch_factset_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from FactSet."""
        try:
            config = self.data_sources['factset']
            api_key = config.api_key

            # FactSet API integration would go here
            # This is a placeholder for the actual FactSet API implementation

            logger.info("FactSet integration requires FactSet subscription")
            return None

        except Exception as e:
            logger.error(f"FactSet error: {e}")
            return None

    def _fetch_sec_edgar_data(self, identifier: str) -> Optional[FinancialData]:
        """Fetch data from SEC EDGAR filings."""
        try:
            # SEC EDGAR is publicly available but requires parsing XBRL/HTML filings
            # This is a simplified implementation

            # First, get the CIK (Central Index Key) for the company
            cik = self._get_cik_from_ticker(identifier)
            if not cik:
                return None

            data = FinancialData(
                company_name=identifier,  # Would need to look up proper name
                ticker=identifier,
                sector='',
                industry='',
                market_cap=0,
                shares_outstanding=0,
                beta=1.2,
                data_source='sec_edgar',
                last_updated=datetime.now().isoformat(),
                data_quality_score=70  # Lower quality due to parsing complexity
            )

            # SEC EDGAR parsing is complex and would require:
            # 1. Finding the latest 10-K filing
            # 2. Parsing XBRL or HTML financial statements
            # 3. Extracting relevant financial metrics
            # This is beyond the scope of this demo but could be implemented

            logger.info("SEC EDGAR parsing requires complex XBRL/HTML parsing - simplified implementation")
            return data

        except Exception as e:
            logger.error(f"SEC EDGAR error: {e}")
            return None

    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK from ticker symbol (simplified implementation)."""
        try:
            # This would normally query the SEC's CIK lookup service
            # For demo purposes, return a placeholder
            cik_map = {
                'AAPL': '0000320193',
                'MSFT': '0000789019',
                'GOOGL': '0001652044',
                'AMZN': '0001018724',
                'TSLA': '0001318605'
            }
            return cik_map.get(ticker.upper())
        except Exception as e:
            logger.error(f"CIK lookup error: {e}")
            return None

    def _rate_limit_check(self, source_name: str):
        """Implement rate limiting for API calls."""
        now = datetime.now()
        config = self.data_sources[source_name]

        if source_name not in self.last_request_time:
            self.last_request_time[source_name] = now
            self.request_counts[source_name] = 1
            return

        # Calculate time since last request
        time_diff = (now - self.last_request_time[source_name]).total_seconds()

        # Reset counter if minute has passed
        if time_diff >= 60:
            self.request_counts[source_name] = 1
            self.last_request_time[source_name] = now
            return

        # Check rate limit
        if self.request_counts[source_name] >= config.rate_limit_per_minute:
            sleep_time = 60 - time_diff
            logger.info(f"   ⏳ Rate limit reached, sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
            self.request_counts[source_name] = 1
            self.last_request_time[source_name] = datetime.now()
        else:
            self.request_counts[source_name] += 1

    def _get_cached_data(self, identifier: str) -> Optional[FinancialData]:
        """Get cached data if available and fresh."""
        # DISABLE CACHING - Always return None to force fresh data pulling
        logger.debug(f"💨 Skipping cache for {identifier} - pulling fresh data")
        return None

    def _cache_data(self, identifier: str, data: FinancialData):
        """Cache financial data."""
        # DISABLE CACHING - Do nothing to force fresh data pulling
        logger.debug(f"💨 Skipping cache write for {identifier} - using fresh data only")
        pass

    def upload_financial_data(self, file_path: str, company_name: str) -> Optional[FinancialData]:
        """Upload and parse financial data from Excel/CSV files."""
        logger.info(f"📁 Processing uploaded file: {file_path}")

        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.xlsx':
                df = pd.read_excel(file_path)
            elif file_ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            # Parse uploaded data (this would need customization based on file format)
            data = FinancialData(
                company_name=company_name,
                ticker="UPLOADED",
                data_source='manual_upload',
                last_updated=datetime.now().isoformat(),
                data_quality_score=100
            )

            # Extract data from DataFrame (simplified)
            if 'revenue' in df.columns:
                data.revenue = df['revenue'].iloc[-1] / 1_000_000

            logger.info("✅ Uploaded data processed successfully")
            return data

        except Exception as e:
            logger.error(f"Upload processing error: {e}")
            return None

    def get_available_sources(self) -> List[str]:
        """Get list of available and enabled data sources."""
        return [name for name, config in self.data_sources.items() if config.enabled]

    def enable_source(self, source_name: str, enabled: bool = True):
        """Enable or disable a data source."""
        if source_name in self.data_sources:
            self.data_sources[source_name].enabled = enabled
            logger.info(f"{'Enabled' if enabled else 'Disabled'} data source: {source_name}")

    def get_data_quality_metrics(self, data: FinancialData) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        metrics = {
            'completeness_score': 0,
            'freshness_score': 0,
            'consistency_score': 0,
            'overall_quality': data.data_quality_score
        }

        # Calculate completeness
        fields = ['revenue', 'ebitda', 'net_income', 'total_assets', 'total_debt']
        filled_fields = sum(1 for field in fields if getattr(data, field, 0) != 0)
        metrics['completeness_score'] = (filled_fields / len(fields)) * 100

        return metrics
