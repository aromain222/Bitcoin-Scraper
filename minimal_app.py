#!/usr/bin/env python3
"""
Minimal FinModAI app for testing
"""

from flask import Flask

# Create minimal Flask app
app = Flask(__name__)
app.secret_key = 'test_key'

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FinModAI - Minimal Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .status { background: #e8f5e8; padding: 20px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🚀 FinModAI - Minimal Version</h1>
        <div class="status">
            <h2>✅ App is running successfully!</h2>
            <p>This minimal version loads instantly and works reliably.</p>
        </div>
        
        <h2>Available Pages:</h2>
        <ul>
            <li><a href="/ping">Ping Test</a></li>
            <li><a href="/status">Status</a></li>
            <li><a href="/test">Simple Test</a></li>
        </ul>
        
        <h2>Next Steps:</h2>
        <ol>
            <li>Confirm this loads quickly</li>
            <li>Add features back gradually</li>
            <li>Identify what was causing the slowness</li>
        </ol>
    </body>
    </html>
    """

@app.route('/ping')
def ping():
    return "pong"

@app.route('/status')
def status():
    import os
    return {
        "status": "running",
        "port": os.environ.get('PORT', 'not_set'),
        "app": "minimal_finmodai"
    }

@app.route('/test')
def test():
    return "Minimal FinModAI Test - Working!"

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting minimal app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
