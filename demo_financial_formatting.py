#!/usr/bin/env python3
"""
Demo script showing the enhanced financial formatting and data extraction
"""

from professional_dcf_model import (
    format_financial_value,
    format_percentage,
    get_financial_data_with_fallbacks
)

def demo_financial_formatting():
    """Demonstrate the enhanced financial formatting"""
    print("🏦 Enhanced Financial Formatting Demo")
    print("=" * 50)

    # Test values
    test_companies = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

    for ticker in test_companies:
        print(f"\n📊 {ticker} Financial Data:")
        print("-" * 30)

        # Get financial data
        revenue = get_financial_data_with_fallbacks(ticker, 'revenue')
        ebitda = get_financial_data_with_fallbacks(ticker, 'ebitda')
        ebit = get_financial_data_with_fallbacks(ticker, 'ebit')
        nopat = get_financial_data_with_fallbacks(ticker, 'nopat')

        # Display with formatting
        print(f"  Revenue:  {format_financial_value(revenue, color=False) if revenue else 'N/A'}")
        print(f"  EBITDA:   {format_financial_value(ebitda, color=False) if ebitda else 'N/A'}")
        print(f"  EBIT:     {format_financial_value(ebit, color=False) if ebit else 'N/A'}")
        print(f"  NOPAT:    {format_financial_value(nopat, color=False) if nopat else 'N/A'}")

        # Calculate and display margins
        if revenue and ebitda:
            ebitda_margin = ebitda / revenue
            print(f"  EBITDA Margin: {format_percentage(ebitda_margin, color=False)}")

def demo_color_formatting():
    """Demonstrate color formatting for HTML output"""
    print("\n\n🌈 Color Formatting Demo (HTML)")
    print("=" * 50)

    test_values = [
        ("Revenue", 100000000000),  # 100B
        ("EBITDA", 25000000000),    # 25B
        ("EBIT", 20000000000),      # 20B
        ("NOPAT", 15000000000),     # 15B
        ("Loss", -5000000000),      # -5B
    ]

    for label, value in test_values:
        html_formatted = format_financial_value(value, color=True)
        print(f"{label:12}: {html_formatted}")

if __name__ == "__main__":
    demo_financial_formatting()
    demo_color_formatting()

    print("\n\n✅ Demo Complete!")
    print("🎯 Your financial models now include:")
    print("   • Enhanced data extraction with fallbacks")
    print("   • Proper financial formatting (B, M, K suffixes)")
    print("   • Comma-separated thousands")
    print("   • Color-coded positive/negative values")
    print("   • Zero-value handling")
