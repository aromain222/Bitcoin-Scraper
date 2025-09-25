#!/usr/bin/env python3
"""
Directly fix the formatting to show raw numbers
"""

def fix_raw_numbers_direct():
    """Directly fix the formatting to show raw numbers"""
    
    # Read the app.py file
    with open('financial-models-app/backend/app.py', 'r') as f:
        lines = f.readlines()
    
    # Fix specific lines that format numbers
    for i, line in enumerate(lines):
        # Fix the revenue display line
        if "print(f\"   💰 Revenue: $" in line and "/1e9:.2f}B\")" in line:
            lines[i] = "        print(f\"   💰 Revenue: {data['revenue']}\")\n"
        
        # Fix the EBITDA display line
        elif "print(f\"   📈 EBITDA: $" in line and "/1e9:.2f}B" in line:
            lines[i] = "        print(f\"   📈 EBITDA: {data['ebitda']} ({data['ebitda_margin']*100}% margin)\")\n"
        
        # Fix the SEC data comparison line
        elif "Keeping Yahoo Finance revenue ($" in line and "B) over SEC data ($" in line:
            lines[i] = "                    print(f\"   📊 Keeping Yahoo Finance revenue ({data.get('revenue', 0)}) over SEC data ({sec_data['sec_revenue']})\")\n"
        
        # Fix any other formatting in the DCF model
        elif "Base revenue: $" in line and "M" in line:
            lines[i] = lines[i].replace("M", "").replace("$", "").replace(":", ": ")
        
        # Fix growth rates formatting
        elif "Growth rates: [" in line and "%" in line:
            lines[i] = lines[i].replace("%", "").replace("'", "")
    
    # Write the fixed content back
    with open('financial-models-app/backend/app.py', 'w') as f:
        f.writelines(lines)
    
    print("✅ Fixed formatting to show raw numbers")

if __name__ == "__main__":
    fix_raw_numbers_direct() 