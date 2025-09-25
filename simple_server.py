#!/usr/bin/env python3
"""
Simple Excel Sharing Server
A reliable server that stays running and works with ngrok
"""

import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from flask import Flask, send_file, render_template_string

app = Flask(__name__)

# Global variables
EXCEL_FILE = None
MODEL_TYPE = None
FILE_ID = None

def generate_file_id(file_path):
    """Generate a unique file ID."""
    return hashlib.sha1(file_path.encode()).hexdigest()[:12]

def setup_server(file_path, model_type):
    """Setup the server with file details."""
    global EXCEL_FILE, MODEL_TYPE, FILE_ID
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    EXCEL_FILE = file_path
    MODEL_TYPE = model_type
    FILE_ID = generate_file_id(file_path)
    
    print(f"✅ Server configured:")
    print(f"   📁 File: {os.path.basename(file_path)}")
    print(f"   📊 Model: {model_type}")
    print(f"   🔑 ID: {FILE_ID}")
    
    return True

@app.route('/')
def index():
    """Main page with download link."""
    if not EXCEL_FILE:
        return "Server not configured", 500
    
    file_name = os.path.basename(EXCEL_FILE)
    file_size_bytes = os.path.getsize(EXCEL_FILE)
    file_size_kb = round(file_size_bytes / 1024, 2)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FinModAI - Excel Model Download</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                padding: 40px;
                max-width: 600px;
                text-align: center;
            }}
            h1 {{
                color: #3d3c9d;
                margin-bottom: 20px;
                font-size: 2.5em;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 1.2em;
            }}
            .file-info {{
                background: linear-gradient(135deg, #eef2f7 0%, #f8f9fa 100%);
                border-left: 5px solid #5ecfdb;
                padding: 20px;
                margin: 30px 0;
                border-radius: 10px;
                text-align: left;
            }}
            .file-info p {{
                margin: 8px 0;
                font-size: 1.1em;
            }}
            .download-btn {{
                background: linear-gradient(135deg, #886ff4 0%, #5ecfdb 100%);
                color: white;
                padding: 20px 40px;
                border: none;
                border-radius: 10px;
                font-size: 1.3em;
                font-weight: bold;
                cursor: pointer;
                text-decoration: none;
                transition: all 0.3s ease;
                display: inline-block;
                margin: 20px 0;
                box-shadow: 0 5px 15px rgba(136, 111, 244, 0.3);
            }}
            .download-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(136, 111, 244, 0.4);
            }}
            .footer {{
                margin-top: 40px;
                font-size: 0.9em;
                color: #777;
            }}
            .status {{
                background-color: #d4edda;
                color: #155724;
                padding: 10px;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 FinModAI Excel Model</h1>
            <p class="subtitle">Your professional financial model is ready for download</p>
            
            <div class="status">
                ✅ Server is running and ready
            </div>
            
            <div class="file-info">
                <p><strong>📁 File Name:</strong> {file_name}</p>
                <p><strong>📊 Model Type:</strong> {model_type.upper()}</p>
                <p><strong>📏 File Size:</strong> {file_size_kb} KB</p>
                <p><strong>🕒 Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>🔑 Download ID:</strong> {FILE_ID}</p>
            </div>
            
            <a href="/download" class="download-btn">
                📥 Download {file_name}
            </a>
            
            <p class="footer">
                Powered by FinModAI Excel Sharing System<br>
                Professional Financial Modeling Made Simple
            </p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/download')
def download():
    """Download the Excel file."""
    if not EXCEL_FILE or not os.path.exists(EXCEL_FILE):
        return "File not found", 404
    
    return send_file(
        EXCEL_FILE,
        as_attachment=True,
        download_name=os.path.basename(EXCEL_FILE),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route(f'/{FILE_ID}')
def direct_download():
    """Direct download with file ID."""
    return download()

def start_server(file_path, model_type, port=8080):
    """Start the server."""
    if not setup_server(file_path, model_type):
        return False
    
    print(f"🚀 Starting server on http://localhost:{port}")
    print(f"🔗 Main URL: http://localhost:{port}")
    print(f"📥 Direct download: http://localhost:{port}/{FILE_ID}")
    print(f"🌍 Ready for ngrok tunnel!")
    print(f"Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python simple_server.py <file_path> <model_type> [port]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    model_type = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8080
    
    start_server(file_path, model_type, port)
