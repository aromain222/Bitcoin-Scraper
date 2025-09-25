import pandas as pd
import sys
sys.path.append('financial-models-app/backend')
from app import get_comprehensive_company_data, create_professional_excel_model

# Generate a DCF model
data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
result = create_professional_excel_model(data, 'dcf')

print('=== DCF MODEL CONTENTS ===')
print(f'File: {result}')

try:
    xl = pd.ExcelFile(result)
    print(f'Sheets: {xl.sheet_names}')
    
    for sheet in xl.sheet_names:
        print(f'\n--- {sheet} ---')
        df = pd.read_excel(result, sheet_name=sheet)
        print(f'Shape: {df.shape}')
        print(df.head(20).to_string())
        
        # Check for empty cells
        empty_cells = df.isnull().sum().sum()
        print(f'Empty cells: {empty_cells}')
        
except Exception as e:
    print(f'Error reading Excel file: {e}') 