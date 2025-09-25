#!/usr/bin/env python3
"""
Improved script to fix worksheet.update calls in professional_dcf_model.py
More careful handling of complex expressions and f-strings
"""

import re

def fix_update_calls_v2(file_path):
    """Fix all worksheet.update calls in the file more carefully"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line_num, line in enumerate(lines, 1):
        # Look for simple update calls that we can safely fix
        # Pattern: worksheet.update('range', simple_data)
        if '.update(' in line and 'range_name=' not in line:
            # Try to match simple cases
            simple_pattern = r'(\w+)\.update\(\'([^\']+)\',\s*([^)]+)\)$'
            match = re.search(simple_pattern, line.strip())
            
            if match:
                worksheet = match.group(1)
                range_name = match.group(2)
                data = match.group(3)
                
                # Check if this is a complex expression that might break
                if '{' in data and '}' in data and 'datetime.now(' in data:
                    # This is likely an f-string that got broken, skip for manual fix
                    print(f"Skipping complex expression at line {line_num}: {line.strip()}")
                    fixed_lines.append(line)
                else:
                    # Safe to replace
                    indent = len(line) - len(line.lstrip())
                    fixed_line = ' ' * indent + f"{worksheet}.update(values={data}, range_name='{range_name}')\n"
                    fixed_lines.append(fixed_line)
                    print(f"Fixed line {line_num}: {line.strip()}")
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print("Completed fixing worksheet.update calls!")

if __name__ == "__main__":
    # First, let's restore the original file and try again
    print("Restoring and fixing update calls...")
    fix_update_calls_v2("professional_dcf_model.py") 