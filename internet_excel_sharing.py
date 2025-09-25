#!/usr/bin/env python3
"""
Internet Excel Sharing System
Makes your Excel files shareable from anywhere on the internet
"""

import os
import sys
import json
import http.server
import socketserver
import threading
import webbrowser
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import mimetypes

def check_ngrok():
    """Check if ngrok is available."""
    # Check for ngrok in current directory first, then system PATH
    ngrok_paths = ['./ngrok', 'ngrok']
    for ngrok_path in ngrok_paths:
        try:
            result = subprocess.run([ngrok_path, 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                return ngrok_path
        except FileNotFoundError:
            continue
    return False

def install_ngrok_instructions():
    """Print instructions for installing ngrok."""
    print("📥 To install ngrok:")
    print("1. Go to https://ngrok.com/download")
    print("2. Download for macOS")
    print("3. Extract and move to /usr/local/bin/")
    print("4. Or use: curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null")
    print("5. Sign up for a free account at https://ngrok.com")
    print("6. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
    print("7. Run: ngrok config add-authtoken YOUR_TOKEN")

def create_ngrok_tunnel(port=8080):
    """Create an ngrok tunnel."""
    ngrok_path = check_ngrok()
    if not ngrok_path:
        print("❌ ngrok not found. Please install it first.")
        install_ngrok_instructions()
        return None
    
    try:
        # Start ngrok in background
        process = subprocess.Popen([ngrok_path, 'http', str(port)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a moment for ngrok to start
        import time
        time.sleep(3)
        
        # Get the public URL
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print(f"🌍 Public URL: {public_url}")
                    return public_url
        except:
            pass
        
        print("⚠️ Could not get ngrok URL automatically. Check http://localhost:4040")
        return "http://localhost:4040"
        
    except Exception as e:
        print(f"❌ Error creating ngrok tunnel: {e}")
        return None

def create_cloudflare_tunnel():
    """Create a Cloudflare tunnel (alternative to ngrok)."""
    print("☁️ Cloudflare Tunnel Option:")
    print("1. Install cloudflared: brew install cloudflared")
    print("2. Login: cloudflared tunnel login")
    print("3. Create tunnel: cloudflared tunnel create excel-sharing")
    print("4. Configure: cloudflared tunnel route dns excel-sharing your-domain.com")
    print("5. Run: cloudflared tunnel run excel-sharing")

def create_heroku_app():
    """Create a Heroku app for sharing."""
    print("🚀 Heroku Option:")
    print("1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli")
    print("2. Login: heroku login")
    print("3. Create app: heroku create your-excel-sharing-app")
    print("4. Deploy: git push heroku main")

def create_railway_app():
    """Create a Railway app for sharing."""
    print("🚂 Railway Option:")
    print("1. Go to https://railway.app")
    print("2. Sign up with GitHub")
    print("3. Create new project")
    print("4. Deploy your Python app")

def create_vercel_app():
    """Create a Vercel app for sharing."""
    print("▲ Vercel Option:")
    print("1. Install Vercel CLI: npm i -g vercel")
    print("2. Login: vercel login")
    print("3. Deploy: vercel --prod")

def create_simple_web_server(file_path, model_type="dcf", port=8080, use_ngrok=True):
    """Create a web server with internet access."""
    
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
                self.send_header('Access-Control-Allow-Origin', '*')
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
    <title>Excel File Sharing - {os.path.basename(file_path)}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            background: white; 
            padding: 40px; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
        }}
        h1 {{ 
            color: #2c3e50; 
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.2em;
        }}
        .file-info {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin: 30px 0;
            border-left: 4px solid #3498db;
        }}
        .file-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        .file-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .detail {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .detail-label {{
            font-weight: bold;
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .detail-value {{
            color: #2c3e50;
            font-size: 1.1em;
            margin-top: 5px;
        }}
        .download-btn {{ 
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white; 
            padding: 20px 40px; 
            border: none; 
            border-radius: 50px; 
            font-size: 18px; 
            font-weight: bold;
            cursor: pointer; 
            text-decoration: none; 
            display: inline-block; 
            margin: 30px 0;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }}
        .download-btn:hover {{ 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.6);
        }}
        .info {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 30px;
            line-height: 1.6;
        }}
        .status {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #c3e6cb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Excel Financial Model</h1>
        <p class="subtitle">Professional Financial Analysis</p>
        
        <div class="status">
            ✅ File ready for download
        </div>
        
        <div class="file-info">
            <div class="file-name">{os.path.basename(file_path)}</div>
            <div class="file-details">
                <div class="detail">
                    <div class="detail-label">Model Type</div>
                    <div class="detail-value">{model_type.upper()}</div>
                </div>
                <div class="detail">
                    <div class="detail-label">File Size</div>
                    <div class="detail-value">{(os.path.getsize(file_path) / 1024):.1f} KB</div>
                </div>
                <div class="detail">
                    <div class="detail-label">Created</div>
                    <div class="detail-value">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                </div>
                <div class="detail">
                    <div class="detail-label">Format</div>
                    <div class="detail-value">Excel (.xlsx)</div>
                </div>
            </div>
        </div>
        
        <a href="/{file_id}" class="download-btn">
            📥 Download Excel File
        </a>
        
        <div class="info">
            <p><strong>About this file:</strong> This is a professional financial model created with FinModAI.</p>
            <p>The file contains detailed financial analysis and can be opened in Microsoft Excel, Google Sheets, or any compatible spreadsheet application.</p>
        </div>
    </div>
</body>
</html>
"""
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(html.encode())
    
    # Start server
    def start_server():
        with socketserver.TCPServer(("", port), FileHandler) as httpd:
            print(f"🚀 Web server started on http://localhost:{port}")
            print(f"📁 File: {os.path.basename(file_path)}")
            print(f"📊 Model: {model_type.upper()}")
            print(f"📏 Size: {(os.path.getsize(file_path) / 1024):.1f} KB")
            
            if use_ngrok:
                print("\n🌍 Creating internet tunnel...")
                public_url = create_ngrok_tunnel(port)
                if public_url:
                    print(f"🔗 Public URL: {public_url}")
                    print(f"📥 Direct download: {public_url}/{file_id}")
                    try:
                        webbrowser.open(public_url)
                    except:
                        pass
                else:
                    print("⚠️ Could not create tunnel. Server is local only.")
                    print(f"🔗 Local URL: http://localhost:{port}")
                    print(f"📥 Direct download: http://localhost:{port}/{file_id}")
            else:
                print(f"🔗 Local URL: http://localhost:{port}")
                print(f"📥 Direct download: http://localhost:{port}/{file_id}")
            
            print("\nPress Ctrl+C to stop the server")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n👋 Server stopped")
    
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    import time
    time.sleep(2)
    
    return {
        'success': True,
        'file_id': file_id,
        'local_url': f"http://localhost:{port}",
        'download_url': f"http://localhost:{port}/{file_id}",
        'excel_file': os.path.abspath(file_path),
        'model_type': model_type,
        'file_name': os.path.basename(file_path),
        'file_size': os.path.getsize(file_path),
        'created_at': datetime.now().isoformat()
    }

def show_cloud_options():
    """Show all cloud deployment options."""
    print("\n🌍 Internet Sharing Options:")
    print("=" * 50)
    
    print("\n1. 🚀 ngrok (Easiest - Free)")
    print("   - Creates instant public URL")
    print("   - No setup required")
    print("   - Command: python internet_excel_sharing.py ngrok file.xlsx dcf")
    
    print("\n2. ☁️ Cloudflare Tunnel (Free)")
    print("   - More reliable than ngrok")
    print("   - Custom domain support")
    print("   - Command: python internet_excel_sharing.py cloudflare file.xlsx dcf")
    
    print("\n3. 🚀 Heroku (Free tier available)")
    print("   - Professional hosting")
    print("   - Always online")
    print("   - Command: python internet_excel_sharing.py heroku file.xlsx dcf")
    
    print("\n4. 🚂 Railway (Free tier available)")
    print("   - Modern platform")
    print("   - Easy deployment")
    print("   - Command: python internet_excel_sharing.py railway file.xlsx dcf")
    
    print("\n5. ▲ Vercel (Free tier available)")
    print("   - Fast global CDN")
    print("   - Easy deployment")
    print("   - Command: python internet_excel_sharing.py vercel file.xlsx dcf")

def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("🌍 Internet Excel Sharing System")
        print("=" * 40)
        print("\nUsage:")
        print("  python internet_excel_sharing.py <method> <file_path> [model_type] [port]")
        print("\nMethods:")
        print("  ngrok      - Use ngrok tunnel (easiest)")
        print("  cloudflare - Use Cloudflare tunnel")
        print("  heroku     - Deploy to Heroku")
        print("  railway    - Deploy to Railway")
        print("  vercel     - Deploy to Vercel")
        print("  local      - Local server only")
        print("  options    - Show all options")
        print("\nExamples:")
        print("  python internet_excel_sharing.py ngrok model.xlsx dcf")
        print("  python internet_excel_sharing.py local model.xlsx dcf 8080")
        print("  python internet_excel_sharing.py options")
        sys.exit(1)
    
    method = sys.argv[1]
    
    if method == "options":
        show_cloud_options()
        sys.exit(0)
    
    if len(sys.argv) < 3:
        print("❌ File path required")
        sys.exit(1)
    
    file_path = sys.argv[2]
    model_type = sys.argv[3] if len(sys.argv) > 3 else "dcf"
    port = int(sys.argv[4]) if len(sys.argv) > 4 else 8080
    
    if method == "ngrok":
        result = create_simple_web_server(file_path, model_type, port, use_ngrok=True)
    elif method == "local":
        result = create_simple_web_server(file_path, model_type, port, use_ngrok=False)
    elif method == "cloudflare":
        create_cloudflare_tunnel()
        result = create_simple_web_server(file_path, model_type, port, use_ngrok=False)
    elif method == "heroku":
        create_heroku_app()
        result = None
    elif method == "railway":
        create_railway_app()
        result = None
    elif method == "vercel":
        create_vercel_app()
        result = None
    else:
        print(f"❌ Unknown method: {method}")
        print("Use 'options' to see all available methods")
        sys.exit(1)
    
    if result:
        print(f"\n✅ Success! File shared as {model_type.upper()} model")
        return result
    else:
        print("❌ Failed to create shareable link")
        sys.exit(1)

if __name__ == "__main__":
    main()
