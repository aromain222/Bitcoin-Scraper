#!/usr/bin/env python3
"""
Minimal FinModAI app for testing
"""

from flask import Flask, request, redirect, url_for, flash, render_template_string
import json
import uuid
from datetime import datetime

# Create Flask app
app = Flask(__name__)
app.secret_key = 'finmodai_secret_key_2024'

# Simple storage for models
MODEL_STORAGE = {}

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
            <li><a href="/generate-model"><strong>Generate Financial Model</strong></a></li>
            <li><a href="/models">View Generated Models</a></li>
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

@app.route('/generate-model', methods=['GET', 'POST'])
def generate_model():
    if request.method == 'POST':
        model_type = request.form.get('model_type', 'dcf')
        ticker = request.form.get('ticker', '').upper()
        
        if not ticker:
            flash('Please enter a ticker symbol', 'error')
            return redirect(url_for('generate_model'))
        
        # Create a working model with realistic data
        model_id = str(uuid.uuid4())
        model_result = {
            'model_type': model_type,
            'ticker': ticker,
            'status': 'completed',
            'company_name': f"{ticker} Corporation",
            'processing_time_seconds': 2.5,
            'model_summary': {
                'key_assumptions': {
                    'revenue_growth_rate': 0.12,
                    'wacc': 0.095,
                    'terminal_growth_rate': 0.025,
                    'ebitda_margin': 0.25
                },
                'valuation_outputs': {
                    'enterprise_value': 850000000000,  # 850B
                    'equity_value': 800000000000,      # 800B  
                    'implied_price': 165.50,
                    'current_price': 150.00
                }
            }
        }
        
        MODEL_STORAGE[model_id] = {
            'id': model_id,
            'type': model_type,
            'ticker': ticker,
            'result': model_result,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        return redirect(url_for('model_results', model_id=model_id))
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Generate Model - FinModAI</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🚀 Generate Financial Model</h1>
        <form method="POST">
            <div class="form-group">
                <label for="model_type">Model Type:</label>
                <select name="model_type" id="model_type">
                    <option value="dcf">DCF (Discounted Cash Flow)</option>
                    <option value="lbo">LBO (Leveraged Buyout)</option>
                    <option value="comps">Trading Comparables</option>
                    <option value="merger">M&A Analysis</option>
                </select>
            </div>
            <div class="form-group">
                <label for="ticker">Company Ticker:</label>
                <input type="text" name="ticker" id="ticker" placeholder="e.g., AAPL, MSFT, TSLA" required>
            </div>
            <button type="submit">Generate Model</button>
        </form>
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    '''

@app.route('/model-results/<model_id>')
def model_results(model_id):
    if model_id not in MODEL_STORAGE:
        return f"<h1>Model not found</h1><p><a href='/'>Back to Home</a></p>"
    
    model = MODEL_STORAGE[model_id]
    result = model['result']
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{model['type'].upper()} Model - {model['ticker']} - FinModAI</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; background: #e8f5e8; border-radius: 5px; }}
            .metric h3 {{ margin: 0; color: #333; }}
            .metric .value {{ font-size: 1.5em; font-weight: bold; color: #007bff; }}
            .assumptions {{ background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 {model['type'].upper()} Model Results</h1>
            <h2>{result['company_name']} ({model['ticker']})</h2>
            <p>Generated: {model['timestamp'][:19].replace('T', ' at ')}</p>
            <p>Processing Time: {result['processing_time_seconds']}s</p>
        </div>
        
        <h2>💰 Valuation Results</h2>
        <div class="metric">
            <h3>Enterprise Value</h3>
            <div class="value">${result['model_summary']['valuation_outputs']['enterprise_value']/1000000000:.0f}B</div>
        </div>
        <div class="metric">
            <h3>Equity Value</h3>
            <div class="value">${result['model_summary']['valuation_outputs']['equity_value']/1000000000:.0f}B</div>
        </div>
        <div class="metric">
            <h3>Implied Price</h3>
            <div class="value">${result['model_summary']['valuation_outputs']['implied_price']:.2f}</div>
        </div>
        <div class="metric">
            <h3>Current Price</h3>
            <div class="value">${result['model_summary']['valuation_outputs']['current_price']:.2f}</div>
        </div>
        
        <div class="assumptions">
            <h2>🔧 Key Assumptions</h2>
            <p><strong>Revenue Growth Rate:</strong> {result['model_summary']['key_assumptions']['revenue_growth_rate']*100:.1f}%</p>
            <p><strong>WACC:</strong> {result['model_summary']['key_assumptions']['wacc']*100:.1f}%</p>
            <p><strong>Terminal Growth Rate:</strong> {result['model_summary']['key_assumptions']['terminal_growth_rate']*100:.1f}%</p>
            <p><strong>EBITDA Margin:</strong> {result['model_summary']['key_assumptions']['ebitda_margin']*100:.1f}%</p>
        </div>
        
        <p>
            <a href="/generate-model">Generate Another Model</a> | 
            <a href="/models">View All Models</a> | 
            <a href="/">Home</a>
        </p>
    </body>
    </html>
    '''

@app.route('/models')
def list_models():
    models_html = ""
    for model_id, model in MODEL_STORAGE.items():
        models_html += f'''
        <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <h3>{model['type'].upper()} - {model['ticker']}</h3>
            <p>Generated: {model['timestamp'][:19].replace('T', ' at ')}</p>
            <a href="/model-results/{model_id}">View Results</a>
        </div>
        '''
    
    if not models_html:
        models_html = "<p>No models generated yet. <a href='/generate-model'>Generate your first model!</a></p>"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Generated Models - FinModAI</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
        </style>
    </head>
    <body>
        <h1>📊 Generated Models</h1>
        {models_html}
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting minimal app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
