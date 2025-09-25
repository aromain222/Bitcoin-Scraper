# WARNING: Auto-installing packages at runtime is not best practice for production code.
# This is for user convenience in a development environment only.
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

# List of (import_name, pip_name) pairs
REQUIRED_MODULES = [
    ("openai", "openai"),
    ("pandas", "pandas"),
    ("openpyxl", "openpyxl"),
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
    ("dotenv", "python-dotenv"),
    ("tiktoken", "tiktoken"),
    ("yfinance", "yfinance"),
    ("tldextract", "tldextract"),
    ("lxml", "lxml"),
    ("gspread", "gspread"),
    ("google.auth", "google-auth"),
    ("google_auth_oauthlib", "google-auth-oauthlib"),
    ("google_auth_httplib2", "google-auth-httplib2"),
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
from dotenv import load_dotenv
from urllib.parse import urljoin

# Optional imports with error handling
try:
    import openai
except ImportError:
    openai = None
try:
    import yfinance as yf
except ImportError:
    yf = None
try:
    import tldextract
except ImportError:
    tldextract = None
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# --- CONFIG ---
YEARS = 5
DISCOUNT_RATE = 0.10  # 10% WACC for MVP
TERMINAL_GROWTH = 0.03  # 3% perpetual growth

# --- DCF FIELDS ---
DCF_FIELDS = [
    'Revenue', 'EBITDA', 'EBIT', 'Taxes', 'NOPAT', 'Depreciation', 'CapEx', 'Δ Working Cap', 'FCF'
]

# --- yfinance Extraction for Public Companies ---
def get_yfinance_financials(ticker):
    if not yf:
        print("yfinance is not installed. Please install it to use this feature.")
        return {}
    try:
        ticker_obj = yf.Ticker(ticker)
        fin = ticker_obj.financials.T  # DataFrame: index=years, columns=fields
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

# --- LLM Extraction Fallback ---
def extract_financials_with_llm(company_name_or_text):
    if not openai or not OPENAI_API_KEY:
        print("OpenAI is not installed or API key is missing.")
        return {}
    prompt = f"""
Extract the most recent annual financials for {company_name_or_text}. Return a JSON object with keys: Revenue, EBITDA, EBIT, Net Income, Depreciation, CapEx, Working Capital. Use 'Unknown' if not found.
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
        return json.loads(content)
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        return {}

# --- Simple Web Crawler ---
def crawl_company_website(base_url, max_depth=2, max_pages=20):
    if not tldextract:
        print("tldextract is not installed. Please install it to use this feature.")
        return set()
    visited = set()
    to_visit = [(base_url, 0)]
    relevant_urls = set()
    keywords = ['investor', 'financial', 'annual', 'report', 'press', 'news', 'sec', 'filing', 'earnings']
    domain = tldextract.extract(base_url).registered_domain
    while to_visit and len(visited) < max_pages:
        url, depth = to_visit.pop(0)
        if url in visited or depth > max_depth:
            continue
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                continue
            visited.add(url)
            soup = BeautifulSoup(resp.text, 'lxml')
            if any(kw in url.lower() for kw in keywords) or any(kw in soup.get_text().lower() for kw in keywords):
                relevant_urls.add(url)
            for link in soup.find_all('a', href=True):
                # Only use .get() if link is a Tag (not NavigableString)
                if not isinstance(link, Tag):
                    continue
                href = link.get('href', None)
                if not isinstance(href, str):
                    continue
                href_str = str(href)
                if not href_str.startswith('http'):
                    href_str = str(urljoin(url, href_str))
                link_domain = tldextract.extract(href_str).registered_domain
                if link_domain == domain and href_str not in visited:
                    to_visit.append((href_str, depth + 1))
        except Exception:
            continue
    return relevant_urls

# --- Simple Web Scraper for Financials ---
def scrape_financials_from_url(url):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return {}
        soup = BeautifulSoup(resp.text, 'lxml')
        text = soup.get_text(" ", strip=True)
        patterns = {
            'Revenue': r'(?:revenue|total sales)[^\$\d]{0,20}\$?([\d,.]+) ?(million|billion|bn|m|b)?',
            'EBITDA': r'(?:ebitda)[^\$\d]{0,20}\$?([\d,.]+) ?(million|billion|bn|m|b)?',
            'EBIT': r'(?:ebit|operating income)[^\$\d]{0,20}\$?([\d,.]+) ?(million|billion|bn|m|b)?',
        }
        found = {}
        for field, pat in patterns.items():
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).replace(',', '')
                mult = m.group(2) or ''
                try:
                    val = float(val)
                    if mult.lower() in ['billion', 'bn', 'b']:
                        val *= 1e9
                    elif mult.lower() in ['million', 'm']:
                        val *= 1e6
                    found[field] = val
                except Exception:
                    continue
        if len(found) < 2:
            llm_fields = extract_financials_with_llm(text[:4000])
            found.update({k: v for k, v in llm_fields.items() if k not in found})
        return found
    except Exception:
        return {}

# --- DCF Calculation ---
def project_financials(base, growth=0.08, years=YEARS):
    return [round(base * ((1 + growth) ** i), 2) for i in range(years)]

def calculate_fcf(revenue, ebitda, ebit, taxes, depreciation, capex, delta_wc):
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
    return last_fcf * (1 + growth) / (discount_rate - growth)

def discount_cash_flows(fcfs, terminal_value, discount_rate=DISCOUNT_RATE):
    discounted = [fcf / ((1 + discount_rate) ** (i + 1)) for i, fcf in enumerate(fcfs)]
    tv_discounted = terminal_value / ((1 + discount_rate) ** len(fcfs))
    return discounted, tv_discounted

# --- Google Sheets Helper ---
def get_gsheet(sheet_name="DCF Model", worksheet_name="DCF", creds_path=None):
    if not gspread or not Credentials:
        print("gspread or google-auth is not installed. Please install them to use Google Sheets output.")
        return None, None
    creds_path = creds_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS') or 'credentials/google_sheets_credentials.json'
    
    # Load credentials and verify project ID
    try:
        import json
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
        project_id = creds_data.get('project_id', '')
        print(f"Using Google Cloud Project: {project_id}")
        
        # Verify this is your project
        if project_id != 'ecstatic-magpie-466323-s3':
            print(f"WARNING: Using project {project_id}, but expected 'ecstatic-magpie-466323-s3'")
            print("Make sure you're using the correct service account credentials file!")
    except Exception as e:
        print(f"Error reading credentials file: {e}")
        return None, None
    
    # Use only Sheets API scope to avoid Drive API issues
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(creds)
    
    try:
        # Try to open existing sheet first
        sh = gc.open(sheet_name)
        print(f"Found existing sheet: {sheet_name}")
    except gspread.SpreadsheetNotFound:
        print(f"Sheet '{sheet_name}' not found.")
        print("Please create a Google Sheet manually and share it with your service account email.")
        print("Service account email:", creds_data.get('client_email', 'Unknown'))
        print("Then run the script again.")
        return None, None
    except Exception as e:
        print(f"Error accessing Google Sheets: {e}")
        print("Make sure you've shared the sheet with your service account email.")
        return None, None
    
    try:
        ws = sh.worksheet(worksheet_name)
        print(f"Found existing worksheet: {worksheet_name}")
    except gspread.WorksheetNotFound:
        print(f"Worksheet '{worksheet_name}' not found in sheet '{sheet_name}'.")
        print("Please create a worksheet with that name or the script will use the first available worksheet.")
        try:
            ws = sh.get_worksheet(0)  # Get first worksheet
            if ws:
                print(f"Using first available worksheet: {ws.title}")
            else:
                print("No worksheets found in the sheet.")
                return None, None
        except Exception:
            print("Could not access any worksheets.")
            return None, None
    
    return sh, ws

# --- Google Sheets Output ---
def write_to_gsheet(company, years, revenue, ebitda, ebit, fcf, terminal_value, enterprise_value, sheet_name="DCF Model", worksheet_name="DCF"):
    sh, ws = get_gsheet(sheet_name, worksheet_name)
    if not ws:
        print("Google Sheets worksheet not available. Skipping Google Sheets output.")
        return
    ws.clear()
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
    ws.update('A1', data)
    try:
        fmt = {"textFormat": {"bold": True}}
        ws.format("A3:Z3", fmt)
    except Exception:
        pass
    # Only print sh.url if sh is not None and has attribute 'url'
    if sh and hasattr(sh, 'url'):
        print(f"Google Sheet URL: {sh.url}")
    else:
        print("Google Sheet created, but URL not available.")

# --- Excel Output ---
def write_to_excel(company, years, revenue, ebitda, ebit, fcf, terminal_value, enterprise_value, filename):
    wb = Workbook()
    ws = wb.active
    # Only set title and append if ws is not None and has the required methods
    if ws and hasattr(ws, 'title') and hasattr(ws, 'append'):
        ws.title = "DCF Model"
        ws.append(["Company", company])
        ws.append([])
        ws.append(["Year"] + years)
        ws.append(["Revenue"] + revenue)
        ws.append(["EBITDA"] + ebitda)
        ws.append(["EBIT"] + ebit)
        ws.append(["FCF"] + fcf)
        ws.append([])
        ws.append(["Terminal Value", terminal_value])
        ws.append(["Enterprise Value", enterprise_value])
        wb.save(filename)
        print(f"Saved DCF model to {filename}")
    else:
        print("Excel worksheet not available. Skipping Excel output.")

# --- Main Pipeline (updated) ---
def build_dcf_model(company_name, ticker=None, website=None, output="excel", sheet_name="DCF Model", worksheet_name="DCF"):
    print(f"Building DCF model for {company_name}")
    data = get_yfinance_financials(ticker) if ticker else {}
    if not data or not data.get('Revenue'):
        print("Falling back to LLM extraction...")
        data = extract_financials_with_llm(company_name)
    if (not data or not data.get('Revenue')) and website:
        print("Trying web crawler and scraper...")
        urls = crawl_company_website(website)
        for url in urls:
            scraped = scrape_financials_from_url(url)
            if scraped.get('Revenue'):
                data.update(scraped)
                break
    base_revenue = float(str(data.get('Revenue', [0])[0] if isinstance(data.get('Revenue'), list) else data.get('Revenue', 0)).replace(',', '').replace('$', '')) if data.get('Revenue') else 1000000
    revenue_proj = project_financials(base_revenue)
    ebitda_proj = [r * 0.25 for r in revenue_proj]
    ebit_proj = [r * 0.15 for r in revenue_proj]
    fcf_proj = calculate_fcf(revenue_proj, ebitda_proj, ebit_proj, None, None, None, None)
    terminal_value = calculate_terminal_value(fcf_proj[-1])
    discounted_fcfs, discounted_tv = discount_cash_flows(fcf_proj, terminal_value)
    enterprise_value = round(sum(discounted_fcfs) + discounted_tv, 2)
    years = [datetime.now().year + i for i in range(YEARS)]
    if output == "excel":
        write_to_excel(company_name, years, revenue_proj, ebitda_proj, ebit_proj, fcf_proj, terminal_value, enterprise_value, f"dcf_{company_name}.xlsx")
    elif output == "gsheet":
        write_to_gsheet(company_name, years, revenue_proj, ebitda_proj, ebit_proj, fcf_proj, terminal_value, enterprise_value, sheet_name, worksheet_name)
    else:
        print("Unknown output type. Use 'excel' or 'gsheet'.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Interactive DCF Model Builder")
        print("=" * 50)
        company_name = input("Enter company name: ").strip()
        ticker = input("Enter ticker symbol (leave blank if private): ").strip() or None
        website = input("Enter company website (optional): ").strip() or None
        
        # Default to Google Sheets with your specific setup
        output = input("Output type (gsheet/excel) [gsheet]: ").strip() or "gsheet"
        
        # Default to your existing sheet and tab
        sheet_name = input("Google Sheet name [DCF]: ").strip() or "DCF"
        worksheet_name = input("Worksheet/tab name [Microsoft]: ").strip() or "Microsoft"
        
        build_dcf_model(company_name, ticker, website, output, sheet_name, worksheet_name)
    else:
        build_dcf_model(
            sys.argv[1],
            sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else None,
            sys.argv[4] if len(sys.argv) > 4 else "gsheet",
            sys.argv[5] if len(sys.argv) > 5 else "DCF",
            sys.argv[6] if len(sys.argv) > 6 else "Microsoft"
        ) 