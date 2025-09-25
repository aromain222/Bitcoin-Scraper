#!/usr/bin/env python3
"""
Data Models for Financial Analysis
Provides standardized data structures for all financial models.

Supports:
- DCF Analysis
- Comparable Company Analysis
- Precedent Transactions (LBO)
- Industry Benchmarks
- Risk Analysis
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import pandas as pd


class ValuationMethod(Enum):
    """Supported valuation methods."""
    DCF = "dcf"
    COMPARABLES = "comps"
    PRECEDENT_TRANSACTIONS = "precedents"
    LBO = "lbo"
    SUM_OF_PARTS = "sop"


class RiskLevel(Enum):
    """Risk assessment levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ValuationInputs:
    """Base class for valuation model inputs."""
    ticker: str = ""
    company_name: str = ""
    valuation_date: datetime = field(default_factory=datetime.now)
    analyst_name: str = ""
    model_version: str = "1.0"

    # Common valuation parameters
    risk_free_rate: float = 0.04
    market_risk_premium: float = 0.06
    tax_rate: float = 0.25
    perpetual_growth_rate: float = 0.025

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, Enum):
                data[key] = value.value
            else:
                data[key] = value
        return data


@dataclass
class DCFInputs(ValuationInputs):
    """Inputs specific to DCF valuation."""
    method: ValuationMethod = ValuationMethod.DCF

    # DCF-specific parameters
    beta: float = 1.1
    cost_of_debt: float = 0.05
    debt_to_capital: float = 0.3
    terminal_growth_method: str = "gordon_growth"  # or "fade_method"

    # Projection parameters
    projection_years: int = 5
    revenue_growth_years: List[float] = field(default_factory=lambda: [0.10, 0.08, 0.06, 0.04, 0.03])
    margin_expansion: List[float] = field(default_factory=lambda: [0.02, 0.01, 0.005, 0.0, 0.0])
    capex_to_sales: float = 0.05
    nwc_to_sales: float = 0.10

    # Sensitivity analysis
    beta_range: List[float] = field(default_factory=lambda: [0.8, 1.0, 1.2])
    growth_range: List[float] = field(default_factory=lambda: [0.02, 0.025, 0.03])


@dataclass
class CompsInputs(ValuationInputs):
    """Inputs for comparable company analysis."""
    method: ValuationMethod = ValuationMethod.COMPARABLES

    # Comps-specific parameters
    peer_companies: List[str] = field(default_factory=list)
    valuation_multiples: List[str] = field(default_factory=lambda: [
        'EV/Revenue', 'EV/EBITDA', 'EV/EBIT', 'P/E', 'P/B'
    ])

    # Statistical parameters
    outlier_threshold: float = 2.0  # Standard deviations
    weight_by_market_cap: bool = True
    adjust_for_growth: bool = True
    adjust_for_risk: bool = True


@dataclass
class LBOInputs(ValuationInputs):
    """Inputs for LBO/precedent transactions analysis."""
    method: ValuationMethod = ValuationMethod.LBO

    # LBO-specific parameters
    target_debt_ratio: float = 0.6
    interest_rate: float = 0.08
    exit_multiple: float = 10.0
    holding_period_years: int = 5

    # Financing assumptions
    senior_debt_ratio: float = 0.5
    subordinated_debt_ratio: float = 0.1
    equity_contribution: float = 0.4

    # Transaction costs
    acquisition_premium: float = 0.20
    financing_fees: float = 0.02
    working_capital_adjustment: float = 0.0


@dataclass
class IndustryBenchmark:
    """Industry benchmark data for comparison."""
    industry_name: str = ""
    sector: str = ""

    # Valuation metrics
    median_pe_ratio: float = 0.0
    median_ev_ebitda: float = 0.0
    median_ev_revenue: float = 0.0
    median_pb_ratio: float = 0.0

    # Growth metrics
    median_revenue_growth: float = 0.0
    median_ebitda_growth: float = 0.0
    median_eps_growth: float = 0.0

    # Risk metrics
    median_beta: float = 1.0
    median_debt_equity: float = 0.0

    # Sample size
    companies_in_sample: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment for a company."""
    company_ticker: str = ""
    assessment_date: datetime = field(default_factory=datetime.now)

    # Business risk factors
    industry_risk: RiskLevel = RiskLevel.MEDIUM
    competitive_position: RiskLevel = RiskLevel.MEDIUM
    management_quality: RiskLevel = RiskLevel.MEDIUM
    customer_concentration: RiskLevel = RiskLevel.MEDIUM

    # Financial risk factors
    leverage_risk: RiskLevel = RiskLevel.MEDIUM
    liquidity_risk: RiskLevel = RiskLevel.MEDIUM
    profitability_risk: RiskLevel = RiskLevel.MEDIUM

    # Market risk factors
    beta_risk: RiskLevel = RiskLevel.MEDIUM
    volatility_risk: RiskLevel = RiskLevel.MEDIUM
    market_position: RiskLevel = RiskLevel.MEDIUM

    # Overall assessment
    overall_risk_level: RiskLevel = RiskLevel.MEDIUM
    recommended_beta_adjustment: float = 0.0
    risk_premium_adjustment: float = 0.0

    # Supporting data
    qualitative_notes: str = ""
    quantitative_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ModelOutputs:
    """Standardized outputs from any valuation model."""
    ticker: str = ""
    company_name: str = ""
    valuation_method: ValuationMethod = ValuationMethod.DCF
    valuation_date: datetime = field(default_factory=datetime.now)

    # Core valuation results
    enterprise_value: float = 0.0
    equity_value: float = 0.0
    share_price: float = 0.0
    upside_downside: float = 0.0

    # Valuation components
    operating_assets_value: float = 0.0
    debt_value: float = 0.0
    cash_value: float = 0.0
    minority_interests: float = 0.0

    # Key assumptions and drivers
    wacc: float = 0.0
    terminal_value: float = 0.0
    terminal_growth_rate: float = 0.025
    exit_multiple: float = 0.0

    # Risk and uncertainty
    confidence_interval_low: float = 0.0
    confidence_interval_high: float = 0.0
    key_risks: List[str] = field(default_factory=list)

    # Model quality metrics
    data_quality_score: float = 0.0
    model_sensitivity: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, list):
                data[key] = value
            elif isinstance(value, dict):
                data[key] = value
            else:
                data[key] = value
        return data

    def format_currency(self, value: float) -> str:
        """Format currency value for display."""
        if abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.1f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.0f}K"
        else:
            return f"${value:.2f}"

    def get_summary_report(self) -> str:
        """Generate a formatted summary report."""
        report = ".2f"".2f"".2f"".2f"".2f"".2f"".2f"".2f"f"""
VALUATION SUMMARY REPORT
{ticker} - {company_name}
{'='*50}
Valuation Method: {valuation_method.value.upper()}
Date: {valuation_date.strftime('%Y-%m-%d')}

CORE VALUATION RESULTS:
  Enterprise Value: {format_currency(enterprise_value)}
  Equity Value: {format_currency(equity_value)}
  Implied Share Price: {format_currency(share_price)}
  Upside/(Downside): {upside_downside:+.1f}%

VALUATION COMPONENTS:
  Operating Assets: {format_currency(operating_assets_value)}
  Debt: {format_currency(debt_value)}
  Cash: {format_currency(cash_value)}
  Minority Interests: {format_currency(minority_interests)}

KEY ASSUMPTIONS:
  WACC: {wacc:.1f}%
  Terminal Value: {format_currency(terminal_value)}
  Terminal Growth Rate: {terminal_growth_rate:.1f}%
  Exit Multiple: {exit_multiple:.1f}x

RISK & UNCERTAINTY:
  Confidence Interval: {format_currency(confidence_interval_low)} - {format_currency(confidence_interval_high)}
  Data Quality Score: {data_quality_score:.1f}/100

KEY RISKS:
{chr(10).join(f"  • {risk}" for risk in key_risks)}
"""
        return report


@dataclass
class ModelComparison:
    """Compare outputs from different valuation models."""
    ticker: str = ""
    company_name: str = ""
    comparison_date: datetime = field(default_factory=datetime.now)

    # Model results
    dcf_value: Optional[float] = None
    comps_value: Optional[float] = None
    lbo_value: Optional[float] = None
    precedent_value: Optional[float] = None

    # Weighted average
    blended_value: float = 0.0
    recommended_weighting: Dict[str, float] = field(default_factory=dict)

    # Range analysis
    valuation_range_low: float = 0.0
    valuation_range_high: float = 0.0
    confidence_level: str = "MEDIUM"

    # Key insights
    primary_valuation_method: str = ""
    key_drivers: List[str] = field(default_factory=list)
    investment_recommendation: str = ""

    def calculate_blended_value(self):
        """Calculate weighted average of available valuations."""
        values_and_weights = []

        if self.dcf_value:
            weight = self.recommended_weighting.get('dcf', 0.4)
            values_and_weights.append((self.dcf_value, weight))

        if self.comps_value:
            weight = self.recommended_weighting.get('comps', 0.3)
            values_and_weights.append((self.comps_value, weight))

        if self.lbo_value:
            weight = self.recommended_weighting.get('lbo', 0.15)
            values_and_weights.append((self.lbo_value, weight))

        if self.precedent_value:
            weight = self.recommended_weighting.get('precedent', 0.15)
            values_and_weights.append((self.precedent_value, weight))

        if values_and_weights:
            total_weight = sum(weight for _, weight in values_and_weights)
            if total_weight > 0:
                self.blended_value = sum(value * weight for value, weight in values_and_weights) / total_weight

                # Calculate range
                values = [value for value, _ in values_and_weights]
                self.valuation_range_low = min(values) * 0.9  # 10% below minimum
                self.valuation_range_high = max(values) * 1.1  # 10% above maximum

    def get_comparison_report(self) -> str:
        """Generate comparison report."""
        report = f"""
VALUATION METHOD COMPARISON
{self.ticker} - {self.company_name}
{'='*50}

INDIVIDUAL METHOD RESULTS:
"""

        if self.dcf_value:
            report += ".2f"
        if self.comps_value:
            report += ".2f"
        if self.lbo_value:
            report += ".2f"
        if self.precedent_value:
            report += ".2f"

        report += ".2f"".2f"".2f"f"""
BLENDED VALUATION:
  Weighted Average: {self.blended_value}
  Valuation Range: {self.valuation_range_low} - {self.valuation_range_high}
  Confidence Level: {self.confidence_level}

PRIMARY METHOD: {self.primary_valuation_method}
RECOMMENDATION: {self.investment_recommendation}

KEY DRIVERS:
{chr(10).join(f"  • {driver}" for driver in self.key_drivers)}
"""
        return report


# Utility functions for data conversion
def valuation_inputs_from_dict(data: Dict[str, Any]) -> ValuationInputs:
    """Create appropriate ValuationInputs subclass from dictionary."""
    method = data.get('method', 'dcf')

    if method == 'dcf':
        return DCFInputs(**data)
    elif method == 'comps':
        return CompsInputs(**data)
    elif method == 'lbo':
        return LBOInputs(**data)
    else:
        return ValuationInputs(**data)


def create_model_template(method: ValuationMethod, ticker: str = "", company_name: str = "") -> ValuationInputs:
    """Create a template inputs object for a specific valuation method."""
    base_data = {
        'ticker': ticker,
        'company_name': company_name,
        'method': method
    }

    if method == ValuationMethod.DCF:
        return DCFInputs(**base_data)
    elif method == ValuationMethod.COMPARABLES:
        return CompsInputs(**base_data)
    elif method == ValuationMethod.LBO:
        return LBOInputs(**base_data)
    else:
        return ValuationInputs(**base_data)


# Example usage
if __name__ == "__main__":
    print("🔧 Testing Data Models...")

    # Create DCF inputs template
    dcf_inputs = create_model_template(ValuationMethod.DCF, "AAPL", "Apple Inc.")
    print(f"✅ Created DCF template for {dcf_inputs.company_name}")

    # Create comps inputs template
    comps_inputs = create_model_template(ValuationMethod.COMPARABLES, "MSFT", "Microsoft Corp.")
    comps_inputs.peer_companies = ["GOOGL", "AMZN", "META"]
    print(f"✅ Created Comps template for {comps_inputs.company_name} with {len(comps_inputs.peer_companies)} peers")

    # Create sample outputs
    outputs = ModelOutputs(
        ticker="AAPL",
        company_name="Apple Inc.",
        enterprise_value=2500000000000,
        equity_value=2400000000000,
        share_price=150.00,
        wacc=0.085,
        data_quality_score=92.5
    )

    print("\n📊 Sample Valuation Output:")
    print(outputs.get_summary_report())

    print("🎯 Data models ready for all valuation methods!")
