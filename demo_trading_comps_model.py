#!/usr/bin/env python3
"""
Trading Comparables Model Demonstration
Shows how to use the Professional Trading Comps Model with different industries and peer groups
"""

from professional_trading_comps_model import ProfessionalTradingCompsModel

def demo_technology_sector_comps():
    """Demo: Technology Sector Trading Comparables"""
    print("🔥 Demo: Technology Sector Trading Comparables")
    print("=" * 60)

    model = ProfessionalTradingCompsModel("CloudTech Corp.", "CLOUDTECH")

    # Technology sector peers with higher valuations
    results, excel_file = model.run_trading_comps_model(
        # Target Company Data
        target_revenue=1500.0,      # $1.5B revenue
        target_ebitda=450.0,        # $450M EBITDA (30% margin)
        target_net_income=270.0,    # $270M net income
        target_eps=4.50,            # $4.50 EPS
        target_net_debt=150.0,      # $150M net debt (conservative)
        target_shares_outstanding=60.0,  # 60M shares

        # Technology Peer Group
        peer_names=["SaaS Leader Inc", "Cloud Platform Ltd", "DataTech Corp", "Software Plus LLC", "Tech Services Inc"],
        peer_tickers=["SAAS", "CLOUD", "DATA", "SOFT", "TECH"],
        peer_revenues=[1200.0, 1800.0, 800.0, 2200.0, 1600.0],      # $M
        peer_ebitdas=[360.0, 540.0, 240.0, 660.0, 480.0],          # $M
        peer_net_incomes=[216.0, 324.0, 144.0, 396.0, 288.0],      # $M
        peer_epss=[3.60, 5.40, 2.40, 6.60, 4.80],                  # $
        peer_net_debts=[120.0, 180.0, 80.0, 220.0, 160.0],         # $M
        peer_shares_outstanding=[60.0, 60.0, 60.0, 60.0, 60.0],   # Million shares
        peer_share_prices=[72.0, 108.0, 48.0, 132.0, 96.0]        # $ (higher valuations)
    )

    return results, excel_file

def demo_manufacturing_sector_comps():
    """Demo: Manufacturing Sector Trading Comparables"""
    print("\n🔧 Demo: Manufacturing Sector Trading Comparables")
    print("=" * 60)

    model = ProfessionalTradingCompsModel("IndustCo Inc.", "INDUST")

    # Manufacturing peers with moderate valuations
    results, excel_file = model.run_trading_comps_model(
        # Target Company Data
        target_revenue=800.0,        # $800M revenue
        target_ebitda=160.0,         # $160M EBITDA (20% margin)
        target_net_income=80.0,      # $80M net income
        target_eps=2.00,             # $2.00 EPS
        target_net_debt=240.0,       # $240M net debt
        target_shares_outstanding=40.0,  # 40M shares

        # Manufacturing Peer Group
        peer_names=["AutoParts Corp", "MetalWorks Inc", "Chemicals Plus", "Equipment Mfg", "Indust Supply"],
        peer_tickers=["AUTOP", "METAL", "CHEM", "EQUIP", "SUPPLY"],
        peer_revenues=[600.0, 1000.0, 700.0, 1200.0, 900.0],      # $M
        peer_ebitdas=[120.0, 200.0, 140.0, 240.0, 180.0],         # $M
        peer_net_incomes=[60.0, 100.0, 70.0, 120.0, 90.0],        # $M
        peer_epss=[1.50, 2.50, 1.75, 3.00, 2.25],                 # $
        peer_net_debts=[180.0, 300.0, 210.0, 360.0, 270.0],       # $M
        peer_shares_outstanding=[40.0, 40.0, 40.0, 40.0, 40.0],   # Million shares
        peer_share_prices=[30.0, 50.0, 35.0, 60.0, 45.0]          # $
    )

    return results, excel_file

def demo_consumer_sector_comps():
    """Demo: Consumer Sector Trading Comparables"""
    print("\n🛍️  Demo: Consumer Sector Trading Comparables")
    print("=" * 60)

    model = ProfessionalTradingCompsModel("RetailMax Corp.", "RETAIL")

    # Consumer/retail peers with lower valuations
    results, excel_file = model.run_trading_comps_model(
        # Target Company Data
        target_revenue=2500.0,       # $2.5B revenue
        target_ebitda=250.0,         # $250M EBITDA (10% margin)
        target_net_income=125.0,     # $125M net income
        target_eps=2.50,             # $2.50 EPS
        target_net_debt=500.0,       # $500M net debt
        target_shares_outstanding=50.0,  # 50M shares

        # Consumer Peer Group
        peer_names=["Fashion Retail", "Home Goods Inc", "Sports Store", "Electronics Plus", "Department Store"],
        peer_tickers=["FASHION", "HOME", "SPORTS", "ELECT", "DEPT"],
        peer_revenues=[2000.0, 3000.0, 1500.0, 3500.0, 2500.0],   # $M
        peer_ebitdas=[200.0, 300.0, 150.0, 350.0, 250.0],         # $M
        peer_net_incomes=[100.0, 150.0, 75.0, 175.0, 125.0],      # $M
        peer_epss=[2.00, 3.00, 1.50, 3.50, 2.50],                 # $
        peer_net_debts=[400.0, 600.0, 300.0, 700.0, 500.0],       # $M
        peer_shares_outstanding=[50.0, 50.0, 50.0, 50.0, 50.0],   # Million shares
        peer_share_prices=[40.0, 60.0, 30.0, 70.0, 50.0]          # $
    )

    return results, excel_file

def demo_healthcare_sector_comps():
    """Demo: Healthcare Sector Trading Comparables"""
    print("\n🏥 Demo: Healthcare Sector Trading Comparables")
    print("=" * 60)

    model = ProfessionalTradingCompsModel("MediCorp Inc.", "MEDI")

    # Healthcare peers with stable valuations
    results, excel_file = model.run_trading_comps_model(
        # Target Company Data
        target_revenue=1200.0,       # $1.2B revenue
        target_ebitda=240.0,         # $240M EBITDA (20% margin)
        target_net_income=144.0,     # $144M net income
        target_eps=2.88,             # $2.88 EPS
        target_net_debt=360.0,       # $360M net debt
        target_shares_outstanding=50.0,  # 50M shares

        # Healthcare Peer Group
        peer_names=["Hospital Chain", "Clinic Group Inc", "MedTech Corp", "Pharma Services", "Health Systems"],
        peer_tickers=["HOSP", "CLINIC", "MEDTECH", "PHARMA", "HEALTH"],
        peer_revenues=[1000.0, 1400.0, 800.0, 1600.0, 1200.0],    # $M
        peer_ebitdas=[200.0, 280.0, 160.0, 320.0, 240.0],         # $M
        peer_net_incomes=[120.0, 168.0, 96.0, 192.0, 144.0],      # $M
        peer_epss=[2.40, 3.36, 1.92, 3.84, 2.88],                 # $
        peer_net_debts=[300.0, 420.0, 240.0, 480.0, 360.0],       # $M
        peer_shares_outstanding=[50.0, 50.0, 50.0, 50.0, 50.0],   # Million shares
        peer_share_prices=[48.0, 67.2, 38.4, 76.8, 57.6]          # $
    )

    return results, excel_file

def demo_energy_sector_comps():
    """Demo: Energy Sector Trading Comparables"""
    print("\n⚡ Demo: Energy Sector Trading Comparables")
    print("=" * 60)

    model = ProfessionalTradingCompsModel("EnergyCorp Ltd.", "ENERGY")

    # Energy peers with cyclical valuations
    results, excel_file = model.run_trading_comps_model(
        # Target Company Data
        target_revenue=1800.0,       # $1.8B revenue
        target_ebitda=360.0,         # $360M EBITDA (20% margin)
        target_net_income=180.0,     # $180M net income
        target_eps=3.60,             # $3.60 EPS
        target_net_debt=720.0,       # $720M net debt (higher leverage)
        target_shares_outstanding=50.0,  # 50M shares

        # Energy Peer Group
        peer_names=["Oil & Gas Inc", "Pipeline Corp", "Refinery Ltd", "Exploration Co", "Energy Services"],
        peer_tickers=["OILGAS", "PIPE", "REFINE", "EXPLORE", "ENERGY"],
        peer_revenues=[1500.0, 2100.0, 1200.0, 2400.0, 1800.0],   # $M
        peer_ebitdas=[300.0, 420.0, 240.0, 480.0, 360.0],         # $M
        peer_net_incomes=[150.0, 210.0, 120.0, 240.0, 180.0],     # $M
        peer_epss=[3.00, 4.20, 2.40, 4.80, 3.60],                 # $
        peer_net_debts=[600.0, 840.0, 480.0, 960.0, 720.0],       # $M
        peer_shares_outstanding=[50.0, 50.0, 50.0, 50.0, 50.0],   # Million shares
        peer_share_prices=[60.0, 84.0, 48.0, 96.0, 72.0]          # $
    )

    return results, excel_file

if __name__ == "__main__":
    print("📊 Professional Trading Comparables Model Demonstration")
    print("=" * 80)

    # Run different industry sector comps
    tech_results, tech_excel = demo_technology_sector_comps()
    mfg_results, mfg_excel = demo_manufacturing_sector_comps()
    consumer_results, consumer_excel = demo_consumer_sector_comps()
    healthcare_results, healthcare_excel = demo_healthcare_sector_comps()
    energy_results, energy_excel = demo_energy_sector_comps()

    print("\n📊 Industry Sector Comparison:")
    print("=" * 80)

    sectors = [
        ("Technology", tech_results),
        ("Manufacturing", mfg_results),
        ("Consumer/Retail", consumer_results),
        ("Healthcare", healthcare_results),
        ("Energy", energy_results)
    ]

    print("Sector Comparison (Median Multiples):")
    print("<20")
    print("-" * 90)

    for name, results in sectors:
        summary_stats = results['summary_stats']
        valuation_ranges = results['valuation_ranges']

        print("<20"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<15.0f")

    print("\n✅ All trading comps models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {consumer_excel}")
    print(f"   • {healthcare_excel}")
    print(f"   • {energy_excel}")

    print("\n💡 Key Industry Insights:")
    print("=" * 80)
    print("• Technology: Highest valuations (25th-75th percentile ranges)")
    print("• Manufacturing: Moderate valuations, consistent across peers")
    print("• Consumer/Retail: Lower multiples, tighter valuation ranges")
    print("• Healthcare: Stable valuations, regulated environment factors")
    print("• Energy: Volatile valuations, commodity price sensitivity")
    print("\n🎯 Trading Comps Applications:")
    print("   - IPO valuation and pricing analysis")
    print("   - M&A target valuation and premium assessment")
    print("   - Investment thesis development and benchmarking")
    print("   - Sector analysis and relative positioning")
    print("   - Fair value assessment for investment decisions")
    print("   - Pitch book exhibits and valuation sensitivity analysis")
