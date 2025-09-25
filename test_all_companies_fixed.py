#!/usr/bin/env python3
"""
Test the fix on multiple companies
"""

import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

def test_all_companies():
    """Test the fix on multiple companies"""
    
    companies = [
        ('MSFT', 'Microsoft Corporation'),
        ('AAPL', 'Apple Inc.'),
        ('GOOGL', 'Alphabet Inc.'),
        ('TSLA', 'Tesla Inc.')
    ]
    
    print("=== TESTING FIXED DATA ON ALL COMPANIES ===")
    
    for ticker, name in companies:
        print(f"\n📊 {name} ({ticker}):")
        data = get_comprehensive_company_data(ticker, name)
        
        revenue = data['revenue']
        operating_income = data['operating_income']
        ebitda = data['ebitda']
        ebitda_margin = ebitda / revenue
        
        print(f"   Revenue: ${revenue:,.0f}")
        print(f"   Operating Income: ${operating_income:,.0f}")
        print(f"   EBITDA: ${ebitda:,.0f}")
        print(f"   EBITDA Margin: {ebitda_margin*100:.1f}%")
        
        # Check if reasonable
        if 0.05 <= ebitda_margin <= 0.8:
            print(f"   ✅ Reasonable EBITDA margin")
        else:
            print(f"   ❌ Unreasonable EBITDA margin")
        
        # Check if operating income < revenue
        if operating_income < revenue:
            print(f"   ✅ Operating Income < Revenue (correct)")
        else:
            print(f"   ❌ Operating Income > Revenue (impossible)")

if __name__ == "__main__":
    test_all_companies() 