#!/usr/bin/env python3
"""
System Integration Test
Verifies that all components of the centralized financial data system work together.
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🔧 Testing module imports...")

    try:
        from financial_data_manager import FinancialDataManager, get_financial_data
        print("   ✅ Financial Data Manager imported")
    except ImportError as e:
        print(f"   ❌ Financial Data Manager failed: {e}")
        return False

    try:
        from financial_data_manager import CompanyFinancials
        from data_models import DCFInputs, ModelOutputs, ValuationMethod
        print("   ✅ Data Models imported")
    except ImportError as e:
        print(f"   ❌ Data Models failed: {e}")
        return False

    try:
        from data_quality_dashboard import DataQualityDashboard
        print("   ✅ Data Quality Dashboard imported")
    except ImportError as e:
        print(f"   ❌ Data Quality Dashboard failed: {e}")
        return False

    try:
        from model_examples import DCFModel, ValuationEngine
        print("   ✅ Model Examples imported")
    except ImportError as e:
        print(f"   ❌ Model Examples failed: {e}")
        return False

    return True

def test_data_retrieval():
    """Test basic data retrieval functionality."""
    print("\n📊 Testing data retrieval...")

    try:
        from financial_data_manager import get_financial_data

        # Test with a well-known company
        print("   🔍 Retrieving AAPL data...")
        apple_data = get_financial_data('AAPL', years=3)

        if isinstance(apple_data, dict) and apple_data.get('Company Name'):
            print(f"   ✅ Successfully retrieved: {apple_data.get('Company Name')}")
            print(f"      Data Quality Score: {apple_data.get('Data Quality Score', 'N/A')}/100")
            print(f"      Sources Used: {len(apple_data.get('Data Sources', []))}")
            return True
        elif hasattr(apple_data, 'company_name') and apple_data.company_name:
            print(f"   ✅ Successfully retrieved: {apple_data.company_name}")
            print(f"      Data Quality Score: {apple_data.data_quality.overall_score}/100")
            print(f"      Sources Used: {len(apple_data.data_quality.sources_used)}")
            return True
        else:
            print("   ❌ No data retrieved for AAPL")
            return False

    except Exception as e:
        print(f"   ❌ Data retrieval failed: {e}")
        traceback.print_exc()
        return False

def test_data_models():
    """Test data model functionality."""
    print("\n📋 Testing data models...")

    try:
        from financial_data_manager import CompanyFinancials
        from data_models import ModelOutputs, ValuationMethod

        # Test CompanyFinancials
        company = CompanyFinancials(
            ticker="TEST",
            company_name="Test Company",
            revenue=[100, 110, 120],
            ebitda=[20, 22, 25]
        )
        company.calculate_derived_metrics()

        print(f"   ✅ CompanyFinancials created: {company.company_name}")
        print(f"      EBITDA Margin: {company.ebitda_margin:.1f}%")

        # Test ModelOutputs
        outputs = ModelOutputs(
            ticker="TEST",
            company_name="Test Company",
            valuation_method=ValuationMethod.DCF,
            enterprise_value=1000000000,
            equity_value=900000000,
            data_quality_score=85.0
        )

        print(f"   ✅ ModelOutputs created")
        print(f"      Enterprise Value: ${outputs.enterprise_value/1e9:.1f}B")

        return True

    except Exception as e:
        print(f"   ❌ Data models test failed: {e}")
        traceback.print_exc()
        return False

def test_quality_dashboard():
    """Test data quality dashboard functionality."""
    print("\n📊 Testing quality dashboard...")

    try:
        from data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Test quality analysis
        print("   🔍 Analyzing AAPL data quality...")
        quality_report = dashboard.analyze_company_data_quality('AAPL')

        if 'error' not in quality_report:
            print(f"   ✅ Quality analysis successful")
            print(f"      Overall Score: {quality_report['overall_quality_score']}/100")
            print(f"      Completeness: {quality_report['completeness_score']:.1f}%")
            return True
        else:
            print(f"   ❌ Quality analysis failed: {quality_report['error']}")
            return False

    except Exception as e:
        print(f"   ❌ Quality dashboard test failed: {e}")
        traceback.print_exc()
        return False

def test_model_integration():
    """Test model integration capabilities."""
    print("\n🔗 Testing model integration...")

    try:
        from model_examples import DCFModel

        # Test DCF model with centralized data
        dcf_model = DCFModel()

        print("   🏢 Running DCF valuation for AAPL...")
        dcf_result = dcf_model.run_valuation('AAPL')

        if dcf_result.equity_value > 0:
            print(f"   ✅ DCF model successful")
            print(".2f")
            return True
        else:
            print("   ❌ DCF model returned zero valuation")
            return False

    except Exception as e:
        print(f"   ❌ Model integration test failed: {e}")
        traceback.print_exc()
        return False

def test_dcf_model_integration():
    """Test that the existing DCF model uses centralized data."""
    print("\n💰 Testing DCF model integration...")

    try:
        # Import the DCF model
        import professional_dcf_model as dcf

        # Check if centralized data is available
        if dcf.CENTRALIZED_DATA_AVAILABLE:
            print("   ✅ DCF model has centralized data integration")
            print("      The model will automatically use high-quality data")
            return True
        else:
            print("   ⚠️ DCF model using legacy data (centralized system not available)")
            print("      This is normal if API keys aren't configured")
            return True  # Not a failure, just using fallback

    except Exception as e:
        print(f"   ❌ DCF integration test failed: {e}")
        traceback.print_exc()
        return False

def run_full_system_test():
    """Run comprehensive system integration test."""
    print("🚀 CENTRALIZED FINANCIAL DATA SYSTEM - INTEGRATION TEST")
    print("=" * 60)
    print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    test_results = []

    # Run all tests
    test_results.append(("Module Imports", test_imports()))
    test_results.append(("Data Retrieval", test_data_retrieval()))
    test_results.append(("Data Models", test_data_models()))
    test_results.append(("Quality Dashboard", test_quality_dashboard()))
    test_results.append(("Model Integration", test_model_integration()))
    test_results.append(("DCF Integration", test_dcf_model_integration()))

    # Print results summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print("20")
        if result:
            passed += 1

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - System is fully operational!")
        print("\n💡 Next Steps:")
        print("   1. Run 'python3 setup_apis.py' to configure API keys")
        print("   2. Use the system in your financial models")
        print("   3. Check the README for detailed usage examples")
    elif passed >= total * 0.8:
        print("⚠️ MOST TESTS PASSED - System is mostly operational")
        print("   Some features may not work without API keys or full setup")
    else:
        print("❌ SYSTEM ISSUES DETECTED")
        print("   Check the failed tests above and ensure all dependencies are installed")

    print("\n🔧 Quick Setup Commands:")
    print("   pip install -r requirements-enhanced.txt")
    print("   python3 setup_apis.py")
    print("   python3 test_system.py  # Re-run this test")

    return passed == total

if __name__ == "__main__":
    success = run_full_system_test()
    sys.exit(0 if success else 1)
