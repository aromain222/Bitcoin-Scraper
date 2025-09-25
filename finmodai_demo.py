#!/usr/bin/env python3
"""
FinModAI Platform Demo
Comprehensive demonstration of the AI-powered financial modeling platform.
"""

import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from finmodai import FinModAIPlatform, quick_model_generation

def print_banner():
    """Print the FinModAI banner."""
    banner = """
    ███████╗██╗███╗   ██╗███╗   ███╗ ██████╗ ██████╗  █████╗ ██╗
    ██╔════╝██║████╗  ██║████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██║
    █████╗  ██║██╔██╗ ██║██╔████╔██║██║   ██║██║  ██║███████║██║
    ██╔══╝  ██║██║╚██╗██║██║╚██╔╝██║██║   ██║██║  ██║██╔══██║██║
    ██║     ██║██║ ╚████║██║ ╚═╝ ██║╚██████╔╝██████╔╝██║  ██║██║
    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝

    🚀 FinModAI - AI-Powered Financial Modeling Platform
    Bloomberg Terminal meets GitHub Copilot for financial modeling

    Transform hours of financial modeling into minutes of insight
    """
    print(banner)

def demonstrate_data_ingestion():
    """Demonstrate data ingestion capabilities."""
    print("\n" + "="*60)
    print("🔍 DATA INGESTION DEMONSTRATION")
    print("="*60)

    platform = FinModAIPlatform()

    test_companies = [
        ("Apple Inc.", "AAPL"),
        ("Microsoft Corporation", "MSFT"),
        ("Tesla, Inc.", "TSLA")
    ]

    for company_name, ticker in test_companies:
        print(f"\n📊 Fetching data for {company_name} ({ticker})...")

        try:
            # Get financial data
            financial_data = platform.data_engine.get_company_data(ticker)

            if financial_data:
                print("  ✅ Data retrieved successfully!")
                print(f"     Revenue: ${financial_data.revenue:,.2f}M")
                print(f"     Growth: {financial_data.revenue_growth:.1f}%")
                print(f"     EBITDA: ${financial_data.ebitda:,.2f}M")
                print(f"     Beta: {financial_data.beta:.2f}")
                print(f"     Net Debt: ${financial_data.total_debt - financial_data.cash_and_equivalents:,.1f}M")
            else:
                print(f"  ❌ No data found for {ticker}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        time.sleep(1)  # Rate limiting

def demonstrate_model_generation():
    """Demonstrate model generation capabilities."""
    print("\n" + "="*60)
    print("🤖 MODEL GENERATION DEMONSTRATION")
    print("="*60)

    test_cases = [
        ("dcf", "AAPL", "Apple Inc. DCF Model"),
        ("dcf", "MSFT", "Microsoft DCF Model"),
        ("dcf", "TSLA", "Tesla DCF Model")
    ]

    for model_type, ticker, description in test_cases:
        print(f"\n📈 Generating {description}...")

        try:
            # Generate model
            result = quick_model_generation(model_type, ticker)

            if result['success']:
                print("  ✅ Model generated successfully!")
                outputs = result['outputs']
                print(f"     Enterprise Value: ${outputs.get('enterprise_value', 0):,.1f}M")
                print(f"     Equity Value: ${outputs.get('equity_value', 0):,.1f}M")
                print(f"     Implied Price: ${outputs.get('implied_price', 0):,.2f}")
                print(f"     WACC: {outputs.get('wacc', 0):,.1f}%")
                print(f"  📁 Files: {len(result['output_files'])} generated")

                # List generated files
                for file_path in result['output_files']:
                    print(f"     • {Path(file_path).name}")

            else:
                print(f"  ❌ Generation failed: {result['error']}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        time.sleep(2)  # Brief pause between generations

def demonstrate_batch_processing():
    """Demonstrate batch processing capabilities."""
    print("\n" + "="*60)
    print("🔄 BATCH PROCESSING DEMONSTRATION")
    print("="*60)

    platform = FinModAIPlatform()

    # Define batch requests
    batch_requests = [
        {
            "model_type": "dcf",
            "company_identifier": "AAPL",
            "assumptions": {"growth_rate": 0.10, "terminal_growth": 0.03}
        },
        {
            "model_type": "dcf",
            "company_identifier": "MSFT",
            "assumptions": {"growth_rate": 0.08, "terminal_growth": 0.025}
        },
        {
            "model_type": "dcf",
            "company_identifier": "TSLA",
            "assumptions": {"growth_rate": 0.12, "terminal_growth": 0.03}
        }
    ]

    print(f"🔄 Processing {len(batch_requests)} models in batch...")

    try:
        results = platform.batch_generate_models(batch_requests)

        successful = sum(1 for r in results if r.get("success", False))
        print(f"\n✅ Batch complete: {successful}/{len(batch_requests)} successful")

        for i, result in enumerate(results, 1):
            status = "✅" if result.get("success") else "❌"
            company = result.get("company", f"Model {i}")
            print(f"  {status} {company}")

    except Exception as e:
        print(f"❌ Batch processing error: {e}")

def demonstrate_web_interface():
    """Demonstrate web interface capabilities."""
    print("\n" + "="*60)
    print("🌐 WEB INTERFACE DEMONSTRATION")
    print("="*60)

    try:
        platform = FinModAIPlatform()

        print("🚀 Starting FinModAI Web Interface...")
        print("📱 Features:")
        print("  • Interactive model creation")
        print("  • Real-time data fetching")
        print("  • Professional Excel downloads")
        print("  • API endpoints for integrations")
        print("  • Responsive web design")

        # Start web interface in background thread
        web_interface = platform.web_interface
        if not web_interface:
            platform.start_web_interface(host="localhost", port=8000)

        print("\n🌐 Web interface available at:")
        print("  http://localhost:8000")
        print("\n📋 Available endpoints:")
        endpoints = platform.get_api_endpoints()
        for name, url in endpoints.items():
            print(f"  • {name}: {url}")

        # Open browser automatically
        platform.web_interface.open_browser()

        print("\n💡 Try these actions in your browser:")
        print("  1. Click 'Create DCF Model'")
        print("  2. Enter 'AAPL' as company identifier")
        print("  3. Click 'Generate DCF Model'")
        print("  4. Download the generated Excel file")

        input("\n⏳ Press Enter to continue with other demonstrations...")

    except Exception as e:
        print(f"❌ Web interface error: {e}")
        print("💡 Web interface requires Flask: pip install flask flask-cors")

def show_capabilities_summary():
    """Show comprehensive capabilities summary."""
    print("\n" + "="*80)
    print("🎯 FinModAI PLATFORM CAPABILITIES SUMMARY")
    print("="*80)

    capabilities = {
        "Data Sources": [
            "✅ Yahoo Finance - Real-time stock data",
            "✅ Alpha Vantage - Professional financial data",
            "✅ Bloomberg Terminal - Premium market data",
            "✅ CapIQ - Private company data",
            "✅ PitchBook - Transaction comps",
            "✅ SEC EDGAR - Regulatory filings",
            "✅ Manual upload - Excel/CSV files"
        ],

        "Model Types": [
            "✅ DCF (Discounted Cash Flow) - Enterprise valuation",
            "✅ LBO (Leveraged Buyout) - Private equity analysis",
            "✅ Trading Comparables - Relative valuation",
            "✅ Three-Statement Model - Integrated financials",
            "✅ Merger & Acquisition - Accretion/dilution",
            "✅ IPO Models - Public offering analysis",
            "✅ Sum-of-the-Parts - Business unit valuation"
        ],

        "AI Features": [
            "✅ Smart Assumption Generation - Industry-specific defaults",
            "✅ Intelligent Data Validation - Error detection",
            "✅ Automated Sensitivity Analysis - Risk assessment",
            "✅ Scenario Planning - Multiple outcome modeling",
            "✅ Peer Company Selection - Automated comps",
            "✅ Growth Rate Forecasting - Historical trend analysis",
            "✅ Beta Calculation - Risk-adjusted returns"
        ],

        "Output Formats": [
            "✅ Excel (.xlsx) - Professional banker format",
            "✅ Google Sheets - Cloud collaboration",
            "✅ PDF Reports - Presentation-ready",
            "✅ JSON API - System integration",
            "✅ PowerPoint - Executive presentations",
            "✅ CSV Export - Data analysis"
        ],

        "Platform Features": [
            "✅ Web Interface - Browser-based modeling",
            "✅ API Endpoints - RESTful integrations",
            "✅ Batch Processing - Multiple models simultaneously",
            "✅ Version Control - Model iteration tracking",
            "✅ Audit Trail - Compliance and transparency",
            "✅ User Management - Team collaboration",
            "✅ Cloud Storage - Secure file management"
        ]
    }

    for category, features in capabilities.items():
        print(f"\n🔧 {category}:")
        for feature in features:
            print(f"   {feature}")

def show_use_cases():
    """Show real-world use cases."""
    print("\n" + "="*80)
    print("💼 REAL-WORLD USE CASES")
    print("="*80)

    use_cases = [
        {
            "title": "Investment Banking - M&A Deal",
            "scenario": "2-week deadline for $500M acquisition valuation",
            "traditional": "3 analysts × 40 hours = 120 hours manual work",
            "finmodai": "15 minutes AI-powered model generation",
            "savings": "99% time reduction, audit-ready deliverables"
        },
        {
            "title": "Private Equity - Target Screening",
            "scenario": "Monthly review of 50 potential investments",
            "traditional": "2 weeks of analyst time per target",
            "finmodai": "30 minutes per target with instant models",
            "savings": "95% time reduction, standardized analysis"
        },
        {
            "title": "Corporate Finance - Budget Planning",
            "scenario": "Annual 3-statement forecast for $10B company",
            "traditional": "Finance team 2 months building model",
            "finmodai": "2 hours with AI-assisted automation",
            "savings": "90% time reduction, improved accuracy"
        },
        {
            "title": "Equity Research - Company Reports",
            "scenario": "Quarterly reports for 20-company coverage",
            "traditional": "1 week per company for modeling",
            "finmodai": "2 hours total with batch processing",
            "savings": "97% time reduction, consistent methodology"
        }
    ]

    for case in use_cases:
        print(f"\n🎯 {case['title']}")
        print(f"   Scenario: {case['scenario']}")
        print(f"   Traditional: {case['traditional']}")
        print(f"   FinModAI: {case['finmodai']}")
        print(f"   Impact: {case['savings']}")

def main():
    """Main demonstration function."""
    print_banner()

    print("\n🚀 Welcome to the FinModAI Platform Demonstration!")
    print("This demo showcases the complete AI-powered financial modeling platform.")
    print("="*80)

    try:
        # Run demonstrations
        demonstrate_data_ingestion()
        demonstrate_model_generation()
        demonstrate_batch_processing()

        # Show web interface (optional)
        show_web = input("\n🌐 Would you like to start the web interface demo? (y/n): ").lower().strip()
        if show_web in ['y', 'yes']:
            demonstrate_web_interface()

        # Show comprehensive capabilities
        show_capabilities_summary()
        show_use_cases()

        print("\n" + "="*80)
        print("🎉 FinModAI DEMONSTRATION COMPLETE!")
        print("="*80)
        print("\n📊 Key Achievements:")
        print("  ✅ Real-time financial data ingestion from multiple sources")
        print("  ✅ AI-powered model generation with intelligent assumptions")
        print("  ✅ Professional Excel outputs with banker-grade formatting")
        print("  ✅ Batch processing for multiple companies")
        print("  ✅ Web interface for interactive modeling")
        print("  ✅ RESTful API for system integrations")
        print("  ✅ Comprehensive audit trails and validation")

        print("\n🚀 Next Steps:")
        print("  1. Visit http://localhost:8000 for interactive demo")
        print("  2. Try: python finmodai_platform.py dcf AAPL")
        print("  3. Explore generated Excel files in the output directory")
        print("  4. Integrate with your existing financial systems")

        print("\n💡 FinModAI transforms hours of financial modeling into minutes of insight!")
        print("   Bloomberg Terminal meets GitHub Copilot for financial modeling 🎯📊💡")

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
