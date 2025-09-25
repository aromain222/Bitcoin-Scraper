#!/usr/bin/env python3
"""
Simple DCF Model Generator
Generates DCF models and prints results directly to console
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from finmodai_platform import FinModAIPlatform
    print("FinModAI Platform imported successfully")
except ImportError as e:
    print(f"Error importing FinModAI Platform: {e}")
    sys.exit(1)

def generate_dcf_model(ticker):
    """Generate a DCF model and return results"""
    print(f"Generating DCF Model for {ticker}")
    print("=" * 50)

    try:
        # Initialize platform
        print("📊 DEBUG: About to create FinModAIPlatform")
        platform = FinModAIPlatform()
        print("📊 DEBUG: Platform initialized successfully")

        # Debug: Check what data is being pulled
        print("🔍 DEBUG: Testing data retrieval...")
        data_engine = platform.data_engine
        test_data = data_engine.get_company_data(ticker)
        if test_data:
            print(f"📊 Raw Financial Data for {ticker}:")
            print(f"   Company: {test_data.company_name}")
            print(f"   Market Cap: ${test_data.market_cap/1_000_000_000:.1f}B")
            print(f"   Revenue: ${test_data.revenue:.1f}B")
            print(f"   Net Income: ${test_data.net_income:.1f}B")
            print(f"   EBITDA: ${test_data.ebitda:.1f}B")
            print(f"   Shares Outstanding: {test_data.shares_outstanding/1_000_000:.1f}M")
            print(f"   Beta: {test_data.beta}")
            print(f"   Sector: {test_data.sector}")
            print(f"   Data Quality: {test_data.data_quality_score}%")
        else:
            print("❌ No data retrieved")

        # Generate model
        print(f"📊 DEBUG: About to call platform.generate_model")
        result = platform.generate_model(
            model_type="dcf",
            company_identifier=ticker
        )
        print(f"📊 DEBUG: platform.generate_model returned")

        print("Model generated successfully")

        # Print key results
        if result.get('success', False):
            print("DCF MODEL RESULTS")
            print("=" * 30)

            # Print model summary
            summary = result.get('model_summary', {})
            if summary:
                print(f"Company: {summary.get('company', 'N/A')}")
                print(f"Model Type: {summary.get('model_type', 'N/A').upper()}")
                print(f"Processing Time: {result.get('processing_time_seconds', 0):.1f}s")

                # Print key assumptions
                assumptions = summary.get('key_assumptions', {})
                if assumptions:
                    print("Key Assumptions:")
                    print(f"   • Revenue Growth: {assumptions.get('revenue_growth', 0)*100:.1f}%")
                    print(f"   • WACC: {assumptions.get('wacc', 0)*100:.1f}%")
                    print(f"   • Terminal Growth: {assumptions.get('terminal_growth', 0)*100:.1f}%")

                # Print valuation outputs
                outputs = summary.get('valuation_outputs', {})
                if outputs:
                    print("Valuation Outputs:")
                    print(f"   • Enterprise Value: ${outputs.get('enterprise_value', 0)/1_000_000_000:.1f}B")
                    print(f"   • Equity Value: ${outputs.get('equity_value', 0)/1_000_000_000:.1f}B")
                    print(f"   • Implied Price: ${outputs.get('implied_price', 0):.2f}")

            # Print output files
            output_files = result.get('output_files', [])
            if output_files:
                print("Output Files:")
                for file in output_files:
                    print(f"   • {file}")

                print("Excel model saved and ready for analysis!")
            else:
                print("No Excel file was generated (UI issue - model data is still valid)")
        else:
            print(f"Model generation failed: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        print(f"Error generating model: {e}")
        return None

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python simple_dcf_generator.py <ticker>")
        print("Example: python simple_dcf_generator.py AAPL")
        print("Example: python simple_dcf_generator.py APPL  # Auto-corrects to AAPL")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    print("DCF Model Generator v1.0")
    print(f"Ticker: {ticker}")

    result = generate_dcf_model(ticker)

    if result and result.get('success', False):
        print("SUCCESS: Model generated successfully!")
        print(f"Your DCF model for {ticker} is ready!")
        output_files = result.get('output_files', [])
        if output_files:
            print(f"📊 Check the generated Excel file: {output_files[0]}")
        else:
            print("📊 No Excel file generated (check the debug output above)")
    else:
        print("FAILED: Could not generate model")
        print("Try with a different ticker or check the error messages above")

if __name__ == "__main__":
    main()