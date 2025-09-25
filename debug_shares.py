import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

# Get data
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')

print("=== SHARES OUTSTANDING DEBUG ===")
print(f"Shares Outstanding: {data['shares_outstanding']}")
print(f"Type: {type(data['shares_outstanding'])}")
print(f"Current Price: ${data['current_price']}")
print(f"Market Cap: ${data['market_cap']}")

# Calculate what it should be
expected_shares = data['market_cap'] / data['current_price']
print(f"Expected shares (from market cap / price): {expected_shares:,.0f}")

# Check if shares are in millions
if data['shares_outstanding'] > 1000000000:  # If over 1 billion
    shares_in_millions = data['shares_outstanding'] / 1000000
    print(f"Shares in millions: {shares_in_millions:,.0f}M")
    
    # Recalculate intrinsic price
    equity_value = 57608  # From debug output
    intrinsic_price = (equity_value * 1000000) / shares_in_millions
    print(f"Recalculated intrinsic price: ${intrinsic_price:.2f}") 