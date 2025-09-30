#!/usr/bin/env python3
"""
Minimal FinModAI app for testing
"""

from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify
import json
import uuid
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

# Create Flask app
app = Flask(__name__)
app.secret_key = 'finmodai_secret_key_2024'

# Simple storage for models
MODEL_STORAGE = {}

class FinancialDataEngine:
    """Real financial data engine using yfinance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
    
    def get_company_data(self, ticker):
        """Fetch comprehensive company data"""
        try:
            # Check cache first (5 minute expiry)
            cache_key = f"{ticker}_data"
            if cache_key in self.cache and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                return self.cache[cache_key]
            
            stock = yf.Ticker(ticker)
            
            # Get basic info
            info = stock.info
            
            # Get financial statements (last 4 years)
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            # Get current stock data
            hist = stock.history(period="1y")
            current_price = float(hist['Close'].iloc[-1]) if not hist.empty else None
            
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
            
            # Cache the result
            self.cache[cache_key] = data
            self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
            
            return data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
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
            if revenue == 0 and company_data.get('market_cap', 0) > 0:
                # Estimate revenue from market cap using industry average P/S ratio
                revenue = company_data['market_cap'] / 3  # Assume 3x P/S ratio
            
            if revenue == 0:
                revenue = 1000000000  # Default $1B if no data
            
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
            
            # Equity value (subtract net debt)
            net_debt = company_data.get('total_debt', 0) - company_data.get('total_cash', 0)
            equity_value = enterprise_value - net_debt
            
            # Per share value
            shares = company_data.get('shares_outstanding', 0)
            if shares == 0:
                shares = company_data.get('market_cap', 0) / max(company_data.get('current_price', 100), 1)
            
            implied_price = equity_value / shares if shares > 0 else 0
            
            return {
                'enterprise_value': float(enterprise_value),
                'equity_value': float(equity_value),
                'implied_price': float(implied_price),
                'current_price': float(company_data.get('current_price', 0)),
                'upside_downside': float((implied_price - company_data.get('current_price', 0)) / company_data.get('current_price', 1) * 100) if company_data.get('current_price', 0) > 0 else 0,
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

@app.route('/status')
def status():
    import os
    return {
        "status": "running",
        "port": os.environ.get('PORT', 'not_set'),
        "app": "minimal_finmodai"
    }

@app.route('/test')
def test():
    return "Minimal FinModAI Test - Working!"

@app.route('/generate-model', methods=['GET', 'POST'])
def generate_model():
    if request.method == 'POST':
        model_type = request.form.get('model_type', 'dcf')
        ticker = request.form.get('ticker', '').upper()
        use_market_data = request.form.get('use_market_data', 'true') == 'true'
        scenario = request.form.get('scenario', 'base')  # base, bull, bear, or all
        
        if not ticker:
            flash('Please enter a ticker symbol', 'error')
            return redirect(url_for('generate_model'))
        
        try:
            start_time = datetime.now()
            model_id = str(uuid.uuid4())
            
            if model_type == 'dcf' and use_market_data:
                # Use real financial data for DCF
                dcf_data = financial_engine.calculate_dcf_scenarios(ticker)
                
                if not dcf_data:
                    flash(f'Could not fetch financial data for {ticker}. Please check the ticker symbol.', 'error')
                    return redirect(url_for('generate_model'))
                
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
            else:
                # Fallback to mock data for other model types or when market data is disabled
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
            
            MODEL_STORAGE[model_id] = {
                'id': model_id,
                'type': model_type,
                'ticker': ticker,
                'result': model_result,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            return redirect(url_for('model_results', model_id=model_id))
            
        except Exception as e:
            flash(f'Error generating model: {str(e)}', 'error')
            return redirect(url_for('generate_model'))
    
    return '''
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
        </script>
    </body>
    </html>
    '''

@app.route('/model-results/<model_id>')
def model_results(model_id):
    if model_id not in MODEL_STORAGE:
        return f"<h1>Model not found</h1><p><a href='/'>Back to Home</a></p>"
    
    model = MODEL_STORAGE[model_id]
    result = model['result']
    
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
                            <div class="bg-gray-50 rounded-lg p-3 mb-4">
                                <p class="text-sm font-mono text-gray-700">{model['type'].upper()}_{model['ticker']}_2025-09-29.xlsx</p>
                            </div>
                            <button class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors flex items-center justify-center">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                Download Excel
                            </button>
                        </div>

                        <!-- Key Assumptions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Key Assumptions</h3>
                            <div class="space-y-3">
{format_assumptions_html(result)}
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
                            
{generate_valuation_html(result)}
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
