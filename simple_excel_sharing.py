#!/usr/bin/env python3
"""
Simple Excel Sharing System
Uses file.io for quick file sharing without complex cloud setup
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def share_excel_file(file_path: str, model_type: str) -> Dict[str, Any]:
    """Share Excel file using file.io service."""
    try:
        print(f"📤 Sharing Excel file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Upload to file.io
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post('https://file.io', files=files)
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if data.get('success'):
                    return {
                        "success": True,
                        "model_type": model_type,
                        "file_name": os.path.basename(file_path),
                        "url": data['link'],
                        "expires": "1 download or 14 days",
                        "provider": "file.io",
                        "file_size": data.get('size', 'Unknown'),
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Upload failed: {data.get('error', 'Unknown error')}"
                    }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {response.text}"
                }
        else:
            return {
                "success": False,
                "error": f"HTTP error: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload failed: {str(e)}"
        }

def main():
    """Main function for command line usage."""
    if len(sys.argv) < 3:
        print("Usage: python simple_excel_sharing.py <excel_file> <model_type>")
        print("Example: python simple_excel_sharing.py model.xlsx dcf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    model_type = sys.argv[2]
    
    print("🚀 Simple Excel Sharing System")
    print("=" * 40)
    
    result = share_excel_file(file_path, model_type)
    
    if result["success"]:
        print("✅ File shared successfully!")
        print(f"🔗 URL: {result['url']}")
        print(f"📁 File: {result['file_name']}")
        print(f"📊 Model: {result['model_type']}")
        print(f"⏰ Expires: {result['expires']}")
        print(f"📏 Size: {result.get('file_size', 'Unknown')}")
        
        # Save result to JSON
        result_file = f"sharing_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Result saved to: {result_file}")
        
    else:
        print("❌ Sharing failed!")
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
