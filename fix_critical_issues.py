#!/usr/bin/env python3
"""
Targeted script to fix only the critical set_column_width issues
"""

import re

def fix_critical_issues(file_path):
    """Fix only the set_column_width issues that cause AttributeError"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Only fix set_column_width calls with integer parameters
    # Pattern: set_column_width(worksheet, integer, width)
    pattern = r'set_column_width\(([^,]+),\s*(\d+),\s*(\d+)\)'
    
    def column_number_to_letter(col_num):
        """Convert column number to Excel column letter(s)"""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
        return result
    
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
    
    print("Fixed critical set_column_width issues!")

if __name__ == "__main__":
    fix_critical_issues("professional_dcf_model.py") 