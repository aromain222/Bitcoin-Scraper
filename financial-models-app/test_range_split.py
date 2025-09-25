#!/usr/bin/env python3
"""
Test script to demonstrate correct range splitting methods
Fixes the error: parts = range/split(:)
"""

def safe_split(val, sep=None):
    """Safe split function that handles different data types"""
    if isinstance(val, str):
        return val.split(sep)
    else:
        print(f"[DEBUG] safe_split called on non-string: {val} (type: {type(val)})")
        return [str(val)]

def parse_excel_range(range_str):
    """Parse Excel range like 'A1:B5' into start and end cells"""
    if ':' in range_str:
        parts = range_str.split(':')
        start_cell = parts[0]
        end_cell = parts[1]
        return start_cell, end_cell
    else:
        return range_str, range_str

def test_range_splitting():
    """Test various range splitting scenarios"""
    print("🔧 Testing Range Splitting Methods")
    print("=" * 40)
    
    # Test cases
    test_ranges = [
        "A1:B5",
        "Sheet1!A1:C10", 
        "A1:G1",
        "B2:D8",
        "A1"  # Single cell
    ]
    
    for range_str in test_ranges:
        print(f"\n📊 Testing: '{range_str}'")
        
        # Method 1: Direct split
        try:
            parts = range_str.split(':')
            print(f"   ✅ Direct split: {parts}")
        except Exception as e:
            print(f"   ❌ Direct split error: {e}")
        
        # Method 2: Safe split
        try:
            parts = safe_split(range_str, ':')
            print(f"   ✅ Safe split: {parts}")
        except Exception as e:
            print(f"   ❌ Safe split error: {e}")
        
        # Method 3: Parse function
        try:
            start, end = parse_excel_range(range_str)
            print(f"   ✅ Parse function: Start={start}, End={end}")
        except Exception as e:
            print(f"   ❌ Parse function error: {e}")

if __name__ == "__main__":
    test_range_splitting() 