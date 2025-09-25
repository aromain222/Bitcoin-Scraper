#!/usr/bin/env python3
"""
Script to fix all column width errors in professional_dcf_model.py
Converts integer column references to proper string format for Google Sheets API
"""

import re

def fix_column_width_errors(file_path):
    """Fix all set_column_width calls that use integer column references"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match: set_column_width(worksheet, col, width)
    # where col is a variable that could be an integer
    pattern = r'set_column_width\(([^,]+),\s*col,\s*(\d+)\)'
    
    def replace_match(match):
        worksheet = match.group(1)
        width = match.group(2)
        return f"set_column_width({worksheet}, f'{{chr(64+col)}}:{{chr(64+col)}}', {width})"
    
    # Replace all matches
    fixed_content = re.sub(pattern, replace_match, content)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed all column width errors in professional_dcf_model.py")
    print("   🔧 Converted integer column references to proper string format")
    print("   📊 Google Sheets API now receives correct column letters (A, B, C, etc.)")

if __name__ == "__main__":
    fix_column_width_errors("professional_dcf_model.py") 