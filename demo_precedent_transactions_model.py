#!/usr/bin/env python3
"""
Precedent Transactions Model Demonstration
Shows how to use the Professional Precedent Transactions Model with different industries and deal scenarios
"""

from professional_precedent_transactions_model import ProfessionalPrecedentTransactionsModel

def demo_technology_mergers():
    """Demo: Technology Sector Precedent Transactions"""
    print("🔥 Demo: Technology Sector Precedent Transactions")
    print("=" * 60)

    model = ProfessionalPrecedentTransactionsModel("CloudTech Corp.", "CLOUDTECH")

    # Technology sector deals with higher valuations
    results, excel_file = model.run_precedent_transactions_model(
        # Target Company Data
        target_revenue=1500.0,      # $1.5B revenue
        target_ebitda=450.0,        # $450M EBITDA (30% margin)
        target_net_income=270.0,    # $270M net income
        target_eps=4.50,            # $4.50 EPS
        target_net_debt=150.0,      # $150M net debt
        target_shares_outstanding=60.0,  # 60M shares

        # Precedent Technology Deals
        deal_dates=["2023-01-15", "2023-03-22", "2023-06-10", "2023-09-05", "2023-11-28"],
        acquirers=["BigTech Corp", "Global Tech Inc", "Mega Soft Ltd", "TechGiant Corp", "Cloud Systems Inc"],
        targets=["SaaS Startup Inc", "Data Analytics Corp", "AI Platform Ltd", "DevTools Inc", "Cloud Services Co"],
        equity_values=[800.0, 1200.0, 600.0, 1500.0, 900.0],      # $M
        enterprise_values=[920.0, 1380.0, 690.0, 1725.0, 1035.0], # $M
        deal_revenues=[400.0, 600.0, 300.0, 750.0, 450.0],        # $M
        deal_ebitdas=[120.0, 180.0, 90.0, 225.0, 135.0],          # $M
        deal_net_incomes=[80.0, 120.0, 60.0, 150.0, 90.0]         # $M
    )

    return results, excel_file

def demo_manufacturing_acquisitions():
    """Demo: Manufacturing Sector Precedent Transactions"""
    print("\n🔧 Demo: Manufacturing Sector Precedent Transactions")
    print("=" * 60)

    model = ProfessionalPrecedentTransactionsModel("IndustCo Inc.", "INDUST")

    # Manufacturing deals with moderate valuations
    results, excel_file = model.run_precedent_transactions_model(
        # Target Company Data
        target_revenue=800.0,       # $800M revenue
        target_ebitda=160.0,        # $160M EBITDA (20% margin)
        target_net_income=80.0,     # $80M net income
        target_eps=2.00,            # $2.00 EPS
        target_net_debt=240.0,      # $240M net debt
        target_shares_outstanding=40.0,  # 40M shares

        # Precedent Manufacturing Deals
        deal_dates=["2022-08-15", "2022-11-22", "2023-02-10", "2023-05-05", "2023-08-28"],
        acquirers=["AutoGiant Corp", "MetalWorks Inc", "Chemicals Plus", "Equipment Mfg", "Indust Supply"],
        targets=["Parts Supplier Inc", "Steel Producer Corp", "Chemical Plant Ltd", "Machinery Inc", "Components Co"],
        equity_values=[500.0, 750.0, 400.0, 1000.0, 600.0],       # $M
        enterprise_values=[650.0, 975.0, 520.0, 1300.0, 780.0],   # $M
        deal_revenues=[300.0, 450.0, 250.0, 600.0, 350.0],        # $M
        deal_ebitdas=[60.0, 90.0, 50.0, 120.0, 70.0],             # $M
        deal_net_incomes=[40.0, 60.0, 35.0, 80.0, 45.0]           # $M
    )

    return results, excel_file

def demo_consumer_retail_deals():
    """Demo: Consumer Retail Precedent Transactions"""
    print("\n🛍️  Demo: Consumer Retail Precedent Transactions")
    print("=" * 60)

    model = ProfessionalPrecedentTransactionsModel("RetailMax Corp.", "RETAIL")

    # Retail deals with lower multiples
    results, excel_file = model.run_precedent_transactions_model(
        # Target Company Data
        target_revenue=2500.0,      # $2.5B revenue
        target_ebitda=250.0,        # $250M EBITDA (10% margin)
        target_net_income=125.0,    # $125M net income
        target_eps=2.50,            # $2.50 EPS
        target_net_debt=500.0,      # $500M net debt
        target_shares_outstanding=50.0,  # 50M shares

        # Precedent Retail Deals
        deal_dates=["2022-06-15", "2022-09-22", "2023-01-10", "2023-04-05", "2023-07-28"],
        acquirers=["Fashion Retail", "Home Goods Inc", "Sports Store", "Electronics Plus", "Department Store"],
        targets=["Boutique Chain Inc", "Decor Store Corp", "Sporting Goods Ltd", "Gadget Shop Inc", "Clothing Co"],
        equity_values=[400.0, 600.0, 300.0, 750.0, 450.0],        # $M
        enterprise_values=[500.0, 750.0, 375.0, 937.5, 562.5],    # $M
        deal_revenues=[800.0, 1200.0, 600.0, 1500.0, 900.0],      # $M
        deal_ebitdas=[80.0, 120.0, 60.0, 150.0, 90.0],            # $M
        deal_net_incomes=[50.0, 75.0, 40.0, 95.0, 55.0]           # $M
    )

    return results, excel_file

def demo_healthcare_mergers():
    """Demo: Healthcare Sector Precedent Transactions"""
    print("\n🏥 Demo: Healthcare Sector Precedent Transactions")
    print("=" * 60)

    model = ProfessionalPrecedentTransactionsModel("MediCorp Inc.", "MEDI")

    # Healthcare deals with premium valuations
    results, excel_file = model.run_precedent_transactions_model(
        # Target Company Data
        target_revenue=1200.0,      # $1.2B revenue
        target_ebitda=240.0,        # $240M EBITDA (20% margin)
        target_net_income=144.0,    # $144M net income
        target_eps=2.88,            # $2.88 EPS
        target_net_debt=360.0,      # $360M net debt
        target_shares_outstanding=50.0,  # 50M shares

        # Precedent Healthcare Deals
        deal_dates=["2022-07-15", "2022-10-22", "2023-03-10", "2023-06-05", "2023-09-28"],
        acquirers=["HealthSys Corp", "Clinic Group Inc", "MedTech Corp", "Pharma Services", "Health Systems"],
        targets=["Specialty Clinic Inc", "Medical Practice Corp", "Device Company Ltd", "Pharma Dist Inc", "Hospital Chain"],
        equity_values=[600.0, 900.0, 450.0, 1125.0, 675.0],       # $M
        enterprise_values=[750.0, 1125.0, 562.5, 1406.25, 843.75], # $M
        deal_revenues=[400.0, 600.0, 300.0, 750.0, 450.0],        # $M
        deal_ebitdas=[80.0, 120.0, 60.0, 150.0, 90.0],            # $M
        deal_net_incomes=[60.0, 90.0, 45.0, 112.5, 67.5]          # $M
    )

    return results, excel_file

def demo_energy_acquisitions():
    """Demo: Energy Sector Precedent Transactions"""
    print("\n⚡ Demo: Energy Sector Precedent Transactions")
    print("=" * 60)

    model = ProfessionalPrecedentTransactionsModel("EnergyCorp Ltd.", "ENERGY")

    # Energy deals with capital-intensive valuations
    results, excel_file = model.run_precedent_transactions_model(
        # Target Company Data
        target_revenue=1800.0,      # $1.8B revenue
        target_ebitda=360.0,        # $360M EBITDA (20% margin)
        target_net_income=180.0,    # $180M net income
        target_eps=3.60,            # $3.60 EPS
        target_net_debt=720.0,      # $720M net debt
        target_shares_outstanding=50.0,  # 50M shares

        # Precedent Energy Deals
        deal_dates=["2022-05-15", "2022-08-22", "2022-12-10", "2023-03-05", "2023-06-28"],
        acquirers=["Oil & Gas Inc", "Pipeline Corp", "Refinery Ltd", "Exploration Co", "Energy Services"],
        targets=["Shale Producer Inc", "Pipeline Assets Corp", "Refinery Complex Ltd", "Oil Field Inc", "Drilling Co"],
        equity_values=[800.0, 1200.0, 600.0, 1500.0, 900.0],      # $M
        enterprise_values=[1400.0, 2100.0, 1050.0, 2625.0, 1575.0], # $M
        deal_revenues=[600.0, 900.0, 450.0, 1125.0, 675.0],       # $M
        deal_ebitdas=[120.0, 180.0, 90.0, 225.0, 135.0],          # $M
        deal_net_incomes=[80.0, 120.0, 60.0, 150.0, 90.0]         # $M
    )

    return results, excel_file

def demo_large_cap_mergers():
    """Demo: Large Cap Strategic Mergers"""
    print("\n🏢 Demo: Large Cap Strategic Mergers")
    print("=" * 60)

    model = ProfessionalPrecedentTransactionsModel("MegaCorp Inc.", "MEGACORP")

    # Large strategic deals with premium valuations
    results, excel_file = model.run_precedent_transactions_model(
        # Target Company Data (Large cap)
        target_revenue=5000.0,      # $5B revenue
        target_ebitda=1000.0,       # $1B EBITDA (20% margin)
        target_net_income=600.0,    # $600M net income
        target_eps=6.00,            # $6.00 EPS
        target_net_debt=1000.0,     # $1B net debt
        target_shares_outstanding=100.0,  # 100M shares

        # Precedent Large Cap Deals
        deal_dates=["2022-04-15", "2022-07-22", "2022-11-10", "2023-02-05", "2023-05-28"],
        acquirers=["Global Corp", "World Enterprises", "International Ltd", "Continental Inc", "Global Systems"],
        targets=["Regional Leader Inc", "National Champion Corp", "Market Leader Ltd", "Industry Giant Inc", "Sector Leader"],
        equity_values=[3000.0, 4500.0, 2250.0, 5625.0, 3375.0],   # $M
        enterprise_values=[3750.0, 5625.0, 2812.5, 7031.25, 4218.75], # $M
        deal_revenues=[1500.0, 2250.0, 1125.0, 2812.5, 1687.5],   # $M
        deal_ebitdas=[300.0, 450.0, 225.0, 562.5, 337.5],         # $M
        deal_net_incomes=[225.0, 337.5, 168.75, 421.875, 253.125] # $M
    )

    return results, excel_file

if __name__ == "__main__":
    print("🤝 Professional Precedent Transactions Model Demonstration")
    print("=" * 80)

    # Run different industry sector precedent transactions
    tech_results, tech_excel = demo_technology_mergers()
    mfg_results, mfg_excel = demo_manufacturing_acquisitions()
    retail_results, retail_excel = demo_consumer_retail_deals()
    healthcare_results, healthcare_excel = demo_healthcare_mergers()
    energy_results, energy_excel = demo_energy_acquisitions()
    large_cap_results, large_cap_excel = demo_large_cap_mergers()

    print("\n📊 Precedent Transactions Comparison:")
    print("=" * 80)

    sectors = [
        ("Technology", tech_results),
        ("Manufacturing", mfg_results),
        ("Retail", retail_results),
        ("Healthcare", healthcare_results),
        ("Energy", energy_results),
        ("Large Cap", large_cap_results)
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

    print("\n✅ All precedent transactions models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {retail_excel}")
    print(f"   • {healthcare_excel}")
    print(f"   • {energy_excel}")
    print(f"   • {large_cap_excel}")

    print("\n💡 Key Precedent Transactions Insights:")
    print("=" * 80)
    print("• Technology: Premium valuations (2.3x EV/Revenue), strategic value")
    print("• Manufacturing: Moderate multiples (7.8x EV/EBITDA), operational focus")
    print("• Retail: Lower multiples (10.0x Equity/Net Income), competitive pressures")
    print("• Healthcare: Premium valuations (13.5x EV/EBITDA), regulatory factors")
    print("• Energy: Capital intensive (12.0x EV/EBITDA), commodity exposure")
    print("• Large Cap: Strategic premiums, market positioning considerations")
    print("\n🎯 Precedent Transactions Applications:")
    print("   - M&A valuation and fairness opinions")
    print("   - Premium analysis and negotiation support")
    print("   - Strategic acquisition planning")
    print("   - Competitive bidding strategies")
    print("   - Investment banking pitch books")
    print("   - Regulatory filing support")
