#!/usr/bin/env python3
"""
COMPREHENSIVE FINANCIAL MODELS AUDIT
====================================
This script audits all models to identify issues causing terrible output.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.append('financial-models-app/backend')

def audit_data_quality():
    """Audit the data quality issues"""
    print("🔍 AUDITING DATA QUALITY ISSUES")
    print("=" * 50)
    
    try:
        from app import get_comprehensive_company_data
        
        # Test with multiple companies
        companies = [
            ('MSFT', 'Microsoft Corporation'),
            ('AAPL', 'Apple Inc.'),
            ('GOOGL', 'Alphabet Inc.'),
            ('TSLA', 'Tesla Inc.')
        ]
        
        for ticker, name in companies:
            print(f"\n📊 Testing {name} ({ticker}):")
            data = get_comprehensive_company_data(ticker, name)
            
            # Check for data quality issues
            revenue = data.get('revenue', 0)
            ebitda = data.get('ebitda', 0)
            ebitda_margin = ebitda / revenue if revenue > 0 else 0
            
            print(f"   Revenue: ${revenue:,.0f}")
            print(f"   EBITDA: ${ebitda:,.0f}")
            print(f"   EBITDA Margin: {ebitda_margin*100:.1f}%")
            
            # Flag unreasonable margins
            if ebitda_margin > 0.8:
                print(f"   ❌ UNREASONABLE EBITDA MARGIN: {ebitda_margin*100:.1f}%")
            elif ebitda_margin < 0.05:
                print(f"   ⚠️ LOW EBITDA MARGIN: {ebitda_margin*100:.1f}%")
            else:
                print(f"   ✅ Reasonable EBITDA margin")
                
    except Exception as e:
        print(f"❌ Data quality audit failed: {e}")

def audit_model_outputs():
    """Audit each model's output quality"""
    print("\n🔍 AUDITING MODEL OUTPUT QUALITY")
    print("=" * 50)
    
    try:
        from app import get_comprehensive_company_data, create_professional_excel_model
        
        # Test each model type
        model_types = ['dcf', 'ma', 'lbo', 'comps', 'ipo', 'options', '3-statement']
        
        for model_type in model_types:
            print(f"\n📋 Testing {model_type.upper()} Model:")
            
            # Get test data
            data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
            
            # Create model
            result = create_professional_excel_model(data, model_type)
            
            # Analyze the Excel file
            try:
                xl = pd.ExcelFile(result)
                print(f"   Sheets: {xl.sheet_names}")
                
                total_rows = 0
                total_cells = 0
                empty_cells = 0
                formula_cells = 0
                
                for sheet in xl.sheet_names:
                    df = pd.read_excel(result, sheet_name=sheet)
                    rows, cols = df.shape
                    total_rows += rows
                    total_cells += rows * cols
                    
                    # Count empty cells
                    empty_cells += df.isnull().sum().sum()
                    
                    # Look for formula-like text
                    for col in df.columns:
                        for value in df[col].dropna():
                            if isinstance(value, str) and any(indicator in value for indicator in ['=', '+', '-', '*', '/', 'SUM', 'AVERAGE']):
                                formula_cells += 1
                
                print(f"   Total rows: {total_rows}")
                print(f"   Total cells: {total_cells}")
                print(f"   Empty cells: {empty_cells} ({empty_cells/total_cells*100:.1f}%)")
                print(f"   Formula cells: {formula_cells}")
                
                # Flag issues
                if empty_cells / total_cells > 0.5:
                    print(f"   ❌ TOO MANY EMPTY CELLS: {empty_cells/total_cells*100:.1f}%")
                if formula_cells > 0:
                    print(f"   ❌ FORMULAS AS TEXT: {formula_cells} cells")
                if total_rows < 10:
                    print(f"   ❌ TOO FEW ROWS: {total_rows}")
                    
            except Exception as e:
                print(f"   ❌ Excel analysis failed: {e}")
                
    except Exception as e:
        print(f"❌ Model output audit failed: {e}")

def audit_code_issues():
    """Audit the code for common issues"""
    print("\n🔍 AUDITING CODE ISSUES")
    print("=" * 50)
    
    # Check for common problems in the main app file
    app_file = 'financial-models-app/backend/app.py'
    
    if os.path.exists(app_file):
        with open(app_file, 'r') as f:
            content = f.read()
            
        issues = []
        
        # Check for placeholder comments
        if 'Implementation details' in content:
            issues.append("Placeholder comments found")
        if 'Add detailed' in content:
            issues.append("Incomplete implementations")
        if 'TODO' in content:
            issues.append("TODO comments found")
            
        # Check for hardcoded values
        if 'hardcoded' in content.lower():
            issues.append("Hardcoded values detected")
            
        # Check for error handling
        if 'except Exception as e:' not in content:
            issues.append("Missing error handling")
            
        if issues:
            print("❌ Code issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ No obvious code issues found")
    else:
        print("❌ App file not found")

def audit_specific_models():
    """Audit specific model implementations"""
    print("\n🔍 AUDITING SPECIFIC MODEL IMPLEMENTATIONS")
    print("=" * 50)
    
    try:
        from app import get_comprehensive_company_data, create_professional_excel_model
        
        # Test DCF model specifically
        print("\n📈 DCF Model Audit:")
        data = get_comprehensive_company_data('MSFT', 'Microsoft Corporation')
        result = create_professional_excel_model(data, 'dcf')
        
        # Check DCF specific issues
        xl = pd.ExcelFile(result)
        df = pd.read_excel(result, sheet_name=xl.sheet_names[0])
        
        # Look for DCF-specific problems
        dcf_issues = []
        
        # Check if projections are present
        if 'Revenue' not in df.values:
            dcf_issues.append("Missing revenue projections")
        if 'EBITDA' not in df.values:
            dcf_issues.append("Missing EBITDA projections")
        if 'Free Cash Flow' not in df.values:
            dcf_issues.append("Missing FCF projections")
            
        # Check for valuation summary
        if 'Enterprise Value' not in df.values:
            dcf_issues.append("Missing enterprise value")
        if 'Intrinsic Value' not in df.values:
            dcf_issues.append("Missing intrinsic value")
            
        if dcf_issues:
            print("❌ DCF issues found:")
            for issue in dcf_issues:
                print(f"   - {issue}")
        else:
            print("✅ DCF model appears complete")
            
        # Test M&A model specifically
        print("\n🤝 M&A Model Audit:")
        result = create_professional_excel_model(data, 'ma')
        
        xl = pd.ExcelFile(result)
        print(f"   Sheets: {xl.sheet_names}")
        
        ma_issues = []
        
        # Check for required sheets
        required_sheets = ['MA Model', 'M&A Assumptions', 'Pro Forma Analysis']
        for sheet in required_sheets:
            if sheet not in xl.sheet_names:
                ma_issues.append(f"Missing {sheet} sheet")
                
        # Check for empty sheets
        for sheet in xl.sheet_names:
            df = pd.read_excel(result, sheet_name=sheet)
            if df.empty:
                ma_issues.append(f"Empty {sheet} sheet")
                
        if ma_issues:
            print("❌ M&A issues found:")
            for issue in ma_issues:
                print(f"   - {issue}")
        else:
            print("✅ M&A model appears complete")
            
    except Exception as e:
        print(f"❌ Specific model audit failed: {e}")

def main():
    """Run comprehensive audit"""
    print("🔍 COMPREHENSIVE FINANCIAL MODELS AUDIT")
    print("=" * 60)
    print("This audit will identify all issues causing terrible output.")
    print("=" * 60)
    
    audit_data_quality()
    audit_model_outputs()
    audit_code_issues()
    audit_specific_models()
    
    print("\n" + "=" * 60)
    print("🎯 AUDIT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main() 