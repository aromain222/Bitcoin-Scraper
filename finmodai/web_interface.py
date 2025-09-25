#!/usr/bin/env python3
"""
FinModAI Web Interface
Professional web interface for the financial modeling platform.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import webbrowser
import threading
import time

# Web framework
try:
    from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("Flask not available - web interface disabled")

# Alternative simple HTTP server
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    import html
    HTTP_SERVER_AVAILABLE = True
except ImportError:
    HTTP_SERVER_AVAILABLE = False

logger = logging.getLogger('FinModAI.WebInterface')

class WebInterface:
    """Web interface for FinModAI platform."""

    def __init__(self, platform, host: str = "localhost", port: int = 8000):
        self.platform = platform
        self.host = host
        self.port = port
        self.server = None
        self.templates_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"

        # Create directories if they don't exist
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)

        # Initialize web framework
        if FLASK_AVAILABLE:
            self.app = self._create_flask_app()
            self.use_flask = True
        elif HTTP_SERVER_AVAILABLE:
            self.use_flask = False
            logger.info("Using simple HTTP server")
        else:
            raise ImportError("Neither Flask nor basic HTTP server available")

        logger.info(f"🌐 Web interface initialized on {host}:{port}")

    def _create_flask_app(self):
        """Create Flask application."""
        app = Flask(__name__,
                   template_folder=str(self.templates_dir),
                   static_folder=str(self.static_dir))
        app.secret_key = os.environ.get('SECRET_KEY', 'finmodai-secret-key')
        CORS(app)

        @app.route('/')
        def index():
            """Main dashboard page."""
            return self._render_template('index.html', {
                'title': 'FinModAI - AI-Powered Financial Modeling',
                'supported_models': self.platform.get_supported_models(),
                'recent_models': self._get_recent_models()
            })

        @app.route('/model/<model_type>', methods=['GET', 'POST'])
        def model_page(model_type):
            """Model creation page."""
            if request.method == 'POST':
                return self._handle_model_creation(request, model_type)

            templates = self.platform.get_model_templates()
            template = templates.get(model_type, {})

            return self._render_template('model.html', {
                'title': f'Create {model_type.upper()} Model',
                'model_type': model_type,
                'template': template,
                'supported_models': self.platform.get_supported_models()
            })

        @app.route('/api/generate-model', methods=['POST'])
        def api_generate_model():
            """API endpoint for model generation."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400

                model_type = data.get('model_type')
                company_identifier = data.get('company_identifier')
                assumptions = data.get('assumptions', {})

                if not model_type or not company_identifier:
                    return jsonify({'error': 'Model type and company identifier required'}), 400

                result = self.platform.generate_model(
                    model_type=model_type,
                    company_identifier=company_identifier,
                    assumptions=assumptions
                )

                return jsonify(result)

            except Exception as e:
                logger.error(f"API error: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/api/models', methods=['GET'])
        def api_get_models():
            """Get available model types."""
            return jsonify({
                'models': self.platform.get_supported_models(),
                'templates': self.platform.get_model_templates()
            })

        @app.route('/download/<filename>')
        def download_file(filename):
            """Download generated model files."""
            try:
                filepath = Path(self.platform.config.output_dir) / filename
                if filepath.exists():
                    return send_file(filepath, as_attachment=True)
                else:
                    return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @app.route('/results/<model_id>')
        def model_results(model_id):
            """Display model results."""
            # In a real implementation, you'd store and retrieve model results
            return self._render_template('results.html', {
                'title': 'Model Results',
                'model_id': model_id,
                'supported_models': self.platform.get_supported_models()
            })

        return app

    def _handle_model_creation(self, request, model_type):
        """Handle model creation form submission."""
        try:
            # Extract form data
            company_identifier = request.form.get('company_identifier', '').strip()
            custom_assumptions = {}

            # Extract custom assumptions from form
            for key, value in request.form.items():
                if key.startswith('assumption_'):
                    assumption_key = key.replace('assumption_', '')
                    try:
                        # Try to convert to number
                        if '.' in value or '%' in value:
                            custom_assumptions[assumption_key] = float(value.replace('%', '')) / 100 if '%' in value else float(value)
                        else:
                            custom_assumptions[assumption_key] = float(value)
                    except ValueError:
                        custom_assumptions[assumption_key] = value

            # Generate model
            result = self.platform.generate_model(
                model_type=model_type,
                company_identifier=company_identifier,
                assumptions=custom_assumptions
            )

            if result['success']:
                flash('Model generated successfully!', 'success')
                # Store result for display
                return self._render_template('results.html', {
                    'title': f'{model_type.upper()} Model Results',
                    'result': result,
                    'supported_models': self.platform.get_supported_models()
                })
            else:
                flash(f'Error: {result["error"]}', 'error')
                return redirect(url_for('model_page', model_type=model_type))

        except Exception as e:
            logger.error(f"Model creation error: {e}")
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('model_page', model_type=model_type))

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render HTML template with context."""
        if self.use_flask:
            return render_template(template_name, **context)
        else:
            return self._render_simple_template(template_name, context)

    def _render_simple_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Simple template rendering for basic HTTP server."""
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            return self._generate_default_html(context)

        try:
            with open(template_path, 'r') as f:
                template_content = f.read()

            # Simple template substitution
            for key, value in context.items():
                template_content = template_content.replace(f'{{{{ {key} }}}}', str(value))

            return template_content
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return self._generate_default_html(context)

    def _generate_default_html(self, context: Dict[str, Any]) -> str:
        """Generate default HTML when templates are not available."""
        title = context.get('title', 'FinModAI')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    color: #1f4e79;
                    margin-bottom: 30px;
                }}
                .model-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .model-card {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    transition: transform 0.2s;
                }}
                .model-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .model-card h3 {{
                    color: #2e7d32;
                    margin-bottom: 10px;
                }}
                .btn {{
                    background: #1f4e79;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin: 5px;
                }}
                .btn:hover {{
                    background: #153449;
                }}
                .btn-success {{
                    background: #2e7d32;
                }}
                .btn-success:hover {{
                    background: #1b5e20;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 FinModAI</h1>
                    <p><em>Bloomberg Terminal meets GitHub Copilot for financial modeling</em></p>
                    <p>AI-powered platform that transforms hours of financial modeling into minutes of insight</p>
                </div>

                <h2>Available Models</h2>
                <div class="model-grid">
        """

        # Add model cards
        supported_models = context.get('supported_models', [])
        for model in supported_models:
            html += f"""
                    <div class="model-card">
                        <h3>{model.upper()}</h3>
                        <p>Create professional {model.upper()} models with AI assistance</p>
                        <a href="/model/{model}" class="btn">Create {model.upper()} Model</a>
                    </div>
            """

        html += """
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <h3>🚀 Key Features</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
                        <div style="text-align: left;">
                            <h4>⚡ 10x Faster Creation</h4>
                            <p>Transform hours of manual work into minutes with AI-powered automation</p>
                        </div>
                        <div style="text-align: left;">
                            <h4>🔄 One-Click Data Ingestion</h4>
                            <p>Automatically pull financial data from 50+ sources or upload your own files</p>
                        </div>
                        <div style="text-align: left;">
                            <h4>🎯 Audit-Ready Outputs</h4>
                            <p>Professional Excel models with built-in validation and explainable AI logic</p>
                        </div>
                        <div style="text-align: left;">
                            <h4>🔗 Enterprise Integration</h4>
                            <p>Seamlessly connect with Bloomberg, CapIQ, Excel, and PowerPoint</p>
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p><strong>FinModAI</strong> - Where AI meets Finance. Investment banking's most powerful modeling platform.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _get_recent_models(self) -> List[Dict[str, Any]]:
        """Get list of recently generated models."""
        try:
            output_dir = Path(self.platform.config.output_dir)
            if not output_dir.exists():
                return []

            # Get recent Excel files
            excel_files = list(output_dir.glob("*.xlsx"))
            excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            recent_models = []
            for file_path in excel_files[:5]:  # Last 5 models
                stat = file_path.stat()
                recent_models.append({
                    'filename': file_path.name,
                    'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'size': f"{stat.st_size / 1024:.1f} KB"
                })

            return recent_models

        except Exception as e:
            logger.error(f"Error getting recent models: {e}")
            return []

    def start(self):
        """Start the web interface."""
        if self.use_flask:
            logger.info(f"🌐 Starting Flask server on http://{self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False)
        else:
            logger.info(f"🌐 Starting simple HTTP server on http://{self.host}:{self.port}")
            self._start_simple_server()

    def _start_simple_server(self):
        """Start simple HTTP server as fallback."""
        class FinModAIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                """Handle GET requests."""
                try:
                    if self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()

                        context = {
                            'title': 'FinModAI - AI-Powered Financial Modeling',
                            'supported_models': ['dcf', 'lbo', 'comps', 'three_statement']
                        }
                        html = self.server.web_interface._generate_default_html(context)
                        self.wfile.write(html.encode())

                    elif self.path.startswith('/model/'):
                        # Extract model type from path
                        model_type = self.path.split('/model/')[1]
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()

                        context = {
                            'title': f'Create {model_type.upper()} Model',
                            'model_type': model_type,
                            'supported_models': ['dcf', 'lbo', 'comps', 'three_statement']
                        }
                        html = self.server.web_interface._generate_default_html(context)
                        self.wfile.write(html.encode())

                    else:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(b'Not Found')

                except Exception as e:
                    logger.error(f"HTTP handler error: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'Internal Server Error')

        try:
            server_address = (self.host, self.port)
            self.server = HTTPServer(server_address, FinModAIHandler)
            self.server.web_interface = self

            logger.info(f"🌐 Simple HTTP server running on http://{self.host}:{self.port}")
            self.server.serve_forever()

        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")

    def stop(self):
        """Stop the web interface."""
        if self.server:
            self.server.shutdown()
            logger.info("🛑 Web server stopped")

    def open_browser(self):
        """Open web interface in default browser."""
        url = f"http://{self.host}:{self.port}"
        logger.info(f"🌐 Opening browser to {url}")

        def open_url():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(url)

        threading.Thread(target=open_url, daemon=True).start()

def create_html_templates():
    """Create basic HTML templates if they don't exist."""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Create index.html
    index_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; color: #1f4e79; margin-bottom: 30px; }
            .model-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
            .model-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center; transition: transform 0.2s; }
            .model-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .model-card h3 { color: #2e7d32; margin-bottom: 10px; }
            .btn { background: #1f4e79; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
            .btn:hover { background: #153449; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 FinModAI</h1>
                <p><em>Bloomberg Terminal meets GitHub Copilot for financial modeling</em></p>
            </div>

            <h2>Available Models</h2>
            <div class="model-grid">
                {% for model in supported_models %}
                <div class="model-card">
                    <h3>{{ model.upper() }}</h3>
                    <p>Create professional {{ model.upper() }} models with AI assistance</p>
                    <a href="/model/{{ model }}" class="btn">Create {{ model.upper() }} Model</a>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """

    with open(templates_dir / "index.html", 'w') as f:
        f.write(index_html)

    # Create model.html
    model_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { background: #1f4e79; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #153449; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{{ title }}</h1>

            <form method="POST">
                <div class="form-group">
                    <label for="company_identifier">Company Identifier:</label>
                    <input type="text" id="company_identifier" name="company_identifier" placeholder="AAPL, Microsoft Corporation, or TICKER" required>
                </div>

                <div class="form-group">
                    <label for="growth_rate">Revenue Growth Rate (%):</label>
                    <input type="number" id="growth_rate" name="assumption_growth_rate" step="0.1" value="8.0">
                </div>

                <div class="form-group">
                    <label for="ebitda_margin">EBITDA Margin (%):</label>
                    <input type="number" id="ebitda_margin" name="assumption_ebitda_margin" step="0.1" value="25.0">
                </div>

                <div class="form-group">
                    <label for="terminal_growth">Terminal Growth Rate (%):</label>
                    <input type="number" id="terminal_growth" name="assumption_terminal_growth" step="0.01" value="2.5">
                </div>

                <button type="submit" class="btn">Generate {{ model_type.upper() }} Model</button>
            </form>

            <br>
            <a href="/">← Back to Home</a>
        </div>
    </body>
    </html>
    """

    with open(templates_dir / "model.html", 'w') as f:
        f.write(model_html)

    # Create results.html
    results_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .success { color: #2e7d32; font-weight: bold; }
            .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #1f4e79; }
            .btn { background: #1f4e79; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; }
            .btn:hover { background: #153449; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{{ title }}</h1>

            {% if result.success %}
            <div class="success">✅ Model Generated Successfully!</div>

            <h2>Key Results</h2>
            <div class="metric">
                <div>Enterprise Value: <span class="metric-value">${{ "%.1f"|format(result.outputs.enterprise_value) }}M</span></div>
            </div>
            <div class="metric">
                <div>Equity Value: <span class="metric-value">${{ "%.1f"|format(result.outputs.equity_value) }}M</span></div>
            </div>
            <div class="metric">
                <div>Implied Price: <span class="metric-value">${{ "%.2f"|format(result.outputs.implied_price) }}</span></div>
            </div>

            <h3>Generated Files</h3>
            <ul>
                {% for file in result.output_files %}
                <li><a href="/download/{{ file.split('/')[-1] }}" class="btn">Download {{ file.split('/')[-1] }}</a></li>
                {% endfor %}
            </ul>
            {% else %}
            <div style="color: #d32f2f; font-weight: bold;">❌ Error: {{ result.error }}</div>
            {% endif %}

            <br>
            <a href="/" class="btn">← Back to Home</a>
            <a href="/model/{{ result.model_type }}" class="btn">Create Another Model</a>
        </div>
    </body>
    </html>
    """

    with open(templates_dir / "results.html", 'w') as f:
        f.write(results_html)

# Create templates on import
create_html_templates()
