#!/usr/bin/env python3
"""
FinModAI Professional Web Interface
Complete financial modeling platform with data input, model generation, and analysis
"""

import os
import sys
import json
import uuid
from datetime import datetime
from flask import Flask, render_template_string, request, send_file, flash, redirect, url_for, session, jsonify
import threading
import time
from io import BytesIO
import zipfile
import tempfile
# Lazy import pandas to speed up startup
pd = None

def get_pandas():
    """Lazy load pandas when needed"""
    global pd
    if pd is None:
        import pandas as pandas_module
        pd = pandas_module
    return pd
import shutil

# Lazy import FinModAI platform to speed up startup
FinModAIPlatform = None
DataIngestionEngine = None
PlatformConfig = None

def get_finmodai_platform():
    """Lazy load FinModAI platform when needed"""
    global FinModAIPlatform
    if FinModAIPlatform is None:
        try:
            from finmodai_platform import FinModAIPlatform as FMP
            FinModAIPlatform = FMP
            print("✅ FinModAI Platform loaded")
        except ImportError as e:
            print(f"⚠️ FinModAI Platform not available: {e}")
    return FinModAIPlatform

def get_data_ingestion():
    """Lazy load data ingestion when needed"""
    global DataIngestionEngine, PlatformConfig
    if DataIngestionEngine is None:
        try:
            from finmodai.data_ingestion import DataIngestionEngine as DIE
            from finmodai_platform import PlatformConfig as PC
            DataIngestionEngine = DIE
            PlatformConfig = PC
            print("✅ Data ingestion loaded")
        except ImportError as e:
            print(f"⚠️ Data ingestion not available: {e}")
    return DataIngestionEngine, PlatformConfig

# Create data storage
DATA_STORAGE = {}
MODEL_STORAGE = {}

# Application startup state
APP_READY = True  # Start as ready for basic health checks

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'finmodai_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists - but don't fail startup if this fails
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('generated_models', exist_ok=True)
    print("✅ Directories created successfully")
except Exception as e:
    print(f"⚠️ Directory creation warning: {e}")
    # Don't fail startup for directory issues

print("🚀 Flask app initialized - ready for requests")

# Memory management
import gc
gc.set_threshold(700, 10, 10)  # More aggressive garbage collection

# Add error handler for uncaught exceptions
@app.errorhandler(500)
def internal_error(error):
    print(f"❌ Internal server error: {error}")
    return "Internal Server Error - Check logs for details", 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Unhandled exception: {e}")
    import traceback
    traceback.print_exc()
    return "Application Error - Check logs for details", 500

# HTML Templates for the web interface
MAIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinModAI - Investment Banking Platform</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-navy: #1a365d;
            --secondary-navy: #2d3748;
            --accent-gold: #d4af37;
            --light-gray: #f7fafc;
            --medium-gray: #e2e8f0;
            --dark-gray: #4a5568;
            --text-primary: #2d3748;
            --text-secondary: #718096;
            --white: #ffffff;
            --success-green: #38a169;
            --warning-orange: #ed8936;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--light-gray);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .navbar {
            background: var(--white);
            border-bottom: 1px solid var(--medium-gray);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 72px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary-navy);
            letter-spacing: -0.5px;
        }
        
        .logo i {
            color: var(--accent-gold);
            margin-right: 8px;
        }
        
        .nav-links {
            display: flex;
            gap: 8px;
        }
        
        .nav-link {
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
            padding: 12px 20px;
            border-radius: 6px;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .nav-link:hover, .nav-link.active {
            background: var(--primary-navy);
            color: var(--white);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 96px 24px 40px;
        }
        
        .hero-section {
            background: var(--white);
            border-radius: 12px;
            border: 1px solid var(--medium-gray);
            padding: 48px;
            text-align: center;
            margin-bottom: 48px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .hero-section h1 {
            font-size: 48px;
            font-weight: 700;
            color: var(--primary-navy);
            margin-bottom: 16px;
            letter-spacing: -1px;
        }
        
        .hero-section .subtitle {
            font-size: 20px;
            color: var(--text-secondary);
            margin-bottom: 32px;
            font-weight: 400;
        }
        
        .cta-buttons {
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 14px 28px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-width: 160px;
            justify-content: center;
        }
        
        .btn-primary {
            background: var(--primary-navy);
            color: var(--white);
            border: 2px solid var(--primary-navy);
        }
        
        .btn-primary:hover {
            background: var(--secondary-navy);
            border-color: var(--secondary-navy);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(26, 54, 93, 0.3);
        }
        
        .btn-secondary {
            background: var(--white);
            color: var(--primary-navy);
            border: 2px solid var(--primary-navy);
        }
        
        .btn-secondary:hover {
            background: var(--primary-navy);
            color: var(--white);
            transform: translateY(-1px);
        }
        
        .features-section {
            margin-bottom: 48px;
        }
        
        .section-title {
            font-size: 32px;
            font-weight: 700;
            color: var(--primary-navy);
            text-align: center;
            margin-bottom: 48px;
            letter-spacing: -0.5px;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
        }
        
        .feature-card {
            background: var(--white);
            border: 1px solid var(--medium-gray);
            border-radius: 12px;
            padding: 32px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: var(--accent-gold);
        }
        
        .feature-icon {
            width: 48px;
            height: 48px;
            background: var(--primary-navy);
            color: var(--white);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-bottom: 20px;
        }
        
        .feature-card h3 {
            font-size: 20px;
            font-weight: 600;
            color: var(--primary-navy);
            margin-bottom: 12px;
            letter-spacing: -0.25px;
        }
        
        .feature-card p {
            color: var(--text-secondary);
            line-height: 1.6;
            font-size: 16px;
        }
        
        .stats-section {
            background: var(--primary-navy);
            color: var(--white);
            border-radius: 12px;
            padding: 48px;
            text-align: center;
            margin-bottom: 48px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 32px;
            margin-top: 32px;
        }
        
        .stat-item h4 {
            font-size: 36px;
            font-weight: 700;
            color: var(--accent-gold);
            margin-bottom: 8px;
        }
        
        .stat-item p {
            font-size: 14px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        @media (max-width: 768px) {
            .hero-section {
                padding: 32px 24px;
            }
            
            .hero-section h1 {
                font-size: 36px;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
            
            .cta-buttons {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-university"></i>FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link active">Dashboard</a>
                <a href="/company-data" class="nav-link">Data Management</a>
                <a href="/generate-model" class="nav-link">Model Builder</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="hero-section">
            <h1>Investment Banking Platform</h1>
            <p class="subtitle">Professional-grade financial modeling and valuation tools for investment professionals</p>
            <div class="cta-buttons">
                <a href="/generate-model" class="btn btn-primary">
                    <i class="fas fa-calculator"></i>Build Models
                </a>
                <a href="/company-data" class="btn btn-secondary">
                    <i class="fas fa-database"></i>Data Center
                </a>
            </div>
        </div>

        <div class="stats-section">
            <h2 style="font-size: 28px; margin-bottom: 16px;">Trusted by Finance Professionals</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <h4>14+</h4>
                    <p>Data Sources</p>
                </div>
                <div class="stat-item">
                    <h4>5</h4>
                    <p>Model Types</p>
                </div>
                <div class="stat-item">
                    <h4>100%</h4>
                    <p>Excel Compatible</p>
                </div>
                <div class="stat-item">
                    <h4>Real-time</h4>
                    <p>Market Data</p>
                </div>
            </div>
        </div>

        <div class="features-section">
            <h2 class="section-title">Professional Financial Modeling Suite</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h3>DCF Valuation Models</h3>
                    <p>Build comprehensive discounted cash flow models with automated WACC calculations, terminal value analysis, and sensitivity testing. Industry-standard methodologies used by top-tier investment banks.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-building"></i>
                    </div>
                    <h3>LBO & M&A Analysis</h3>
                    <p>Leveraged buyout modeling with debt capacity analysis, returns calculations, and transaction structuring. Complete merger models with accretion/dilution analysis and synergy valuations.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-balance-scale"></i>
                    </div>
                    <h3>Comparable Company Analysis</h3>
                    <p>Automated trading and transaction comparables with peer group selection, multiple analysis, and benchmarking. Real-time market data integration for accurate valuations.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-file-invoice-dollar"></i>
                    </div>
                    <h3>3-Statement Financial Models</h3>
                    <p>Integrated income statement, balance sheet, and cash flow models with automatic balancing, working capital analysis, and debt scheduling capabilities.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <h3>AI-Powered Assumptions</h3>
                    <p>Intelligent assumption generation based on industry benchmarks, company fundamentals, and market conditions. Reduces modeling time while maintaining accuracy.</p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-download"></i>
                    </div>
                    <h3>Excel Integration</h3>
                    <p>Professional Excel outputs with proper formatting, formulas, and documentation. Fully auditable models that meet institutional standards and compliance requirements.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

COMPANY_DATA_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Data Management - FinModAI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        .navbar {
            background: #667eea;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }
        .nav-links {
            display: flex;
            gap: 2rem;
        }
        .nav-link {
            color: white;
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        .nav-link:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .page-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .page-header h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .form-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .form-section h2 {
            color: #333;
            margin-bottom: 25px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        .data-table {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        .data-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .data-table th,
        .data-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        .data-table th {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-chart-line"></i> FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/company-data" class="nav-link">Company Data</a>
                <a href="/generate-model" class="nav-link">Model Generation</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="page-header">
            <h1><i class="fas fa-database"></i> Company Data Management</h1>
            <p>Input and manage company financial data for custom modeling</p>
        </div>

        <div class="form-section">
            <h2><i class="fas fa-edit"></i> Manual Company Data Entry</h2>
            <form method="POST" action="/company-data">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="company_name">Company Name *</label>
                        <input type="text" id="company_name" name="company_name" required placeholder="e.g., Apple Inc.">
                    </div>
                    <div class="form-group">
                        <label for="ticker">Stock Ticker *</label>
                        <input type="text" id="ticker" name="ticker" required placeholder="e.g., AAPL">
                    </div>
                    <div class="form-group">
                        <label for="sector">Sector</label>
                        <select id="sector" name="sector">
                            <option value="">Select Sector</option>
                            <option value="Technology">Technology</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Financial Services">Financial Services</option>
                            <option value="Consumer Cyclical">Consumer Cyclical</option>
                            <option value="Industrials">Industrials</option>
                            <option value="Energy">Energy</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="revenue">Revenue ($M)</label>
                        <input type="number" id="revenue" name="revenue" step="0.01" placeholder="e.g., 365817">
                    </div>
                    <div class="form-group">
                        <label for="ebitda">EBITDA ($M)</label>
                        <input type="number" id="ebitda" name="ebitda" step="0.01" placeholder="e.g., 123136">
                    </div>
                    <div class="form-group">
                        <label for="net_income">Net Income ($M)</label>
                        <input type="number" id="net_income" name="net_income" step="0.01" placeholder="e.g., 99803">
                    </div>
                    <div class="form-group">
                        <label for="beta">Beta</label>
                        <input type="number" id="beta" name="beta" step="0.01" value="1.20" placeholder="e.g., 1.20">
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> Save Company Data
                </button>
            </form>
        </div>

        <div class="form-section">
            <h2><i class="fas fa-list"></i> Saved Company Data</h2>
            <div class="data-table">
                <table>
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>Ticker</th>
                            <th>Sector</th>
                            <th>Revenue ($M)</th>
                            <th>EBITDA ($M)</th>
                            <th>Source</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for company in companies %}
                        <tr>
                            <td><strong>{{ company.name }}</strong></td>
                            <td><span style="color: #667eea; font-weight: 500;">{{ company.ticker }}</span></td>
                            <td>{{ company.sector }}</td>
                            <td>{{ "{:,.0f}".format(company.revenue) if company.revenue else "-" }}</td>
                            <td>{{ "{:,.0f}".format(company.ebitda) if company.ebitda else "-" }}</td>
                            <td><span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">Manual</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

MODEL_GENERATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Builder - FinModAI Investment Banking Platform</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-navy: #1a365d;
            --secondary-navy: #2d3748;
            --accent-gold: #d4af37;
            --light-gray: #f7fafc;
            --medium-gray: #e2e8f0;
            --dark-gray: #4a5568;
            --text-primary: #2d3748;
            --text-secondary: #718096;
            --white: #ffffff;
            --success-green: #38a169;
            --warning-orange: #ed8936;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--light-gray);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .navbar {
            background: var(--white);
            border-bottom: 1px solid var(--medium-gray);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 72px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary-navy);
            letter-spacing: -0.5px;
        }
        
        .logo i {
            color: var(--accent-gold);
            margin-right: 8px;
        }
        
        .nav-links {
            display: flex;
            gap: 8px;
        }
        
        .nav-link {
            text-decoration: none;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 14px;
            padding: 12px 20px;
            border-radius: 6px;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .nav-link:hover, .nav-link.active {
            background: var(--primary-navy);
            color: var(--white);
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px;
        }
        
        .page-header {
            text-align: center;
            margin-bottom: 48px;
        }
        
        .page-header h1 {
            font-size: 42px;
            font-weight: 700;
            color: var(--primary-navy);
            margin-bottom: 16px;
            letter-spacing: -1px;
        }
        
        .page-header p {
            font-size: 18px;
            color: var(--text-secondary);
            font-weight: 400;
        }
        
        .form-section {
            background: var(--white);
            border: 1px solid var(--medium-gray);
            border-radius: 12px;
            padding: 48px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .section-title {
            font-size: 24px;
            font-weight: 600;
            color: var(--primary-navy);
            margin-bottom: 32px;
            display: flex;
            align-items: center;
            gap: 12px;
            letter-spacing: -0.25px;
        }
        
        .form-group {
            margin-bottom: 32px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 12px;
            font-weight: 600;
            font-size: 16px;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 14px;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 16px;
            border: 2px solid var(--medium-gray);
            border-radius: 6px;
            font-size: 16px;
            font-family: inherit;
            transition: all 0.2s ease;
            background: var(--white);
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--primary-navy);
            box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
        }
        
        .btn {
            padding: 16px 32px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: inherit;
        }
        
        .btn-primary {
            background: var(--primary-navy);
            color: var(--white);
            border: 2px solid var(--primary-navy);
        }
        
        .btn-primary:hover {
            background: var(--secondary-navy);
            border-color: var(--secondary-navy);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(26, 54, 93, 0.3);
        }
        
        .model-types {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .model-type {
            padding: 24px;
            border: 2px solid var(--medium-gray);
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: var(--white);
        }
        
        .model-type:hover {
            border-color: var(--accent-gold);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .model-type.selected {
            border-color: var(--primary-navy);
            background: var(--primary-navy);
            color: var(--white);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(26, 54, 93, 0.3);
        }
        
        .model-type i {
            font-size: 32px;
            margin-bottom: 16px;
            display: block;
            color: var(--accent-gold);
        }
        
        .model-type.selected i {
            color: var(--accent-gold);
        }
        
        .model-type h3 {
            margin-bottom: 8px;
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.25px;
        }
        
        .model-type small {
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .input-hint {
            color: var(--text-secondary);
            font-size: 14px;
            margin-top: 8px;
            display: block;
        }
        
        .form-actions {
            text-align: center;
            margin-top: 48px;
            padding-top: 32px;
            border-top: 1px solid var(--medium-gray);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 24px 16px;
            }
            
            .form-section {
                padding: 32px 24px;
            }
            
            .model-types {
                grid-template-columns: 1fr;
            }
            
            .page-header h1 {
                font-size: 32px;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-university"></i>FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/company-data" class="nav-link">Data Management</a>
                <a href="/generate-model" class="nav-link active">Model Builder</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="page-header">
            <h1>Financial Model Builder</h1>
            <p>Generate institutional-grade financial models with AI-powered analysis</p>
        </div>

        <div class="form-section">
            <h2 class="section-title">
                <i class="fas fa-calculator"></i>Model Configuration
            </h2>
            
            <form method="POST" action="/generate-model" id="modelForm">
                <div class="form-group">
                    <label>Select Model Type</label>
                    <div class="model-types" id="modelTypes">
                        <div class="model-type" data-value="dcf">
                            <i class="fas fa-chart-line"></i>
                            <h3>DCF Model</h3>
                            <small>Discounted Cash Flow</small>
                        </div>
                        <div class="model-type" data-value="lbo">
                            <i class="fas fa-building"></i>
                            <h3>LBO Model</h3>
                            <small>Leveraged Buyout</small>
                        </div>
                        <div class="model-type" data-value="comps">
                            <i class="fas fa-balance-scale"></i>
                            <h3>Comps</h3>
                            <small>Trading Comparables</small>
                        </div>
                        <div class="model-type" data-value="three_statement">
                            <i class="fas fa-file-invoice-dollar"></i>
                            <h3>3-Statement</h3>
                            <small>Financial Statements</small>
                        </div>
                        <div class="model-type" data-value="merger">
                            <i class="fas fa-handshake"></i>
                            <h3>M&A Model</h3>
                            <small>Merger & Acquisition</small>
                        </div>
                    </div>
                    <input type="hidden" name="model_type" id="selectedModelType" required>
                </div>

                <div class="form-group">
                    <label for="use_custom">Data Source</label>
                    <select name="custom_data" id="use_custom">
                        <option value="false">Real-time Market Data (14+ sources)</option>
                        <option value="true">Custom Company Data</option>
                    </select>
                </div>

                <div class="form-group" id="customDataGroup" style="display: none;">
                    <label for="company_id">Select Company</label>
                    <select name="company_id" id="company_id">
                        <option value="">Choose a company...</option>
                        {% for company in companies %}
                        <option value="{{ company.id }}">{{ company.name }} ({{ company.ticker }})</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-group" id="tickerGroup">
                    <label for="ticker">Stock Ticker Symbol</label>
                    <input type="text" id="ticker" name="ticker" placeholder="e.g., AAPL, MSFT, TSLA, GOOGL" required>
                    <span class="input-hint">
                        Enter a valid stock ticker symbol to generate a model using real-time market data
                    </span>
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-rocket"></i> Generate Model
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Model type selection
        const modelTypes = document.querySelectorAll('.model-type');
        const selectedModelTypeInput = document.getElementById('selectedModelType');

        modelTypes.forEach(type => {
            type.addEventListener('click', function() {
                modelTypes.forEach(t => t.classList.remove('selected'));
                this.classList.add('selected');
                selectedModelTypeInput.value = this.dataset.value;
            });
        });

        // Data source toggle
        const useCustomSelect = document.getElementById('use_custom');
        const customDataGroup = document.getElementById('customDataGroup');
        const tickerGroup = document.getElementById('tickerGroup');
        const tickerInput = document.getElementById('ticker');

        useCustomSelect.addEventListener('change', function() {
            if (this.value === 'true') {
                customDataGroup.style.display = 'block';
                tickerGroup.style.display = 'none';
                tickerInput.required = false;
                document.getElementById('company_id').required = true;
            } else {
                customDataGroup.style.display = 'none';
                tickerGroup.style.display = 'block';
                tickerInput.required = true;
                document.getElementById('company_id').required = false;
            }
        });

        // Form validation
        document.getElementById('modelForm').addEventListener('submit', function(e) {
            if (!selectedModelTypeInput.value) {
                e.preventDefault();
                alert('Please select a model type before generating.');
                return false;
            }
        });
    </script>
</body>
</html>
"""

MODEL_RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ model.type.upper() }} Model - {{ model.corrected_ticker if model.corrected_ticker != model.ticker else model.ticker }} - FinModAI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 0;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.8em;
            font-weight: bold;
            color: white;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 30px rgba(0,0,0,0.1);
        }
        .header-card h1 {
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            font-size: 2.5em;
        }
        .header-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .info-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }
        .info-item h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .info-item .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        .model-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .model-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .model-section h2 {
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        .data-table th {
            background: #667eea;
            color: white;
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
        }
        .data-table td {
            padding: 12px 10px;
            border-bottom: 1px solid #eee;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
        .data-table .positive {
            color: #28a745;
        }
        .data-table .negative {
            color: #dc3545;
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        .assumptions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .assumption-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .assumption-item h4 {
            margin-bottom: 8px;
            color: #333;
        }
        .assumption-item .value {
            font-weight: bold;
            color: #667eea;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            margin: 5px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .btn-download {
            background: #17a2b8;
            color: white;
        }
        .btn-download:hover {
            background: #138496;
            transform: translateY(-2px);
        }
        .sensitivity-controls {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .sensitivity-controls h2 {
            margin-bottom: 20px;
            color: #333;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .control-item {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .control-item label {
            font-weight: 600;
            color: #555;
        }
        .control-item input {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        .control-item input:focus {
            outline: none;
            border-color: #667eea;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .model-icon {
            font-size: 1.2em;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .tab {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 600;
            color: #666;
            border-bottom: 3px solid transparent;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }

        @media (max-width: 768px) {
            .model-content {
                grid-template-columns: 1fr;
            }
            .header-info {
                grid-template-columns: 1fr;
            }
            .assumptions-grid {
                grid-template-columns: 1fr;
            }
            .control-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-chart-line"></i> FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="btn btn-secondary">
                    <i class="fas fa-home"></i> Dashboard
                </a>
                <a href="/generate-model" class="btn btn-primary">
                    <i class="fas fa-plus"></i> New Model
                </a>
            </div>
                    </div>
    </nav>

    <div class="container">
        <div class="header-card">
            <h1>
                <i class="fas fa-chart-bar model-icon"></i>
                {{ model.type.upper() }} Model
                <small style="font-size: 0.4em; font-weight: normal; opacity: 0.7;">
                    {{ model.corrected_ticker if model.corrected_ticker != model.ticker else model.ticker }}
                </small>
            </h1>

            <div class="header-info">
                <div class="info-item">
                    <h3><i class="fas fa-calendar"></i> Generated</h3>
                    <div class="value">{{ model.timestamp[:19].replace('T', ' at ') }}</div>
                </div>
                <div class="info-item">
                    <h3><i class="fas fa-check-circle"></i> Status</h3>
                    <div class="value">
                        <span class="status status-success">{{ model.status.title() }}</span>
                    </div>
                </div>
                {% if model.result and model.result.get('company_name') %}
                <div class="info-item">
                    <h3><i class="fas fa-building"></i> Company</h3>
                    <div class="value">{{ model.result.company_name }}</div>
                </div>
                {% endif %}
                {% if model.result and model.result.get('processing_time_seconds') %}
                <div class="info-item">
                    <h3><i class="fas fa-clock"></i> Processing Time</h3>
                    <div class="value">{{ "%.1f"|format(model.result.processing_time_seconds) }}s</div>
                </div>
                {% endif %}
                    </div>

            {% if model.result and model.result.get('output_files') %}
            <div style="text-align: center; margin-top: 20px;">
                <a href="/download/{{ model.id }}" class="btn btn-download">
                    <i class="fas fa-download"></i> Download Excel Model
                </a>
            </div>
            {% endif %}
        </div>

            {% if model.result %}
            {% if model.type == 'dcf' %}
                <!-- DCF Model Specific Content -->
                <div class="model-content">
                    <div class="model-section">
                        <h2><i class="fas fa-chart-line"></i> DCF Valuation</h2>
                        {% if model.result.get('model_summary') and model.result.model_summary.get('valuation_outputs') %}
                        <div class="assumptions-grid">
                            <div class="assumption-item">
                                <h4>Enterprise Value</h4>
                                <div class="value">${{ "%.0f"|format(model.result.model_summary.valuation_outputs.enterprise_value/1000000000) }}B</div>
                            </div>
                            <div class="assumption-item">
                                <h4>Equity Value</h4>
                                <div class="value">${{ "%.0f"|format(model.result.model_summary.valuation_outputs.equity_value/1000000000) }}B</div>
                            </div>
                            <div class="assumption-item">
                                <h4>Implied Price</h4>
                                <div class="value">${{ "%.2f"|format(model.result.model_summary.valuation_outputs.implied_price) }}</div>
                            </div>
                            <div class="assumption-item">
                                <h4>WACC</h4>
                                <div class="value">{{ "%.1f"|format((model.result.model_summary.key_assumptions.wacc*100)) }}%</div>
                            </div>
                        </div>
                        {% endif %}
                    </div>

                    <div class="model-section">
                        <h2><i class="fas fa-cog"></i> Key Assumptions</h2>
                        {% if model.result.get('model_summary') and model.result.model_summary.get('key_assumptions') %}
                        <div class="assumptions-grid">
                            {% for key, value in model.result.model_summary.key_assumptions.items() %}
                                {% if key != 'shares_outstanding' %}
                                <div class="assumption-item">
                                    <h4>{{ key.replace('_', ' ').title() }}</h4>
                                    <div class="value">
                                        {% if 'rate' in key.lower() or 'growth' in key.lower() or 'wacc' in key.lower() %}
                                            {{ "%.1f"|format(value*100) }}%
                                        {% elif value > 1000000 %}
                                            ${{ "%.0f"|format(value/1000000) }}M
                                        {% else %}
                                            {{ "%.2f"|format(value) }}
                                        {% endif %}
                                    </div>
                                </div>
                                {% endif %}
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                </div>

                <div class="model-section">
                    <h2><i class="fas fa-chart-area"></i> Revenue & EBITDA Projections</h2>
                    <div class="chart-container">
                        <canvas id="projectionChart"></canvas>
                    </div>
                </div>

                <div class="model-section">
                    <h2><i class="fas fa-calculator"></i> Sensitivity Analysis</h2>
                    <div class="sensitivity-controls">
                        <div class="control-grid">
                            <div class="control-item">
                                <label for="growthRate">Revenue Growth Rate (%)</label>
                                <input type="range" id="growthRate" min="0" max="50" step="1" value="15" oninput="updateSensitivity()">
                            </div>
                            <div class="control-item">
                                <label for="waccRate">WACC (%)</label>
                                <input type="range" id="waccRate" min="5" max="25" step="0.5" value="10" oninput="updateSensitivity()">
                            </div>
                            <div class="control-item">
                                <label for="terminalGrowth">Terminal Growth (%)</label>
                                <input type="range" id="terminalGrowth" min="0" max="5" step="0.1" value="2.5" oninput="updateSensitivity()">
                            </div>
                        </div>
                        <div style="margin-top: 20px; text-align: center;">
                            <button onclick="resetSensitivity()" class="btn btn-secondary">Reset</button>
                        </div>
                    </div>
                </div>

            {% elif model.type == 'lbo' %}
                <!-- LBO Model Specific Content -->
                <div class="model-section">
                    <h2><i class="fas fa-building"></i> LBO Analysis</h2>
                    <p>Interactive LBO model coming soon!</p>
                </div>

            {% elif model.type == 'comps' %}
                <!-- Comparable Companies Specific Content -->
                <div class="model-section">
                    <h2><i class="fas fa-balance-scale"></i> Trading Comparables</h2>
                    <p>Interactive comparable companies analysis coming soon!</p>
                </div>

            {% elif model.type == 'three_statement' %}
                <!-- 3-Statement Model Specific Content -->
                <div class="model-section">
                    <h2><i class="fas fa-file-alt"></i> Financial Statements</h2>
                    <p>Interactive financial statements coming soon!</p>
                </div>

            {% elif model.type == 'merger' %}
                <!-- M&A Model Specific Content -->
                <div class="model-section">
                    <h2><i class="fas fa-handshake"></i> M&A Analysis</h2>
                    <p>Interactive M&A model coming soon!</p>
                </div>

            {% else %}
                <!-- Generic Model Display -->
                <div class="model-section">
                    <h2><i class="fas fa-chart-bar"></i> Model Results</h2>
                    <div class="assumptions-grid">
                    {% for key, value in model.result.items() %}
                        <div class="assumption-item">
                        <h4>{{ key.replace('_', ' ').title() }}</h4>
                        <div class="value">
                            {% if 'multiple' in key.lower() or 'moic' in key.lower() %}
                                {{ "%.1f"|format(value) }}x
                            {% elif 'price' in key.lower() or 'value' in key.lower() %}
                                ${{ "%.0f"|format(value) if value > 1000000 else "%.2f"|format(value) }}
                            {% elif value|float == value and value > 1000000 %}
                                ${{ "%.0f"|format(value) }}
                            {% elif value|float == value %}
                                {{ "%.2f"|format(value) }}
                            {% else %}
                                {{ value }}
                            {% endif %}
                </div>
                </div>
                    {% endfor %}
                </div>
                </div>
            {% endif %}

            <div style="text-align: center; margin-top: 30px;">
                <a href="/generate-model" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Generate Another Model
                </a>
                <a href="/" class="btn btn-secondary">
                    <i class="fas fa-home"></i> Back to Dashboard
                </a>
            </div>
        {% else %}
            <div class="model-section" style="text-align: center; padding: 60px; color: #666;">
                <i class="fas fa-info-circle" style="font-size: 4em; margin-bottom: 20px; opacity: 0.5;"></i>
                <h2>Model Data Not Available</h2>
                <p>The model was generated but the detailed results are not available yet.</p>
                <p style="margin-top: 20px;">
                    <a href="/generate-model" class="btn btn-primary">Generate New Model</a>
                </p>
        </div>
        {% endif %}
    </div>

    <script>
        // Chart.js configuration for DCF projections
        {% if model.type == 'dcf' and model.result.get('model_summary') and model.result.model_summary.get('calculations') %}
        const projectionData = {
            labels: {{ model.result.model_summary.calculations.revenue_projection|tojson }},
            datasets: [
                {
                    label: 'Revenue ($B)',
                    data: {{ model.result.model_summary.calculations.revenue_projection|tojson }},
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'EBITDA ($B)',
                    data: {{ model.result.model_summary.calculations.ebitda_projection|tojson }},
                    borderColor: 'rgb(40, 167, 69)',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.1,
                    fill: true
                }
            ]
        };

        const config = {
            type: 'line',
            data: projectionData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(1) + 'B';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'DCF Revenue & EBITDA Projections'
                    }
                }
            }
        };

        const projectionChart = new Chart(
            document.getElementById('projectionChart'),
            config
        );
        {% endif %}

        function updateSensitivity() {
            // Update sensitivity analysis in real-time
            const growthRate = document.getElementById('growthRate').value;
            const waccRate = document.getElementById('waccRate').value;
            const terminalGrowth = document.getElementById('terminalGrowth').value;

            // This would make an AJAX call to recalculate the model
            console.log('Sensitivity inputs:', { growthRate, waccRate, terminalGrowth });
        }

        function resetSensitivity() {
            document.getElementById('growthRate').value = 15;
            document.getElementById('waccRate').value = 10;
            document.getElementById('terminalGrowth').value = 2.5;
            updateSensitivity();
        }
    </script>
</body>
</html>
"""

# Main dashboard
@app.route('/')
def dashboard():
    """Main dashboard with navigation to all features"""
    try:
        print("📊 Dashboard endpoint accessed")
        return render_template_string(MAIN_DASHBOARD_HTML)
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        # Return simple fallback instead of error
        return """
        <!DOCTYPE html>
        <html>
        <head><title>FinModAI - Dashboard Error</title></head>
        <body>
            <h1>FinModAI Dashboard</h1>
            <p>Dashboard template failed to load. Using simple fallback.</p>
            <h2>Available Pages:</h2>
            <ul>
                <li><a href="/simple">Simple Test Page</a></li>
                <li><a href="/test-modules">Test Modules</a></li>
                <li><a href="/debug-models">Debug Models</a></li>
                <li><a href="/generate-model">Generate Model</a></li>
                <li><a href="/status">Status</a></li>
            </ul>
            <p><strong>Error:</strong> """ + str(e) + """</p>
        </body>
        </html>
        """

@app.route('/health')
def health_check():
    """Simple health check endpoint for deployment platforms"""
    try:
        if APP_READY:
            return "OK", 200
        else:
            return "Starting", 503
    except Exception as e:
        print(f"Health check error: {e}")
        return "Error", 500

@app.route('/healthz')
def health_check_detailed():
    """Detailed health check endpoint"""
    try:
        return {
            "status": "healthy" if APP_READY else "starting",
            "service": "FinModAI",
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }, 200 if APP_READY else 503
    except Exception as e:
        print(f"Detailed health check error: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/ping')
def ping():
    """Ultra-simple ping endpoint"""
    print("🏓 Ping endpoint hit!")
    return "pong"

@app.route('/simple')
def simple():
    """Ultra-simple HTML page"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>FinModAI - Simple Test</title></head>
    <body>
        <h1>FinModAI is Working!</h1>
        <p>This is a simple test page.</p>
        <a href="/test-modules">Test Modules</a> | 
        <a href="/debug-models">Debug Models</a> |
        <a href="/status">Status</a>
    </body>
    </html>
    """

@app.route('/status')
def status():
    """Simple status endpoint for debugging"""
    try:
        print("📊 Status endpoint hit!")
        return {
            "status": "running",
            "app_ready": APP_READY,
            "port": os.environ.get('PORT', 'not_set'),
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "flask_app": "financial_models_ui"
        }
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return {"error": str(e)}, 500

@app.route('/test')
def test():
    """Ultra-simple test endpoint"""
    try:
        print("🧪 Test endpoint hit!")
        return "FinModAI Test - App is running!"
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
        return f"Test Error: {str(e)}", 500

@app.route('/test-modules')
def test_modules():
    """Test if FinModAI modules are available"""
    try:
        results = {
            "finmodai_platform": False,
            "data_ingestion": False,
            "pandas": False,
            "errors": []
        }
        
        # Test FinModAI platform
        try:
            platform = get_finmodai_platform()
            results["finmodai_platform"] = platform is not None
            if platform:
                # Try to create an instance
                instance = platform()
                results["platform_instance"] = instance is not None
        except Exception as e:
            results["errors"].append(f"FinModAI Platform: {str(e)}")
        
        # Test data ingestion
        try:
            data_engine, config = get_data_ingestion()
            results["data_ingestion"] = data_engine is not None
        except Exception as e:
            results["errors"].append(f"Data Ingestion: {str(e)}")
            
        # Test pandas
        try:
            pd = get_pandas()
            results["pandas"] = pd is not None
        except Exception as e:
            results["errors"].append(f"Pandas: {str(e)}")
        
        return f"<pre>{json.dumps(results, indent=2)}</pre>"
        
    except Exception as e:
        return f"<h1>Module Test Error</h1><p>{str(e)}</p>"

# Company data input
@app.route('/company-data', methods=['GET', 'POST'])
def company_data():
    """Company data input and management interface"""
    if request.method == 'POST':
        # Process company data submission
        company_data = {
            'id': str(uuid.uuid4()),
            'name': request.form.get('company_name'),
            'ticker': request.form.get('ticker'),
            'sector': request.form.get('sector'),
            'revenue': float(request.form.get('revenue', 0)),
            'ebitda': float(request.form.get('ebitda', 0)),
            'net_income': float(request.form.get('net_income', 0)),
            'total_assets': float(request.form.get('total_assets', 0)),
            'total_debt': float(request.form.get('total_debt', 0)),
            'cash': float(request.form.get('cash', 0)),
            'shares_outstanding': float(request.form.get('shares_outstanding', 0)),
            'beta': float(request.form.get('beta', 1.2)),
            'date_added': datetime.now().isoformat(),
            'source': 'manual_input'
        }

        DATA_STORAGE[company_data['id']] = company_data
        flash(f"Company data for {company_data['name']} saved successfully!", "success")
        return redirect(url_for('company_data'))

    return render_template_string(COMPANY_DATA_HTML, companies=DATA_STORAGE)

# Model generation
@app.route('/generate-model', methods=['GET', 'POST'])
def generate_model():
    """Model generation interface"""
    if request.method == 'POST':
        model_type = request.form.get('model_type')
        company_id = request.form.get('company_id')
        custom_data = request.form.get('custom_data', 'false') == 'true'


        if custom_data and company_id and company_id in DATA_STORAGE:
            # Use custom data
            company_data = DATA_STORAGE[company_id]
        else:
            # Use API data
            ticker = request.form.get('ticker')
            print(f"🔍 Model generation requested: {model_type} for {ticker}")
            
            # Simplified: Skip platform loading for now and use mock data
            print(f"🔍 Using simplified model generation for debugging")
            
            if ticker:
                try:
                    print(f"🔍 Starting model generation for {model_type} - {ticker}")
                    
                    # Create a simple mock result for now to test the UI
                    model_result = {
                        'model_type': model_type,
                        'ticker': ticker,
                        'status': 'completed',
                        'message': 'Model generation temporarily simplified for debugging',
                        'output_files': [],  # No files for now
                        'processing_time_seconds': 1.0,
                        'company_name': f"{ticker} Corporation",
                        'model_summary': {
                            'key_assumptions': {
                                'revenue_growth_rate': 0.15,
                                'wacc': 0.10,
                                'terminal_growth_rate': 0.025
                            },
                            'valuation_outputs': {
                                'enterprise_value': 1000000000,
                                'equity_value': 900000000,
                                'implied_price': 150.00
                            }
                        }
                    }
                    
                    print(f"🔍 Mock model result created successfully!")

                    # Skip file generation for now
                    try:
                        output_files = model_result.get('output_files') or []
                        print(f"🔧 DEBUG: model_result output_files: {output_files}")
                        staged_files = []

                        # If no output files from Excel engine, check for recent files in generated_models
                        if not output_files:
                            print(f"🔧 DEBUG: No output files from Excel engine, checking generated_models directory")
                            os.makedirs('generated_models', exist_ok=True)
                            import glob
                            from pathlib import Path
                            # Look for all Excel files in generated_models
                            all_files = glob.glob('generated_models/*.xlsx')
                            print(f"🔧 DEBUG: Found {len(all_files)} Excel files in generated_models")
                            for file_path in all_files:
                                if os.path.exists(file_path):
                                    staged_files.append(file_path)
                                    print(f"🔧 DEBUG: Found file: {file_path}")
                            if staged_files:
                                model_result['output_files'] = staged_files
                                print(f"🔧 DEBUG: Added files to model_result: {staged_files}")
                            else:
                                print(f"🔧 DEBUG: No Excel files found in generated_models")
                        else:
                            # Stage files from Excel engine
                            for src_path in output_files:
                                try:
                                    abs_src = os.path.abspath(src_path)
                                    print(f"🔧 DEBUG: Checking source file: {abs_src}")
                                    if os.path.exists(abs_src):
                                        dest_name = os.path.basename(abs_src)
                                        dest_path = os.path.join('generated_models', dest_name)
                                        print(f"🔧 DEBUG: Copying to: {dest_path}")
                                        # Only copy if not already the same file
                                        if os.path.abspath(abs_src) != os.path.abspath(dest_path):
                                            shutil.copy2(abs_src, dest_path)
                                        staged_files.append(dest_path)
                                    else:
                                        print(f"🔧 DEBUG: Output file does not exist on disk: {src_path}")
                                except Exception as e_copy:
                                    print(f"🔧 DEBUG: Failed to stage file '{src_path}': {e_copy}")
                            if staged_files:
                                model_result['output_files'] = staged_files
                                print(f"🔧 DEBUG: Updated model_result with staged files: {staged_files}")
                    except Exception as e_stage:
                        print(f"🔧 DEBUG: Output file staging error: {e_stage}")

                    # Store model result
                    model_id = str(uuid.uuid4())
                    MODEL_STORAGE[model_id] = {
                        'id': model_id,
                        'type': model_type,
                        'ticker': ticker,  # Keep original ticker for reference
                        'corrected_ticker': model_result.get('corrected_ticker', ticker),  # Use corrected ticker if available
                        'result': model_result,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'completed'
                    }
                    flash(f"{model_type.upper()} model for {ticker} generated successfully!", "success")
                    return redirect(url_for('model_results', model_id=model_id))
                except Exception as e:
                    print(f"❌ Error generating model: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    flash(f"Error generating model: {str(e)}", "error")
            else:
                print("❌ Ticker not provided")
                flash("Ticker not provided", "error")

    return render_template_string(MODEL_GENERATION_HTML, companies=DATA_STORAGE)

# Model results
@app.route('/model-results/<model_id>')
def model_results(model_id):
    """Display model results"""
    if model_id in MODEL_STORAGE:
        model = MODEL_STORAGE[model_id]
        return render_template_string(MODEL_RESULTS_HTML, model=model)
    else:
        flash("Model not found", "error")
        return redirect(url_for('dashboard'))

@app.route('/download/<model_id>')
def download_model(model_id):
    """Download Excel model file"""
    print(f"🔍 Download requested for model_id: {model_id}")
    
    if model_id in MODEL_STORAGE:
        model = MODEL_STORAGE[model_id]
        print(f"🔍 Model found: {model.get('type')} for {model.get('ticker')}")
        
        # Debug model result structure
        if model.get('result'):
            print(f"🔍 Model result keys: {list(model['result'].keys())}")
            print(f"🔍 Has output_files: {'output_files' in model['result']}")
            
            if 'output_files' in model['result']:
                output_files = model['result']['output_files']
                print(f"🔍 Output files: {output_files}")
                
                if output_files and len(output_files) > 0:
                    file_path = output_files[0]
                    print(f"🔍 Checking file path: {file_path}")
                    
                    if os.path.exists(file_path):
                        print(f"✅ File exists, sending: {file_path}")
                        return send_file(file_path, as_attachment=True)
                    else:
                        print(f"❌ File not found on disk: {file_path}")
                        # Check if file exists in generated_models directory
                        filename = os.path.basename(file_path)
                        alt_path = os.path.join('generated_models', filename)
                        print(f"🔍 Checking alternative path: {alt_path}")
                        
                        if os.path.exists(alt_path):
                            print(f"✅ Found file at alternative path: {alt_path}")
                            return send_file(alt_path, as_attachment=True)
                        else:
                            print(f"❌ File not found at alternative path either")
                            flash("Excel file not found on disk", "error")
                else:
                    print("❌ Output files list is empty")
                    flash("No Excel file path available", "error")
            else:
                print("❌ No output_files key in result")
                flash("No Excel file available for this model", "error")
        else:
            print("❌ No result in model")
            flash("Model has no result data", "error")
    else:
        print(f"❌ Model {model_id} not found in storage")
        flash("Model not found", "error")

    return redirect(url_for('model_results', model_id=model_id))

# API endpoints for AJAX
@app.route('/api/company-data', methods=['GET'])
def get_company_data():
    """API endpoint to get company data"""
    return jsonify(list(DATA_STORAGE.values()))

@app.route('/api/company-data/<company_id>', methods=['DELETE'])
def delete_company_data(company_id):
    """Delete company data"""
    if company_id in DATA_STORAGE:
        del DATA_STORAGE[company_id]
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/api/models', methods=['GET'])
def get_models():
    """API endpoint to get models"""
    return jsonify(list(MODEL_STORAGE.values()))

@app.route('/debug-models')
def debug_models():
    """Debug endpoint to check model storage"""
    debug_info = {
        'total_models': len(MODEL_STORAGE),
        'generated_models_dir_exists': os.path.exists('generated_models'),
        'generated_models_files': [],
        'models': {}
    }
    
    # Check generated_models directory
    if os.path.exists('generated_models'):
        try:
            debug_info['generated_models_files'] = os.listdir('generated_models')
        except Exception as e:
            debug_info['generated_models_error'] = str(e)
    
    for model_id, model in MODEL_STORAGE.items():
        debug_info['models'][model_id] = {
            'type': model.get('type'),
            'ticker': model.get('ticker'),
            'status': model.get('status'),
            'result_keys': list(model.get('result', {}).keys()) if model.get('result') else [],
            'has_output_files': 'output_files' in model.get('result', {}) if model.get('result') else False,
            'output_files': model.get('result', {}).get('output_files') if model.get('result') else None,
            'timestamp': model.get('timestamp')
        }
    
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route('/test-template/<model_id>')
def test_template(model_id):
    """Test template rendering for a specific model"""
    if model_id in MODEL_STORAGE:
        model = MODEL_STORAGE[model_id]
        try:
            # Test the template condition
            has_output_files = 'output_files' in model.get('result', {}) if model.get('result') else False
            return f"""
            <h1>Template Test for Model {model_id}</h1>
            <p>Model result: {model.get('result') is not None}</p>
            <p>Has output_files key: {has_output_files}</p>
            <p>Output files: {model.get('result', {}).get('output_files') if model.get('result') else 'None'}</p>
            <p>Template condition should be: {model.get('result') is not None and has_output_files}</p>
            """
        except Exception as e:
            return f"<h1>Template Error</h1><p>{str(e)}</p>"
    else:
        return f"<h1>Model {model_id} not found</h1>"

@app.route('/test-download/<model_id>')
def test_download(model_id):
    """Test download section rendering"""
    if model_id in MODEL_STORAGE:
        model = MODEL_STORAGE[model_id]
        if model.get('result') and model.get('result').get('output_files'):
            return f"""
            <h1>Download Test for Model {model_id}</h1>
            <div style="background: #e8f4fd; border: 2px solid #667eea; border-radius: 10px; padding: 25px; margin: 30px 0;">
                <h3 style="color: #667eea; margin-bottom: 20px;">
                    <i class="fas fa-file-excel"></i> Download Your Model
                </h3>
                <p>Your {model.get('type', '').upper()} model for {model.get('ticker', '')} has been generated successfully!</p>
                <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
                    <a href="/download/{model.get('result').get('output_files')[0].split('/')[-1]}" 
                       style="background: #28a745; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px;">
                        <i class="fas fa-download"></i> Download Excel Model
                    </a>
                </div>
            </div>
            """
        else:
            return f"<h1>No output files found for model {model_id}</h1>"
    else:
        return f"<h1>Model {model_id} not found</h1>"

@app.route('/test-template-simple/<model_id>')
def test_template_simple(model_id):
    """Test simple template rendering"""
    if model_id in MODEL_STORAGE:
        model = MODEL_STORAGE[model_id]
        return f"""
        <h1>Simple Template Test for Model {model_id}</h1>
        <p>Model result exists: {model.get('result') is not None}</p>
        <p>Output files exist: {model.get('result', {}).get('output_files') is not None if model.get('result') else False}</p>
        <p>Output files: {model.get('result', {}).get('output_files') if model.get('result') else 'None'}</p>
        <p>Template condition: {model.get('result') and model.get('result').get('output_files')}</p>
        """
    else:
        return f"<h1>Model {model_id} not found</h1>"

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated Excel files"""
    try:
        file_path = os.path.join('generated_models', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash("File not found", "error")
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f"Download error: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/download-all')
def download_all_models():
    """Download all models as a zip file"""
    try:
        import zipfile
        import tempfile
        from datetime import datetime
        
        # Create temporary zip file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"FinModAI_All_Models_{timestamp}.zip"
        
        # Create zip in memory
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            models_dir = os.path.join(os.getcwd(), 'generated_models')
            if os.path.exists(models_dir):
                for filename in os.listdir(models_dir):
                    if filename.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(models_dir, filename)
                        zipf.write(file_path, filename)
        
        return send_file(
            temp_zip.name, 
            as_attachment=True, 
            download_name=zip_filename,
            mimetype='application/zip'
        )
    except Exception as e:
        flash(f"Bulk download error: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/view-model/<filename>')
def view_model(filename):
    """View Excel model in browser (read-only)"""
    try:
        file_path = os.path.join('generated_models', filename)
        if os.path.exists(file_path):
            # For now, redirect to download since Excel viewing in browser is complex
            # In a production app, you'd use a library like SheetJS or similar
            return redirect(url_for('download_file', filename=filename))
        else:
            flash("Model file not found", "error")
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f"View error: {str(e)}", "error")
        return redirect(url_for('dashboard'))

# File upload for bulk data
@app.route('/upload-data', methods=['POST'])
def upload_data():
    """Handle file upload for bulk company data"""
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('company_data'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('company_data'))

    if file and file.filename.endswith(('.xlsx', '.xls', '.csv')):
        try:
            # Save file temporarily
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}")
            file.save(temp_path)

            # Process file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:
                df = pd.read_excel(temp_path)

            # Process each row as company data
            for _, row in df.iterrows():
                company_data = {
                    'id': str(uuid.uuid4()),
                    'name': row.get('Company Name', row.get('Name', 'Unknown')),
                    'ticker': row.get('Ticker', row.get('Symbol', 'Unknown')),
                    'sector': row.get('Sector', 'Unknown'),
                    'revenue': float(row.get('Revenue', row.get('Sales', 0))),
                    'ebitda': float(row.get('EBITDA', 0)),
                    'net_income': float(row.get('Net Income', 0)),
                    'total_assets': float(row.get('Total Assets', 0)),
                    'total_debt': float(row.get('Total Debt', 0)),
                    'cash': float(row.get('Cash', 0)),
                    'shares_outstanding': float(row.get('Shares Outstanding', 0)),
                    'beta': float(row.get('Beta', 1.2)),
                    'date_added': datetime.now().isoformat(),
                    'source': 'file_upload'
                }
                DATA_STORAGE[company_data['id']] = company_data

            # Clean up temp file
            os.remove(temp_path)

            flash(f"Successfully uploaded {len(df)} companies from {file.filename}", "success")

        except Exception as e:
            flash(f"Error processing file: {str(e)}", "error")

    else:
        flash('Invalid file type. Please upload .xlsx, .xls, or .csv files', 'error')

    return redirect(url_for('company_data'))

# Main function to run the app
def create_ngrok_tunnel(port):
    """Create an ngrok tunnel and return the public URL."""
    import requests
    import time
    import subprocess
    from pathlib import Path

    ngrok_path = Path('./ngrok')
    if not ngrok_path.exists():
        print("⚠️ ngrok not found in current directory")
        return None

    try:
        # Start ngrok in background
        subprocess.Popen([str(ngrok_path), 'http', str(port)], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        
        # Wait for tunnel
        time.sleep(2)
        
        try:
            # Get public URL
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    return tunnels[0]['public_url']
        except Exception as e:
            print(f"⚠️ Could not get ngrok URL: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating ngrok tunnel: {e}")
        return None

def main():
    """Run the FinModAI web interface"""
    import argparse
    parser = argparse.ArgumentParser(description="FinModAI Web Interface")
    parser.add_argument("--port", "-p", type=int, default=int(os.environ.get('PORT', 8000)),
                      help="Port to run the server on (default: 8000)")
    parser.add_argument("--no-ngrok", action="store_true",
                      help="Disable ngrok tunnel creation")
    args = parser.parse_args()
    
    port = args.port
    
    # Check if running in production (cloud environment)
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT') is not None or os.environ.get('RENDER') is not None
    
    print("🚀 Starting FinModAI Professional Web Interface...")
    
    if not args.no_ngrok and not is_production:
        print("📡 Creating ngrok tunnel...")
        public_url = create_ngrok_tunnel(port)
        if public_url:
            print(f"\n🌎 Public URL: {public_url}")
            print(f"   📊 Dashboard: {public_url}")
            print(f"   💰 Company Data: {public_url}/company-data")
            print(f"   🤖 Model Generation: {public_url}/generate-model")
        else:
            print("⚠️ Could not create ngrok tunnel. Running in local-only mode.")
    
    if is_production:
        print("🌐 Running in production mode")
        print(f"🚀 Server will be available on port {port}")
    else:
        print(f"\n💻 Local URLs:")
        print(f"   📊 Dashboard: http://localhost:{port}")
        print(f"   💰 Company Data: http://localhost:{port}/company-data")
        print(f"   🤖 Model Generation: http://localhost:{port}/generate-model")
        print()
        print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Use different configurations for production vs development
    # In production, Gunicorn will handle the WSGI app
    if not is_production:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

def run_server():
    """Run the FinModAI web interface (alias for main)"""
    main()

if __name__ == '__main__':
    main()

# HTML Templates for the web interface
MAIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinModAI - Professional Financial Modeling Platform</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .navbar {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 0;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        .nav-links {
            display: flex;
            gap: 2rem;
        }
        .nav-link {
            color: #333;
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        .nav-link:hover {
            background: #667eea;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 100px 20px 40px;
        }
        .hero {
            text-align: center;
            color: white;
            margin-bottom: 60px;
        }
        .hero h1 {
            font-size: 3.5em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .hero p {
            font-size: 1.3em;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .btn {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        .feature-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .feature-card p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-chart-line"></i> FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/company-data" class="nav-link">Company Data</a>
                <a href="/generate-model" class="nav-link">Model Generation</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="hero">
            <h1>🏦 FinModAI Professional</h1>
            <p>Bloomberg Terminal meets GitHub Copilot for financial modeling</p>
            <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap;">
                <a href="/company-data" class="btn btn-primary">
                    <i class="fas fa-database"></i> Manage Company Data
                </a>
                <a href="/generate-model" class="btn btn-primary">
                    <i class="fas fa-robot"></i> Generate Models
                </a>
                                </div>
                                </div>

        <div class="features-grid">
            <div class="feature-card">
                <h3><i class="fas fa-database"></i> Data Input & Management</h3>
                <p>Comprehensive company data input with manual entry and bulk upload capabilities for custom analysis.</p>
                                </div>

            <div class="feature-card">
                <h3><i class="fas fa-robot"></i> AI-Powered Model Generation</h3>
                <p>Advanced financial modeling with intelligent assumptions and professional Excel outputs using 14+ data sources.</p>
                                </div>

            <div class="feature-card">
                <h3><i class="fas fa-chart-bar"></i> Professional Analytics</h3>
                <p>Investment banking-grade analysis with comprehensive financial statements, sensitivity analysis, and valuation models.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

COMPANY_DATA_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Data Management - FinModAI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        .navbar {
            background: #667eea;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }
        .nav-links {
            display: flex;
            gap: 2rem;
        }
        .nav-link {
            color: white;
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        .nav-link:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .page-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .page-header h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .form-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .form-section h2 {
            color: #333;
            margin-bottom: 25px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        .data-table {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        .data-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .data-table th,
        .data-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        .data-table th {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-chart-line"></i> FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/company-data" class="nav-link">Company Data</a>
                <a href="/generate-model" class="nav-link">Model Generation</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="page-header">
            <h1><i class="fas fa-database"></i> Company Data Management</h1>
            <p>Input and manage company financial data for custom modeling</p>
        </div>

        <div class="form-section">
            <h2><i class="fas fa-edit"></i> Manual Company Data Entry</h2>
            <form method="POST" action="/company-data">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="company_name">Company Name *</label>
                        <input type="text" id="company_name" name="company_name" required placeholder="e.g., Apple Inc.">
                    </div>
                    <div class="form-group">
                        <label for="ticker">Stock Ticker *</label>
                        <input type="text" id="ticker" name="ticker" required placeholder="e.g., AAPL">
                    </div>
                    <div class="form-group">
                        <label for="sector">Sector</label>
                        <select id="sector" name="sector">
                            <option value="">Select Sector</option>
                            <option value="Technology">Technology</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Financial Services">Financial Services</option>
                            <option value="Consumer Cyclical">Consumer Cyclical</option>
                            <option value="Industrials">Industrials</option>
                            <option value="Energy">Energy</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="revenue">Revenue ($M)</label>
                        <input type="number" id="revenue" name="revenue" step="0.01" placeholder="e.g., 365817">
                    </div>
                    <div class="form-group">
                        <label for="ebitda">EBITDA ($M)</label>
                        <input type="number" id="ebitda" name="ebitda" step="0.01" placeholder="e.g., 123136">
                    </div>
                    <div class="form-group">
                        <label for="net_income">Net Income ($M)</label>
                        <input type="number" id="net_income" name="net_income" step="0.01" placeholder="e.g., 99803">
                    </div>
                    <div class="form-group">
                        <label for="beta">Beta</label>
                        <input type="number" id="beta" name="beta" step="0.01" value="1.20" placeholder="e.g., 1.20">
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> Save Company Data
                </button>
            </form>
        </div>

        <div class="form-section">
            <h2><i class="fas fa-list"></i> Saved Company Data</h2>
            <div class="data-table">
                <table>
                    <thead>
                        <tr>
                            <th>Company Name</th>
                            <th>Ticker</th>
                            <th>Sector</th>
                            <th>Revenue ($M)</th>
                            <th>EBITDA ($M)</th>
                            <th>Source</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for company in companies %}
                        <tr>
                            <td><strong>{{ company.name }}</strong></td>
                            <td><span style="color: #667eea; font-weight: 500;">{{ company.ticker }}</span></td>
                            <td>{{ company.sector }}</td>
                            <td>{{ "{:,.0f}".format(company.revenue) if company.revenue else "-" }}</td>
                            <td>{{ "{:,.0f}".format(company.ebitda) if company.ebitda else "-" }}</td>
                            <td><span style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 12px; font-size: 0.8em;">Manual</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

MODEL_GENERATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Generation - FinModAI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        .navbar {
            background: #667eea;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }
        .nav-links {
            display: flex;
            gap: 2rem;
        }
        .nav-link {
            color: white;
            text-decoration: none;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        .nav-link:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .page-header {
            text-align: center;
            margin-bottom: 40px;
        }
        .page-header h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .form-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .form-section h2 {
            color: #333;
            margin-bottom: 25px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        .model-types {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .model-type {
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .model-type:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .model-type.selected {
            border-color: #667eea;
            background: #667eea;
            color: white;
        }
        .model-type i {
            font-size: 2em;
            margin-bottom: 10px;
            display: block;
        }
        .model-type h3 {
            margin-bottom: 5px;
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-chart-line"></i> FinModAI
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/company-data" class="nav-link">Company Data</a>
                <a href="/generate-model" class="nav-link">Model Generation</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="page-header">
            <h1><i class="fas fa-robot"></i> Model Generation</h1>
            <p>Generate professional financial models using AI-powered analysis</p>
        </div>

        <div class="form-section">
            <h2><i class="fas fa-cogs"></i> Model Configuration</h2>
            <form method="POST" action="/generate-model" id="modelForm">
                <div class="form-group">
                    <label>Model Type</label>
                    <div class="model-types" id="modelTypes">
                        <div class="model-type" data-value="dcf">
                            <i class="fas fa-chart-line"></i>
                            <h3>DCF Model</h3>
                            <small>Discounted Cash Flow</small>
                        </div>
                        <div class="model-type" data-value="lbo">
                            <i class="fas fa-building"></i>
                            <h3>LBO Model</h3>
                            <small>Leveraged Buyout</small>
                        </div>
                        <div class="model-type" data-value="comps">
                            <i class="fas fa-balance-scale"></i>
                            <h3>Comps</h3>
                            <small>Trading Comparables</small>
                        </div>
                        <div class="model-type" data-value="three_statement">
                            <i class="fas fa-file-alt"></i>
                            <h3>3-Statement</h3>
                            <small>Financial Statements</small>
                        </div>
                        <div class="model-type" data-value="merger">
                            <i class="fas fa-handshake"></i>
                            <h3>M&A Model</h3>
                            <small>Merger Analysis</small>
                        </div>
                    </div>
                    <input type="hidden" name="model_type" id="selectedModelType" required>
                </div>

                <div class="form-group">
                    <label for="ticker">Company Ticker</label>
                    <input type="text" id="ticker" name="ticker" placeholder="e.g., AAPL, MSFT, TSLA" required>
                    <small style="color: #666; display: block; margin-top: 5px;">
                        Enter a valid stock ticker to generate a model using real market data
                    </small>
                </div>

                <div class="assumptions-panel" id="assumptionsPanel">
                    <h3><i class="fas fa-sliders-h"></i> Model Assumptions</h3>
                    
                    <div class="assumptions-grid">
                        <!-- DCF Assumptions -->
                        <div class="assumption-group" data-model="dcf">
                            <div class="form-group">
                                <label>Revenue Growth (%)</label>
                                <input type="number" name="dcf_revenue_growth" step="0.1" placeholder="e.g., 5.0">
                            </div>
                            <div class="form-group">
                                <label>EBITDA Margin (%)</label>
                                <input type="number" name="dcf_ebitda_margin" step="0.1" placeholder="e.g., 25.0">
                            </div>
                            <div class="form-group">
                                <label>Terminal Growth (%)</label>
                                <input type="number" name="dcf_terminal_growth" step="0.1" placeholder="e.g., 2.0">
                            </div>
                            <div class="form-group">
                                <label>WACC (%)</label>
                                <input type="number" name="dcf_wacc" step="0.1" placeholder="e.g., 10.0">
                            </div>
                        </div>

                        <!-- LBO Assumptions -->
                        <div class="assumption-group" data-model="lbo" style="display: none;">
                            <div class="form-group">
                                <label>Purchase Multiple</label>
                                <input type="number" name="lbo_purchase_multiple" step="0.1" placeholder="e.g., 12.0">
                            </div>
                            <div class="form-group">
                                <label>Debt/EBITDA</label>
                                <input type="number" name="lbo_leverage" step="0.1" placeholder="e.g., 6.0">
                            </div>
                            <div class="form-group">
                                <label>Exit Year</label>
                                <input type="number" name="lbo_exit_year" step="1" placeholder="e.g., 5">
                            </div>
                            <div class="form-group">
                                <label>Exit Multiple</label>
                                <input type="number" name="lbo_exit_multiple" step="0.1" placeholder="e.g., 10.0">
                            </div>
                        </div>

                        <!-- Comps Assumptions -->
                        <div class="assumption-group" data-model="comps" style="display: none;">
                            <div class="form-group">
                                <label>Comparable Companies</label>
                                <textarea name="comps_peers" placeholder="Enter tickers, one per line"></textarea>
                            </div>
                            <div class="form-group">
                                <label>Metrics to Compare</label>
                                <select name="comps_metrics" multiple>
                                    <option value="ev_ebitda">EV/EBITDA</option>
                                    <option value="pe">P/E</option>
                                    <option value="ps">P/S</option>
                                    <option value="pb">P/B</option>
                                </select>
                            </div>
                        </div>

                        <!-- Three Statement Assumptions -->
                        <div class="assumption-group" data-model="three_statement" style="display: none;">
                            <div class="form-group">
                                <label>Forecast Years</label>
                                <input type="number" name="three_statement_years" step="1" placeholder="e.g., 5">
                            </div>
                            <div class="form-group">
                                <label>Revenue Growth (%)</label>
                                <input type="number" name="three_statement_growth" step="0.1" placeholder="e.g., 5.0">
                            </div>
                            <div class="form-group">
                                <label>Working Capital (%)</label>
                                <input type="number" name="three_statement_wc" step="0.1" placeholder="e.g., 10.0">
                            </div>
                        </div>

                        <!-- Merger Model Assumptions -->
                        <div class="assumption-group" data-model="merger" style="display: none;">
                            <div class="form-group">
                                <label>Target Ticker</label>
                                <input type="text" name="merger_target" placeholder="e.g., CRM">
                            </div>
                            <div class="form-group">
                                <label>Premium (%)</label>
                                <input type="number" name="merger_premium" step="0.1" placeholder="e.g., 25.0">
                            </div>
                            <div class="form-group">
                                <label>Synergies ($M)</label>
                                <input type="number" name="merger_synergies" step="1" placeholder="e.g., 100">
                            </div>
                            <div class="form-group">
                                <label>Deal Structure</label>
                                <select name="merger_structure">
                                    <option value="cash">All Cash</option>
                                    <option value="stock">All Stock</option>
                                    <option value="mixed">Cash & Stock</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn btn-primary" id="generateBtn">
                        <i class="fas fa-play"></i> Generate Model
                    </button>
                    <div class="loading-spinner" id="loadingSpinner" style="display: none;">
                        <i class="fas fa-spinner fa-spin"></i> Generating model...
                    </div>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Model type selection
        const modelTypes = document.querySelectorAll('.model-type');
        const selectedModelTypeInput = document.getElementById('selectedModelType');

        modelTypes.forEach(type => {
            type.addEventListener('click', function() {
                modelTypes.forEach(t => t.classList.remove('selected'));
                this.classList.add('selected');
                selectedModelTypeInput.value = this.dataset.value;
            });
        });

        // Data source toggle
        const useCustomSelect = document.getElementById('use_custom');
        const customDataGroup = document.getElementById('customDataGroup');
        const tickerGroup = document.getElementById('tickerGroup');
        const tickerInput = document.getElementById('ticker');

        useCustomSelect.addEventListener('change', function() {
            if (this.value === 'true') {
                customDataGroup.style.display = 'block';
                tickerGroup.style.display = 'none';
                tickerInput.required = false;
                document.getElementById('company_id').required = true;
            } else {
                customDataGroup.style.display = 'none';
                tickerGroup.style.display = 'block';
                tickerInput.required = true;
                document.getElementById('company_id').required = false;
            }
        });
    </script>
</body>
</html>
"""

MODEL_RESULTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Results - FinModAI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        .navbar {
            background: #667eea;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            color: white;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .result-card {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .result-card h2 {
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .result-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .result-item {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        .result-item h4 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .result-item .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .status-success {
            background: #4CAF50;
            color: white;
        }
        .status-error {
            background: #f44336;
            color: white;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <i class="fas fa-chart-line"></i> FinModAI
            </div>
    </nav>

    <div class="container">
        <div class="result-card">
            <h2><i class="fas fa-chart-bar"></i> Model Results</h2>

            <div style="margin-bottom: 20px;">
                <strong>Model Type:</strong> {{ model.type.upper() }} |
                <strong>Ticker:</strong> {{ model.corrected_ticker if model.corrected_ticker != model.ticker else model.ticker }} |
                <strong>Status:</strong>
                <span class="status status-{{ 'success' if model.status == 'completed' else 'error' }}">
                    {{ model.status.title() }}
                </span>
            </div>

            <div style="margin-bottom: 20px;">
                <strong>Generated:</strong> {{ model.timestamp[:19].replace('T', ' ') }}
            </div>

            {% if model.result %}
                <h3 style="color: #333; margin-bottom: 20px;">Key Outputs</h3>
                <div class="result-grid">
                    {% for key, value in model.result.items() %}
                        {% if key != 'output_files' %}
                        <div class="result-item">
                            <h4>{{ key.replace('_', ' ').title() }}</h4>
                            <div class="value">
                                {% if 'multiple' in key.lower() or 'moic' in key.lower() %}
                                    {{ "%.1f"|format(value) }}x
                                {% elif 'price' in key.lower() or 'value' in key.lower() %}
                                    ${{ "%.0f"|format(value) if value > 1000000 else "%.2f"|format(value) }}
                                {% elif value|float == value and value > 1000000 %}
                                    ${{ "%.0f"|format(value) }}
                                {% elif value|float == value %}
                                    {{ "%.2f"|format(value) }}
                                {% else %}
                                    {{ value }}
                                {% endif %}
                            </div>
                        </div>
                        {% endif %}
                    {% endfor %}
                </div>
            {% else %}
                <div style="text-align: center; padding: 40px; color: #666;">
                    <i class="fas fa-info-circle" style="font-size: 3em; margin-bottom: 20px;"></i>
                    <p>Model generation in progress or no results available yet.</p>
                </div>
            {% endif %}

            {% if model.status in ['completed', 'success'] %}
                {% if model.result and model.result.get('success', True) %}
                    <div style="background: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 25px; margin: 30px 0;">
                        <h3 style="color: #155724; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                            <i class="fas fa-check-circle"></i> Model Generated Successfully
                        </h3>
                        <p style="color: #155724; margin-bottom: 20px;">
                            Your {{ model.type.upper() }} model for {{ model.corrected_ticker if model.corrected_ticker != model.ticker else model.ticker }} has been generated successfully!
                        </p>
                        <div style="background: white; border-radius: 5px; padding: 15px; margin-top: 15px;">
                            <p style="margin: 0;"><strong>Model Type:</strong> {{ model.type.upper() }}</p>
                            <p style="margin: 0;"><strong>Company:</strong> {{ model.result.get('company', model.ticker) if model.result else model.ticker }}</p>
                            <p style="margin: 0;"><strong>Generated:</strong> {{ model.timestamp[:19].replace('T', ' ') }}</p>
                        </div>
                    </div>
                    {% else %}
                    <div style="background: #f8d7da; border: 2px solid #dc3545; border-radius: 10px; padding: 25px; margin: 30px 0;">
                        <h3 style="color: #721c24; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                            <i class="fas fa-exclamation-triangle"></i> Model Generation Failed
                        </h3>
                        <p style="color: #721c24; margin-bottom: 20px;">
                            There was an error generating your {{ model.type.upper() }} model for {{ model.corrected_ticker if model.corrected_ticker != model.ticker else model.ticker }}.
                        </p>
                        <div style="background: white; border-radius: 5px; padding: 15px; margin-top: 15px;">
                            <p style="margin: 0;"><strong>Error:</strong> {{ model.result.get('error', 'Unknown error') if model.result else 'No error details available' }}</p>
                            <p style="margin: 0;"><strong>Model Type:</strong> {{ model.type.upper() }}</p>
                            <p style="margin: 0;"><strong>Generated:</strong> {{ model.timestamp[:19].replace('T', ' ') }}</p>
                        </div>
                    </div>
                    {% endif %}
                {% else %}
                    <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 25px; margin: 30px 0;">
                        <h3 style="color: #856404; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                            <i class="fas fa-info-circle"></i> Model Status Unknown
                        </h3>
                        <p style="color: #856404; margin-bottom: 20px;">
                            The model status is {{ model.status }}, but the result details are not available or incomplete.
                        </p>
                        <div style="background: white; border-radius: 5px; padding: 15px; margin-top: 15px;">
                            <p style="margin: 0;"><strong>Model Type:</strong> {{ model.type.upper() }}</p>
                            <p style="margin: 0;"><strong>Generated:</strong> {{ model.timestamp[:19].replace('T', ' ') }}</p>
                        </div>
                    </div>
                {% endif %}
            {% endif %}

            {% if model.result and model.result.output_files %}
                <div style="background: #e8f4fd; border: 2px solid #667eea; border-radius: 10px; padding: 25px; margin: 30px 0;">
                    <h3 style="color: #667eea; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-file-excel"></i> Download Your Model
                    </h3>
                    <p style="color: #666; margin-bottom: 20px;">
                        Your {{ model.type.upper() }} model for {{ model.corrected_ticker if model.corrected_ticker != model.ticker else model.ticker }} has been generated successfully!
                        Click below to download the Excel file.
                    </p>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
                        {% for file in model.result.output_files %}
                        <a href="/download/{{ file.split('/')[-1] }}" 
                           class="btn btn-primary" 
                           style="background: #28a745; font-size: 1.1em; padding: 15px 25px;">
                            <i class="fas fa-download"></i> Download Excel Model
                        </a>
                        <a href="/view-model/{{ file.split('/')[-1] }}" 
                           class="btn btn-secondary" 
                           style="background: #17a2b8; font-size: 1.1em; padding: 15px 25px;">
                            <i class="fas fa-eye"></i> View Model
                        </a>
                        {% endfor %}
                    </div>
                    <div style="margin-top: 15px; text-align: center;">
                        <small style="color: #666;">
                            <i class="fas fa-info-circle"></i> 
                            File: {{ model.result.output_files[0].split('/')[-1] if model.result.output_files else 'N/A' }}
                        </small>
                    </div>
                </div>
            {% elif model.status in ['completed', 'success'] %}
                <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 25px; margin: 30px 0;">
                    <h3 style="color: #856404; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-info-circle"></i> Model Generated
                    </h3>
                    <p style="color: #856404; margin-bottom: 10px;">
                        Your model was generated successfully, but the Excel file is not currently available for download.
                    </p>
                    <p style="color: #856404;">
                        This might be because:
                    </p>
                    <ul style="color: #856404; margin-left: 20px;">
                        <li>The Excel file generation is still in progress</li>
                        <li>The file is being processed</li>
                        <li>A temporary issue with file generation</li>
                    </ul>
                    <p style="color: #856404; margin-top: 15px;">
                        <strong>Try refreshing the page in a few moments, or generate a new model.</strong>
                    </p>
                </div>
            {% else %}
                <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 25px; margin: 30px 0;">
                    <h3 style="color: #856404; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-exclamation-triangle"></i> Debug Info
                    </h3>
                    <p style="color: #856404; margin-bottom: 10px;">
                        Model result structure: {{ model.result.keys() if model.result else 'No result' }}
                    </p>
                    <p style="color: #856404; margin-bottom: 10px;">
                        Output files: {{ model.result.get('output_files') if model.result else 'No result' }}
                    </p>
                    <p style="color: #856404;">
                        This debug info will help us fix the download button issue.
                    </p>
                </div>
            {% endif %}

            <div style="text-align: center; margin-top: 30px;">
                <a href="/" class="btn btn-primary">
                    <i class="fas fa-home"></i> Back to Dashboard
                </a>
                <a href="/generate-model" class="btn btn-secondary" style="margin-left: 10px;">
                    <i class="fas fa-plus"></i> Generate Another Model
                </a>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Main function to run the app
def create_ngrok_tunnel(port):
    """Create an ngrok tunnel and return the public URL."""
    import requests
    import time
    import subprocess
    from pathlib import Path

    ngrok_path = Path('./ngrok')
    if not ngrok_path.exists():
        print("⚠️ ngrok not found in current directory")
        return None

    try:
        # Start ngrok in background
        subprocess.Popen([str(ngrok_path), 'http', str(port)], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        
        # Wait for tunnel
        time.sleep(2)
        
        try:
            # Get public URL
            response = requests.get('http://localhost:4040/api/tunnels')
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    return tunnels[0]['public_url']
        except Exception as e:
            print(f"⚠️ Could not get ngrok URL: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating ngrok tunnel: {e}")
        return None

def main():
    """Run the FinModAI web interface"""
    import argparse
    parser = argparse.ArgumentParser(description="FinModAI Web Interface")
    parser.add_argument("--port", "-p", type=int, default=int(os.environ.get('PORT', 8000)),
                      help="Port to run the server on (default: 8000)")
    parser.add_argument("--no-ngrok", action="store_true",
                      help="Disable ngrok tunnel creation")
    args = parser.parse_args()
    
    port = args.port
    
    # Check if running in production (cloud environment)
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RAILWAY_ENVIRONMENT') is not None or os.environ.get('RENDER') is not None
    
    print("🚀 Starting FinModAI Professional Web Interface...")
    
    if not args.no_ngrok and not is_production:
        print("📡 Creating ngrok tunnel...")
        public_url = create_ngrok_tunnel(port)
        if public_url:
            print(f"\n🌎 Public URL: {public_url}")
            print(f"   📊 Dashboard: {public_url}")
            print(f"   💰 Company Data: {public_url}/company-data")
            print(f"   🤖 Model Generation: {public_url}/generate-model")
        else:
            print("⚠️ Could not create ngrok tunnel. Running in local-only mode.")
    
    if is_production:
        print("🌐 Running in production mode")
        print(f"🚀 Server will be available on port {port}")
    else:
        print(f"\n💻 Local URLs:")
        print(f"   📊 Dashboard: http://localhost:{port}")
        print(f"   💰 Company Data: http://localhost:{port}/company-data")
        print(f"   🤖 Model Generation: http://localhost:{port}/generate-model")
        print()
        print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Use different configurations for production vs development
    # In production, Gunicorn will handle the WSGI app
    if not is_production:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

def run_server():
    """Run the FinModAI web interface (alias for main)"""
    main()

if __name__ == '__main__':
    main()
