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
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IB Modeling Assistant - Professional Financial Models</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        },
                        fontFamily: {
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/models" class="text-sm text-navy hover:text-navy/80 font-medium">View Models</a>
                        <a href="/status" class="text-sm text-gray-600 hover:text-gray-800">Status</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="grid grid-cols-12 gap-6">
                <!-- Input Panel -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="bg-gray-50 rounded-xl p-6 shadow-sm">
                        <h2 class="text-lg font-semibold text-gray-900 mb-4">Model Selection</h2>
                        
                        <!-- Model Tabs -->
                        <div class="mb-6">
                            <div class="flex flex-wrap gap-2" role="tablist">
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-navy text-white" role="tab" onclick="setActiveModel('dcf')">DCF</button>
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors" role="tab" onclick="setActiveModel('lbo')">LBO</button>
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors" role="tab" onclick="setActiveModel('merger')">Merger</button>
                                <button class="px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors" role="tab" onclick="setActiveModel('comps')">Comps</button>
                            </div>
                        </div>

                        <!-- Quick Start -->
                        <div class="bg-white rounded-xl p-4 border border-gray-200 mb-4">
                            <h3 class="font-medium text-gray-900 mb-3">Quick Start</h3>
                            <a href="/generate-model" class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors inline-block text-center">
                                Generate Model
                            </a>
                        </div>

                        <!-- Status -->
                        <div class="bg-white rounded-xl p-4 border border-gray-200">
                            <div class="flex items-center">
                                <div class="w-2 h-2 bg-success rounded-full mr-3"></div>
                                <span class="text-sm font-medium text-gray-900">System Ready</span>
                            </div>
                            <p class="text-xs text-gray-600 mt-1">Ready to generate banker-formatted Excel models</p>
                        </div>
                    </div>
                </div>

                <!-- Output Panel -->
                <div class="col-span-12 lg:col-span-8">
                    <div class="space-y-6">
                        <!-- Welcome Card -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h2 class="text-xl font-semibold text-gray-900 mb-2">Professional Financial Modeling Platform</h2>
                            <p class="text-gray-600 mb-4">Create investment-grade financial models with institutional-quality formatting and analysis.</p>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                <div class="bg-success-bg rounded-lg p-4">
                                    <h3 class="font-medium text-success mb-1">DCF Models</h3>
                                    <p class="text-sm text-gray-600">Discounted cash flow analysis with sensitivity tables</p>
                                </div>
                                <div class="bg-blue-50 rounded-lg p-4">
                                    <h3 class="font-medium text-blue-700 mb-1">LBO Models</h3>
                                    <p class="text-sm text-gray-600">Leveraged buyout modeling with returns analysis</p>
                                </div>
                                <div class="bg-purple-50 rounded-lg p-4">
                                    <h3 class="font-medium text-purple-700 mb-1">M&A Models</h3>
                                    <p class="text-sm text-gray-600">Merger analysis with accretion/dilution</p>
                                </div>
                                <div class="bg-orange-50 rounded-lg p-4">
                                    <h3 class="font-medium text-orange-700 mb-1">Comps Analysis</h3>
                                    <p class="text-sm text-gray-600">Trading and transaction comparables</p>
                                </div>
                            </div>
                        </div>

                        <!-- Key Features -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">Platform Features</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="text-center">
                                    <div class="w-12 h-12 bg-navy/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                                        <svg class="w-6 h-6 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                        </svg>
                                    </div>
                                    <h4 class="font-medium text-gray-900 mb-1">Professional Output</h4>
                                    <p class="text-sm text-gray-600">Investment-grade Excel formatting</p>
                                </div>
                                <div class="text-center">
                                    <div class="w-12 h-12 bg-success/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                                        <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                        </svg>
                                    </div>
                                    <h4 class="font-medium text-gray-900 mb-1">Fast Generation</h4>
                                    <p class="text-sm text-gray-600">Models ready in seconds</p>
                                </div>
                                <div class="text-center">
                                    <div class="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mx-auto mb-3">
                                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                    </div>
                                    <h4 class="font-medium text-gray-900 mb-1">Validated Models</h4>
                                    <p class="text-sm text-gray-600">Industry-standard methodologies</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function setActiveModel(model) {
                // Update active tab styling
                const tabs = document.querySelectorAll('[role="tab"]');
                tabs.forEach(tab => {
                    if (tab.textContent.toLowerCase() === model.toLowerCase()) {
                        tab.className = 'px-3 py-2 text-sm font-medium rounded-lg bg-navy text-white';
                    } else {
                        tab.className = 'px-3 py-2 text-sm font-medium rounded-lg bg-white text-navy border border-navy hover:bg-navy hover:text-white transition-colors';
                    }
                });
            }
        </script>
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
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generate Model - IB Modeling Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        },
                        fontFamily: {
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/" class="text-sm text-navy hover:text-navy/80 font-medium">Home</a>
                        <a href="/models" class="text-sm text-navy hover:text-navy/80 font-medium">View Models</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="grid grid-cols-12 gap-6">
                <!-- Input Panel -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="bg-gray-50 rounded-xl p-6 shadow-sm sticky top-8">
                        <h2 class="text-lg font-semibold text-gray-900 mb-6">Model Configuration</h2>
                        
                        <form method="POST" class="space-y-6">
                            <!-- Operating Assumptions -->
                            <div class="bg-white rounded-xl p-4 border border-gray-200">
                                <h3 class="font-medium text-gray-900 mb-4 flex items-center">
                                    <svg class="w-5 h-5 text-navy mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                    </svg>
                                    Operating Assumptions
                                </h3>
                                
                                <div class="space-y-4">
                                    <div>
                                        <label for="model_type" class="block text-sm font-medium text-gray-700 mb-2">Model Type</label>
                                        <select name="model_type" id="model_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-navy">
                                            <option value="dcf">DCF (Discounted Cash Flow)</option>
                                            <option value="lbo">LBO (Leveraged Buyout)</option>
                                            <option value="comps">Trading Comparables</option>
                                            <option value="merger">M&A Analysis</option>
                                        </select>
                                    </div>
                                    
                                    <div>
                                        <label for="ticker" class="block text-sm font-medium text-gray-700 mb-2">Company Ticker</label>
                                        <input type="text" name="ticker" id="ticker" placeholder="e.g., AAPL, MSFT, TSLA" required
                                               class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-navy uppercase">
                                    </div>
                                </div>
                            </div>

                            <!-- Market Data -->
                            <div class="bg-white rounded-xl p-4 border border-gray-200">
                                <h3 class="font-medium text-gray-900 mb-4 flex items-center">
                                    <svg class="w-5 h-5 text-navy mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                                    </svg>
                                    Market Data
                                </h3>
                                <p class="text-xs text-gray-600 mb-3">Real-time data will be fetched automatically</p>
                                
                                <!-- Preset Pills -->
                                <div class="flex gap-2 mb-4">
                                    <button type="button" class="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors">Base Case</button>
                                    <button type="button" class="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors">Bull Case</button>
                                    <button type="button" class="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors">Bear Case</button>
                                </div>
                            </div>

                            <!-- Generate Button -->
                            <button type="submit" class="w-full bg-navy text-white px-6 py-3 rounded-lg font-medium hover:bg-navy/90 transition-colors flex items-center justify-center">
                                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                </svg>
                                Generate Model
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Output Panel -->
                <div class="col-span-12 lg:col-span-8">
                    <div class="space-y-6">
                        <!-- Status -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <div class="flex items-center justify-between mb-4">
                                <h2 class="text-lg font-semibold text-gray-900">Model Generation</h2>
                                <div class="flex items-center">
                                    <div class="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                                    <span class="text-sm text-gray-600">Ready to generate</span>
                                </div>
                            </div>
                            <p class="text-gray-600">Select a model type and enter a company ticker to generate a banker-formatted Excel model.</p>
                        </div>

                        <!-- Instructions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">How It Works</h3>
                            <div class="space-y-4">
                                <div class="flex items-start">
                                    <div class="w-8 h-8 bg-navy/10 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                        <span class="text-sm font-medium text-navy">1</span>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-gray-900">Select Model Type</h4>
                                        <p class="text-sm text-gray-600">Choose from DCF, LBO, M&A, or Comparables analysis</p>
                                    </div>
                                </div>
                                <div class="flex items-start">
                                    <div class="w-8 h-8 bg-navy/10 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                        <span class="text-sm font-medium text-navy">2</span>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-gray-900">Enter Company Ticker</h4>
                                        <p class="text-sm text-gray-600">Input the stock symbol (e.g., AAPL, MSFT, TSLA)</p>
                                    </div>
                                </div>
                                <div class="flex items-start">
                                    <div class="w-8 h-8 bg-navy/10 rounded-full flex items-center justify-center mr-3 mt-0.5">
                                        <span class="text-sm font-medium text-navy">3</span>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-gray-900">Generate & Download</h4>
                                        <p class="text-sm text-gray-600">Get a professional Excel model ready for analysis</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
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
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{model['type'].upper()} Model - {model['ticker']} - IB Modeling Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        }},
                        fontFamily: {{
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/" class="text-sm text-navy hover:text-navy/80 font-medium">Home</a>
                        <a href="/models" class="text-sm text-navy hover:text-navy/80 font-medium">View Models</a>
                        <a href="/generate-model" class="text-sm text-navy hover:text-navy/80 font-medium">Generate</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Success Banner -->
            <div class="bg-success-bg border border-success/20 rounded-xl p-4 mb-6">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-success mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div>
                        <h3 class="font-medium text-success">Model Generated Successfully</h3>
                        <p class="text-sm text-success/80">{model['type'].upper()} model for {result['company_name']} completed in {result['processing_time_seconds']}s</p>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-12 gap-6">
                <!-- Left Panel - Model Info -->
                <div class="col-span-12 lg:col-span-4">
                    <div class="space-y-6">
                        <!-- Model Header -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <div class="flex items-center mb-4">
                                <div class="w-12 h-12 bg-navy/10 rounded-lg flex items-center justify-center mr-4">
                                    <svg class="w-6 h-6 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h2 class="text-lg font-semibold text-gray-900">{model['type'].upper()} Model</h2>
                                    <p class="text-sm text-gray-600">{result['company_name']} ({model['ticker']})</p>
                                </div>
                            </div>
                            <div class="text-xs text-gray-500">
                                <p>Generated: {model['timestamp'][:19].replace('T', ' at ')}</p>
                            </div>
                        </div>

                        <!-- Download Card -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Your Excel Model</h3>
                            <div class="bg-gray-50 rounded-lg p-3 mb-4">
                                <p class="text-sm font-mono text-gray-700">{model['type'].upper()}_{model['ticker']}_2025-09-29.xlsx</p>
                            </div>
                            <button class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors flex items-center justify-center">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                Download Excel
                            </button>
                        </div>

                        <!-- Key Assumptions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Key Assumptions</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between">
                                    <span class="text-sm text-gray-600">Revenue Growth</span>
                                    <span class="text-sm font-medium text-gray-900">{result['model_summary']['key_assumptions']['revenue_growth_rate']*100:.1f}%</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-gray-600">WACC</span>
                                    <span class="text-sm font-medium text-gray-900">{result['model_summary']['key_assumptions']['wacc']*100:.1f}%</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-gray-600">Terminal Growth</span>
                                    <span class="text-sm font-medium text-gray-900">{result['model_summary']['key_assumptions']['terminal_growth_rate']*100:.1f}%</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-sm text-gray-600">EBITDA Margin</span>
                                    <span class="text-sm font-medium text-gray-900">{result['model_summary']['key_assumptions']['ebitda_margin']*100:.1f}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Panel - Valuation Results -->
                <div class="col-span-12 lg:col-span-8">
                    <div class="space-y-6">
                        <!-- Key Outputs -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h2 class="text-lg font-semibold text-gray-900 mb-6">Valuation Results</h2>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="bg-success-bg rounded-lg p-4 text-center">
                                    <h3 class="text-sm font-medium text-success mb-2">Enterprise Value</h3>
                                    <div class="text-2xl font-bold text-success">${result['model_summary']['valuation_outputs']['enterprise_value']/1000000000:.0f}B</div>
                                </div>
                                <div class="bg-success-bg rounded-lg p-4 text-center">
                                    <h3 class="text-sm font-medium text-success mb-2">Equity Value</h3>
                                    <div class="text-2xl font-bold text-success">${result['model_summary']['valuation_outputs']['equity_value']/1000000000:.0f}B</div>
                                </div>
                                <div class="bg-blue-50 rounded-lg p-4 text-center">
                                    <h3 class="text-sm font-medium text-blue-700 mb-2">Implied Price</h3>
                                    <div class="text-2xl font-bold text-blue-700">${result['model_summary']['valuation_outputs']['implied_price']:.2f}</div>
                                </div>
                                <div class="bg-gray-50 rounded-lg p-4 text-center">
                                    <h3 class="text-sm font-medium text-gray-700 mb-2">Current Price</h3>
                                    <div class="text-2xl font-bold text-gray-700">${result['model_summary']['valuation_outputs']['current_price']:.2f}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
                            <h3 class="font-medium text-gray-900 mb-4">Next Steps</h3>
                            <div class="flex flex-wrap gap-3">
                                <a href="/generate-model" class="bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors">
                                    Generate Another Model
                                </a>
                                <a href="/models" class="bg-white text-navy border border-navy px-4 py-2 rounded-lg font-medium hover:bg-navy hover:text-white transition-colors">
                                    View All Models
                                </a>
                                <a href="/" class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors">
                                    Home
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/models')
def list_models():
    models_html = ""
    for model_id, model in MODEL_STORAGE.items():
        models_html += f'''
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div class="flex items-center mb-4">
                <div class="w-10 h-10 bg-navy/10 rounded-lg flex items-center justify-center mr-3">
                    <svg class="w-5 h-5 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                </div>
                <div>
                    <h3 class="font-semibold text-gray-900">{model['type'].upper()} Model</h3>
                    <p class="text-sm text-gray-600">{model['ticker']}</p>
                </div>
            </div>
            <div class="mb-4">
                <div class="text-xs text-gray-500 mb-2">Generated: {model['timestamp'][:19].replace('T', ' at ')}</div>
                <div class="flex items-center">
                    <div class="w-2 h-2 bg-success rounded-full mr-2"></div>
                    <span class="text-sm text-success font-medium">Completed</span>
                </div>
            </div>
            <a href="/model-results/{model_id}" class="w-full bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors inline-block text-center">
                View Results
            </a>
        </div>
        '''
    
    if not models_html:
        models_html = '''
        <div class="col-span-full">
            <div class="bg-white rounded-xl p-12 shadow-sm border border-gray-200 text-center">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No models generated yet</h3>
                <p class="text-gray-600 mb-6">Get started by creating your first financial model</p>
                <a href="/generate-model" class="bg-navy text-white px-6 py-3 rounded-lg font-medium hover:bg-navy/90 transition-colors inline-flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                    </svg>
                    Generate Your First Model
                </a>
            </div>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="en" class="h-full">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Models - IB Modeling Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {{
                theme: {{
                    extend: {{
                        colors: {{
                            'navy': '#1F4E79',
                            'success': '#2E7D32',
                            'success-bg': '#E8F5E9'
                        }},
                        fontFamily: {{
                            'inter': ['Inter', 'system-ui', 'sans-serif']
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body class="h-full bg-white font-inter">
        <!-- Top Bar -->
        <header class="bg-white border-b border-gray-200 shadow-sm">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div>
                        <h1 class="text-xl font-semibold text-gray-900">IB Modeling Assistant</h1>
                        <p class="text-sm text-gray-600">Generate banker-formatted Excel models</p>
                    </div>
                    <div class="flex space-x-4">
                        <a href="/" class="text-sm text-navy hover:text-navy/80 font-medium">Home</a>
                        <a href="/generate-model" class="text-sm text-navy hover:text-navy/80 font-medium">Generate</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-gray-900">Generated Models</h2>
                <a href="/generate-model" class="bg-navy text-white px-4 py-2 rounded-lg font-medium hover:bg-navy/90 transition-colors">
                    Generate New Model
                </a>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {models_html}
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting minimal app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
