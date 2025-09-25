#!/usr/bin/env python3
"""
Script to fix set_column_width calls in professional_dcf_model.py
Converts integer column numbers to proper column range strings
"""

import re

def column_number_to_letter(col_num):
    """Convert column number to Excel column letter(s)"""
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(65 + col_num % 26) + result
        col_num //= 26
    return result

def fix_set_column_width_calls(file_path):
    """Fix all set_column_width calls in the file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match set_column_width calls with integer parameters
    pattern = r'set_column_width\(([^,]+),\s*(\d+),\s*(\d+)\)'
    
    def replace_match(match):
        worksheet = match.group(1)
        col_num = int(match.group(2))
        width = match.group(3)
        
        # Convert column number to letter
        col_letter = column_number_to_letter(col_num)
        
        # Return the fixed call
        return f"set_column_width({worksheet}, '{col_letter}:{col_letter}', {width})"
    
    # Replace all matches
    fixed_content = re.sub(pattern, replace_match, content)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print("Fixed all set_column_width calls!")

if __name__ == "__main__":
    fix_set_column_width_calls("professional_dcf_model.py") 