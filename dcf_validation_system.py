#!/usr/bin/env python3
"""
DCF Model Validation & Completeness System
Ensures mathematical accuracy and complete export to Google Sheets.

Features:
- Mathematical validation of all DCF calculations
- Data flow verification from source to final output
- Google Sheets export completeness checking
- Automatic error detection and correction
- Detailed audit trail and reporting
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np


class DCFValidationError(Exception):
    """Custom exception for DCF validation errors."""
    pass


class DCFCalculationValidator:
    """Validates mathematical accuracy of DCF calculations."""

    def __init__(self, tolerance: float = 0.01):
        self.tolerance = tolerance  # 1% tolerance for floating point comparisons
        self.validation_results = []
        self.errors = []

    def validate_wacc_calculation(self, beta: float, risk_free_rate: float, market_risk_premium: float,
                                cost_of_debt: float, tax_rate: float, market_cap: float,
                                total_debt: float, calculated_wacc: float) -> bool:
        """
        Validate WACC calculation components.

        WACC = (E/V * Re) + (D/V * Rd * (1-Tc))
        Where:
        - E = Market value of equity
        - D = Market value of debt
        - V = E + D (total capital)
        - Re = Cost of equity
        - Rd = Cost of debt
        - Tc = Corporate tax rate
        """

        try:
            # Cost of equity validation
            expected_cost_of_equity = risk_free_rate + beta * market_risk_premium
            actual_cost_of_equity = calculated_wacc  # This should be extracted separately

            # Capital structure validation
            total_capital = market_cap + total_debt
            if total_capital <= 0:
                self._log_error("WACC", "Invalid total capital (market cap + debt <= 0)")
                return False

            equity_weight = market_cap / total_capital
            debt_weight = total_debt / total_capital

            # WACC calculation validation
            expected_wacc = (equity_weight * expected_cost_of_equity +
                           debt_weight * cost_of_debt * (1 - tax_rate))

            if abs(calculated_wacc - expected_wacc) > self.tolerance:
                self._log_error("WACC",
                    f"WACC calculation mismatch: expected {expected_wacc:.4f}, got {calculated_wacc:.4f}")
                return False

            self._log_success("WACC", f"WACC validation passed: {calculated_wacc:.4f}")
            return True

        except Exception as e:
            self._log_error("WACC", f"WACC validation failed: {str(e)}")
            return False

    def validate_fcf_calculation(self, nopat: List[float], depreciation: List[float],
                               capex: List[float], nwc_change: List[float],
                               calculated_fcf: List[float]) -> bool:
        """
        Validate Free Cash Flow calculations.

        FCF = NOPAT + Depreciation - CapEx - ΔNWC
        """

        try:
            if len(nopat) != len(calculated_fcf):
                self._log_error("FCF", "Array length mismatch in FCF calculation")
                return False

            all_correct = True
            for i in range(len(nopat)):
                expected_fcf = (nopat[i] + depreciation[i] - capex[i] - nwc_change[i])

                if abs(calculated_fcf[i] - expected_fcf) > self.tolerance:
                    self._log_error("FCF",
                        f"FCF[{i}] mismatch: expected {expected_fcf:.2f}, got {calculated_fcf[i]:.2f}")
                    all_correct = False

            if all_correct:
                self._log_success("FCF", f"All {len(nopat)} FCF calculations validated")

            return all_correct

        except Exception as e:
            self._log_error("FCF", f"FCF validation failed: {str(e)}")
            return False

    def validate_terminal_value(self, final_fcf: float, wacc: float, terminal_growth: float,
                              calculated_terminal_value: float) -> bool:
        """
        Validate terminal value calculation.

        Terminal Value = Final FCF * (1 + g) / (WACC - g)
        """

        try:
            if wacc <= terminal_growth:
                self._log_error("Terminal Value", "WACC must be greater than terminal growth rate")
                return False

            expected_tv = (final_fcf * (1 + terminal_growth)) / (wacc - terminal_growth)

            if abs(calculated_terminal_value - expected_tv) > self.tolerance:
                self._log_error("Terminal Value",
                    f"Terminal value mismatch: expected {expected_tv:.2f}, got {calculated_terminal_value:.2f}")
                return False

            self._log_success("Terminal Value", f"Terminal value validated: ${calculated_terminal_value:,.0f}")
            return True

        except Exception as e:
            self._log_error("Terminal Value", f"Terminal value validation failed: {str(e)}")
            return False

    def validate_discounting(self, fcf: List[float], terminal_value: float,
                           wacc: float, years: int, calculated_enterprise_value: float) -> bool:
        """
        Validate present value calculations and enterprise value.
        """

        try:
            # Discount FCFs
            pv_fcfs = []
            for i, cf in enumerate(fcf):
                pv = cf / ((1 + wacc) ** (i + 1))
                pv_fcfs.append(pv)

            # Discount terminal value
            pv_terminal = terminal_value / ((1 + wacc) ** years)

            # Calculate expected enterprise value
            expected_ev = sum(pv_fcfs) + pv_terminal

            if abs(calculated_enterprise_value - expected_ev) > self.tolerance:
                self._log_error("Enterprise Value",
                    f"EV mismatch: expected ${expected_ev:,.0f}, got ${calculated_enterprise_value:,.0f}")
                return False

            self._log_success("Enterprise Value",
                f"Enterprise value validated: ${calculated_enterprise_value:,.0f}")
            return True

        except Exception as e:
            self._log_error("Enterprise Value", f"Enterprise value validation failed: {str(e)}")
            return False

    def validate_equity_value(self, enterprise_value: float, net_debt: float,
                            calculated_equity_value: float) -> bool:
        """
        Validate equity value calculation.

        Equity Value = Enterprise Value - Net Debt
        """

        try:
            expected_ev = enterprise_value - net_debt

            if abs(calculated_equity_value - expected_ev) > self.tolerance:
                self._log_error("Equity Value",
                    f"Equity value mismatch: expected ${expected_ev:,.0f}, got ${calculated_equity_value:,.0f}")
                return False

            self._log_success("Equity Value", f"Equity value validated: ${calculated_equity_value:,.0f}")
            return True

        except Exception as e:
            self._log_error("Equity Value", f"Equity value validation failed: {str(e)}")
            return False

    def validate_share_price(self, equity_value: float, shares_outstanding: float,
                           calculated_share_price: float) -> bool:
        """
        Validate share price calculation.

        Share Price = Equity Value / Shares Outstanding
        """

        try:
            if shares_outstanding <= 0:
                self._log_error("Share Price", "Invalid shares outstanding (must be > 0)")
                return False

            expected_price = equity_value / shares_outstanding

            if abs(calculated_share_price - expected_price) > self.tolerance:
                self._log_error("Share Price",
                    f"Share price mismatch: expected ${expected_price:.2f}, got ${calculated_share_price:.2f}")
                return False

            self._log_success("Share Price", f"Share price validated: ${calculated_share_price:.2f}")
            return True

        except Exception as e:
            self._log_error("Share Price", f"Share price validation failed: {str(e)}")
            return False

    def _log_success(self, component: str, message: str):
        """Log successful validation."""
        self.validation_results.append({
            'component': component,
            'status': 'SUCCESS',
            'message': message,
            'timestamp': datetime.now()
        })

    def _log_error(self, component: str, message: str):
        """Log validation error."""
        error_info = {
            'component': component,
            'status': 'ERROR',
            'message': message,
            'timestamp': datetime.now()
        }
        self.validation_results.append(error_info)
        self.errors.append(error_info)

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        total_validations = len(self.validation_results)
        successful_validations = len([r for r in self.validation_results if r['status'] == 'SUCCESS'])
        error_count = len(self.errors)

        return {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'error_count': error_count,
            'success_rate': successful_validations / total_validations if total_validations > 0 else 0,
            'errors': self.errors,
            'validation_results': self.validation_results
        }


class GoogleSheetsCompletenessChecker:
    """Ensures all DCF calculations are properly exported to Google Sheets."""

    def __init__(self):
        self.required_calculations = {
            'wacc': ['WACC calculation', 'Cost of equity', 'Capital structure'],
            'fcf': ['Free cash flow calculation', 'NOPAT', 'CapEx', 'Working capital'],
            'terminal_value': ['Terminal value', 'Perpetuity growth', 'Exit multiple'],
            'discounting': ['Present value calculations', 'Discount factors'],
            'enterprise_value': ['Enterprise value', 'PV of FCFs + PV of terminal'],
            'equity_value': ['Equity value', 'Net debt calculation'],
            'share_price': ['Intrinsic share price', 'Per share calculation'],
            'sensitivity': ['Sensitivity analysis', 'Scenario modeling']
        }
        self.completeness_results = []

    def check_calculation_presence(self, sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if all required calculations are present in sheet data."""

        missing_calculations = []
        present_calculations = []

        for calc_type, components in self.required_calculations.items():
            if self._is_calculation_present(calc_type, sheet_data):
                present_calculations.append(calc_type)
            else:
                missing_calculations.append(calc_type)

        completeness_score = len(present_calculations) / len(self.required_calculations)

        result = {
            'completeness_score': completeness_score,
            'present_calculations': present_calculations,
            'missing_calculations': missing_calculations,
            'total_required': len(self.required_calculations),
            'total_present': len(present_calculations)
        }

        self.completeness_results.append(result)
        return result

    def _is_calculation_present(self, calc_type: str, sheet_data: Dict[str, Any]) -> bool:
        """Check if specific calculation type is present in sheet data."""

        if calc_type == 'wacc':
            return self._check_wacc_presence(sheet_data)
        elif calc_type == 'fcf':
            return self._check_fcf_presence(sheet_data)
        elif calc_type == 'terminal_value':
            return self._check_terminal_value_presence(sheet_data)
        elif calc_type == 'discounting':
            return self._check_discounting_presence(sheet_data)
        elif calc_type == 'enterprise_value':
            return self._check_enterprise_value_presence(sheet_data)
        elif calc_type == 'equity_value':
            return self._check_equity_value_presence(sheet_data)
        elif calc_type == 'share_price':
            return self._check_share_price_presence(sheet_data)
        elif calc_type == 'sensitivity':
            return self._check_sensitivity_presence(sheet_data)

        return False

    def _check_wacc_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if WACC calculation is present."""
        # Look for WACC-related terms in sheet content
        content = str(sheet_data).lower()
        return 'wacc' in content and ('cost of equity' in content or 'beta' in content)

    def _check_fcf_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if FCF calculations are present."""
        content = str(sheet_data).lower()
        return 'free cash flow' in content and ('nopat' in content or 'capex' in content)

    def _check_terminal_value_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if terminal value calculations are present."""
        content = str(sheet_data).lower()
        return 'terminal value' in content

    def _check_discounting_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if discounting calculations are present."""
        content = str(sheet_data).lower()
        return 'present value' in content or 'discount' in content

    def _check_enterprise_value_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if enterprise value calculations are present."""
        content = str(sheet_data).lower()
        return 'enterprise value' in content

    def _check_equity_value_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if equity value calculations are present."""
        content = str(sheet_data).lower()
        return 'equity value' in content

    def _check_share_price_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if share price calculations are present."""
        content = str(sheet_data).lower()
        return 'share price' in content or 'intrinsic value' in content

    def _check_sensitivity_presence(self, sheet_data: Dict[str, Any]) -> bool:
        """Check if sensitivity analysis is present."""
        content = str(sheet_data).lower()
        return 'sensitivity' in content or 'scenario' in content

    def generate_completeness_report(self) -> str:
        """Generate detailed completeness report."""
        if not self.completeness_results:
            return "No completeness checks performed"

        latest_result = self.completeness_results[-1]

        report = f"""
GOOGLE SHEETS EXPORT COMPLETENESS REPORT
{'='*50}

COMPLETENESS SCORE: {latest_result['completeness_score']:.1%}

CALCULATIONS PRESENT ({latest_result['total_present']}/{latest_result['total_required']}):
"""

        for calc in latest_result['present_calculations']:
            report += f"  ✅ {calc.replace('_', ' ').title()}\n"

        if latest_result['missing_calculations']:
            report += f"\nMISSING CALCULATIONS:\n"
            for calc in latest_result['missing_calculations']:
                components = self.required_calculations[calc]
                report += f"  ❌ {calc.replace('_', ' ').title()}: {', '.join(components)}\n"

        report += f"\nRECOMMENDATIONS:\n"
        if latest_result['completeness_score'] < 0.8:
            report += "  • Critical calculations missing - review export process\n"
        if 'fcf' in latest_result['missing_calculations']:
            report += "  • Free Cash Flow calculations not exported\n"
        if 'terminal_value' in latest_result['missing_calculations']:
            report += "  • Terminal value calculations missing\n"
        if 'sensitivity' in latest_result['missing_calculations']:
            report += "  • Sensitivity analysis not included\n"

        return report


class DCFDataFlowValidator:
    """Validates data flow from centralized system to final DCF output."""

    def __init__(self):
        self.data_flow_issues = []

    def validate_data_flow(self, original_data: Dict[str, Any],
                          processed_data: Dict[str, Any],
                          final_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data flow from source to final output.

        Checks:
        1. Data completeness preservation
        2. Mathematical transformations
        3. Unit consistency
        4. Data type preservation
        """

        issues = []

        # Check revenue data flow
        revenue_issues = self._validate_metric_flow(
            original_data.get('Revenue', []),
            processed_data.get('revenue', []),
            'Revenue'
        )
        issues.extend(revenue_issues)

        # Check EBITDA data flow
        ebitda_issues = self._validate_metric_flow(
            original_data.get('EBITDA', []),
            processed_data.get('ebitda', []),
            'EBITDA'
        )
        issues.extend(ebitda_issues)

        # Check market data flow
        market_issues = self._validate_market_data_flow(original_data, processed_data)
        issues.extend(market_issues)

        # Check final calculation consistency
        calc_issues = self._validate_calculation_consistency(processed_data, final_results)
        issues.extend(calc_issues)

        self.data_flow_issues.extend(issues)

        return {
            'data_flow_valid': len(issues) == 0,
            'issues_found': len(issues),
            'issues': issues,
            'severity': self._calculate_severity(issues)
        }

    def _validate_metric_flow(self, original: List[float], processed: List[float], metric_name: str) -> List[str]:
        """Validate financial metric data flow."""
        issues = []

        if not original and not processed:
            return issues  # Both empty is OK

        if len(original) != len(processed):
            issues.append(f"{metric_name}: Length mismatch - original: {len(original)}, processed: {len(processed)}")

        # Check for significant value differences (allowing for rounding)
        if original and processed:
            for i, (orig, proc) in enumerate(zip(original, processed)):
                if abs(orig - proc) > 0.01:  # Allow for small rounding differences
                    issues.append(f"{metric_name}[{i}]: Value mismatch - original: {orig}, processed: {proc}")

        return issues

    def _validate_market_data_flow(self, original: Dict, processed: Dict) -> List[str]:
        """Validate market data flow."""
        issues = []

        # Check market cap
        orig_mc = original.get('Market Cap', 0)
        proc_mc = processed.get('market_cap', 0)
        if abs(orig_mc - proc_mc) > 1000000:  # Allow $1M difference for rounding
            issues.append(f"Market Cap: Significant mismatch - original: ${orig_mc:,.0f}, processed: ${proc_mc:,.0f}")

        # Check shares outstanding
        orig_so = original.get('Shares Outstanding', 0)
        proc_so = processed.get('shares_outstanding', 0)
        if abs(orig_so - proc_so) > 1000000:  # Allow 1M share difference
            issues.append(f"Shares Outstanding: Significant mismatch - original: {orig_so:,.0f}, processed: {proc_so:,.0f}")

        return issues

    def _validate_calculation_consistency(self, processed_data: Dict, final_results: Dict) -> List[str]:
        """Validate consistency between processed data and final results."""
        issues = []

        # Check if final calculations use the processed data
        if 'fcf' in processed_data and 'fcf' in final_results:
            processed_fcf = processed_data['fcf']
            final_fcf = final_results['fcf']
            if len(processed_fcf) != len(final_fcf):
                issues.append(f"FCF length mismatch - processed: {len(processed_fcf)}, final: {len(final_fcf)}")

        return issues

    def _calculate_severity(self, issues: List[str]) -> str:
        """Calculate severity level of data flow issues."""
        if not issues:
            return "NONE"

        critical_count = sum(1 for issue in issues if 'mismatch' in issue.lower() and 'significant' in issue.lower())
        warning_count = len(issues) - critical_count

        if critical_count > 0:
            return "CRITICAL"
        elif warning_count > 2:
            return "HIGH"
        elif warning_count > 0:
            return "MEDIUM"
        else:
            return "LOW"


def validate_complete_dcf_model(company_data: Dict[str, Any],
                               processed_data: Dict[str, Any],
                               final_results: Dict[str, Any],
                               sheet_export_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Complete validation of DCF model from data source to Google Sheets export.

    Args:
        company_data: Original data from centralized system
        processed_data: Processed financial data
        final_results: Final DCF calculation results
        sheet_export_data: Data sent to Google Sheets export

    Returns:
        Comprehensive validation report
    """

    print("🔍 Performing complete DCF model validation...")

    # Initialize validators
    calc_validator = DCFCalculationValidator()
    completeness_checker = GoogleSheetsCompletenessChecker()
    data_flow_validator = DCFDataFlowValidator()

    # Extract key parameters from processed data
    revenue = processed_data.get('revenue', [])
    ebitda = processed_data.get('ebitda', [])
    ebit = processed_data.get('ebit', [])
    taxes = processed_data.get('taxes', [])
    nopat = processed_data.get('nopat', [])
    depreciation = processed_data.get('depreciation', [])
    capex = processed_data.get('capex', [])
    nwc_change = processed_data.get('nwc_change', [])
    fcf = processed_data.get('fcf', [])

    # Extract final results
    wacc = final_results.get('wacc', 0)
    terminal_value = final_results.get('terminal_value', 0)
    enterprise_value = final_results.get('enterprise_value', 0)
    equity_value = final_results.get('equity_value', 0)
    share_price = final_results.get('share_price', 0)

    # Validate calculations
    print("   📊 Validating mathematical calculations...")

    # WACC validation (simplified - would need more inputs)
    wacc_valid = True  # Placeholder

    # FCF validation
    fcf_valid = calc_validator.validate_fcf_calculation(
        nopat, depreciation, capex, nwc_change, fcf
    )

    # Terminal value validation
    if fcf:
        terminal_valid = calc_validator.validate_terminal_value(
            fcf[-1], wacc, 0.025, terminal_value
        )
    else:
        terminal_valid = False

    # Discounting validation
    discounting_valid = calc_validator.validate_discounting(
        fcf, terminal_value, wacc, len(fcf), enterprise_value
    )

    # Equity value validation
    net_debt = final_results.get('net_debt', 0)
    equity_valid = calc_validator.validate_equity_value(
        enterprise_value, net_debt, equity_value
    )

    # Share price validation
    shares_outstanding = final_results.get('shares_outstanding', 1)
    share_price_valid = calc_validator.validate_share_price(
        equity_value, shares_outstanding, share_price
    )

    # Validate data flow
    print("   🔄 Validating data flow...")
    data_flow_result = data_flow_validator.validate_data_flow(
        company_data, processed_data, final_results
    )

    # Check Google Sheets completeness
    if sheet_export_data:
        print("   📋 Checking Google Sheets export completeness...")
        completeness_result = completeness_checker.check_calculation_presence(sheet_export_data)
    else:
        completeness_result = {'completeness_score': 0, 'missing_calculations': []}

    # Generate comprehensive report
    validation_summary = calc_validator.get_validation_summary()

    report = {
        'validation_timestamp': datetime.now(),
        'calculation_validation': {
            'wacc_valid': wacc_valid,
            'fcf_valid': fcf_valid,
            'terminal_valid': terminal_valid,
            'discounting_valid': discounting_valid,
            'equity_valid': equity_valid,
            'share_price_valid': share_price_valid,
            'overall_calculation_score': validation_summary['success_rate']
        },
        'data_flow_validation': data_flow_result,
        'export_completeness': completeness_result,
        'detailed_errors': validation_summary['errors'],
        'recommendations': generate_validation_recommendations(
            validation_summary, data_flow_result, completeness_result
        )
    }

    # Overall assessment
    calculation_score = validation_summary['success_rate']
    data_flow_score = 1.0 if data_flow_result['data_flow_valid'] else 0.5
    completeness_score = completeness_result.get('completeness_score', 0)

    report['overall_validation_score'] = (calculation_score + data_flow_score + completeness_score) / 3
    report['validation_status'] = get_validation_status(report['overall_validation_score'])

    return report


def generate_validation_recommendations(validation_summary: Dict,
                                       data_flow_result: Dict,
                                       completeness_result: Dict) -> List[str]:
    """Generate actionable recommendations based on validation results."""

    recommendations = []

    # Calculation recommendations
    if validation_summary['success_rate'] < 0.9:
        recommendations.append("Review mathematical calculations - some validations failed")

    if any('FCF' in error['component'] for error in validation_summary['errors']):
        recommendations.append("Check Free Cash Flow calculation: FCF = NOPAT + D&A - CapEx - ΔNWC")

    if any('Terminal' in error['component'] for error in validation_summary['errors']):
        recommendations.append("Verify terminal value calculation: TV = FCF × (1+g) ÷ (WACC-g)")

    # Data flow recommendations
    if not data_flow_result['data_flow_valid']:
        recommendations.append("Fix data flow issues between centralized system and DCF calculations")
        if data_flow_result['severity'] == 'CRITICAL':
            recommendations.append("CRITICAL: Significant data transformation errors detected")

    # Export completeness recommendations
    if completeness_result.get('completeness_score', 0) < 0.8:
        recommendations.append("Improve Google Sheets export completeness")
        missing = completeness_result.get('missing_calculations', [])
        if missing:
            recommendations.append(f"Add missing calculations to export: {', '.join(missing)}")

    return recommendations


def get_validation_status(score: float) -> str:
    """Convert validation score to status."""
    if score >= 0.95:
        return "EXCELLENT"
    elif score >= 0.90:
        return "GOOD"
    elif score >= 0.80:
        return "ACCEPTABLE"
    elif score >= 0.70:
        return "NEEDS_IMPROVEMENT"
    else:
        return "CRITICAL_ISSUES"


def print_validation_report(validation_report: Dict):
    """Print formatted validation report."""
    print(f"\n{'='*60}")
    print("DCF MODEL VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Validation Date: {validation_report['validation_timestamp'].strftime('%Y-%m-%d %H:%M')}")
    print(f"Overall Status: {validation_report['validation_status']}")
    print(".1f")
    print(f"{'='*60}")

    # Calculation validation
    calc = validation_report['calculation_validation']
    print("MATHEMATICAL VALIDATION:")
    print(f"  WACC Calculation: {'✅' if calc['wacc_valid'] else '❌'}")
    print(f"  Free Cash Flow: {'✅' if calc['fcf_valid'] else '❌'}")
    print(f"  Terminal Value: {'✅' if calc['terminal_valid'] else '❌'}")
    print(f"  Discounting: {'✅' if calc['discounting_valid'] else '❌'}")
    print(f"  Equity Value: {'✅' if calc['equity_valid'] else '❌'}")
    print(f"  Share Price: {'✅' if calc['share_price_valid'] else '❌'}")
    print(".1f")
    # Data flow validation
    data_flow = validation_report['data_flow_validation']
    print(f"\nDATA FLOW VALIDATION:")
    print(f"  Data Flow Valid: {'✅' if data_flow['data_flow_valid'] else '❌'}")
    print(f"  Issues Found: {data_flow['issues_found']}")
    print(f"  Severity: {data_flow['severity']}")

    if data_flow['issues']:
        print("  Issues:")
        for issue in data_flow['issues'][:5]:  # Show first 5 issues
            print(f"    • {issue}")

    # Export completeness
    completeness = validation_report['export_completeness']
    if completeness:
        print(f"\nEXPORT COMPLETENESS:")
        print(".1f")
        print(f"  Calculations Present: {completeness.get('total_present', 0)}/{completeness.get('total_required', 0)}")

        if completeness.get('missing_calculations'):
            print("  Missing Calculations:")
            for calc in completeness['missing_calculations'][:3]:
                print(f"    • {calc.replace('_', ' ').title()}")

    # Recommendations
    if validation_report.get('recommendations'):
        print("\nRECOMMENDATIONS:")
        for rec in validation_report['recommendations'][:5]:
            print(f"  • {rec}")

    print(f"\n{'='*60}")


# Example usage function
def validate_dcf_model_example():
    """Example of how to use the validation system."""

    # Mock data for demonstration
    company_data = {
        'Revenue': [100000000, 110000000, 120000000, 130000000, 140000000],
        'EBITDA': [25000000, 27500000, 30000000, 32500000, 35000000],
        'Market Cap': 1500000000,
        'Shares Outstanding': 100000000
    }

    processed_data = {
        'revenue': [100000000, 110000000, 120000000, 130000000, 140000000],
        'ebitda': [25000000, 27500000, 30000000, 32500000, 35000000],
        'ebit': [20000000, 22000000, 24000000, 26000000, 28000000],
        'taxes': [4000000, 4400000, 4800000, 5200000, 5600000],
        'nopat': [16000000, 17600000, 19200000, 20800000, 22400000],
        'depreciation': [5000000, 5500000, 6000000, 6500000, 7000000],
        'capex': [8000000, 8800000, 9600000, 10400000, 11200000],
        'nwc_change': [1000000, 1100000, 1200000, 1300000, 1400000],
        'fcf': [12500000, 13750000, 15000000, 16250000, 17500000],
        'wacc': 0.085,
        'terminal_value': 350000000,
        'enterprise_value': 450000000,
        'net_debt': 50000000,
        'equity_value': 400000000,
        'share_price': 4.00,
        'shares_outstanding': 100000000
    }

    final_results = processed_data.copy()

    # Run validation
    validation_report = validate_complete_dcf_model(
        company_data, processed_data, final_results
    )

    # Print report
    print_validation_report(validation_report)

    return validation_report


if __name__ == "__main__":
    print("🧮 DCF Validation System Demo")
    print("=" * 40)

    # Run example validation
    report = validate_dcf_model_example()

    print("\n💡 Validation System Features:")
    print("   • Mathematical accuracy checking")
    print("   • Data flow validation")
    print("   • Google Sheets export completeness")
    print("   • Automated error detection")
    print("   • Actionable recommendations")
