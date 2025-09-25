#!/usr/bin/env python3
"""
M&A Merger Model Demonstration
Shows how to use the Professional Merger Model with different scenarios and deal structures
"""

from professional_merger_model import ProfessionalMergerModel

def demo_accretive_tech_merger():
    """Demo: Accretive Technology Merger"""
    print("🔥 Demo: Accretive Technology Merger")
    print("=" * 60)

    model = ProfessionalMergerModel("BigTech Corp.", "BIGTECH", "StartupTech Inc.", "STARTUP")

    results, excel_file = model.run_merger_model(
        # Acquirer Details (Large, profitable tech company)
        acquirer_share_price=100.0,      # Premium valuation
        acquirer_shares_outstanding=200.0,  # Large company
        acquirer_eps=5.00,               # Strong EPS

        # Target Details (High-growth startup)
        target_share_price=20.0,         # Growth stock
        target_shares_outstanding=25.0,  # Smaller target
        target_net_debt=50.0,            # Minimal debt
        target_eps=0.80,                 # Lower EPS but high growth

        # Transaction Details
        offer_price_per_share=35.0,      # 75% premium
        premium_pct=0.75,

        # Consideration Mix (Stock-heavy for tax benefits)
        cash_pct=0.30,                   # 30% cash
        stock_pct=0.70,                  # 70% stock
        debt_pct=0.00,                   # No new debt

        # Synergy Assumptions (Tech integration)
        revenue_synergies=200.0,         # Platform synergies
        cost_synergies_pct=0.08,         # 8% cost savings
        one_time_costs=75.0,             # Integration costs

        # Financing Assumptions
        new_debt_interest_rate=0.04,
        foregone_cash_yield=0.025,
        transaction_fees_pct=0.012,

        # Pro Forma Assumptions
        intangible_amortization_years=7,  # Shorter for tech
        tax_rate=0.21,                   # Lower tax rate
        combined_revenue=3500.0,         # Combined revenue
        combined_ebitda=1000.0,          # Combined EBITDA
        combined_depreciation=150.0,
        combined_tax_rate=0.21
    )

    return results, excel_file

def demo_defensive_manufacturing_merger():
    """Demo: Defensive Manufacturing Merger"""
    print("\n🔧 Demo: Defensive Manufacturing Merger")
    print("=" * 60)

    model = ProfessionalMergerModel("IndustCo Inc.", "INDUST", "SupplierCorp Ltd.", "SUPPLIER")

    results, excel_file = model.run_merger_model(
        # Acquirer Details (Established manufacturer)
        acquirer_share_price=40.0,
        acquirer_shares_outstanding=150.0,
        acquirer_eps=2.20,

        # Target Details (Key supplier - defensive acquisition)
        target_share_price=25.0,
        target_shares_outstanding=40.0,
        target_net_debt=150.0,           # Higher debt load
        target_eps=1.50,

        # Transaction Details (Lower premium for defensive deal)
        offer_price_per_share=28.0,      # 12% premium
        premium_pct=0.12,

        # Consideration Mix (Cash-heavy for clean break)
        cash_pct=0.80,                   # 80% cash
        stock_pct=0.20,                  # 20% stock
        debt_pct=0.00,

        # Synergy Assumptions (Supply chain integration)
        revenue_synergies=50.0,          # Limited revenue synergies
        cost_synergies_pct=0.12,         # 12% cost savings
        one_time_costs=60.0,             # Higher integration costs

        # Financing Assumptions
        new_debt_interest_rate=0.055,
        foregone_cash_yield=0.03,
        transaction_fees_pct=0.018,

        # Pro Forma Assumptions
        intangible_amortization_years=10,
        tax_rate=0.25,
        combined_revenue=2200.0,
        combined_ebitda=450.0,
        combined_depreciation=120.0,
        combined_tax_rate=0.25
    )

    return results, excel_file

def demo_dilutive_consumer_merger():
    """Demo: Dilutive Consumer Merger"""
    print("\n🛍️  Demo: Dilutive Consumer Merger")
    print("=" * 60)

    model = ProfessionalMergerModel("RetailGiant Corp.", "RETAIL", "TrendyBrand Inc.", "TRENDY")

    results, excel_file = model.run_merger_model(
        # Acquirer Details (Large retailer)
        acquirer_share_price=60.0,
        acquirer_shares_outstanding=300.0,
        acquirer_eps=3.00,

        # Target Details (Premium brand)
        target_share_price=40.0,
        target_shares_outstanding=30.0,
        target_net_debt=100.0,
        target_eps=2.00,                 # Higher EPS but smaller

        # Transaction Details (High premium for brand value)
        offer_price_per_share=70.0,      # 75% premium
        premium_pct=0.75,

        # Consideration Mix (Stock-heavy for brand alignment)
        cash_pct=0.40,
        stock_pct=0.60,
        debt_pct=0.00,

        # Synergy Assumptions (Brand + distribution synergies)
        revenue_synergies=300.0,         # Significant cross-selling
        cost_synergies_pct=0.06,         # 6% cost savings
        one_time_costs=90.0,             # Brand integration costs

        # Financing Assumptions
        new_debt_interest_rate=0.045,
        foregone_cash_yield=0.025,
        transaction_fees_pct=0.015,

        # Pro Forma Assumptions
        intangible_amortization_years=15, # Long brand life
        tax_rate=0.24,
        combined_revenue=4800.0,
        combined_ebitda=850.0,
        combined_depreciation=180.0,
        combined_tax_rate=0.24
    )

    return results, excel_file

def demo_high_premium_healthcare_merger():
    """Demo: High Premium Healthcare Merger"""
    print("\n🏥 Demo: High Premium Healthcare Merger")
    print("=" * 60)

    model = ProfessionalMergerModel("HealthSys Corp.", "HEALTH", "SpecialtyClinic Inc.", "SPECIALTY")

    results, excel_file = model.run_merger_model(
        # Acquirer Details (Healthcare system)
        acquirer_share_price=80.0,
        acquirer_shares_outstanding=120.0,
        acquirer_eps=4.50,

        # Target Details (Specialty clinic)
        target_share_price=35.0,
        target_shares_outstanding=15.0,
        target_net_debt=75.0,
        target_eps=2.20,

        # Transaction Details (High premium for strategic value)
        offer_price_per_share=65.0,      # 86% premium
        premium_pct=0.86,

        # Consideration Mix (Cash for clean acquisition)
        cash_pct=0.90,                   # 90% cash
        stock_pct=0.10,                  # 10% stock
        debt_pct=0.00,

        # Synergy Assumptions (Patient referrals, cost sharing)
        revenue_synergies=150.0,         # Referral synergies
        cost_synergies_pct=0.10,         # 10% cost savings
        one_time_costs=45.0,             # Regulatory/compliance costs

        # Financing Assumptions
        new_debt_interest_rate=0.04,
        foregone_cash_yield=0.02,
        transaction_fees_pct=0.010,

        # Pro Forma Assumptions
        intangible_amortization_years=12,
        tax_rate=0.21,                   # Lower healthcare tax rate
        combined_revenue=1800.0,
        combined_ebitda=550.0,
        combined_depreciation=95.0,
        combined_tax_rate=0.21
    )

    return results, excel_file

def demo_leveraged_buyout_structure():
    """Demo: LBO-Style Merger with Debt Financing"""
    print("\n💰 Demo: LBO-Style Merger with Debt Financing")
    print("=" * 60)

    model = ProfessionalMergerModel("PrivateEquity LLC", "PEFUND", "TargetBiz Corp.", "TARGETBIZ")

    results, excel_file = model.run_merger_model(
        # Acquirer Details (PE firm - simplified as stock issuer)
        acquirer_share_price=100.0,      # PE fund valuation
        acquirer_shares_outstanding=10.0, # Small PE entity
        acquirer_eps=0.01,               # Minimal earnings for calculation

        # Target Details (Operating company)
        target_share_price=45.0,
        target_shares_outstanding=80.0,
        target_net_debt=300.0,           # Existing debt to be refinanced
        target_eps=2.80,

        # Transaction Details (LBO-style)
        offer_price_per_share=55.0,      # 22% premium
        premium_pct=0.22,

        # Consideration Mix (Debt-financed)
        cash_pct=0.60,                   # 60% cash
        stock_pct=0.20,                  # 20% equity from PE
        debt_pct=0.20,                   # 20% new debt financing

        # Synergy Assumptions (Operational improvements)
        revenue_synergies=80.0,          # Growth initiatives
        cost_synergies_pct=0.15,         # 15% cost savings (LBO-style)
        one_time_costs=120.0,            # Restructuring costs

        # Financing Assumptions
        new_debt_interest_rate=0.07,     # Higher LBO financing rate
        foregone_cash_yield=0.035,
        transaction_fees_pct=0.020,      # Higher fees for LBO

        # Pro Forma Assumptions
        intangible_amortization_years=8,
        tax_rate=0.25,
        combined_revenue=2500.0,
        combined_ebitda=650.0,
        combined_depreciation=140.0,
        combined_tax_rate=0.25
    )

    return results, excel_file

if __name__ == "__main__":
    print("🤝 Professional M&A Merger Model Demonstration")
    print("=" * 80)

    # Run different merger scenarios
    accretive_results, accretive_excel = demo_accretive_tech_merger()
    defensive_results, defensive_excel = demo_defensive_manufacturing_merger()
    dilutive_results, dilutive_excel = demo_dilutive_consumer_merger()
    healthcare_results, healthcare_excel = demo_high_premium_healthcare_merger()
    lbo_results, lbo_excel = demo_leveraged_buyout_structure()

    print("\n📊 Merger Scenario Comparison:")
    print("=" * 80)

    scenarios = [
        ("Accretive Tech Merger", accretive_results),
        ("Defensive Manufacturing", defensive_results),
        ("Dilutive Consumer", dilutive_results),
        ("High Premium Healthcare", healthcare_results),
        ("LBO-Style Merger", lbo_results)
    ]

    print("Scenario Comparison:")
    print("<25")
    print("-" * 100)

    for name, results in scenarios:
        summary = results['summary_metrics']
        deal = summary['deal_overview']
        accretion = summary['accretion_dilution']

        print("<25"
              "<12.0f"
              "<10.1f"
              "<12.1f"
              "<12.0f")

    print("\n✅ All merger models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {accretive_excel}")
    print(f"   • {defensive_excel}")
    print(f"   • {dilutive_excel}")
    print(f"   • {healthcare_excel}")
    print(f"   • {lbo_excel}")

    print("\n💡 Key Merger Insights:")
    print("=" * 80)
    print("• Accretive Tech: High synergies, stock consideration, EPS accretion")
    print("• Defensive Manufacturing: Strategic value, cash consideration, cost focus")
    print("• Dilutive Consumer: Premium valuation, brand synergies, growth focus")
    print("• High Premium Healthcare: Strategic fit, regulatory considerations")
    print("• LBO-Style: Debt financing, operational improvements, quick returns")
    print("\n🎯 Merger Models are Essential For:")
    print("   - Valuation analysis and premium assessment")
    print("   - Financing structure optimization")
    print("   - EPS accretion/dilution analysis")
    print("   - Synergy quantification and ROI modeling")
    print("   - Investment committee presentations")
    print("   - Shareholder communication materials")
    print("   - Regulatory filing support")
