#!/usr/bin/env python3
"""IPO Model Builder
Creates a clean, presentation-ready IPO workbook in Google Sheets with:
1. IPO Assumptions
2. Sources & Uses
3. Pre/Post IPO Ownership
4. Proceeds Allocation
5. Valuation Summary
6. Sensitivity Table

Run:  python ipo_model.py "My IPO Sheet"
"""
import os
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    format_cell_range, CellFormat, Color, TextFormat, set_frozen
)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

YELLOW = Color(1, 0.95, 0.8)
BLUE_HEADER = Color(0.8, 0.88, 1)
GRAY_HEADER = Color(0.9, 0.9, 0.9)
GREEN_OUTPUT = Color(0.85, 0.93, 0.83)


def _bold(cf: CellFormat) -> CellFormat:  # convenience
    cf.textFormat = TextFormat(bold=True)
    return cf


def open_sheet(sheet_name: str):
    creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS") or "credentials/google_sheets_credentials.json"
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(creds)
    try:
        sh = gc.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        raise RuntimeError(
            f"Google Sheet '{sheet_name}' not found. Create it and share with your service-account email."
        )
    return sh


def get_ws(sh, title: str, rows: int = 200, cols: int = 20):
    try:
        ws = sh.worksheet(title)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=str(rows), cols=str(cols))
    return ws


# ---------------------------------------------------------------------
# Tab builders
# ---------------------------------------------------------------------

def build_assumptions_tab(ws):
    ws.update("A1", [["IPO Assumption", "Input"]])
    inputs = [
        ["Offering Price ($/sh)", 20],
        ["Primary Shares Offered", 10_000_000],
        ["Secondary Shares Offered", 2_000_000],
        ["Existing Shares Out.", 50_000_000],
        ["Greenshoe %", 0.15],
        ["Underwriting Discount %", 0.07],
        ["Other Fees ($)", 5_000_000],
        ["Founders %", 0.4],
        ["Investors %", 0.45],
        ["ESOP %", 0.15],
    ]
    ws.update("A2", inputs)
    # formatting
    format_cell_range(ws, "A1:B1", _bold(CellFormat(backgroundColor=GRAY_HEADER)))
    format_cell_range(ws, "A2:B20", CellFormat(backgroundColor=YELLOW))
    set_frozen(ws, rows=1, cols=1)


def build_sources_uses(ws):
    ws.update("A1", [["Sources / Uses", "Amount"]])
    rows = [
        ["Primary Proceeds", "='IPO Assumptions'!B2*'IPO Assumptions'!B1"],
        ["Secondary Proceeds", "='IPO Assumptions'!B3*'IPO Assumptions'!B1"],
        ["Greenshoe Proceeds", "='IPO Assumptions'!B5*'IPO Assumptions'!B2*'IPO Assumptions'!B1"],
        ["Total Gross Proceeds", "=SUM(B2:B4)"],
        ["Underwriter Discount", "=B4*'IPO Assumptions'!B6"],
        ["Other Fees", "='IPO Assumptions'!B7"],
        ["Net Proceeds to Company", "=B4-B5-B6"],
    ]
    ws.update("A2", rows)
    format_cell_range(ws, "A1:B1", _bold(CellFormat(backgroundColor=GRAY_HEADER)))


def build_ownership_tab(ws):
    ws.update("A1", [["Stakeholder", "Pre-IPO Sh.", "Sold", "Post-IPO Sh.", "% Pre", "% Post", "Dilution %"]])
    rows = [
        ["Founders", "='IPO Assumptions'!B8*'IPO Assumptions'!B4", 0, "=B2-C2", "=B2/SUM($B$2:$B$4)", "=D2/SUM($D$2:$D$4)", "=1-E2/F2"],
        ["Investors", "='IPO Assumptions'!B9*'IPO Assumptions'!B4", 0, "=B3-C3", "=B3/SUM($B$2:$B$4)", "=D3/SUM($D$2:$D$4)", "=1-E3/F3"],
        ["ESOP", "='IPO Assumptions'!B10*'IPO Assumptions'!B4", 0, "=B4-C4", "=B4/SUM($B$2:$B$4)", "=D4/SUM($D$2:$D$4)", "=1-E4/F4"],
        ["New Investors", 0, "='IPO Assumptions'!B2+'IPO Assumptions'!B3", "=C5", 0, "=D5/SUM($D$2:$D$5)", "=1-E5/F5"],
    ]
    ws.update("A2", rows)
    format_cell_range(ws, "A1:G1", _bold(CellFormat(backgroundColor=GRAY_HEADER)))


def build_proceeds_alloc(ws):
    ws.update("A1", [["Use of Proceeds", "Amount"]])
    rows = [
        ["Cash to Balance Sheet", "='Sources & Uses'!B7"],
        ["Debt Repayment", 0],
        ["Growth CapEx", 0],
    ]
    ws.update("A2", rows)
    format_cell_range(ws, "A1:B1", _bold(CellFormat(backgroundColor=GRAY_HEADER)))
    format_cell_range(ws, "B2", CellFormat(backgroundColor=GREEN_OUTPUT))


def build_valuation(ws):
    ws.update("A1", [["Valuation Metric", "Value"]])
    rows = [
        ["Post-Money Shares", "='IPO Assumptions'!B4 + 'IPO Assumptions'!B2 + 'IPO Assumptions'!B3 + ('IPO Assumptions'!B5*'IPO Assumptions'!B2)"],
        ["IPO Price", "='IPO Assumptions'!B1"],
        ["Implied Market Cap", "=B2*B3"],
    ]
    ws.update("A2", rows)
    format_cell_range(ws, "A1:B1", _bold(CellFormat(backgroundColor=GRAY_HEADER)))
    format_cell_range(ws, "B4", CellFormat(backgroundColor=GREEN_OUTPUT))


def build_sensitivity(ws):
    prices = [i for i in range(15, 31, 3)]  # $15 – $30
    offers = [8_000_000, 10_000_000, 12_000_000]
    ws.update("B1", [[p for p in prices]])
    data = []
    for shs in offers:
        row = [shs]
        for p in prices:
            row.append(p * shs)
        data.append(row)
    ws.update("A2", data)
    format_cell_range(ws, f"A1:{chr(65+len(prices))}1", _bold(CellFormat(backgroundColor=GRAY_HEADER)))


# ---------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------

def build_ipo_model(sheet_name="IPO Model Demo"):
    sh = open_sheet(sheet_name)
    build_assumptions_tab(get_ws(sh, "IPO Assumptions"))
    build_sources_uses(get_ws(sh, "Sources & Uses"))
    build_ownership_tab(get_ws(sh, "Pre/Post Ownership"))
    build_proceeds_alloc(get_ws(sh, "Proceeds Allocation"))
    build_valuation(get_ws(sh, "Valuation Summary"))
    build_sensitivity(get_ws(sh, "Sensitivity"))
    print(f"✅ IPO model created / updated in sheet: {sh.url}")


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "IPO Model Demo"
    build_ipo_model(name) 