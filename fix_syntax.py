#!/usr/bin/env python3
import re

# Read the file
with open('professional_dcf_model.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the exact problematic pattern using regex
# Pattern: print(" followed by newline then content")
pattern = r'print\(\"\n(.*?)\)\n'
replacement = r'print("\n\1")\n'

content = re.sub(pattern, replacement, content)

# Also fix any remaining unclosed print statements
content = re.sub(r'print\(\"\n([^\)]*)$', r'print("\n\1")', content, flags=re.MULTILINE)

# Write back
with open('professional_dcf_model.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed syntax errors')
