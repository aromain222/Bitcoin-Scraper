#!/usr/bin/env python3
"""
Direct Excel Sharing System
Creates a simple shareable link for Excel files using a local web server
"""

import os
import sys
import json
import http.server
import socketserver
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import mimetypes

def create_shareable_link(file_path, model_type="dcf"):
    """Create a shareable link for an Excel file."""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    # Generate a unique file ID
    import hashlib
    import time
    file_id = hashlib.md5(f"{time.time()}{os.path.basename(file_path)}".encode()).hexdigest()[:12]
    
    # Create a simple HTML file with download link
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Excel File Download - {os.path.basename(file_path)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        h1 {{ color: #2c3e50; margin-bottom: 20px; }}
        .file-info {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .download-btn {{
            background: #3498db;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 20px 0;
        }}
        .download-btn:hover {{
            background: #2980b9;
        }}
        .info {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Excel Financial Model</h1>
        <div class="file-info">
            <h3>{os.path.basename(file_path)}</h3>
            <p><strong>Model Type:</strong> {model_type.upper()}</p>
            <p><strong>File Size:</strong> {(os.path.getsize(file_path) / 1024):.1f} KB</p>
            <p><strong>Created:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <a href="file://{os.path.abspath(file_path)}" class="download-btn">
            📥 Download Excel File
        </a>
        
        <div class="info">
            <p>This is a local file sharing link. The file will be downloaded directly from your computer.</p>
            <p>For security, this link only works when the file is accessible on your local machine.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    html_file = f"share_{file_id}.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    # Get absolute path
    html_path = os.path.abspath(html_file)
    
    print("✅ Shareable link created!")
    print(f"🔗 HTML File: {html_path}")
    print(f"📁 Excel File: {os.path.abspath(file_path)}")
    print(f"📊 Model Type: {model_type}")
    print(f"📏 File Size: {(os.path.getsize(file_path) / 1024):.1f} KB")
    print(f"⏰ Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n🌐 Open this file in your browser to share:")
    print(f"   file://{html_path}")
    
    # Try to open in browser
    try:
        webbrowser.open(f"file://{html_path}")
        print("🚀 Opened in your default browser!")
    except:
        print("💡 Manually open the HTML file in your browser to share")
    
    return {
        'success': True,
        'file_id': file_id,
        'html_file': html_path,
        'excel_file': os.path.abspath(file_path),
        'model_type': model_type,
        'file_name': os.path.basename(file_path),
        'file_size': os.path.getsize(file_path),
        'created_at': datetime.now().isoformat()
    }

def create_web_server_link(file_path, model_type="dcf", port=8080):
    """Create a web server to share the file."""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    # Generate file ID
    import hashlib
    import time
    file_id = hashlib.md5(f"{time.time()}{os.path.basename(file_path)}".encode()).hexdigest()[:12]
    
    class FileHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == f'/{file_id}':
                self.serve_excel_file(file_path)
            elif self.path == '/':
                self.serve_info_page(file_path, model_type, file_id)
            else:
                self.send_response(404)
                self.end_headers()
        
        def serve_excel_file(self, file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                
                self.send_response(200)
                self.send_header('Content-type', mime_type)
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                
                self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
        
        def serve_info_page(self, file_path, model_type, file_id):
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Excel File Sharing</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        h1 {{ color: #2c3e50; }}
        .download-btn {{ background: #3498db; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; margin: 20px 0; }}
        .download-btn:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Excel Financial Model</h1>
        <h3>{os.path.basename(file_path)}</h3>
        <p><strong>Model Type:</strong> {model_type.upper()}</p>
        <p><strong>File Size:</strong> {(os.path.getsize(file_path) / 1024):.1f} KB</p>
        <a href="/{file_id}" class="download-btn">📥 Download Excel File</a>
    </div>
</body>
</html>
"""
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
    
    # Start server in a separate thread
    def start_server():
        with socketserver.TCPServer(("", port), FileHandler) as httpd:
            print(f"🚀 Web server started on http://localhost:{port}")
            print(f"🔗 Share this URL: http://localhost:{port}")
            print(f"📥 Direct download: http://localhost:{port}/{file_id}")
            print("Press Ctrl+C to stop the server")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 Server stopped")
    
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    import time
    time.sleep(1)
    
    # Open browser
    try:
        webbrowser.open(f"http://localhost:{port}")
        print("🚀 Opened in your default browser!")
    except:
        print(f"💡 Open http://localhost:{port} in your browser")
    
    return {
        'success': True,
        'file_id': file_id,
        'url': f"http://localhost:{port}",
        'download_url': f"http://localhost:{port}/{file_id}",
        'excel_file': os.path.abspath(file_path),
        'model_type': model_type,
        'file_name': os.path.basename(file_path),
        'file_size': os.path.getsize(file_path),
        'created_at': datetime.now().isoformat()
    }

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python direct_excel_sharing.py html <file_path> [model_type]")
        print("  python direct_excel_sharing.py server <file_path> [model_type] [port]")
        print("\nExamples:")
        print("  python direct_excel_sharing.py html model.xlsx dcf")
        print("  python direct_excel_sharing.py server model.xlsx dcf 8080")
        sys.exit(1)
    
    method = sys.argv[1]
    file_path = sys.argv[2]
    model_type = sys.argv[3] if len(sys.argv) > 3 else "dcf"
    port = int(sys.argv[4]) if len(sys.argv) > 4 else 8080
    
    if method == "html":
        result = create_shareable_link(file_path, model_type)
    elif method == "server":
        result = create_web_server_link(file_path, model_type, port)
    else:
        print("❌ Unknown method. Use 'html' or 'server'")
        sys.exit(1)
    
    if result:
        print(f"\n✅ Success! File shared as {model_type.upper()} model")
        return result
    else:
        print("❌ Failed to create shareable link")
        sys.exit(1)

if __name__ == "__main__":
    main()
