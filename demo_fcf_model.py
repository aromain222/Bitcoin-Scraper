#!/usr/bin/env python3
"""
Free Cash Flow Model Demonstration
Shows how to use the Professional FCF Model with different scenarios and industries
"""

from professional_fcf_model import ProfessionalFCFModel

def demo_technology_company():
    """Demo: Technology Company FCF Model"""
    print("🔥 Demo: Technology Company FCF Model")
    print("=" * 50)

    model = ProfessionalFCFModel("TechFlow Inc.", "TECHFLOW")

    results, excel_file = model.run_fcf_model(
        # Company Basics
        starting_revenue=1200.0,  # $1.2B starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.15, 0.12, 0.10, 0.08, 0.06],  # High growth tech
        growth_bull=[0.20, 0.18, 0.15, 0.12, 0.09],
        growth_bear=[0.10, 0.08, 0.06, 0.04, 0.03],

        # Operating Margins (%)
        ebitda_margin=0.35,  # 35% EBITDA margin (SaaS)
        ebit_margin=0.30,    # 30% EBIT margin

        # Depreciation & Amortization (% of revenue)
        depreciation_pct=0.03,  # Lower for tech (less equipment)

        # Capital Expenditures (% of revenue)
        capex_pct=0.02,  # Lower CapEx for tech

        # Net Working Capital (% of revenue)
        nwc_pct=0.08,  # Moderate NWC

        # Tax Rate
        tax_rate=0.21,  # Lower effective tax rate

        # Terminal Value
        terminal_growth_rate=0.03,  # 3% growth (tech)
        wacc=0.10,  # 10% WACC

        forecast_years=5
    )

    return results, excel_file

def demo_manufacturing_company():
    """Demo: Manufacturing Company FCF Model"""
    print("\n🔧 Demo: Manufacturing Company FCF Model")
    print("=" * 50)

    model = ProfessionalFCFModel("Industrio Corp.", "INDUST")

    results, excel_file = model.run_fcf_model(
        # Company Basics
        starting_revenue=800.0,   # $800M starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.06, 0.05, 0.04, 0.04, 0.03],  # Moderate growth
        growth_bull=[0.08, 0.07, 0.06, 0.05, 0.04],
        growth_bear=[0.04, 0.03, 0.02, 0.02, 0.01],

        # Operating Margins (%)
        ebitda_margin=0.18,  # 18% EBITDA margin
        ebit_margin=0.12,    # 12% EBIT margin

        # Depreciation & Amortization (% of revenue)
        depreciation_pct=0.08,  # Higher for manufacturing

        # Capital Expenditures (% of revenue)
        capex_pct=0.10,  # Higher CapEx for equipment

        # Net Working Capital (% of revenue)
        nwc_pct=0.15,  # High NWC (inventory + AR)

        # Tax Rate
        tax_rate=0.25,

        # Terminal Value
        terminal_growth_rate=0.025,  # 2.5% growth
        wacc=0.09,  # 9% WACC

        forecast_years=5
    )

    return results, excel_file

def demo_consumer_retail():
    """Demo: Consumer Retail Company FCF Model"""
    print("\n🛍️  Demo: Consumer Retail FCF Model")
    print("=" * 50)

    model = ProfessionalFCFModel("RetailMax Corp.", "RETAIL")

    results, excel_file = model.run_fcf_model(
        # Company Basics
        starting_revenue=2000.0,  # $2B starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.04, 0.03, 0.03, 0.02, 0.02],  # Low growth retail
        growth_bull=[0.06, 0.05, 0.04, 0.03, 0.03],
        growth_bear=[0.02, 0.01, 0.01, 0.00, 0.00],

        # Operating Margins (%)
        ebitda_margin=0.08,  # 8% EBITDA margin (retail)
        ebit_margin=0.05,    # 5% EBIT margin

        # Depreciation & Amortization (% of revenue)
        depreciation_pct=0.02,  # Lower depreciation

        # Capital Expenditures (% of revenue)
        capex_pct=0.03,  # Moderate CapEx

        # Net Working Capital (% of revenue)
        nwc_pct=0.12,  # High NWC (inventory heavy)

        # Tax Rate
        tax_rate=0.25,

        # Terminal Value
        terminal_growth_rate=0.02,  # 2% growth
        wacc=0.085,  # 8.5% WACC

        forecast_years=5
    )

    return results, excel_file

def demo_healthcare_company():
    """Demo: Healthcare Company FCF Model"""
    print("\n🏥 Demo: Healthcare Company FCF Model")
    print("=" * 50)

    model = ProfessionalFCFModel("MediCare Plus.", "MEDICARE")

    results, excel_file = model.run_fcf_model(
        # Company Basics
        starting_revenue=600.0,   # $600M starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.08, 0.07, 0.06, 0.05, 0.04],  # Steady healthcare growth
        growth_bull=[0.12, 0.10, 0.08, 0.07, 0.06],
        growth_bear=[0.04, 0.03, 0.03, 0.02, 0.02],

        # Operating Margins (%)
        ebitda_margin=0.22,  # 22% EBITDA margin
        ebit_margin=0.18,    # 18% EBIT margin

        # Depreciation & Amortization (% of revenue)
        depreciation_pct=0.04,  # Moderate depreciation

        # Capital Expenditures (% of revenue)
        capex_pct=0.06,  # Moderate CapEx

        # Net Working Capital (% of revenue)
        nwc_pct=0.08,  # Moderate NWC

        # Tax Rate
        tax_rate=0.21,  # Lower tax rate

        # Terminal Value
        terminal_growth_rate=0.025,  # 2.5% growth
        wacc=0.085,  # 8.5% WACC

        forecast_years=5
    )

    return results, excel_file

def demo_energy_company():
    """Demo: Energy Company FCF Model"""
    print("\n⚡ Demo: Energy Company FCF Model")
    print("=" * 50)

    model = ProfessionalFCFModel("EnergyCorp Ltd.", "ENERGY")

    results, excel_file = model.run_fcf_model(
        # Company Basics
        starting_revenue=1500.0,  # $1.5B starting revenue

        # Revenue Growth Scenarios (%)
        growth_base=[0.03, 0.02, 0.02, 0.01, 0.01],  # Low growth energy
        growth_bull=[0.05, 0.04, 0.03, 0.02, 0.02],
        growth_bear=[0.01, 0.00, 0.00, -0.01, -0.01],

        # Operating Margins (%)
        ebitda_margin=0.25,  # 25% EBITDA margin
        ebit_margin=0.20,    # 20% EBIT margin

        # Depreciation & Amortization (% of revenue)
        depreciation_pct=0.10,  # High depreciation (assets)

        # Capital Expenditures (% of revenue)
        capex_pct=0.12,  # High CapEx (maintenance + growth)

        # Net Working Capital (% of revenue)
        nwc_pct=0.06,  # Lower NWC

        # Tax Rate
        tax_rate=0.25,

        # Terminal Value
        terminal_growth_rate=0.015,  # 1.5% growth
        wacc=0.08,  # 8% WACC

        forecast_years=5
    )

    return results, excel_file

if __name__ == "__main__":
    print("💰 Professional FCF Model Demonstration")
    print("=" * 60)

    # Run different industry scenarios
    tech_results, tech_excel = demo_technology_company()
    mfg_results, mfg_excel = demo_manufacturing_company()
    retail_results, retail_excel = demo_consumer_retail()
    healthcare_results, healthcare_excel = demo_healthcare_company()
    energy_results, energy_excel = demo_energy_company()

    print("\n📊 Industry Comparison:")
    print("=" * 80)

    industries = [
        ("Technology", tech_results),
        ("Manufacturing", mfg_results),
        ("Retail", retail_results),
        ("Healthcare", healthcare_results),
        ("Energy", energy_results)
    ]

    print("Industry Comparison (Base Case):")
    print("<20")
    print("-" * 100)

    for name, results in industries:
        summary = results['summary_metrics']['base']
        fcf_data = results['fcf_forecasts']['base']

        print("<20"
              "<15.0f"
              "<12.1f"
              "<15.0f"
              "<15.0f")

    print("\n✅ All FCF models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {retail_excel}")
    print(f"   • {healthcare_excel}")
    print(f"   • {energy_excel}")

    print("\n💡 Key Industry Insights:")
    print("=" * 80)
    print("• Technology: Highest UFCF margins (35%), lowest CapEx, strongest growth")
    print("• Manufacturing: High CapEx requirements, significant NWC investment")
    print("• Retail: Lowest margins, inventory-heavy, stable but slow growth")
    print("• Healthcare: Steady growth, moderate margins, regulated environment")
    print("• Energy: High CapEx, volatile commodity exposure, long-term assets")
    print("\n🎯 FCF Models are Perfect For:")
    print("   - DCF valuation inputs (terminal value calculations)")
    print("   - LBO debt paydown capacity analysis")
    print("   - Cash generation capacity assessment")
    print("   - Investment memo exhibits and pitch decks")
    print("   - M&A target evaluation and synergy analysis")
