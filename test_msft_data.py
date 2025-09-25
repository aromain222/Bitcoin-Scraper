#!/usr/bin/env python3
"""
Quick test to show Microsoft financial data from FinModAI platform
"""

from finmodai.data_ingestion import DataIngestionEngine
from finmodai_platform import PlatformConfig

def main():
    print("🎯 TESTING MICROSOFT DATA RETRIEVAL")
    print("=" * 50)

    config = PlatformConfig()
    engine = DataIngestionEngine(config)
    data = engine.get_company_data('MSFT')

    if data:
        print("✅ MICROSOFT FINANCIAL DATA RETRIEVED:")
        print(f"   📊 Company: {data.company_name}")
        print(f"   💰 Revenue: ${data.revenue:,.0f}M")
        print(f"   📈 EBITDA: ${data.ebitda:,.0f}M")
        print(f"   💸 Net Income: ${data.net_income:,.0f}M")
        print(f"   📊 Beta: {data.beta:.2f}")
        print(f"   🏢 Sector: {data.sector}")
        print(f"   📈 Market Cap: ${data.market_cap:,.0f}M")
        print(f"   📊 Shares Outstanding: {data.shares_outstanding:,.0f}M")
        print(f"   🔍 Data Source: {data.data_source}")
        print(f"   ⭐ Quality Score: {data.data_quality_score}/100")
        print(f"   📅 Last Updated: {data.last_updated}")
    else:
        print("❌ Failed to retrieve Microsoft data")

    print("\n" + "=" * 50)
    print("🎉 FinModAI Microsoft Test Complete!")

if __name__ == "__main__":
    main()
