#!/usr/bin/env python3
"""
Script to fix set_column_width calls that use variables (like in loops)
"""

import re

def fix_loop_column_width(file_path):
    """Fix set_column_width calls that use variables"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    def column_number_to_letter(col_num):
        """Convert column number to Excel column letter(s)"""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + col_num % 26) + result
            col_num //= 26
        return result
    
    # Pattern to match set_column_width calls with variable parameters in loops
    # set_column_width(worksheet, col, width) where col is a variable
    pattern = r'set_column_width\(([^,]+),\s*([a-zA-Z_][a-zA-Z0-9_]*),\s*(\d+)\)'
    
    def replace_match(match):
        worksheet = match.group(1)
        col_var = match.group(2)
        width = match.group(3)
        
        # For variable column references, we need to convert at runtime
        # We'll use a helper function that converts the number to a column letter
        return f"set_column_width({worksheet}, f'{{{col_var}}}:{{{col_var}}}', {width}) if isinstance({col_var}, str) else set_column_width({worksheet}, f'{{chr(64+{col_var})}}:{{chr(64+{col_var})}}', {width})"
    
    # This is getting complex, let's use a simpler approach
    # Replace with a more direct fix for the common case
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if 'set_column_width(' in line and 'col' in line and 'for col in range' not in line:
            # This is likely a problematic line
            # Replace set_column_width(ws, col, width) with proper format
            if re.search(r'set_column_width\([^,]+,\s*col,\s*\d+\)', line):
                # Replace col with a formula that converts to column letter
                line = re.sub(
                    r'set_column_width\(([^,]+),\s*col,\s*(\d+)\)',
                    r"set_column_width(\1, chr(64+col) + ':' + chr(64+col), \2)",
                    line
                )
        fixed_lines.append(line)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("Fixed loop-based set_column_width calls!")

if __name__ == "__main__":
    fix_loop_column_width("professional_dcf_model.py") 