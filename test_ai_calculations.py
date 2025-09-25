#!/usr/bin/env python3
"""
Test script to demonstrate the AI-powered financial calculation system.
"""

import sys
import os

# Add the current directory to the path so we can import our functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_calculations():
    """Test the AI calculation system with various scenarios."""

    print("🧮 TESTING AI-POWERED FINANCIAL CALCULATIONS")
    print("=" * 60)

    # Test data derivation for a company with limited data
    test_data_1 = {
        'Company Name': 'TechStart Inc',
        'Industry': 'Technology',
        'Revenue': [100000000],  # $100M revenue
        'Current Price': 15.0,   # $15 share price
        'Shares Outstanding': 50000000,  # 50M shares
    }

    print("\n📊 Test Case 1: Limited Data Company")
    print(f"Input: {test_data_1}")

    try:
        from professional_dcf_model import derive_missing_financial_data

        enhanced_data = derive_missing_financial_data(test_data_1, 'TechStart Inc')

        print("\n✅ Derived Data:")
        for key, value in enhanced_data.items():
            if key not in test_data_1:
                print(f"   {key}: {value}")

    except ImportError as e:
        print(f"❌ Import error: {e}")

    # Test data derivation for a company with market cap data
    test_data_2 = {
        'Company Name': 'GrowthCo Ltd',
        'Industry': 'Healthcare',
        'Market Cap': 5000000000,  # $5B market cap
        'Net Income': 200000000,   # $200M net income
    }

    print("\n\n📊 Test Case 2: Market Cap Focused Company")
    print(f"Input: {test_data_2}")

    try:
        enhanced_data_2 = derive_missing_financial_data(test_data_2, 'GrowthCo Ltd')

        print("\n✅ Derived Data:")
        for key, value in enhanced_data_2.items():
            if key not in test_data_2:
                print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test AI calculation for missing metrics
    test_data_3 = {
        'Company Name': 'IndustrialCorp',
        'Industry': 'Industrials',
        'Revenue': [2000000000],
        'EBITDA': [400000000],
        'Net Income': [150000000],
    }

    print("\n\n📊 Test Case 3: AI Calculation for Ratios")
    print(f"Input: {test_data_3}")

    try:
        from professional_dcf_model import calculate_missing_cell_formula

        # Test P/E ratio calculation
        pe_ratio = calculate_missing_cell_formula('P/E Ratio', test_data_3)
        print(f"✅ Calculated P/E Ratio: {pe_ratio}")

        # Test EBITDA margin
        ebitda_margin = calculate_missing_cell_formula('EBITDA Margin', test_data_3)
        print(f"✅ Calculated EBITDA Margin: {ebitda_margin}%")

        # Test missing Free Cash Flow
        fcf = calculate_missing_cell_formula('Free Cash Flow', test_data_3)
        print(f"✅ Estimated Free Cash Flow: ${fcf:,.0f}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("🎉 AI CALCULATION SYSTEM TEST COMPLETED")
    print("💡 The system intelligently derives missing financial data")
    print("   using industry norms, financial relationships, and AI analysis!")

if __name__ == "__main__":
    test_ai_calculations()
