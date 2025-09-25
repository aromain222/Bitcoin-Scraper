#!/usr/bin/env python3
"""
Remove all formatting and keep only raw numbers
"""

def remove_all_formatting():
    """Remove all formatting from the app.py file"""
    
    # Read the app.py file
    with open('financial-models-app/backend/app.py', 'r') as f:
        content = f.read()
    
    import re
    
    # Remove all format_financial_number calls
    content = re.sub(
        r"format_financial_number\([^)]+\)",
        r"str(data.get('revenue', 0))",
        content
    )
    
    # Remove all f-string formatting for display
    content = re.sub(
        r"f\"\$\{([^}]+)/1e9:\.1f\}B\"",
        r"\1",
        content
    )
    
    content = re.sub(
        r"f\"\$\{([^}]+):,\.0f\}\"",
        r"\1",
        content
    )
    
    content = re.sub(
        r"f\"\$\{([^}]+):\.1f\}%\"",
        r"\1 * 100",
        content
    )
    
    content = re.sub(
        r"f\"\$\{([^}]+):\.2f\}\"",
        r"\1",
        content
    )
    
    content = re.sub(
        r"f\"\$\{([^}]+):\.1f\}x\"",
        r"\1",
        content
    )
    
    # Remove any other formatting patterns
    content = re.sub(
        r"f\"\$\{([^}]+):\.0f\}\"",
        r"\1",
        content
    )
    
    # Remove the display formatting in the summary prints
    content = re.sub(
        r"print\(f\"   💰 Revenue: \$\{data\['revenue'\]/1e9:\.2f\}B\"\)",
        r"print(f\"   💰 Revenue: {data['revenue']}\")",
        content
    )
    
    content = re.sub(
        r"print\(f\"   📈 EBITDA: \$\{data\['ebitda'\]/1e9:\.2f\}B \(\{data\['ebitda_margin'\]\*100:\.1f\}% margin\)\"\)",
        r"print(f\"   📈 EBITDA: {data['ebitda']} ({data['ebitda_margin']*100}% margin)\")",
        content
    )
    
    # Write the fixed content back
    with open('financial-models-app/backend/app.py', 'w') as f:
        f.write(content)
    
    print("✅ Removed all formatting - using raw numbers only")

if __name__ == "__main__":
    remove_all_formatting() 