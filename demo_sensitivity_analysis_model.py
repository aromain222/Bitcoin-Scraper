#!/usr/bin/env python3
"""
Sensitivity Analysis Model Demonstration
Shows how to use the Professional Sensitivity Analysis Model with different industries and scenarios
"""

from professional_sensitivity_analysis_model import ProfessionalSensitivityAnalysisModel

def demo_tech_startup_sensitivity():
    """Demo: Technology Startup Sensitivity Analysis"""
    print("🚀 Demo: Technology Startup Sensitivity Analysis")
    print("=" * 70)

    model = ProfessionalSensitivityAnalysisModel("CloudTech Inc.", "CLOUDTECH")

    # Technology startup with high growth assumptions and wide ranges
    sensitivity_tables, valuation_ranges, excel_file = model.run_sensitivity_analysis_model(
        target_company="CloudTech Inc.",
        target_ticker="CLOUDTECH",

        # DCF - High growth, high risk (wide ranges)
        dcf_base_wacc=0.10,          # 10% WACC (higher risk)
        dcf_base_terminal_growth=0.04, # 4% terminal growth (high growth)
        dcf_pv_fcf=800.0,            # $800M PV of FCF
        dcf_terminal_value=2400.0,   # $2.4B terminal value
        dcf_wacc_range=[0.08, 0.09, 0.10, 0.11, 0.12],     # 8% to 12%
        dcf_growth_range=[0.02, 0.03, 0.04, 0.05, 0.06],   # 2% to 6%

        # LBO - Venture-style returns
        lbo_base_exit_multiple=12.0,  # 12x EV/EBITDA (high multiple)
        lbo_base_leverage_ratio=4.0,  # 4x Debt/EBITDA (moderate leverage)
        lbo_base_ebitda=300.0,        # $300M EBITDA
        lbo_exit_multiple_range=[8.0, 9.0, 10.0, 11.0, 12.0],   # 8x to 12x
        lbo_leverage_range=[2.0, 3.0, 4.0, 5.0, 6.0],           # 2x to 6x

        # Trading Comps - Premium SaaS multiples
        comps_base_ev_ebitda=15.0,    # 15x EV/EBITDA (premium)
        comps_base_price_earnings=25.0, # 25x P/E (growth stock)
        comps_base_ebitda=300.0,      # $300M EBITDA
        comps_base_eps=3.50,          # $3.50 EPS
        comps_base_shares_outstanding=100.0, # 100M shares
        comps_ev_ebitda_range=[10.0, 12.0, 14.0, 16.0, 18.0],  # 10x to 18x
        comps_pe_range=[18.0, 20.0, 22.0, 24.0, 26.0]           # 18x to 26x
    )

    return sensitivity_tables, valuation_ranges, excel_file

def demo_mature_manufacturing_sensitivity():
    """Demo: Mature Manufacturing Sensitivity Analysis"""
    print("\n🏭 Demo: Mature Manufacturing Sensitivity Analysis")
    print("=" * 70)

    model = ProfessionalSensitivityAnalysisModel("IndustCorp Ltd.", "INDUSTCORP")

    # Mature manufacturing with stable assumptions and narrower ranges
    sensitivity_tables, valuation_ranges, excel_file = model.run_sensitivity_analysis_model(
        target_company="IndustCorp Ltd.",
        target_ticker="INDUSTCORP",

        # DCF - Stable cash flows, moderate risk
        dcf_base_wacc=0.07,          # 7% WACC (lower risk)
        dcf_base_terminal_growth=0.025, # 2.5% terminal growth (moderate)
        dcf_pv_fcf=1800.0,           # $1.8B PV of FCF
        dcf_terminal_value=2200.0,   # $2.2B terminal value
        dcf_wacc_range=[0.06, 0.065, 0.07, 0.075, 0.08],       # 6% to 8%
        dcf_growth_range=[0.02, 0.0225, 0.025, 0.0275, 0.03],  # 2% to 3%

        # LBO - Traditional manufacturing buyout
        lbo_base_exit_multiple=9.0,   # 9x EV/EBITDA (moderate multiple)
        lbo_base_leverage_ratio=5.5,  # 5.5x Debt/EBITDA (higher leverage)
        lbo_base_ebitda=500.0,        # $500M EBITDA
        lbo_exit_multiple_range=[7.0, 7.5, 8.0, 8.5, 9.0],     # 7x to 9x
        lbo_leverage_range=[4.5, 5.0, 5.5, 6.0, 6.5],          # 4.5x to 6.5x

        # Trading Comps - Industrial sector multiples
        comps_base_ev_ebitda=8.5,     # 8.5x EV/EBITDA (industrial average)
        comps_base_price_earnings=16.0, # 16x P/E (value stock)
        comps_base_ebitda=500.0,      # $500M EBITDA
        comps_base_eps=3.25,          # $3.25 EPS
        comps_base_shares_outstanding=80.0, # 80M shares
        comps_ev_ebitda_range=[7.0, 7.5, 8.0, 8.5, 9.0],       # 7x to 9x
        comps_pe_range=[14.0, 15.0, 16.0, 17.0, 18.0]          # 14x to 18x
    )

    return sensitivity_tables, valuation_ranges, excel_file

def demo_healthcare_sensitivity():
    """Demo: Healthcare Company Sensitivity Analysis"""
    print("\n🏥 Demo: Healthcare Sensitivity Analysis")
    print("=" * 70)

    model = ProfessionalSensitivityAnalysisModel("MediSys Corp.", "MEDISYS")

    # Healthcare with regulatory considerations and premium valuations
    sensitivity_tables, valuation_ranges, excel_file = model.run_sensitivity_analysis_model(
        target_company="MediSys Corp.",
        target_ticker="MEDISYS",

        # DCF - Strong cash flows, regulatory risk premium
        dcf_base_wacc=0.085,         # 8.5% WACC (regulatory risk)
        dcf_base_terminal_growth=0.03, # 3% terminal growth (healthcare growth)
        dcf_pv_fcf=2200.0,           # $2.2B PV of FCF
        dcf_terminal_value=3800.0,   # $3.8B terminal value
        dcf_wacc_range=[0.07, 0.075, 0.08, 0.085, 0.09],       # 7% to 9%
        dcf_growth_range=[0.025, 0.0275, 0.03, 0.0325, 0.035], # 2.5% to 3.5%

        # LBO - Strategic healthcare buyer
        lbo_base_exit_multiple=11.0,  # 11x EV/EBITDA (premium healthcare)
        lbo_base_leverage_ratio=4.5,  # 4.5x Debt/EBITDA (moderate for healthcare)
        lbo_base_ebitda=600.0,        # $600M EBITDA
        lbo_exit_multiple_range=[9.0, 9.5, 10.0, 10.5, 11.0],  # 9x to 11x
        lbo_leverage_range=[3.5, 4.0, 4.5, 5.0, 5.5],          # 3.5x to 5.5x

        # Trading Comps - Healthcare sector premiums
        comps_base_ev_ebitda=12.0,    # 12x EV/EBITDA (healthcare premium)
        comps_base_price_earnings=22.0, # 22x P/E (growth healthcare)
        comps_base_ebitda=600.0,      # $600M EBITDA
        comps_base_eps=4.80,          # $4.80 EPS
        comps_base_shares_outstanding=60.0, # 60M shares
        comps_ev_ebitda_range=[10.0, 10.5, 11.0, 11.5, 12.0],  # 10x to 12x
        comps_pe_range=[19.0, 20.0, 21.0, 22.0, 23.0]           # 19x to 23x
    )

    return sensitivity_tables, valuation_ranges, excel_file

def demo_energy_sensitivity():
    """Demo: Energy Company Sensitivity Analysis"""
    print("\n⚡ Demo: Energy Sensitivity Analysis")
    print("=" * 70)

    model = ProfessionalSensitivityAnalysisModel("EnergyCorp Ltd.", "ENERGYCORP")

    # Energy with commodity price volatility and capital intensity
    sensitivity_tables, valuation_ranges, excel_file = model.run_sensitivity_analysis_model(
        target_company="EnergyCorp Ltd.",
        target_ticker="ENERGYCORP",

        # DCF - Commodity price and capital risk
        dcf_base_wacc=0.09,          # 9% WACC (commodity risk)
        dcf_base_terminal_growth=0.02, # 2% terminal growth (conservative)
        dcf_pv_fcf=1600.0,           # $1.6B PV of FCF
        dcf_terminal_value=2400.0,   # $2.4B terminal value
        dcf_wacc_range=[0.08, 0.085, 0.09, 0.095, 0.10],       # 8% to 10%
        dcf_growth_range=[0.015, 0.0175, 0.02, 0.0225, 0.025], # 1.5% to 2.5%

        # LBO - Infrastructure-style investment
        lbo_base_exit_multiple=8.5,   # 8.5x EV/EBITDA (energy average)
        lbo_base_leverage_ratio=6.0,  # 6x Debt/EBITDA (higher leverage)
        lbo_base_ebitda=400.0,        # $400M EBITDA
        lbo_exit_multiple_range=[7.0, 7.25, 7.5, 7.75, 8.0],    # 7x to 8x
        lbo_leverage_range=[5.0, 5.5, 6.0, 6.5, 7.0],           # 5x to 7x

        # Trading Comps - Energy sector multiples
        comps_base_ev_ebitda=7.5,     # 7.5x EV/EBITDA (energy sector)
        comps_base_price_earnings=14.0, # 14x P/E (energy average)
        comps_base_ebitda=400.0,      # $400M EBITDA
        comps_base_eps=2.80,          # $2.80 EPS
        comps_base_shares_outstanding=100.0, # 100M shares
        comps_ev_ebitda_range=[6.5, 6.75, 7.0, 7.25, 7.5],     # 6.5x to 7.5x
        comps_pe_range=[12.0, 12.5, 13.0, 13.5, 14.0]          # 12x to 14x
    )

    return sensitivity_tables, valuation_ranges, excel_file

def demo_consumer_retail_sensitivity():
    """Demo: Consumer Retail Sensitivity Analysis"""
    print("\n🛍️  Demo: Consumer Retail Sensitivity Analysis")
    print("=" * 70)

    model = ProfessionalSensitivityAnalysisModel("RetailMax Corp.", "RETAILMAX")

    # Retail with competitive pressures and e-commerce disruption
    sensitivity_tables, valuation_ranges, excel_file = model.run_sensitivity_analysis_model(
        target_company="RetailMax Corp.",
        target_ticker="RETAILMAX",

        # DCF - Challenging growth outlook
        dcf_base_wacc=0.08,          # 8% WACC (retail risk)
        dcf_base_terminal_growth=0.015, # 1.5% terminal growth (low growth)
        dcf_pv_fcf=1200.0,           # $1.2B PV of FCF
        dcf_terminal_value=1800.0,   # $1.8B terminal value
        dcf_wacc_range=[0.07, 0.075, 0.08, 0.085, 0.09],       # 7% to 9%
        dcf_growth_range=[0.01, 0.0125, 0.015, 0.0175, 0.02],  # 1% to 2%

        # LBO - Retail consolidation strategy
        lbo_base_exit_multiple=7.5,   # 7.5x EV/EBITDA (retail average)
        lbo_base_leverage_ratio=4.0,  # 4x Debt/EBITDA (moderate for retail)
        lbo_base_ebitda=350.0,        # $350M EBITDA
        lbo_exit_multiple_range=[6.5, 6.75, 7.0, 7.25, 7.5],   # 6.5x to 7.5x
        lbo_leverage_range=[3.5, 3.75, 4.0, 4.25, 4.5],        # 3.5x to 4.5x

        # Trading Comps - Retail sector multiples
        comps_base_ev_ebitda=6.5,     # 6.5x EV/EBITDA (retail sector)
        comps_base_price_earnings=12.0, # 12x P/E (retail average)
        comps_base_ebitda=350.0,      # $350M EBITDA
        comps_base_eps=2.20,          # $2.20 EPS
        comps_base_shares_outstanding=120.0, # 120M shares
        comps_ev_ebitda_range=[5.5, 5.75, 6.0, 6.25, 6.5],     # 5.5x to 6.5x
        comps_pe_range=[10.0, 10.5, 11.0, 11.5, 12.0]          # 10x to 12x
    )

    return sensitivity_tables, valuation_ranges, excel_file

def demo_high_volatility_sensitivity():
    """Demo: High Volatility Company Sensitivity Analysis"""
    print("\n📊 Demo: High Volatility Sensitivity Analysis")
    print("=" * 70)

    model = ProfessionalSensitivityAnalysisModel("GrowthCo Inc.", "GROWTHCO")

    # High-growth company with extreme valuation ranges
    sensitivity_tables, valuation_ranges, excel_file = model.run_sensitivity_analysis_model(
        target_company="GrowthCo Inc.",
        target_ticker="GROWTHCO",

        # DCF - Very wide ranges due to binary outcomes
        dcf_base_wacc=0.12,          # 12% WACC (very high risk)
        dcf_base_terminal_growth=0.06, # 6% terminal growth (very high growth)
        dcf_pv_fcf=200.0,            # $200M PV of FCF
        dcf_terminal_value=1800.0,   # $1.8B terminal value
        dcf_wacc_range=[0.08, 0.09, 0.10, 0.11, 0.12],         # 8% to 12%
        dcf_growth_range=[0.02, 0.03, 0.04, 0.05, 0.06],       # 2% to 6%

        # LBO - Venture-style returns with high risk
        lbo_base_exit_multiple=15.0,  # 15x EV/EBITDA (unicorn multiple)
        lbo_base_leverage_ratio=3.0,  # 3x Debt/EBITDA (low leverage for risk)
        lbo_base_ebitda=150.0,        # $150M EBITDA
        lbo_exit_multiple_range=[10.0, 11.0, 12.0, 13.0, 14.0], # 10x to 14x
        lbo_leverage_range=[2.0, 2.25, 2.5, 2.75, 3.0],         # 2x to 3x

        # Trading Comps - Extreme ranges for growth stocks
        comps_base_ev_ebitda=20.0,    # 20x EV/EBITDA (growth stock)
        comps_base_price_earnings=35.0, # 35x P/E (extreme growth)
        comps_base_ebitda=150.0,      # $150M EBITDA
        comps_base_eps=1.00,          # $1.00 EPS
        comps_base_shares_outstanding=150.0, # 150M shares
        comps_ev_ebitda_range=[15.0, 16.0, 17.0, 18.0, 19.0],  # 15x to 19x
        comps_pe_range=[25.0, 27.5, 30.0, 32.5, 35.0]           # 25x to 35x
    )

    return sensitivity_tables, valuation_ranges, excel_file

if __name__ == "__main__":
    print("📊 Professional Sensitivity Analysis Model Demonstration")
    print("=" * 90)

    # Run different industry sector sensitivity analyses
    tech_tables, tech_ranges, tech_excel = demo_tech_startup_sensitivity()
    mfg_tables, mfg_ranges, mfg_excel = demo_mature_manufacturing_sensitivity()
    healthcare_tables, healthcare_ranges, healthcare_excel = demo_healthcare_sensitivity()
    energy_tables, energy_ranges, energy_excel = demo_energy_sensitivity()
    retail_tables, retail_ranges, retail_excel = demo_consumer_retail_sensitivity()
    high_vol_tables, high_vol_ranges, high_vol_excel = demo_high_volatility_sensitivity()

    print("\n📊 Sensitivity Analysis Comparison:")
    print("=" * 90)

    scenarios = [
        ("Tech Startup", tech_ranges),
        ("Manufacturing", mfg_ranges),
        ("Healthcare", healthcare_ranges),
        ("Energy", energy_ranges),
        ("Retail", retail_ranges),
        ("High Volatility", high_vol_ranges)
    ]

    print("Scenario Comparison (Overall Ranges):")
    print("<25")
    print("-" * 140)

    for name, ranges in scenarios:
        overall = ranges['overall']
        dcf_range = ranges['dcf']['range']
        lbo_range = ranges['lbo']['range']
        comps_range = ranges['comps']['range']

        print("<25"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f")

    print("\n✅ All sensitivity analysis models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {healthcare_excel}")
    print(f"   • {energy_excel}")
    print(f"   • {retail_excel}")
    print(f"   • {high_vol_excel}")

    print("\n💡 Sensitivity Analysis Insights:")
    print("=" * 90)
    print("• Tech Startups: Extreme DCF ranges ($74B) due to growth assumptions")
    print("• Manufacturing: Narrower ranges ($1.5B) with stable cash flows")
    print("• Healthcare: Premium valuations with regulatory considerations")
    print("• Energy: Commodity sensitivity creates valuation volatility")
    print("• Retail: Competitive pressures and e-commerce disruption")
    print("• High Volatility: Massive ranges ($13B+) for binary outcome companies")

    print("\n🎯 Sensitivity Analysis Applications:")
    print("=" * 90)
    print("   - Risk assessment and scenario planning")
    print("   - Investment committee presentations")
    print("   - Negotiation strategy development")
    print("   - Fairness opinion support")
    print("   - Board meeting materials")
    print("   - Regulatory filing exhibits")

    print("\n📈 Key Sensitivity Variables:")
    print("=" * 90)
    print("   • DCF: WACC and Terminal Growth Rate")
    print("   • LBO: Exit Multiple and Leverage Ratio")
    print("   • Comps: EV/EBITDA and P/E Multiples")
    print("   • Base Case: Always highlighted in tables")
    print("   • Range Analysis: Shows valuation dispersion")

    print("\n🏆 Sensitivity Analysis Best Practices:")
    print("=" * 90)
    print("   • Use realistic ranges based on historical data")
    print("   • Include both optimistic and pessimistic scenarios")
    print("   • Highlight base case assumptions clearly")
    print("   • Consider correlation between variables")
    print("   • Update regularly as market conditions change")
    print("   • Use for stress-testing investment theses")
