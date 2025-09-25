#!/usr/bin/env python3
"""
Fix the app to use raw numbers without any formatting or rounding
"""

def fix_raw_numbers():
    """Remove all formatting and keep raw numbers"""
    
    # Read the app.py file
    with open('financial-models-app/backend/app.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Remove format_financial_number calls that round numbers
    import re
    
    # Replace format_financial_number calls with raw values
    content = re.sub(
        r"format_financial_number\(([^,]+), millions=True\)",
        r"\1",
        content
    )
    
    content = re.sub(
        r"format_financial_number\(([^,]+), millions=False\)",
        r"\1",
        content
    )
    
    content = re.sub(
        r"format_financial_number\(([^,]+)\)",
        r"\1",
        content
    )
    
    # Fix 2: Remove f-string formatting that rounds numbers
    content = re.sub(
        r"f\"\{([^}]+):\.1f\}%\"",
        r"\1 * 100",
        content
    )
    
    content = re.sub(
        r"f\"\{([^}]+):\.2f\}\"",
        r"\1",
        content
    )
    
    content = re.sub(
        r"f\"\{([^}]+):\.1f\}x\"",
        r"\1",
        content
    )
    
    # Fix 3: Remove any other formatting that might round
    content = re.sub(
        r"f\"\{([^}]+):\.0f\}\"",
        r"\1",
        content
    )
    
    # Write the fixed content back
    with open('financial-models-app/backend/app.py', 'w') as f:
        f.write(content)
    
    print("✅ Removed all number formatting and rounding")

if __name__ == "__main__":
    fix_raw_numbers() 