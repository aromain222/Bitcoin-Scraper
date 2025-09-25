import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

# Get data
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')

print("=== MICROSOFT ACTUAL DATA ===")
print(f"Revenue: ${data['revenue']:,.0f}")
print(f"EBITDA: ${data['ebitda']:,.0f}")
print(f"Actual EBITDA Margin: {(data['ebitda']/data['revenue']*100):.1f}%")
print(f"Current Price: ${data['current_price']:.2f}")
print(f"Market Cap: ${data['market_cap']:,.0f}")

# Check what the research assumptions are using
if 'research_assumptions' in data and data['research_assumptions']:
    assumptions = data['research_assumptions']
    print(f"\n=== RESEARCH ASSUMPTIONS ===")
    print(f"EBITDA Margin: {assumptions['ebitda_margin']*100:.1f}%")
    print(f"Revenue Growth: {[f'{g*100:.1f}%' for g in assumptions['revenue_growth']]}")
    print(f"WACC: {assumptions['wacc']*100:.1f}%")
    print(f"Terminal Growth: {assumptions['terminal_growth']*100:.1f}%")

# The issue is that the research assumptions are too conservative
# Microsoft's actual EBITDA margin is much higher than 20%
print(f"\n=== ISSUE IDENTIFIED ===")
print(f"Microsoft's actual EBITDA margin: {(data['ebitda']/data['revenue']*100):.1f}%")
print(f"Research assumption EBITDA margin: {assumptions['ebitda_margin']*100:.1f}%")
print(f"This is causing the DCF to be severely undervalued!") 