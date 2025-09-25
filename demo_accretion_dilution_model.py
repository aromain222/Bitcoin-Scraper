#!/usr/bin/env python3
"""
Accretion/Dilution Model Demonstration
Shows how to use the Professional Accretion/Dilution Model with different deal scenarios
"""

from professional_accretion_dilution_model import ProfessionalAccretionDilutionModel

def demo_tech_acquisition():
    """Demo: Large Tech Company Acquiring Startup"""
    print("🚀 Demo: Tech Giant Acquiring AI Startup")
    print("=" * 55)

    model = ProfessionalAccretionDilutionModel("TechMega Corp.", "AISolutions Inc.", "TECHMEGA", "AISOL")

    # Large tech company acquiring AI startup with high synergies
    results = model.run_accretion_dilution_model(

        # Buyer financials (large tech giant)
        buyer_net_income=5000.0,      # $5B NI
        buyer_eps=12.50,              # $12.50 EPS
        buyer_shares_outstanding=400.0,  # 400M shares
        buyer_pe_ratio=25.0,          # 25x P/E (growth stock)

        # Seller financials (high-growth AI startup)
        seller_net_income=100.0,      # $100M NI
        seller_shares_outstanding=40.0,  # 40M shares
        seller_pe_ratio=40.0,         # 40x P/E (premium for growth)

        # Deal structure (premium for strategic acquisition)
        purchase_premium_pct=0.50,    # 50% premium (strategic value)
        cash_pct=0.70,                # 70% cash (quick close)
        stock_pct=0.20,               # 20% stock (retention)
        debt_pct=0.10,                # 10% debt (balance sheet)

        # Financing assumptions
        interest_rate=0.04,           # 4% interest rate (investment grade)
        tax_rate=0.21,                # 21% corporate tax rate

        # Synergies (AI integration benefits)
        revenue_synergies=300.0,      # $300M cross-selling
        cost_synergies=400.0,         # $400M operational efficiencies
        one_time_costs=75.0           # $75M integration costs
    )

    return results

def demo_manufacturing_consolidation():
    """Demo: Manufacturing Consolidation Deal"""
    print("\n🏭 Demo: Industrial Conglomerate Acquiring Specialty Manufacturer")
    print("=" * 75)

    model = ProfessionalAccretionDilutionModel("IndustCorp Ltd.", "PrecisionMfg Inc.", "INDUSTCORP", "PRECISION")

    # Traditional manufacturing consolidation with moderate synergies
    results = model.run_accretion_dilution_model(

        # Buyer financials (industrial conglomerate)
        buyer_net_income=800.0,       # $800M NI
        buyer_eps=8.00,               # $8.00 EPS
        buyer_shares_outstanding=100.0,  # 100M shares
        buyer_pe_ratio=15.0,          # 15x P/E (industrial average)

        # Seller financials (specialty manufacturer)
        seller_net_income=60.0,       # $60M NI
        seller_shares_outstanding=30.0,  # 30M shares
        seller_pe_ratio=18.0,         # 18x P/E (specialty premium)

        # Deal structure (industry consolidation)
        purchase_premium_pct=0.30,    # 30% premium (industry standard)
        cash_pct=0.50,                # 50% cash
        stock_pct=0.40,               # 40% stock (significant dilution)
        debt_pct=0.10,                # 10% debt

        # Financing assumptions
        interest_rate=0.06,           # 6% interest rate (industrial risk)
        tax_rate=0.25,                # 25% corporate tax rate

        # Synergies (manufacturing efficiencies)
        revenue_synergies=80.0,       # $80M expanded distribution
        cost_synergies=120.0,         # $120M procurement savings
        one_time_costs=40.0           # $40M integration costs
    )

    return results

def demo_healthcare_roll_up():
    """Demo: Healthcare Provider Roll-Up"""
    print("\n🏥 Demo: Hospital System Acquiring Physician Practices")
    print("=" * 60)

    model = ProfessionalAccretionDilutionModel("MediSys Health", "FamilyMed Group", "MEDISYS", "FAMILYMED")

    # Healthcare roll-up with regulatory and operational synergies
    results = model.run_accretion_dilution_model(

        # Buyer financials (large hospital system)
        buyer_net_income=600.0,       # $600M NI
        buyer_eps=6.00,               # $6.00 EPS
        buyer_shares_outstanding=100.0,  # 100M shares
        buyer_pe_ratio=20.0,          # 20x P/E (healthcare premium)

        # Seller financials (independent physician group)
        seller_net_income=30.0,       # $30M NI
        seller_shares_outstanding=15.0,  # 15M shares
        seller_pe_ratio=25.0,         # 25x P/E (private practice)

        # Deal structure (healthcare roll-up)
        purchase_premium_pct=0.40,    # 40% premium (physician compensation)
        cash_pct=0.30,                # 30% cash
        stock_pct=0.60,               # 60% stock (physician retention)
        debt_pct=0.10,                # 10% debt

        # Financing assumptions
        interest_rate=0.045,          # 4.5% interest rate (healthcare bonds)
        tax_rate=0.21,                # 21% corporate tax rate

        # Synergies (healthcare integration benefits)
        revenue_synergies=120.0,      # $120M expanded services
        cost_synergies=80.0,          # $80M administrative savings
        one_time_costs=30.0           # $30M regulatory/compliance costs
    )

    return results

def demo_consumer_retail_dilutive():
    """Demo: Retail Chain with Dilutive Acquisition"""
    print("\n🛍️  Demo: Retail Chain Making Aggressive Acquisition")
    print("=" * 55)

    model = ProfessionalAccretionDilutionModel("RetailMax Corp.", "TrendyBrand Inc.", "RETAILMAX", "TRENDYBRAND")

    # Retail deal with high premium and limited synergies (potentially dilutive)
    results = model.run_accretion_dilution_model(

        # Buyer financials (traditional retailer)
        buyer_net_income=400.0,       # $400M NI
        buyer_eps=4.00,               # $4.00 EPS
        buyer_shares_outstanding=100.0,  # 100M shares
        buyer_pe_ratio=12.0,          # 12x P/E (retail average)

        # Seller financials (high-fashion brand)
        seller_net_income=80.0,       # $80M NI
        seller_shares_outstanding=20.0,  # 20M shares
        seller_pe_ratio=35.0,         # 35x P/E (premium brand)

        # Deal structure (aggressive premium)
        purchase_premium_pct=0.75,    # 75% premium (brand value)
        cash_pct=0.80,                # 80% cash (acquirer confidence)
        stock_pct=0.15,               # 15% stock
        debt_pct=0.05,                # 5% debt

        # Financing assumptions
        interest_rate=0.055,          # 5.5% interest rate (retail risk)
        tax_rate=0.25,                # 25% corporate tax rate

        # Synergies (limited for brand acquisition)
        revenue_synergies=60.0,       # $60M cross-selling
        cost_synergies=40.0,          # $40M limited efficiencies
        one_time_costs=50.0           # $50M brand integration costs
    )

    return results

def demo_financial_services_deal():
    """Demo: Bank Acquisition of Wealth Management Firm"""
    print("\n🏦 Demo: Regional Bank Acquiring Wealth Management Firm")
    print("=" * 65)

    model = ProfessionalAccretionDilutionModel("MetroBank Corp.", "WealthAdvisors LLC", "METROBANK", "WEALTHADV")

    # Financial services deal with stable synergies
    results = model.run_accretion_dilution_model(

        # Buyer financials (regional bank)
        buyer_net_income=300.0,       # $300M NI
        buyer_eps=3.00,               # $3.00 EPS
        buyer_shares_outstanding=100.0,  # 100M shares
        buyer_pe_ratio=14.0,          # 14x P/E (financial services)

        # Seller financials (wealth management firm)
        seller_net_income=25.0,       # $25M NI
        seller_shares_outstanding=10.0,  # 10M shares
        seller_pe_ratio=20.0,         # 20x P/E (wealth management)

        # Deal structure (financial services acquisition)
        purchase_premium_pct=0.35,    # 35% premium (industry standard)
        cash_pct=0.45,                # 45% cash
        stock_pct=0.45,               # 45% stock (equal mix)
        debt_pct=0.10,                # 10% debt

        # Financing assumptions
        interest_rate=0.04,           # 4% interest rate (bank financing)
        tax_rate=0.21,                # 21% corporate tax rate

        # Synergies (wealth management integration)
        revenue_synergies=50.0,       # $50M expanded client base
        cost_synergies=30.0,          # $30M operational efficiencies
        one_time_costs=15.0           # $15M system integration
    )

    return results

def demo_tech_giant_startup():
    """Demo: Tech Giant Acquiring High-Growth Startup"""
    print("\n💻 Demo: Big Tech Acquiring Disruptive Startup")
    print("=" * 50)

    model = ProfessionalAccretionDilutionModel("BigTech Corp.", "DisruptTech Inc.", "BIGTECH", "DISRUPTECH")

    # Massive tech company acquiring small but high-potential startup
    results = model.run_accretion_dilution_model(

        # Buyer financials (massive tech company)
        buyer_net_income=15000.0,     # $15B NI
        buyer_eps=15.00,              # $15.00 EPS
        buyer_shares_outstanding=1000.0,  # 1B shares
        buyer_pe_ratio=30.0,          # 30x P/E (tech premium)

        # Seller financials (high-growth startup)
        seller_net_income=5.0,        # $5M NI (pre-profit)
        seller_shares_outstanding=50.0,  # 50M shares
        seller_pe_ratio=100.0,        # 100x P/E (startup valuation)

        # Deal structure (strategic tech acquisition)
        purchase_premium_pct=1.00,    # 100% premium (strategic value)
        cash_pct=0.90,                # 90% cash (all-cash deal)
        stock_pct=0.05,               # 5% stock (founder retention)
        debt_pct=0.05,                # 5% debt

        # Financing assumptions
        interest_rate=0.035,          # 3.5% interest rate (AAA credit)
        tax_rate=0.21,                # 21% corporate tax rate

        # Synergies (massive platform integration)
        revenue_synergies=2000.0,     # $2B expanded ecosystem
        cost_synergies=500.0,         # $500M R&D efficiencies
        one_time_costs=100.0          # $100M acquisition costs
    )

    return results

if __name__ == "__main__":
    print("📊 Professional Accretion/Dilution Model Demonstration")
    print("=" * 95)

    # Run different deal scenarios
    tech_results = demo_tech_acquisition()
    mfg_results = demo_manufacturing_consolidation()
    healthcare_results = demo_healthcare_roll_up()
    retail_results = demo_consumer_retail_dilutive()
    financial_results = demo_financial_services_deal()
    big_tech_results = demo_tech_giant_startup()

    print("\n📊 Accretion/Dilution Comparison:")
    print("=" * 95)

    scenarios = [
        ("Tech Acquisition", tech_results['accretion_dilution']),
        ("Manufacturing", mfg_results['accretion_dilution']),
        ("Healthcare", healthcare_results['accretion_dilution']),
        ("Retail (Dilutive)", retail_results['accretion_dilution']),
        ("Financial Services", financial_results['accretion_dilution']),
        ("Big Tech Startup", big_tech_results['accretion_dilution'])
    ]

    print("Scenario Comparison:")
    print("<25")
    print("-" * 140)

    for name, accretion in scenarios:
        eps_impact = accretion['eps_impact']
        accretion_pct = accretion['accretion_dilution_pct']
        status = accretion['status']

        print("<25"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<25")

    print("\n✅ All accretion/dilution models completed successfully!")
    print("📁 Excel files generated for each scenario")

    print("\n💡 Accretion/Dilution Key Insights:")
    print("=" * 95)
    print("• Tech Acquisitions: Often accretive due to synergies and growth opportunities")
    print("• Manufacturing: Moderate accretion with operational efficiencies")
    print("• Healthcare: Strong accretion from integrated care delivery")
    print("• Retail: Can be dilutive with high premiums and limited synergies")
    print("• Financial Services: Stable accretion with client base expansion")
    print("• Big Tech: Minimal EPS impact due to massive buyer size")

    print("\n🎯 Deal Structuring Best Practices:")
    print("=" * 95)
    print("   • Stock consideration increases shares but shares upside")
    print("   • Cash consideration avoids dilution but increases balance sheet leverage")
    print("   • Premium affects accretion - lower premium = more accretive")
    print("   • Synergies are critical - higher synergies = more accretive")
    print("   • Tax rate impacts after-tax synergy benefits")
    print("   • One-time costs reduce accretion in early years")

    print("\n📈 Strategic Considerations:")
    print("=" * 95)
    print("   • EPS accretion is important but not the only consideration")
    print("   • Consider strategic value, market position, and long-term growth")
    print("   • Balance sheet impact affects future M&A capacity")
    print("   • Cultural fit and integration risk are often more important")
    print("   • Shareholder communication around accretion/dilution is key")
    print("   • Consider multiple scenarios and sensitivity analysis")
