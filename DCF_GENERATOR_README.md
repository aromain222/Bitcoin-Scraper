# 🚀 Company DCF Generator

Generate professional banker-style DCF models for any public company with real financial data.

## 🎯 What It Does

- **Input**: Company ticker symbol (e.g., AAPL, MSFT, TSLA)
- **Output**: Complete Excel DCF model with 5 professional tabs
- **Data**: Automatically fetches real financial data using yfinance
- **Customization**: Populates DCF assumptions based on company-specific data

## 📊 Generated Excel File Includes

### 5 Professional Tabs:
1. **Assumptions & Drivers** - All input parameters (revenue, growth, margins, WACC, etc.)
2. **Forecast & FCF** - Revenue projections and cash flow calculations
3. **DCF Valuation** - Discounting and terminal value calculations
4. **Sensitivity Analysis** - 2-way sensitivity tables (WACC vs growth, WACC vs exit multiple)
5. **Summary** - Key outputs and mini time-series

### Professional Formatting:
- ✅ **Color Coding**: Blue inputs, Green outputs, Black calculations
- ✅ **Number Formats**: Currency ($MM), Percentages, Multiples
- ✅ **Borders**: Thin borders for tables, thick for key outputs
- ✅ **Layout**: Years horizontally, proper alignment
- ✅ **Print Setup**: Landscape, fit to 1 page wide

## 🚀 Quick Start

### Method 1: Command Line
```bash
# Generate DCF for Apple
python quick_dcf_generator.py AAPL

# Generate DCF for Microsoft
python quick_dcf_generator.py MSFT

# Generate DCF for Tesla
python quick_dcf_generator.py TSLA
```

### Method 2: Interactive Demo
```bash
python dcf_demo.py
```
Then enter tickers interactively.

## 📈 Example Output

### Apple (AAPL) Results:
- **Revenue**: $391B
- **EBITDA Margin**: 34.4%
- **Beta**: 1.17
- **Shares Outstanding**: 14.8B
- **Net Debt**: $76.7B
- **WACC**: 8.5%

### Microsoft (MSFT) Results:
- **Revenue**: $282B
- **EBITDA Margin**: 56.9%
- **Beta**: 1.05
- **Shares Outstanding**: 7.4B
- **Net Debt**: $30.3B
- **WACC**: 8.1%

### Tesla (TSLA) Results:
- **Revenue**: $97.7B
- **EBITDA Margin**: 15.1%
- **Beta**: 2.00 (high risk)
- **Shares Outstanding**: 3.2B
- **Net Debt**: $0B
- **WACC**: 11.5%

## 🧮 How It Works

1. **Data Fetching**: Uses yfinance to get real financial statements
2. **Assumption Calculation**: Derives DCF inputs from company data:
   - Revenue from income statement
   - Beta from company info
   - EBITDA margin from financial ratios
   - Shares outstanding and debt levels
3. **Model Population**: Inserts real data into the expert DCF template
4. **Excel Generation**: Creates formatted Excel file with all calculations

## 📁 Files Generated

```
DCF_AAPL_20250903_220118.xlsx
DCF_MSFT_20250903_220127.xlsx
DCF_TSLA_20250903_220145.xlsx
```

## 🛠️ Technical Details

### Dependencies:
- `yfinance` - For financial data retrieval
- `openpyxl` - For Excel file generation
- `pandas` - For data processing
- `datetime` - For timestamps

### Key Functions:
- `get_company_data(ticker)` - Fetches financial data
- `calculate_dcf_inputs(data)` - Derives DCF assumptions
- `generate_dcf_for_ticker(ticker)` - Main generation function

### Data Sources:
- Company info, beta, shares outstanding
- Income statement (revenue, EBITDA, net income)
- Balance sheet (debt, cash)
- Cash flow statement (depreciation, capex)

## 🎨 DCF Assumptions Used

- **Forecast Horizon**: 6 years
- **Growth Rate**: 8% (or company-specific if available)
- **Risk-free Rate**: 4.5%
- **Equity Risk Premium**: 6%
- **Tax Rate**: 25%
- **Terminal Growth**: 2.5%
- **Exit Multiple**: 10x EV/EBITDA

## 📋 Usage Examples

```python
from quick_dcf_generator import generate_dcf_for_ticker

# Generate DCF for NVIDIA
filename = generate_dcf_for_ticker("NVDA")
print(f"DCF generated: {filename}")

# Generate DCF for Amazon
filename = generate_dcf_for_ticker("AMZN")
print(f"DCF generated: {filename}")
```

## 🔧 Customization

You can modify assumptions in the `calculate_dcf_inputs()` function:

```python
# Change default growth rate
inputs['g_base'] = 0.10  # 10% instead of 8%

# Change risk-free rate
inputs['Rf'] = 0.05  # 5% instead of 4.5%

# Change terminal growth
inputs['g_term'] = 0.03  # 3% instead of 2.5%
```

## 📊 Output Analysis

Each generated Excel file contains:

### Key Valuation Outputs:
- **Enterprise Value (EV)**
- **Equity Value**
- **Implied Share Price**
- **WACC Calculation**
- **Terminal Value**

### Sensitivity Analysis:
- Price per Share vs WACC & Growth Rate
- Equity Value vs WACC & Exit Multiple
- Base case highlighting

### Quality Checks:
- WACC vs Cost of Equity validation
- Terminal growth rate checks
- EBITDA margin reasonableness flags

## 🎯 Perfect For

- **Investment Banking**: Professional DCF models for analysis
- **Corporate Finance**: Valuation work for M&A, IPOs
- **Equity Research**: Company valuation reports
- **Private Equity**: Target company analysis
- **Academic**: Financial modeling education

## 🚀 Ready to Use!

The system is production-ready and generates investment-grade DCF models with real financial data. Simply run:

```bash
python quick_dcf_generator.py YOUR_FAVORITE_TICKER
```

And get a complete, professionally formatted DCF model instantly! 🎉
