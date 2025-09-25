#!/usr/bin/env python3
"""
Quick DCF Generator
Simple version that takes a company ticker and generates a DCF model with real financial data.
"""

import sys
import os
import yfinance as yf
from datetime import datetime
from expert_dcf_model import ExpertDCFModel

def get_company_data(ticker: str):
    """Get basic financial data for a company using yfinance."""
    try:
        print(f"🔍 Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)

        # Get basic info
        info = stock.info

        # Get financial statements (most recent)
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow

        data = {
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'shares_outstanding': info.get('sharesOutstanding', 0),
            'beta': info.get('beta', 1.2),
            'revenue': 0,
            'ebitda': 0,
            'net_income': 0,
            'total_debt': 0,
            'cash': 0
        }

        # Extract most recent financial data
        if not income_stmt.empty and 'Total Revenue' in income_stmt.index:
            data['revenue'] = income_stmt.loc['Total Revenue'].iloc[0] / 1000000  # Convert to $MM

        if not income_stmt.empty and 'EBITDA' in income_stmt.index:
            data['ebitda'] = income_stmt.loc['EBITDA'].iloc[0] / 1000000
        elif not income_stmt.empty and 'Operating Income' in income_stmt.index:
            # Estimate EBITDA as Operating Income + Depreciation
            op_income = income_stmt.loc['Operating Income'].iloc[0]
            dep = 0
            if 'Depreciation' in cash_flow.index:
                dep = cash_flow.loc['Depreciation'].iloc[0]
            data['ebitda'] = (op_income + dep) / 1000000

        if not income_stmt.empty and 'Net Income' in income_stmt.index:
            data['net_income'] = income_stmt.loc['Net Income'].iloc[0] / 1000000

        if not balance_sheet.empty and 'Total Debt' in balance_sheet.index:
            data['total_debt'] = balance_sheet.loc['Total Debt'].iloc[0] / 1000000

        if not balance_sheet.empty and 'Cash And Cash Equivalents' in balance_sheet.index:
            data['cash'] = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] / 1000000

        print("✅ Data retrieved successfully")
        return data

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def calculate_dcf_inputs(company_data: dict):
    """Calculate DCF inputs based on company data."""

    # Base inputs
    inputs = {
        'BaseYear': datetime.now().year,
        'Horizon': 6,
        'TerminalMethod': 'Perpetuity',
        'Rev0': 1000.0,  # Default $1B
        'g_base': 0.08,  # 8% growth
        'g_bull': 0.12,
        'g_bear': 0.04,
        'EBITDA_m': 0.25,  # 25% EBITDA margin
        'DA_pct': 0.05,
        'Capex_pct': 0.06,
        'NWC_pct': 0.02,
        'TaxRate': 0.25,
        'Rf': 0.045,  # 4.5% risk-free rate
        'ERP': 0.06,  # 6% equity risk premium
        'Beta': 1.2,
        'CoD_pre': 0.055,  # 5.5% pre-tax cost of debt
        'Wd': 0.40,  # 40% debt ratio
        'Tax_marg': 0.25,
        'g_term': 0.025,  # 2.5% terminal growth
        'ExitMult': 10.0,
        'MidYear': True,
        'NetDebt': 200.0,
        'OtherAdj': 0.0,
        'Shares': 50.0
    }

    # Override with real data if available
    if company_data['revenue'] > 0:
        inputs['Rev0'] = company_data['revenue']
        print(f"   Revenue: ${inputs['Rev0']:,.1f}M")
    if company_data['beta'] and company_data['beta'] > 0:
        inputs['Beta'] = min(2.0, max(0.5, company_data['beta']))  # Clamp beta
        print(f"   Beta: {inputs['Beta']:.2f}")
    if company_data['shares_outstanding'] > 0:
        inputs['Shares'] = company_data['shares_outstanding'] / 1000000  # Convert to millions
        print(f"   Shares: {inputs['Shares']:,.1f}M")
    if company_data['total_debt'] > 0 and company_data['cash'] > 0:
        net_debt = company_data['total_debt'] - company_data['cash']
        inputs['NetDebt'] = max(0, net_debt)  # Can't have negative net debt
        print(f"   Net Debt: ${inputs['NetDebt']:,.1f}M")
    # Estimate EBITDA margin if we have both revenue and EBITDA
    if company_data['revenue'] > 0 and company_data['ebitda'] > 0:
        margin = company_data['ebitda'] / company_data['revenue']
        inputs['EBITDA_m'] = min(0.60, max(0.05, margin))  # Clamp between 5%-60%
        print(f"   EBITDA Margin: {inputs['EBITDA_m']:.1%}")

    return inputs

def generate_dcf_for_ticker(ticker: str):
    """Generate DCF model for a given ticker."""
    print("🚀 Quick DCF Generator")
    print("=" * 40)
    print(f"📊 Analyzing: {ticker.upper()}")

    # Get company data
    company_data = get_company_data(ticker)

    if not company_data:
        print("❌ Could not retrieve company data")
        return None

    print(f"🏢 Company: {company_data['company_name']}")
    print(f"🏭 Sector: {company_data['sector']}")
    print(f"📈 Industry: {company_data['industry']}")

    # Calculate DCF inputs
    print("\n🧮 Calculating DCF assumptions...")
    dcf_inputs = calculate_dcf_inputs(company_data)

    # Generate DCF model
    print("📊 Building DCF model...")
    dcf_model = ExpertDCFModel()
    dcf_model.defaults.update(dcf_inputs)

    # Create workbook
    wb = dcf_model.build_model()

    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DCF_{ticker.upper()}_{timestamp}.xlsx"
    dcf_model.save_model(filename)

    print("\n✅ DCF Model Generated!")
    print(f"📁 File: {filename}")

    # Show key outputs
    print("\n📊 Key Metrics:")
    print(f"   Revenue: ${dcf_inputs['Rev0']:,.1f}M")
    print(f"   Growth Rate: {dcf_inputs['g_base']:.1%}")
    print(f"   EBITDA Margin: {dcf_inputs['EBITDA_m']:.1%}")
    print(f"   Beta: {dcf_inputs['Beta']:.2f}")
    print(f"   WACC: {(dcf_inputs['Rf'] + dcf_inputs['Beta'] * dcf_inputs['ERP']) * (1 - dcf_inputs['Wd']) + (dcf_inputs['CoD_pre'] * (1 - dcf_inputs['Tax_marg'])) * dcf_inputs['Wd']:.1%}")

    return filename

def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_dcf_generator.py TICKER")
        print("Example: python quick_dcf_generator.py AAPL")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    generate_dcf_for_ticker(ticker)

if __name__ == "__main__":
    main()
