import yfinance as yf

ticker = yf.Ticker('SOFI')
info = ticker.info

print('SoFi (SOFI) Real-time Data:')
print(f'Current Price: ${info.get("currentPrice", "N/A")}')
print(f'Market Cap: ${info.get("marketCap", 0):,.0f}')
print(f'Shares Outstanding: {info.get("sharesOutstanding", 0):,.0f}')
print(f'Industry: {info.get("industry", "Unknown")}')
print(f'Sector: {info.get("sector", "Unknown")}')

# Test validation function
def validate_ticker_and_get_info(ticker):
    """Validate if ticker exists and get basic company info."""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        # Check if we got meaningful data
        has_data = (
            info and
            (info.get('longName') or info.get('shortName')) and
            (info.get('marketCap', 0) > 0 or info.get('currentPrice', 0) > 0)
        )

        return info if has_data else None, has_data
    except Exception as e:
        print(f"Ticker validation failed for {ticker}: {e}")
        return None, False

info_result, is_valid = validate_ticker_and_get_info('SOFI')
print(f'\nValidation Result: {"✅ Valid" if is_valid else "❌ Invalid"}')
