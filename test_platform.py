#!/usr/bin/env python3
"""
Quick test of the FinModAI platform.
"""

import sys
sys.path.insert(0, '.')

from finmodai_platform import FinModAIPlatform

def test_platform():
    print("🚀 Testing FinModAI Platform")
    print("=" * 50)

    try:
        # Initialize platform
        platform = FinModAIPlatform()
        print("✅ Platform initialized successfully!")

        # Test data ingestion
        print("\n📊 Testing data ingestion...")
        data = platform.data_engine.get_company_data('AAPL')

        if data:
            print("✅ Apple data retrieved:")
            print(f"   Revenue: ${data.revenue:,.0f}M")
            print(f"   EBITDA: ${data.ebitda:,.0f}M")
            print(f"   Beta: {data.beta:.2f}")
            print(f"   Net Debt: ${data.total_debt - data.cash_and_equivalents:,.0f}M")
        else:
            print("❌ Data retrieval failed")

        # Test model generation
        print("\n🤖 Testing model generation...")
        result = platform.generate_model('dcf', 'AAPL')

        if result['success']:
            print("✅ DCF model generated successfully!")
            outputs = result['outputs']
            print("   Valuation Results:")
            print(f"   Enterprise Value: ${outputs.get('enterprise_value', 0):,.0f}M")
            print(f"   Equity Value: ${outputs.get('equity_value', 0):,.0f}M")
            print(f"   Implied Price: ${outputs.get('implied_price', 0):.2f}")
            print(f"   WACC: {outputs.get('wacc', 0):.1%}")

            print(f"   Generated files: {len(result['output_files'])}")
            for file in result['output_files']:
                print(f"   📁 {file}")
        else:
            print(f"❌ Model generation failed: {result['error']}")

        print("\n🎉 FinModAI Platform Test Complete!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_platform()
    sys.exit(0 if success else 1)
