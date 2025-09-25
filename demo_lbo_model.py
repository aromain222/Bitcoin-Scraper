#!/usr/bin/env python3
"""
LBO Model Demonstration
Shows how to use the Professional LBO Model with different scenarios
"""

from professional_lbo_model import ProfessionalLBOModel

def demo_technology_lbo():
    """Demo: Technology Company LBO"""
    print("🔥 Demo: Technology Company LBO")
    print("=" * 50)

    lbo_model = ProfessionalLBOModel("TechFlow Inc.", "TECHFLOW")

    results, excel_file = lbo_model.run_lbo_model(
        entry_ebitda=400.0,
        entry_multiple=11.5,
        exit_multiple_base=12.5,
        exit_multiple_bull=14.0,
        exit_multiple_bear=10.5,
        senior_debt_pct=0.60,
        mezzanine_pct=0.10,
        equity_pct=0.30,
        senior_rate=0.055,
        mezz_rate=0.105,
        revenue_growth=[0.18, 0.15, 0.12, 0.09, 0.07, 0.05],
        ebitda_margin=0.35,
        forecast_years=6
    )

    return results, excel_file

def demo_manufacturing_lbo():
    """Demo: Manufacturing Company LBO"""
    print("\n🔧 Demo: Manufacturing Company LBO")
    print("=" * 50)

    lbo_model = ProfessionalLBOModel("Industrio Corp.", "INDUST")

    results, excel_file = lbo_model.run_lbo_model(
        entry_ebitda=150.0,
        entry_multiple=9.0,
        exit_multiple_base=10.0,
        exit_multiple_bull=11.5,
        exit_multiple_bear=8.5,
        senior_debt_pct=0.50,
        mezzanine_pct=0.15,
        equity_pct=0.35,
        senior_rate=0.065,
        mezz_rate=0.115,
        revenue_growth=[0.06, 0.05, 0.04, 0.04, 0.03, 0.03],
        ebitda_margin=0.22,
        capex_pct=0.08,
        forecast_years=6
    )

    return results, excel_file

def demo_high_leverage_lbo():
    """Demo: High Leverage LBO Scenario"""
    print("\n💰 Demo: High Leverage LBO Scenario")
    print("=" * 50)

    lbo_model = ProfessionalLBOModel("HighGrowth Ltd.", "HIGHGROW")

    results, excel_file = lbo_model.run_lbo_model(
        entry_ebitda=200.0,
        entry_multiple=14.0,  # Aggressive entry
        exit_multiple_base=11.0,
        exit_multiple_bull=12.5,
        exit_multiple_bear=9.5,
        senior_debt_pct=0.70,  # High leverage
        mezzanine_pct=0.15,
        equity_pct=0.15,  # Low equity contribution
        senior_rate=0.07,
        mezz_rate=0.125,
        revenue_growth=[0.25, 0.20, 0.15, 0.10, 0.08, 0.06],  # High growth
        ebitda_margin=0.30,
        forecast_years=6
    )

    return results, excel_file

if __name__ == "__main__":
    print("🚀 Professional LBO Model Demonstration")
    print("=" * 60)

    # Run different LBO scenarios
    tech_results, tech_excel = demo_technology_lbo()
    mfg_results, mfg_excel = demo_manufacturing_lbo()
    highlev_results, highlev_excel = demo_high_leverage_lbo()

    print("\n📊 Comparative Analysis:")
    print("=" * 60)

    scenarios = [
        ("Technology Company", tech_results),
        ("Manufacturing Company", mfg_results),
        ("High Leverage Scenario", highlev_results)
    ]

    print("Scenario Comparison:")
    print("<25")
    print("-" * 70)

    for name, results in scenarios:
        assumptions = results['assumptions']
        returns = results['returns_analysis']

        print("<25"
              "<10.1f"
              "<10.1f"
              "<10.1f")

    print("\n✅ All LBO models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {highlev_excel}")
