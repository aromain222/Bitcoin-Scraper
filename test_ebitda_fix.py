import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

# Test the EBITDA fix
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')

print("=== EBITDA FIX TEST ===")
print(f"Revenue: ${data['revenue']:,.0f}")
print(f"Operating Income: ${data['operating_income']:,.0f}")
print(f"EBITDA: ${data['ebitda']:,.0f}")
print(f"EBITDA Margin: {data['ebitda_margin']*100:.1f}%")

# Test other companies
companies = [('AAPL', 'Apple Inc.'), ('GOOGL', 'Alphabet Inc.'), ('TSLA', 'Tesla Inc.')]

for ticker, name in companies:
    print(f"\n=== {name} ({ticker}) ===")
    data = get_comprehensive_company_data(ticker, name)
    print(f"Revenue: ${data['revenue']:,.0f}")
    print(f"Operating Income: ${data['operating_income']:,.0f}")
    print(f"EBITDA: ${data['ebitda']:,.0f}")
    print(f"EBITDA Margin: {data['ebitda_margin']*100:.1f}%") 