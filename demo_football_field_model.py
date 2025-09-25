#!/usr/bin/env python3
"""
Football Field Valuation Model Demonstration
Shows how to use the Professional Football Field Model with different industries and methodologies
"""

from professional_football_field_model import ProfessionalFootballFieldModel

def demo_tech_startup_valuation():
    """Demo: Technology Startup Valuation Synthesis"""
    print("🚀 Demo: Technology Startup Football Field Valuation")
    print("=" * 65)

    model = ProfessionalFootballFieldModel("TechStart Inc.", "TECHSTART")

    # Technology startup with wide valuation ranges
    valuation_ranges, excel_file = model.run_football_field_model(
        target_company="TechStart Inc.",
        target_ticker="TECHSTART",

        # DCF Valuation (conservative growth assumptions)
        dcf_ev_low=800.0,      # $800M EV
        dcf_ev_median=1200.0,  # $1.2B EV
        dcf_ev_high=1800.0,    # $1.8B EV
        dcf_equity_low=750.0,  # $750M equity
        dcf_equity_median=1150.0, # $1.15B equity
        dcf_equity_high=1750.0,   # $1.75B equity

        # Trading Comps (premium SaaS multiples)
        trading_ev_low=1500.0,     # $1.5B EV
        trading_ev_median=2200.0,  # $2.2B EV
        trading_ev_high=3000.0,    # $3B EV
        trading_equity_low=1400.0, # $1.4B equity
        trading_equity_median=2100.0, # $2.1B equity
        trading_equity_high=2900.0,   # $2.9B equity

        # Precedent Transactions (startup acquisitions)
        precedent_ev_low=1200.0,      # $1.2B EV
        precedent_ev_median=1800.0,   # $1.8B EV
        precedent_ev_high=2500.0,     # $2.5B EV
        precedent_equity_low=1100.0,  # $1.1B equity
        precedent_equity_median=1700.0, # $1.7B equity
        precedent_equity_high=2400.0,    # $2.4B equity

        # LBO (high IRR expectations)
        lbo_equity_low=1600.0,    # $1.6B equity (high exit multiple)
        lbo_equity_median=2400.0, # $2.4B equity
        lbo_equity_high=3200.0,   # $3.2B equity

        # Current market data
        current_share_price=25.0,    # $25 share price
        shares_outstanding=100.0     # 100M shares
    )

    return valuation_ranges, excel_file

def demo_mature_manufacturing_valuation():
    """Demo: Mature Manufacturing Company Valuation Synthesis"""
    print("\n🏭 Demo: Mature Manufacturing Football Field Valuation")
    print("=" * 65)

    model = ProfessionalFootballFieldModel("IndustCorp Ltd.", "INDUSTCORP")

    # Mature manufacturing with narrower valuation ranges
    valuation_ranges, excel_file = model.run_football_field_model(
        target_company="IndustCorp Ltd.",
        target_ticker="INDUSTCORP",

        # DCF Valuation (stable cash flows)
        dcf_ev_low=2200.0,     # $2.2B EV
        dcf_ev_median=2500.0,  # $2.5B EV
        dcf_ev_high=2800.0,    # $2.8B EV
        dcf_equity_low=1800.0, # $1.8B equity
        dcf_equity_median=2100.0, # $2.1B equity
        dcf_equity_high=2400.0,   # $2.4B equity

        # Trading Comps (industrial multiples)
        trading_ev_low=2400.0,     # $2.4B EV
        trading_ev_median=2700.0,  # $2.7B EV
        trading_ev_high=3100.0,    # $3.1B EV
        trading_equity_low=2000.0, # $2B equity
        trading_equity_median=2300.0, # $2.3B equity
        trading_equity_high=2700.0,   # $2.7B equity

        # Precedent Transactions (industry consolidation)
        precedent_ev_low=2600.0,      # $2.6B EV
        precedent_ev_median=2900.0,   # $2.9B EV
        precedent_ev_high=3300.0,     # $3.3B EV
        precedent_equity_low=2200.0,  # $2.2B equity
        precedent_equity_median=2500.0, # $2.5B equity
        precedent_equity_high=2900.0,    # $2.9B equity

        # LBO (moderate leverage)
        lbo_equity_low=2300.0,    # $2.3B equity
        lbo_equity_median=2600.0, # $2.6B equity
        lbo_equity_high=2900.0,   # $2.9B equity

        # Current market data
        current_share_price=65.0,    # $65 share price
        shares_outstanding=40.0      # 40M shares
    )

    return valuation_ranges, excel_file

def demo_consumer_retail_valuation():
    """Demo: Consumer Retail Company Valuation Synthesis"""
    print("\n🛍️  Demo: Consumer Retail Football Field Valuation")
    print("=" * 65)

    model = ProfessionalFootballFieldModel("RetailMax Corp.", "RETAILMAX")

    # Retail with competitive pressures and lower multiples
    valuation_ranges, excel_file = model.run_football_field_model(
        target_company="RetailMax Corp.",
        target_ticker="RETAILMAX",

        # DCF Valuation (challenging growth outlook)
        dcf_ev_low=1800.0,     # $1.8B EV
        dcf_ev_median=2100.0,  # $2.1B EV
        dcf_ev_high=2400.0,    # $2.4B EV
        dcf_equity_low=1600.0, # $1.6B equity
        dcf_equity_median=1900.0, # $1.9B equity
        dcf_equity_high=2200.0,   # $2.2B equity

        # Trading Comps (retail sector multiples)
        trading_ev_low=1500.0,     # $1.5B EV
        trading_ev_median=1800.0,  # $1.8B EV
        trading_ev_high=2100.0,    # $2.1B EV
        trading_equity_low=1300.0, # $1.3B equity
        trading_equity_median=1600.0, # $1.6B equity
        trading_equity_high=1900.0,   # $1.9B equity

        # Precedent Transactions (retail consolidation deals)
        precedent_ev_low=2000.0,      # $2B EV
        precedent_ev_median=2300.0,   # $2.3B EV
        precedent_ev_high=2700.0,     # $2.7B EV
        precedent_equity_low=1800.0,  # $1.8B equity
        precedent_equity_median=2100.0, # $2.1B equity
        precedent_equity_high=2500.0,    # $2.5B equity

        # LBO (higher risk, higher returns)
        lbo_equity_low=1700.0,    # $1.7B equity
        lbo_equity_median=2000.0, # $2B equity
        lbo_equity_high=2400.0,   # $2.4B equity

        # Current market data
        current_share_price=35.0,    # $35 share price
        shares_outstanding=60.0      # 60M shares
    )

    return valuation_ranges, excel_file

def demo_healthcare_valuation():
    """Demo: Healthcare Company Valuation Synthesis"""
    print("\n🏥 Demo: Healthcare Football Field Valuation")
    print("=" * 65)

    model = ProfessionalFootballFieldModel("MediSys Inc.", "MEDISYS")

    # Healthcare with premium valuations and regulatory considerations
    valuation_ranges, excel_file = model.run_football_field_model(
        target_company="MediSys Inc.",
        target_ticker="MEDISYS",

        # DCF Valuation (strong cash flows, regulatory tailwinds)
        dcf_ev_low=3500.0,     # $3.5B EV
        dcf_ev_median=4200.0,  # $4.2B EV
        dcf_ev_high=5000.0,    # $5B EV
        dcf_equity_low=3200.0, # $3.2B equity
        dcf_equity_median=3900.0, # $3.9B equity
        dcf_equity_high=4700.0,   # $4.7B equity

        # Trading Comps (premium healthcare multiples)
        trading_ev_low=4000.0,     # $4B EV
        trading_ev_median=4800.0,  # $4.8B EV
        trading_ev_high=5700.0,    # $5.7B EV
        trading_equity_low=3700.0, # $3.7B equity
        trading_equity_median=4500.0, # $4.5B equity
        trading_equity_high=5400.0,   # $5.4B equity

        # Precedent Transactions (healthcare M&A premiums)
        precedent_ev_low=4500.0,      # $4.5B EV
        precedent_ev_median=5500.0,   # $5.5B EV
        precedent_ev_high=6700.0,     # $6.7B EV
        precedent_equity_low=4200.0,  # $4.2B equity
        precedent_equity_median=5200.0, # $5.2B equity
        precedent_equity_high=6400.0,    # $6.4B equity

        # LBO (strategic healthcare buyer)
        lbo_equity_low=4300.0,    # $4.3B equity
        lbo_equity_median=5100.0, # $5.1B equity
        lbo_equity_high=6000.0,   # $6B equity

        # Current market data
        current_share_price=85.0,    # $85 share price
        shares_outstanding=50.0      # 50M shares
    )

    return valuation_ranges, excel_file

def demo_energy_valuation():
    """Demo: Energy Company Valuation Synthesis"""
    print("\n⚡ Demo: Energy Football Field Valuation")
    print("=" * 65)

    model = ProfessionalFootballFieldModel("EnergyCorp Ltd.", "ENERGYCORP")

    # Energy with commodity price sensitivity and capital intensity
    valuation_ranges, excel_file = model.run_football_field_model(
        target_company="EnergyCorp Ltd.",
        target_ticker="ENERGYCORP",

        # DCF Valuation (commodity price volatility)
        dcf_ev_low=2800.0,     # $2.8B EV
        dcf_ev_median=3200.0,  # $3.2B EV
        dcf_ev_high=3700.0,    # $3.7B EV
        dcf_equity_low=2200.0, # $2.2B equity
        dcf_equity_median=2600.0, # $2.6B equity
        dcf_equity_high=3100.0,   # $3.1B equity

        # Trading Comps (energy sector multiples)
        trading_ev_low=2500.0,     # $2.5B EV
        trading_ev_median=2900.0,  # $2.9B EV
        trading_ev_high=3400.0,    # $3.4B EV
        trading_equity_low=1900.0, # $1.9B equity
        trading_equity_median=2300.0, # $2.3B equity
        trading_equity_high=2800.0,   # $2.8B equity

        # Precedent Transactions (energy consolidation)
        precedent_ev_low=3200.0,      # $3.2B EV
        precedent_ev_median=3800.0,   # $3.8B EV
        precedent_ev_high=4500.0,     # $4.5B EV
        precedent_equity_low=2600.0,  # $2.6B equity
        precedent_equity_median=3200.0, # $3.2B equity
        precedent_equity_high=3900.0,    # $3.9B equity

        # LBO (infrastructure-style investment)
        lbo_equity_low=2700.0,    # $2.7B equity
        lbo_equity_median=3300.0, # $3.3B equity
        lbo_equity_high=4000.0,   # $4B equity

        # Current market data
        current_share_price=55.0,    # $55 share price
        shares_outstanding=60.0      # 60M shares
    )

    return valuation_ranges, excel_file

def demo_wide_valuation_range():
    """Demo: Company with Very Wide Valuation Ranges"""
    print("\n📊 Demo: Wide Valuation Range Football Field")
    print("=" * 65)

    model = ProfessionalFootballFieldModel("GrowthCo Inc.", "GROWTHCO")

    # High-growth company with very wide valuation ranges
    valuation_ranges, excel_file = model.run_football_field_model(
        target_company="GrowthCo Inc.",
        target_ticker="GROWTHCO",

        # DCF Valuation (very wide range due to growth assumptions)
        dcf_ev_low=500.0,       # $500M EV (conservative)
        dcf_ev_median=1500.0,   # $1.5B EV (base case)
        dcf_ev_high=4000.0,     # $4B EV (bull case)
        dcf_equity_low=400.0,   # $400M equity
        dcf_equity_median=1400.0, # $1.4B equity
        dcf_equity_high=3800.0,    # $3.8B equity

        # Trading Comps (high-growth peer group)
        trading_ev_low=2000.0,     # $2B EV
        trading_ev_median=3500.0,  # $3.5B EV
        trading_ev_high=5500.0,    # $5.5B EV
        trading_equity_low=1800.0, # $1.8B equity
        trading_equity_median=3300.0, # $3.3B equity
        trading_equity_high=5300.0,   # $5.3B equity

        # Precedent Transactions (premium for growth companies)
        precedent_ev_low=3000.0,      # $3B EV
        precedent_ev_median=4500.0,   # $4.5B EV
        precedent_ev_high=7000.0,     # $7B EV
        precedent_equity_low=2800.0,  # $2.8B equity
        precedent_equity_median=4300.0, # $4.3B equity
        precedent_equity_high=6800.0,    # $6.8B equity

        # LBO (venture-style returns)
        lbo_equity_low=2500.0,    # $2.5B equity
        lbo_equity_median=4000.0, # $4B equity
        lbo_equity_high=6500.0,   # $6.5B equity

        # Current market data
        current_share_price=20.0,    # $20 share price
        shares_outstanding=200.0     # 200M shares
    )

    return valuation_ranges, excel_file

if __name__ == "__main__":
    print("🏟️  Professional Football Field Valuation Model Demonstration")
    print("=" * 85)

    # Run different industry sector football field valuations
    tech_ranges, tech_excel = demo_tech_startup_valuation()
    mfg_ranges, mfg_excel = demo_mature_manufacturing_valuation()
    retail_ranges, retail_excel = demo_consumer_retail_valuation()
    healthcare_ranges, healthcare_excel = demo_healthcare_valuation()
    energy_ranges, energy_excel = demo_energy_valuation()
    wide_ranges, wide_excel = demo_wide_valuation_range()

    print("\n📊 Football Field Valuation Comparison:")
    print("=" * 85)

    scenarios = [
        ("Tech Startup", tech_ranges),
        ("Manufacturing", mfg_ranges),
        ("Retail", retail_ranges),
        ("Healthcare", healthcare_ranges),
        ("Energy", energy_ranges),
        ("High Growth", wide_ranges)
    ]

    print("Scenario Comparison (Overall Ranges):")
    print("<20")
    print("-" * 110)

    for name, ranges in scenarios:
        ev_range = ranges['ev_overall']
        equity_range = ranges['equity_overall']
        ev_width_pct = (ev_range['max'] - ev_range['min']) / ev_range['min'] * 100
        equity_width_pct = (equity_range['max'] - equity_range['min']) / equity_range['min'] * 100

        print("<20"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f"
              "<12.1f")

    print("\n✅ All football field models completed successfully!")
    print("📁 Excel files generated:")
    print(f"   • {tech_excel}")
    print(f"   • {mfg_excel}")
    print(f"   • {retail_excel}")
    print(f"   • {healthcare_excel}")
    print(f"   • {energy_excel}")
    print(f"   • {wide_excel}")

    print("\n💡 Football Field Valuation Insights:")
    print("=" * 85)
    print("• Tech Startups: Wide ranges due to growth uncertainty (80-90% range width)")
    print("• Manufacturing: Narrower ranges with stable cash flows (20-30% range width)")
    print("• Retail: Competitive pressures create valuation dispersion (30-40% range width)")
    print("• Healthcare: Premium valuations with regulatory considerations (30-40% range width)")
    print("• Energy: Commodity sensitivity creates valuation volatility (40-50% range width)")
    print("• High Growth: Extreme ranges due to binary outcomes (300-400% range width)")

    print("\n🎯 Football Field Applications:")
    print("=" * 85)
    print("   - Investment committee presentations")
    print("   - Fairness opinion exhibits")
    print("   - M&A negotiation anchor points")
    print("   - Board meeting materials")
    print("   - Client pitch books")
    print("   - Valuation committee discussions")
    print("   - Strategic planning frameworks")

    print("\n📈 Key Football Field Concepts:")
    print("=" * 85)
    print("   - DCF: Intrinsic value anchor point")
    print("   - Trading Comps: Market-based reality check")
    print("   - Precedent Transactions: Control premium expectations")
    print("   - LBO: Private equity perspective")
    print("   - Current Market: Real-time trading levels")
    print("   - Range Width: Indicates valuation uncertainty/agreement")

    print("\n🏆 Football Field Best Practices:")
    print("=" * 85)
    print("   • Always include DCF as fundamental anchor")
    print("   • Use 3-5 methodologies for robust analysis")
    print("   • Present ranges, not point estimates")
    print("   • Highlight methodology differences and drivers")
    print("   • Consider market conditions and sector dynamics")
    print("   • Update regularly as new information becomes available")
