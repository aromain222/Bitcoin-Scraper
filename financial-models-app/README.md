# 🏦 Professional Financial Models Generator

Generate Wall Street-quality financial models directly in your Google Drive with professional formatting and real market data.

## ✨ Features

### 🎯 **One-Time Fee: $499 for All Models**
- No subscriptions or recurring charges
- Lifetime access to all 7 professional models
- Direct creation in your Google Drive
- Real-time financial data integration

### 📊 **Available Models**
All models include professional formatting, real financial data, and comprehensive analysis:

1. **DCF (Discounted Cash Flow)** - Enterprise valuation with sensitivity analysis
2. **LBO (Leveraged Buyout)** - Private equity transaction modeling with IRR/MOIC
3. **M&A (Merger & Acquisition)** - Accretion/dilution analysis with synergies
4. **IPO Model** - Public offering valuation and structure analysis
5. **Options Pricing** - Black-Scholes with Greeks calculations
6. **3-Statement Model** - Integrated financial statements with dynamic linking
7. **Scenario Analysis** - Multi-case modeling with probability weighting

### 🚀 **Google Sheets Integration**
- **Direct to Drive**: Models created instantly in your Google Drive
- **Professional Formatting**: Color-coded inputs, formulas, and headers
- **Real-Time Data**: Automatic financial data retrieval via Yahoo Finance
- **Collaborative**: Share and collaborate like any Google Sheet
- **Accessible**: No software installation - works in any browser

## 🔧 Quick Start

### Prerequisites
- Python 3.7+
- Google Account
- Modern web browser

### 1. Install Dependencies
```bash
cd financial-models-app/backend
pip install -r requirements.txt
```

### 2. Set Up Google OAuth (Required)
**⚠️ Important**: You must complete Google OAuth setup to create sheets in your Drive.

See detailed instructions in: [`GOOGLE_SETUP.md`](GOOGLE_SETUP.md)

Quick summary:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project and enable APIs (Sheets, Drive, OAuth2)
3. Set up OAuth consent screen
4. Create OAuth credentials
5. Update `backend/app.py` with your credentials

### 3. Start the Application
```bash
# Mac/Linux
./start.sh

# Windows  
start.bat
```

### 4. Open Your Browser
Visit: http://localhost:8080

## 🎯 How to Use

### Step 1: Enter Your Email
- Enter your Google account email
- Click "Continue with Google"
- Complete the OAuth permission flow

### Step 2: Company Information
- Enter company name (e.g., "Apple Inc.", "Tesla")
- Optional: Add ticker symbol for real data (e.g., AAPL, TSLA)
- Leave ticker blank for private companies

### Step 3: Select Models
- Choose from 7 professional financial models
- All models included in one-time $499 fee
- Select multiple models for comprehensive analysis

### Step 4: Generate & Access
- Click "Generate Google Sheets"
- Models created directly in your Google Drive
- Open, edit, and share like any Google Sheet

## 📈 Sample Output

Each model creates professionally formatted Google Sheets with:

- **Multiple Tabs**: Assumptions, Model, Sensitivity, Summary
- **Color Coding**: Blue inputs, black formulas, gray headers
- **Real Data**: Automatic financial data integration
- **Dynamic Formulas**: Fully linked and audit-friendly
- **Professional Design**: Investment bank quality formatting

## 🔐 Security & Privacy

### Data Security
- OAuth 2.0 standard authentication
- No storage of your Google credentials
- Files created directly in your Drive
- Only creates files - no reading of existing data

### Permissions Required
- **Create Google Sheets**: Generate your financial models
- **Access Google Drive**: Save files to your Drive
- **View Email**: Authentication purposes only

## 🛠️ Requirements

### System Requirements
- Python 3.7 or higher
- 2GB RAM minimum
- Internet connection (for data retrieval)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Google Account Setup
- Personal or business Google account
- Google Drive access
- No Google Workspace required

## ✅ Success Indicators

When everything is working correctly:

1. **Backend starts**: "🚀 Starting Financial Models API..."
2. **Frontend loads**: Professional UI at http://localhost:8080
3. **OAuth works**: Google permission screen appears
4. **Models generate**: Sheets appear in your Google Drive
5. **Data flows**: Real financial data populates automatically

## 🆘 Troubleshooting

### Common Issues

**"No module named 'gspread'"**
```bash
pip install -r requirements.txt
```

**"redirect_uri_mismatch"**
- Check OAuth redirect URI: `http://localhost:5001/callback`
- Verify JavaScript origins: `http://localhost:8080`

**"Authentication failed"**
- Complete Google OAuth setup (see GOOGLE_SETUP.md)
- Use same email in app and Google Console
- Check that all APIs are enabled

**Models not appearing in Drive**
- Check Google Drive "Recent" section
- Search for company name in Drive
- Verify app permissions in Google Account settings

### Port Issues
- Backend runs on port 5001
- Frontend runs on port 8080
- Kill existing processes: `lsof -ti:5001 | xargs kill -9`

## 📂 Project Structure

```
financial-models-app/
├── backend/
│   ├── app.py              # Flask API with Google Sheets integration
│   ├── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html         # Multi-step UI with OAuth flow
│   ├── script.js          # JavaScript for Google integration
│   ├── styles.css         # Professional styling
├── start.sh               # Mac/Linux startup script
├── start.bat              # Windows startup script
├── GOOGLE_SETUP.md        # Detailed OAuth setup guide
└── README.md              # This file
```

## 🚀 Advanced Features

### Real-Time Data Integration
- Automatic retrieval from Yahoo Finance
- SEC filing data where available
- Industry-specific assumptions
- Live market data updates

### Professional Formatting
- Investment bank standard layouts
- Color-coded sections for clarity
- Conditional formatting for insights
- Print-ready presentations

### Collaboration Ready
- Standard Google Sheets sharing
- Real-time collaborative editing
- Comment and suggestion features
- Version history tracking

## 🎯 Perfect For

- **Investment Professionals**: Analysts, Associates, VPs
- **Corporate Finance**: FP&A, Treasury, Strategic Planning  
- **Consultants**: Management consulting, Financial advisory
- **Students**: MBA, Finance, Accounting programs
- **Entrepreneurs**: Fundraising, Business planning

## 💡 Tips for Best Results

1. **Use Real Tickers**: Public companies get live data automatically
2. **Check Assumptions**: Review and adjust model assumptions  
3. **Save Copies**: Create template versions for reuse
4. **Share Selectively**: Use Google's sharing controls
5. **Regular Updates**: Refresh data for current analysis

## 🔄 Updates & Support

This is a standalone application - no cloud dependencies or subscription required. All models run locally and create files directly in your Google Drive.

For technical support, check:
1. Browser console for JavaScript errors
2. Python terminal for backend errors  
3. Google Cloud Console for OAuth issues
4. GOOGLE_SETUP.md for detailed instructions

---

**Ready to generate professional financial models?** 

1. Complete the Google OAuth setup
2. Run `./start.sh` or `start.bat`
3. Open http://localhost:8080
4. Start modeling! 🚀 