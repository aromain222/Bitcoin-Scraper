#!/usr/bin/env python3
"""
Model Updater
Updates existing DCF models to follow the new professional template structure
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Import the new professional template
from professional_dcf_template import ProfessionalDCFTemplate
from data_integrator import ComprehensiveDataIntegrator

class ModelUpdater:
    """Updates existing models to follow the new template structure"""

    def __init__(self):
        self.template = ProfessionalDCFTemplate()
        self.integrator = ComprehensiveDataIntegrator()

    def update_existing_models(self):
        """Update all existing models to follow the new template"""
        print("🔄 Updating existing models to follow professional template")
        print("=" * 60)

        # Find existing DCF models
        existing_models = self._find_existing_models()

        if not existing_models:
            print("❌ No existing models found to update")
            return

        print(f"📁 Found {len(existing_models)} existing models:")
        for model in existing_models:
            print(f"   • {model}")

        print("\n🚀 Starting model updates...")
        updated_models = []

        for model_path in existing_models:
            try:
                print(f"\n📝 Updating: {os.path.basename(model_path)}")

                # Extract company info from model
                company_info = self._extract_company_info(model_path)

                if company_info:
                    # Create new model using template
                    new_model_path = self._create_updated_model(company_info)

                    if new_model_path:
                        updated_models.append(new_model_path)
                        print(f"   ✅ Updated: {os.path.basename(new_model_path)}")
                    else:
                        print(f"   ❌ Failed to update: {os.path.basename(model_path)}")
                else:
                    print(f"   ⚠️ Could not extract company info from: {os.path.basename(model_path)}")

            except Exception as e:
                print(f"   ❌ Error updating {os.path.basename(model_path)}: {e}")
                continue

        print("\n" + "=" * 60)
        print(f"✅ Model update complete!")
        print(f"   Updated models: {len(updated_models)}")
        print("=" * 60)

        return updated_models

    def _find_existing_models(self):
        """Find existing DCF model files"""
        model_patterns = [
            "*dcf*.py",
            "*DCF*.py",
            "*model*.py",
            "*valuation*.py",
            "*financial*.py"
        ]

        existing_models = []

        # Search in current directory and subdirectories
        for pattern in model_patterns:
            for file_path in Path(".").glob(f"**/{pattern}"):
                if file_path.is_file():
                    existing_models.append(str(file_path))

        # Filter out the new template files we just created
        exclude_files = [
            "professional_dcf_template.py",
            "data_integrator.py",
            "model_updater.py"
        ]

        filtered_models = []
        for model in existing_models:
            if not any(exclude in os.path.basename(model) for exclude in exclude_files):
                filtered_models.append(model)

        return filtered_models

    def _extract_company_info(self, model_path):
        """Extract company information from existing model"""
        try:
            with open(model_path, 'r') as f:
                content = f.read()

            # Try to extract company name from content
            company_indicators = [
                r"company_name\s*=\s*['\"]([^'\"]*)['\"]",
                r"company\s*=\s*['\"]([^'\"]*)['\"]",
                r"Company:\s*([^\n\r]*)",
                r"#\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]

            company_name = None
            for pattern in company_indicators:
                import re
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    company_name = match.group(1).strip()
                    break

            # Try to extract ticker
            ticker_indicators = [
                r"ticker\s*=\s*['\"]([^'\"]*)['\"]",
                r"ticker:\s*([A-Z]{1,5})",
                r"([A-Z]{1,5})\s*ticker",
            ]

            ticker = None
            for pattern in ticker_indicators:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    ticker = match.group(1).strip().upper()
                    break

            if company_name or ticker:
                return {
                    'company_name': company_name or ticker or "Unknown Company",
                    'ticker': ticker,
                    'source_file': model_path
                }

        except Exception as e:
            print(f"   ⚠️ Error extracting info from {model_path}: {e}")

        return None

    def _create_updated_model(self, company_info):
        """Create updated model using the professional template"""
        try:
            company_name = company_info['company_name']
            ticker = company_info.get('ticker')

            # Build new model using template
            new_model_path = self.template.build_professional_dcf(company_name, ticker)

            if new_model_path and os.path.exists(new_model_path):
                return new_model_path

        except Exception as e:
            print(f"   ❌ Error creating updated model: {e}")

        return None

    def create_model_comparison(self, updated_models):
        """Create a comparison report of updated models"""
        print("\n📊 Creating model comparison report...")

        comparison_data = []

        for model_path in updated_models:
            try:
                model_info = {
                    'filename': os.path.basename(model_path),
                    'path': model_path,
                    'created_date': datetime.fromtimestamp(os.path.getctime(model_path)).isoformat(),
                    'size_kb': round(os.path.getsize(model_path) / 1024, 2)
                }
                comparison_data.append(model_info)
            except Exception as e:
                print(f"   ⚠️ Error getting info for {model_path}: {e}")

        # Create comparison report
        report_path = f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_path, 'w') as f:
            f.write("DCF Model Update Comparison Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total models updated: {len(comparison_data)}\n\n")

            for i, model in enumerate(comparison_data, 1):
                f.write(f"{i}. {model['filename']}\n")
                f.write(f"   Path: {model['path']}\n")
                f.write(f"   Created: {model['created_date']}\n")
                f.write(f"   Size: {model['size_kb']} KB\n")
                f.write(f"   Features: 6-tab professional structure, integrated data sources\n\n")

            f.write("Key Improvements:\n")
            f.write("• 6-tab professional structure (Assumptions, Forecast, DCF, Sensitivity, Output, Summary)\n")
            f.write("• Blue input cells for assumptions with proper formatting\n")
            f.write("• Integrated data from Yahoo Finance, Finviz, SEC, MacroTrends, and web scrapers\n")
            f.write("• Professional valuation calculations with WACC and terminal value\n")
            f.write("• Sensitivity analysis tables\n")
            f.write("• Client-ready output formatting\n")

        print(f"   📄 Comparison report saved: {report_path}")
        return report_path

def main():
    """Main function"""
    updater = ModelUpdater()

    print("🔄 DCF Model Updater")
    print("=" * 60)
    print("This tool updates existing DCF models to follow the new professional template:")
    print("• 6-tab investment banking structure")
    print("• Professional formatting and formulas")
    print("• Integrated data sources")
    print("• Client-ready outputs")
    print()

    # Update existing models
    updated_models = updater.update_existing_models()

    if updated_models:
        # Create comparison report
        updater.create_model_comparison(updated_models)

    print("\n✅ Model update process complete!")

if __name__ == "__main__":
    main()
