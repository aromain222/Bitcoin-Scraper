#!/usr/bin/env python3
"""
Excel Sharing Demo - Test the Excel sharing system with sample files

This script demonstrates the Excel sharing system functionality including:
- Pre-flight checks
- File validation
- Cloud storage setup requirements
- Sharing process simulation

Usage:
    python excel_sharing_demo.py
"""

import os
import sys
from pathlib import Path
from excel_sharing_system import ExcelSharingSystem, SharingConfig

def demo_pre_flight_check():
    """Demonstrate pre-flight check functionality."""
    print("🚀 Excel Sharing System Demo")
    print("=" * 60)

    # Initialize sharing system
    config = SharingConfig(
        provider="google_drive",
        credentials_path="google_drive_credentials.json",
        link_expiration_days=30
    )

    sharing_system = ExcelSharingSystem(config)

    # Test with existing Excel file
    excel_files = list(Path("generated_models").glob("*.xlsx"))
    if excel_files:
        test_file = str(excel_files[0])
        print(f"📊 Testing with file: {test_file}")
    else:
        # Create a test file path for demo
        test_file = "generated_models/FinModAI_DCF_Apple Inc_20250908_134701.xlsx"
        print(f"📊 Testing with file: {test_file} (may not exist)")

    # Perform pre-flight check
    print("\n🔍 Performing Pre-Flight Check...")
    print("-" * 40)

    preflight_result = sharing_system.pre_flight_check(test_file, "dcf")

    print(f"Status: {preflight_result['status']}")
    print(f"Summary: {preflight_result['summary']}")

    if preflight_result['requirements']['required_setup']:
        print("\n📋 Required Setup:")
        for i, req in enumerate(preflight_result['requirements']['required_setup'], 1):
            print(f"  {i}. {req}")

    # File validation
    if os.path.exists(test_file):
        print("\n📊 Excel Validation...")
        print("-" * 40)
        validation = sharing_system.validate_excel_formatting(test_file)
        if validation.get('workbook_loaded'):
            print("✅ Excel file loaded successfully")
            print(f"📊 Worksheets found: {', '.join(validation.get('worksheets', []))}")
            for sheet in validation.get('worksheets', []):
                formulas = validation.get(f"{sheet}_formulas", 0)
                print(f"   • {sheet}: {formulas} formulas detected")
        else:
            print("❌ Excel validation failed")
            for issue in validation.get('issues', []):
                print(f"   • {issue}")

    return sharing_system, test_file

def demo_sharing_process(sharing_system, file_path):
    """Demonstrate the sharing process."""
    print("\n📤 Attempting to Share Excel File...")
    print("-" * 40)

    # Note: This will fail without proper AWS credentials
    result = sharing_system.share_excel_file(file_path, "dcf")

    if result.success:
        print("✅ File shared successfully!")
        print(f"🔗 URL: {result.url}")
        print(f"⏰ Expires: {result.expires}")
    else:
        print("❌ Sharing failed (expected without credentials)")
        print(f"Error: {result.error_message}")

        print("\n🔧 To make this work, you would need to:")
        print("1. Set up AWS S3 bucket")
        print("2. Configure AWS credentials")
        print("3. Install boto3: pip install boto3")
        print("4. Set environment variables:")
        print("   export AWS_ACCESS_KEY_ID='your-key'")
        print("   export AWS_SECRET_ACCESS_KEY='your-secret'")
        print("   export AWS_DEFAULT_REGION='us-east-1'")

def show_supported_providers():
    """Show supported cloud storage providers."""
    print("\n☁️ Supported Cloud Storage Providers")
    print("-" * 40)

    providers = {
        "aws_s3": {
            "name": "Amazon S3",
            "requirements": [
                "AWS account with S3 service",
                "IAM user with S3 permissions",
                "S3 bucket creation",
                "AWS CLI or boto3 credentials"
            ],
            "pros": ["Highly scalable", "Low cost", "Enterprise-grade"],
            "cons": ["Complex setup", "AWS account required"]
        },
        "google_drive": {
            "name": "Google Drive",
            "requirements": [
                "Google Cloud Platform account",
                "Google Drive API enabled",
                "Service account credentials",
                "Google Drive folder sharing"
            ],
            "pros": ["Easy to use", "Familiar interface", "Good for small teams"],
            "cons": ["API quota limits", "Less scalable for large files"]
        },
        "dropbox": {
            "name": "Dropbox",
            "requirements": [
                "Dropbox account",
                "Dropbox API app",
                "Access token generation",
                "Dropbox API permissions"
            ],
            "pros": ["Simple API", "Good for collaboration", "Mobile access"],
            "cons": ["Storage limits", "Less enterprise features"]
        },
        "azure_blob": {
            "name": "Azure Blob Storage",
            "requirements": [
                "Azure account",
                "Storage account creation",
                "Blob container setup",
                "Azure storage credentials"
            ],
            "pros": ["Enterprise-grade", "Global CDN", "Advanced security"],
            "cons": ["Microsoft ecosystem", "Complex pricing"]
        }
    }

    for provider_id, info in providers.items():
        print(f"\n🔹 {info['name']} ({provider_id})")
        print(f"   Requirements:")
        for req in info['requirements']:
            print(f"     • {req}")
        print(f"   Pros: {', '.join(info['pros'])}")
        print(f"   Cons: {', '.join(info['cons'])}")

def main():
    """Main demo function."""
    try:
        # Show supported providers
        show_supported_providers()

        # Demo pre-flight check
        sharing_system, test_file = demo_pre_flight_check()

        # Demo sharing process (will show requirements)
        demo_sharing_process(sharing_system, test_file)

        # Show usage examples
        print("\n📖 Usage Examples")
        print("-" * 40)
        print("Command Line:")
        print("  python excel_sharing_system.py /path/to/model.xlsx dcf --provider aws_s3 --bucket my-models")
        print()
        print("Python API:")
        print("  from excel_sharing_system import ExcelSharingSystem, SharingConfig")
        print("  config = SharingConfig(provider='aws_s3', bucket_name='my-models')")
        print("  system = ExcelSharingSystem(config)")
        print("  result = system.share_excel_file('model.xlsx', 'dcf')")
        print("  print(f'Shareable URL: {result.url}')")

        print("\n✨ Demo completed! The Excel sharing system is ready for use.")
        print("   Set up your preferred cloud provider credentials to enable file sharing.")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
