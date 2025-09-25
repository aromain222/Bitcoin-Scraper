#!/usr/bin/env python3
"""
Google Sheets DCF Model Builder
Uses simplified authentication approach
"""

import sys
import subprocess
import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from openpyxl import Workbook
from urllib.parse import urljoin

def install_and_import(package, pip_name=None):
    """Auto-install missing packages."""
    pip_name = pip_name or package
    try:
        __import__(package)
    except ImportError:
        print(f"Installing missing package: {pip_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        __import__(package)

# Install required packages
REQUIRED_MODULES = [
    ("pandas", "pandas"),
    ("openpyxl", "openpyxl"),
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
    ("yfinance", "yfinance"),
    ("openai", "openai"),
    ("gspread", "gspread"),
    ("google.auth", "google-auth"),
    ("dotenv", "python-dotenv"),
]

for mod, pip_name in REQUIRED_MODULES:
    install_and_import(mod, pip_name)

# Optional imports
try:
    import openai
except ImportError:
    openai = None
try:
    import yfinance as yf
except ImportError:
    yf = None
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Configuration
YEARS = 5
DISCOUNT_RATE = 0.10
TERMINAL_GROWTH = 0.03

def get_yfinance_financials(ticker):
    """Get financial data from yfinance for public companies."""
    if not yf:
        print("yfinance not available")
        return {}
    try:
        ticker_obj = yf.Ticker(ticker)
        fin = ticker_obj.financials.T
        years = fin.index[-YEARS:]
        data = {}
        if 'Total Revenue' in fin.columns:
            data['Revenue'] = [float(fin.loc[y, 'Total Revenue']) for y in years]
        if 'EBITDA' in fin.columns:
            data['EBITDA'] = [float(fin.loc[y, 'EBITDA']) for y in years]
        if 'Operating Income' in fin.columns:
            data['EBIT'] = [float(fin.loc[y, 'Operating Income']) for y in years]
        return data
    except Exception as e:
        print(f"yfinance extraction failed: {e}")
        return {}

def extract_financials_with_llm(company_name):
    """Extract financials using OpenAI."""
    if not openai or not OPENAI_API_KEY:
        print("OpenAI not available")
        return {}
    prompt = f"""
Extract the most recent annual financials for {company_name}. Return a JSON object with keys: Revenue, EBITDA, EBIT, Net Income, Depreciation, CapEx, Working Capital. Use 'Unknown' if not found.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=600,
        )
        import json
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
        else:
            return {}
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        return {}

def project_financials(base, growth=0.08, years=YEARS):
    """Project financials into the future."""
    return [round(base * ((1 + growth) ** i), 2) for i in range(years)]

def calculate_fcf(revenue, ebitda, ebit, taxes, depreciation, capex, delta_wc):
    """Calculate Free Cash Flow."""
    tax_rate = 0.25
    fcf = []
    for i in range(len(revenue)):
        EBIT = ebit[i] if ebit else revenue[i] * 0.15
        Taxes = EBIT * tax_rate
        Dep = depreciation[i] if depreciation else revenue[i] * 0.05
        Cap = capex[i] if capex else revenue[i] * 0.06
        DWC = delta_wc[i] if delta_wc else revenue[i] * 0.02
        fcf.append(round(EBIT - Taxes + Dep - Cap - DWC, 2))
    return fcf

def calculate_terminal_value(last_fcf, discount_rate=DISCOUNT_RATE, growth=TERMINAL_GROWTH):
    """Calculate terminal value."""
    return last_fcf * (1 + growth) / (discount_rate - growth)

def discount_cash_flows(fcfs, terminal_value, discount_rate=DISCOUNT_RATE):
    """Discount cash flows to present value."""
    discounted = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(fcfs)]
    tv_discounted = terminal_value / ((1 + discount_rate) ** len(fcfs))
    return discounted, tv_discounted

def setup_google_sheets():
    """Setup Google Sheets connection with better error handling."""
    if not gspread or not Credentials:
        print("❌ Google Sheets libraries not available")
        return None, None
    
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or 'credentials/google_sheets_credentials.json'
    
    try:
        # Load credentials
        import json
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id', '')
        client_email = creds_data.get('client_email', '')
        
        print(f"📋 Using project: {project_id}")
        print(f"📋 Service account: {client_email}")
        
        # Try different scope combinations
        scopes_options = [
            ['https://www.googleapis.com/auth/spreadsheets'],
            ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'],
            ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file'],
        ]
        
        for scopes in scopes_options:
            try:
                print(f"🔄 Trying scopes: {scopes}")
                creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
                gc = gspread.authorize(creds)
                
                # Test the connection
                gc.list_spreadsheet_files()
                print("✅ Google Sheets connection successful!")
                return gc, client_email
                
            except Exception as e:
                print(f"❌ Failed with scopes {scopes}: {e}")
                continue
        
        print("❌ All authentication attempts failed")
        return None, None
        
    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        return None, None

# --- Helper ---------------------------------------------------------------

# Simple helper to convert a zero-based column index to its corresponding
# Google Sheets column letter (0 -> A, 1 -> B, ... 25 -> Z, 26 -> AA, etc.).
def _col_letter(idx: int) -> str:
    idx += 1  # Switch to 1-based for calculation
    letters = ""
    while idx:
        idx, remainder = divmod(idx - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


# -------------------------------------------------------------------------

# We now include assumption inputs (growth rate, discount rate, etc.) and write
# formulas instead of hard-coded projections, so the sheet updates
# automatically if the user edits the assumptions.

def write_to_google_sheets(
    company,
    base_revenue,
    growth_rate,
    discount_rate,
    terminal_growth,
    years,
    revenue,
    ebitda,
    ebit,
    fcf,
    terminal_value,
    enterprise_value,
    sheet_name="DCF",
    worksheet_name="Microsoft",
):
    """Write DCF model to Google Sheets."""
    gc, client_email = setup_google_sheets()
    if not gc:
        print("❌ Could not connect to Google Sheets")
        return False
    
    try:
        # Try to open existing sheet
        try:
            sh = gc.open(sheet_name)
            print(f"✅ Found existing sheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            print(f"❌ Sheet '{sheet_name}' not found")
            print(f"Please create a Google Sheet named '{sheet_name}' and share it with:")
            print(f"   {client_email}")
            print("Then run the script again.")
            return False
        
        # Try to access worksheet
        try:
            ws = sh.worksheet(worksheet_name)
            print(f"✅ Found worksheet: {worksheet_name}")
        except gspread.WorksheetNotFound:
            print(f"❌ Worksheet '{worksheet_name}' not found")
            print(f"Please create a worksheet named '{worksheet_name}' in your '{sheet_name}' sheet")
            return False
        
        # Clear existing content first
        ws.clear()

        # ---------------- Header / Assumptions ----------------------
        data = []
        data.append(["Company", company])                                   # Row 1
        data.append(["Growth Rate", growth_rate])                           # Row 2
        data.append(["Discount Rate", discount_rate])                       # Row 3
        data.append(["Terminal Growth", terminal_growth])                   # Row 4
        data.append(["Base Revenue", base_revenue])                         # Row 5
        data.append([])                                                      # Row 6 (empty)

        # ---------------- Years Row --------------------------------
        data.append(["Year"] + years)                                        # Row 7

        # The row index of the first revenue value in Google Sheets (1-based).
        # We need this to build formulas that reference the correct cells.
        base_row = 5  # "Base Revenue" value is on row 5 (indexing starts at 1)
        growth_row = 2  # Growth Rate is on row 2
        revenue_row_number = 8  # after appending Year row, revenue row will be row 8

        # Build revenue formulas so that each period references the previous cell.
        revenue_row = ["Revenue"]
        for i in range(len(years)):
            col_letter = _col_letter(i + 1)  # revenue values start in column B
            if i == 0:
                # First projected year references base revenue directly
                formula = f"=$B${base_row}*(1+$B${growth_row})"
            else:
                prev_col = _col_letter(i)  # previous column letter
                formula = f"={prev_col}{revenue_row_number}*(1+$B${growth_row})"
            revenue_row.append(formula)

        # EBITDA = Revenue * 0.25
        ebitda_row = ["EBITDA"]
        # EBIT = Revenue * 0.15
        ebit_row = ["EBIT"]
        # FCF = Revenue * 0.0825 (simple approximation consistent with python)
        fcf_row = ["FCF"]

        for i in range(len(years)):
            col_letter = _col_letter(i + 1)
            ebitda_row.append(f"={col_letter}{revenue_row_number}*0.25")
            ebit_row.append(f"={col_letter}{revenue_row_number}*0.15")
            fcf_row.append(f"={col_letter}{revenue_row_number}*0.0825")

        data.append(revenue_row)
        data.append(ebitda_row)
        data.append(ebit_row)
        data.append(fcf_row)

        # Empty spacer row
        data.append([])

        # We still write the originally computed Terminal & Enterprise values so
        # users have a reference, but these are optional.
        data.append(["Terminal Value (static)", terminal_value])
        data.append(["Enterprise Value (static)", enterprise_value])

        # Push the batch update starting from A1
        ws.update("A1", data, value_input_option="USER_ENTERED")
        
        # Try formatting
        try:
            fmt = {"textFormat": {"bold": True}}
            ws.format("A3:Z3", fmt)
        except Exception:
            pass
        
        print("✅ Dynamic DCF model written to Google Sheets. Editing the growth rate (cell B2) will now recalculate projections automatically!")
        print(f"📊 Sheet URL: {sh.url}")
        return True
        
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")
        print("This might be due to:")
        print("1. Google Sheets API not enabled")
        print("2. Insufficient permissions")
        print("3. Sheet not shared with service account")
        return False

# -------------------------------------------------------------------------
#                          Main Build Function
# -------------------------------------------------------------------------

def build_dcf_model(company_name, ticker=None):
    """Build DCF model for a company."""
    print(f"Building DCF model for {company_name}")
    
    # Get financial data
    data = get_yfinance_financials(ticker) if ticker else {}
    if not data or not data.get('Revenue'):
        print("Falling back to LLM extraction...")
        data = extract_financials_with_llm(company_name)
    
    # Use default values if no data found
    if not data or not data.get('Revenue'):
        print("Using default financial assumptions...")
        base_revenue = 1000000  # $1M default
    else:
        base_revenue = float(str(data.get('Revenue', [0])[0] if isinstance(data.get('Revenue'), list) else data.get('Revenue', 0)).replace(',', '').replace('$', ''))
    
    # Project financials
    revenue_proj = project_financials(base_revenue)
    ebitda_proj = [r * 0.25 for r in revenue_proj]
    ebit_proj = [r * 0.15 for r in revenue_proj]
    fcf_proj = calculate_fcf(revenue_proj, ebitda_proj, ebit_proj, None, None, None, None)
    
    # Calculate terminal value and enterprise value
    terminal_value = calculate_terminal_value(fcf_proj[-1])
    discounted_fcfs, discounted_tv = discount_cash_flows(fcf_proj, terminal_value)
    enterprise_value = round(sum(discounted_fcfs) + discounted_tv, 2)
    
    # Create years
    years = [datetime.now().year + i for i in range(YEARS)]
    
    # Write to Google Sheets (dynamic version)
    success = write_to_google_sheets(
        company_name,
        base_revenue,
        growth_rate=0.08,
        discount_rate=DISCOUNT_RATE,
        terminal_growth=TERMINAL_GROWTH,
        years=years,
        revenue=revenue_proj,
        ebitda=ebitda_proj,
        ebit=ebit_proj,
        fcf=fcf_proj,
        terminal_value=terminal_value,
        enterprise_value=enterprise_value,
    )
    
    if success:
        # Print summary
        print(f"\n📊 DCF Model Summary for {company_name}")
        print(f"Base Revenue: ${base_revenue:,.0f}")
        print(f"Terminal Value: ${terminal_value:,.0f}")
        print(f"Enterprise Value: ${enterprise_value:,.0f}")
        print(f"Discount Rate: {DISCOUNT_RATE*100}%")
        print(f"Terminal Growth: {TERMINAL_GROWTH*100}%")
        print(f"✅ Model successfully written to Google Sheets with formatted numbers!")
    else:
        print("❌ Failed to write to Google Sheets")
        print("Consider using the Excel version: python simple_unified_dcf.py")

def main_menu():
    """Main interactive menu."""
    print("🚀 Google Sheets DCF Model Builder")
    print("=" * 50)
    print("This tool creates DCF models in Google Sheets")
    print("Make sure you have:")
    print("1. Google Sheets API enabled")
    print("2. A sheet named 'DCF' with 'Microsoft' tab")
    print("3. Sheet shared with service account")
    print()
    
    # Get user inputs
    company_name = input("Enter company name: ").strip()
    ticker = input("Enter ticker symbol (optional): ").strip() or None
    
    # Build the model
    build_dcf_model(company_name, ticker)

if __name__ == "__main__":
    main_menu() 