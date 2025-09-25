# 🏦 Professional Financial Models Web UI

A beautiful, modern web interface for all your financial modeling tools with one-click downloads.

## 🚀 **NEW: Auto-Launch Feature**

**Simply run your main script and it automatically opens the web UI!**

```bash
python professional_dcf_model.py
```

The script will:
1. ✅ Automatically launch the web interface
2. ✅ Open your browser to http://localhost:5000
3. ✅ Show the beautiful web UI for all models
4. ✅ Fall back to terminal menu if web UI fails

No more remembering different commands - just run your main file!

## 🚀 Quick Start

### Option 1: Simple Launcher (Recommended)
```bash
python run_web_ui.py
```

### Option 2: Direct Run
```bash
python financial_models_ui.py
```

Then open your browser to: **http://localhost:5000**

## 🎯 Features

### ✨ Clean Modern Interface
- Beautiful gradient design with professional styling
- Responsive layout that works on all devices
- Intuitive navigation with hover effects
- Progress tracking during model generation

### 📊 Complete Model Library
All your terminal models are now available with a click:

1. **📈 DCF Model** - Complete intrinsic valuation
2. **📊 Comps Analysis** - Peer-based valuation
3. **💰 LBO Model** - Private equity modeling
4. **📋 3-Statement Model** - Integrated financials
5. **💸 FCF Model** - Cash flow analysis
6. **📊 Sensitivity Analysis** - Risk assessment
7. **📈 Trading Comps** - Market multiples
8. **🏟️ Football Field** - Valuation synthesis
9. **🤝 M&A Model** - Accretion/dilution
10. **🔀 Sum-of-the-Parts** - Conglomerate valuation
11. **📋 Precedent Transactions** - Historical deals
12. **🚀 IPO Model** - Public offering analysis
13. **📉 Options Model** - Black-Scholes pricing

### 💾 Instant Downloads
- **Excel Files**: Direct download of `.xlsx` files
- **Google Sheets**: Auto-generated web links
- **Both Formats**: Get both Excel and web versions
- **Progress Tracking**: Real-time status updates

## 🔧 Configuration Options

### Company Setup
- **Company Name**: Required for all models
- **Company Type**: Public or Private
- **Stock Ticker**: For public companies (optional)
- **Forecast Period**: 3, 5, 7, or 10 years

### Output Formats
- **Excel**: Professional `.xlsx` files with formatting
- **Google Sheets**: Shareable web spreadsheets
- **Both**: Get both formats simultaneously

## 📁 File Locations

Generated files are saved in your current directory:
```
/Users/averyromain/Scraper/
├── CompanyName_DCF_Model.xlsx
├── CompanyName_LBO_Model.xlsx
├── CompanyName_Comps_Analysis.xlsx
└── ... (all your models)
```

## 🛠️ Troubleshooting

### Common Issues

**Port 5000 Already in Use**
```bash
# Kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

**Missing Dependencies**
```bash
pip install flask openpyxl pandas numpy yfinance gspread google-auth requests
```

**Browser Won't Open**
- Manually navigate to: http://localhost:5000
- Try a different browser
- Check firewall settings

### Error Messages

**"Model type not supported"**
- The selected model hasn't been fully implemented in the web interface yet
- Use the terminal version for now: `python professional_dcf_model.py`

**"File not found"**
- The Excel file hasn't been generated yet
- Check that the model completed successfully
- Look in your current directory for the file

## 🎨 Interface Guide

### Navigation
1. **Model Selection**: Click any model card to configure
2. **Form Filling**: Enter company details and preferences
3. **Progress Tracking**: Watch the progress bar during generation
4. **Download**: Click download buttons for your files

### Model Configuration
- **Required Fields**: Company name is always required
- **Optional Fields**: Ticker is optional for public companies
- **Smart Defaults**: Sensible defaults for most options
- **Validation**: Form validates inputs before submission

## 🔄 Integration with Terminal

The web UI uses the same underlying code as your terminal models, so:
- ✅ All calculations are identical
- ✅ All data sources are the same
- ✅ All output formats are supported
- ✅ All features are available

## 🚀 Advanced Usage

### Custom Port
```bash
# Run on different port
export FLASK_RUN_PORT=8080
python run_web_ui.py
```

### Debug Mode
```bash
# Enable Flask debug mode
export FLASK_DEBUG=1
python run_web_ui.py
```

### Background Running
```bash
# Run in background
python run_web_ui.py &
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Try the terminal versions of the models
4. Check the generated files in your directory

## 🎉 What's Next

Future enhancements planned:
- ✅ **Batch Processing**: Generate multiple models at once
- 🔄 **Model Comparison**: Side-by-side analysis tools
- 📊 **Dashboard**: Analytics and reporting features
- 🔗 **API Integration**: Connect to external data sources
- 📱 **Mobile Optimization**: Enhanced mobile experience

---

**Enjoy your new Professional Financial Models Web UI! 🎯**