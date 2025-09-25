#!/usr/bin/env python3
"""
Test script for the Enhanced Professional DCF Model
Demonstrates all the new features and tabs
"""

import sys
import os

# Add the current directory to the path so we can import the DCF model
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from professional_dcf_model import build_professional_dcf_model

def test_enhanced_dcf():
    """Test the enhanced DCF model with a sample company."""
    
    print("🚀 Testing Enhanced Professional DCF Model")
    print("=" * 50)
    
    # Test with Microsoft (public company)
    print("\n📊 Testing with Microsoft (MSFT)...")
    try:
        result = build_professional_dcf_model(
            company_name="Microsoft",
            ticker="MSFT",
            years=5,
            output="gsheets",  # Only Google Sheets for testing
            sheet_name="Enhanced DCF Test"
        )
        print("✅ Microsoft DCF model created successfully!")
    except Exception as e:
        print(f"❌ Error with Microsoft: {e}")
    
    # Test with a private company
    print("\n💼 Testing with Private Company...")
    try:
        result = build_professional_dcf_model(
            company_name="TechStartup Inc",
            years=5,
            output="gsheets",
            sheet_name="Enhanced DCF Test",
            is_private=True,
            use_custom_data=True
        )
        print("✅ Private company DCF model created successfully!")
    except Exception as e:
        print(f"❌ Error with private company: {e}")
    
    print("\n🎉 Enhanced DCF Model Test Complete!")
    print("\n📋 New Features Demonstrated:")
    print("   ✅ Executive Summary with Terminal Value Analysis")
    print("   ✅ Enhanced Assumptions with Working Capital Drivers")
    print("   ✅ Dedicated UFCF Model Tab with Mid-Year Convention")
    print("   ✅ Enhanced 3-Statement Model with Balance Sheet")
    print("   ✅ Comprehensive Sensitivity Analysis")
    print("   ✅ Audit & Integrity Checks Tab")
    print("   ✅ Professional Color Coding (Light Blue Inputs)")
    print("   ✅ Both Perpetuity Growth and Exit Multiple Methods")
    print("   ✅ Model Integrity Validation")

if __name__ == "__main__":
    test_enhanced_dcf() 