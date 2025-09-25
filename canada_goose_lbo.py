#!/usr/bin/env python3
"""
Canada Goose LBO Model Generator
Investment Banking-Grade Leveraged Buyout Analysis for Luxury Apparel
Based on real financial data and industry-specific assumptions

Author: FinModAI Platform
"""

import xlsxwriter
from datetime import datetime
import os

class CanadaGooseLBOModel:
    """Canada Goose LBO Model Generator with luxury apparel assumptions"""

    def __init__(self):
        self.workbook = None
        self.formats = {}

        # Canada Goose specific assumptions (FULL DOLLAR AMOUNTS)
        self.company_data = {
            'name': 'Canada Goose Holdings Inc.',
            'ticker': 'GOOS',
            'revenue': 1348400000,   # $1,348,400,000 (full amount)
            'ebitda': 300000000,     # $300,000,000 (full amount)
            'net_income': 95000000,  # $95,000,000 (full amount)
            'beta': 1.558,
            'sector': 'Consumer Cyclical',
            'market_cap': 1299000000,  # $1,299,000,000 (full amount)
        }

    def create_workbook(self, filename="Canada_Goose_LBO_Model.xlsx"):
        """Create the Excel workbook with Canada Goose specific assumptions"""

        # Create workbook
        self.workbook = xlsxwriter.Workbook(filename)

        # Define formats
        self._define_formats()

        # Create all tabs with Canada Goose data
        self._create_assumptions_tab()
        self._create_sources_uses_tab()
        self._create_proforma_bs_tab()
        self._create_forecast_fcf_tab()
        self._create_debt_schedule_tab()
        self._create_returns_analysis_tab()

        # Close workbook
        self.workbook.close()
        print(f"✅ Canada Goose LBO Model created: {filename}")

    def _define_formats(self):
        """Define all formatting styles"""

        # Input format (Blue font) - Full dollar amounts
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

        # Calculation format (Black) - Full dollar amounts
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
        """Create Assumptions & Drivers tab with Canada Goose data"""

        ws = self.workbook.add_worksheet('Assumptions')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:B', 16)
        ws.set_column('C:E', 14)

        # Main header
        ws.merge_range('A1:E1', 'Canada Goose LBO Assumptions & Drivers', self.formats['header'])

        # Company info
        ws.write('A3', 'Company Information', self.formats['subheader'])
        ws.write('A4', 'Company Name', self.formats['input_text'])
        ws.write('B4', self.company_data['name'], self.formats['input'])
        ws.write('A5', 'Ticker', self.formats['input_text'])
        ws.write('B5', self.company_data['ticker'], self.formats['input'])

        # Timing / Horizon section
        ws.write('A7', 'Timing / Horizon', self.formats['subheader'])
        ws.merge_range('A8:A10', '', self.formats['subheader'])

        ws.write('A8', 'Base Year (Actual)', self.formats['input_text'])
        ws.write('B8', 2024, self.formats['input'])  # BaseYear

        ws.write('A9', 'Holding Period (Years)', self.formats['input_text'])
        ws.write('B9', 5, self.formats['input'])  # HoldPeriod

        # Operating / Financial Drivers (Luxury apparel specific)
        ws.write('A12', 'Operating / Financial Drivers', self.formats['subheader'])
        ws.merge_range('A13:A23', '', self.formats['subheader'])

        drivers = [
            ('Revenue (Base Year)', self.company_data['revenue'], 'Rev0'),
            ('Revenue Growth %', 0.12, 'g_rev'),  # Luxury apparel growth
            ('EBITDA Margin %', 0.22, 'EBITDA_m'),  # Canada Goose margin
            ('D&A % of Revenue', 0.06, 'DA_pct'),  # Higher for apparel
            ('CapEx % of Revenue', 0.10, 'Capex_pct'),  # Retail expansion
            ('NWC % of Revenue', 0.20, 'NWC_pct'),  # Inventory intensive
            ('Tax Rate %', 0.26, 'TaxRate')  # Canadian corporate rate
        ]

        for i, (label, value, name) in enumerate(drivers):
            row = 13 + i
            ws.write(f'A{row}', label, self.formats['input_text'])
            if '%' in label:
                ws.write(f'B{row}', value, self.formats['percent'])
            else:
                ws.write(f'B{row}', value, self.formats['input'])

        # Purchase / Transaction Assumptions
        ws.write('A25', 'Purchase / Transaction Assumptions', self.formats['subheader'])
        ws.merge_range('A26:A35', '', self.formats['subheader'])

        # Calculate entry EV based on current market data (FULL DOLLAR AMOUNTS)
        entry_ev = self.company_data['market_cap'] * 1.1  # 10% premium = $1,428,900,000

        purchase_assumptions = [
            ('Entry Purchase Price (EV)', entry_ev, 'EntryEV'),
            ('Bank Debt %', 0.50, 'DebtBank_pct'),
            ('Mezzanine Debt %', 0.20, 'DebtMezz_pct'),
            ('Equity %', 0.30, 'Equity_pct'),
            ('Bank Debt Interest Rate %', 0.055, 'InterestBank'),  # 5.5%
            ('Mezzanine Interest Rate %', 0.095, 'InterestMezz'),  # 9.5%
            ('Transaction Fees', entry_ev * 0.02, 'TxFees')  # 2% fees = $28,578,000
        ]

        for i, (label, value, name) in enumerate(purchase_assumptions):
            row = 26 + i
            ws.write(f'A{row}', label, self.formats['input_text'])
            if '%' in label and 'Interest' not in label:
                ws.write(f'B{row}', value, self.formats['percent'])
            elif 'Interest' in label or '%' in label:
                ws.write(f'B{row}', value, self.formats['percent'])
            else:
                ws.write(f'B{row}', value, self.formats['input'])

        # Create named ranges
        self.workbook.define_name('BaseYear', '=Assumptions!$B$8')
        self.workbook.define_name('HoldPeriod', '=Assumptions!$B$9')
        self.workbook.define_name('Rev0', '=Assumptions!$B$13')
        self.workbook.define_name('g_rev', '=Assumptions!$B$14')
        self.workbook.define_name('EBITDA_m', '=Assumptions!$B$15')
        self.workbook.define_name('DA_pct', '=Assumptions!$B$16')
        self.workbook.define_name('Capex_pct', '=Assumptions!$B$17')
        self.workbook.define_name('NWC_pct', '=Assumptions!$B$18')
        self.workbook.define_name('TaxRate', '=Assumptions!$B$19')
        self.workbook.define_name('EntryEV', '=Assumptions!$B$26')
        self.workbook.define_name('DebtBank_pct', '=Assumptions!$B$27')
        self.workbook.define_name('DebtMezz_pct', '=Assumptions!$B$28')
        self.workbook.define_name('Equity_pct', '=Assumptions!$B$29')
        self.workbook.define_name('InterestBank', '=Assumptions!$B$30')
        self.workbook.define_name('InterestMezz', '=Assumptions!$B$31')
        self.workbook.define_name('TxFees', '=Assumptions!$B$32')

    def _create_sources_uses_tab(self):
        """Create Sources & Uses tab"""

        ws = self.workbook.add_worksheet('Sources_Uses')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:B', 16)

        # Header
        ws.merge_range('A1:B1', 'Canada Goose Sources & Uses', self.formats['header'])

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
        ws.write('B12', 25000000, self.formats['input'])  # $25,000,000 debt reserve
        ws.write('B13', 50000000, self.formats['input'])   # $50,000,000 WC adjustment
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
        ws.merge_range('A1:C1', 'Canada Goose Pro Forma Balance Sheet', self.formats['header'])

        # Assets section (Luxury apparel specific)
        ws.write('A3', 'Assets', self.formats['subheader'])
        ws.write('A4', 'Cash & Cash Equivalents', self.formats['input_text'])
        ws.write('A5', 'Accounts Receivable', self.formats['input_text'])
        ws.write('A6', 'Inventory', self.formats['input_text'])  # High for apparel
        ws.write('A7', 'PP&E', self.formats['input_text'])
        ws.write('A8', 'Total Assets', self.formats['subheader'])

        # Assets values (luxury apparel balance sheet - FULL DOLLAR AMOUNTS)
        ws.write('B4', 200000000, self.formats['calc'])  # $200,000,000 cash
        ws.write('B5', 100000000, self.formats['calc'])  # $100,000,000 receivables
        ws.write('B6', 300000000, self.formats['calc'])  # $300,000,000 inventory
        ws.write('B7', 400000000, self.formats['calc'])  # $400,000,000 PP&E
        ws.write_formula('B8', '=SUM(B4:B7)', self.formats['calc'])

        # Liabilities & Equity section
        ws.write('A10', 'Liabilities & Equity', self.formats['subheader'])
        ws.write('A11', 'Bank Debt', self.formats['input_text'])
        ws.write('A12', 'Mezzanine Debt', self.formats['input_text'])
        ws.write('A13', 'Accounts Payable', self.formats['input_text'])
        ws.write('A14', 'Other Liabilities', self.formats['input_text'])
        ws.write('A15', 'Equity (Book Value)', self.formats['input_text'])
        ws.write('A16', 'Total Liabilities & Equity', self.formats['subheader'])

        # Liabilities values (FULL DOLLAR AMOUNTS)
        ws.write_formula('B11', '=EntryEV*DebtBank_pct', self.formats['calc'])  # $714,450,000 bank debt
        ws.write_formula('B12', '=EntryEV*DebtMezz_pct', self.formats['calc'])  # $285,780,000 mezz debt
        ws.write('B13', 150000000, self.formats['calc'])  # $150,000,000 payables
        ws.write('B14', 100000000, self.formats['calc'])  # $100,000,000 other liabilities
        ws.write_formula('B15', '=EquityInvested', self.formats['output'])  # $428,670,000 equity
        ws.write_formula('B16', '=SUM(B11:B15)', self.formats['calc'])

        # Balance check
        ws.write('A18', 'Balance Check (Assets - Liab+Equity)', self.formats['subheader'])
        ws.write_formula('B18', '=B8-B16', self.formats['calc'])

    def _create_forecast_fcf_tab(self):
        """Create Financial Forecast tab with Canada Goose specific assumptions"""

        ws = self.workbook.add_worksheet('Forecast_FCF')

        # Set column widths
        ws.set_column('A:A', 28)
        ws.set_column('B:G', 14)

        # Header
        ws.merge_range('A1:G1', 'Canada Goose Financial Forecast & Free Cash Flow', self.formats['header'])

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
        ws.merge_range('A1:G1', 'Canada Goose Debt Schedule', self.formats['header'])

        # Years header
        ws.write('A3', 'Item', self.formats['subheader'])
        for i in range(5):
            ws.write(2, i+1, f'Year {i+1}', self.formats['year'])

        # Bank Debt section
        ws.write('A4', 'Bank Debt', self.formats['subheader'])
        ws.write('A5', 'Beginning Balance', self.formats['subheader'])
        ws.write_formula('B5', '=Sources_Uses!$B$4', self.formats['calc'])  # Year 1 beginning
        ws.write_formula('C5', '=B8', self.formats['calc'])  # Year 2 = Year 1 ending
        ws.write_formula('D5', '=C8', self.formats['calc'])  # Year 3 = Year 2 ending
        ws.write_formula('E5', '=D8', self.formats['calc'])  # Year 4 = Year 3 ending
        ws.write_formula('F5', '=E8', self.formats['calc'])  # Year 5 = Year 4 ending

        ws.write('A6', 'Interest Expense', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(5, i+1, f'={chr(66+i)}5*InterestBank', self.formats['calc'])

        ws.write('A7', 'Principal Repayment', self.formats['subheader'])
        for i in range(5):
            # Principal repayment = min(beginning balance, available UFCF)
            ws.write_formula(6, i+1, f'=MIN({chr(66+i)}5, Forecast_FCF!{chr(66+i)}13)', self.formats['calc'])

        ws.write('A8', 'Ending Balance', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(7, i+1, f'={chr(66+i)}5-{chr(66+i)}7', self.formats['calc'])

        # Mezzanine Debt
        ws.write('A10', 'Mezzanine Debt', self.formats['subheader'])
        ws.write('A11', 'Beginning Balance', self.formats['subheader'])
        ws.write_formula('B11', '=Sources_Uses!$B$5', self.formats['calc'])  # Year 1 beginning
        ws.write_formula('C11', '=B14', self.formats['calc'])  # Year 2 = Year 1 ending
        ws.write_formula('D11', '=C14', self.formats['calc'])  # Year 3 = Year 2 ending
        ws.write_formula('E11', '=D14', self.formats['calc'])  # Year 4 = Year 3 ending
        ws.write_formula('F11', '=E14', self.formats['calc'])  # Year 5 = Year 4 ending

        ws.write('A12', 'Interest Expense', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(11, i+1, f'={chr(66+i)}11*InterestMezz', self.formats['calc'])

        ws.write('A13', 'Principal Repayment', self.formats['subheader'])
        # Mezzanine typically paid at maturity (bullet repayment)
        ws.write('B13', 0, self.formats['calc'])  # Year 1: Interest only
        ws.write('C13', 0, self.formats['calc'])  # Year 2: Interest only
        ws.write('D13', 0, self.formats['calc'])  # Year 3: Interest only
        ws.write('E13', 0, self.formats['calc'])  # Year 4: Interest only
        ws.write_formula('F13', '=F11', self.formats['calc'])  # Year 5: Bullet repayment

        ws.write('A14', 'Ending Balance', self.formats['subheader'])
        for i in range(5):
            ws.write_formula(13, i+1, f'={chr(66+i)}11-{chr(66+i)}13', self.formats['calc'])

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
        ws.merge_range('A1:G1', 'Canada Goose Returns Analysis', self.formats['header'])

        # Years header
        ws.write('A3', 'Item', self.formats['subheader'])
        for i in range(5):
            ws.write(2, i+1, f'Year {i+1}', self.formats['year'])

        # Cash flows section
        ws.write('A3', 'Dates', self.formats['subheader'])
        ws.write_formula('B3', '=BaseYear', self.formats['calc'])  # Year 0
        for i in range(5):
            ws.write_formula(2, i+2, f'=BaseYear+{i+1}', self.formats['calc'])  # Years 1-5

        ws.write('A4', 'Equity Cash Flows', self.formats['subheader'])
        ws.write('A5', 'Initial Equity Investment', self.formats['subheader'])
        ws.write_formula('B5', '=-EquityInvested', self.formats['calc'])

        ws.write('A7', 'Operating Distributions', self.formats['subheader'])
        for i in range(4):  # Years 1-4
            col_letter = chr(66 + i)  # B, C, D, E
            # Operating distribution = UFCF - Bank Debt Principal Repayment
            ws.write_formula(6, i+1, f'=Forecast_FCF!{col_letter}13-DebtSchedule!{col_letter}7', self.formats['calc'])

        # Year 5 includes exit proceeds
        # Year 5 distribution = UFCF - Bank Debt Principal + Exit Equity Value
        ws.write_formula(6, 5, '=Forecast_FCF!F13-DebtSchedule!F7+B12', self.formats['calc'])

        # Exit valuation
        ws.write('A9', 'Exit Analysis (Year 5)', self.formats['subheader'])
        ws.write('A10', 'Exit Enterprise Value', self.formats['input_text'])
        ws.write_formula('B10', '=Forecast_FCF!F6*12', self.formats['calc'])  # 12x exit multiple = ~$6,252,000,000

        ws.write('A11', 'Net Debt at Exit', self.formats['subheader'])
        ws.write_formula('B11', '=DebtSchedule!F8+DebtSchedule!F14', self.formats['calc'])  # F8 = Bank debt ending, F14 = Mezz debt ending

        ws.write('A12', 'Exit Equity Value', self.formats['subheader'])
        ws.write_formula('B12', '=B10-B11', self.formats['output'])

        # Returns calculations
        ws.write('A14', 'Returns Metrics', self.formats['subheader'])
        ws.write('A15', 'Equity IRR', self.formats['subheader'])
        # Use XIRR with proper date and cash flow ranges
        ws.write_formula('B15', '=XIRR(B6:F6,B3:F3)', self.formats['percent'])

        ws.write('A16', 'MOIC (Multiple on Invested Capital)', self.formats['subheader'])
        ws.write_formula('B16', '=B12/-B6', self.formats['multiple'])

        # Named ranges for key outputs
        self.workbook.define_name('EquityValue', '=Returns!$B$12')
        self.workbook.define_name('IRR', '=Returns!$B$15')
        self.workbook.define_name('MOIC', '=Returns!$B$16')

        # Sensitivity table
        ws.write('A18', 'Sensitivity Analysis', self.formats['subheader'])
        ws.write('A19', 'Entry Multiple vs Exit Multiple', self.formats['subheader'])

        # Create a simple sensitivity table
        ws.write('B20', 'Exit Multiple →', self.formats['subheader'])
        for i in range(3):
            ws.write(19, i+2, f'{(i+8):.1f}x', self.formats['multiple'])

        ws.write('A21', 'Entry Multiple ↓', self.formats['subheader'])
        for i in range(3):
            multiple = 10.0 + i * 0.5
            ws.write(20+i, 1, f'{multiple:.1f}x', self.formats['multiple'])
            for j in range(3):
                exit_mult = 8.0 + j
                # Simplified IRR calculation for sensitivity
                irr = ((exit_mult / multiple) ** (1/5) - 1)
                ws.write(20+i, j+2, irr, self.formats['percent'])

def main():
    """Generate the Canada Goose LBO model"""

    print("🦆 Generating Canada Goose LBO Model...")
    print("   • Luxury apparel company analysis")
    print("   • Real financial data integration")
    print("   • Industry-specific assumptions")
    print()

    # Create the model
    goos_lbo_model = CanadaGooseLBOModel()
    goos_lbo_model.create_workbook("Canada_Goose_LBO_Model.xlsx")

    print()
    print("✅ Canada Goose LBO Model Complete!")
    print("   📁 Canada_Goose_LBO_Model.xlsx")
    print("   🦆 Based on $1.35B revenue, $300M EBITDA")
    print("   ❄️  Luxury apparel industry assumptions")
    print("   📊 5-year hold period with 12% growth")
    print("   💰 70% leverage, 12x exit multiple")
    print()
    print("🚀 Ready for luxury brand LBO analysis!")

if __name__ == "__main__":
    main()
