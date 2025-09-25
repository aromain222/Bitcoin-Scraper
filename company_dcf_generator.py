#!/usr/bin/env python3
"""
Company DCF Generator
Takes a company name or ticker and generates a customized DCF model Excel file
with real financial data and appropriate assumptions.

Usage:
    python company_dcf_generator.py "Apple Inc" AAPL
    python company_dcf_generator.py "Microsoft Corporation"
    python company_dcf_generator.py TSLA
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from expert_dcf_model import ExpertDCFModel
from financial_data_manager import FinancialDataManager, CompanyFinancials

def get_ticker_from_company_name(company_name: str) -> Optional[str]:
    """Convert company name to ticker symbol using yfinance lookup."""
    try:
        import yfinance as yf
        # Simple ticker lookup - in production you'd use a more robust mapping
        ticker_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "disney": "DIS",
            "coca cola": "KO",
            "pepsi": "PEP",
            "johnson & johnson": "JNJ",
            "jnj": "JNJ",
            "procter & gamble": "PG",
            "pfizer": "PFE",
            "verizon": "VZ",
            "att": "T",
            "walmart": "WMT",
            "home depot": "HD",
            "mcdonalds": "MCD",
            "starbucks": "SBUX",
            "uber": "UBER",
            "lyft": "LYFT",
            "airbnb": "ABNB",
            "zoom": "ZM",
            "slack": "WORK",  # Now part of Salesforce
            "salesforce": "CRM",
            "shopify": "SHOP",
            "square": "SQ",  # Now Block
            "block": "SQ",
            "paypal": "PYPL",
            "stripe": "N/A",  # Private company
            "coinbase": "COIN",
            "robinhood": "HOOD"
        }

        # Clean company name for lookup
        clean_name = company_name.lower().strip()

        # Direct lookup first
        if clean_name in ticker_map:
            return ticker_map[clean_name]

        # Partial match
        for key, ticker in ticker_map.items():
            if key in clean_name or clean_name in key:
                return ticker

        # If no match found, try to use yfinance search
        try:
            search_results = yf.Ticker(company_name).info
            if search_results and 'symbol' in search_results:
                return search_results['symbol']
        except:
            pass

        return None

    except ImportError:
        print("⚠️ yfinance not available for ticker lookup")
        return None

def calculate_dcf_assumptions(financials: CompanyFinancials) -> Dict[str, Any]:
    """Calculate appropriate DCF assumptions based on company financials."""

    assumptions = {
        'BaseYear': datetime.now().year,
        'Horizon': 6,
        'TerminalMethod': 'Perpetuity',
        'Rev0': 0,
        'g_base': 0.08,  # Default growth
        'g_bull': 0.12,
        'g_bear': 0.04,
        'EBITDA_m': 0.25,  # Default EBITDA margin
        'DA_pct': 0.05,
        'Capex_pct': 0.06,
        'NWC_pct': 0.02,
        'TaxRate': 0.25,
        'Rf': 0.045,  # Risk-free rate (4.5%)
        'ERP': 0.06,  # Equity risk premium (6%)
        'Beta': 1.2,   # Default beta
        'CoD_pre': 0.055,  # Pre-tax cost of debt (5.5%)
        'Wd': 0.40,   # Target debt ratio (40%)
        'Tax_marg': 0.25,  # Marginal tax rate
        'g_term': 0.025,  # Terminal growth (2.5%)
        'ExitMult': 10.0,  # Exit multiple
        'MidYear': True,
        'NetDebt': 0,
        'OtherAdj': 0,
        'Shares': 100.0  # Default shares outstanding
    }

    # Update with real data if available
    if financials.revenue:
        assumptions['Rev0'] = financials.revenue[0] / 1000000  # Convert to $mm

    if financials.ebitda and financials.revenue and len(financials.revenue) > 0:
        # Calculate EBITDA margin
        ebitda_margin = financials.ebitda[0] / financials.revenue[0] if financials.revenue[0] > 0 else 0.25
        assumptions['EBITDA_m'] = max(0.05, min(0.60, ebitda_margin))  # Clamp between 5%-60%

    if financials.revenue_growth:
        assumptions['g_base'] = min(0.15, max(0.01, financials.revenue_growth / 100))  # Clamp growth rate
        assumptions['g_bull'] = assumptions['g_base'] * 1.5
        assumptions['g_bear'] = assumptions['g_base'] * 0.5

    if hasattr(financials, 'beta') and financials.beta:
        assumptions['Beta'] = financials.beta

    if hasattr(financials, 'debt_to_equity') and financials.debt_to_equity:
        # Calculate target debt ratio from actual
        assumptions['Wd'] = min(0.80, max(0.10, financials.debt_to_equity / (1 + financials.debt_to_equity)))

    if hasattr(financials, 'total_debt') and financials.total_debt:
        assumptions['NetDebt'] = financials.total_debt / 1000000  # Convert to $mm

    if hasattr(financials, 'shares_outstanding') and financials.shares_outstanding:
        assumptions['Shares'] = financials.shares_outstanding / 1000000  # Convert to mm

    return assumptions

def generate_company_dcf(company_name: str, ticker: Optional[str] = None, output_dir: str = ".") -> str:
    """
    Generate a customized DCF model for a specific company.

    Args:
        company_name: Name of the company
        ticker: Stock ticker (optional, will be looked up if not provided)
        output_dir: Directory to save the Excel file

    Returns:
        Path to the generated Excel file
    """

    print("🚀 Company DCF Generator")
    print("=" * 50)
    print(f"📊 Company: {company_name}")

    # Get ticker if not provided
    if not ticker:
        ticker = get_ticker_from_company_name(company_name)
        if ticker:
            print(f"🔍 Found ticker: {ticker}")
        else:
            print("⚠️ Could not find ticker, using default assumptions")
            ticker = "UNKNOWN"

    # Initialize financial data manager
    try:
        data_manager = FinancialDataManager()
        print("📡 Fetching financial data...")

        # Get financial data
        financials = data_manager.get_company_financials(ticker, years=3)

        if financials and financials.revenue:
            print("✅ Financial data retrieved successfully")
            print(f"   Revenue: ${financials.revenue[0]/1000000:,.2f}M")
            if hasattr(financials, 'revenue_growth') and financials.revenue_growth:
                print(f"   Growth: {financials.revenue_growth:.1f}%")
        else:
            print("⚠️ Limited financial data available, using defaults")

    except Exception as e:
        print(f"❌ Error fetching financial data: {e}")
        print("📝 Using default assumptions")
        financials = CompanyFinancials(ticker=ticker)

    # Calculate DCF assumptions
    print("🧮 Calculating DCF assumptions...")
    assumptions = calculate_dcf_assumptions(financials)

    # Create customized DCF model
    print("📊 Building DCF model...")
    dcf_model = ExpertDCFModel()

    # Override defaults with calculated assumptions
    dcf_model.defaults.update(assumptions)

    # Build the model
    wb = dcf_model.build_model()

    # Generate filename
    safe_company_name = company_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DCF_{safe_company_name}_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)

    # Save the model
    dcf_model.save_model(filepath)

    print("\n✅ DCF Model Generated Successfully!")
    print(f"📁 File: {filepath}")
    print("\n📊 Key Assumptions:")
    print(f"   Revenue (Base): ${assumptions['Rev0']:,.1f}M")
    print(f"   Growth Rate: {assumptions['g_base']:.1%}")
    print(f"   EBITDA Margin: {assumptions['EBITDA_m']:.1%}")
    print(f"   Beta: {assumptions['Beta']:.2f}")
    print(f"   WACC: {(assumptions['Rf'] + assumptions['Beta'] * assumptions['ERP']) * (1 - assumptions['Wd']) + (assumptions['CoD_pre'] * (1 - assumptions['Tax_marg'])) * assumptions['Wd']:.1%}")
    print(f"   Terminal Growth: {assumptions['g_term']:.1%}")

    if financials.revenue:
        print("\n📈 Historical Data:")
        print(f"   Latest Revenue: ${financials.revenue[0]/1000000:,.2f}M")
        if len(financials.revenue) > 1:
            print(f"   Revenue Growth: {((financials.revenue[0]/financials.revenue[1])-1)*100:.1f}%")
    return filepath

def main():
    parser = argparse.ArgumentParser(description="Generate DCF model for a company")
    parser.add_argument("company_name", help="Name of the company")
    parser.add_argument("ticker", nargs="?", help="Stock ticker (optional)")
    parser.add_argument("-o", "--output", default=".", help="Output directory")

    args = parser.parse_args()

    try:
        filepath = generate_company_dcf(
            company_name=args.company_name,
            ticker=args.ticker,
            output_dir=args.output
        )

        print(f"\n🎉 Your DCF model is ready: {filepath}")
        print("📋 Open in Excel to view the complete analysis")

    except Exception as e:
        print(f"❌ Error generating DCF model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode
        print("Company DCF Generator")
        print("=" * 30)

        company_name = input("Enter company name: ").strip()
        ticker = input("Enter ticker symbol (optional): ").strip() or None

        if company_name:
            try:
                generate_company_dcf(company_name, ticker)
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("❌ Company name is required")
    else:
        # Command line mode
        main()
