#!/usr/bin/env python3
"""
FinModAI - AI-Powered Financial Modeling Platform
Bloomberg Terminal meets GitHub Copilot for financial modeling
"""

__version__ = "1.0.0"
__author__ = "FinModAI Team"
__description__ = "AI-powered platform for automated financial modeling"

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'FinModAIPlatform':
        from .platform import FinModAIPlatform
        return FinModAIPlatform
    elif name == 'quick_model_generation':
        from .platform import quick_model_generation
        return quick_model_generation
    elif name == 'DataIngestionEngine':
        from .data_ingestion import DataIngestionEngine
        return DataIngestionEngine
    elif name == 'FinancialData':
        from .data_ingestion import FinancialData
        return FinancialData
    elif name == 'ModelFactory':
        from .model_factory import ModelFactory
        return ModelFactory
    elif name == 'ModelSpecification':
        from .model_factory import ModelSpecification
        return ModelSpecification
    elif name == 'ExcelGenerationEngine':
        from .excel_engine import ExcelGenerationEngine
        return ExcelGenerationEngine
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'FinModAIPlatform',
    'quick_model_generation',
    'DataIngestionEngine',
    'FinancialData',
    'ModelFactory',
    'ModelSpecification',
    'ExcelGenerationEngine'
]
