import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

# Get data
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')

print("=== EBITDA CALCULATION DEBUG ===")
print(f"Revenue: ${data['revenue']:,.0f}")
print(f"Operating Income: ${data['operating_income']:,.0f}")
print(f"EBITDA: ${data['ebitda']:,.0f}")
print(f"EBITDA Margin: {data['ebitda_margin']*100:.1f}%")

# Check what the DCF model would calculate
actual_ebitda_margin = data['ebitda'] / data['revenue']
print(f"\nDCF Model Calculation:")
print(f"actual_ebitda_margin = {data['ebitda']} / {data['revenue']} = {actual_ebitda_margin}")
print(f"actual_ebitda_margin = {actual_ebitda_margin*100:.1f}%")

# Check if this is reasonable
if 0.1 <= actual_ebitda_margin <= 0.8:
    print(f"✅ This is reasonable (10% to 80%)")
else:
    print(f"❌ This is unreasonable (should be 10% to 80%)") 