import yfinance as yf
from datetime import datetime

def test_data_freshness(ticker, test_count=3):
    """Test how fresh the data is by making multiple calls."""
    print(f"\n🔄 Testing data freshness for {ticker}")
    print("=" * 50)

    for i in range(test_count):
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        current_price = info.get('currentPrice', 'N/A')
        last_updated = datetime.now().strftime("%H:%M:%S")

        print(f"Call {i+1}: ${current_price} at {last_updated}")

        # Small delay to see if data updates
        import time
        time.sleep(2)

    print("\n📊 Market Data Details:")
    print(f"Regular Market Price: ${info.get('regularMarketPrice', 'N/A')}")
    print(f"Previous Close: ${info.get('previousClose', 'N/A')}")
    print(f"Market State: {info.get('marketState', 'Unknown')}")

    # Test historical data freshness
    print("\n📈 Recent Historical Data:")
    hist = ticker_obj.history(period="1d", interval="1m")
    if not hist.empty:
        latest_time = hist.index[-1]
        latest_price = hist['Close'].iloc[-1]
        print(f"Latest 1-min bar: ${latest_price:.2f} at {latest_time}")
        print(f"Time difference: {(datetime.now() - latest_time.to_pydatetime()).seconds} seconds ago")

if __name__ == "__main__":
    test_data_freshness("SOFI")
    test_data_freshness("AAPL")
