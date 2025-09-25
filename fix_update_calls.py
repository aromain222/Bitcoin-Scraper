#!/usr/bin/env python3
"""
Script to fix worksheet.update calls in professional_dcf_model.py
Converts old format update('range', data) to new format update(values=data, range_name='range')
"""

import re

def fix_update_calls(file_path):
    """Fix all worksheet.update calls in the file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match .update('range', data) calls
    pattern = r'(\w+)\.update\(\'([^\']+)\',\s*([^)]+)\)'
    
    def replace_match(match):
        worksheet = match.group(1)
        range_name = match.group(2)
        data = match.group(3)
        
        # Return the fixed call with named parameters
        return f"{worksheet}.update(values={data}, range_name='{range_name}')"
    
    # Replace all matches
    fixed_content = re.sub(pattern, replace_match, content)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print("Fixed all worksheet.update calls!")

if __name__ == "__main__":
    fix_update_calls("professional_dcf_model.py") 