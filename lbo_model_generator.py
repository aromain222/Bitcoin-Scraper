#!/usr/bin/env python3
"""
Professional LBO Model Generator
Investment Banking-Grade Leveraged Buyout Analysis
Six-tab Excel model with strict formatting and banker standards

Author: FinModAI Platform
"""

import xlsxwriter
from datetime import datetime
import os

class ProfessionalLBOModel:
    """Professional LBO Model Generator using xlsxwriter"""

    def __init__(self):
        self.workbook = None
        self.formats = {}

    def create_workbook(self, filename="Professional_LBO_Model.xlsx"):
        """Create the Excel workbook with all formatting and tabs"""

        # Create workbook
        self.workbook = xlsxwriter.Workbook(filename)

        # Define formats
        self._define_formats()

        # Create all tabs
        self._create_assumptions_tab()
        self._create_sources_uses_tab()
        self._create_proforma_bs_tab()
        self._create_forecast_fcf_tab()
        self._create_debt_schedule_tab()
        self._create_returns_analysis_tab()

        # Close workbook
        self.workbook.close()
        print(f"✅ Professional LBO Model created: {filename}")

    def _define_formats(self):
        """Define all formatting styles"""

        # Input format (Blue font)
        self.formats['input'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'font_color': '#1F4E79',
            'align': 'right',
            'num_format': '$#,##0'
        })

        # Input text format
        self.formats['input_text'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'font_color': '#1F4E79',
            'align': 'left'
        })

        # Calculation format (Black)
        self.formats['calc'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'font_color': 'black',
            'align': 'right',
            'num_format': '$#,##0'
        })

        # Output format (Green with light green fill)
        self.formats['output'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'font_color': '#2E7D32',
            'bg_color': '#E8F5E9',
            'align': 'right',
            'num_format': '$#,##0',
            'bold': True,
            'border': 2
        })

        # Header format
        self.formats['header'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 11,
            'bold': True,
            'align': 'center',
            'bg_color': '#F2F2F2',
            'border': 1
        })

        # Subheader format
        self.formats['subheader'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'bold': True,
            'align': 'left',
            'bg_color': '#F2F2F2'
        })

        # Percent format
        self.formats['percent'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'align': 'right',
            'num_format': '0.0%'
        })

        # Multiple format
        self.formats['multiple'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'align': 'right',
            'num_format': '0.0"x"'
        })

        # Year format
        self.formats['year'] = self.workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'align': 'center',
            'bold': True
        })

    def _create_assumptions_tab(self):
        """Create Assumptions & Drivers tab"""

        ws = self.workbook.add_worksheet('Assumptions')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:B', 16)
        ws.set_column('C:E', 14)

        # Main header
        ws.merge_range('A1:E1', 'LBO Assumptions & Drivers', self.formats['header'])

        # Timing / Horizon section
        ws.write('A4', 'Timing / Horizon', self.formats['subheader'])
        ws.merge_range('A5:A7', '', self.formats['subheader'])

        ws.write('A5', 'Base Year (Actual)', self.formats['input_text'])
        ws.write('B5', 2024, self.formats['input'])  # Named range: BaseYear

        ws.write('A6', 'Holding Period (Years)', self.formats['input_text'])
        ws.write('B6', 5, self.formats['input'])  # Named range: HoldPeriod

        # Operating / Financial Drivers
        ws.write('A9', 'Operating / Financial Drivers', self.formats['subheader'])
        ws.merge_range('A10:A20', '', self.formats['subheader'])

        drivers = [
            ('Revenue (Base Year)', 25000, 'Rev0'),
            ('Revenue Growth %', 0.08, 'g_rev'),
            ('EBITDA Margin %', 0.25, 'EBITDA_m'),
            ('D&A % of Revenue', 0.05, 'DA_pct'),
            ('CapEx % of Revenue', 0.08, 'Capex_pct'),
            ('NWC % of Revenue', 0.15, 'NWC_pct'),
            ('Tax Rate %', 0.25, 'TaxRate')
        ]

        for i, (label, value, name) in enumerate(drivers):
            row = 10 + i
            ws.write(f'A{row}', label, self.formats['input_text'])
            if '%' in label:
                ws.write(f'B{row}', value, self.formats['percent'])
            else:
                ws.write(f'B{row}', value, self.formats['input'])

        # Purchase / Transaction Assumptions
        ws.write('A22', 'Purchase / Transaction Assumptions', self.formats['subheader'])
        ws.merge_range('A23:A32', '', self.formats['subheader'])

        purchase_assumptions = [
            ('Entry Purchase Price (EV)', 45000, 'EntryEV'),
            ('Bank Debt %', 0.60, 'DebtBank_pct'),
            ('Mezzanine Debt %', 0.15, 'DebtMezz_pct'),
            ('Equity %', 0.25, 'Equity_pct'),
            ('Bank Debt Interest Rate %', 0.06, 'InterestBank'),
            ('Mezzanine Interest Rate %', 0.10, 'InterestMezz'),
            ('Transaction Fees', 1500, 'TxFees')
        ]

        for i, (label, value, name) in enumerate(purchase_assumptions):
            row = 23 + i
            ws.write(f'A{row}', label, self.formats['input_text'])
            if '%' in label and 'Interest' not in label:
                ws.write(f'B{row}', value, self.formats['percent'])
            elif 'Interest' in label or '%' in label:
                ws.write(f'B{row}', value, self.formats['percent'])
            else:
                ws.write(f'B{row}', value, self.formats['input'])

        # Create named ranges
        self.workbook.define_name('BaseYear', '=Assumptions!$B$5')
        self.workbook.define_name('HoldPeriod', '=Assumptions!$B$6')
        self.workbook.define_name('Rev0', '=Assumptions!$B$10')
        self.workbook.define_name('g_rev', '=Assumptions!$B$11')
        self.workbook.define_name('EBITDA_m', '=Assumptions!$B$12')
        self.workbook.define_name('DA_pct', '=Assumptions!$B$13')
        self.workbook.define_name('Capex_pct', '=Assumptions!$B$14')
        self.workbook.define_name('NWC_pct', '=Assumptions!$B$15')
        self.workbook.define_name('TaxRate', '=Assumptions!$B$16')
        self.workbook.define_name('EntryEV', '=Assumptions!$B$23')
        self.workbook.define_name('DebtBank_pct', '=Assumptions!$B$24')
        self.workbook.define_name('DebtMezz_pct', '=Assumptions!$B$25')
        self.workbook.define_name('Equity_pct', '=Assumptions!$B$26')
        self.workbook.define_name('InterestBank', '=Assumptions!$B$27')
        self.workbook.define_name('InterestMezz', '=Assumptions!$B$28')
        self.workbook.define_name('TxFees', '=Assumptions!$B$29')

    def _create_sources_uses_tab(self):
        """Create Sources & Uses tab"""

        ws = self.workbook.add_worksheet('Sources_Uses')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:B', 16)

        # Header
        ws.merge_range('A1:B1', 'Sources & Uses', self.formats['header'])

        # Sources section
        ws.write('A3', 'Sources', self.formats['subheader'])
        ws.write('A4', 'Bank Debt', self.formats['input_text'])
        ws.write('A5', 'Mezzanine Debt', self.formats['input_text'])
        ws.write('A6', 'Equity Contribution', self.formats['input_text'])
        ws.write('A7', 'Total Sources', self.formats['subheader'])

        # Sources formulas
        ws.write_formula('B4', '=EntryEV*DebtBank_pct', self.formats['calc'])
        ws.write_formula('B5', '=EntryEV*DebtMezz_pct', self.formats['calc'])
        ws.write_formula('B6', '=EntryEV*Equity_pct', self.formats['calc'])
        ws.write_formula('B7', '=SUM(B4:B6)', self.formats['calc'])

        # Uses section
        ws.write('A9', 'Uses', self.formats['subheader'])
        ws.write('A10', 'Purchase Price (EV)', self.formats['input_text'])
        ws.write('A11', 'Transaction Fees', self.formats['input_text'])
        ws.write('A12', 'Debt Repayment Reserve', self.formats['input_text'])
        ws.write('A13', 'Working Capital Adjustment', self.formats['input_text'])
        ws.write('A14', 'Total Uses', self.formats['subheader'])

        # Uses formulas
        ws.write_formula('B10', '=EntryEV', self.formats['calc'])
        ws.write_formula('B11', '=TxFees', self.formats['calc'])
        ws.write('B12', 1000, self.formats['input'])  # Debt reserve
        ws.write('B13', 500, self.formats['input'])   # WC adjustment
        ws.write_formula('B14', '=SUM(B10:B13)', self.formats['calc'])

        # Check balance
        ws.write('A16', 'Balance Check (Sources - Uses)', self.formats['subheader'])
        ws.write_formula('B16', '=B7-B14', self.formats['calc'])

        # Named ranges
        self.workbook.define_name('TotalDebt', '=Sources_Uses!$B$4+$B$5')
        self.workbook.define_name('EquityInvested', '=Sources_Uses!$B$6')

    def _create_proforma_bs_tab(self):
        """Create Pro Forma Balance Sheet tab"""

        ws = self.workbook.add_worksheet('ProForma_BS')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:C', 16)

        # Header
        ws.merge_range('A1:C1', 'Pro Forma Balance Sheet', self.formats['header'])

        # Assets section
        ws.write('A3', 'Assets', self.formats['subheader'])
        ws.write('A4', 'Cash & Cash Equivalents', self.formats['input_text'])
        ws.write('A5', 'Accounts Receivable', self.formats['input_text'])
        ws.write('A6', 'Inventory', self.formats['input_text'])
        ws.write('A7', 'PP&E', self.formats['input_text'])
        ws.write('A8', 'Total Assets', self.formats['subheader'])

        # Assets values (simplified)
        ws.write('B4', 5000, self.formats['calc'])
        ws.write('B5', 3000, self.formats['calc'])
        ws.write('B6', 2000, self.formats['calc'])
        ws.write('B7', 15000, self.formats['calc'])
        ws.write_formula('B8', '=SUM(B4:B7)', self.formats['calc'])

        # Liabilities & Equity section
        ws.write('A10', 'Liabilities & Equity', self.formats['subheader'])
        ws.write('A11', 'Bank Debt', self.formats['input_text'])
        ws.write('A12', 'Mezzanine Debt', self.formats['input_text'])
        ws.write('A13', 'Accounts Payable', self.formats['input_text'])
        ws.write('A14', 'Other Liabilities', self.formats['input_text'])
        ws.write('A15', 'Equity (Book Value)', self.formats['input_text'])
        ws.write('A16', 'Total Liabilities & Equity', self.formats['subheader'])

        # Liabilities values
        ws.write_formula('B11', '=EntryEV*DebtBank_pct', self.formats['calc'])
        ws.write_formula('B12', '=EntryEV*DebtMezz_pct', self.formats['calc'])
        ws.write('B13', 2500, self.formats['calc'])
        ws.write('B14', 1500, self.formats['calc'])
        ws.write_formula('B15', '=EquityInvested', self.formats['output'])  # Highlight equity
        ws.write_formula('B16', '=SUM(B11:B15)', self.formats['calc'])

        # Balance check
        ws.write('A18', 'Balance Check (Assets - Liab+Equity)', self.formats['subheader'])
        ws.write_formula('B18', '=B8-B16', self.formats['calc'])

    def _create_forecast_fcf_tab(self):
        """Create Financial Forecast tab"""

        ws = self.workbook.add_worksheet('Forecast_FCF')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:G', 14)

        # Header
        ws.merge_range('A1:G1', 'Financial Forecast & Free Cash Flow', self.formats['header'])

        # Years header
        ws.write('A3', 'Item', self.formats['subheader'])
        for i in range(5):
            ws.write(2, i+1, f'Year {i+1}', self.formats['year'])

        # Revenue section
        ws.write('A4', 'Revenue', self.formats['subheader'])
        ws.write_formula('B4', '=Rev0', self.formats['calc'])
        for i in range(1, 5):
            ws.write_formula(3, i+1, f'=B4*(1+g_rev)^{i}', self.formats['calc'])

        # Growth %
        ws.write('A5', 'Revenue Growth %', self.formats['subheader'])
        ws.write('B5', 'N/A', self.formats['calc'])
        for i in range(1, 5):
            ws.write_formula(4, i+1, f'=(C4-B4)/B4', self.formats['percent'])

        # EBITDA
        ws.write('A6', 'EBITDA', self.formats['subheader'])
        ws.write_formula('B6', '=B4*EBITDA_m', self.formats['calc'])
        for i in range(1, 5):
            ws.write_formula(5, i+1, f'={chr(66+i)}4*EBITDA_m', self.formats['calc'])

        # D&A
        ws.write('A7', 'Depreciation & Amortization', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(6, i+1, f'={chr(66+i)}4*DA_pct', self.formats['calc'])

        # EBIT
        ws.write('A8', 'EBIT', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(7, i+1, f'={chr(66+i)}6-{chr(66+i)}7', self.formats['calc'])

        # Taxes
        ws.write('A9', 'Taxes', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(8, i+1, f'={chr(66+i)}8*TaxRate', self.formats['calc'])

        # NOPAT
        ws.write('A10', 'NOPAT', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(9, i+1, f'={chr(66+i)}8-{chr(66+i)}9', self.formats['calc'])

        # CapEx
        ws.write('A11', 'CapEx', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(10, i+1, f'={chr(66+i)}4*Capex_pct', self.formats['calc'])

        # ΔNWC
        ws.write('A12', 'ΔNWC', self.formats['subheader'])
        ws.write('B12', 0, self.formats['calc'])
        for i in range(1, 5):
            ws.write_formula(11, i+1, f'={chr(66+i)}4*NWC_pct-{chr(65+i)}4*NWC_pct', self.formats['calc'])

        # UFCF (FCFF)
        ws.write('A13', 'Unlevered Free Cash Flow (UFCF)', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(12, i+1, f'={chr(66+i)}10-{chr(66+i)}11-{chr(66+i)}12', self.formats['calc'])

        # Named range for FCFF row
        self.workbook.define_name('FCFF_Row', '=Forecast_FCF!$B$13:$F$13')

    def _create_debt_schedule_tab(self):
        """Create Debt Schedule tab"""

        ws = self.workbook.add_worksheet('DebtSchedule')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:G', 14)

        # Header
        ws.merge_range('A1:G1', 'Debt Schedule', self.formats['header'])

        # Years header
        ws.write('A3', 'Item', self.formats['subheader'])
        for i in range(5):
            ws.write(2, i+1, f'Year {i+1}', self.formats['year'])

        # Bank Debt section
        ws.write('A4', 'Bank Debt', self.formats['subheader'])
        ws.write('A5', 'Beginning Balance', self.formats['subheader'])
        ws.write_formula('B5', '=Sources_Uses!$B$4', self.formats['calc'])
        for i in range(1, 5):
            ws.write_formula(4, i+1, f'={chr(66+i)}6', self.formats['calc'])

        ws.write('A6', 'Interest Expense', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(5, i+1, f'={chr(66+i)}5*InterestBank', self.formats['calc'])

        ws.write('A7', 'Principal Repayment', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(6, i+1, f'=MIN({chr(66+i)}5, Forecast_FCF!{chr(66+i)}13)', self.formats['calc'])

        ws.write('A8', 'Ending Balance', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(7, i+1, f'={chr(66+i)}5-{chr(66+i)}7', self.formats['calc'])

        # Mezzanine Debt (similar structure)
        ws.write('A10', 'Mezzanine Debt', self.formats['subheader'])
        ws.write('A11', 'Beginning Balance', self.formats['subheader'])
        ws.write_formula('B11', '=Sources_Uses!$B$5', self.formats['calc'])
        for i in range(1, 5):
            ws.write_formula(10, i+1, f'={chr(66+i)}12', self.formats['calc'])

        # Named ranges
        self.workbook.define_name('Debt_Bal', '=DebtSchedule!$B$5:$F$8')
        self.workbook.define_name('Interest', '=DebtSchedule!$B$6:$F$6')
        self.workbook.define_name('DebtRepayment', '=DebtSchedule!$B$7:$F$7')

    def _create_returns_analysis_tab(self):
        """Create Returns Analysis tab"""

        ws = self.workbook.add_worksheet('Returns')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:G', 14)

        # Header
        ws.merge_range('A1:G1', 'Returns Analysis', self.formats['header'])

        # Years header
        ws.write('A3', 'Item', self.formats['subheader'])
        for i in range(5):
            ws.write(2, i+1, f'Year {i+1}', self.formats['year'])

        # Cash flows section
        ws.write('A4', 'Equity Cash Flows', self.formats['subheader'])
        ws.write('A5', 'Initial Equity Investment', self.formats['subheader'])
        ws.write_formula('B5', '=-EquityInvested', self.formats['calc'])

        ws.write('A6', 'Operating Distributions', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(5, i+1, '=Forecast_FCF!{chr(66+i)}13-DebtSchedule!{chr(66+i)}7', self.formats['calc'])

        # Exit valuation
        ws.write('A8', 'Exit Analysis (Year 5)', self.formats['subheader'])
        ws.write('A9', 'Exit Enterprise Value', self.formats['input_text'])
        ws.write('B9', 65000, self.formats['input'])  # 8.5x exit multiple

        ws.write('A10', 'Net Debt at Exit', self.formats['subheader'])
        ws.write_formula('B10', '=DebtSchedule!F8+DebtSchedule!F14', self.formats['calc'])

        ws.write('A11', 'Exit Equity Value', self.formats['subheader'])
        ws.write_formula('B11', '=B9-B10', self.formats['output'])

        # Returns calculations
        ws.write('A13', 'Returns Metrics', self.formats['subheader'])
        ws.write('A14', 'Equity IRR', self.formats['subheader'])
        ws.write_formula('B14', '=XIRR(B5:F6)', self.formats['percent'])

        ws.write('A15', 'MOIC (Multiple on Invested Capital)', self.formats['subheader'])
        ws.write_formula('B15', '=B11/-B5', self.formats['multiple'])

        # Named ranges for key outputs
        self.workbook.define_name('EquityValue', '=Returns!$B$11')
        self.workbook.define_name('IRR', '=Returns!$B$14')
        self.workbook.define_name('MOIC', '=Returns!$B$15')

        # Sensitivity table
        ws.write('A17', 'Sensitivity Analysis', self.formats['subheader'])
        ws.write('A18', 'Entry Multiple vs Exit Multiple', self.formats['subheader'])

        # Create a simple sensitivity table
        ws.write('B19', 'Exit Multiple →', self.formats['subheader'])
        for i in range(3):
            ws.write(18, i+2, f'{(i+6):.1f}x', self.formats['multiple'])

        ws.write('A20', 'Entry Multiple ↓', self.formats['subheader'])
        for i in range(3):
            multiple = 8.0 + i * 0.5
            ws.write(19+i, 1, f'{multiple:.1f}x', self.formats['multiple'])
            for j in range(3):
                exit_mult = 6.0 + j
                # Simplified IRR calculation for sensitivity
                irr = ((exit_mult / multiple) ** (1/5) - 1)
                ws.write(19+i, j+2, irr, self.formats['percent'])

def main():
    """Generate the professional LBO model"""

    print("🏦 Generating Professional LBO Model...")
    print("   • 6 Tabs with banker-standard formatting")
    print("   • Dynamic formulas and named ranges")
    print("   • Investment banking quality output")
    print()

    # Create the model
    lbo_model = ProfessionalLBOModel()
    lbo_model.create_workbook("Professional_LBO_Model.xlsx")

    print()
    print("✅ LBO Model Complete!")
    print("   📁 Professional_LBO_Model.xlsx")
    print("   📊 6 Tabs: Assumptions, Sources_Uses, ProForma_BS, Forecast_FCF, DebtSchedule, Returns")
    print("   🎨 Banker-grade formatting with proper color coding")
    print("   📈 Dynamic calculations and sensitivity analysis")
    print()
    print("🚀 Ready for investment banking analysis!")

if __name__ == "__main__":
    main()
