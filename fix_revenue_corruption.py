#!/usr/bin/env python3
"""
Fix the revenue corruption issue
"""

import sys
sys.path.append('financial-models-app/backend')

def fix_revenue_corruption():
    """Fix the revenue corruption issue"""
    
    # Read the app.py file
    with open('financial-models-app/backend/app.py', 'r') as f:
        content = f.read()
    
    # The issue is that SEC data is overwriting the correct Yahoo Finance revenue
    # Let's fix this by preventing SEC data from overwriting revenue if we already have it from Yahoo Finance
    
    # Find the SEC data section and modify it
    old_sec_section = """            # Cross-validate with SEC data
            if sec_data.get('sec_revenue'):
                data['sec_revenue_formatted'] = format_financial_number(sec_data['sec_revenue'], millions=True)
                # Use SEC data if significantly different from Yahoo
                if abs(sec_data['sec_revenue'] - data.get('revenue', 0)) / data.get('revenue', 1) > 0.1:
                    data['revenue'] = sec_data['sec_revenue'] 
                    data['data_quality'] = 'sec_verified'"""
    
    new_sec_section = """            # Cross-validate with SEC data
            if sec_data.get('sec_revenue'):
                data['sec_revenue_formatted'] = format_financial_number(sec_data['sec_revenue'], millions=True)
                # Only use SEC data if we don't have revenue from Yahoo Finance financial statements
                if not data.get('revenue_set_from_financials', False):
                    # Use SEC data if significantly different from Yahoo
                    if abs(sec_data['sec_revenue'] - data.get('revenue', 0)) / data.get('revenue', 1) > 0.1:
                        data['revenue'] = sec_data['sec_revenue'] 
                        data['data_quality'] = 'sec_verified'
                else:
                    print(f"   📊 Keeping Yahoo Finance revenue (${data.get('revenue', 0)/1e9:.1f}B) over SEC data (${sec_data['sec_revenue']/1e9:.1f}B)")"""
    
    content = content.replace(old_sec_section, new_sec_section)
    
    # Write the fixed content back
    with open('financial-models-app/backend/app.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed revenue corruption issue")

if __name__ == "__main__":
    fix_revenue_corruption() 