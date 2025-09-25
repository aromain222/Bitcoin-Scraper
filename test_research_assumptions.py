#!/usr/bin/env python3
"""
Test Script for Research-Based Financial Assumptions
Demonstrates comprehensive debt, capital structure, and valuation assumptions
"""

import sys
import os
sys.path.append('financial-models-app/backend')

def test_research_assumptions():
    """Test the research-based assumptions system"""
    print("🔬 RESEARCH-BASED FINANCIAL ASSUMPTIONS TEST")
    print("=" * 80)
    
    try:
        from enhanced_assumptions_research import (
            get_research_based_assumptions,
            get_debt_assumptions,
            get_valuation_assumptions
        )
        
        # Test companies across different industries
        test_companies = [
            ("Microsoft Corporation", "Technology - Software"),
            ("Apple Inc.", "Technology - Hardware"),
            ("JPMorgan Chase & Co.", "Financial Services"),
            ("Johnson & Johnson", "Healthcare - Pharmaceuticals"),
            ("Procter & Gamble", "Consumer Goods"),
            ("ExxonMobil Corporation", "Energy"),
            ("Simon Property Group", "Real Estate")
        ]
        
        for company_name, industry in test_companies:
            print(f"\n🏢 TESTING: {company_name}")
            print("-" * 60)
            
            # Get comprehensive assumptions
            assumptions = get_research_based_assumptions(company_name, None, industry)
            
            # Display key metrics
            print(f"📊 KEY METRICS:")
            print(f"   💰 Debt/Equity Ratio: {assumptions['debt_to_equity']:.2f}")
            print(f"   🏦 Debt/EBITDA: {assumptions['debt_to_ebitda']:.1f}x")
            print(f"   📈 Interest Coverage: {assumptions['interest_coverage']:.1f}x")
            print(f"   💵 Current Ratio: {assumptions['current_ratio']:.1f}")
            print(f"   🏦 WACC: {assumptions['wacc']*100:.1f}%")
            print(f"   📈 Revenue Growth (Y1): {assumptions['revenue_growth'][0]*100:.1f}%")
            print(f"   🎯 EBITDA Margin: {assumptions['ebitda_margin']*100:.1f}%")
            
            # Display capital structure
            cap_structure = assumptions['capital_structure']
            print(f"\n🏗️ CAPITAL STRUCTURE:")
            print(f"   🎯 Target Debt Ratio: {cap_structure['target_debt_ratio']*100:.1f}%")
            print(f"   💰 Cost of Debt: {cap_structure['cost_of_debt']*100:.1f}%")
            print(f"   📈 Cost of Equity: {cap_structure['cost_of_equity']*100:.1f}%")
            print(f"   💸 Dividend Payout: {cap_structure['dividend_payout_ratio']*100:.1f}%")
            print(f"   🔄 Share Repurchase: {cap_structure['share_repurchase_pct_fcf']*100:.1f}% of FCF")
            
            # Display working capital
            wc = assumptions['working_capital_days']
            print(f"\n💼 WORKING CAPITAL:")
            print(f"   📦 Days Sales in Inventory: {wc['dsi']} days")
            print(f"   📊 Days Sales Outstanding: {wc['dso']} days")
            print(f"   💳 Days Payable Outstanding: {wc['dpo']} days")
            print(f"   💰 Prepaid Expenses: {wc['prepaid_pct_revenue']*100:.1f}% of revenue")
            print(f"   🏦 Accrued Expenses: {wc['accrued_pct_revenue']*100:.1f}% of revenue")
            
            # Display valuation metrics
            val_metrics = assumptions['valuation_metrics']
            print(f"\n💰 VALUATION METRICS:")
            print(f"   📊 EV/EBITDA: {val_metrics['ev_ebitda']:.1f}x")
            print(f"   📈 EV/Revenue: {val_metrics['ev_revenue']:.1f}x")
            print(f"   📊 P/E Ratio: {val_metrics['pe_ratio']:.1f}x")
            print(f"   📈 P/B Ratio: {val_metrics['pb_ratio']:.1f}x")
            print(f"   📊 P/S Ratio: {val_metrics['ps_ratio']:.1f}x")
            
            # Display research metadata
            metadata = assumptions['research_metadata']
            print(f"\n🔬 RESEARCH METADATA:")
            print(f"   📅 Research Date: {metadata['research_date']}")
            print(f"   🏭 Industry: {metadata['industry_detected']} → {metadata['industry_category']}")
            print(f"   📊 Market Condition: {metadata['market_condition']}")
            print(f"   🎯 Confidence Level: {metadata['confidence_level']}")
            print(f"   📚 Data Sources: {len(metadata['data_sources'])} sources")
            
            print("\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing research assumptions: {e}")
        return False

def test_debt_specific_assumptions():
    """Test debt-specific assumptions"""
    print("\n💰 DEBT ASSUMPTIONS DEEP DIVE")
    print("=" * 60)
    
    try:
        from enhanced_assumptions_research import get_debt_assumptions
        
        test_companies = [
            ("Microsoft Corporation", "Technology - Software"),
            ("JPMorgan Chase & Co.", "Financial Services"),
            ("ExxonMobil Corporation", "Energy")
        ]
        
        for company_name, industry in test_companies:
            print(f"\n🏢 {company_name}")
            print("-" * 40)
            
            debt_assumptions = get_debt_assumptions(company_name, industry)
            
            # Debt metrics
            debt_metrics = debt_assumptions['debt_metrics']
            print(f"📊 DEBT METRICS:")
            print(f"   💰 Debt/Equity: {debt_metrics['debt_to_equity']:.2f}")
            print(f"   🏦 Debt/EBITDA: {debt_metrics['debt_to_ebitda']:.1f}x")
            print(f"   📈 Interest Coverage: {debt_metrics['interest_coverage']:.1f}x")
            print(f"   💵 Current Ratio: {debt_metrics['current_ratio']:.1f}")
            print(f"   ⚡ Quick Ratio: {debt_metrics['quick_ratio']:.1f}")
            print(f"   💰 Cash Ratio: {debt_metrics['cash_ratio']:.1f}")
            
            # Cost of capital
            cost_capital = debt_assumptions['cost_of_capital']
            print(f"\n💰 COST OF CAPITAL:")
            print(f"   🏦 WACC: {cost_capital['wacc']*100:.1f}%")
            print(f"   💰 Cost of Debt: {cost_capital['cost_of_debt']*100:.1f}%")
            print(f"   📈 Cost of Equity: {cost_capital['cost_of_equity']*100:.1f}%")
            
            # Working capital
            wc = debt_assumptions['working_capital']
            print(f"\n💼 WORKING CAPITAL DAYS:")
            print(f"   📦 DSI: {wc['dsi']} days")
            print(f"   📊 DSO: {wc['dso']} days")
            print(f"   💳 DPO: {wc['dpo']} days")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing debt assumptions: {e}")
        return False

def test_valuation_assumptions():
    """Test valuation-specific assumptions"""
    print("\n💰 VALUATION ASSUMPTIONS DEEP DIVE")
    print("=" * 60)
    
    try:
        from enhanced_assumptions_research import get_valuation_assumptions
        
        test_companies = [
            ("Microsoft Corporation", "Technology - Software"),
            ("Apple Inc.", "Technology - Hardware"),
            ("JPMorgan Chase & Co.", "Financial Services")
        ]
        
        for company_name, industry in test_companies:
            print(f"\n🏢 {company_name}")
            print("-" * 40)
            
            val_assumptions = get_valuation_assumptions(company_name, industry)
            
            # Valuation metrics
            val_metrics = val_assumptions['valuation_metrics']
            print(f"💰 VALUATION MULTIPLES:")
            print(f"   📊 EV/EBITDA: {val_metrics['ev_ebitda']:.1f}x")
            print(f"   📈 EV/Revenue: {val_metrics['ev_revenue']:.1f}x")
            print(f"   📊 P/E Ratio: {val_metrics['pe_ratio']:.1f}x")
            print(f"   📈 P/B Ratio: {val_metrics['pb_ratio']:.1f}x")
            print(f"   📊 P/S Ratio: {val_metrics['ps_ratio']:.1f}x")
            
            # Growth assumptions
            growth = val_assumptions['growth_assumptions']
            print(f"\n📈 GROWTH ASSUMPTIONS:")
            print(f"   📊 Revenue Growth (5 years): {[f'{g*100:.1f}%' for g in growth['revenue_growth']]}")
            print(f"   🎯 Terminal Growth: {growth['terminal_growth']*100:.1f}%")
            
            # Profitability
            profitability = val_assumptions['profitability']
            print(f"\n📊 PROFITABILITY METRICS:")
            print(f"   🎯 EBITDA Margin: {profitability['ebitda_margin']*100:.1f}%")
            print(f"   💰 Gross Margin: {profitability['gross_margin']*100:.1f}%")
            print(f"   📈 ROA: {profitability['roa']*100:.1f}%")
            print(f"   📊 ROE: {profitability['roe']*100:.1f}%")
            print(f"   🎯 ROIC: {profitability['roic']*100:.1f}%")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing valuation assumptions: {e}")
        return False

def test_market_conditions():
    """Test different market condition scenarios"""
    print("\n📊 MARKET CONDITION SCENARIOS")
    print("=" * 60)
    
    try:
        from enhanced_assumptions_research import get_research_based_assumptions
        
        company_name = "Microsoft Corporation"
        industry = "Technology - Software"
        
        market_conditions = ['current', 'bull_market', 'bear_market']
        
        for condition in market_conditions:
            print(f"\n📈 {condition.upper().replace('_', ' ')} SCENARIO")
            print("-" * 40)
            
            assumptions = get_research_based_assumptions(company_name, None, industry, condition)
            
            print(f"💰 Debt/Equity: {assumptions['debt_to_equity']:.2f}")
            print(f"🏦 WACC: {assumptions['wacc']*100:.1f}%")
            print(f"📈 Revenue Growth (Y1): {assumptions['revenue_growth'][0]*100:.1f}%")
            print(f"🎯 Terminal Growth: {assumptions['terminal_growth']*100:.1f}%")
            print(f"💰 Cost of Debt: {assumptions['capital_structure']['cost_of_debt']*100:.1f}%")
            print(f"📈 Cost of Equity: {assumptions['capital_structure']['cost_of_equity']*100:.1f}%")
            print(f"🎯 Confidence: {assumptions['research_metadata']['confidence_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing market conditions: {e}")
        return False

def main():
    """Main test function"""
    print("🔬 COMPREHENSIVE RESEARCH ASSUMPTIONS TEST")
    print("=" * 80)
    print("Testing research-based financial assumptions with real industry data")
    print("=" * 80)
    
    # Run all tests
    test_results = []
    
    test_results.append(("Research Assumptions", test_research_assumptions()))
    test_results.append(("Debt Assumptions", test_debt_specific_assumptions()))
    test_results.append(("Valuation Assumptions", test_valuation_assumptions()))
    test_results.append(("Market Conditions", test_market_conditions()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL RESEARCH ASSUMPTIONS TESTS PASSED!")
        print("✅ Comprehensive debt, capital structure, and valuation assumptions working")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 