#!/usr/bin/env python3
"""
Bulk Download Script for FinModAI Generated Models
Creates a zip file with all generated financial models
"""

import os
import zipfile
import datetime
from pathlib import Path

def create_models_zip():
    """Create a zip file with all generated models"""
    
    # Check if generated_models directory exists
    models_dir = Path("generated_models")
    if not models_dir.exists():
        print("❌ No generated_models directory found")
        return None
    
    # Get all Excel files
    excel_files = list(models_dir.glob("*.xlsx")) + list(models_dir.glob("*.xls"))
    
    if not excel_files:
        print("❌ No Excel model files found")
        return None
    
    # Create zip file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"FinModAI_Models_{timestamp}.zip"
    
    print(f"📦 Creating bulk download: {zip_filename}")
    print(f"📊 Found {len(excel_files)} model files")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in excel_files:
            # Add file to zip with relative path
            arcname = file_path.name
            zipf.write(file_path, arcname)
            print(f"   ✅ Added: {arcname}")
    
    # Get file size
    zip_size = os.path.getsize(zip_filename)
    zip_size_mb = zip_size / (1024 * 1024)
    
    print(f"\n🎉 Success! Created {zip_filename}")
    print(f"📁 File size: {zip_size_mb:.2f} MB")
    print(f"📍 Location: {os.path.abspath(zip_filename)}")
    
    return zip_filename

def list_available_models():
    """List all available models with details"""
    
    models_dir = Path("generated_models")
    if not models_dir.exists():
        print("❌ No generated_models directory found")
        return
    
    excel_files = list(models_dir.glob("*.xlsx")) + list(models_dir.glob("*.xls"))
    
    if not excel_files:
        print("❌ No Excel model files found")
        return
    
    print("📊 Available Financial Models:")
    print("=" * 60)
    
    for i, file_path in enumerate(excel_files, 1):
        # Parse filename to extract info
        filename = file_path.name
        parts = filename.replace('.xlsx', '').split('_')
        
        if len(parts) >= 4:
            model_type = parts[1]  # DCF, LBO, etc.
            company = parts[2]     # Company name
            date_time = parts[3]   # Date and time
            
            # Format date
            try:
                dt = datetime.datetime.strptime(date_time, "%Y%m%d%H%M%S")
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = date_time
            
            # Get file size
            file_size = file_path.stat().st_size
            file_size_kb = file_size / 1024
            
            print(f"{i:2d}. {model_type:3s} | {company:25s} | {formatted_date:16s} | {file_size_kb:6.1f} KB")
        else:
            print(f"{i:2d}. {filename}")
    
    print("=" * 60)
    print(f"Total: {len(excel_files)} models")

if __name__ == "__main__":
    print("🚀 FinModAI Bulk Download Tool")
    print("=" * 40)
    
    # List available models
    list_available_models()
    
    print("\n" + "=" * 40)
    
    # Create zip file
    zip_file = create_models_zip()
    
    if zip_file:
        print(f"\n💡 You can now:")
        print(f"   • Download the zip file: {zip_file}")
        print(f"   • Share it with colleagues")
        print(f"   • Extract individual models as needed")
        print(f"   • Access via web interface: https://ff17399c54ae.ngrok-free.app")
