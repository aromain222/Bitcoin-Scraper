#!/usr/bin/env python3
"""
FinModAI Model Factory
AI-powered factory for generating different types of financial models.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

logger = logging.getLogger('FinModAI.ModelFactory')

@dataclass
class ModelTemplate:
    """Template for a financial model type."""
    name: str
    description: str
    required_inputs: List[str]
    output_components: List[str]
    default_assumptions: Dict[str, Any]
    validation_rules: Dict[str, Any]

@dataclass
class ModelSpecification:
    """Complete specification for a financial model."""
    model_type: str
    company_data: Dict[str, Any]
    assumptions: Dict[str, Any]
    calculations: Dict[str, Any]
    outputs: Dict[str, Any]
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    scenario_analysis: Optional[Dict[str, Any]] = None
    visualization_config: Optional[Dict[str, Any]] = None
    audit_trail: List[str] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []

class ModelFactory:
    """AI-powered factory for generating financial models."""

    def __init__(self, config):
        self.config = config
        self.templates = self._load_model_templates()

        # AI components
        self.assumption_engine = AssumptionEngine()
        self.validation_engine = ValidationEngine()
        self.sensitivity_engine = SensitivityEngine()

        logger.info("🏭 Model Factory initialized with AI components")

    def _load_model_templates(self) -> Dict[str, ModelTemplate]:
        """Load model templates from configuration."""
        templates = {}

        # DCF Model Template
        templates['dcf'] = ModelTemplate(
            name='Discounted Cash Flow',
            description='Valuation based on discounted future free cash flows',
            required_inputs=['revenue', 'ebitda', 'beta', 'debt', 'shares'],
            output_components=['enterprise_value', 'equity_value', 'implied_price', 'wacc'],
            default_assumptions={
                'forecast_period': 6,
                'terminal_method': 'perpetuity',
                'terminal_growth': 0.025,
                'risk_free_rate': 0.045,
                'market_risk_premium': 0.06,
                'tax_rate': 0.25
            },
            validation_rules={
                'wacc_range': [0.05, 0.20],
                'terminal_growth_range': [0.01, 0.04],
                'beta_range': [0.5, 3.0]
            }
        )

        # LBO Model Template
        templates['lbo'] = ModelTemplate(
            name='Leveraged Buyout',
            description='Private equity acquisition valuation with leverage',
            required_inputs=['revenue', 'ebitda', 'debt_capacity', 'exit_multiple'],
            output_components=['enterprise_value', 'equity_value', 'irr', 'multiple_of_invested_capital'],
            default_assumptions={
                'leverage_ratio': 6.0,
                'interest_rate': 0.08,
                'hold_period': 5,
                'exit_multiple': 10.0,
                'fees_percentage': 0.02
            },
            validation_rules={
                'leverage_range': [3.0, 8.0],
                'irr_target': [0.15, 0.35],
                'hold_period_range': [3, 7]
            }
        )

        # Comps Model Template
        templates['comps'] = ModelTemplate(
            name='Trading Comparables',
            description='Relative valuation using peer company multiples',
            required_inputs=['peer_companies', 'valuation_multiples'],
            output_components=['implied_value', 'peer_analysis', 'valuation_range'],
            default_assumptions={
                'peer_count': 8,
                'outlier_threshold': 0.2,
                'weighting_method': 'equal'
            },
            validation_rules={
                'peer_count_range': [5, 15],
                'multiple_range': [5.0, 25.0]
            }
        )

        # Three Statement Model Template
        templates['three_statement'] = ModelTemplate(
            name='Three Statement Model',
            description='Integrated income statement, balance sheet, and cash flow',
            required_inputs=['historical_financials', 'assumptions'],
            output_components=['income_statement', 'balance_sheet', 'cash_flow_statement', 'ratios'],
            default_assumptions={
                'forecast_years': 5,
                'growth_rate': 0.08,
                'margin_stability': True
            },
            validation_rules={
                'forecast_years_range': [3, 10],
                'growth_range': [0.01, 0.20]
            }
        )

        logger.info(f"📋 Loaded {len(templates)} model templates")
        return templates

    def create_model(
        self,
        model_type: str,
        financial_data: Dict[str, Any],
        custom_assumptions: Optional[Dict[str, Any]] = None,
        include_sensitivity: bool = True,
        include_dashboard: bool = True
    ) -> ModelSpecification:
        """
        Create a complete model specification using AI.

        Args:
            model_type: Type of model to create
            financial_data: Financial data from data ingestion
            custom_assumptions: User-provided assumptions
            include_sensitivity: Include sensitivity analysis
            include_dashboard: Include visualization dashboard

        Returns:
            Complete ModelSpecification
        """
        print(f"📊 DEBUG: ModelFactory.create_model called with model_type={model_type}")
        logger.info(f"🤖 AI generating {model_type.upper()} model specification")
        print(f"📊 DEBUG: Starting model creation for {model_type}")

        if model_type not in self.templates:
            raise ValueError(f"Unsupported model type: {model_type}")

        template = self.templates[model_type]
        print(f"📊 DEBUG: Using template: {template.name}")

        # Step 1: Generate AI-powered assumptions
        assumptions = self._generate_assumptions(
            template, financial_data, custom_assumptions
        )

        # Step 2: Generate model calculations
        print(f"📊 DEBUG: About to generate {model_type} calculations")
        calculations = self._generate_calculations(model_type, financial_data, assumptions)
        print(f"📊 DEBUG: Generated calculations keys: {list(calculations.keys())}")

        # Step 3: Calculate outputs
        print(f"📊 DEBUG: About to calculate outputs")
        print(f"📊 DEBUG: Calculations keys: {list(calculations.keys())}")
        print(f"📊 DEBUG: Assumptions keys: {list(assumptions.keys())}")
        outputs = self._calculate_outputs(model_type, calculations, assumptions)
        print(f"📊 DEBUG: Calculated outputs: {outputs}")

        # Step 4: Generate sensitivity analysis
        sensitivity = None
        if include_sensitivity:
            sensitivity = self.sensitivity_engine.generate_sensitivity(
                model_type, calculations, assumptions
            )

        # Step 5: Generate visualization config
        visualization = None
        if include_dashboard:
            visualization = self._generate_visualization_config(model_type, outputs)

        # Step 6: Create audit trail
        audit_trail = self._create_audit_trail(
            model_type, financial_data, assumptions, outputs
        )

        # Create model specification
        model_spec = ModelSpecification(
            model_type=model_type,
            company_data=financial_data,
            assumptions=assumptions,
            calculations=calculations,
            outputs=outputs,
            sensitivity_analysis=sensitivity,
            visualization_config=visualization,
            audit_trail=audit_trail
        )

        # Validate the model
        validation_result = self.validate_model(model_spec)
        if not validation_result['valid']:
            logger.warning(f"Model validation issues: {validation_result['issues']}")

        logger.info("✅ Model specification generated successfully")
        return model_spec

    def _generate_assumptions(
        self,
        template: ModelTemplate,
        financial_data: Dict[str, Any],
        custom_assumptions: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered assumptions based on financial data."""
        assumptions = template.default_assumptions.copy()

        # Override with custom assumptions
        if custom_assumptions:
            assumptions.update(custom_assumptions)

        # AI-powered assumption generation
        print(f"📊 DEBUG: Before assumption engine - assumptions keys: {list(assumptions.keys())}")
        print(f"📊 DEBUG: Financial data type: {type(financial_data)}")
        if hasattr(financial_data, 'revenue_growth'):
            print(f"📊 DEBUG: Financial data revenue_growth: {financial_data.revenue_growth}")
        else:
            print(f"📊 DEBUG: Financial data keys: {list(financial_data.keys()) if isinstance(financial_data, dict) else 'Not a dict'}")

        try:
            smart_assumptions = self.assumption_engine.generate_smart_assumptions(
                template.name, financial_data, assumptions
            )
            print(f"📊 DEBUG: After assumption engine - smart assumptions keys: {list(smart_assumptions.keys())}")
            assumptions.update(smart_assumptions)
            print(f"📊 DEBUG: Final assumptions keys: {list(assumptions.keys())}")
        except Exception as e:
            print(f"⚠️ DEBUG: Assumption engine error: {e}")
            print(f"⚠️ DEBUG: Using default assumptions")

        logger.debug(f"Generated assumptions: {list(assumptions.keys())}")
        return assumptions

    def _generate_calculations(
        self,
        model_type: str,
        financial_data: Dict[str, Any],
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate model calculations."""
        calculations = {}

        if model_type == 'dcf':
            calculations = self._generate_dcf_calculations(financial_data, assumptions)
        elif model_type == 'lbo':
            calculations = self._generate_lbo_calculations(financial_data, assumptions)
        elif model_type == 'comps':
            calculations = self._generate_comps_calculations(financial_data, assumptions)
        elif model_type == 'three_statement':
            calculations = self._generate_three_statement_calculations(financial_data, assumptions)

        return calculations

    def _generate_dcf_calculations(
        self,
        financial_data: Any,
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate DCF-specific calculations."""
        calc = {}

        # Handle both dict and FinancialData object
        if hasattr(financial_data, 'revenue'):
            # FinancialData object
            base_revenue = float(financial_data.revenue)
            beta = financial_data.beta
            shares_outstanding = financial_data.shares_outstanding
            print(f"📊 DEBUG: Using FinancialData object - Revenue: ${base_revenue:.1f}B, Shares: {shares_outstanding/1_000_000:.1f}M")
            print(f"📊 DEBUG: Revenue type: {type(base_revenue)}, Value: {base_revenue}")
        else:
            # Dictionary
            base_revenue = float(getattr(financial_data, 'revenue', 1000))
            beta = getattr(financial_data, 'beta', 1.2)
            shares_outstanding = getattr(financial_data, 'shares_outstanding', 1000)
            print(f"📊 DEBUG: Using Dictionary - Revenue: ${base_revenue:.1f}B, Shares: {shares_outstanding/1_000_000:.1f}M")
            print(f"📊 DEBUG: Revenue type: {type(base_revenue)}, Value: {base_revenue}")

        growth_rate = assumptions.get('growth_rate', 0.08)
        forecast_years = assumptions.get('forecast_years', 6)
        print(f"📊 DEBUG: DCF calc - growth_rate: {growth_rate}, forecast_years: {forecast_years}")
        print(f"📊 DEBUG: DCF calc - assumptions keys: {list(assumptions.keys())}")
        print(f"📊 DEBUG: base_revenue before projection: ${base_revenue:.1f}B")

        base_revenue_dollars = assumptions.get('base_revenue')
        if base_revenue_dollars:
            base_revenue_value = base_revenue_dollars
        else:
            base_revenue_value = base_revenue * 1_000_000_000

        calc['revenue_projection'] = []
        print(f"📊 DEBUG: Starting revenue projection with base_revenue dollars: ${base_revenue_value:.0f}")
        for year in range(forecast_years):
            projected_revenue = base_revenue_value * ((1 + growth_rate) ** year)
            calc['revenue_projection'].append(projected_revenue)
            print(f"📊 DEBUG: Year {year+1} - Base Revenue: ${base_revenue_value/1_000_000_000:.1f}B, Growth Rate: {growth_rate:.3f}, Projected Revenue: ${projected_revenue/1_000_000_000:.1f}B")

        # Cost projections (simplified)
        ebitda_margin = assumptions.get('ebitda_margin', 0.25)
        print(f"📊 DEBUG: EBITDA margin: {ebitda_margin:.3f}")
        print(f"📊 DEBUG: Revenue projection: {[f'${rev/1_000_000_000:.1f}B' for rev in calc['revenue_projection']]}")

        calc['ebitda_projection'] = []
        for rev in calc['revenue_projection']:
            ebitda_val = rev * ebitda_margin
            calc['ebitda_projection'].append(ebitda_val)
        print(f"📊 DEBUG: EBITDA projection: {[f'${ebitda/1_000_000_000:.1f}B' for ebitda in calc['ebitda_projection']]}")

        # Capex and NWC assumptions
        capex_pct = assumptions.get('capex_pct', 0.06)
        nwc_pct = assumptions.get('nwc_pct', 0.02)

        calc['capex_projection'] = [rev * capex_pct for rev in calc['revenue_projection']]
        calc['nwc_projection'] = [rev * nwc_pct for rev in calc['revenue_projection']]

        # Calculate UFCF
        tax_rate = assumptions.get('tax_rate', 0.25)
        calc['ufcf_projection'] = []

        for i, ebitda in enumerate(calc['ebitda_projection']):
            # Simplified NOPAT calculation
            nopat = ebitda * (1 - tax_rate)
            print(f"📊 DEBUG: Year {i+1} - EBITDA: ${ebitda/1_000_000_000:.1f}B, NOPAT: ${nopat/1_000_000_000:.1f}B")

            # Capex and NWC changes
            capex = calc['capex_projection'][i]
            nwc_change = calc['nwc_projection'][i] - (calc['nwc_projection'][i-1] if i > 0 else 0)

            ufcf = nopat - capex - nwc_change
            print(f"📊 DEBUG: Year {i+1} - Capex: ${capex/1_000_000_000:.1f}B, NWC Change: ${nwc_change/1_000_000_000:.1f}B, UFCF: ${ufcf/1_000_000_000:.1f}B")
            calc['ufcf_projection'].append(ufcf)

        # WACC calculation
        rf = assumptions.get('risk_free_rate', 0.045)
        market_premium = assumptions.get('market_risk_premium', 0.06)
        debt_ratio = assumptions.get('debt_ratio', 0.40)
        cost_of_debt = assumptions.get('cost_of_debt', 0.055)

        cost_of_equity = rf + beta * market_premium
        wacc = debt_ratio * cost_of_debt * (1 - tax_rate) + (1 - debt_ratio) * cost_of_equity

        calc['wacc'] = wacc
        calc['cost_of_equity'] = cost_of_equity

        # Discount factors
        calc['discount_factors'] = []
        for year in range(1, forecast_years + 1):
            df = 1 / ((1 + wacc) ** year)
            calc['discount_factors'].append(df)

        # PV of UFCF
        calc['pv_ufcf'] = [
            ufcf * df for ufcf, df in zip(calc['ufcf_projection'], calc['discount_factors'])
        ]
        print(f"📊 DEBUG: UFCF projection: {[f'${ufcf/1_000_000_000:.1f}B' for ufcf in calc['ufcf_projection']]}")
        print(f"📊 DEBUG: Discount factors: {[f'{df:.3f}' for df in calc['discount_factors']]}")
        print(f"📊 DEBUG: PV UFCF: {[f'${pv/1_000_000_000:.1f}B' for pv in calc['pv_ufcf']]}")
        print(f"📊 DEBUG: PV UFCF sum: ${sum(calc['pv_ufcf'])/1_000_000_000:.1f}B")

        # Terminal value
        terminal_growth = assumptions.get('terminal_growth', 0.025)
        last_ufcf = calc['ufcf_projection'][-1]
        last_df = calc['discount_factors'][-1]

        if assumptions.get('terminal_method', 'perpetuity') == 'perpetuity':
            terminal_value = last_ufcf * (1 + terminal_growth) / (wacc - terminal_growth)
        else:
            exit_multiple = assumptions.get('exit_multiple', 10.0)
            terminal_value = last_ufcf * exit_multiple

        calc['terminal_value'] = terminal_value
        calc['pv_terminal'] = terminal_value * last_df
        calc['terminal_discount_factor'] = last_df

        return calc

    def _generate_lbo_calculations(
        self,
        financial_data: Any,
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate LBO-specific calculations."""
        calc = {}

        # Handle both dict and FinancialData object
        if hasattr(financial_data, 'ebitda'):
            ebitda = financial_data.ebitda
        else:
            ebitda = getattr(financial_data, 'ebitda', 100)

        # Simplified LBO calculations
        leverage_ratio = assumptions.get('leverage_ratio', 6.0)
        enterprise_value = ebitda * leverage_ratio
        calc['enterprise_value'] = enterprise_value

        # Debt structure (simplified)
        senior_debt_ratio = 0.6
        subordinated_debt_ratio = 0.4
        calc['senior_debt'] = enterprise_value * senior_debt_ratio
        calc['subordinated_debt'] = enterprise_value * subordinated_debt_ratio

        # Equity contribution
        total_debt = calc['senior_debt'] + calc['subordinated_debt']
        calc['equity_contribution'] = enterprise_value - total_debt

        # IRR calculation (simplified)
        exit_multiple = assumptions.get('exit_multiple', 10.0)
        exit_value = ebitda * exit_multiple
        total_return = exit_value - total_debt - calc['equity_contribution']
        
        # Safe IRR calculation
        if calc['equity_contribution'] > 0:
            irr = (total_return / calc['equity_contribution']) ** (1/5) - 1  # 5-year hold
        else:
            irr = 0.0
        calc['irr'] = irr

        return calc

    def _generate_comps_calculations(
        self,
        financial_data: Any,
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trading comps calculations."""
        calc = {}

        # Handle both dict and FinancialData object
        if hasattr(financial_data, 'ebitda'):
            target_metric = financial_data.ebitda
        else:
            target_metric = getattr(financial_data, 'ebitda', 100)

        # Simplified peer analysis
        base_multiple = assumptions.get('base_multiple', 12.0)
        peer_variation = 0.2  # 20% variation

        calc['peer_multiples'] = [
            base_multiple * (1 + peer_variation * (i - 2) / 2)
            for i in range(5)
        ]

        calc['average_multiple'] = np.mean(calc['peer_multiples'])
        calc['median_multiple'] = np.median(calc['peer_multiples'])

        # Apply to target company
        calc['implied_value'] = target_metric * calc['average_multiple']

        return calc

    def _generate_three_statement_calculations(
        self,
        financial_data: Any,
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate three-statement model calculations."""
        calc = {}

        # Handle both dict and FinancialData object
        if hasattr(financial_data, 'revenue'):
            base_revenue = financial_data.revenue
        else:
            base_revenue = getattr(financial_data, 'revenue', 1000)

        growth_rate = assumptions.get('growth_rate', 0.08)
        forecast_years = assumptions.get('forecast_years', 5)

        # Income Statement
        calc['income_statement'] = {}
        calc['income_statement']['revenue'] = [
            base_revenue * ((1 + growth_rate) ** year)
            for year in range(forecast_years)
        ]

        # Balance Sheet (simplified)
        calc['balance_sheet'] = {}
        calc['balance_sheet']['assets'] = calc['income_statement']['revenue']  # Simplified

        # Cash Flow Statement
        calc['cash_flow'] = {}
        ebitda_margin = assumptions.get('ebitda_margin', 0.25)
        calc['cash_flow']['operating_cash_flow'] = [
            rev * ebitda_margin * 0.7  # Simplified
            for rev in calc['income_statement']['revenue']
        ]

        return calc

    def _calculate_outputs(
        self,
        model_type: str,
        calculations: Dict[str, Any],
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate final model outputs."""
        outputs = {}

        if model_type == 'dcf':
            # Sum of PV UFCF + PV Terminal
            pv_ufcf_sum = sum(calculations.get('pv_ufcf', []))
            pv_terminal = calculations.get('pv_terminal', 0)
            enterprise_value = pv_ufcf_sum + pv_terminal
            print(f"📊 DEBUG: pv_ufcf_sum: ${pv_ufcf_sum/1_000_000_000:.1f}B")
            print(f"📊 DEBUG: pv_terminal: ${pv_terminal/1_000_000_000:.1f}B")
            print(f"📊 DEBUG: enterprise_value: ${enterprise_value/1_000_000_000:.1f}B")

            # Net debt adjustment
            net_debt = assumptions.get('net_debt', 0)
            print(f"📊 DEBUG: net_debt: ${net_debt/1_000_000_000:.1f}B")
            equity_value = enterprise_value - net_debt
            print(f"📊 DEBUG: equity_value: ${equity_value/1_000_000_000:.1f}B")

            # Per share valuation - use actual data if available
            shares_outstanding = assumptions.get('shares_outstanding', 0)
            if shares_outstanding > 0:
                implied_price = equity_value / shares_outstanding
            else:
                implied_price = 0
            print(f"📊 DEBUG: Using shares_outstanding: {shares_outstanding/1_000_000:.1f}M for implied price calculation")
            print(f"📊 DEBUG: Calculated implied_price: ${implied_price:.2f}")

            outputs.update({
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'implied_price': implied_price,
                'wacc': calculations.get('wacc', 0),
                'terminal_value': calculations.get('terminal_value', 0),
                'pv_terminal': pv_terminal
            })

        elif model_type == 'lbo':
            outputs.update({
                'enterprise_value': calculations.get('enterprise_value', 0),
                'equity_value': calculations.get('equity_contribution', 0),
                'irr': calculations.get('irr', 0),
                'total_debt': calculations.get('senior_debt', 0) + calculations.get('subordinated_debt', 0)
            })

        elif model_type == 'comps':
            outputs.update({
                'implied_value': calculations.get('implied_value', 0),
                'average_multiple': calculations.get('average_multiple', 0),
                'valuation_range': [
                    calculations.get('implied_value', 0) * 0.9,
                    calculations.get('implied_value', 0) * 1.1
                ]
            })

        return outputs

    def _generate_visualization_config(
        self,
        model_type: str,
        outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate visualization configuration."""
        config = {
            'charts': [],
            'dashboards': []
        }

        if model_type == 'dcf':
            config['charts'] = [
                {
                    'type': 'waterfall',
                    'title': 'Enterprise Value Bridge',
                    'data': ['PV_UFCF', 'PV_Terminal', 'Enterprise_Value']
                },
                {
                    'type': 'line',
                    'title': 'UFCF Projection',
                    'data': 'ufcf_projection'
                }
            ]

        return config

    def _create_audit_trail(
        self,
        model_type: str,
        financial_data: Dict[str, Any],
        assumptions: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> List[str]:
        """Create audit trail for the model."""
        # Handle both dict and FinancialData object
        if hasattr(financial_data, 'company_name'):
            company_name = financial_data.company_name
            data_source = financial_data.data_source
        else:
            company_name = getattr(financial_data, 'company_name', 'Unknown')
            data_source = getattr(financial_data, 'data_source', 'Unknown')

        trail = [
            f"Model Type: {model_type}",
            f"Company: {company_name}",
            f"Data Source: {data_source}",
            f"Generated: {outputs.get('timestamp', 'Unknown')}"
        ]

        # Add key assumptions
        for key, value in assumptions.items():
            if isinstance(value, (int, float)):
                trail.append(f"Assumption - {key}: {value:.4f}")
            else:
                trail.append(f"Assumption - {key}: {value}")

        return trail

    def validate_model(self, model_spec: ModelSpecification) -> Dict[str, Any]:
        """Validate a model specification."""
        return self.validation_engine.validate(model_spec)

    def get_available_templates(self) -> Dict[str, Any]:
        """Get information about available model templates."""
        return {
            name: {
                'name': template.name,
                'description': template.description,
                'required_inputs': template.required_inputs,
                'output_components': template.output_components
            }
            for name, template in self.templates.items()
        }

class AssumptionEngine:
    """AI-powered assumption generation engine."""

    def generate_smart_assumptions(
        self,
        model_type: str,
        financial_data: Any,
        existing_assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate smart assumptions based on financial data."""
        assumptions = {}

        # Handle both dict and FinancialData object
        if hasattr(financial_data, 'sector'):
            sector = financial_data.sector.lower() if financial_data.sector else ''
            industry = financial_data.industry.lower() if financial_data.industry else ''
        else:
            sector = getattr(financial_data, 'sector', '').lower()
            industry = getattr(financial_data, 'industry', '').lower()

        # Technology sector assumptions
        if 'tech' in sector or 'technology' in sector:
            beta_value = getattr(financial_data, 'beta', 1.2)
            assumptions.update({
                'growth_rate': 0.12,  # Higher growth for tech
                'beta': max(beta_value, 1.3),  # Higher beta
                'capex_pct': 0.08,  # Higher capex for tech
                'terminal_growth': 0.03  # Higher terminal growth
            })

        # Financial sector assumptions
        elif 'financial' in sector:
            beta_value = getattr(financial_data, 'beta', 1.2)
            assumptions.update({
                'beta': min(beta_value, 1.1),
                'leverage_ratio': 8.0,  # Higher leverage for financials
                'tax_rate': 0.30  # Higher tax rate
            })

        # Extract from financial data - use calculated historical growth
        growth_rate = 0.08  # Default growth rate

        if hasattr(financial_data, 'revenue_growth') and financial_data.revenue_growth and financial_data.revenue_growth > 0:
            growth_rate = min(financial_data.revenue_growth / 100, 0.15)
            print(f"📈 DEBUG: Using calculated revenue growth: {financial_data.revenue_growth:.2f}%")
        elif isinstance(financial_data, dict) and financial_data.get('revenue_growth'):
            growth_rate = min(financial_data['revenue_growth'] / 100, 0.15)
            print(f"📈 DEBUG: Using dict revenue growth: {financial_data['revenue_growth']:.2f}%")
        else:
            print(f"📈 DEBUG: Using default growth rate: {growth_rate:.2f}%")

        assumptions['growth_rate'] = growth_rate

        # Convert commonly used financial metrics into dollars for downstream calculations
        revenue_billion = getattr(financial_data, 'revenue', 0) or 0
        ebitda_billion = getattr(financial_data, 'ebitda', 0) or 0
        operating_cf_billion = getattr(financial_data, 'operating_cash_flow', 0) or 0
        capex_billion = getattr(financial_data, 'capex', 0) or 0
        total_debt_billion = getattr(financial_data, 'total_debt', 0) or 0
        cash_billion = getattr(financial_data, 'cash_and_equivalents', 0) or 0

        revenue_dollars = revenue_billion * 1_000_000_000
        ebitda_dollars = ebitda_billion * 1_000_000_000
        operating_cf_dollars = operating_cf_billion * 1_000_000_000
        capex_dollars = capex_billion * 1_000_000_000

        if revenue_dollars > 0:
            assumptions['base_revenue'] = revenue_dollars

        if ebitda_dollars > 0 and revenue_dollars > 0:
            ebitda_margin = ebitda_dollars / revenue_dollars
            assumptions['ebitda_margin'] = max(0.01, min(ebitda_margin, 0.6))
            assumptions['base_ebitda'] = ebitda_dollars
        elif 'ebitda_margin' not in assumptions:
            assumptions['ebitda_margin'] = 0.25

        if revenue_dollars > 0 and capex_dollars > 0:
            capex_pct = capex_dollars / revenue_dollars
            assumptions['capex_pct'] = max(0.0, min(capex_pct, 0.2))

        if revenue_dollars > 0 and operating_cf_dollars > 0:
            ocf_margin = operating_cf_dollars / revenue_dollars
            # Approximate net working capital need from the gap between EBITDA and operating CF
            if 'nwc_pct' not in assumptions:
                assumptions['nwc_pct'] = max(0.0, min(max(assumptions['ebitda_margin'] - ocf_margin, 0.0), 0.15))

        if hasattr(financial_data, 'beta') and financial_data.beta:
            assumptions['beta'] = financial_data.beta
        elif isinstance(financial_data, dict) and financial_data.get('beta'):
            assumptions['beta'] = financial_data['beta']

        # Calculate WACC components
        if hasattr(financial_data, 'total_debt') and hasattr(financial_data, 'total_equity'):
            debt = total_debt_billion * 1_000_000_000
            equity = getattr(financial_data, 'total_equity', 0) * 1_000_000_000
            total_capital = debt + equity

            if total_capital > 0 and assumptions.get('beta') is not None:
                debt_ratio = debt / total_capital
                equity_ratio = equity / total_capital

                # Use industry-standard assumptions with adjustments when data exists
                risk_free_rate = assumptions.get('risk_free_rate', 0.045)
                market_risk_premium = assumptions.get('market_risk_premium', 0.06)
                cost_of_debt = assumptions.get('cost_of_debt', 0.055)
                tax_rate = assumptions.get('tax_rate', 0.25)

                cost_of_equity = risk_free_rate + assumptions['beta'] * market_risk_premium
                wacc = debt_ratio * cost_of_debt * (1 - tax_rate) + equity_ratio * cost_of_equity

                assumptions.update({
                    'risk_free_rate': risk_free_rate,
                    'market_risk_premium': market_risk_premium,
                    'cost_of_debt': cost_of_debt,
                    'tax_rate': tax_rate,
                    'debt_ratio': debt_ratio,
                    'equity_ratio': equity_ratio,
                    'cost_of_equity': cost_of_equity,
                    'wacc': wacc
                })
                print(f"📊 DEBUG: Calculated WACC: {wacc:.3f} ({wacc*100:.1f}%)")
        else:
            # Fallback WACC calculation
            beta_value = assumptions.get('beta', getattr(financial_data, 'beta', 1.2))
            risk_free_rate = assumptions.get('risk_free_rate', 0.045)
            market_risk_premium = assumptions.get('market_risk_premium', 0.06)
            cost_of_equity = risk_free_rate + beta_value * market_risk_premium
            wacc = assumptions.get('wacc', 0.08)

            assumptions.update({
                'risk_free_rate': risk_free_rate,
                'market_risk_premium': market_risk_premium,
                'cost_of_equity': cost_of_equity,
                'wacc': wacc,
                'debt_ratio': assumptions.get('debt_ratio', 0.4),
                'equity_ratio': assumptions.get('equity_ratio', 0.6)
            })
            print(f"📊 DEBUG: Using default WACC: {wacc:.3f} ({wacc*100:.1f}%)")

        # Net debt assumption for enterprise value bridge
        net_debt_dollars = (total_debt_billion - cash_billion) * 1_000_000_000
        assumptions['net_debt'] = net_debt_dollars

        # Set shares outstanding from financial data
        if hasattr(financial_data, 'shares_outstanding') and financial_data.shares_outstanding > 0:
            assumptions['shares_outstanding'] = financial_data.shares_outstanding
            print(f"📊 DEBUG: Using actual shares outstanding: {financial_data.shares_outstanding/1_000_000:.1f}M")

        return assumptions

class ValidationEngine:
    """Model validation engine."""

    def validate(self, model_spec: ModelSpecification) -> Dict[str, Any]:
        """Validate a model specification."""
        issues = []

        # Basic validation
        if not model_spec.outputs:
            issues.append("No outputs generated")

        if model_spec.model_type not in ['dcf', 'lbo', 'comps', 'three_statement']:
            issues.append(f"Invalid model type: {model_spec.model_type}")

        # Model-specific validation
        if model_spec.model_type == 'dcf':
            wacc = model_spec.outputs.get('wacc', 0)
            if not 0.03 <= wacc <= 0.20:  # Allow 3% to 20% for WACC
                issues.append(f"WACC out of range: {wacc}")

            terminal_growth = model_spec.assumptions.get('terminal_growth', 0)
            if not 0.01 <= terminal_growth <= 0.04:
                issues.append(f"Terminal growth out of range: {terminal_growth}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': []
        }

class SensitivityEngine:
    """Sensitivity analysis engine."""

    def generate_sensitivity(
        self,
        model_type: str,
        calculations: Dict[str, Any],
        assumptions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate sensitivity analysis."""
        sensitivity = {}

        if model_type == 'dcf':
            # WACC sensitivity
            base_wacc = calculations.get('wacc', 0.10)
            wacc_range = [base_wacc * 0.8, base_wacc * 0.9, base_wacc, base_wacc * 1.1, base_wacc * 1.2]

            # Terminal growth sensitivity
            base_growth = assumptions.get('terminal_growth', 0.025)
            growth_range = [0.01, 0.015, 0.02, 0.025, 0.03]

            sensitivity = {
                'wacc_sensitivity': wacc_range,
                'terminal_growth_sensitivity': growth_range,
                'output_metric': 'enterprise_value'
            }

        return sensitivity
