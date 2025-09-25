#!/usr/bin/env python3
"""
FinModAI - AI-Powered Financial Modeling Platform
Bloomberg Terminal meets GitHub Copilot for financial modeling

Core platform architecture and main entry points.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FinModAI')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import platform modules
from finmodai.data_ingestion import DataIngestionEngine
from finmodai.model_factory import ModelFactory
from finmodai.excel_engine import ExcelGenerationEngine
from finmodai.web_interface import WebInterface

@dataclass
class PlatformConfig:
    """Platform configuration settings."""
    data_cache_dir: str = ".finmodai_cache"
    model_templates_dir: str = "templates"
    output_dir: str = "generated_models"
    max_cache_age_hours: int = 24
    enable_api_integrations: bool = True
    supported_model_types: List[str] = None

    def __post_init__(self):
        if self.supported_model_types is None:
            self.supported_model_types = [
                "dcf", "lbo", "comps", "three_statement",
                "merger", "ipo", "sotp", "football_field"
            ]

class FinModAIPlatform:
    """
    Main FinModAI Platform Class
    Handles all platform operations and coordinates between components.
    """

    def __init__(self, config: Optional[PlatformConfig] = None):
        self.config = config or PlatformConfig()
        self._setup_directories()

        # Initialize core components
        self.data_engine = DataIngestionEngine(self.config)
        self.model_factory = ModelFactory(self.config)
        self.excel_engine = ExcelGenerationEngine(self.config)

        # Initialize web interface if needed
        self.web_interface = None

        logger.info("🚀 FinModAI Platform initialized successfully")

    def _setup_directories(self):
        """Create necessary directories."""
        dirs = [
            self.config.data_cache_dir,
            self.config.model_templates_dir,
            self.config.output_dir
        ]

        for dir_path in dirs:
            Path(dir_path).mkdir(exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

    def generate_model(
        self,
        model_type: str,
        company_identifier: Union[str, Dict[str, Any]],
        assumptions: Optional[Dict[str, Any]] = None,
        output_format: str = "excel",
        include_sensitivity: bool = True,
        include_dashboard: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a financial model for a company.

        Args:
            model_type: Type of model (dcf, lbo, comps, etc.)
            company_identifier: Company ticker, name, or financial data dict
            assumptions: Custom assumptions to override defaults
            output_format: Output format (excel, json, pdf)
            include_sensitivity: Include sensitivity analysis
            include_dashboard: Include visualization dashboard

        Returns:
            Dict containing model results and file paths
        """

        print(f"📊 DEBUG: FinModAIPlatform.generate_model called with model_type={model_type}")
        logger.info(f"🔄 Generating {model_type.upper()} model for {company_identifier}")

        start_time = datetime.now()

        try:
            # Step 1: Ingest financial data
            if isinstance(company_identifier, str):
                logger.info("📊 Fetching financial data...")
                financial_data = self.data_engine.get_company_data(company_identifier)
            else:
                logger.info("📊 Using provided financial data...")
                financial_data = company_identifier

            if not financial_data:
                raise ValueError(f"Could not retrieve data for {company_identifier}")

            # Add corrected ticker info if available
            corrected_ticker = getattr(financial_data, 'corrected_ticker', None) if hasattr(financial_data, 'corrected_ticker') else None

            # Step 2: Generate model using AI factory
            logger.info("🤖 AI generating model structure...")
            model_spec = self.model_factory.create_model(
                model_type=model_type,
                financial_data=financial_data,
                custom_assumptions=assumptions,
                include_sensitivity=include_sensitivity,
                include_dashboard=include_dashboard
            )

            # Step 3: Generate output files
            logger.info("📄 Creating output files...")
            print(f"🔧 DEBUG: About to call excel engine with model_spec.model_type: {model_spec.model_type}")
            try:
                output_files = self.excel_engine.generate_output(
                    model_spec=model_spec,
                    output_format=output_format
                )
                print(f"🔧 DEBUG: Excel engine returned {len(output_files)} output files: {output_files}")
            except Exception as e:
                logger.error(f"❌ Excel engine failed: {e}")
                print(f"🔧 DEBUG: Excel engine failed: {e}")
                output_files = []

            # Always check for recent Excel files as fallback
            import glob
            from pathlib import Path
            all_files = glob.glob('generated_models/*.xlsx')
            for file_path in all_files:
                if Path(file_path).exists():
                    file_path_obj = Path(file_path)
                    if (datetime.now().timestamp() - file_path_obj.stat().st_mtime) < 3600:
                        if file_path not in output_files:
                            output_files.append(file_path)
                            print(f"🔧 DEBUG: Found fallback file: {file_path}")
            if output_files:
                print(f"🔧 DEBUG: Using {len(output_files)} output files")

            # Step 4: Calculate performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "model_type": model_type,
                "company": getattr(financial_data, 'company_name', company_identifier),
                "processing_time_seconds": processing_time,
                "output_files": output_files,
                "model_summary": self._generate_model_summary(model_spec, company_identifier, corrected_ticker),
                "generated_at": datetime.now().isoformat(),
                "platform_version": "1.0.0"
            }

            logger.info(f"✅ Model generated in {processing_time:.1f}s")
            return result

        except Exception as e:
            logger.error(f"❌ Model generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model_type": model_type,
                "company": company_identifier,
                "generated_at": datetime.now().isoformat()
            }

    def _generate_model_summary(self, model_spec: Dict[str, Any], company_identifier: str, corrected_ticker: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary of the created model."""
        summary = {
            "key_assumptions": {},
            "valuation_outputs": {},
            "sensitivity_ranges": {},
            "data_quality_score": 0
        }

        # Extract key metrics from model spec
        if hasattr(model_spec, 'assumptions') and model_spec.assumptions:
            assumptions = model_spec.assumptions
            summary["key_assumptions"] = {
                "revenue": assumptions.get("Rev0", assumptions.get("revenue", 0)),
                "growth_rate": assumptions.get("g_base", assumptions.get("growth_rate", 0)),
                "wacc": assumptions.get("WACC", assumptions.get("wacc", 0)),
                "terminal_growth": assumptions.get("g_term", assumptions.get("terminal_growth", 0))
            }

        if hasattr(model_spec, 'outputs') and model_spec.outputs:
            outputs = model_spec.outputs
            summary["valuation_outputs"] = {
                "enterprise_value": outputs.get("EV", outputs.get("enterprise_value", 0)),
                "equity_value": outputs.get("EquityValue", outputs.get("equity_value", 0)),
                "implied_price": outputs.get("ImpliedPrice", outputs.get("implied_price", 0))
            }

        # Also check calculations for additional metrics
        if hasattr(model_spec, 'calculations') and model_spec.calculations:
            calculations = model_spec.calculations
            if not summary["key_assumptions"].get("revenue"):
                summary["key_assumptions"]["revenue"] = calculations.get("revenue", 0)
            if not summary["valuation_outputs"].get("enterprise_value"):
                summary["valuation_outputs"]["enterprise_value"] = calculations.get("enterprise_value", 0)

        # Add corrected ticker info if available
        if corrected_ticker and corrected_ticker != company_identifier:
            summary["corrected_ticker"] = corrected_ticker
        else:
            summary["corrected_ticker"] = company_identifier  # Use original if no correction

        return summary

    def batch_generate_models(
        self,
        model_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple models in batch.

        Args:
            model_requests: List of model generation requests

        Returns:
            List of results
        """
        logger.info(f"🔄 Batch generating {len(model_requests)} models")

        results = []
        for i, request in enumerate(model_requests, 1):
            logger.info(f"Processing model {i}/{len(model_requests)}")
            result = self.generate_model(**request)
            results.append(result)

        successful = sum(1 for r in results if r.get("success", False))
        logger.info(f"✅ Batch complete: {successful}/{len(model_requests)} successful")

        return results

    def get_supported_models(self) -> List[str]:
        """Get list of supported model types."""
        return self.config.supported_model_types.copy()

    def get_model_templates(self) -> Dict[str, Any]:
        """Get available model templates and their configurations."""
        return self.model_factory.get_available_templates()

    def start_web_interface(self, host: str = "localhost", port: int = 8000):
        """Start the web interface for the platform."""
        if not self.web_interface:
            self.web_interface = WebInterface(self, host, port)
        self.web_interface.start()

    def validate_model(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a model specification for errors and inconsistencies."""
        return self.model_factory.validate_model(model_spec)

    def export_model_to_powerpoint(self, model_result: Dict[str, Any]) -> str:
        """Export model results to PowerPoint presentation."""
        # This would integrate with PowerPoint generation
        logger.info("📊 PowerPoint export not yet implemented")
        return ""

    def get_api_endpoints(self) -> Dict[str, str]:
        """Get available API endpoints for integrations."""
        return {
            "generate_model": "/api/v1/generate-model",
            "batch_generate": "/api/v1/batch-generate",
            "get_templates": "/api/v1/templates",
            "validate_model": "/api/v1/validate",
            "health_check": "/api/v1/health"
        }

def quick_model_generation(model_type: str, company: str) -> Dict[str, Any]:
    """
    Quick model generation function for simple use cases.

    Usage:
        result = quick_model_generation("dcf", "AAPL")
    """
    platform = FinModAIPlatform()
    return platform.generate_model(model_type, company)

def main():
    """Main entry point for command line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="FinModAI - AI-Powered Financial Modeling")
    parser.add_argument("model_type", help="Model type (dcf, lbo, comps, etc.)")
    parser.add_argument("company", help="Company ticker or name")
    parser.add_argument("--format", default="excel", help="Output format")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--host", default="localhost", help="Web interface host")
    parser.add_argument("--port", type=int, default=8000, help="Web interface port")

    args = parser.parse_args()

    if args.web:
        # Start web interface
        platform = FinModAIPlatform()
        platform.start_web_interface(args.host, args.port)
    else:
        # Generate single model
        result = quick_model_generation(args.model_type, args.company)

        if result["success"]:
            print("✅ Model generated successfully!")
            print(f"📁 Files: {', '.join(result['output_files'])}")
            print(f"⏱️ Processing time: {result.get('processing_time_seconds', 0):.1f}s")
        else:
            print(f"❌ Generation failed: {result['error']}")

if __name__ == "__main__":
    main()
