#!/usr/bin/env python3
"""
Sum-of-the-Parts (SOTP) Model Demonstration
Shows how to use the Professional SOTP Model with different conglomerate scenarios
"""

from professional_sotp_model import ProfessionalSOTPModel

def demo_conglomerate_with_discount():
    """Demo: Traditional Conglomerate with Conglomerate Discount"""
    print("🏢 Demo: Traditional Conglomerate with Conglomerate Discount")
    print("=" * 70)

    model = ProfessionalSOTPModel("Industrial Conglomerate Corp.", "INDCONG")

    # Traditional conglomerate with conglomerate discount
    segments = [
        {
            'name': 'Manufacturing Division',
            'description': 'Heavy industrial manufacturing',
            'revenue': 4000.0,
            'ebitda': 600.0,
            'net_income': 400.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 8.0,  # Industrial average
            'growth_rate': 0.03,
            'beta': 1.1,
            'risk_premium': 0.06
        },
        {
            'name': 'Aerospace Division',
            'description': 'Aerospace and defense',
            'revenue': 3000.0,
            'ebitda': 500.0,
            'net_income': 350.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 12.0,  # Aerospace premium
            'growth_rate': 0.04,
            'beta': 1.0,
            'risk_premium': 0.05
        },
        {
            'name': 'Energy Division',
            'description': 'Oil and gas operations',
            'revenue': 2000.0,
            'ebitda': 400.0,
            'net_income': 200.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 6.0,  # Energy sector
            'growth_rate': 0.02,
            'beta': 1.2,
            'risk_premium': 0.07
        },
        {
            'name': 'Services Division',
            'description': 'Business services and consulting',
            'revenue': 1500.0,
            'ebitda': 250.0,
            'net_income': 150.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 10.0,  # Services premium
            'growth_rate': 0.05,
            'beta': 0.9,
            'risk_premium': 0.045
        }
    ]

    results = model.run_sotp_model(
        company_name="Industrial Conglomerate Corp.",
        ticker="INDCONG",
        segments=segments,

        # Corporate adjustments (conglomerate with discount)
        net_debt=1500.0,                  # $1.5B net debt
        minority_interests=200.0,         # $200M minority interests
        cash_and_investments=800.0,       # $800M cash
        other_assets=100.0,               # $100M other assets
        other_liabilities=150.0,          # $150M other liabilities
        shares_outstanding=200.0,         # 200M shares
        current_share_price=60.0          # $60 current price (discounted)
    )

    return results

def demo_tech_conglomerate_premium():
    """Demo: Tech Conglomerate with Conglomerate Premium"""
    print("\n💻 Demo: Tech Conglomerate with Conglomerate Premium")
    print("=" * 65)

    model = ProfessionalSOTPModel("TechMega Corp.", "TECHMEGA")

    # Tech conglomerate with conglomerate premium
    segments = [
        {
            'name': 'Cloud Computing Division',
            'description': 'Cloud infrastructure and services',
            'revenue': 8000.0,
            'ebitda': 2500.0,
            'net_income': 2000.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 20.0,  # Cloud premium
            'growth_rate': 0.12,
            'beta': 1.3,
            'risk_premium': 0.04
        },
        {
            'name': 'Software Division',
            'description': 'Enterprise software and productivity',
            'revenue': 6000.0,
            'ebitda': 2000.0,
            'net_income': 1600.0,
            'valuation_method': 'P/E Multiple',
            'multiple': 30.0,  # Software growth premium
            'growth_rate': 0.10,
            'beta': 1.2,
            'risk_premium': 0.045
        },
        {
            'name': 'Hardware Division',
            'description': 'Consumer electronics and devices',
            'revenue': 5000.0,
            'ebitda': 800.0,
            'net_income': 600.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 12.0,  # Hardware average
            'growth_rate': 0.06,
            'beta': 1.4,
            'risk_premium': 0.05
        },
        {
            'name': 'Services Division',
            'description': 'Consulting and cloud migration',
            'revenue': 3000.0,
            'ebitda': 600.0,
            'net_income': 450.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 15.0,  # Services premium
            'growth_rate': 0.08,
            'beta': 1.1,
            'risk_premium': 0.04
        }
    ]

    results = model.run_sotp_model(
        company_name="TechMega Corp.",
        ticker="TECHMEGA",
        segments=segments,

        # Corporate adjustments (tech conglomerate premium)
        net_debt=500.0,                   # $500M net debt (low leverage)
        minority_interests=100.0,         # $100M minority interests
        cash_and_investments=2000.0,      # $2B cash (tech company cash pile)
        other_assets=300.0,               # $300M other assets
        other_liabilities=200.0,          # $200M other liabilities
        shares_outstanding=150.0,         # 150M shares
        current_share_price=200.0         # $200 current price (premium)
    )

    return results

def demo_financial_conglomerate():
    """Demo: Financial Services Conglomerate"""
    print("\n🏦 Demo: Financial Services Conglomerate")
    print("=" * 55)

    model = ProfessionalSOTPModel("Financial Group Inc.", "FINANCIAL")

    # Financial conglomerate with banking and insurance
    segments = [
        {
            'name': 'Commercial Banking',
            'description': 'Corporate and commercial banking',
            'revenue': 4000.0,
            'ebitda': 1200.0,
            'net_income': 800.0,
            'valuation_method': 'P/E Multiple',
            'multiple': 12.0,  # Banking P/E
            'growth_rate': 0.04,
            'beta': 1.1,
            'risk_premium': 0.06
        },
        {
            'name': 'Retail Banking',
            'description': 'Consumer banking and deposits',
            'revenue': 3000.0,
            'ebitda': 1000.0,
            'net_income': 700.0,
            'valuation_method': 'P/E Multiple',
            'multiple': 10.0,  # Retail banking P/E
            'growth_rate': 0.035,
            'beta': 0.9,
            'risk_premium': 0.055
        },
        {
            'name': 'Investment Banking',
            'description': 'Capital markets and advisory',
            'revenue': 2500.0,
            'ebitda': 800.0,
            'net_income': 550.0,
            'valuation_method': 'P/E Multiple',
            'multiple': 15.0,  # Investment banking premium
            'growth_rate': 0.045,
            'beta': 1.3,
            'risk_premium': 0.065
        },
        {
            'name': 'Insurance Division',
            'description': 'Property and casualty insurance',
            'revenue': 3500.0,
            'ebitda': 400.0,
            'net_income': 300.0,
            'valuation_method': 'P/E Multiple',
            'multiple': 14.0,  # Insurance P/E
            'growth_rate': 0.03,
            'beta': 1.0,
            'risk_premium': 0.05
        }
    ]

    results = model.run_sotp_model(
        company_name="Financial Group Inc.",
        ticker="FINANCIAL",
        segments=segments,

        # Corporate adjustments (financial conglomerate)
        net_debt=2000.0,                  # $2B net debt (typical for financials)
        minority_interests=300.0,         # $300M minority interests
        cash_and_investments=1500.0,      # $1.5B cash and investments
        other_assets=400.0,               # $400M other assets
        other_liabilities=250.0,          # $250M other liabilities
        shares_outstanding=120.0,         # 120M shares
        current_share_price=85.0          # $85 current price
    )

    return results

def demo_consumer_conglomerate():
    """Demo: Consumer Goods Conglomerate"""
    print("\n🛍️  Demo: Consumer Goods Conglomerate")
    print("=" * 50)

    model = ProfessionalSOTPModel("Consumer Group Corp.", "CONSUMER")

    # Consumer conglomerate with branded businesses
    segments = [
        {
            'name': 'Food & Beverage Division',
            'description': 'Packaged foods and beverages',
            'revenue': 6000.0,
            'ebitda': 1200.0,
            'net_income': 800.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 14.0,  # Consumer premium
            'growth_rate': 0.04,
            'beta': 0.7,
            'risk_premium': 0.04
        },
        {
            'name': 'Personal Care Division',
            'description': 'Personal care and beauty products',
            'revenue': 4000.0,
            'ebitda': 800.0,
            'net_income': 600.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 16.0,  # Beauty premium
            'growth_rate': 0.05,
            'beta': 0.8,
            'risk_premium': 0.045
        },
        {
            'name': 'Household Products',
            'description': 'Cleaning and household products',
            'revenue': 3500.0,
            'ebitda': 700.0,
            'net_income': 500.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 12.0,  # Household products
            'growth_rate': 0.035,
            'beta': 0.75,
            'risk_premium': 0.0425
        },
        {
            'name': 'International Division',
            'description': 'Emerging markets operations',
            'revenue': 2500.0,
            'ebitda': 400.0,
            'net_income': 250.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 10.0,  # Emerging markets discount
            'growth_rate': 0.06,
            'beta': 1.0,
            'risk_premium': 0.07
        }
    ]

    results = model.run_sotp_model(
        company_name="Consumer Group Corp.",
        ticker="CONSUMER",
        segments=segments,

        # Corporate adjustments (consumer conglomerate)
        net_debt=1200.0,                  # $1.2B net debt
        minority_interests=150.0,         # $150M minority interests
        cash_and_investments=900.0,       # $900M cash
        other_assets=200.0,               # $200M other assets
        other_liabilities=100.0,          # $100M other liabilities
        shares_outstanding=180.0,         # 180M shares
        current_share_price=75.0          # $75 current price
    )

    return results

def demo_healthcare_conglomerate():
    """Demo: Healthcare Services Conglomerate"""
    print("\n🏥 Demo: Healthcare Services Conglomerate")
    print("=" * 55)

    model = ProfessionalSOTPModel("HealthSys Group", "HEALTHSYS")

    # Healthcare conglomerate with hospitals and services
    segments = [
        {
            'name': 'Hospitals Division',
            'description': 'Acute care hospitals and clinics',
            'revenue': 8000.0,
            'ebitda': 1000.0,
            'net_income': 600.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 10.0,  # Hospital average
            'growth_rate': 0.03,
            'beta': 0.9,
            'risk_premium': 0.045
        },
        {
            'name': 'Physician Services',
            'description': 'Physician practices and ambulatory care',
            'revenue': 4000.0,
            'ebitda': 600.0,
            'net_income': 400.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 12.0,  # Physician services premium
            'growth_rate': 0.04,
            'beta': 0.85,
            'risk_premium': 0.04
        },
        {
            'name': 'Insurance Division',
            'description': 'Health insurance and managed care',
            'revenue': 12000.0,
            'ebitda': 800.0,
            'net_income': 500.0,
            'valuation_method': 'P/E Multiple',
            'multiple': 16.0,  # Insurance P/E
            'growth_rate': 0.035,
            'beta': 1.0,
            'risk_premium': 0.05
        },
        {
            'name': 'Specialty Services',
            'description': 'Diagnostic and specialty services',
            'revenue': 3000.0,
            'ebitda': 500.0,
            'net_income': 350.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 15.0,  # Specialty premium
            'growth_rate': 0.045,
            'beta': 0.95,
            'risk_premium': 0.0475
        }
    ]

    results = model.run_sotp_model(
        company_name="HealthSys Group",
        ticker="HEALTHSYS",
        segments=segments,

        # Corporate adjustments (healthcare conglomerate)
        net_debt=1800.0,                  # $1.8B net debt
        minority_interests=250.0,         # $250M minority interests
        cash_and_investments=1200.0,      # $1.2B cash
        other_assets=150.0,               # $150M other assets
        other_liabilities=200.0,          # $200M other liabilities
        shares_outstanding=140.0,         # 140M shares
        current_share_price=95.0          # $95 current price
    )

    return results

def demo_international_conglomerate():
    """Demo: International Conglomerate with Geographic Segments"""
    print("\n🌍 Demo: International Conglomerate with Geographic Segments")
    print("=" * 70)

    model = ProfessionalSOTPModel("Global Industries Ltd.", "GLOBALIND")

    # International conglomerate with geographic segments
    segments = [
        {
            'name': 'North America Division',
            'description': 'US and Canadian operations',
            'revenue': 8000.0,
            'ebitda': 1600.0,
            'net_income': 1200.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 12.0,  # North America premium
            'growth_rate': 0.04,
            'beta': 1.0,
            'risk_premium': 0.05
        },
        {
            'name': 'Europe Division',
            'description': 'European Union operations',
            'revenue': 6000.0,
            'ebitda': 1000.0,
            'net_income': 700.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 10.0,  # Europe average
            'growth_rate': 0.03,
            'beta': 1.1,
            'risk_premium': 0.06
        },
        {
            'name': 'Asia Pacific Division',
            'description': 'Asia Pacific operations',
            'revenue': 5000.0,
            'ebitda': 900.0,
            'net_income': 650.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 14.0,  # Asia growth premium
            'growth_rate': 0.06,
            'beta': 1.2,
            'risk_premium': 0.065
        },
        {
            'name': 'Emerging Markets',
            'description': 'Latin America, Africa, Middle East',
            'revenue': 3000.0,
            'ebitda': 500.0,
            'net_income': 300.0,
            'valuation_method': 'EV/EBITDA Multiple',
            'multiple': 8.0,   # Emerging markets discount
            'growth_rate': 0.05,
            'beta': 1.4,
            'risk_premium': 0.08
        }
    ]

    results = model.run_sotp_model(
        company_name="Global Industries Ltd.",
        ticker="GLOBALIND",
        segments=segments,

        # Corporate adjustments (international conglomerate)
        net_debt=2000.0,                  # $2B net debt
        minority_interests=400.0,         # $400M minority interests
        cash_and_investments=1500.0,      # $1.5B cash
        other_assets=300.0,               # $300M other assets
        other_liabilities=250.0,          # $250M other liabilities
        shares_outstanding=160.0,         # 160M shares
        current_share_price=110.0         # $110 current price
    )

    return results

if __name__ == "__main__":
    print("🧩 Professional Sum-of-the-Parts (SOTP) Model Demonstration")
    print("=" * 85)

    # Run different conglomerate scenarios
    discount_results = demo_conglomerate_with_discount()
    tech_results = demo_tech_conglomerate_premium()
    financial_results = demo_financial_conglomerate()
    consumer_results = demo_consumer_conglomerate()
    healthcare_results = demo_healthcare_conglomerate()
    international_results = demo_international_conglomerate()

    print("\n📊 SOTP Valuation Comparison:")
    print("=" * 85)

    scenarios = [
        ("Industrial Conglomerate", discount_results['consolidation']),
        ("Tech Conglomerate", tech_results['consolidation']),
        ("Financial Conglomerate", financial_results['consolidation']),
        ("Consumer Conglomerate", consumer_results['consolidation']),
        ("Healthcare Conglomerate", healthcare_results['consolidation']),
        ("International Conglomerate", international_results['consolidation'])
    ]

    print("Scenario Comparison (Key Metrics):")
    print("<25")
    print("-" * 140)

    for name, consolidation in scenarios:
        total_ev = consolidation['total_ev']
        equity_value = consolidation['equity_value']
        implied_price = consolidation['implied_share_price']
        current_price = consolidation['current_share_price']
        premium_pct = consolidation['premium_discount_pct']

        print("<25"
              "<12.1f"
              "<12.1f"
              "<12.2f"
              "<12.2f"
              "<12.1f")

    print("\n✅ All SOTP models completed successfully!")
    print("📁 Excel files generated for each conglomerate scenario")

    print("\n💡 SOTP Valuation Insights:")
    print("=" * 85)
    print("• Conglomerate Discount: When sum of parts > current market value")
    print("• Conglomerate Premium: When market recognizes diversification benefits")
    print("• Hidden Value: SOTP reveals undervalued segments")
    print("• Break-up Value: Maximum theoretical value if divested separately")
    print("• Segment Volatility: Different segments have different risk profiles")
    print("• Geographic Diversification: Can create or destroy value")

    print("\n🎯 SOTP Applications:")
    print("=" * 85)
    print("   - Conglomerate valuation and fairness opinions")
    print("   - Break-up analysis for activist investors")
    print("   - Spin-off and divestiture planning")
    print("   - M&A target identification")
    print("   - Portfolio company analysis")
    print("   - Equity research and investment recommendations")

    print("\n📈 SOTP Best Practices:")
    print("=" * 85)
    print("   • Use most appropriate valuation method for each segment")
    print("   • Apply consistent discount rates and growth assumptions")
    print("   • Account for corporate overhead allocation")
    print("   • Consider tax implications of structure")
    print("   • Update regularly as market conditions change")
    print("   • Validate with comparable transactions")

    print("\n🏆 When to Use SOTP:")
    print("=" * 85)
    print("   • Conglomerates with distinct business segments")
    print("   • Companies with mixed industrial exposure")
    print("   • Firms with geographic diversification")
    print("   • Holdings companies or investment vehicles")
    print("   • Companies trading at apparent discount to peers")
    print("   • Firms considering strategic divestitures")
