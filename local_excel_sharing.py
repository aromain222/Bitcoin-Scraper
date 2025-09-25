#!/usr/bin/env python3
"""
Local Excel Sharing System
Creates a simple local web server to share Excel files
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
from urllib.parse import urlparse, parse_qs
import mimetypes

class ExcelSharingHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for Excel file sharing."""
    
    def __init__(self, *args, **kwargs):
        self.shared_files = {}
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = self.generate_dashboard_html()
            self.wfile.write(html.encode())
            return
        
        elif parsed_path.path.startswith('/share/'):
            file_id = parsed_path.path.split('/')[-1]
            if file_id in self.shared_files:
                file_path = self.shared_files[file_id]['path']
                if os.path.exists(file_path):
                    self.serve_file(file_path)
                    return
        
        elif parsed_path.path == '/api/files':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            files_data = []
            for file_id, file_info in self.shared_files.items():
                files_data.append({
                    'id': file_id,
                    'name': file_info['name'],
                    'type': file_info['type'],
                    'size': file_info['size'],
                    'created': file_info['created'],
                    'url': f'http://localhost:8080/share/{file_id}'
                })
            
            self.wfile.write(json.dumps(files_data).encode())
            return
        
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for file sharing."""
        if self.path == '/api/share':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            file_path = data.get('file_path')
            model_type = data.get('model_type', 'unknown')
            
            if file_path and os.path.exists(file_path):
                file_id = self.generate_file_id()
                file_info = {
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'type': model_type,
                    'size': os.path.getsize(file_path),
                    'created': datetime.now().isoformat()
                }
                
                self.shared_files[file_id] = file_info
                
                share_url = f'http://localhost:8080/share/{file_id}'
                
                response = {
                    'success': True,
                    'file_id': file_id,
                    'url': share_url,
                    'file_name': file_info['name'],
                    'model_type': model_type,
                    'created_at': file_info['created']
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                return
        
        self.send_response(400)
        self.end_headers()
    
    def serve_file(self, file_path):
        """Serve a file with proper headers."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error serving file: {str(e)}'.encode())
    
    def generate_file_id(self):
        """Generate a unique file ID."""
        import hashlib
        import time
        return hashlib.md5(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()[:12]
    
    def generate_dashboard_html(self):
        """Generate the dashboard HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Excel Sharing Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .file-list { margin-top: 20px; }
        .file-item { padding: 15px; border: 1px solid #ddd; margin: 10px 0; border-radius: 5px; background: #f9f9f9; }
        .file-name { font-weight: bold; color: #2c3e50; }
        .file-url { margin: 10px 0; }
        .file-url input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }
        .copy-btn { background: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 3px; cursor: pointer; margin-left: 10px; }
        .copy-btn:hover { background: #2980b9; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Excel Sharing Dashboard</h1>
        <p>Share your Excel financial models with secure, temporary links.</p>
        
        <div id="status"></div>
        
        <div class="file-list" id="fileList">
            <p>Loading shared files...</p>
        </div>
    </div>

    <script>
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(function() {
                showStatus('Link copied to clipboard!', 'success');
            });
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            setTimeout(() => statusDiv.innerHTML = '', 3000);
        }
        
        function loadFiles() {
            fetch('/api/files')
                .then(response => response.json())
                .then(files => {
                    const fileList = document.getElementById('fileList');
                    if (files.length === 0) {
                        fileList.innerHTML = '<p>No files shared yet. Use the Python script to share files.</p>';
                        return;
                    }
                    
                    fileList.innerHTML = files.map(file => `
                        <div class="file-item">
                            <div class="file-name">${file.name}</div>
                            <div>Type: ${file.type} | Size: ${(file.size / 1024).toFixed(1)} KB</div>
                            <div>Created: ${new Date(file.created).toLocaleString()}</div>
                            <div class="file-url">
                                <input type="text" value="${file.url}" readonly id="url-${file.id}">
                                <button class="copy-btn" onclick="copyToClipboard('${file.url}')">Copy Link</button>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    document.getElementById('fileList').innerHTML = '<p>Error loading files: ' + error + '</p>';
                });
        }
        
        // Load files on page load
        loadFiles();
        
        // Refresh every 5 seconds
        setInterval(loadFiles, 5000);
    </script>
</body>
</html>
        """

def start_sharing_server(port=8080):
    """Start the sharing server."""
    handler = ExcelSharingHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🚀 Excel Sharing Server started on http://localhost:{port}")
        print("📊 Dashboard: http://localhost:8080")
        print("🔗 Share files using the Python API")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

def share_excel_file(file_path, model_type, server_url="http://localhost:8080"):
    """Share an Excel file via the local server."""
    import requests
    
    try:
        response = requests.post(f"{server_url}/api/share", json={
            'file_path': file_path,
            'model_type': model_type
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ File shared successfully!")
            print(f"🔗 URL: {result['url']}")
            print(f"📁 File: {result['file_name']}")
            print(f"📊 Model: {result['model_type']}")
            print(f"⏰ Created: {result['created_at']}")
            return result
        else:
            print(f"❌ Error sharing file: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to sharing server. Make sure it's running on port 8080.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Start server: python local_excel_sharing.py server")
        print("  Share file:   python local_excel_sharing.py share <file_path> <model_type>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "server":
        start_sharing_server()
    elif command == "share":
        if len(sys.argv) < 4:
            print("Usage: python local_excel_sharing.py share <file_path> <model_type>")
            sys.exit(1)
        
        file_path = sys.argv[2]
        model_type = sys.argv[3]
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        
        share_excel_file(file_path, model_type)
    else:
        print("Unknown command. Use 'server' or 'share'")
        sys.exit(1)

if __name__ == "__main__":
    main()
