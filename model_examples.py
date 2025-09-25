#!/usr/bin/env python3
"""
Examples of using the centralized data management system across different financial models.

This script demonstrates how to:
1. Use the same high-quality data across multiple valuation models
2. Switch between DCF, Comps, and LBO analysis seamlessly
3. Compare results from different methodologies
4. Generate professional reports

All models share the same data foundation for consistency and accuracy.
"""

from financial_data_manager import FinancialDataManager, get_financial_data
from data_models import (
    DCFInputs, CompsInputs, LBOInputs, ModelOutputs,
    ValuationMethod, ModelComparison, create_model_template
)
import pandas as pd
from datetime import datetime


class DCFModel:
    """DCF Valuation Model using centralized data."""

    def __init__(self, data_manager=None):
        self.data_manager = data_manager or FinancialDataManager()
        self.model_type = "DCF"

    def run_valuation(self, ticker: str, custom_inputs: DCFInputs = None) -> ModelOutputs:
        """Run DCF valuation using centralized data."""
        print(f"🏢 Running DCF Valuation for {ticker}...")

        # Get standardized financial data
        company_data = self.data_manager.get_company_financials(ticker, years=5)

        if not company_data.company_name:
            return ModelOutputs(ticker=ticker, valuation_method=ValuationMethod.DCF)

        # Use custom inputs or create defaults
        if custom_inputs:
            inputs = custom_inputs
        else:
            inputs = create_model_template(ValuationMethod.DCF, ticker, company_data.company_name)
            # Set some reasonable defaults based on company data
            inputs.beta = company_data.beta or 1.1
            inputs.projection_years = min(5, len(company_data.revenue)) if company_data.revenue else 5

        # Simplified DCF calculation (in real implementation, this would be more sophisticated)
        enterprise_value = self._calculate_dcf_value(company_data, inputs)

        # Create outputs
        outputs = ModelOutputs(
            ticker=ticker,
            company_name=company_data.company_name,
            valuation_method=ValuationMethod.DCF,
            enterprise_value=enterprise_value,
            equity_value=enterprise_value - (company_data.total_debt[0] if company_data.total_debt else 0) + (company_data.cash_and_equivalents[0] if company_data.cash_and_equivalents else 0),
            wacc=self._calculate_wacc(inputs, company_data),
            data_quality_score=company_data.data_quality.overall_score,
            key_risks=self._identify_key_risks(company_data)
        )

        if outputs.equity_value > 0 and company_data.shares_outstanding > 0:
            outputs.share_price = outputs.equity_value / company_data.shares_outstanding

        # Calculate upside/downside if current price available
        if company_data.current_price > 0:
            outputs.upside_downside = ((outputs.share_price / company_data.current_price) - 1) * 100

        print(".2f")
        return outputs

    def _calculate_dcf_value(self, data, inputs: DCFInputs) -> float:
        """Simplified DCF calculation."""
        if not data.revenue or not data.free_cash_flow:
            return 0.0

        # Use available historical data
        historical_years = min(len(data.free_cash_flow), inputs.projection_years)

        # Simple projection: grow last FCF by terminal growth
        last_fcf = data.free_cash_flow[-1] if data.free_cash_flow else 0
        if last_fcf <= 0:
            return data.enterprise_value or 0.0

        # Calculate terminal value
        terminal_value = last_fcf * (1 + inputs.perpetual_growth_rate) / (inputs.wacc - inputs.perpetual_growth_rate)

        # Discount terminal value (simplified - assume 5 years)
        pv_terminal = terminal_value / (1 + inputs.wacc) ** 5

        # Estimate enterprise value
        enterprise_value = pv_terminal * 1.2  # Rough approximation

        return enterprise_value

    def _calculate_wacc(self, inputs: DCFInputs, data) -> float:
        """Calculate WACC."""
        cost_of_equity = inputs.risk_free_rate + inputs.beta * (inputs.market_risk_premium)
        cost_of_debt = inputs.cost_of_debt * (1 - inputs.tax_rate)  # After-tax

        # Estimate capital structure
        total_capital = (data.market_cap or 1000000000) + (data.total_debt[0] if data.total_debt else 0)
        equity_ratio = (data.market_cap or 1000000000) / total_capital if total_capital > 0 else 0.6
        debt_ratio = 1 - equity_ratio

        wacc = cost_of_equity * equity_ratio + cost_of_debt * debt_ratio
        return wacc

    def _identify_key_risks(self, data) -> list:
        """Identify key risks based on financial data."""
        risks = []

        # Leverage risk
        if data.debt_to_equity and data.debt_to_equity > 1.5:
            risks.append("High leverage increases financial risk")

        # Profitability risk
        if data.roe and data.roe < 0.05:
            risks.append("Low profitability may affect growth prospects")

        # Growth risk
        if data.revenue_growth and data.revenue_growth < 0:
            risks.append("Negative revenue growth indicates challenges")

        # Market risk
        if data.beta and data.beta > 1.5:
            risks.append("High beta indicates significant market volatility")

        if not risks:
            risks.append("Standard market and operational risks apply")

        return risks


class CompsModel:
    """Comparable Company Analysis using centralized data."""

    def __init__(self, data_manager=None):
        self.data_manager = data_manager or FinancialDataManager()
        self.model_type = "Comps"

    def run_valuation(self, ticker: str, peer_tickers: list, custom_inputs: CompsInputs = None) -> ModelOutputs:
        """Run comparable company valuation."""
        print(f"📊 Running Comps Valuation for {ticker}...")

        # Get target company data
        target_data = self.data_manager.get_company_financials(ticker)

        if not target_data.company_name:
            return ModelOutputs(ticker=ticker, valuation_method=ValuationMethod.COMPARABLES)

        # Get peer company data
        peer_data = {}
        for peer in peer_tickers:
            try:
                peer_data[peer] = self.data_manager.get_company_financials(peer)
            except:
                print(f"   ⚠️ Could not get data for peer {peer}")
                continue

        if not peer_data:
            print("   ❌ No peer data available")
            return ModelOutputs(ticker=ticker, valuation_method=ValuationMethod.COMPARABLES)

        # Use custom inputs or create defaults
        if custom_inputs:
            inputs = custom_inputs
        else:
            inputs = create_model_template(ValuationMethod.COMPARABLES, ticker, target_data.company_name)
            inputs.peer_companies = peer_tickers

        # Calculate valuation multiples
        valuation = self._calculate_comps_valuation(target_data, peer_data, inputs)

        # Create outputs
        outputs = ModelOutputs(
            ticker=ticker,
            company_name=target_data.company_name,
            valuation_method=ValuationMethod.COMPARABLES,
            enterprise_value=valuation['enterprise_value'],
            equity_value=valuation['equity_value'],
            data_quality_score=min([d.data_quality.overall_score for d in peer_data.values()] + [target_data.data_quality.overall_score]),
            key_risks=["Reliance on peer company multiples", "Industry changes may affect comparability"]
        )

        if outputs.equity_value > 0 and target_data.shares_outstanding > 0:
            outputs.share_price = outputs.equity_value / target_data.shares_outstanding

        if target_data.current_price > 0:
            outputs.upside_downside = ((outputs.share_price / target_data.current_price) - 1) * 100

        print(".2f")
        return outputs

    def _calculate_comps_valuation(self, target_data, peer_data: dict, inputs: CompsInputs) -> dict:
        """Calculate valuation using comparable multiples."""
        # Calculate average multiples from peers
        ev_ebitda_multiples = []
        ev_revenue_multiples = []
        pe_multiples = []

        for peer_name, peer in peer_data.items():
            if peer.ebitda and peer.ebitda[0] > 0:
                ev_ebitda = peer.enterprise_value / peer.ebitda[0] if peer.enterprise_value > 0 else 0
                if ev_ebitda > 0:
                    ev_ebitda_multiples.append(ev_ebitda)

            if peer.revenue and peer.revenue[0] > 0:
                ev_revenue = peer.enterprise_value / peer.revenue[0] if peer.enterprise_value > 0 else 0
                if ev_revenue > 0:
                    ev_revenue_multiples.append(ev_revenue)

            if peer.pe_ratio and peer.pe_ratio > 0:
                pe_multiples.append(peer.pe_ratio)

        # Calculate averages
        avg_ev_ebitda = sum(ev_ebitda_multiples) / len(ev_ebitda_multiples) if ev_ebitda_multiples else 10.0
        avg_ev_revenue = sum(ev_revenue_multiples) / len(ev_revenue_multiples) if ev_revenue_multiples else 2.0
        avg_pe = sum(pe_multiples) / len(pe_multiples) if pe_multiples else 15.0

        # Apply to target company
        enterprise_value_ebitda = (target_data.ebitda[0] * avg_ev_ebitda) if target_data.ebitda else 0
        enterprise_value_revenue = (target_data.revenue[0] * avg_ev_revenue) if target_data.revenue else 0

        # Use EBITDA multiple as primary, revenue as secondary
        enterprise_value = enterprise_value_ebitda if enterprise_value_ebitda > 0 else enterprise_value_revenue

        # Calculate equity value
        debt = target_data.total_debt[0] if target_data.total_debt else 0
        cash = target_data.cash_and_equivalents[0] if target_data.cash_and_equivalents else 0
        equity_value = enterprise_value - debt + cash

        return {
            'enterprise_value': enterprise_value,
            'equity_value': max(0, equity_value),  # Ensure non-negative
            'avg_ev_ebitda': avg_ev_ebitda,
            'avg_ev_revenue': avg_ev_revenue,
            'avg_pe': avg_pe
        }


class ValuationEngine:
    """Unified valuation engine that can run multiple models."""

    def __init__(self):
        self.data_manager = FinancialDataManager()
        self.models = {
            'dcf': DCFModel(self.data_manager),
            'comps': CompsModel(self.data_manager)
        }

    def run_all_models(self, ticker: str, peer_tickers: list = None) -> ModelComparison:
        """Run all available valuation models and compare results."""
        print(f"🚀 Running comprehensive valuation analysis for {ticker}...")

        # Run DCF
        dcf_result = self.models['dcf'].run_valuation(ticker)

        # Run Comps if peers provided
        comps_result = None
        if peer_tickers:
            comps_result = self.models['comps'].run_valuation(ticker, peer_tickers)

        # Create comparison
        comparison = ModelComparison(
            ticker=ticker,
            company_name=dcf_result.company_name,
            dcf_value=dcf_result.enterprise_value if dcf_result.enterprise_value > 0 else None,
            comps_value=comps_result.enterprise_value if comps_result and comps_result.enterprise_value > 0 else None
        )

        # Calculate blended value
        comparison.calculate_blended_value()

        # Determine primary method and recommendation
        if comparison.dcf_value and comparison.comps_value:
            diff_pct = abs(comparison.dcf_value - comparison.comps_value) / min(comparison.dcf_value, comparison.comps_value)
            if diff_pct < 0.2:  # Within 20%
                comparison.primary_valuation_method = "Blended DCF/Comps"
                comparison.recommended_weighting = {'dcf': 0.6, 'comps': 0.4}
            elif comparison.dcf_value > comparison.comps_value:
                comparison.primary_valuation_method = "DCF"
                comparison.recommended_weighting = {'dcf': 0.7, 'comps': 0.3}
            else:
                comparison.primary_valuation_method = "Comps"
                comparison.recommended_weighting = {'dcf': 0.3, 'comps': 0.7}
        elif comparison.dcf_value:
            comparison.primary_valuation_method = "DCF"
            comparison.recommended_weighting = {'dcf': 1.0}
        else:
            comparison.primary_valuation_method = "Comps"
            comparison.recommended_weighting = {'comps': 1.0}

        comparison.investment_recommendation = self._generate_recommendation(comparison)
        comparison.key_drivers = self._identify_key_drivers(dcf_result, comps_result)

        return comparison

    def _generate_recommendation(self, comparison: ModelComparison) -> str:
        """Generate investment recommendation based on valuation."""
        if not comparison.blended_value:
            return "Unable to determine valuation - insufficient data"

        # This would be more sophisticated in a real implementation
        return "HOLD - Valuation analysis complete, further due diligence recommended"

    def _identify_key_drivers(self, dcf_result, comps_result) -> list:
        """Identify key drivers of valuation differences."""
        drivers = []

        if dcf_result and comps_result:
            if abs(dcf_result.data_quality_score - comps_result.data_quality_score) > 10:
                drivers.append("Data quality differences between models")
            drivers.append("Market expectations vs. fundamental cash flows")
        elif dcf_result:
            drivers.append("Focus on long-term cash flow generation")
        else:
            drivers.append("Market-based valuation using peer comparisons")

        return drivers


def main():
    """Demonstrate the unified valuation system."""
    print("🎯 Financial Model Integration Demo")
    print("=" * 50)

    # Initialize valuation engine
    engine = ValuationEngine()

    # Example 1: Run DCF only
    print("\n📊 Example 1: DCF Valuation")
    print("-" * 30)
    dcf_result = engine.models['dcf'].run_valuation('AAPL')
    print(dcf_result.get_summary_report())

    # Example 2: Run Comps
    print("\n📊 Example 2: Comparable Company Analysis")
    print("-" * 30)
    peers = ['MSFT', 'GOOGL', 'AMZN']
    comps_result = engine.models['comps'].run_valuation('AAPL', peers)
    print(comps_result.get_summary_report())

    # Example 3: Run comprehensive analysis
    print("\n📊 Example 3: Comprehensive Valuation Comparison")
    print("-" * 30)
    comparison = engine.run_all_models('AAPL', peers)
    print(comparison.get_comparison_report())

    print("\n✅ Demo complete!")
    print("\n💡 Key Benefits:")
    print("   • Same high-quality data across all models")
    print("   • Consistent data quality scoring")
    print("   • Easy comparison between methodologies")
    print("   • Professional reporting format")
    print("   • Extensible for additional models")


if __name__ == "__main__":
    main()
