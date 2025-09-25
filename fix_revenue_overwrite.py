#!/usr/bin/env python3
"""
Fix the revenue overwriting issue in the app.py file
"""

def fix_revenue_overwrite():
    """Fix the revenue overwriting issue"""
    
    # Read the app.py file
    with open('financial-models-app/backend/app.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Add flag when revenue is set from financial statements
    old_pattern = """                        if real_revenue and not pd.isna(real_revenue):
                            data['revenue'] = abs(float(real_revenue))
                            data['revenue_set_from_financials'] = True  # Mark that we got revenue from financial statements
                            data['yfinance_revenue'] = format_financial_number(data['revenue'], millions=True)"""
    
    new_pattern = """                        if real_revenue and not pd.isna(real_revenue):
                            data['revenue'] = abs(float(real_revenue))
                            data['revenue_set_from_financials'] = True  # Mark that we got revenue from financial statements
                            data['yfinance_revenue'] = format_financial_number(data['revenue'], millions=True)"""
    
    content = content.replace(old_pattern, new_pattern)
    
    # Fix 2: Update the condition to check the flag
    old_condition = """            # Update revenue if we got it from info but not financials
            # Only update if we don't already have revenue from financial statements
            if info.get('totalRevenue') and data['data_quality'] == 'real' and data.get('revenue', 0) == 0:"""
    
    new_condition = """            # Update revenue if we got it from info but not financials
            # Only update if we don't already have revenue from financial statements
            if info.get('totalRevenue') and data['data_quality'] == 'real' and not data.get('revenue_set_from_financials', False):"""
    
    content = content.replace(old_condition, new_condition)
    
    # Write the fixed content back
    with open('financial-models-app/backend/app.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed revenue overwriting issue")

if __name__ == "__main__":
    fix_revenue_overwrite() 