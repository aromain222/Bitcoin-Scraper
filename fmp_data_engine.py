"""
Financial Modeling Prep (FMP) Data Engine
Fetches real historical financial data and computes company-specific assumptions
"""

import requests
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import time
import math

class FMPDataEngine:
    """Data engine using Financial Modeling Prep APIs"""
    
    def __init__(self):
        """Initialize FMP data engine"""
        self.api_key = os.getenv('FMP_API_KEY')
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request to FMP"""
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable not set")
        
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"FMP API request failed: {e}")
            return None
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func) -> Optional[Any]:
        """Get data from cache or fetch if expired"""
        now = time.time()
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if now - timestamp < self.cache_duration:
                return data
        
        # Cache miss or expired, fetch new data
        data = fetch_func()
        if data is not None:
            self.cache[cache_key] = (data, now)
        return data
    
    def get_income_statements(self, ticker: str, limit: int = 5) -> Optional[List[Dict]]:
        """Get income statements for the last N years"""
        def fetch():
            endpoint = f"/income-statement/{ticker}"
            return self._make_request(endpoint, {'limit': limit})
        
        cache_key = f"income_stmt_{ticker}_{limit}"
        return self._get_cached_or_fetch(cache_key, fetch)
    
    def get_cash_flow_statements(self, ticker: str, limit: int = 5) -> Optional[List[Dict]]:
        """Get cash flow statements for the last N years"""
        def fetch():
            endpoint = f"/cash-flow-statement/{ticker}"
            return self._make_request(endpoint, {'limit': limit})
        
        cache_key = f"cash_flow_{ticker}_{limit}"
        return self._get_cached_or_fetch(cache_key, fetch)
    
    def get_ratios_ttm(self, ticker: str) -> Optional[Dict]:
        """Get TTM ratios"""
        def fetch():
            endpoint = f"/ratios-ttm/{ticker}"
            return self._make_request(endpoint)
        
        cache_key = f"ratios_ttm_{ticker}"
        return self._get_cached_or_fetch(cache_key, fetch)
    
    def get_key_metrics(self, ticker: str, limit: int = 5) -> Optional[List[Dict]]:
        """Get key metrics for the last N years"""
        def fetch():
            endpoint = f"/key-metrics/{ticker}"
            return self._make_request(endpoint, {'limit': limit})
        
        cache_key = f"key_metrics_{ticker}_{limit}"
        return self._get_cached_or_fetch(cache_key, fetch)
    
    def get_company_profile(self, ticker: str) -> Optional[Dict]:
        """Get company profile"""
        def fetch():
            endpoint = f"/profile/{ticker}"
            return self._make_request(endpoint)
        
        cache_key = f"profile_{ticker}"
        return self._get_cached_or_fetch(cache_key, fetch)
    
    def extract_historical_data(self, ticker: str) -> Dict[str, Any]:
        """Extract all historical financial data"""
        result = {
            'ticker': ticker,
            'income_statements': [],
            'cash_flows': [],
            'ratios_ttm': {},
            'key_metrics': [],
            'company_profile': {},
            'errors': [],
            'data_provenance': {}
        }
        
        # Get income statements
        income_data = self.get_income_statements(ticker, 5)
        if income_data and len(income_data) >= 3:
            result['income_statements'] = income_data
            result['data_provenance']['income_statements'] = 'FMP'
        else:
            result['errors'].append('Insufficient income statement data (< 3 years)')
        
      # Get cash flow statements
        cash_flow_data = self.get_cash_flow_statements(ticker, 5)
        if cash_flow_data:
            result['cash_flows'] = cash_flow_data
            result['data_provenance']['cash_flows'] = 'FMP'
        
        # Get TTM ratios
        ratios_data = self.get_ratios_ttm(ticker)
        if ratios_data:
            result['ratios_ttm'] = ratios_data
            result['data_provenance']['ratios_ttm'] = 'FMP'
        
        # Get key metrics
        metrics_data = self.get_key_metrics(ticker, 5)
        if metrics_data:
            result['key_metrics'] = metrics_data
            result['data_provenance']['key_metrics'] = 'FMP'
        
        # Get company profile
        profile_data = self.get_company_profile(ticker)
        if profile_data:
            result['company_profile'] = profile_data
            result['data_provenance']['company_profile'] = 'FMP'
        
        return result
    
    def calculate_revenue_growth(self, income_statements: List[Dict]) -> List[float]:
        """Calculate revenue growth rates from historical data"""
        if not income_statements or len(income_statements) < 2:
            return []
        
        # Extract revenue (most recent first)
        revenues = [stmt.get('revenue', 0) for stmt in income_statements if stmt.get('revenue')]
        
        if len(revenues) < 2:
            return []
        
        growth_rates = []
        for i in range(len(revenues) - 1):
            prev_revenue = revenues[i + 1]
            curr_revenue = revenues[i]
            if prev_revenue > 0:
                growth = (curr_revenue - prev_revenue) / prev_revenue
                growth_rates.append(growth)
        
        return growth_rates
    
    def calculate_cagr(self, values: List[float], years: int = 3) -> Optional[float]:
        """Calculate CAGR from historical values"""
        if not values or len(values) < 2:
            return None
        
        years = min(years, len(values))
        if years < 2:
            return None
        
        start_value = values[-1]  # Older value
        end_value = values[0]     # Most recent value
        
        if start_value <= 0:
            return None
        
        cagr = (end_value / start_value) ** (1 / years) - 1
        return cagr
    
    def calculate_operating_margins(self, income_statements: List[Dict]) -> List[float]:
        """Calculate operating margins from historical data"""
        if not income_statements:
            return []
        
        margins = []
        for stmt in income_statements:
            revenue = stmt.get('revenue', 0)
            operating_income = stmt.get('operatingIncome', 0)
            
            if revenue > 0:
                margin = operating_income / revenue
                margins.append(margin)
        
        return margins
    
    def calculate_average_ratio(self, values: List[float], years: int = 3) -> Optional[float]:
        """Calculate average ratio over specified years"""
        if not values or len(values) == 0:
            return None
        
        years = min(years, len(values))
        return sum(values[:years]) / years
    
    def calculate_effective_tax_rate(self, income_statements: List[Dict]) -> List[float]:
        """Calculate effective tax rates from historical data"""
        if not income_statements:
            return []
        
        tax_rates = []
        for stmt in income_statements:
            income_before_tax = stmt.get('incomeBeforeTax', 0)
            income_tax_expense = stmt.get('incomeTaxExpense', 0)
            
            if income_before_tax > 0:
                tax_rate = income_tax_expense / income_before_tax
                tax_rates.append(tax_rate)
        
        return tax_rates
    
    def calculate_capex_percentages(self, cash_flows: List[Dict], revenues: List[float]) -> List[float]:
        """Calculate CapEx as percentage of revenue"""
        if not cash_flows or not revenues:
            return []
        
        capex_percentages = []
        min_len = min(len(cash_flows), len(revenues))
        
        for i in range(min_len):
            capex = cash_flows[i].get('capitalExpenditure', 0)
            revenue = revenues[i]
            
            if revenue > 0:
                capex_percentages.append(capex / revenue)
        
        return capex_percentages
    
    def calculate_nwc_percentages(self, cash_flows: List[Dict], revenue_changes: List[float]) -> List[float]:
        """Calculate ΔNWC as percentage of revenue change"""
        if not cash_flows or not revenue_changes:
            return []
        
        nwc_percentages = []
        min_len = min(len(cash_flows), len(revenue_changes))
        
        for i in range(min_len):
            nwc_change = cash_flows[i].get('changeInWorkingCapital', 0)
            revenue_change = revenue_changes[i]
            
            if revenue_change != 0:
                nwc_percentages.append(nwc_change / revenue_change)
        
        return nwc_percentages
    
    def calculate_da_percentages(self, income_statements: List[Dict], revenues: List[float]) -> List[float]:
        """Calculate D&A as percentage of revenue"""
        if not income_statements or not revenues:
            return []
        
        da_percentages = []
        min_len = min(len(income_statements), len(revenues))
        
        for i in range(min_len):
            da = income_statements[i].get('depreciationAndAmortization', 0)
            revenue = revenues[i]
            
            if revenue > 0:
                da_percentages.append(da / revenue)
        
        return da_percentages
    
    def build_assumptions_from_data(self, ticker: str) -> Dict[str, Any]:
        """Build complete assumptions from FMP data"""
        # Extract all historical data
        historical_data = self.extract_historical_data(ticker)
        
        result = {
            'ticker': ticker,
            'company_name': historical_data['company_profile'].get('companyName', ticker),
            'data_source': 'FMP',
            'assumptions': {},
            'historicals': {},
            'provenance': historical_data['data_provenance'],
            'errors': historical_data['errors'],
            'historical_data': historical_data
        }
        
        # Check if we have sufficient data
        income_statements = historical_data['income_statements']
        cash_flows = historical_data['cash_flows']
        
        if len(income_statements) < 3:
            result['error'] = 'INSUFFICIENT_HISTORICAL_DATA'
            result['message'] = 'Need ≥3 years of income statement data to build assumptions'
            return result
        
        # Calculate historical metrics
        revenues = [stmt['revenue'] for stmt in income_statements if stmt.get('revenue', 0) > 0]
        revenue_growth_rates = self.calculate_revenue_growth(income_statements)
        operating_margins = self.calculate_operating_margins(income_statements)
        tax_rates = self.calculate_effective_tax_rate(income_statements)
        
        # Calculate CAGR
        revenue_cagr = self.calculate_cagr(revenues, min(3, len(revenues)))
        avg_margin = self.calculate_average_ratio(operating_margins, 3)
        avg_tax_rate = self.calculate_average_ratio(tax_rates, 3)
        
        # Calculate additional ratios from cash flows
        capex_percentages = self.calculate_capex_percentages(cash_flows, revenues)
        avg_capex_percent = self.calculate_average_ratio(capex_percentages, 3) if capex_percentages else 0.06
        
        da_percentages = self.calculate_da_percentages(income_statements, revenues)
        avg_da_percent = self.calculate_average_ratio(da_percentages, 3) if da_percentages else 0.04
        
        # Calculate revenue change for NWC
        revenue_changes = []
        for i in range(len(revenues) - 1):
            change = revenues[i] - revenues[i + 1]
            revenue_changes.append(change)
        
        nwc_percentages = self.calculate_nwc_percentages(cash_flows, revenue_changes)
        avg_nwc_percent = self.calculate_average_ratio(nwc_percentages, 3) if nwc_percentages else 0.03
        
        # Build forecast assumptions
        forecast_years = 5
        
        # Revenue growth path (fade from CAGR to long-term growth)
        revenue_growth_path = []
        if revenue_cagr:
            terminal_growth = min(0.025, max(0.02, revenue_cagr * 0.3))  # Conservative terminal growth
            for year in range(forecast_years):
                # Linear fade from CAGR to terminal growth
                progress = year / (forecast_years - 1)
                growth_rate = revenue_cagr * (1 - progress) + terminal_growth * progress
                revenue_growth_path.append(max(0.005, min(0.30, growth_rate)))  # Clamp 0.5%-30%
        else:
            revenue_growth_path = [0.08] * forecast_years
        
        # Operating margin path (use historical average with slight variation)
        operating_margin_path = []
        base_margin = avg_margin if avg_margin else 0.20
        
        for year in range(forecast_years):
            # Allow slight margin improvement over time
            margin_improvement = 0.005 * (forecast_years - year) / forecast_years  # Up to 50bps improvement
            margin = base_margin + margin_improvement
            operating_margin_path.append(max(0.05, min(0.50, margin)))  # Clamp 5%-50%
        
        # Store all assumptions
        result['assumptions'] = {
            'revenue_growth': revenue_growth_path,
            'operating_margin': operating_margin_path,
            'tax_rate': avg_tax_rate if avg_tax_rate else 0.21,
            'capex_percent_revenue': avg_capex_percent,
            'da_percent_revenue': avg_da_percent,
            'nwc_percent_revenue': avg_nwc_percent,
            'wacc': 0.10,  # Will be calculated separately
            'terminal_growth': terminal_growth
        }
        
        # Store historical data for UI
        result['historicals'] = {
            'revenue': revenues[:5],  # Last 5 years
            'revenue_growth_rates': revenue_growth_rates[:4],
            'operating_margins': operating_margins[:5],
            'tax_rates': tax_rates[:3],
            'capex_percentages': capex_percentages[:3],
            'da_percentages': da_percentages[:3],
            'nwc_percentages': nwc_percentages[:3],
            'revenue_cagr_3yr': revenue_cagr,
            'avg_operating_margin_3yr': avg_margin,
            'avg_tax_rate_3yr': avg_tax_rate
        }
        
        return result

def build_fmp_assumptions(ticker: str) -> Dict[str, Any]:
    """Entry point for FMP assumptions builder"""
    engine = FMPDataEngine()
    return engine.build_assumptions_from_data(ticker)
