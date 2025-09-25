#!/usr/bin/env python3
"""
Microsoft DCF Model Builder
Automatically puts DCF models in the "Microsoft" tab of the "DCF" Google Sheet.
"""

import sys
import subprocess

def install_and_import(package, pip_name=None):
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
]
for mod, pip_name in REQUIRED_MODULES:
    install_and_import(mod, pip_name)

import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from openpyxl import Workbook
from urllib.parse import urljoin

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

def write_to_microsoft_tab(company, years, revenue, ebitda, ebit, fcf, terminal_value, enterprise_value):
    """Write DCF model to the Microsoft tab in the DCF Google Sheet."""
    if not gspread or not Credentials:
        print("Google Sheets not available")
        return False
    
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or 'credentials/google_sheets_credentials.json'
    
    try:
        # Load credentials
        import json
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id', '')
        client_email = creds_data.get('client_email', '')
        
        print(f"Connecting to Google Sheets...")
        print(f"Project: {project_id}")
        print(f"Service Account: {client_email}")
        
        # Verify this is the correct project
        if project_id != 'modeo-466403':
            print(f"⚠️  WARNING: Using project {project_id}, but expected 'modeo-466403'")
            print("Make sure you're using the correct service account credentials file!")
        
        # Use only Sheets API scope
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        
        # Open the DCF sheet
        sh = gc.open("DCF")
        print("✅ Found 'DCF' sheet")
        
        # Get the Microsoft tab
        try:
            ws = sh.worksheet("Microsoft")
            print("✅ Found 'Microsoft' tab")
        except gspread.WorksheetNotFound:
            print("❌ 'Microsoft' tab not found in 'DCF' sheet")
            print("Please create a tab named 'Microsoft' in your DCF sheet")
            return False
        
        # Clear existing data and add new DCF model
        ws.clear()
        
        # Prepare data
        data = []
        data.append(["Company", company])
        data.append([])
        data.append(["Year"] + years)
        data.append(["Revenue"] + revenue)
        data.append(["EBITDA"] + ebitda)
        data.append(["EBIT"] + ebit)
        data.append(["FCF"] + fcf)
        data.append([])
        data.append(["Terminal Value", terminal_value])
        data.append(["Enterprise Value", enterprise_value])
        
        # Update the sheet
        ws.update('A1', data)
        
        # Try to format headers
        try:
            fmt = {"textFormat": {"bold": True}}
            ws.format("A3:Z3", fmt)
        except Exception:
            pass
        
        print(f"✅ DCF model written to Microsoft tab")
        print(f"📊 Sheet URL: {sh.url}")
        return True
        
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")
        return False

def build_microsoft_dcf_model(company_name, ticker=None):
    """Build DCF model for Microsoft and put it in the Microsoft tab."""
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
    
    # Write to Microsoft tab
    success = write_to_microsoft_tab(company_name, years, revenue_proj, ebitda_proj, ebit_proj, fcf_proj, terminal_value, enterprise_value)
    
    if success:
        # Print summary
        print(f"\n📊 DCF Model Summary for {company_name}")
        print(f"Base Revenue: ${base_revenue:,.0f}")
        print(f"Terminal Value: ${terminal_value:,.0f}")
        print(f"Enterprise Value: ${enterprise_value:,.0f}")
        print(f"Discount Rate: {DISCOUNT_RATE*100}%")
        print(f"Terminal Growth: {TERMINAL_GROWTH*100}%")
        print(f"✅ Model successfully written to Microsoft tab in DCF sheet!")
    else:
        print("❌ Failed to write to Google Sheets")

if __name__ == "__main__":
    print("🚀 Microsoft DCF Model Builder")
    print("=" * 40)
    print("This will put the DCF model in the 'Microsoft' tab of your 'DCF' Google Sheet")
    print()
    
    company_name = input("Enter company name: ").strip()
    ticker = input("Enter ticker symbol (optional): ").strip() or None
    
    build_microsoft_dcf_model(company_name, ticker) 