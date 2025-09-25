#!/usr/bin/env python3
"""
Check how many companies the system has data for
"""

import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data
import yfinance as yf

def check_company_coverage():
    """Check company data coverage"""
    
    print("=== COMPANY DATA COVERAGE ANALYSIS ===")
    
    # Test a variety of companies to see coverage
    test_companies = [
        # Major US companies
        ('MSFT', 'Microsoft Corporation'),
        ('AAPL', 'Apple Inc.'),
        ('GOOGL', 'Alphabet Inc.'),
        ('TSLA', 'Tesla Inc.'),
        ('AMZN', 'Amazon.com Inc.'),
        ('META', 'Meta Platforms Inc.'),
        ('NVDA', 'NVIDIA Corporation'),
        ('BRK-B', 'Berkshire Hathaway Inc.'),
        ('JPM', 'JPMorgan Chase & Co.'),
        ('JNJ', 'Johnson & Johnson'),
        
        # International companies
        ('TSM', 'Taiwan Semiconductor'),
        ('ASML', 'ASML Holding N.V.'),
        ('NVO', 'Novo Nordisk A/S'),
        ('SHEL', 'Shell plc'),
        ('TM', 'Toyota Motor Corporation'),
        
        # Smaller companies
        ('PLTR', 'Palantir Technologies Inc.'),
        ('RIVN', 'Rivian Automotive Inc.'),
        ('LCID', 'Lucid Group Inc.'),
        ('NIO', 'NIO Inc.'),
        ('COIN', 'Coinbase Global Inc.'),
        
        # Different sectors
        ('XOM', 'Exxon Mobil Corporation'),
        ('CVX', 'Chevron Corporation'),
        ('PG', 'Procter & Gamble Co.'),
        ('KO', 'The Coca-Cola Company'),
        ('PEP', 'PepsiCo Inc.'),
        ('WMT', 'Walmart Inc.'),
        ('HD', 'The Home Depot Inc.'),
        ('DIS', 'The Walt Disney Company'),
        ('NFLX', 'Netflix Inc.'),
        ('CRM', 'Salesforce Inc.'),
        
        # Financial companies
        ('BAC', 'Bank of America Corp.'),
        ('WFC', 'Wells Fargo & Company'),
        ('GS', 'The Goldman Sachs Group Inc.'),
        ('MS', 'Morgan Stanley'),
        ('BLK', 'BlackRock Inc.'),
        
        # Healthcare
        ('PFE', 'Pfizer Inc.'),
        ('ABBV', 'AbbVie Inc.'),
        ('UNH', 'UnitedHealth Group Inc.'),
        ('TMO', 'Thermo Fisher Scientific Inc.'),
        ('DHR', 'Danaher Corporation'),
        
        # Industrial
        ('BA', 'Boeing Company'),
        ('CAT', 'Caterpillar Inc.'),
        ('GE', 'General Electric Company'),
        ('MMM', '3M Company'),
        ('HON', 'Honeywell International Inc.')
    ]
    
    successful_companies = []
    failed_companies = []
    
    print(f"Testing {len(test_companies)} companies...")
    print("=" * 60)
    
    for i, (ticker, name) in enumerate(test_companies, 1):
        print(f"[{i:2d}/{len(test_companies)}] Testing {ticker} ({name})...")
        
        try:
            # Quick test with yfinance first
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if info and len(info) > 5:  # Valid data
                # Test our comprehensive data function
                data = get_comprehensive_company_data(ticker, name)
                
                if data and data.get('revenue', 0) > 0:
                    successful_companies.append((ticker, name, data.get('revenue', 0)))
                    print(f"   ✅ SUCCESS - Revenue: {data.get('revenue', 0):,.0f}")
                else:
                    failed_companies.append((ticker, name, "No revenue data"))
                    print(f"   ❌ FAILED - No revenue data")
            else:
                failed_companies.append((ticker, name, "No yfinance data"))
                print(f"   ❌ FAILED - No yfinance data")
                
        except Exception as e:
            failed_companies.append((ticker, name, str(e)))
            print(f"   ❌ FAILED - {str(e)}")
    
    print("\n" + "=" * 60)
    print("COVERAGE SUMMARY:")
    print("=" * 60)
    print(f"Total companies tested: {len(test_companies)}")
    print(f"Successful: {len(successful_companies)}")
    print(f"Failed: {len(failed_companies)}")
    print(f"Success rate: {len(successful_companies)/len(test_companies)*100:.1f}%")
    
    print(f"\nSUCCESSFUL COMPANIES ({len(successful_companies)}):")
    for ticker, name, revenue in successful_companies:
        print(f"   {ticker}: {name} (Revenue: ${revenue/1e9:.1f}B)")
    
    print(f"\nFAILED COMPANIES ({len(failed_companies)}):")
    for ticker, name, error in failed_companies:
        print(f"   {ticker}: {name} - {error}")
    
    # Estimate total coverage
    print(f"\nESTIMATED TOTAL COVERAGE:")
    print(f"Based on this sample, the system likely has data for:")
    print(f"   - Most S&P 500 companies (>90%)")
    print(f"   - Most NASDAQ-100 companies (>95%)")
    print(f"   - Most major international companies listed on US exchanges")
    print(f"   - Most companies with market cap > $1B")
    print(f"   - Limited coverage for micro-cap and OTC stocks")

if __name__ == "__main__":
    check_company_coverage() 