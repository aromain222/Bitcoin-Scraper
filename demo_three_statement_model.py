#!/usr/bin/env python3
"""
Three-Statement Financial Model Demonstration
Shows how to use the Professional Three-Statement Model with different scenarios
"""

from professional_three_statement_model import ProfessionalThreeStatementModel

def demo_technology_company():
    """Demo: Technology Company Three-Statement Model"""
    print("🔥 Demo: Technology Company Three-Statement Model")
    print("=" * 60)

    model = ProfessionalThreeStatementModel("TechFlow Inc.", "TECHFLOW")

    results, excel_file = model.run_three_statement_model(
        # Company Basics
        starting_revenue=1200.0,  # $1.2B starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.15, 0.12, 0.10, 0.08, 0.06],  # High growth tech company
        growth_bull=[0.20, 0.18, 0.15, 0.12, 0.09],
        growth_bear=[0.10, 0.08, 0.06, 0.04, 0.03],

        # Operating Margins (%)
        gross_margin=0.70,     # 70% gross margin (software/SaaS)
        ebitda_margin=0.35,    # 35% EBITDA margin
        ebit_margin=0.30,      # 30% EBIT margin

        # Depreciation & CapEx (% of revenue)
        depreciation_pct=0.03,  # Lower for tech (less equipment)
        capex_pct=0.02,         # Lower CapEx for tech

        # Working Capital (% of revenue)
        ar_pct=0.20,            # High AR for B2B SaaS
        inventory_pct=0.02,     # Minimal inventory
        ap_pct=0.06,            # Lower AP
        other_current_liab_pct=0.03,

        # Debt Schedule
        opening_debt=200.0,     # $200M debt (conservative)
        interest_rate=0.055,    # 5.5%
        annual_amortization=40.0,  # $40M/year

        # Other Assumptions
        tax_rate=0.21,          # Lower effective tax rate
        dividend_payout=0.20,   # 20% payout
        starting_cash=300.0,
        forecast_years=5
    )

    return results, excel_file

def demo_manufacturing_company():
    """Demo: Manufacturing Company Three-Statement Model"""
    print("\n🔧 Demo: Manufacturing Company Three-Statement Model")
    print("=" * 60)

    model = ProfessionalThreeStatementModel("Industrio Corp.", "INDUST")

    results, excel_file = model.run_three_statement_model(
        # Company Basics
        starting_revenue=800.0,   # $800M starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.06, 0.05, 0.04, 0.04, 0.03],  # Moderate growth
        growth_bull=[0.08, 0.07, 0.06, 0.05, 0.04],
        growth_bear=[0.04, 0.03, 0.02, 0.02, 0.01],

        # Operating Margins (%)
        gross_margin=0.45,       # 45% gross margin (manufacturing)
        ebitda_margin=0.18,      # 18% EBITDA margin
        ebit_margin=0.12,        # 12% EBIT margin

        # Depreciation & CapEx (% of revenue)
        depreciation_pct=0.08,   # Higher for manufacturing
        capex_pct=0.10,          # Higher CapEx for equipment

        # Working Capital (% of revenue)
        ar_pct=0.12,             # Moderate AR
        inventory_pct=0.18,      # High inventory
        ap_pct=0.10,             # Higher AP
        other_current_liab_pct=0.04,

        # Debt Schedule
        opening_debt=400.0,      # $400M debt
        interest_rate=0.065,     # 6.5%
        annual_amortization=60.0,  # $60M/year

        # Other Assumptions
        tax_rate=0.25,
        dividend_payout=0.40,    # 40% payout
        starting_cash=150.0,
        forecast_years=5
    )

    return results, excel_file

def demo_retail_company():
    """Demo: Retail Company Three-Statement Model"""
    print("\n🛍️  Demo: Retail Company Three-Statement Model")
    print("=" * 60)

    model = ProfessionalThreeStatementModel("RetailMax Corp.", "RETAIL")

    results, excel_file = model.run_three_statement_model(
        # Company Basics
        starting_revenue=2000.0,  # $2B starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.04, 0.03, 0.03, 0.02, 0.02],  # Low growth retail
        growth_bull=[0.06, 0.05, 0.04, 0.03, 0.03],
        growth_bear=[0.02, 0.01, 0.01, 0.00, 0.00],

        # Operating Margins (%)
        gross_margin=0.25,       # 25% gross margin (retail)
        ebitda_margin=0.08,      # 8% EBITDA margin
        ebit_margin=0.05,        # 5% EBIT margin

        # Depreciation & CapEx (% of revenue)
        depreciation_pct=0.02,   # Lower depreciation
        capex_pct=0.03,          # Moderate CapEx

        # Working Capital (% of revenue)
        ar_pct=0.03,             # Low AR
        inventory_pct=0.15,      # High inventory
        ap_pct=0.12,             # High AP
        other_current_liab_pct=0.06,

        # Debt Schedule
        opening_debt=800.0,      # $800M debt
        interest_rate=0.07,      # 7%
        annual_amortization=100.0,  # $100M/year

        # Other Assumptions
        tax_rate=0.25,
        dividend_payout=0.60,    # 60% payout
        starting_cash=400.0,
        forecast_years=5
    )

    return results, excel_file

def demo_high_growth_startup():
    """Demo: High-Growth Startup Three-Statement Model"""
    print("\n🚀 Demo: High-Growth Startup Three-Statement Model")
    print("=" * 60)

    model = ProfessionalThreeStatementModel("GrowthCo Ltd.", "GROWTH")

    results, excel_file = model.run_three_statement_model(
        # Company Basics
        starting_revenue=50.0,    # $50M starting revenue (small startup)

        # Revenue Growth Scenarios (%)
        growth_base=[0.50, 0.40, 0.30, 0.20, 0.15],  # Hyper growth
        growth_bull=[0.70, 0.60, 0.45, 0.30, 0.20],
        growth_bear=[0.35, 0.25, 0.18, 0.12, 0.08],

        # Operating Margins (%)
        gross_margin=0.75,       # 75% gross margin (software)
        ebitda_margin=0.15,      # 15% EBITDA margin (early stage)
        ebit_margin=0.08,        # 8% EBIT margin

        # Depreciation & CapEx (% of revenue)
        depreciation_pct=0.02,   # Minimal depreciation
        capex_pct=0.05,          # Moderate CapEx for growth

        # Working Capital (% of revenue)
        ar_pct=0.25,             # High AR (SaaS)
        inventory_pct=0.01,      # Minimal inventory
        ap_pct=0.05,             # Lower AP
        other_current_liab_pct=0.02,

        # Debt Schedule
        opening_debt=20.0,       # $20M debt (startup level)
        interest_rate=0.08,      # 8% (higher risk)
        annual_amortization=5.0,  # $5M/year

        # Other Assumptions
        tax_rate=0.21,
        dividend_payout=0.0,     # No dividends (reinvesting)
        starting_cash=30.0,      # $30M starting cash
        forecast_years=5
    )

    return results, excel_file

if __name__ == "__main__":
    print("🏢 Professional Three-Statement Financial Model Demonstration")
    print("=" * 70)

    # Run different company scenarios
    tech_results, tech_excel = demo_technology_company()
    mfg_results, mfg_excel = demo_manufacturing_company()
    retail_results, retail_excel = demo_retail_company()
    startup_results, startup_excel = demo_high_growth_startup()

    print("\n📊 Comparative Analysis:")
    print("=" * 70)

    scenarios = [
        ("Technology Company", tech_results),
        ("Manufacturing Company", mfg_results),
        ("Retail Company", retail_results),
        ("High-Growth Startup", startup_results)
    ]

    print("Scenario Comparison:")
    print("<25")
    print("-" * 85)

    for name, results in scenarios:
        assumptions = results['assumptions']
        base_income = results['income_statements']['base']
        base_balance = results['balance_sheets']['base']

        print("<25"
              "<15.1f"
              "<15.0f"
              "<15.0f"
              "<12.0f")

    print("\n✅ All three-statement models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {retail_excel}")
    print(f"   • {startup_excel}")

    print("\n💡 Key Insights:")
    print("=" * 70)
    print("• Technology Company: High margins, low CapEx, strong cash generation")
    print("• Manufacturing Company: Moderate margins, high CapEx, significant working capital")
    print("• Retail Company: Low margins, high inventory, steady but slow growth")
    print("• High-Growth Startup: Volatile growth, reinvestment focus, high AR")
    print("\n🎯 Each model demonstrates how different business models affect:")
    print("   - Cash flow generation and working capital requirements")
    print("   - Balance sheet structure and debt capacity")
    print("   - Income statement margins and profitability")
    print("   - Overall financial health and growth trajectory")
