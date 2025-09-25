import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data

# Get data
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')

print("=== RESEARCH ASSUMPTIONS DEBUG ===")
if 'research_assumptions' in data and data['research_assumptions']:
    assumptions = data['research_assumptions']
    print(f"Keys in research_assumptions: {list(assumptions.keys())}")
    
    # Check for required keys
    required_keys = ['revenue_growth', 'ebitda_margin', 'capex_pct_revenue', 'tax_rate', 'wacc', 'terminal_growth', 'beta']
    
    for key in required_keys:
        if key in assumptions:
            print(f"✅ {key}: {assumptions[key]}")
        else:
            print(f"❌ {key}: MISSING")
            
    # Check structure of revenue_growth
    if 'revenue_growth' in assumptions:
        growth = assumptions['revenue_growth']
        print(f"Revenue growth type: {type(growth)}")
        print(f"Revenue growth value: {growth}")
        if isinstance(growth, list):
            print(f"Revenue growth length: {len(growth)}")
        else:
            print("⚠️ Revenue growth is not a list!")
else:
    print("❌ No research assumptions found") 