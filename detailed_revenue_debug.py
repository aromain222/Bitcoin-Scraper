#!/usr/bin/env python3
"""
Detailed debug script to track revenue changes
"""

import sys
sys.path.append('financial-models-app/backend')

def debug_revenue_changes():
    """Debug revenue changes step by step"""
    
    # Import the function
    from app import get_comprehensive_company_data
    
    print("=== DETAILED REVENUE DEBUG ===")
    
    # Get data
    data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
    
    print(f"\nFinal Data:")
    print(f"Revenue: ${data['revenue']:,.0f}")
    print(f"Operating Income: ${data['operating_income']:,.0f}")
    print(f"EBITDA: ${data['ebitda']:,.0f}")
    print(f"EBITDA Margin: {data['ebitda_margin']*100:.1f}%")
    print(f"Revenue set from financials: {data.get('revenue_set_from_financials', False)}")
    
    # Check the calculation
    actual_ebitda_margin = data['ebitda'] / data['revenue']
    print(f"\nCalculation:")
    print(f"actual_ebitda_margin = {data['ebitda']} / {data['revenue']} = {actual_ebitda_margin}")
    print(f"actual_ebitda_margin = {actual_ebitda_margin*100:.1f}%")
    
    # Check if the values make sense
    print(f"\nValue Analysis:")
    print(f"Revenue in billions: {data['revenue'] / 1e9:.2f}B")
    print(f"EBITDA in billions: {data['ebitda'] / 1e9:.2f}B")
    print(f"Operating Income in billions: {data['operating_income'] / 1e9:.2f}B")
    
    # Check if operating income > revenue (which would be impossible)
    if data['operating_income'] > data['revenue']:
        print(f"❌ IMPOSSIBLE: Operating Income ({data['operating_income']/1e9:.2f}B) > Revenue ({data['revenue']/1e9:.2f}B)")
    else:
        print(f"✅ Operating Income < Revenue (reasonable)")
    
    # Check if EBITDA > revenue (which would be impossible)
    if data['ebitda'] > data['revenue']:
        print(f"❌ IMPOSSIBLE: EBITDA ({data['ebitda']/1e9:.2f}B) > Revenue ({data['revenue']/1e9:.2f}B)")
    else:
        print(f"✅ EBITDA < Revenue (reasonable)")

if __name__ == "__main__":
    debug_revenue_changes() 