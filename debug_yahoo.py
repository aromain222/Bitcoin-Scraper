import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

# Get data
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')

print("=== YAHOO FINANCE DATA DEBUG ===")
print(f"Raw shares outstanding: {data['shares_outstanding']}")
print(f"Market cap: {data['market_cap']}")
print(f"Current price: {data['current_price']}")

# Check if shares outstanding is in millions
if data['shares_outstanding'] > 1000000000:
    print("Shares outstanding appears to be in actual shares (not millions)")
    shares_in_millions = data['shares_outstanding'] / 1000000
    print(f"Shares in millions: {shares_in_millions:,.0f}M")
    
    # Verify with market cap calculation
    calculated_shares = data['market_cap'] / data['current_price']
    print(f"Calculated shares from market cap: {calculated_shares:,.0f}")
    
    # The issue might be that equity_value is in millions but we're treating shares as millions
    equity_value_millions = 57608  # From debug output
    intrinsic_price_correct = (equity_value_millions * 1000000) / data['shares_outstanding']
    print(f"Correct intrinsic price: ${intrinsic_price_correct:.2f}")
    
    # What the current calculation is doing
    intrinsic_price_wrong = (equity_value_millions * 1000000) / (data['shares_outstanding'] / 1000000)
    print(f"Wrong intrinsic price: ${intrinsic_price_wrong:.2f}")
else:
    print("Shares outstanding appears to be in millions") 