#!/usr/bin/env python3
"""
Script to fix broken f-strings in professional_dcf_model.py
Fixes patterns like {company_name.upper(, range_name='A1')} back to {company_name.upper()}
"""

import re

def fix_broken_fstrings(file_path):
    """Fix all broken f-strings in the file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match broken f-strings with upper( followed by , range_name
    # {company_name.upper(, range_name='A1')}
    pattern = r'\{([^}]+)\.upper\(, range_name=\'[^\']+\'\)'
    
    def replace_match(match):
        variable = match.group(1)
        return f"{{{variable}.upper()}}"
    
    # Replace all matches
    fixed_content = re.sub(pattern, replace_match, content)
    
    # Also fix other similar patterns if they exist
    # {variable.method(, range_name='...')}
    pattern2 = r'\{([^}]+)\.([a-zA-Z_]+)\(, range_name=\'[^\']+\'\)'
    
    def replace_match2(match):
        variable = match.group(1)
        method = match.group(2)
        return f"{{{variable}.{method}()}}"
    
    fixed_content = re.sub(pattern2, replace_match2, fixed_content)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print("Fixed all broken f-strings!")

if __name__ == "__main__":
    fix_broken_fstrings("professional_dcf_model.py") 