#!/usr/bin/env python3
"""
DCF Demo - Interactive Company DCF Generator
Shows how to generate DCF models for any public company.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quick_dcf_generator import generate_dcf_for_ticker

def main():
    print("🚀 Company DCF Generator Demo")
    print("=" * 50)
    print("Generate professional DCF models with real financial data")
    print()

    while True:
        print("Popular companies to try:")
        print("  AAPL - Apple Inc.")
        print("  MSFT - Microsoft Corporation")
        print("  GOOGL - Alphabet (Google)")
        print("  AMZN - Amazon")
        print("  TSLA - Tesla")
        print("  NVDA - NVIDIA")
        print("  META - Meta Platforms")
        print("  NFLX - Netflix")
        print()

        ticker = input("Enter a stock ticker (or 'quit' to exit): ").strip().upper()

        if ticker in ['QUIT', 'EXIT', 'Q']:
            print("👋 Goodbye!")
            break

        if not ticker:
            print("❌ Please enter a valid ticker")
            continue

        try:
            print(f"\n{'='*50}")
            filename = generate_dcf_for_ticker(ticker)
            if filename:
                print(f"\n🎉 Success! Your DCF model is ready:")
                print(f"   📁 {filename}")
                print("   📊 Open in Excel to view the complete analysis")
            else:
                print("❌ Could not generate DCF model for this ticker")
        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "="*50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line usage
        ticker = sys.argv[1].upper()
        print(f"Generating DCF for {ticker}...")
        generate_dcf_for_ticker(ticker)
    else:
        # Interactive mode
        main()
