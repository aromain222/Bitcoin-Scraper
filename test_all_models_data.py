#!/usr/bin/env python3
"""
Comprehensive test to verify all financial models have proper data extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from professional_dcf_model import (
    get_comprehensive_financials,
    format_financial_value,
    get_financial_data_with_fallbacks
)

def test_company_data(ticker, company_name):
    """Test data extraction for a single company"""
    print(f"\n🏢 Testing {company_name} ({ticker})")
    print("=" * 50)

    try:
        # Test individual data points
        print("📊 Individual Data Points:")
        revenue = get_financial_data_with_fallbacks(ticker, 'revenue')
        ebitda = get_financial_data_with_fallbacks(ticker, 'ebitda')
        ebit = get_financial_data_with_fallbacks(ticker, 'ebit')
        nopat = get_financial_data_with_fallbacks(ticker, 'nopat')

        print(f"  Revenue:  {format_financial_value(revenue, color=False) if revenue else '❌ N/A'}")
        print(f"  EBITDA:   {format_financial_value(ebitda, color=False) if ebitda else '❌ N/A'}")
        print(f"  EBIT:     {format_financial_value(ebit, color=False) if ebit else '❌ N/A'}")
        print(f"  NOPAT:    {format_financial_value(nopat, color=False) if nopat else '❌ N/A'}")

        # Test comprehensive financials
        print("\n📈 Comprehensive Financial Data:")
        financial_data = get_comprehensive_financials(ticker, years=3)

        if financial_data:
            rev = financial_data.get('Revenue', [0])[-1]
            ebitda_val = financial_data.get('EBITDA', [0])[-1]
            ebit_val = financial_data.get('EBIT', [0])[-1]
            nopat_val = financial_data.get('NOPAT', [0])[-1]

            print(f"  Revenue:  {format_financial_value(rev, color=False) if rev else '❌ N/A'}")
            print(f"  EBITDA:   {format_financial_value(ebitda_val, color=False) if ebitda_val else '❌ N/A'}")
            print(f"  EBIT:     {format_financial_value(ebit_val, color=False) if ebit_val else '❌ N/A'}")
            print(f"  NOPAT:    {format_financial_value(nopat_val, color=False) if nopat_val else '❌ N/A'}")

            # Check if all values are non-zero
            all_good = all([rev, ebitda_val, ebit_val, nopat_val])
            status = "✅ PASS" if all_good else "❌ FAIL"
            print(f"\n{status}: All financial metrics have data")

            return all_good
        else:
            print("❌ FAIL: No financial data retrieved")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE FINANCIAL DATA TEST")
    print("=" * 60)
    print("Testing data extraction for multiple companies and models")
    print("=" * 60)

    # Test companies from different industries
    test_companies = [
        ('AAPL', 'Apple Inc.'),
        ('MSFT', 'Microsoft Corporation'),
        ('GOOGL', 'Alphabet Inc.'),
        ('TSLA', 'Tesla Inc.'),
        ('NVDA', 'NVIDIA Corporation'),
        ('AMZN', 'Amazon.com Inc.'),
        ('META', 'Meta Platforms Inc.'),
        ('NFLX', 'Netflix Inc.'),
    ]

    results = []
    total_tests = len(test_companies)

    for ticker, company_name in test_companies:
        success = test_company_data(ticker, company_name)
        results.append((ticker, success))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    failed = total_tests - passed

    print(f"Total Companies Tested: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(".1f")

    if failed > 0:
        print("\n❌ Companies with issues:")
        for ticker, success in results:
            if not success:
                print(f"  - {ticker}")

    print("\n" + "=" * 60)
    if passed == total_tests:
        print("🎉 ALL TESTS PASSED! Financial data extraction is working perfectly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    print("=" * 60)

if __name__ == "__main__":
    main()
