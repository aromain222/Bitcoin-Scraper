#!/usr/bin/env python3
"""
Test raw Yahoo Finance data without any processing
"""

import yfinance as yf
import pandas as pd

def test_raw_yahoo_data():
    """Test raw Yahoo Finance data"""
    
    print("=== RAW YAHOO FINANCE DATA TEST ===")
    
    # Get raw data for Microsoft
    ticker = "MSFT"
    stock = yf.Ticker(ticker)
    
    print(f"\nTesting {ticker}:")
    
    # Get raw financial statements
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow
    info = stock.info
    
    print(f"\nFinancials shape: {financials.shape}")
    print(f"Balance sheet shape: {balance_sheet.shape}")
    print(f"Cash flow shape: {cash_flow.shape}")
    
    if not financials.empty and len(financials.columns) > 0:
        latest_year = financials.columns[0]
        print(f"\nLatest year: {latest_year}")
        
        # Get raw revenue
        revenue_items = ['Total Revenue', 'Revenue', 'Total Revenues', 'Net Sales']
        for item in revenue_items:
            if item in financials.index:
                raw_revenue = financials.loc[item, latest_year]
                print(f"Raw {item}: {raw_revenue}")
                if raw_revenue and not pd.isna(raw_revenue):
                    print(f"  Type: {type(raw_revenue)}")
                    print(f"  Value: {raw_revenue}")
                    print(f"  In billions: {raw_revenue / 1e9}")
                    break
        
        # Get raw operating income
        operating_items = ['Operating Income', 'Operating Income Loss', 'Income Before Tax']
        for item in operating_items:
            if item in financials.index:
                raw_operating = financials.loc[item, latest_year]
                print(f"Raw {item}: {raw_operating}")
                if raw_operating and not pd.isna(raw_operating):
                    print(f"  Type: {type(raw_operating)}")
                    print(f"  Value: {raw_operating}")
                    print(f"  In billions: {raw_operating / 1e9}")
                    break
    
    # Get raw info data
    print(f"\nRaw info data:")
    print(f"totalRevenue: {info.get('totalRevenue')}")
    print(f"currentPrice: {info.get('currentPrice')}")
    print(f"marketCap: {info.get('marketCap')}")
    print(f"enterpriseValue: {info.get('enterpriseValue')}")

if __name__ == "__main__":
    test_raw_yahoo_data() 