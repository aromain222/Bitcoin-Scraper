import pandas as pd
import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data, create_professional_excel_model

# Generate an M&A model
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
result = create_professional_excel_model(data, 'ma')

print('=== M&A MODEL CONTENTS ===')
print(f'File: {result}')

try:
    xl = pd.ExcelFile(result)
    print(f'Sheets: {xl.sheet_names}')
    
    for sheet in xl.sheet_names:
        print(f'\n--- {sheet} ---')
        df = pd.read_excel(result, sheet_name=sheet)
        print(f'Shape: {df.shape}')
        
        # Look for any cells that contain formulas or equation-like text
        formula_indicators = ['=', '+', '-', '*', '/', 'SUM', 'AVERAGE', 'IF', 'VLOOKUP']
        
        for idx, row in df.iterrows():
            for col in df.columns:
                cell_value = str(row[col]) if pd.notna(row[col]) else ''
                if any(indicator in cell_value for indicator in formula_indicators):
                    print(f'Row {idx+1}, Col {col}: "{cell_value}"')
        
        # Show first 20 rows
        print(df.head(20).to_string())
        
except Exception as e:
    print(f'Error reading Excel file: {e}')
    import traceback
    traceback.print_exc() 